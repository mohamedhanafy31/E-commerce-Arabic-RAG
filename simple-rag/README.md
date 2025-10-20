<<<<<<< HEAD

# E-commerce-Arabic-RAG

=======

# Simple Arabic RAG System

A streamlined Arabic Retrieval-Augmented Generation (RAG) system with core functionality: file upload, text chunking, embedding generation, vector retrieval, and text generation using Ollama or Gemini.

## 🚀 Features

- **File Upload**: Support for TXT, PDF, DOCX, and Markdown files
- **Arabic Text Chunking**: Intelligent text segmentation respecting Arabic sentence boundaries
- **Embedding Generation**: Arabic-aware embeddings using NAMAA-Space/AraModernBert-Base-V1.0
- **Vector Search**: FAISS-based similarity search
- **Dual Generation**: Choose between Ollama (local) or Gemini (cloud) for text generation
- **RESTful API**: Simple FastAPI-based interface

## 📋 Requirements

- Python 3.8+
- Ollama (for local generation) or Gemini API key (for cloud generation)
- 4GB+ RAM recommended
- GPU optional but recommended for faster embeddings

## 🛠️ Installation

1. **Clone and navigate to the project:**

```bash
cd simple-rag
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Set up environment:**

```bash
cp env.example .env
# Edit .env with your configuration
```

4. **Install Ollama (optional, for local generation):**

```bash
# Install Ollama from https://ollama.ai
# Pull the Arabic model:
ollama pull gemma3:12b
```

## ⚙️ Configuration

Edit `.env` file with your settings:

```env
# Choose generation model
GENERATION_MODEL=ollama  # or "gemini"

# Ollama settings
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:12b

# Gemini settings (if using Gemini)
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Embedding model
EMBEDDING_MODEL=NAMAA-Space/AraModernBert-Base-V1.0
```

## 🚀 Usage

1. **Start the server:**

```bash
python main.py
```

2. **Upload documents:**

```bash
curl -X POST "http://localhost:8000/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

3. **Query documents:**

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "ما هو موضوع هذا المستند؟",
       "max_results": 5,
       "model_choice": "ollama"
     }'
```

## 📚 API Endpoints

### Upload Document

- **POST** `/upload`
- Upload and process a document
- Supported formats: TXT, PDF, DOCX, MD

### Query Documents

- **POST** `/query`
- Query uploaded documents
- Parameters:
  - `query`: Arabic text query
  - `max_results`: Number of results (default: 5)
  - `model_choice`: "ollama" or "gemini"

### System Information

- **GET** `/` - System info
- **GET** `/health` - Health check
- **GET** `/stats` - System statistics
- **GET** `/documents` - List uploaded documents

### Document Management

- **DELETE** `/documents/{file_id}` - Delete a document

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │───▶│   Text Chunking │───▶│   Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Generation    │◀───│   Vector Store  │◀───│   FAISS Index   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Core Components

### 1. File Processor (`core/file_processor.py`)

- Extracts text from various file formats
- Handles encoding issues
- Validates file types and sizes

### 2. Text Chunker (`core/chunker.py`)

- Arabic-aware text segmentation
- Respects sentence boundaries
- Configurable chunk size and overlap

### 3. Embeddings (`core/embeddings.py`)

- Arabic BERT-based embeddings
- Batch processing support
- Similarity calculations

### 4. Vector Store (`core/vector_store.py`)

- FAISS-based vector database
- Metadata storage
- Similarity search

### 5. Generator (`core/generator.py`)

- Dual model support (Ollama/Gemini)
- Arabic prompt engineering
- Error handling and fallbacks

## 📊 Example Usage

### Upload a document:

```python
import requests

with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
    print(response.json())
```

### Query documents:

```python
import requests

query_data = {
    "query": "ما هي النقاط الرئيسية في هذا المستند؟",
    "max_results": 3,
    "model_choice": "ollama"
}

response = requests.post(
    "http://localhost:8000/query",
    json=query_data
)
print(response.json())
```

## 🐳 Docker Support

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t simple-rag .
docker run -p 8000:8000 simple-rag
```

## 🔍 Troubleshooting

### Common Issues:

1. **Embedding model download fails:**

   - Check internet connection
   - Ensure sufficient disk space
   - Try running with `--no-cache-dir` flag
2. **Ollama not responding:**

   - Check if Ollama is running: `ollama list`
   - Verify the model is installed: `ollama pull gemma3:12b`
3. **Gemini API errors:**

   - Verify API key is correct
   - Check API quotas and limits
   - Ensure model name is valid
4. **Memory issues:**

   - Reduce chunk size
   - Use CPU-only FAISS
   - Process smaller files

## 📈 Performance Tips

- Use GPU for faster embeddings
- Adjust chunk size based on your content
- Use Ollama for privacy-sensitive data
- Use Gemini for better Arabic quality
- Implement caching for repeated queries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- NAMAA-Space for the Arabic BERT model
- Ollama team for local LLM support
- Google for Gemini API
- FAISS team for vector search
- FastAPI team for the web framework

>>>>>>> 7954346 (full project)
>>>>>>>
>>>>>>
>>>>>
>>>>
>>>
>>
# E-commerce-Arabic-RAG
