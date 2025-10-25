"""
Unit Tests for RAG System
Tests all endpoints of the Simple Arabic RAG System
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the RAG system app
import sys
sys.path.append(str(Path(__file__).parent.parent / "simple-rag"))
from main import app

class TestRAGSystem:
    """Test suite for RAG System endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client for RAG system"""
        return TestClient(app)
    
    @pytest.fixture
    def test_document_content(self):
        """Test document content"""
        return """🏢 من نحن

نحن شركة الريادة للتجارة والتوزيع، مؤسسة رائدة في قطاع البيع بالتجزئة والجملة. تأسست شركتنا على يد مجموعة من رواد الأعمال الذين جمعهم هدف واحد: توفير منتجات عالية الجودة بأسعار مناسبة لكل فئات المجتمع.

على مدار سنوات عملنا، توسعنا من مجرد متجر محلي صغير إلى شبكة واسعة تضم عشرات الفروع ومراكز التوزيع في القاهرة، الإسكندرية، والدلتا، بالإضافة إلى تعاونات مع موردين عالميين."""

    # Core Information Endpoints
    
    def test_root_endpoint(self, client):
        """Test GET / endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Simple Arabic RAG System"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "endpoints" in data
        assert "upload" in data["endpoints"]
        assert "query" in data["endpoints"]
        assert "health" in data["endpoints"]
    
    def test_health_endpoint(self, client):
        """Test GET /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
        assert "embedder" in data["components"]
        assert "vector_store" in data["components"]
        assert "generator" in data["components"]
    
    def test_stats_endpoint(self, client):
        """Test GET /stats endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "embedder_model" in data
        assert "generation_model" in data
        assert "vector_store_path" in data

    # Document Management Endpoints
    
    def test_upload_document(self, client, test_document_content):
        """Test POST /upload endpoint"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(test_document_content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/upload",
                    files={"file": ("test_document.txt", f, "text/plain")}
                )
            
            assert response.status_code == 200
            
            data = response.json()
            assert "file_id" in data
            assert data["filename"] == "test_document.txt"
            assert data["chunks_created"] > 0
            assert data["processing_time_ms"] > 0
            assert data["status"] == "success"
            
            # Store file_id for other tests
            self.uploaded_file_id = data["file_id"]
            
        finally:
            os.unlink(temp_file.name)
    
    def test_upload_unsupported_file_type(self, client):
        """Test POST /upload with unsupported file type"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False)
        temp_file.write("test content")
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/upload",
                    files={"file": ("test.xyz", f, "application/octet-stream")}
                )
            
            assert response.status_code == 400
            assert "Unsupported file type" in response.json()["detail"]
            
        finally:
            os.unlink(temp_file.name)
    
    def test_list_documents(self, client):
        """Test GET /documents endpoint"""
        response = client.get("/documents")
        assert response.status_code == 200
        
        data = response.json()
        assert "documents" in data
        assert "total_count" in data
        assert isinstance(data["documents"], list)
        assert isinstance(data["total_count"], int)
    
    def test_query_documents(self, client):
        """Test POST /query endpoint"""
        query_data = {
            "query": "ما هو موضوع هذا المستند؟",
            "max_results": 5
        }
        
        response = client.post("/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "processing_time_ms" in data
        assert "model_used" in data
        assert isinstance(data["sources"], list)
    
    def test_query_with_general_conversation(self, client):
        """Test POST /query with general conversation"""
        query_data = {
            "query": "عامل إيه؟",
            "max_results": 5
        }
        
        response = client.post("/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert "الحمد لله" in data["answer"] or "بخير" in data["answer"]
        assert data["model_used"] == "kimo_general"
    
    def test_query_english(self, client):
        """Test POST /query with English query"""
        query_data = {
            "query": "What is the main topic of this document?",
            "max_results": 3
        }
        
        response = client.post("/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "processing_time_ms" in data
    
    def test_query_invalid_max_results(self, client):
        """Test POST /query with invalid max_results"""
        query_data = {
            "query": "test query",
            "max_results": -1
        }
        
        response = client.post("/query", json=query_data)
        # Should still work but with default max_results
        assert response.status_code == 200
    
    def test_update_document_by_filename(self, client, test_document_content):
        """Test PUT /documents endpoint"""
        # First upload a document
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(test_document_content)
        temp_file.close()
        
        try:
            # Upload document
            with open(temp_file.name, 'rb') as f:
                upload_response = client.post(
                    "/upload",
                    files={"file": ("update_test.txt", f, "text/plain")}
                )
            
            assert upload_response.status_code == 200
            
            # Update document
            updated_content = test_document_content + "\n\nتم تحديث المحتوى."
            temp_file2 = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file2.write(updated_content)
            temp_file2.close()
            
            try:
                with open(temp_file2.name, 'rb') as f:
                    response = client.put(
                        "/documents",
                        files={"file": ("update_test.txt", f, "text/plain")}
                    )
                
                assert response.status_code == 200
                data = response.json()
                assert "file_id" in data
                assert data["filename"] == "update_test.txt"
                assert data["status"] == "updated"
                
            finally:
                os.unlink(temp_file2.name)
                
        finally:
            os.unlink(temp_file.name)
    
    def test_delete_document_by_filename(self, client, test_document_content):
        """Test DELETE /documents endpoint"""
        # First upload a document
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(test_document_content)
        temp_file.close()
        
        try:
            # Upload document
            with open(temp_file.name, 'rb') as f:
                upload_response = client.post(
                    "/upload",
                    files={"file": ("delete_test.txt", f, "text/plain")}
                )
            
            assert upload_response.status_code == 200
            
            # Delete document
            delete_data = {"filename": "delete_test.txt"}
            response = client.delete("/documents", json=delete_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "file_id" in data
            assert data["filename"] == "delete_test.txt"
            assert data["status"] == "success"
            assert data["chunks_deleted"] > 0
            
        finally:
            os.unlink(temp_file.name)
    
    def test_delete_nonexistent_document(self, client):
        """Test DELETE /documents with nonexistent document"""
        delete_data = {"filename": "nonexistent.txt"}
        response = client.delete("/documents", json=delete_data)
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]
    
    def test_reset_store(self, client):
        """Test POST /reset endpoint"""
        response = client.post("/reset", params={"remove_originals": True})
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "reset"
        assert "documents_removed" in data
        assert "chunks_removed" in data
    
    def test_reset_store_keep_originals(self, client):
        """Test POST /reset endpoint keeping originals"""
        response = client.post("/reset", params={"remove_originals": False})
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "reset"
    
    # Web Interface Endpoints
    
    def test_manage_ui_endpoint(self, client):
        """Test GET /manage endpoint"""
        response = client.get("/manage")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
    
    def test_static_files(self, client):
        """Test GET /static/* endpoint"""
        # This will return 404 if no static files exist, which is expected
        response = client.get("/static/test.css")
        # Should either return the file or 404
        assert response.status_code in [200, 404]

    # Error Handling Tests
    
    def test_query_without_documents(self, client):
        """Test query when no documents are uploaded"""
        # Reset store first
        client.post("/reset")
        
        query_data = {
            "query": "ما هو موضوع هذا المستند؟",
            "max_results": 5
        }
        
        response = client.post("/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "معذرة" in data["answer"] or "مش لاقي" in data["answer"]
        assert data["model_used"] == "none"
    
    def test_invalid_query_format(self, client):
        """Test query with invalid format"""
        response = client.post("/query", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error
    
    def test_upload_empty_file(self, client):
        """Test upload of empty file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write("")  # Empty content
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/upload",
                    files={"file": ("empty.txt", f, "text/plain")}
                )
            
            # Should handle empty files gracefully
            assert response.status_code in [200, 400]
            
        finally:
            os.unlink(temp_file.name)

    # Performance Tests
    
    def test_query_performance(self, client):
        """Test query performance"""
        query_data = {
            "query": "ما هو موضوع هذا المستند؟",
            "max_results": 5
        }
        
        response = client.post("/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        # Processing time should be reasonable (less than 10 seconds)
        assert data["processing_time_ms"] < 10000
    
    def test_upload_performance(self, client, test_document_content):
        """Test upload performance"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(test_document_content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/upload",
                    files={"file": ("perf_test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 200
            
            data = response.json()
            # Processing time should be reasonable (less than 30 seconds)
            assert data["processing_time_ms"] < 30000
            
        finally:
            os.unlink(temp_file.name)
