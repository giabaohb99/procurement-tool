# DÀI HẠN — LỘ TRÌNH PHÂN HỆ

| | |
|---|---|
| Bản | 1.1 — 10/08/2026 |
| Đối tượng đọc | Ban lãnh đạo · Gia Bảo · Được |
| Trả lời câu hỏi | ERP gồm những module gì, và làm theo thứ tự nào |
| Mức chi tiết | Đầu mục. **Không có mốc thời gian, không có số người-ngày** |
| Liên quan | [`01` Ngắn hạn](./01-ngan-han-2026.md) · [`04` Danh mục chờ quyết](./04-danh-muc-cho.md) |

> **Đây là kế hoạch dài hạn, không phải cam kết.** Thứ tự dưới đây là thứ tự hiệu quả nhất theo điều kiện hiện nay. **Tùy điều kiện thực tế và kế hoạch kinh doanh, thứ tự và phạm vi có thể thay đổi.** Cái không đổi là nguyên tắc: mỗi vòng phải có một phân hệ chạy thật rồi mới sang vòng sau.

---

## 1. Thứ tự các vòng

ERP của DEGO gồm sáu phân hệ. Không làm cùng lúc — làm từng vòng, mỗi vòng đưa một phân hệ vào chạy thật.

| Vòng | Phân hệ | Trạng thái |
|---|---|---|
| Vòng 0 | **Thu mua** | Đã chạy — đang là hệ thống thật của công ty |
| Vòng 1 | **Nhân sự (HRM)** | Đang làm — xem [`01` Ngắn hạn](./01-ngan-han-2026.md) |
| Vòng 2 | **Sản xuất và kho (MFM)** | Chưa khảo sát |
| Vòng 3 | **Kế toán** | Chưa khảo sát. Nhiều khả năng **nối chứ không tự viết** |
| Vòng 4 | **Bán hàng (CRM)** | Chưa khảo sát |
| Xuyên suốt | **Dùng chung** | Mỗi vòng bồi thêm một phần |

---

## 2. Vì sao theo thứ tự này

| Thứ tự | Lý do |
|---|---|
| **HRM trước** | Nền sẵn nhiều nhất — bảng nhân sự đã có công ty, phòng ban, đã nối với tài khoản đăng nhập. Và nó là phép thử khắc nghiệt nhất cho phần phân quyền: nếu HRM phân quyền đúng thì phân hệ nào cũng đúng |
| **MFM thứ hai** | Nối trực tiếp với Thu mua đang chạy: mua nguyên vật liệu, nhập kho, xuất cho sản xuất. Dữ liệu đã có sẵn một nửa. Đây cũng là chỗ công ty đau nhất về số liệu |
| **Kế toán thứ ba** | Sau MFM là đã có đủ hai đầu chi phí lớn nhất — mua vào và sản xuất — đủ để hạch toán và ra giá thành. Phần lớn công việc ở vòng này là đầu nối chứ không phải viết mới, nên đặt sớm được |
| **CRM sau cùng** | Cần đầu ra của sản xuất. Làm trước MFM thì bán được đơn nhưng không biết có làm kịp không, không biết còn hàng không |

**Nguyên tắc chung:** đi theo dòng chảy vật chất và tiền của công ty — mua vào, sản xuất, ghi sổ, bán ra. Không đi theo phòng ban nào kêu to nhất.

**Chỗ có thể đổi:** nếu mảng bán hàng thành ưu tiên kinh doanh, CRM đổi chỗ với Kế toán được. Ngược lại thì không — MFM không đứng trước HRM được, vì phần phân quyền chưa qua phép thử.

---

## 3. Danh sách module

Bản đồ tổng thể của ERP. Ô nào đã có thì không làm lại, chỉ bồi thêm.

### 3.1 Thu mua — vòng 0, đã chạy

| Module | Trạng thái |
|---|---|
| Yêu cầu mua hàng | Đã có |
| Yêu cầu khảo sát giá | Đã có |
| Khảo sát và so sánh giá | Đã có |
| Đơn mua hàng | Đã có |
| Nhà cung cấp | Đã có |
| Hợp đồng mua | Đã có |
| Nhận hàng và nghiệm thu | Đã có |
| Yêu cầu thanh toán | Đã có |
| Công nợ phải trả | Đã có |
| Hồ sơ chứng từ | Đã có |
| Báo cáo thu mua | Đã có, bồi thêm dần |

### 3.2 Nhân sự (HRM) — vòng 1

| Module | Ghi chú |
|---|---|
| Hồ sơ nhân sự | Đã có phần khung, phải mở rộng |
| Cơ cấu tổ chức và chức danh | Đã có phòng ban, chưa có chức danh |
| Hợp đồng lao động | Chưa có |
| Phân công và điều chuyển | Chưa có |
| Tuyển dụng | Chưa có |
| Nghỉ phép | Chưa có |
| Chấm công | **Chờ chốt phạm vi** — [`04` mục C2](./04-danh-muc-cho.md) |
| Lương và phúc lợi | **Chờ chốt phạm vi** — [`04` mục C2](./04-danh-muc-cho.md) |
| Bảo hiểm | Chưa có |
| Đánh giá | Chưa có |
| Đào tạo | Chưa có |
| Nghỉ việc và bàn giao | Chưa có |
| Báo cáo nhân sự | Chưa có |

Phạm vi bản 1 chốt sau khảo sát, theo bộ câu hỏi [`03`](./03-cau-hoi-khao-sat-hrm.md).

### 3.3 Sản xuất và kho (MFM) — vòng 2

| Module | Ghi chú |
|---|---|
| Danh mục sản phẩm nhiều cấp | Bảng sản phẩm cha làm sẵn ở vòng 1 (việc DB6) |
| Định mức nguyên vật liệu (BOM) | Nhiều cấp, có phiên bản, có hiệu lực theo ngày |
| Kế hoạch sản xuất | |
| Lệnh sản xuất | |
| Công đoạn và tổ sản xuất | Nối với HRM nếu có lương theo sản phẩm |
| Xuất nguyên liệu, nhập thành phẩm | |
| Tồn kho | Đã có từ Thu mua — phải rà lại xem có đủ chặt không |
| Luân chuyển kho | Đã có từ Thu mua |
| Kiểm kê | |
| Vị trí kho, lô, hạn dùng | **Chờ chốt** — [`04` mục C5](./04-danh-muc-cho.md) |
| Chất lượng | Chốt sau khi khảo sát |
| Giá thành | **Ranh giới với Kế toán chưa rõ** — [`04` mục C6](./04-danh-muc-cho.md) |
| Bảo trì máy móc | Chốt sau khi khảo sát |
| Báo cáo sản xuất và kho | |

### 3.4 Kế toán — vòng 3

| Module | Ghi chú |
|---|---|
| Hệ thống tài khoản | Chỉ khi tự viết |
| Bút toán và sổ cái | Chỉ khi tự viết |
| Công nợ phải trả | Đã có bên Thu mua, cần cầu nối |
| Công nợ phải thu | Cần CRM, hoặc làm độc lập |
| Thu chi và ngân hàng | |
| Tài sản cố định và khấu hao | |
| Giá thành | Ranh giới với MFM |
| Thuế và hóa đơn | Theo quy định nhà nước |
| Báo cáo tài chính | Theo mẫu quy định |
| **Đầu nối sang phần mềm kế toán** | Đây mới là phần khả năng cao sẽ làm — xem mục 5 |

### 3.5 Bán hàng (CRM) — vòng 4

| Module | Ghi chú |
|---|---|
| Khách hàng | |
| Liên hệ và lịch sử tiếp xúc | |
| Cơ hội bán hàng | |
| Báo giá bán | Đối xứng với khảo sát giá bên Thu mua — dùng lại được nhiều |
| Đơn bán hàng | |
| Giao hàng | Nối với kho ở MFM |
| Công nợ phải thu | Đối xứng với công nợ phải trả đã có |
| Chính sách giá và chiết khấu | |
| Chăm sóc sau bán | Nối được với module Phiếu hỗ trợ đã có |
| Báo cáo bán hàng | |

**Ghi chú:** file `ke-hoach/02` mục 30.4 đã nêu một mâu thuẫn về mảng bán hàng chưa được giải quyết. Phải mở lại và chốt trước khi bắt đầu vòng này.

### 3.6 Dùng chung — bồi thêm mỗi vòng

| Module | Trạng thái |
|---|---|
| Tài khoản và phân quyền | Đã có — vá và gom theo phân hệ ở vòng 1 |
| Danh mục dùng chung | Đã có, mở rộng dần |
| Công ty và phòng ban | Đã có |
| Luồng duyệt dùng chung | Làm ở vòng 1 |
| Thông báo | Đã có — chuông, đẩy, thư |
| Tệp đính kèm và chứng từ | Đã có |
| Nhật ký thao tác | Đã có |
| Nhập liệu hàng loạt | Đã có |
| Webhook và đầu nối ra ngoài | Làm ở vòng 1 |
| Báo cáo và bảng số liệu | Bồi mỗi vòng |
| Trung tâm hướng dẫn sử dụng | Đã có, app riêng |
| Quản lý dự án (Project-M) | Đã có, app riêng |
| Phiếu hỗ trợ | Đã có |
| Sao lưu và phục hồi | Đã có |
| **Trợ lý AI (2 nhánh: gói tri thức + RAG toàn hệ)** | **Kế hoạch — xem 3.7; nhánh gói tri thức ưu tiên sớm** |

### 3.7 Trợ lý AI — HAI sản phẩm tách riêng (ghi 24–25/08/2026)

Rà lại 25/08/2026: đây thực chất là **hai sản phẩm khác nhau**, đừng gộp. Nhánh **AI-1** làm được
sớm và độc lập; nhánh **AI-2** khó, để sau.

#### AI-1 — Trợ lý "gói tri thức" (ưu tiên, khách muốn lên trước)

Khách đã tự đóng gói và **chạy được ngay trên Claude.ai Project**: một thư mục ~12 file (quy định
hệ thống công việc, hướng dẫn vận hành trợ lý, bộ câu hỏi, ngữ cảnh, bảng thuật ngữ, gói hợp
nhất...) dán vào Instructions + nạp vào Project Knowledge. Mục đích: **hỗ trợ lãnh đạo/nhà máy lên
kế hoạch, hiểu và tối ưu quy trình** — hỏi một nghiệp vụ thì trả lời theo kiến thức trong gói, và
rà soát/đề xuất cập nhật quy trình cũ.

Đánh giá + hướng làm:
- **Đây là "gói tri thức có người biên soạn", KHÁC hẳn AI-2.** Nguồn là bộ file cố định, không
  phải chứng từ động; người dùng là số ít sếp/quản lý; **phân quyền theo GÓI** (ai được hỏi gói
  nào), không phải theo từng bản ghi → **crux lọc-quyền-theo-role của AI-2 gần như biến mất ở đây.**
- **CHƯA cần vector DB.** Gói ~1MB thì nạp thẳng vào ngữ cảnh Claude + **prompt caching** (phần gói
  được cache, mỗi câu chỉ tính ~10%). Bỏ được cả Qdrant lẫn embedding ở giai đoạn này. Chỉ khi gói
  phình hàng trăm tài liệu mới cần RAG.
- **Model Opus/Sonnet, KHÔNG phải Haiku** — việc là tư vấn thiết kế/tối ưu quy trình theo khung
  chuẩn, cần suy luận mạnh và bám khung nghiêm; ngược với trợ lý tra cứu rẻ tiền.
- **Ranh giới đọc/đề xuất vs sửa (khách đã đặt sẵn trong Instructions, giữ nguyên):** AI chỉ đánh
  giá + đề xuất, **không tự viết lại/không tự ban hành**; cập nhật quy trình cũ = AI đề xuất →
  người có thẩm quyền duyệt → ghi thành **phiên bản mới** của gói. AI không ghi đè bản gốc.
- **Chống bịa:** buộc trả lời có trích nguồn trong gói, nói thẳng "không có trong tài liệu" thay
  vì đoán (khách đã có quy tắc "phân biệt dẫn chứng vs suy luận").
- **Phần "sản phẩm" thật sự phải xây nằm ở QUẢN LÝ GÓI**, không phải chỗ gọi AI: upload nhiều file,
  sửa, **đánh phiên bản**, ai sở hữu/duy trì, **nhiều gói cho nhiều mục đích** (tổ chức nhà máy,
  lập kế hoạch...), chọn gói khi hỏi — như cơ chế Project của Claude nhưng dựng trong ERP, có phân
  quyền + lưu lịch sử hỏi. Chất lượng = chất lượng gói → cần người nghiệp vụ duy trì.
- **Độc lập với P6/đa pháp nhân**, chen lên trước được; đánh đổi là P6 (gộp phiếu) lùi lại — khách
  quyết ưu tiên. Trong lúc xây bản tích hợp, sếp **dùng tạm bản Claude.ai Project** đã có.
- **Còn chốt:** làm app riêng (như Help Center/Project-M) hay phân hệ trong ERP; danh sách gói ban
  đầu; ai được hỏi gói nào.

#### AI-2 — Trợ lý tài liệu toàn hệ có phân quyền (để sau, khó)

Ý tưởng: một trợ lý cho người dùng **hỏi bằng ngôn ngữ tự nhiên**, AI đọc tài liệu của
**Văn thư** và các nguồn khác rồi trả lời có trích dẫn nguồn. Dùng **API của Claude** để sinh câu
trả lời, một **cơ sở dữ liệu vector** để tìm đoạn liên quan (RAG).

**PHÂN BIỆT CỐT TỬ (rà 25/08/2026) — hai loại câu hỏi, hai công cụ khác nhau, đừng lẫn:**

| | Loại A — dữ liệu CÓ CẤU TRÚC | Loại B — văn bản TỰ DO |
|---|---|---|
| Ví dụ | "HĐ với NCC nào còn hạn/hết hạn bao nhiêu", "sản phẩm mã A giá ổn nhất, đã mua của ai" | "quy trình nghiệm thu mấy bước", "điều khoản phạt trong HĐ nói gì" |
| Công cụ đúng | **Truy vấn CSDL / gọi API sẵn có** (`contract.end_date/status`, `purchase_history`) | **Qdrant vector search + RAG** |
| Vector hóa? | **KHÔNG** — vector tìm gần-nghĩa, không lọc/tính/tổng hợp chính xác → bỏ sót + bịa số | **CÓ** — đúng việc của vector |
| Phân quyền | **Tự đúng** vì gọi API đã gác `apply_scope`; không cần gắn nhãn quyền từng chunk | Phải gắn nhãn quyền vào chunk (crux dưới đây) |

→ Các ví dụ khách nêu ("còn hạn", "giá ổn nhất", "đã mua của ai") **đều là loại A** — dữ liệu đã
nằm sẵn ở `contract`/`purchase_history`, **đừng vector hóa**, cho AI gọi API. **Trợ lý cuối là bản
LAI:** Claude điều phối (tool use) — hỏi số liệu thì gọi truy vấn, hỏi nội dung thì Qdrant, rồi
tổng hợp. Qdrant chỉ dùng cho loại B (HDSD, quy trình, nội dung văn bản dài).

**Văn thư làm kho chung — ranh giới đúng (rà 25/08/2026):** Văn thư là kho quản lý **FILE + hồ sơ**
trung tâm cho loại **CHƯA có nhà riêng** (hợp đồng lao động = "văn bản loại hợp đồng", gắn nhân
viên, có danh sách HĐ; công văn, quyết định, quy trình). **Thứ đã có bảng nghiệp vụ riêng thì giữ
nguyên** (HĐ NCC ở `contract`, chứng từ thu mua) — Văn thư đừng ôm lại dữ liệu, cùng lắm chuẩn hóa
chỗ đính kèm file. Quy tắc: **Văn thư giữ FILE + metadata hồ sơ, KHÔNG ôm dữ liệu nghiệp vụ có cấu
trúc** (giá/số lượng/trạng thái). Dù Văn thư ôm hết hay không **cũng không đổi kiến trúc AI** — AI
luôn cần *(chữ hoặc cách truy vấn, nhãn quyền, link gốc)* qua "đầu nối".

**Điểm cốt lõi khách nhấn mạnh — và cũng là chỗ khó nhất: chỉ một DB vector chung, nhưng KẾT QUẢ
phải bị RÀNG BUỘC theo quyền của người hỏi.** Không tách kho vector theo từng người; thay vào đó
mỗi đoạn (chunk) nạp vào vector kèm **nhãn phân quyền** (chủ sở hữu / phòng ban / công ty / mức
mật) lấy từ chính tài liệu gốc, và lúc truy vấn **lọc theo quyền của người hỏi TRƯỚC khi** đưa
đoạn cho Claude — nếu không, AI sẽ vô tình đọc trích tài liệu mà người đó không được xem. Ràng
buộc này phải trùng khớp với hệ phạm vi hai trục sẵn có (`apply_scope`/`scope_condition`), không
đẻ luật quyền song song.

**Hướng đã chốt sơ bộ 25/08/2026:**

- **Tách hai lớp, KHÔNG dồn mọi thứ vào Văn thư.** Hợp đồng NCC, chứng từ thu mua đã có bảng
  riêng; hợp đồng lao động sẽ thuộc HRM — copy sang Văn thư là nhân đôi dữ liệu và lệch quyền.
  Lớp **lưu trữ** để mỗi loại tài liệu ở đúng module của nó; Văn thư chỉ giữ tài liệu **tự do**
  (công văn, quyết định, quy trình) không thuộc module nào. Lớp **chỉ mục AI** dựng **một "đầu nối"
  cho mỗi loại nguồn**, khai báo cách lấy *(chữ, nhãn quyền entity+scope, đường về bản gốc)*. AI
  đánh chỉ mục **từ nguồn**, không cần gom về Văn thư. Bản chất mỗi thứ AI cần chỉ là ba phần đó —
  không phải "văn bản" theo nghĩa Văn thư.
- **Ràng buộc thứ tự:** *(cập nhật 27/08/2026)* Văn thư **đã có backend thật** trên nhánh `erp-v2`
  (`app/modules/document/` + `app/modules/doc_catalog/`, kèm mô hình quyền tài liệu
  `access_model`/`scope_model`) — ràng buộc "phải làm backend Văn thư trước" coi như **đã gỡ**.
  Hợp đồng/chứng từ thì nguồn đã sẵn, nối đầu nối là index được.
- **Kho vector:** nghiêng về **Qdrant** (một container, lọc payload theo quyền mạnh, hợp VPS nhỏ);
  phương án cực gọn lúc đầu là **Chroma**. Tránh dồn vào pgvector vì hệ đang MySQL.
- **Embedding chạy LOCAL** (bge-m3 hoặc multilingual-e5-base) để **không gửi hợp đồng nhạy cảm ra
  ngoài**. Nhưng **bước sinh câu trả lời vẫn gửi đoạn trích + câu hỏi cho Claude API (Anthropic)** —
  cần khách đồng ý (bật chế độ không lưu giữ / DPA); tài liệu tuyệt mật thì loại khỏi phạm vi AI.
- **Reindex khi nguồn đổi quyền / sửa / xóa:** phát tín hiệu cập nhật hoặc xóa đoạn + nhãn quyền
  trong vector (móc vào tầng audit/mutation, kèm job quét đối chiếu định kỳ). Ràng buộc cứng.
- **Model + chi phí:** mặc định **Haiku 4.5 / Sonnet** cho hỏi-đáp (rẻ), nâng model khi cần suy
  luận sâu. Embedding local gần như miễn phí; mỗi câu hỏi cỡ chục–vài trăm đồng. **Giai đoạn 1 chỉ
  mở cho ban lãnh đạo**, tối ưu chi phí xong mới mở cho nhân viên.

Còn phải chốt khi thiết kế chi tiết: danh sách chính xác nguồn nào đưa vào phạm vi AI; cách chia
đoạn (chunk) cho chứng từ có cấu trúc vs văn bản dài; nhật ký hỏi-đáp để rà soát; giới hạn tần suất.

---

## 4. Ba việc nền của vòng 2

Ghi riêng vì đây là ba thứ làm sai thì cả phân hệ sản xuất sai theo.

1. **Rà lại sổ kho.** Bảng tồn kho hiện có được viết cho mua hàng, chưa chắc đủ chặt để làm nền sản xuất: chặn âm kho, giá vốn, chốt kỳ. Sổ kho không chặt thì mọi số liệu sản xuất phía trên đều sai.
2. **Chốt có làm vị trí kho, lô, hạn dùng hay không.** Quyết định này đổi cấu trúc bảng tồn kho, phải chốt **trước** khi viết BOM.
3. **Thêm công ty cho kho** — làm ở vòng 1 (việc DB5), nhưng chỉ dùng thật khi có nhiều nhà máy.

**Điều kiện bắt đầu vòng 2:** HRM đã chạy thật và không còn lỗi chặn · khảo sát nghiệp vụ sản xuất xong, có biên bản xác nhận · bảng sản phẩm cha (DB6) đã có và đã dùng thật.

---

## 5. Kế toán — nối chứ không tự viết

| Vì sao | |
|---|---|
| Kế toán do luật định | Chế độ kế toán, mẫu báo cáo tài chính, quyết toán thuế đều theo quy định nhà nước và đổi theo văn bản pháp luật |
| Đã có phần mềm chuyên | Thị trường Việt Nam có sẵn phần mềm kế toán được cập nhật theo luật. Tự viết là gánh nghĩa vụ cập nhật pháp lý vĩnh viễn |
| Rủi ro không đối xứng | Phần mềm mua hàng tính sai thì sửa. Phần mềm kế toán tính sai thì làm việc với cơ quan thuế |

**Việc của đội phần mềm ở vòng này là đầu nối:** xuất bút toán từ Thu mua, MFM, CRM sang phần mềm kế toán, và màn hình đối chiếu. Chính là chỗ dùng thật của module webhook làm ở vòng 1.

Quyết định "tự viết hay nối" phải chốt **trước** vòng 3, không phải trong lúc làm — xem [`04` mục C7](./04-danh-muc-cho.md).

---

## 6. Nợ kỹ thuật đã dời — trả ở vòng nào

Vòng 1 chấp nhận không đụng cơ sở dữ liệu cũ. Đó là dời nợ chứ không phải hết nợ. Ghi ra đây để không ai quên.

| Nợ | Trả ở vòng nào | Nếu không trả |
|---|---|---|
| Trạng thái tồn tại hai kiểu: chuỗi tiếng Việt ở bảng cũ, mã ở bảng mới | Vòng 2, khi có cửa sổ bảo trì đầu tiên | Mỗi báo cáo liên phân hệ phải đi qua bảng quy đổi. Càng nhiều phân hệ càng dễ sai |
| Cột `created_by` không nói rõ là tài khoản hay nhân sự | Vòng 2 hoặc vòng 3 | Người mới vào sẽ hiểu nhầm. Đã có tiền lệ với `assignee_id` |
| 75 file migration chưa gộp mốc | Trước vòng 3 | Năm phân hệ thì thành ba trăm file, dựng môi trường mới mất hàng giờ |
| Chưa có kiểm thử tự động đầy đủ | Bồi dần mỗi vòng | Càng nhiều phân hệ, sửa một chỗ càng dễ vỡ chỗ khác mà không ai biết |
| **Nền pháp nhân đầy đủ (P2 của kế hoạch 12) — HOÃN có chủ đích 24/08/2026.** Tạm dùng nền phạm vi hiện có: nhân sự **bắt buộc thuộc một công ty** (ràng buộc lưu trữ, khách chốt), "các công ty liên quan" cấu hình tay bằng `scope=all` + danh sách công ty được cấp; phòng Thu mua và Sản xuất tự đưa bảng phạm vi. Bỏ tạm bậc "công ty và cấp dưới" nở tự động theo cây `parent`, bậc "chỉ các công ty được cấp" gọn, và map người xử lý theo cặp *(pháp nhân, phòng ban)*. | **Khi HRM chuẩn hết** (vòng 1 hoàn thiện) thì quay lại làm P2 đầy đủ | Số pháp nhân/nhà máy phình to thì cấu hình phạm vi bằng tay dày lên, dễ sót; báo cáo cộng dồn theo cây pháp nhân chưa có |

---

## 7. Cái gì bồi thêm ở mỗi vòng

Phần dùng chung không làm một lần xong.

| | Vòng 1 (HRM) | Vòng 2 (MFM) | Vòng 3 (Kế toán) | Vòng 4 (CRM) |
|---|---|---|---|---|
| Phân quyền | Vá lỗ hổng phạm vi, gom theo phân hệ | Thêm phạm vi theo kho, theo nhà máy | Thêm phạm vi theo pháp nhân, theo kỳ kế toán | Thêm phạm vi theo vùng, theo nhân viên bán hàng |
| Luồng duyệt | Làm luồng duyệt dùng chung | Duyệt lệnh sản xuất, duyệt xuất kho | Duyệt bút toán, khóa sổ | Duyệt báo giá, duyệt chiết khấu |
| Báo cáo | Báo cáo nhân sự | Báo cáo sản xuất, giá thành | Báo cáo tài chính, đối chiếu | Báo cáo bán hàng, công nợ phải thu |
| Tích hợp | Module webhook phần lõi | Đồng bộ hai chiều, đối chiếu lệch | Đầu nối phần mềm kế toán | Đầu nối kênh bán |
| Hạ tầng | Nhật ký lỗi, giám sát, hàng đợi | Kiểm thử tải, tối ưu truy vấn | Lưu vết không sửa được | Sao lưu và phục hồi theo phân hệ |

---

## 8. Ba điều kiện để lộ trình này không vỡ

1. **Mỗi vòng phải có một phân hệ chạy thật, không phải chạy demo.** Làm nửa vời ba phân hệ tệ hơn làm xong một.
2. **Khảo sát nghiệp vụ phải xong trước khi viết code của vòng đó.** Vòng 1 đã ghi rõ cách làm, các vòng sau lặp lại đúng khuôn đó.
3. **Bộ phận nghiệp vụ phải cử được đầu mối cho từng vòng.** Đây là điều kiện thường bị coi nhẹ và thường là nguyên nhân trượt lịch thật sự — file `ke-hoach/01` mục 5 đã ghi là chưa hạn nào chờ bộ phận khác được giữ đúng.

---

## 9. Cái gì không nằm trong lộ trình này

| | Vì sao |
|---|---|
| Đa ngôn ngữ | Chưa có nhu cầu thật |
| Ứng dụng di động riêng | Web đã chạy được trên điện thoại. Làm app riêng là nhân đôi khối lượng bảo trì |
| Bán sản phẩm ra ngoài | Là mục tiêu khác hẳn: cần đa khách hàng, cần hỗ trợ, cần bản quyền. Nếu có ý định thì phải bàn từ đầu chứ không chuyển đổi sau |
| Đổi khung công nghệ | Không có lý do kỹ thuật nào đủ mạnh |
