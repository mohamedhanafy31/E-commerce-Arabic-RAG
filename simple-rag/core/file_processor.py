"""
File Processing Module
Handles extraction of text from various file formats
"""

import os
from pathlib import Path
from typing import Optional
import mimetypes


class FileProcessor:
    """Handles text extraction from various file formats"""
    
    def __init__(self):
        self.supported_extensions = {'.txt', '.pdf', '.docx', '.md'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a file based on its extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            raise ValueError(f"File too large: {file_size} bytes (max: {self.max_file_size})")
        
        # Get file extension
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Extract text based on file type
        if file_extension == '.txt':
            return self._extract_txt(file_path)
        elif file_extension == '.pdf':
            return self._extract_pdf(file_path)
        elif file_extension == '.docx':
            return self._extract_docx(file_path)
        elif file_extension == '.md':
            return self._extract_md(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with different encodings
                encodings = ['latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            return f.read()
                    except UnicodeDecodeError:
                        continue
                
                # If all fail, read as binary and decode with errors='ignore'
                with open(file_path, 'rb') as f:
                    content = f.read()
                    return content.decode('utf-8', errors='ignore')
                    
            except Exception as e:
                raise ValueError(f"Failed to read text file: {e}")
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF processing. Install with: pip install PyPDF2")
        
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}")
    
    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
        
        try:
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {e}")
    
    def _extract_md(self, file_path: str) -> str:
        """Extract text from Markdown file"""
        # For now, treat MD files as plain text
        # In the future, you might want to strip markdown formatting
        return self._extract_txt(file_path)
    
    def get_file_info(self, file_path: str) -> dict:
        """Get information about a file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return {
            "filename": os.path.basename(file_path),
            "file_size": stat.st_size,
            "file_extension": Path(file_path).suffix.lower(),
            "mime_type": mime_type,
            "is_supported": Path(file_path).suffix.lower() in self.supported_extensions
        }
    
    def validate_file(self, file_path: str) -> bool:
        """Validate if a file can be processed"""
        try:
            info = self.get_file_info(file_path)
            return (
                info["is_supported"] and 
                info["file_size"] <= self.max_file_size
            )
        except Exception:
            return False
