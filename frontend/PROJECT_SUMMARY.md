# Tóm Tắt Dự Án RAG (Retrieval-Augmented Generation) - Frontend

## Tổng Quan Dự Án

Đây là dự án luận văn phát triển hệ thống **RAG (Retrieval-Augmented Generation)** - một ứng dụng web cho phép người dùng tải lên tài liệu, tạo dự án, và thực hiện trò chuyện AI với khả năng truy xuất thông tin từ cơ sở tri thức được xây dựng từ các tài liệu đã tải lên.

## Công Nghệ Sử Dụng

### Frontend Technologies
- **Next.js 15.2.4** - React framework chính
- **React 18.3.1** - Thư viện UI
- **TypeScript 5** - Ngôn ngữ lập trình
- **Tailwind CSS 3.3.0** - Framework CSS utility-first
- **Radix UI** - Component library (accordion, dialog, popover, tabs, toast, tooltip...)

### UI/UX Libraries
- **shadcn/ui** - Modern component system
- **Lucide React** - Icon library
- **React Icons** - Additional icons
- **class-variance-authority** - Dynamic className management
- **tailwindcss-animate** - Animation utilities

### Form & File Handling
- **React Dropzone** - File upload với drag & drop
- **React File Icon** - Hiển thị icon file theo loại

### Chat & AI Integration
- **Vercel AI SDK (ai 4.0.1)** - Tích hợp AI/LLM
- **React Markdown** - Render markdown trong chat
- **rehype-highlight** - Syntax highlighting cho code
- **remark-gfm** - GitHub Flavored Markdown support

### State Management & Utils
- **date-fns** - Xử lý ngày tháng
- **clsx & tailwind-merge** - Conditional styling

## Kiến Trúc Hệ Thống

### 1. Authentication & Authorization
- **JWT Token-based authentication**
- **Middleware protection** cho các route private
- **Auto-redirect** khi token hết hạn
- **Cookie & localStorage** management

### 2. Modular Architecture
```
src/
├── app/                    # Next.js App Router
├── components/             # Reusable UI components
├── contexts/              # React Context providers
├── lib/                   # Utility libraries
├── modules/               # Feature-based modules
├── styles/                # Global styles
├── types/                 # TypeScript definitions
└── utils/                 # Shared utilities
```

### 3. API Integration
- **Custom API client** với error handling
- **Automatic token management**
- **Type-safe API calls**
- **File upload/download** support
- **Server-Side Events (SSE)** cho real-time chat

## Chức Năng Chính

### 1. Quản Lý Người Dùng
- **Đăng nhập/Đăng ký** với JWT authentication
- **Session management** tự động
- **Logout** với token cleanup

### 2. Quản Lý Dự Án
- **Tạo dự án mới** cho tổ chức tài liệu
- **Xem chi tiết dự án**
- **Xóa dự án** và tài liệu liên quan
- **Danh sách dự án** của người dùng

### 3. Quản Lý Tài Liệu
- **Upload tài liệu** với drag & drop interface
- **Preview tài liệu** trực tiếp trên web
- **Download tài liệu** đã upload
- **Theo dõi trạng thái** xử lý tài liệu
- **Danh sách tài liệu** theo dự án

### 4. Chat AI với RAG
- **Tạo cuộc trò chuyện mới** liên kết với dự án
- **Real-time streaming chat** với AI
- **Retrieval-Augmented Generation** từ cơ sở tri thức
- **Lịch sử chat** đầy đủ
- **Tìm kiếm chat** theo nội dung

### 5. Quản Lý API Keys
- **Tạo API key** cho external access
- **Bật/tắt API key** theo nhu cầu
- **Xóa API key** không còn sử dụng
- **Quản lý permissions** cho từng key

## Đặc Điểm Kỹ Thuật

### 1. Real-time Communication
- **Server-Sent Events (SSE)** cho streaming chat responses
- **Event-driven architecture** với các loại event:
  - `user_message_saved` - Tin nhắn người dùng đã lưu
  - `delta` - Chunks của response AI
  - `assistant_message_saved` - Response AI hoàn chỉnh
  - `error` - Xử lý lỗi
  - `stream_end` - Kết thúc stream

### 2. File Management
- **Multi-format support** cho tài liệu
- **Progress tracking** cho upload
- **Preview functionality** cho các loại file
- **Secure download** với authentication

### 3. Responsive Design
- **Mobile-first approach**
- **Dark/Light theme** support (next-themes)
- **Accessible components** với Radix UI
- **Modern gradient effects** và animations

### 4. Security
- **Route protection** với middleware
- **Token validation** tự động
- **CORS handling** cho API calls
- **Secure file operations**

## Backend Integration

### API Endpoints Chính
- `/api/auth/*` - Authentication services
- `/api/projects/*` - Project management
- `/api/documents/*` - Document operations
- `/api/chat/*` - Chat và RAG functionality
- `/api/api-keys/*` - API key management

### Data Flow
1. **Document Upload** → Vector embedding → Knowledge base
2. **Chat Query** → RAG retrieval → LLM generation → Streaming response
3. **Project Management** → Document organization → Access control

## Lợi Ích & Ứng Dụng

### 1. Doanh Nghiệp
- **Knowledge Management** hiệu quả
- **Q&A System** tự động từ tài liệu nội bộ
- **Document Intelligence** và search

### 2. Giáo Dục
- **Interactive Learning** với AI tutor
- **Document-based Q&A** cho học liệu
- **Research Assistant** thông minh

### 3. Cá Nhân
- **Personal Knowledge Base** từ tài liệu cá nhân
- **Smart Document Search** và truy xuất
- **AI Assistant** có context cụ thể

## Kế Hoạch Phát Triển

### Phase 1 (Hiện tại)
- ✅ Core RAG functionality
- ✅ Document management
- ✅ Real-time chat
- ✅ User authentication

### Phase 2 (Tương lai)
- 📋 Advanced search filters
- 📋 Collaborative features
- 📋 Analytics dashboard
- 📋 Mobile app

### Phase 3 (Mở rộng)
- 📋 Multi-language support
- 📋 Advanced AI models
- 📋 Enterprise features
- 📋 API marketplace

## Kết Luận

Dự án RAG này thể hiện sự kết hợp hiệu quả giữa các công nghệ frontend hiện đại với AI/LLM để tạo ra một hệ thống quản lý tri thức thông minh. Với kiến trúc modular, responsive design, và real-time capabilities, hệ thống có khả năng mở rộng cao và phù hợp cho nhiều use case khác nhau từ cá nhân đến doanh nghiệp.

**Công nghệ chính:** Next.js, TypeScript, Tailwind CSS, React, Radix UI, Vercel AI SDK  
**Tính năng nổi bật:** Real-time RAG chat, Document management, JWT authentication, Responsive design  
**Mục tiêu:** Xây dựng hệ thống knowledge management với AI assistant thông minh từ cơ sở tri thức tùy chỉnh
