"""
Vector Store Module
Handles storage and retrieval of embeddings using FAISS
"""

import os
import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import faiss
from core.config import config


class VectorStore:
    """FAISS-based vector store for embeddings"""
    
    def __init__(self, store_path: str = None):
        self.store_path = store_path or config.vector_store_path
        self.index = None
        self.metadata = {}  # chunk_id -> metadata
        self.document_registry = {}  # file_id -> {filename, file_type, content_hash, upload_time}
        self.is_loaded = False
        self.dimension = 768  # Default for Arabic BERT models
        # Local mapping of FAISS ids -> chunk_id for fast lookup
        self._faiss_id_to_chunk: Dict[int, str] = {}
        
        # Create store directory if it doesn't exist
        os.makedirs(self.store_path, exist_ok=True)
        
        self.index_path = os.path.join(self.store_path, "index.faiss")
        self.metadata_path = os.path.join(self.store_path, "metadata.json")
        self.documents_registry_path = os.path.join(self.store_path, "documents.json")
    
    def load(self):
        """Load existing vector store"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                print(f"📚 Loading vector store from {self.store_path}")
                logging.getLogger("simple-rag.vector_store").info("Loading store from %s", self.store_path)

                # Load FAISS index
                self.index = faiss.read_index(self.index_path)
                self.dimension = self.index.d

                # Load metadata
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                # Load document registry (if present)
                if os.path.exists(self.documents_registry_path):
                    with open(self.documents_registry_path, 'r', encoding='utf-8') as f:
                        self.document_registry = json.load(f)
                # Rebuild in-memory id map from metadata if available
                self._faiss_id_to_chunk.clear()
                for chunk_id, meta in self.metadata.items():
                    faiss_id = meta.get('faiss_id')
                    if isinstance(faiss_id, int):
                        self._faiss_id_to_chunk[faiss_id] = chunk_id

                self.is_loaded = True
                print(f"✅ Vector store loaded: {self.index.ntotal} vectors")
                logging.getLogger("simple-rag.vector_store").info("Loaded index vectors=%d", self.index.ntotal)
            else:
                print("📚 No existing vector store found, will create new one")
                self._create_new_index()
                
        except Exception as e:
            print(f"❌ Failed to load vector store: {e}")
            logging.getLogger("simple-rag.vector_store").exception("Failed to load store: %s", str(e))
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        print(f"🔧 Creating new FAISS index with dimension {self.dimension}")
        logging.getLogger("simple-rag.vector_store").info("Creating new FAISS index dim=%d", self.dimension)
        
        # Create IndexFlatIP wrapped with ID map for stable deletions
        base = faiss.IndexFlatIP(self.dimension)
        self.index = faiss.IndexIDMap2(base)
        self.metadata = {}
        self.is_loaded = True
    
    def add_chunk(self, chunk_id: str, embedding: np.ndarray, metadata: Dict[str, Any]):
        """
        Add a chunk to the vector store
        
        Args:
            chunk_id: Unique identifier for the chunk
            embedding: Vector embedding
            metadata: Associated metadata
        """
        if not self.is_loaded:
            self._create_new_index()
        
        # Ensure embedding is the right shape and type
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        
        embedding = embedding.astype(np.float32)
        
        # Normalize embedding for cosine similarity
        faiss.normalize_L2(embedding)
        
        # Compute deterministic FAISS id from chunk_id
        faiss_id = self._compute_faiss_id(chunk_id)
        ids = np.array([faiss_id], dtype='int64')
        # Add to index with explicit ids
        self.index.add_with_ids(embedding, ids)
        
        # Store metadata
        metadata_with_id = dict(metadata)
        metadata_with_id['faiss_id'] = int(faiss_id)
        self.metadata[chunk_id] = metadata_with_id
        self._faiss_id_to_chunk[int(faiss_id)] = chunk_id
        
        print(f"✅ Added chunk {chunk_id} to vector store")
        logging.getLogger("simple-rag.vector_store").debug("Added chunk id=%s", chunk_id)
    
    def add_chunks_batch(self, chunks: List[Tuple[str, np.ndarray, Dict[str, Any]]]):
        """
        Add multiple chunks in batch for efficiency
        
        Args:
            chunks: List of (chunk_id, embedding, metadata) tuples
        """
        if not chunks:
            return
        
        if not self.is_loaded:
            self._create_new_index()
        
        # Prepare embeddings
        embeddings = []
        for chunk_id, embedding, metadata in chunks:
            if embedding.ndim == 1:
                embedding = embedding.reshape(1, -1)
            embeddings.append(embedding.astype(np.float32))
        
        # Stack embeddings
        embeddings_array = np.vstack(embeddings)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to index with ids
        ids: List[int] = []
        metas_with_id: List[Tuple[str, Dict[str, Any]]] = []
        for chunk_id, _, metadata in chunks:
            fid = self._compute_faiss_id(chunk_id)
            ids.append(int(fid))
            metas_with_id.append((chunk_id, metadata))
        ids_array = np.array(ids, dtype='int64')
        self.index.add_with_ids(embeddings_array, ids_array)
        
        # Store metadata and id map
        for (chunk_id, metadata), fid in zip(metas_with_id, ids):
            m = dict(metadata)
            m['faiss_id'] = int(fid)
            self.metadata[chunk_id] = m
            self._faiss_id_to_chunk[int(fid)] = chunk_id
        
        print(f"✅ Added {len(chunks)} chunks to vector store")
        logging.getLogger("simple-rag.vector_store").info("Added chunks count=%d", len(chunks))
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of results with metadata and similarity scores
        """
        if not self.is_loaded or self.index.ntotal == 0:
            return []
        
        # Ensure query embedding is the right shape
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_embedding = query_embedding.astype(np.float32)
        
        # Normalize query for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search
        similarities, indices = self.index.search(query_embedding, k)
        logging.getLogger("simple-rag.vector_store").debug("Search done k=%d", k)
        
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if idx >= 0:
                chunk_id = self._faiss_id_to_chunk.get(int(idx))
                if chunk_id and chunk_id in self.metadata:
                    results.append({
                        'chunk_id': chunk_id,
                        'similarity': float(similarity),
                        'metadata': self.metadata[chunk_id]
                    })
        
        return results
    
    def _compute_faiss_id(self, chunk_id: str) -> int:
        """Compute a stable 64-bit integer id for a given chunk_id."""
        h = hashlib.sha256(chunk_id.encode('utf-8')).digest()
        # Interpret first 8 bytes as SIGNED 64-bit to stay within numpy int64 range
        fid = int.from_bytes(h[:8], byteorder='big', signed=True)
        # Avoid zero id to reduce accidental ambiguity in maps
        if fid == 0:
            fid = 1
        return fid
    
    def delete_document(self, file_id: str) -> int:
        """
        Delete all chunks belonging to a document
        
        Args:
            file_id: File identifier
            
        Returns:
            Number of chunks deleted
        """
        if not self.is_loaded:
            return 0
        
        # Find chunks belonging to this file
        chunks_to_delete = []
        file_extension = None
        # Consult registry first for file_type
        if file_id in self.document_registry:
            file_extension = self.document_registry[file_id].get('file_type')
        for chunk_id, metadata in self.metadata.items():
            if metadata.get('file_id') == file_id:
                chunks_to_delete.append(chunk_id)
                if file_extension is None:
                    file_extension = metadata.get('file_type')
        
        # Remove from index by ids, and from metadata
        if chunks_to_delete:
            ids = []
            for chunk_id in chunks_to_delete:
                meta = self.metadata.get(chunk_id, {})
                fid = meta.get('faiss_id')
                if isinstance(fid, int):
                    ids.append(fid)
            if ids:
                ids_array = np.array(ids, dtype='int64')
                selector = faiss.IDSelectorArray(len(ids), faiss.swig_ptr(ids_array))
                self.index.remove_ids(selector)
            # Now drop metadata and reverse map entries
            for chunk_id in chunks_to_delete:
                meta = self.metadata.pop(chunk_id, None)
                if meta and isinstance(meta.get('faiss_id'), int):
                    self._faiss_id_to_chunk.pop(meta['faiss_id'], None)
        
        # Also remove the original uploaded file copy (best-effort)
        try:
            if file_extension:
                original_path = os.path.join(config.documents_path, f"{file_id}{file_extension}")
                if os.path.exists(original_path):
                    os.remove(original_path)
        except Exception:
            # Ignore file removal errors to avoid blocking API deletion
            pass
        
        # Remove from registry
        if file_id in self.document_registry:
            try:
                del self.document_registry[file_id]
            except Exception:
                pass
        
        print(f"🗑️ Deleted {len(chunks_to_delete)} chunks for file {file_id}")
        logging.getLogger("simple-rag.vector_store").info("Deleted chunks file_id=%s count=%d", file_id, len(chunks_to_delete))
        return len(chunks_to_delete)
    
    def _rebuild_index(self):
        """No-op: with IDMap we do not need full rebuild for deletions."""
        return
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the store"""
        documents = {}
        
        for chunk_id, metadata in self.metadata.items():
            file_id = metadata.get('file_id')
            if file_id and file_id not in documents:
                documents[file_id] = {
                    'file_id': file_id,
                    'filename': metadata.get('filename', 'Unknown'),
                    'file_type': metadata.get('file_type', 'Unknown'),
                    'upload_time': metadata.get('upload_time', 'Unknown'),
                    'chunk_count': 0
                }
            
            if file_id:
                documents[file_id]['chunk_count'] += 1
        
        return list(documents.values())
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        return len(self.list_documents())
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks"""
        return len(self.metadata)
    
    def save(self):
        """Save the vector store to disk"""
        if not self.is_loaded:
            return
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            # Save document registry
            with open(self.documents_registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.document_registry, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Vector store saved to {self.store_path}")
            logging.getLogger("simple-rag.vector_store").info("Saved store to %s", self.store_path)
            
        except Exception as e:
            print(f"❌ Failed to save vector store: {e}")
            logging.getLogger("simple-rag.vector_store").exception("Failed saving store: %s", str(e))

    def clear_all(self, remove_documents: bool = True) -> Dict[str, Any]:
        """Clear FAISS index, metadata, and document registry. Optionally remove originals.
        Returns basic stats of what was cleared.
        """
        total_chunks = len(self.metadata)
        total_docs = len(self.document_registry)

        # Remove data files in store path
        try:
            for p in [self.index_path, self.metadata_path, self.documents_registry_path]:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
        finally:
            # Reset in-memory
            self.metadata = {}
            self.document_registry = {}
            self._faiss_id_to_chunk.clear()
            self._create_new_index()

        # Optionally clear originals
        removed_files = 0
        if remove_documents:
            try:
                for name in os.listdir(config.documents_path):
                    fp = os.path.join(config.documents_path, name)
                    if os.path.isfile(fp):
                        try:
                            os.remove(fp)
                            removed_files += 1
                        except Exception:
                            pass
            except Exception:
                pass

        logging.getLogger("simple-rag.vector_store").warning(
            "Store cleared docs=%d chunks=%d originals_removed=%d", total_docs, total_chunks, removed_files
        )

        return {
            "documents_cleared": total_docs,
            "chunks_cleared": total_chunks,
            "original_files_removed": removed_files
        }

    def register_document(self, file_id: str, filename: str, file_type: str, content_hash: str, upload_time: str) -> None:
        """Register a document mapping for id -> original name/hash."""
        self.document_registry[file_id] = {
            'filename': filename,
            'file_type': file_type,
            'content_hash': content_hash,
            'upload_time': upload_time
        }

    def find_duplicate(self, filename: str, content_hash: str) -> Optional[str]:
        """Return an existing file_id if a document with same name or hash exists."""
        for fid, info in self.document_registry.items():
            if info.get('filename') == filename or info.get('content_hash') == content_hash:
                return fid
        return None

    def get_file_id_by_filename(self, filename: str) -> Optional[str]:
        """Lookup file_id by original filename."""
        for fid, info in self.document_registry.items():
            if info.get('filename') == filename:
                return fid
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            "is_loaded": self.is_loaded,
            "total_chunks": len(self.metadata),
            "total_documents": self.get_document_count(),
            "index_size": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "store_path": self.store_path
        }
