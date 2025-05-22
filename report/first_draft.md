Tuyệt vời! Dựa trên file giới thiệu đề tài, tổng quan kiến trúc backend bạn cung cấp và mục lục tham khảo, tôi đã xây dựng một kế hoạch chi tiết (dưới dạng mục lục) cho báo cáo khóa luận của bạn. Mục lục này cố gắng bao quát đầy đủ các khía cạnh, logic và có tính học thuật cao.

**BÁO CÁO KHÓA LUẬN TỐT NGHIỆP**

**Tên đề tài: Xây dựng hệ thống hỏi đáp tài liệu tự động cho dự án phần mềm**

---

**MỤC LỤC CHI TIẾT**

**Trang bìa**
**Trang phụ bìa**
**Lời cảm ơn**
**Tóm tắt đề tài (Tiếng Việt)**
**Abstract (Tiếng Anh)**
**Mục lục**
**Danh mục hình ảnh**
**Danh mục bảng biểu**
**Danh mục từ viết tắt**

---

**CHƯƠNG 1: MỞ ĐẦU**

1.1. Đặt vấn đề
    1.1.1. Bối cảnh và sự cần thiết của đề tài (Sự phát triển của LLMs, nhu cầu quản lý tri thức dự án)
    1.1.2. Các vấn đề tồn tại trong việc tra cứu thông tin dự án phần mềm hiện nay
    1.1.3. Giải pháp đề xuất: Hệ thống hỏi đáp tài liệu tự động
1.2. Mục tiêu của đề tài
    1.2.1. Mục tiêu tổng quát
    1.2.2. Mục tiêu cụ thể (Dựa trên "Mục tiêu của đề tài" trong file giới thiệu)
1.3. Đối tượng và phạm vi nghiên cứu
    1.3.1. Đối tượng nghiên cứu (Tài liệu dự án, cơ sở dữ liệu dự án, LLMs, kỹ thuật RAG)
    1.3.2. Phạm vi nghiên cứu (Dựa trên "Phạm vi" trong file giới thiệu: Quản lý người dùng, Bot Hỏi Đáp, Kho Tài Liệu, Tìm kiếm thông minh, Ứng dụng LLM, Tích hợp RAG, Tối ưu hóa prompt)
1.4. Phương pháp nghiên cứu
    1.4.1. Phương pháp nghiên cứu lý thuyết
    1.4.2. Phương pháp thực nghiệm và phát triển hệ thống
    1.4.3. Phương pháp đánh giá
1.5. Ý nghĩa khoa học và thực tiễn của đề tài
    1.5.1. Ý nghĩa khoa học (Đóng góp vào việc ứng dụng LLM, RAG trong lĩnh vực kỹ thuật phần mềm)
    1.5.2. Ý nghĩa thực tiễn (Tăng năng suất, tối ưu quy trình, cải thiện chất lượng dịch vụ cho doanh nghiệp)
1.6. Cấu trúc của luận văn

**CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ TỔNG QUAN CÔNG NGHỆ**

2.1. Tổng quan về Mô hình Ngôn ngữ Lớn (Large Language Models - LLMs)
    2.1.1. Khái niệm và kiến trúc cơ bản của LLMs
    2.1.2. Các loại LLMs phổ biến và ứng dụng (Đề cập Llama3, Qwen, GPT-4o, Gemini 1.5 như trong đề cương)
    2.1.3. Embedding Models (Ví dụ: Sentence Transformers)
        2.1.3.1. Khái niệm và vai trò của embedding
        2.1.3.2. Các mô hình embedding phổ biến
2.2. Kỹ thuật Retrieval Augmented Generation (RAG)
    2.2.1. Khái niệm và kiến trúc của RAG
    2.2.2. Quy trình hoạt động của RAG
    2.2.3. Ưu điểm và nhược điểm của RAG
    2.2.4. Các biến thể của RAG (Nếu có nghiên cứu sâu hơn)
2.3. Vector Database
    2.3.1. Khái niệm và vai trò của Vector Database trong RAG
    2.3.2. Giới thiệu Qdrant: Kiến trúc, tính năng và lý do lựa chọn
    2.3.3. So sánh với các Vector Database khác (Weaviate, Atlas vector database - nếu có khảo sát)
2.4. Xử lý Ngôn ngữ Tự nhiên cho Truy vấn Cơ sở dữ liệu (Text-to-SQL)
    2.4.1. Khái niệm và tầm quan trọng
    2.4.2. Các phương pháp tiếp cận Text-to-SQL sử dụng LLM
2.5. Kỹ thuật Tối ưu hóa Prompt (Prompt Engineering)
    2.5.1. Khái niệm và vai trò
    2.5.2. Các kỹ thuật tối ưu hóa prompt phổ biến
2.6. Các công nghệ và framework sử dụng trong đề tài
    2.6.1. Backend
        2.6.1.1. Python và FastAPI (Lý do lựa chọn, ưu điểm)
        2.6.1.2. Uvicorn (ASGI Server)
        2.6.1.3. SQLAlchemy (ORM cho PostgreSQL) và Alembic (Database Migrations)
        2.6.1.4. Pydantic (Data Validation)
    2.6.2. Cơ sở dữ liệu
        2.6.2.1. PostgreSQL (Lưu trữ dữ liệu quan hệ: người dùng, dự án, tài liệu, chunk metadata, chat)
        2.6.2.2. Qdrant (Lưu trữ vector embeddings)
    2.6.3. Xử lý bất đồng bộ
        2.6.3.1. RabbitMQ (Message Broker)
        2.6.3.2. Document Consumer
    2.6.4. Lưu trữ file và xử lý tài liệu
        2.6.4.1. MinIO (hoặc Local File System)
        2.6.4.2. MarkItDown (Chuyển đổi tài liệu sang Markdown)
    2.6.5. Tích hợp LLM
        2.6.5.1. OpenAI SDK (Cho OpenAI models và Gemini qua API tương thích)
        2.6.5.2. Custom OllamaClient (Cho các mô hình Ollama cục bộ)
        2.6.5.3. LLMFactory và LLMService (Abstraction Layer)
    2.6.6. Xác thực và Phân quyền
        2.6.6.1. JWT (JSON Web Tokens)
        2.6.6.2. `python-jose`, `bcrypt`
    2.6.7. Frontend: NextJs
    2.6.8. Các thư viện hỗ trợ khác (OpenAI SDK)
    
2.7. Tổng quan các nghiên cứu liên quan (Related Work)
    2.7.1. Các hệ thống hỏi đáp tài liệu hiện có
    2.7.2. Các nghiên cứu về ứng dụng RAG trong quản lý tri thức
    2.7.3. Các giải pháp Text-to-SQL sử dụng LLM

**CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG**

3.1. Phân tích yêu cầu
    3.1.1. Yêu cầu chức năng (Dựa trên "Phạm vi" và "Mục tiêu" trong đề cương)
        3.1.1.1. Quản lý người dùng và phân quyền
        3.1.1.2. Quản lý dự án và tài liệu dự án (upload, tóm tắt, lưu trữ, xem trước)
        3.1.1.3. Hệ thống hỏi đáp dựa trên tài liệu (RAG)
        3.1.1.5. Tìm kiếm thông minh (theo chủ đề, từ khóa, thẻ, ngày đăng)
        3.1.1.6. Hỗ trợ tối ưu hóa prompt cho người dùng
    3.1.2. Yêu cầu phi chức năng
        3.1.2.1. Tính chính xác và nhất quán của thông tin
        3.1.2.2. Hiệu năng và tốc độ phản hồi
        3.1.2.3. Khả năng mở rộng
        3.1.2.4. Tính bảo mật
        3.1.2.5. Tính dễ sử dụng

3.3. Thiết kế kiến trúc tổng quan hệ thống
    3.3.1. Sơ đồ kiến trúc (Dựa trên "Tổng quan hệ thống (backend)" bạn cung cấp)
    3.3.2. Mô tả các thành phần chính và tương tác
        3.3.2.2. API Xử lý Tài liệu (Document Processing Service - Consumer)
        3.3.2.3. API ice Hỏi Đáp (Q&A Service - RAG Logic)
3.4. Thiết kế Module chi tiết
    3.4.1. Module Backend
        3.4.1.1. Thiết kế API Endpoints
        3.4.1.2. Luồng xử lý tải lên và tiền xử lý tài liệu (Upload & Async Processing Flow)
        3.4.1.3. Luồng xử lý hỏi đáp RAG (Chat & RAG Flow)
        3.4.1.5. Thiết kế cơ chế Prompt Engineering và tối ưu hóa
    3.4.2. Module Frontend (Nếu có - Sơ đồ các màn hình chính, luồng tương tác người dùng)
3.5. Thiết kế cơ sở dữ liệu
    3.5.1. Thiết kế cơ sở dữ liệu quan hệ (PostgreSQL)
        3.5.1.1. Sơ đồ quan hệ thực thể (ERD)
        3.5.1.2. Mô tả chi tiết các bảng (users, projects, documents, document_chunks_metadata, chat_sessions, messages, permissions, etc.)
    3.5.2. Thiết kế cơ sở dữ liệu vector (Qdrant)
        3.5.2.1. Cấu trúc collection (tên, vector params, payload schema)
        3.5.2.2. Chiến lược indexing và searching
3.6. Thiết kế AI Agent trong hệ thống
    3.6.1. Logic ra quyết định của Agent (Khi nào dùng RAG, khi nào không)
    3.6.2. Cách Agent xây dựng prompt dựa trên ngữ cảnh và dữ liệu truy xuất
3.7. Thiết kế quy trình xử lý tài liệu
    3.7.1. Chuyển đổi định dạng tài liệu (MarkItDown)
    3.7.2. Phân đoạn văn bản (Chunking Strategy)
    3.7.3. Tạo vector embedding và lưu trữ

**CHƯƠNG 4: TRIỂN KHAI HỆ THỐNG**

4.1. Môi trường cài đặt và phát triển
    4.1.1. Phần cứng và phần mềm sử dụng
    4.1.2. Cài đặt các công cụ và thư viện
4.2. Triển khai Backend
    4.2.1. Xây dựng API với FastAPI (Mô tả một số API quan trọng)
    4.2.2. Triển khai module xử lý tài liệu và RabbitMQ consumer
        4.2.2.1. Tích hợp MinIO/Local Storage
        4.2.2.2. Logic chuyển đổi, chunking, embedding
    4.2.3. Triển khai module hỏi đáp RAG
        4.2.3.1. Tích hợp Qdrant client
        4.2.3.2. Logic truy xuất ngữ cảnh và sinh câu trả lời
    4.2.4. Tích hợp các LLM (OpenAI, Gemini, Ollama) thông qua LLMFactory
    4.2.5. Triển khai module xác thực và phân quyền (JWT, RBAC)
    4.2.6. Triển khai cơ sở dữ liệu PostgreSQL và Qdrant
4.3. Triển khai Frontend (Nếu có)
    4.3.1. Xây dựng giao diện người dùng (Mô tả các màn hình chính đã triển khai)
    4.3.2. Tích hợp API với Backend
4.4. Triển khai quy trình Text-to-SQL (Nếu có)
4.5. Một số giải thuật và đoạn mã nổi bật
    4.5.1. Giải thuật phân đoạn văn bản (Chunking)
    4.5.2. Giải thuật xây dựng prompt động cho RAG
    4.5.3. Cách xử lý streaming response từ LLM
4.6. Các thách thức gặp phải và giải pháp trong quá trình triển khai

**CHƯƠNG 5: KIỂM THỬ VÀ ĐÁNH GIÁ HỆ THỐNG**

5.1. Mục tiêu và chiến lược kiểm thử
    5.1.1. Mục tiêu kiểm thử (Đảm bảo tính đúng đắn, hiệu năng, độ tin cậy)
    5.1.2. Chiến lược kiểm thử (Unit test, Integration test, System test, User Acceptance Test)
5.2. Môi trường và dữ liệu kiểm thử
    5.2.1. Thiết lập môi trường kiểm thử
    5.2.2. Chuẩn bị bộ dữ liệu kiểm thử (Tài liệu mẫu, câu hỏi mẫu, kịch bản cơ sở dữ liệu)
5.3. Các kịch bản kiểm thử (Test Cases)
    5.3.1. Kiểm thử chức năng (User Management, Document Upload, RAG Q&A, Text-to-SQL, Search)
    5.3.2. Kiểm thử phi chức năng (Performance, Security)
5.4. Đánh giá hiệu quả của hệ thống
    5.4.1. Đánh giá chất lượng câu trả lời của hệ thống RAG
        5.4.1.1. Các độ đo (Metrics): Độ chính xác (Accuracy), Độ liên quan (Relevance), Độ mạch lạc (Coherence), BLEU, ROUGE (nếu phù hợp)
        5.4.1.2. Phương pháp đánh giá (Tự động, thủ công)
    5.4.2. Đánh giá hiệu quả của việc tối ưu hóa prompt
    5.4.3. Đánh giá khả năng xử lý câu hỏi phức tạp
    5.4.4. Đánh giá hiệu năng tìm kiếm thông tin
    5.4.5. So sánh kết quả với các mục tiêu đề ra ban đầu
5.5. Kết quả kiểm thử và phân tích
    5.5.1. Trình bày kết quả kiểm thử
    5.5.2. Phân tích, nhận xét về các kết quả đạt được
    5.5.3. Thảo luận về những điểm mạnh và điểm cần cải thiện của hệ thống

**CHƯƠNG 6: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN**

6.1. Kết quả đạt được
    6.1.1. Tóm tắt các chức năng chính đã hoàn thành
    6.1.2. Những đóng góp mới của đề tài (so với mục tiêu ban đầu)
6.2. Hạn chế của đề tài
    6.2.1. Các chức năng chưa hoàn thiện hoặc chưa tối ưu
    6.2.2. Những giới hạn về mặt công nghệ hoặc dữ liệu
6.3. Hướng phát triển trong tương lai
    6.3.1. Cải thiện độ chính xác và khả năng hiểu ngữ cảnh của LLM
    6.3.2. Mở rộng hỗ trợ đa dạng loại tài liệu và ngôn ngữ
    6.3.3. Phát triển thêm các tính năng nâng cao (VD: Phân tích cảm xúc, tự động sinh tài liệu)
    6.3.4. Tích hợp sâu hơn với các công cụ quản lý dự án và quy trình làm việc
    6.3.5. Tối ưu hóa hiệu năng và khả năng mở rộng cho quy mô lớn
    6.3.6. Nghiên cứu các kỹ thuật RAG tiên tiến hơn

---

**TÀI LIỆU THAM KHẢO** (Bao gồm các tài liệu [1]-[5] bạn đã liệt kê và các tài liệu khác)

**PHỤ LỤC** (Nếu có)
    Phụ lục A: Một số đoạn mã nguồn quan trọng
    Phụ lục B: Hướng dẫn cài đặt và sử dụng hệ thống
    Phụ lục C: Kết quả chi tiết các thử nghiệm

---

**Lưu ý:**

*   **Thời gian thực hiện:** Hãy đảm bảo các nội dung trong từng chương phù hợp với kế hoạch 12 tuần bạn đã đề ra.
*   **Cán bộ hướng dẫn:** Thường xuyên trao đổi với ThS. Hà Lê Hoài Trung để nhận được góp ý và định hướng kịp thời.
*   **Tính "hoàn chỉnh":** "Xây dựng hệ thống hỏi đáp tài liệu hoàn chỉnh" (Nội dung 5 trong đề cương) ngụ ý rằng cần có một giao diện người dùng nào đó, dù đơn giản (có thể dùng Streamlit cho mục đích demo nhanh chóng nếu không tập trung vào frontend phức tạp). Phần này cần được làm rõ trong báo cáo.
*   **Text2SQL:** Đây là một mục tiêu tham vọng. Nếu triển khai, cần được mô tả kỹ lưỡng. Nếu không, có thể đề cập là một hướng phát triển.

Chúc hai bạn Nguyễn Sỹ Lê Hoàng và Trần Ngọc Tố Như hoàn thành xuất sắc khóa luận này! Hy vọng mục lục chi tiết này sẽ giúp các bạn có một cấu trúc báo cáo rõ ràng và mạch lạc.