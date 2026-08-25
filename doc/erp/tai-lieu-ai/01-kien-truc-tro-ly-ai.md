# Kiến trúc Trợ lý AI cho ERP DEGO

Phiên bản: 25/08/2026. Trạng thái: thiết kế nền, chưa code.
Tài liệu tóm tắt ở `doc/erp/02-dai-han.md` mục 3.7; đây là bản chi tiết kỹ thuật.

---

## 1. Mục tiêu và phạm vi

Xây một trợ lý hỏi - đáp bằng tiếng Việt cho ban lãnh đạo và nhà máy. Hai nhóm nhu cầu:

- Hỗ trợ lên kế hoạch, hiểu và tối ưu quy trình nhà máy (dựa trên gói tri thức biên soạn tay).
- Tra cứu dữ liệu và tra cứu văn bản trong hệ (hợp đồng, lịch sử mua, hướng dẫn sử dụng, quy trình).

Giai đoạn 1 chỉ mở cho ban lãnh đạo. Mở rộng cho nhân viên khi chi phí được tối ưu.

---

## 2. Nguyên tắc cốt tử - HAI loại câu hỏi, HAI công cụ

Đây là quyết định kiến trúc quan trọng nhất. Mọi câu hỏi rơi vào một trong hai loại,
xử lý bằng hai cơ chế khác nhau. Không được lẫn.

| | Loại A - dữ liệu CÓ CẤU TRÚC | Loại B - văn bản TỰ DO |
|---|---|---|
| Ví dụ | "HĐ với NCC nào còn hạn, hết hạn bao nhiêu", "mã A giá tốt nhất, đã mua của ai" | "quy trình nghiệm thu mấy bước", "điều khoản phạt trong HĐ nói gì" |
| Nguồn | Bảng nghiệp vụ (`contract`, `purchase_history`, ...) | Bài viết HDSD, quy trình, nội dung văn bản |
| Công cụ | Gọi API truy vấn có sẵn (tool use) | Tìm trong kho vector Qdrant (RAG) |
| Vector hóa | KHÔNG | CÓ |
| Phân quyền | Tự đúng vì API đã gác `apply_scope` | Gắn nhãn quyền vào từng đoạn (chunk) |

Lý do KHÔNG vector hóa dữ liệu loại A:

1. Vector tìm theo "gần nghĩa", không lọc - tính - tổng hợp chính xác được. Hỏi "HĐ nào hết
   hạn trước 31/12" mà đi so cosine thì bỏ sót và bịa số.
2. Số liệu động (đơn gần nhất, giá thấp nhất) đổi mỗi ngày. Vector đã lưu là ảnh chụp cũ,
   trả lời sai mà người hỏi không biết.
3. Snapshot vector mất lớp phân quyền `apply_scope`.

Kết luận: dữ liệu số liệu luôn gọi API đọc bảng gốc để có số mới nhất và đúng quyền.
Vector chỉ dùng cho văn bản (loại B).

Đã loại bỏ (25/08/2026): phương án worker "biến số liệu hằng ngày thành vector rồi lưu".
Nếu về sau truy vấn nào quá nặng thì tối ưu bằng bảng tổng hợp - materialized view - cache
(vẫn là dữ liệu có cấu trúc, tính lại được, gác quyền được), KHÔNG bằng vector.

---

## 3. Kiến trúc tổng thể - trợ lý LAI có điều phối

```
  Người dùng (câu hỏi tiếng Việt)
        |
        v
  [ Bộ điều phối - Claude API ]   <-- file định nghĩa (system prompt + gói tri thức)
        |
        |-- Câu hỏi số liệu (A) --> gọi TOOL --> API truy vấn có sẵn (gác apply_scope)
        |                                             |
        |-- Câu hỏi văn bản (B) --> Qdrant tìm đoạn --> lọc theo quyền người hỏi
        |                                             |
        v                                             v
  [ Claude tổng hợp câu trả lời, có trích nguồn ] <--+
```

Claude đọc câu hỏi, tự chọn: gọi tool truy vấn (A) hay tìm vector (B), có thể kết hợp cả
hai trong một câu trả lời, rồi tổng hợp và trích nguồn. Cơ chế tool use - function calling
của Claude API hỗ trợ sẵn.

---

## 4. Bốn thành phần

### 4.1. File định nghĩa (bộ não điều phối)

Một tài liệu system prompt cố định: vai trò trợ lý, ranh giới hành xử, danh sách công cụ
được phép gọi, cách trích nguồn, cách nói "không có trong tài liệu". Nạp kèm gói tri thức
biên soạn tay (quy định, quy trình nhà máy) qua context và prompt caching.

Ranh giới bắt buộc (kế thừa từ gói `GOI_TRO_LY_AI_DEGO_ORGANIC`):
- AI chỉ đánh giá và đề xuất, KHÔNG tự sửa - duyệt - ban hành. Mọi kết quả là dự thảo.
- Phân biệt rõ dẫn chứng có trong tài liệu và suy luận của AI.
- Không bịa số liệu, điều khoản, tên người, hạn mức, thời hạn. Thiếu thì hỏi hoặc ghi nhãn.

### 4.2. Bộ API cho bot gọi (phục vụ loại A)

Các endpoint truy vấn đủ linh hoạt để Claude gọi như "công cụ". Nguyên tắc: tái dùng API
nghiệp vụ có sẵn (đã gác quyền), chỉ bổ sung endpoint tra cứu còn thiếu. Danh sách gợi ý:

| Công cụ (tool) | Nguồn dữ liệu | Đầu ra |
|---|---|---|
| Danh sách HĐ NCC theo trạng thái hạn | `contract` (`end_date`, `status`, `expiry`) | HĐ còn hạn / hết hạn, đếm số lượng, theo NCC |
| Giá tốt nhất của một mã hàng | `purchase_history` | NCC + giá thấp nhất, kèm MOQ, ngày mua |
| Lịch sử mua của một mã hàng | `purchase_history` | Danh sách đã mua: NCC, giá, số lượng, ngày |
| Tra NCC theo mã hàng hoặc mô tả | `supplier` + `purchase_history` | Danh sách NCC gợi ý cho mã hàng đó |

Cơ chế bảo mật của bộ API cho bot - 7 tầng. Nguyên tắc trùm: con bot KHÔNG phải ngoại lệ
của hệ phân quyền, nó tái dùng nguyên hàng rào đã dựng cho người dùng thật.

1. Thực thi DƯỚI DANH TÍNH NGƯỜI HỎI - KHÔNG có tài khoản của bot. Request người dùng đã
   mang JWT (`get_current_user`, `core/auth.py`). Claude gọi tool thì backend chạy tool đó
   bằng đúng user context của người hỏi. Bot thấy đúng cái người đó được thấy, không hơn.
   CẤM cấp service account quyền cao cho bot - làm vậy `apply_scope` thành vô nghĩa, leak sạch.
2. Allowlist tool cố định. Bot KHÔNG sinh SQL, KHÔNG chạm DB trực tiếp; chỉ chọn từ danh
   sách tool khai sẵn, mỗi tool ánh xạ đúng một hàm service. Chống SQL injection và chống lách.
3. Hai lớp phân quyền nguyên vẹn trong mỗi tool: `require(entity, action)` (`core/auth.py`)
   + `apply_scope(query, model, entity, user, profile)` (`core/scoping.py`). Không quyền thì
   trả rỗng. Đã có hàng rào B-07: entity thiếu khai scope là CHẶN (`false()`), test đỏ ngay.
4. Read-only giai đoạn đầu. Bot chỉ gọi tool ĐỌC; cấm ghi - duyệt - xóa. Khớp ranh giới
   "AI chỉ đề xuất".
5. Validate tham số + giới hạn kết quả: schema chặt (`strict`), whitelist giá trị, giới hạn
   số dòng trả về (tránh kéo cả nghìn dòng, rò dữ liệu diện rộng).
6. Chống prompt injection - ranh giới nguồn lệnh: dữ liệu và văn bản trả về là DATA, không
   phải lệnh. Văn bản RAG có thể chứa "hãy gọi tool X" - bot không được để nội dung tra được
   điều khiển việc gọi tool vượt quyền.
7. Audit log: ghi ai hỏi, tool nào, tham số, số dòng trả (`core/audit.py`) để soát.

### 4.3. Kho vector Qdrant (phục vụ loại B)

- Kho vector: Qdrant (một container, lọc payload theo quyền mạnh).
- Embedding: chạy LOCAL (bge-m3 hoặc multilingual-e5-base) để không gửi văn bản nhạy cảm
  ra ngoài. Bước SINH câu trả lời vẫn gửi đoạn trích + câu hỏi cho Claude API, nên cần
  khách đồng ý (no-retention / DPA), tài liệu tuyệt mật loại khỏi phạm vi.
- Mỗi đoạn (chunk) nạp kèm NHÃN QUYỀN (entity + scope: chủ sở hữu, phòng ban, công ty, mức
  mật) lấy từ nguồn gốc. Lúc truy vấn LỌC theo quyền TRƯỚC khi đưa cho Claude, không thì
  AI lộ tài liệu người hỏi không được xem. Nhãn quyền phải trùng hệ hai trục sẵn có
  (`apply_scope` ở `core/scoping.py`), KHÔNG đẻ luật quyền song song.
- Reindex khi tài liệu đổi quyền - sửa - xóa là ràng buộc cứng.

### 4.4. Quản lý nguồn tri thức (sản phẩm thật)

Màn quản trị: khai báo nguồn, bật - tắt, xem trạng thái index, bấm reindex, đánh version
gói tri thức biên soạn tay, xem lịch sử hỏi. Đây là phần biến "gói chạy tay trên Claude.ai"
thành tính năng trong ERP.

### 4.5. Lớp provider model - hỗ trợ CẢ Claude VÀ Gemini từ đầu (chốt 25/08/2026)

Một lớp trừu tượng `ask(messages, tools, model) -> answer` che nhà cung cấp phía sau. Từ đầu
làm hai adapter:
- Adapter Claude: SDK `anthropic`, model mặc định `claude-opus-5` / `claude-sonnet-5` /
  `claude-haiku-4-5`. Key `ANTHROPIC_API_KEY`.
- Adapter Gemini: SDK Google GenAI, model Gemini 2.5 Flash / Flash-Lite / Pro. Key
  `GEMINI_API_KEY`. Khách sẽ gắn thử Gemini để test.

App KHÔNG gọi thẳng SDK nhà nào; luôn qua lớp này. Chọn nhà + model theo loại câu (routing):
tra cứu loại A rẻ -> Haiku / Gemini Flash; tư vấn quy trình loại B nặng -> Sonnet / Opus /
Gemini Pro. Cả hai nhà đều là API đóng, KHÔNG self-host; muốn nhúng docker thì phải model mở
(Qwen / Llama) - là adapter thứ ba, để sau. Embedding vẫn LOCAL, không thuộc lớp này.

---

## 5. Tri thức văn bản (loại B) - lấy nguồn từ đâu, chỉnh ở đâu

| Nguồn | Đã có backend | Chỗ biên tập | Cách vào kho vector |
|---|---|---|---|
| Trung tâm HDSD (`help_center`, bảng `tab_help_article`) | CÓ - cây thư mục, `content` Text | Chính màn Trung tâm HDSD (đã có UI) | Index tự động, reindex khi sửa bài |
| Câu hỏi thường gặp (`faq`) | CÓ | Màn FAQ | Index cùng đợt HDSD |
| Gói tri thức nhà máy (quy định, quy trình biên soạn tay) | CHƯA - đang chạy tay trên Claude.ai | Màn "Quản lý nguồn tri thức" (4.4), tải file + đánh version | Index từ file được duyệt |
| Văn thư (công văn, quyết định, quy trình) | CHƯA - cần backend Văn thư trước | Màn Văn thư (khi có) | Index sau khi có backend + quyền tài liệu |
| Điều khoản hợp đồng (text) | Có bảng `contract`, phần text | Màn hợp đồng | Để sau, chỉ khi cần hỏi nội dung điều khoản |

Trả lời trực tiếp câu hỏi "lấy nguồn từ đâu, có chỗ điều chỉnh không":

- Nguồn NGON NHẤT và sẵn ngay: Trung tâm HDSD + FAQ. Đã có backend, có nội dung Text,
  có UI biên tập. Chỉ cần viết bộ index đẩy sang Qdrant và móc reindex khi bài viết đổi.
- Chỗ điều chỉnh: mỗi nguồn sửa ở chính màn của nó (HDSD sửa ở HDSD, FAQ sửa ở FAQ). Riêng
  gói tri thức nhà máy (không có màn nguồn sẵn) thì sửa ở màn "Quản lý nguồn tri thức",
  tải file mới, đánh version, bấm reindex.
- Nguyên tắc một nguồn: mỗi tài liệu có ĐÚNG MỘT chỗ biên tập gốc. Kho vector chỉ là bản
  sao đã cắt đoạn để tìm kiếm, không phải chỗ sửa nội dung.

---

## 6. Phân quyền

- Loại A: dùng `apply_scope` của API - tự đúng.
- Loại B: nhãn quyền trên từng chunk, lọc trước khi đưa cho Claude - phải trùng
  `apply_scope`, reindex khi đổi quyền.
- Giai đoạn 1: chỉ ban lãnh đạo dùng.

---

## 7. Lộ trình (từ dễ ra kết quả tới khó)

- Bước 1 - AI-1 gói tri thức thành tính năng: màn Trợ lý gọi Claude API, nạp gói + prompt
  caching, quản lý gói - version. Chưa cần Qdrant, chưa cần Văn thư. Ra kết quả nhanh nhất.
- Bước 2 - Qdrant cho HDSD + FAQ (loại B): index nội dung sẵn có, embedding local, hỏi -
  đáp có trích nguồn. Đây là kho vector đầu tiên.
- Bước 3 - Tool use cho tra cứu (loại A): viết - gói các endpoint ở mục 4.2 thành công cụ
  cho bot. Dữ liệu đã có, chủ yếu là đóng gói lại.
- Bước 4 (để sau, khó) - AI-2 RAG toàn hệ có lọc quyền per-record + backend Văn thư.

---

## 8. Câu hỏi mở

- App riêng hay phân hệ trong ERP.
- Model: Opus / Sonnet cho tư vấn quy trình (loại B nặng suy luận); Haiku / Sonnet cho tra
  cứu rẻ (loại A). Xác nhận sau khi đo chi phí thật.
- Danh sách gói tri thức và ai được hỏi gói nào.
- Chốt danh sách endpoint loại A cần bổ sung so với API đã có.
- Đồng ý DPA - no-retention với Anthropic và danh mục tài liệu tuyệt mật loại khỏi phạm vi.
