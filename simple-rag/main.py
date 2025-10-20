"""
Simple Arabic RAG System
Core functionality: File upload, chunking, embedding, retrieval, generation
"""

import os
import uuid
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import shutil
import hashlib

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from core.config import Config
from core.chunker import ArabicTextChunker
from core.embeddings import ArabicEmbedder
from core.vector_store import VectorStore
from core.generator import Generator
from core.file_processor import FileProcessor
from core.logging import configure_logging, get_logger, log_operation, log_error, log_performance
from middleware.error_handler import ErrorHandlerMiddleware, RequestLoggingMiddleware


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    max_results: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    processing_time_ms: int
    model_used: str


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    chunks_created: int
    processing_time_ms: int
    status: str


class DeleteByNameRequest(BaseModel):
    filename: str


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
)
logger = logging.getLogger("simple-rag")

# Initialize FastAPI app
app = FastAPI(
    title="Simple Arabic RAG System",
    description="Core RAG functionality: upload, chunk, embed, retrieve, generate",
    version="1.0.0",
    default_response_class=JSONResponse
)

# Configure comprehensive logging
configure_logging()
rag_logger = get_logger("main")

# Add middleware (order matters - first added is outermost)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
config = Config()
chunker = ArabicTextChunker(
    sentences_per_chunk=config.sentences_per_chunk,
    sentence_overlap=config.sentence_overlap
)
embedder = ArabicEmbedder(config.embedding_model)
vector_store = VectorStore(config.vector_store_path)
generator = Generator(config)
file_processor = FileProcessor()
# Mount static files (UI)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/manage")
async def manage_ui():
    """Serve the management UI page"""
    return FileResponse("static/index.html")


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    print("🚀 Starting Simple Arabic RAG System...")
    logger.info("Starting system initialization")
    
    # Initialize embedder
    print("📥 Loading embedding model...")
    logger.info("Loading embedding model")
    embedder.load()
    
    # Load existing vector store if available
    if os.path.exists(config.vector_store_path):
        print("📚 Loading existing vector store...")
        logger.info("Loading existing vector store from %s", config.vector_store_path)
        vector_store.load()
    
    print("✅ System ready!")
    logger.info("System ready")


@app.get("/")
async def root():
    """Root endpoint with system info"""
    return {
        "name": "Simple Arabic RAG System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload": "/upload",
            "query": "/query",
            "health": "/health",
            "stats": "/stats",
            "reset": "/reset"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "embedder": embedder.is_loaded,
            "vector_store": vector_store.is_loaded,
            "generator": generator.is_ready
        }
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_documents": vector_store.get_document_count(),
        "total_chunks": vector_store.get_chunk_count(),
        "embedder_model": config.embedding_model,
        "generation_model": config.generation_model,
        "vector_store_path": config.vector_store_path
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a document
    
    Supported formats: .txt, .pdf, .docx, .md
    """
    start_time = datetime.utcnow()
    # timing start (kept for potential future metrics)
    request_id = str(uuid.uuid4())
    logger.info("[upload] start request_id=%s filename=%s size_bytes=?", request_id, file.filename)
    
    # Validate file type
    allowed_extensions = {'.txt', '.pdf', '.docx', '.md'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )
    
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily
        temp_path = f"temp_{file_id}{file_extension}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        size_bytes = os.path.getsize(temp_path)
        logger.info("[upload] saved temp file request_id=%s file_id=%s size_bytes=%s", request_id, file_id, size_bytes)
        
        # Compute content hash and check duplicates (by name or hash)
        content_hash = hashlib.sha256(content).hexdigest()
        duplicate_id = vector_store.find_duplicate(file.filename, content_hash)
        if duplicate_id:
            # Clean up temp file and reject duplicate
            try:
                os.remove(temp_path)
            except Exception:
                pass
            raise HTTPException(status_code=409, detail=f"Duplicate document detected (file_id={duplicate_id}). Upload skipped.")
        
        # Process file
        print(f"📄 Processing file: {file.filename}")
        t_extract = time.perf_counter()
        text_content = file_processor.extract_text(temp_path)
        logger.info("[upload] extracted text request_id=%s file_id=%s chars=%s elapsed_ms=%d", request_id, file_id, len(text_content), int((time.perf_counter()-t_extract)*1000))
        
        # Chunk text
        print("✂️ Chunking text...")
        t_chunk = time.perf_counter()
        chunks = chunker.chunk(text_content)
        logger.info("[upload] chunked text request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunks), int((time.perf_counter()-t_chunk)*1000))
        
        # Generate embeddings
        print(f"🧠 Generating embeddings for {len(chunks)} chunks...")
        t_embed = time.perf_counter()
        embeddings = embedder.encode(chunks)
        logger.info("[upload] embeddings generated request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunks), int((time.perf_counter()-t_embed)*1000))
        
        # Store in vector database
        print("💾 Storing in vector database...")
        t_store = time.perf_counter()
        chunk_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{file_id}_chunk_{i}"
            metadata = {
                "file_id": file_id,
                "filename": file.filename,
                "chunk_index": i,
                "chunk_text": chunk,
                "file_type": file_extension,
                "upload_time": start_time.isoformat()
            }
            
            vector_store.add_chunk(chunk_id, embedding, metadata)
            chunk_ids.append(chunk_id)
        logger.info("[upload] stored chunks request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunk_ids), int((time.perf_counter()-t_store)*1000))
        
        # Register document mapping for future reference/deletion
        vector_store.register_document(
            file_id=file_id,
            filename=file.filename,
            file_type=file_extension,
            content_hash=content_hash,
            upload_time=start_time.isoformat()
        )
        
        # Persist vector store to disk
        try:
            vector_store.save()
            logger.info("[upload] vector store saved request_id=%s file_id=%s", request_id, file_id)
        except Exception as save_err:
            logger.exception("[upload] failed to save vector store request_id=%s error=%s", request_id, str(save_err))
            # Abort without persisting original
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(save_err)}")

        # Persist original file copy ONLY after successful processing and save
        try:
            dest_filename = f"{file_id}{file_extension}"
            dest_path = os.path.join(config.documents_path, dest_filename)
            shutil.copyfile(temp_path, dest_path)
            logger.info("[upload] copied original file to documents_path file_id=%s dest=%s", file_id, dest_path)
        except Exception as copy_err:
            logger.warning("[upload] failed to copy original file file_id=%s error=%s", file_id, str(copy_err))
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info("[upload] completed request_id=%s file_id=%s total_ms=%d", request_id, file_id, int(processing_time))
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            chunks_created=len(chunks),
            processing_time_ms=int(processing_time),
            status="success"
        )
        
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        # If it's an intentional HTTPException (e.g., 409 duplicate), re-raise as-is
        if isinstance(e, HTTPException):
            raise e
        logger.exception("[upload] failed request_id=%s filename=%s error=%s", request_id, file.filename, str(e))
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query documents and generate response
    
    Args:
        query: Arabic text query
        max_results: Maximum number of relevant chunks to retrieve
    """
    start_time = datetime.utcnow()
    t0 = time.perf_counter()
    request_id = str(uuid.uuid4())
    logger.info("[query] start request_id=%s query='%s' max_results=%d", request_id, request.query, request.max_results)
    
    try:
        # Check if it's a general conversation question
        general_responses = {
            "عامل إيه": "الحمد لله، أنا بخير. إزيك إنت؟",
            "صباح الخير": "صباح النور! إزيك صباح النهاردة؟",
            "مساء الخير": "مساء النور! إزيك المسا؟",
            "إزيك": "الحمد لله، أنا بخير. إزيك إنت؟",
            "أهلا": "أهلا وسهلا! إزيك؟",
            "مرحبا": "مرحبا! إزيك؟",
            "كيف حالك": "الحمد لله، أنا بخير. إزيك إنت؟",
            "شكرا": "العفو! أي وقت.",
            "مع السلامة": "الله معاك! ربنا يخليك.",
            "وداعا": "الله معاك! ربنا يخليك."
        }
        
        # Check for exact matches or similar greetings
        query_lower = request.query.lower().strip()
        for greeting, response in general_responses.items():
            if greeting.lower() in query_lower or query_lower in greeting.lower():
                # Log the general conversation response
                logger.info(
                    "[query] كيمو general conversation response",
                    extra={
                        'operation': 'kimo_general_response',
                        'request_id': request_id,
                        'query': request.query,
                        'greeting_type': greeting,
                        'response': response,
                        'model_used': 'kimo_general'
                    }
                )
                
                resp = QueryResponse(
                    answer=response,
                    sources=[],
                    processing_time_ms=int((time.perf_counter()-t0)*1000),
                    model_used="kimo_general"
                )
                return resp
        
        # Generate query embedding
        print(f"🔍 Processing query: {request.query}")
        query_embedding = embedder.encode([request.query])[0]
        
        # Retrieve relevant chunks
        print(f"📚 Retrieving top {request.max_results} chunks...")
        results = vector_store.search(query_embedding, k=request.max_results)
        logger.info("[query] retrieval done request_id=%s results=%d elapsed_ms=%d", request_id, len(results), int((time.perf_counter()-t0)*1000))
        
        if not results:
            no_results_response = "معذرة، مش لاقي معلومات عن ده في قاعدة البيانات بتاعتي."
            
            # Log the no results response
            logger.info(
                "[query] كيمو no results response",
                extra={
                    'operation': 'kimo_no_results',
                    'request_id': request_id,
                    'query': request.query,
                    'response': no_results_response,
                    'model_used': 'none'
                }
            )
            
            resp = QueryResponse(
                answer=no_results_response,
                sources=[],
                processing_time_ms=int((time.perf_counter()-t0)*1000),
                model_used="none"
            )
            return resp
        
        # Prepare context from retrieved chunks
        context_parts = []
        sources = []
        
        for i, result in enumerate(results):
            chunk_text = result['metadata']['chunk_text']
            context_parts.append(f"{i+1}. {chunk_text}")
            
            sources.append({
                "filename": result['metadata']['filename'],
                "chunk_index": result['metadata']['chunk_index'],
                "similarity_score": float(result['similarity']),
                "preview": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text
            })
        
        context = "\n\n".join(context_parts)
        
        # Generate response
        print("🤖 Generating response using Kimo...")
        t_gen = time.perf_counter()
        answer = await generator.generate(
            query=request.query,
            context=context
        )
        logger.info("[query] generation done request_id=%s model=gemini elapsed_ms=%d", request_id, int((time.perf_counter()-t_gen)*1000))
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info("[query] completed request_id=%s total_ms=%d", request_id, int(processing_time))
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            processing_time_ms=int(processing_time),
            model_used="kimo_gemini"
        )
        
    except Exception as e:
        logger.exception("[query] failed request_id=%s error=%s", request_id, str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    """Delete a document and all its chunks"""
    try:
        deleted_count = vector_store.delete_document(file_id)
        # Persist deletion
        try:
            vector_store.save()
        except Exception as save_err:
            logger.exception("[delete] failed to save vector store after deletion file_id=%s error=%s", file_id, str(save_err))
        return {
            "file_id": file_id,
            "chunks_deleted": deleted_count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@app.delete("/documents")
async def delete_document_by_name(request: DeleteByNameRequest):
    """Delete a document by original filename."""
    try:
        file_id = vector_store.get_file_id_by_filename(request.filename)
        if not file_id:
            raise HTTPException(status_code=404, detail="Document not found")
        deleted_count = vector_store.delete_document(file_id)
        try:
            vector_store.save()
        except Exception as save_err:
            logger.exception("[delete] failed to save vector store after deletion file_id=%s error=%s", file_id, str(save_err))
        return {
            "file_id": file_id,
            "filename": request.filename,
            "chunks_deleted": deleted_count,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@app.put("/documents")
async def update_document(file: UploadFile = File(...)):
    """Update an existing document by original filename, preserving file_id."""
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())
    logger.info("[update] start request_id=%s filename=%s", request_id, file.filename)
    allowed_extensions = {'.txt', '.pdf', '.docx', '.md'}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed_extensions}")

    # Find existing file by original filename
    file_id = vector_store.get_file_id_by_filename(file.filename)
    if not file_id:
        raise HTTPException(status_code=404, detail="Document not found; upload it first.")

    # Save temp content
    temp_path = f"temp_update_{file_id}{file_extension}"
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # If content unchanged (by hash), no-op
        new_hash = hashlib.sha256(content).hexdigest()
        existing = vector_store.document_registry.get(file_id)
        if existing and existing.get('content_hash') == new_hash:
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return {
                "file_id": file_id,
                "filename": file.filename,
                "status": "unchanged"
            }

        # Remove old vectors and original file
        logger.info("[update] deleting previous vectors/file for file_id=%s", file_id)
        vector_store.delete_document(file_id)

        # Re-process content
        print(f"📄 Updating file: {file.filename}")
        t_extract = time.perf_counter()
        text_content = file_processor.extract_text(temp_path)
        logger.info("[update] extracted text request_id=%s file_id=%s chars=%s elapsed_ms=%d", request_id, file_id, len(text_content), int((time.perf_counter()-t_extract)*1000))

        print("✂️ Chunking text...")
        t_chunk = time.perf_counter()
        chunks = chunker.chunk(text_content)
        logger.info("[update] chunked text request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunks), int((time.perf_counter()-t_chunk)*1000))

        print(f"🧠 Generating embeddings for {len(chunks)} chunks...")
        t_embed = time.perf_counter()
        embeddings = embedder.encode(chunks)
        logger.info("[update] embeddings generated request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunks), int((time.perf_counter()-t_embed)*1000))

        print("💾 Storing in vector database...")
        t_store = time.perf_counter()
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{file_id}_chunk_{i}"
            metadata = {
                "file_id": file_id,
                "filename": file.filename,
                "chunk_index": i,
                "chunk_text": chunk,
                "file_type": file_extension,
                "upload_time": start_time.isoformat()
            }
            vector_store.add_chunk(chunk_id, embedding, metadata)
        logger.info("[update] stored chunks request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunks), int((time.perf_counter()-t_store)*1000))

        # Update registry
        vector_store.register_document(
            file_id=file_id,
            filename=file.filename,
            file_type=file_extension,
            content_hash=new_hash,
            upload_time=start_time.isoformat()
        )

        # Save store
        try:
            vector_store.save()
        except Exception as save_err:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.exception("[update] failed to save vector store request_id=%s file_id=%s error=%s", request_id, file_id, str(save_err))
            raise HTTPException(status_code=500, detail=f"Update failed: {str(save_err)}")

        # Persist updated original file ONLY after success
        try:
            dest_filename = f"{file_id}{file_extension}"
            dest_path = os.path.join(config.documents_path, dest_filename)
            shutil.copyfile(temp_path, dest_path)
        finally:
            # Cleanup temp
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return {
            "file_id": file_id,
            "filename": file.filename,
            "chunks_updated": len(chunks),
            "status": "updated"
        }

    except HTTPException:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.exception("[update] failed request_id=%s filename=%s error=%s", request_id, file.filename, str(e))
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@app.put("/documents/{file_id}")
async def update_document_by_id(file_id: str, file: UploadFile = File(...)):
    """Update an existing document by file_id, preserving file_id."""
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())
    logger.info("[updateById] start request_id=%s file_id=%s filename=%s", request_id, file_id, file.filename)
    allowed_extensions = {'.txt', '.pdf', '.docx', '.md'}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed_extensions}")

    # Ensure file_id exists
    if file_id not in vector_store.document_registry:
        raise HTTPException(status_code=404, detail="Document not found; upload it first.")

    temp_path = f"temp_update_{file_id}{file_extension}"
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        new_hash = hashlib.sha256(content).hexdigest()
        existing = vector_store.document_registry.get(file_id)
        if existing and existing.get('content_hash') == new_hash:
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return {
                "file_id": file_id,
                "filename": file.filename,
                "status": "unchanged"
            }

        logger.info("[updateById] deleting previous vectors/file for file_id=%s", file_id)
        vector_store.delete_document(file_id)

        print(f"📄 Updating file (by id): {file.filename}")
        t_extract = time.perf_counter()
        text_content = file_processor.extract_text(temp_path)
        logger.info("[updateById] extracted text request_id=%s file_id=%s chars=%s elapsed_ms=%d", request_id, file_id, len(text_content), int((time.perf_counter()-t_extract)*1000))

        print("✂️ Chunking text...")
        t_chunk = time.perf_counter()
        chunks = chunker.chunk(text_content)
        logger.info("[updateById] chunked text request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunks), int((time.perf_counter()-t_chunk)*1000))

        print(f"🧠 Generating embeddings for {len(chunks)} chunks...")
        t_embed = time.perf_counter()
        embeddings = embedder.encode(chunks)
        logger.info("[updateById] embeddings generated request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunks), int((time.perf_counter()-t_embed)*1000))

        print("💾 Storing in vector database...")
        t_store = time.perf_counter()
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{file_id}_chunk_{i}"
            metadata = {
                "file_id": file_id,
                "filename": file.filename,
                "chunk_index": i,
                "chunk_text": chunk,
                "file_type": file_extension,
                "upload_time": start_time.isoformat()
            }
            vector_store.add_chunk(chunk_id, embedding, metadata)
        logger.info("[updateById] stored chunks request_id=%s file_id=%s chunks=%d elapsed_ms=%d", request_id, file_id, len(chunks), int((time.perf_counter()-t_store)*1000))

        vector_store.register_document(
            file_id=file_id,
            filename=file.filename,
            file_type=file_extension,
            content_hash=new_hash,
            upload_time=start_time.isoformat()
        )

        try:
            vector_store.save()
        except Exception as save_err:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.exception("[updateById] failed to save vector store request_id=%s file_id=%s error=%s", request_id, file_id, str(save_err))
            raise HTTPException(status_code=500, detail=f"Update failed: {str(save_err)}")

        # Persist updated original file ONLY after success
        try:
            dest_filename = f"{file_id}{file_extension}"
            dest_path = os.path.join(config.documents_path, dest_filename)
            shutil.copyfile(temp_path, dest_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return {
            "file_id": file_id,
            "filename": file.filename,
            "chunks_updated": len(chunks),
            "status": "updated"
        }

    except HTTPException:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.exception("[updateById] failed request_id=%s file_id=%s filename=%s error=%s", request_id, file_id, file.filename, str(e))
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = vector_store.list_documents()
        return {
            "documents": documents,
            "total_count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.post("/reset")
async def reset_store(remove_originals: bool = True):
    """Clear all vectors, metadata, registry, and optionally originals in data/documents."""
    try:
        result = vector_store.clear_all(remove_documents=remove_originals)
        # Persist empty store after reset
        vector_store.save()
        return {"status": "reset", **result}
    except Exception as e:
        logger.exception("[reset] failed error=%s", str(e))
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
