# Tóm Tắt Công Nghệ và Chức Năng Dự Án RAG System

## 1. Tổng Quan Dự Án

Hệ thống RAG (Retrieval-Augmented Generation) là một ứng dụng AI thông minh cho phép người dùng tương tác với các tài liệu thông qua chatbot. Hệ thống có khả năng xử lý, phân tích và trả lời câu hỏi dựa trên nội dung của các tài liệu đã được tải lên.

## 2. Kiến Trúc Hệ Thống

### 2.1 Kiến Trúc các service
- **Backend API**: FastAPI Python
- **Xử lý bất đồng bộ**: RabbitMQ message queue
- **Cơ sở dữ liệu chính**: PostgreSQL
- **Vector Database**: Qdrant
- **File Storage**: MinIO (S3-compatible)
- **Container hóa**: Docker & Docker Compose

### 2.2 Mô Hình Dữ Liệu
```
User → Project → Document → DocumentChunk
     ↓
   Chat → Message
```

## 3. Stack Công Nghệ

### 3.1 Backend Framework
- **FastAPI**: Web framework hiện đại, hiệu suất cao
- **Python 3.12**: Ngôn ngữ lập trình chính
- **SQLAlchemy**: ORM cho database operations
- **Alembic**: Database migration tool

### 3.2 Cơ Sở Dữ Liệu
- **PostgreSQL 17**: Cơ sở dữ liệu quan hệ chính
- **Qdrant**: Vector database cho semantic search
- **pgvector**: Vector extension cho PostgreSQL

### 3.3 Message Queue & Async Processing
- **RabbitMQ**: Message broker cho xử lý bất đồng bộ
- **Pika**: Python client cho RabbitMQ

### 3.4 AI/ML Components
- **Sentence Transformers**: Text embedding models
- **OpenAI API**: Large Language Models
- **Google Gemini API**: Alternative LLM provider
- **Ollama**: Local LLM support
- **Transformers**: Hugging Face transformers library

### 3.5 File Processing
- **MarkItDown**: Document conversion to Markdown
- **Beautiful Soup**: HTML parsing
- **python-pptx**: PowerPoint processing
- **pdfminer.six**: PDF text extraction
- **mammoth**: Word document processing

### 3.6 Storage & Infrastructure
- **MinIO**: S3-compatible object storage
- **Boto3**: AWS/S3 client
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

### 3.7 Security & Authentication
- **JWT**: Token-based authentication
- **bcrypt**: Password hashing
- **python-jose**: JWT handling

## 4. Chức Năng Chính

### 4.1 Quản Lý Người Dùng & Dự Án
- Đăng ký/đăng nhập người dùng
- Tạo và quản lý projects
- Hệ thống phân quyền (permissions)
- Chia sẻ projects giữa users

### 4.2 Xử Lý Tài Liệu
- **Upload đa định dạng**: PDF, DOCX, PPTX, HTML, TXT
- **Xử lý bất đồng bộ**: RabbitMQ queue system
- **Conversion pipeline**: Convert sang Markdown
- **Text chunking**: Chia nhỏ document thành chunks
- **Vector embedding**: Tạo embeddings cho semantic search
- **Storage**: Lưu trữ permanent trên MinIO

### 4.3 RAG (Retrieval-Augmented Generation)
- **Semantic search**: Tìm kiếm relevant chunks
- **Context retrieval**: Lấy context từ documents
- **LLM integration**: Multiple LLM providers
- **Citation system**: Trích dẫn nguồn trong responses
- **Query enrichment**: Cải thiện câu hỏi của user

### 4.4 Chat System
- **Multi-turn conversations**: Hỗ trợ đối thoại nhiều lượt
- **Project-scoped chats**: Chat trong phạm vi project
- **Message history**: Lưu trữ lịch sử chat
- **Context-aware responses**: Responses dựa trên context

## 5. Quy Trình Hoạt Động

### 5.1 Document Processing Workflow
```
Upload → Validation → Queue → Processing → Chunking → Embedding → Storage → Ready for RAG
```

### 5.2 Chat/Query Workflow
```
User Query → RAG Decision → Vector Search → Context Retrieval → LLM Processing → Response Generation
```

## 6. Tích Hợp AI/ML

### 6.1 Embedding Models
- **all-MiniLM-L6-v2**: Default embedding model (384 dimensions)
- **Sentence Transformers**: Framework cho text embeddings

### 6.2 Large Language Models
- **OpenAI GPT**: GPT-3.5-turbo, GPT-4
- **Google Gemini**: Gemini-pro
- **Ollama**: Local LLM deployment (Llama, Mistral, etc.)

### 6.3 Prompt Engineering
- **Template system**: Mustache templates
- **Multi-purpose prompts**: RAG answer, normal answer, query enrichment
- **Context injection**: Động thái inject context vào prompts

## 7. Hiệu Suất & Scalability

### 7.1 Async Processing
- **Non-blocking uploads**: API trả về ngay lập tức
- **Background processing**: RabbitMQ workers
- **Status tracking**: Real-time progress monitoring

### 7.2 Caching & Optimization
- **Vector indexing**: Qdrant HNSW indexing
- **Chunk optimization**: Intelligent text chunking
- **Connection pooling**: Database connection management

## 8. Monitoring & Testing

### 8.1 API Documentation
- **OpenAPI/Swagger**: Auto-generated API docs
- **Comprehensive endpoints**: Full CRUD operations

### 8.2 Testing Framework
- **pytest**: Unit và integration testing
- **Test coverage**: CRUD operations, chunking logic

## 9. Deployment & DevOps

### 9.1 Containerization
- **Multi-service docker-compose**: PostgreSQL, RabbitMQ, Qdrant, MinIO
- **Volume persistence**: Data persistence across restarts
- **Network isolation**: Secure service communication

### 9.2 Configuration Management
- **Environment-based config**: Development, Testing, Production
- **Secret management**: Environment variables
- **Multi-environment support**: Flexible deployment

## 10. Lợi Ích Kinh Doanh

### 10.1 Tăng Hiệu Quả Làm Việc
- Tìm kiếm thông tin nhanh chóng trong documents
- Trả lời tự động các câu hỏi phổ biến
- Giảm thời gian đọc và phân tích tài liệu

### 10.2 Scalability
- Xử lý đồng thời nhiều documents
- Hỗ trợ multiple users và projects
- Elastic scaling với container orchestration

### 10.3 Knowledge Management
- Tập trung hóa knowledge base
- Semantic search thông minh
- Version control cho documents

## 11. Roadmap Kỹ Thuật

### 11.1 Current Capabilities
- ✅ Multi-format document processing
- ✅ Async workflow with RabbitMQ
- ✅ Multiple LLM provider support
- ✅ Vector-based semantic search
- ✅ User management & permissions

### 11.2 Potential Enhancements
- **Advanced chunking strategies**: Semantic chunking
- **Multi-modal support**: Images, audio
- **Real-time collaboration**: WebSocket support
- **Advanced analytics**: Usage analytics, performance metrics
- **API rate limiting**: Enhanced security features

---

*Tài liệu này cung cấp cái nhìn tổng quan về kiến trúc và công nghệ của hệ thống RAG, phục vụ cho việc báo cáo lên cấp trên và đánh giá kỹ thuật.*
