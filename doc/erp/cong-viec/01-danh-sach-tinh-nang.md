# PHÂN HỆ QUẢN LÝ CÔNG VIỆC — DANH SÁCH TÍNH NĂNG

**Bản:** 1.4 — 28/08/2026 · **Trạng thái:** danh sách ĐÃ DUYỆT (chốt hướng **CLONE LARK TASKS**), CHƯA viết code · **CR:** CR-216 (bản 1.4: CR-217)

Bộ tài liệu phân hệ (đọc theo thứ tự): **[`01`](./01-danh-sach-tinh-nang.md) danh sách
tính năng** (tệp này) · **[`02`](./02-bang-du-lieu.md) bảng dữ liệu** ·
**[`03`](./03-lo-trinh-phase.md) lộ trình phase** · **[`04`](./04-phan-quyen.md) phân
quyền** · **[`05`](./05-giao-dien.md) đặc tả giao diện** (bản 1.3 thêm — clone thanh công
cụ Lark: All Tasks / Filter / Sort / Group by / Customize, giải phẫu kanban, panel chi
tiết, dashboard, activities, tham khảo DHTMLX Gantt).

Yêu cầu gốc (28/08/2026): làm chức năng quản lý công việc ngay trong ERP, "đại khái như
Lark Tasks" — có danh sách công việc (task list) mời người vào, bảng kanban kéo thả, việc
con, người phụ trách, tag, độ ưu tiên, bình luận. Tài liệu này liệt kê tính năng để duyệt
trước; thiết kế bảng dữ liệu và giao diện làm ở tài liệu sau, sau khi chốt các câu hỏi ở §7.

Nguồn đối chiếu: hai ảnh chụp Lark Tasks của người dùng — (1) bảng kanban 4 cột
Documentation / To do / Doing / Reviewing; thẻ việc có PIC, Tag, Độ ưu tiên, Phiên bản,
tiến độ việc con 0/5, số bình luận; thanh bên trái các task list chia nhóm như
"Công cụ Ai", "Thu mua"; (2) panel chi tiết một task: hạn Today/Tomorrow, thuộc list
"Thu mua" cột "Documentation", các trường nhãn PIC / Tag / Độ ưu tiên / Phiên bản,
danh sách việc con 0/5.

**Bản 1.1 (trao đổi lần 2, 28/08/2026)** bổ sung ba yêu cầu: NHÓM chứa task list và chia
sẻ được (tối đa 2 cấp), NHÃN TÙY BIẾN theo từng list (tự đặt loại nhãn như "Phiên bản")
lên bản đầu, và quy tắc hiển thị việc con (nằm trong list của cha nhưng không hiện thành
thẻ riêng). Chi tiết ở §2, A-08, B-08, C-05.

**Bản 1.4 (CR-217, 28/08/2026)** đối chiếu tài liệu QLDA của Công cụ Văn thư
(`DMS-PM-FEATURES` v1.0 — chuyển từ máy khác sang, mã nguồn không nằm trong repo này) —
xem §4b. Nhận khái niệm **Dự án đứng trên task** theo **QĐ-T2**: dự án = task list kiểu
dự án (A-10), KHÔNG dựng cặp bảng project/task riêng — DB giữ khuôn `tab_work_*` của
mình. Thêm A-10 (P1), B-14 + B-15 (P2, cụm Gantt); nhóm F của tài liệu kia (lịch làm
việc — ngày nghỉ) chốt KHÔNG làm bây giờ, ghi vào W5 làm sau.

---

## 1. Vị trí trong hệ — và quan hệ với Project-M

### 1.1 Đây là phân hệ MỚI, nằm hẳn trong ERP

- Một thẻ phân hệ mới trên lưới ERP v2 (đề xuất tên hiển thị **"Công việc"**), làm ở
  `frontend-v2/` như mọi phân hệ khác, backend là một module mới trong mã nguồn Thu mua —
  đúng khuôn đã dùng cho Văn thư, Diễn đàn, Phiếu hỗ trợ.
- Dùng lại toàn bộ nền sẵn có: tài khoản, nhân sự, phòng ban, pháp nhân, phân quyền hai
  trục, chuông thông báo, tab Việc cần làm (CR-215), upload R2, audit.

### 1.2 Quan hệ với Project-M (QLDA của Ban điều hành)

Project-M (`D:\New folder\thuthapykien\PM`) là lớp GIÁM SÁT: Ban điều hành theo dõi dự
án, mốc, gantt, chỉ số quản trị — brief của nó ghi rõ "không ôm lớp thực thi chi tiết bên
dưới". Phân hệ Công việc này chính là lớp thực thi đó: việc hằng ngày của từng đội, từng
người.

**QĐ-T1 (chốt 28/08/2026):** phân hệ Công việc làm **riêng, độc lập** trong ERP. Kế hoạch
Project-M cũ **không chặn** việc này — về sau nếu muốn thì tích hợp (một task list gắn vào
một dự án Project-M để dồn tiến độ lên), hoặc bỏ qua hẳn. Tài liệu này KHÔNG phụ thuộc
tài liệu nào của PM.

---

## 2. Khái niệm dữ liệu

| Khái niệm | Tiếng Anh (định danh) | Là gì |
|---|---|---|
| Nhóm | Group | Thư mục chứa các task list (như "Công cụ Ai", "Thu mua" ở sidebar). Nhóm chứa task list hoặc nhóm con, **tối đa 2 cấp nhóm**. Gán thành viên ở nhóm là kế thừa xuống mọi list bên trong (Q9). |
| Danh sách công việc | Task List | "Cái bảng" của một đội / một mảng việc, nằm trong một nhóm (hoặc đứng lẻ). Có thành viên riêng, cột riêng, việc riêng, bộ nhãn riêng. Đơn vị phân quyền chính. |
| Dự án | Project (list kind) | **Bản 1.4 — QĐ-T2:** KHÔNG phải thực thể riêng đứng trên task. "Dự án" là một task list bật cờ `kind = dự án`, mở thêm hồ sơ: ngày bắt đầu — kết thúc, trạng thái vòng đời (SMALLINT), tiến độ tổng TỰ TÍNH từ task xong/tổng (không lưu cột). Mọi tính năng list (thành viên, cột, nhãn, kanban) dùng nguyên. Xem §4b + A-10. |
| Cột / nhóm | Section | Cột trên kanban, do từng list tự đặt (Documentation, To do, Doing, Reviewing…). Kéo thả đổi thứ tự, đổi tên được. |
| Công việc | Task | Một việc: tiêu đề, mô tả, người phụ trách, hạn, độ ưu tiên, tag, nằm trong một cột của một list. |
| Việc con | Subtask | Đầu việc nhỏ trong một task, tick từng cái, thẻ cha hiện tiến độ n/m. **Tối đa 2 cấp** (task → việc con, việc con KHÔNG có con). Việc con thuộc list của cha nhưng **không hiện thành thẻ riêng** trên kanban/danh sách — chỉ thấy khi mở panel chi tiết của cha (C-05). |
| Nhãn tùy biến | Custom Label Field | Trường do TỪNG LIST tự đặt: tên trường (như "Phiên bản") + kiểu (chọn một · chọn nhiều · người · số · ngày · chữ) + bộ giá trị kèm màu. **Tag và Độ ưu tiên cũng là trường như thế**, chỉ khác ở chỗ được nạp sẵn lúc tạo dự án. |
| Người phụ trách | Assignee (PIC) | Người chịu trách nhiệm chính của task. |
| Người theo dõi | Follower | Nhận thông báo khi task đổi, không phải người làm. |
| Thành viên list | Member | Người được mời vào task list, kèm vai trò trong list (§5.2). |
| Tag | Tag | Một trường tùy biến kiểu CHỌN NHIỀU nạp sẵn cho mọi dự án; một task gắn nhiều giá trị. Từ migration `c8a1d4f60b72` nó không còn bảng riêng — xóa hay đổi tên đều được. |
| Bình luận | Comment | Trao đổi ngay trong task, có nhắc tên, đính kèm. |

**Hai tầng trạng thái — điểm phải chốt sớm (Q2):** cột kanban là TÙY BIẾN theo từng list
(bảng `section` riêng, task trỏ `section_id`), còn TRẠNG THÁI HỆ THỐNG của task là bộ cố
định nhỏ lưu `SMALLINT` + `IntEnum` theo đúng luật R2/QĐ-11 (đề xuất: `1 open · 2 done ·
3 cancelled`). Tách như vậy thì người dùng tự do đặt cột như Lark mà báo cáo / đếm "việc
chưa xong" / nhắc hạn vẫn có một nguồn sự thật bằng số, không đoán theo tên cột.

---

## 3. Danh sách tính năng

Ưu tiên: **P0** = bản đầu phải có · **P1** = ngay sau bản đầu · **P2** = để sau, làm khi cần.

### Nhóm A — Danh sách công việc và thành viên

| Mã | Tính năng | Ưu tiên | Ghi chú |
|---|---|---|---|
| A-01 | Tạo / sửa / lưu trữ (archive) task list; tên, mô tả, màu | P0 | Lưu trữ chứ không xóa cứng — việc cũ còn tra lại |
| A-02 | Mời thành viên vào list: chọn từ danh bạ nhân sự, gán vai trò trong list | P0 | Mời theo từng người; mời cả phòng ban là P1 (A-06) |
| A-03 | Rời list / gỡ thành viên / đổi vai trò thành viên | P0 | |
| A-04 | Chuyển quyền sở hữu list cho người khác | P0 | Bắt buộc có — người tạo nghỉ việc thì list không mồ côi |
| A-05 | Thanh bên trái: cây nhóm → task list mình là thành viên, ghim list hay dùng | P0 | Như sidebar Lark |
| A-06 | Mời theo phòng ban (cả phòng vào một lượt, người mới vào phòng tự có) | P1 | Cần chốt Q7 |
| A-07 | Nhân bản list / tạo list từ mẫu | P2 | |
| A-08 | **Nhóm (group) chứa task list, tối đa 2 cấp nhóm**; tạo/sửa/lưu trữ nhóm; kéo list vào/ra nhóm | P0 | Bản 1.1. List đứng lẻ ngoài nhóm vẫn hợp lệ |
| A-09 | Chia sẻ Ở CẤP NHÓM: gán thành viên vào nhóm → kế thừa vai trò xuống mọi list bên trong; mời thêm người vào từng list lẻ vẫn được | P0 | Bản 1.1, xem Q9. Mạnh hơn Lark — bên Lark nhóm sidebar chỉ là sắp xếp cá nhân |
| A-10 | **List kiểu "Dự án"** (QĐ-T2): cờ `kind` + hồ sơ dự án — ngày bắt đầu — kết thúc, trạng thái vòng đời, tiến độ tổng % tự tính (= task DONE / tổng task) | P1 | Bản 1.4 — từ đối chiếu §4b. Tiến độ là số DẪN XUẤT lúc đọc, KHÔNG lưu cột; không bắt nhập % tay từng task như QLDA |

### Nhóm B — Công việc (task)

| Mã | Tính năng | Ưu tiên | Ghi chú |
|---|---|---|---|
| B-01 | Tạo / sửa / xóa task: tiêu đề, mô tả | P0 | Xóa là xóa mềm, khôi phục được (B-09) |
| B-02 | Người phụ trách (PIC) — cho phép NHIỀU người như Lark; thêm người theo dõi | P0 | Q5 chốt theo hướng clone Lark: bảng gắn nhiều người, giao diện khuyến khích một người chính |
| B-03 | Ngày bắt đầu — hạn chót | P0 | Nền cho nhắc hạn F-03 và Gantt sau này |
| B-04 | Độ ưu tiên P1–P4 (bộ cố định hệ thống, SMALLINT) | P0 | Như Lark: P1 đỏ, P2 cam… |
| B-05 | Tag nhiều nhãn, quản lý tag theo list | P0 | Xong — nay là trường tùy biến chọn-nhiều, không còn bảng riêng (`c8a1d4f60b72`) |
| B-06 | Đánh dấu hoàn thành / mở lại | P0 | Đổi trạng thái hệ thống, độc lập với cột kanban |
| B-07 | Kéo thả giữa các cột, sắp thứ tự tay trong cột | P0 | Cột lưu `sort_order` |
| B-08 | **Nhãn tùy biến theo list** (kiểu chọn-một-nhãn): tự đặt tên trường như "Phiên bản", tự đặt bộ giá trị + màu, gắn lên task | P0 | Bản 1.1 nâng từ P2 lên theo yêu cầu "custom được mấy cái nhãn, loại nhãn". Chỉ làm KIỂU CHỌN NHÃN ở bản đầu; kiểu chữ/số/ngày/người để B-13 |
| B-13 | Trường tùy chỉnh kiểu khác: chữ tự do, số, ngày, chọn người | P2 | Nặng hơn nhiều (nhập liệu, sort, lọc theo từng kiểu) — chỉ làm khi nhãn chọn không gánh nổi |
| B-09 | Thùng rác của list: xem việc đã xóa, khôi phục | P1 | |
| B-10 | Chuyển task sang list khác | P1 | |
| B-11 | Việc lặp lại (hằng tuần, hằng tháng) | P2 | |
| B-12 | Gắn task vào chứng từ ERP (YCMH, ĐMH, phiếu hỗ trợ, văn bản…) | P2 | Xem Q6 — điểm ăn tiền so với Lark nhưng chưa cần ngay |
| B-14 | Cột mốc (milestone): đánh dấu một task là mốc dự án | P2 | **XONG 31/08/2026 (CR-226)** — cột `tab_work_task.kind`; bật/tắt ở panel chi tiết, Gantt vẽ hình thoi. Đổi thành mốc thì gộp ngày về `due_date` |
| B-15 | Phụ thuộc giữa task (FS/SS/FF/SF) — bảng `tab_work_task_link` | P2 | **XONG 31/08/2026 (CR-226)** — kéo từ chấm ở đầu thanh sang việc khác là tạo, kiểu suy ra từ hai đầu chạm vào. `link_service.creates_cycle()` chặn vòng lặp ngay từ đầu, có test (tài liệu QLDA tự ghi nhận bên đó CHƯA chặn — §4b). `lag_days` mới LƯU, chưa dời lịch dây chuyền |

### Nhóm C — Việc con (subtask)

| Mã | Tính năng | Ưu tiên | Ghi chú |
|---|---|---|---|
| C-01 | Thêm / sửa / xóa / tick hoàn thành việc con trong task | P0 | |
| C-02 | Thẻ task hiện tiến độ n/m như Lark (0/5) | P0 | |
| C-03 | Việc con có PIC và hạn riêng | P1 | Bản đầu chỉ cần tiêu đề + tick |
| C-04 | Nâng việc con thành task độc lập | P2 | |
| C-05 | **Quy tắc hiển thị + độ sâu:** việc con thuộc list của cha nhưng KHÔNG hiện thành thẻ riêng trên kanban/danh sách — chỉ hiện trong panel chi tiết của cha; tối đa 2 cấp (việc con không có con) | P0 | Bản 1.1. Đếm/tiến độ của list chỉ tính task cha; việc con chỉ đóng góp vào n/m của cha |

### Nhóm D — Khung nhìn

| Mã | Tính năng | Ưu tiên | Ghi chú |
|---|---|---|---|
| D-01 | Kanban theo cột, kéo thả | P0 | Khung nhìn chính, đúng ảnh mẫu |
| D-02 | Danh sách (bảng phẳng, sort theo hạn / ưu tiên / PIC) | P0 | Dựng trên `DataTable` dùng chung |
| D-03 | Chi tiết task dạng panel trượt / dialog, mở từ mọi khung nhìn | P0 | |
| D-04 | Lịch (task đổ theo hạn chót trên lịch tháng) | P2 | |
| D-05 | Gantt / timeline | P2 | **XONG** — bản đầu 28/08/2026 (CR-219), dựng lại theo Lark 31/08/2026 (CR-226): lưới trái dùng chung bộ cột với Danh sách · thang Ngày/Tuần/Tháng · thanh NHÓM gom con · cột mốc · mũi tên phụ thuộc. Tự dựng, KHÔNG cài thư viện — xem `05-giao-dien.md` §10 |
| D-06 | Dashboard thống kê theo list (đếm theo cột, theo PIC, quá hạn) | P1 | 4 khối — `05-giao-dien.md` §7 |
| D-07 | Thanh công cụ khung nhìn clone Lark: Việc mới · Tất cả (phạm vi nhanh) · Lọc điều kiện · Sắp xếp · Gom nhóm · Tùy chỉnh thẻ | P0 | Bản 1.3 — đặc tả từng nút ở `05-giao-dien.md` §3; Lọc dùng khung `conditional-filter` sẵn có |
| D-08 | Gom nhóm kanban theo trường khác: PIC / độ ưu tiên / hạn (ngoài cột tự đặt) | P1 | Kéo thẻ giữa nhóm = đổi giá trị trường đó |
| D-09 | Tab Activities: dòng hoạt động cấp LIST (gộp audit mọi task + thành viên vào-ra) | P1 | **XONG** 31/08/2026 (CR-249). Từ 03/09/2026 (CR-254) nó là chỗ DUY NHẤT đọc nhật ký — panel chi tiết đã bỏ khối E-04. ⚠️ Chưa lọc được theo MỘT việc, và bình luận không vào dòng này (không ghi `tab_audit_log`) |

### Nhóm E — Bình luận, đính kèm, nhật ký

| Mã | Tính năng | Ưu tiên | Ghi chú |
|---|---|---|---|
| E-01 | Bình luận trong task | P0 | **XONG** 03/09/2026 (CR-253) — dùng THẲNG `tab_comment` chung, không đẻ bảng riêng |
| E-02 | Nhắc tên @ trong bình luận — người được nhắc nhận thông báo | P1 | **XONG** cùng CR-253 — đi kèm hạ tầng chung, không phải làm thêm |
| E-03 | Đính kèm tệp / ảnh vào task và bình luận (lưu R2) | P1 | **XONG** 03/09/2026 (CR-253) — `tab_file_link` chung; đo được 401 khi tải thiếu token (PQ13) |
| E-04 | Nhật ký hoạt động của task: ai tạo, ai đổi cột, ai đổi PIC, lúc nào | P0 | **XONG**, nhưng KHÔNG còn ở panel chi tiết: bỏ khỏi panel 03/09/2026 (CR-254) vì trùng với tab **Hoạt động** cấp dự án (D-09). Dữ liệu vẫn ghi đủ qua `core/audit.py` |
| E-05 | Sửa / xóa bình luận của mình | P1 | **XÓA đã có** (CR-253, backend chung lo); SỬA thì chưa |

### Nhóm F — Thông báo và tích hợp nền ERP

| Mã | Tính năng | Ưu tiên | Ghi chú |
|---|---|---|---|
| F-01 | Được giao việc → chuông thông báo | P0 | Notification sẵn có |
| F-02 | Task mình phụ trách xuất hiện trong tab **Việc cần làm** (CR-215) | P0 | Thêm loại `job:{id}` vào `build_my_tasks`; giữ bất biến "tab là tập cha của chuông" |
| F-03 | Nhắc hạn: đến hạn / quá hạn → chuông (job chạy nền Celery đã có) | P1 | Điều kiện lọc phải trùng khớp giữa chuông và tab — bài học CR-215 |
| F-04 | Thông báo khi task mình theo dõi đổi trạng thái / có bình luận | P1 | |
| F-05 | Web push (điện thoại) cho giao việc + nhắc hạn | P2 | Hạ tầng web-push đã chạy prod |
| F-06 | Tool cho Trợ lý AI: "việc của tôi hôm nay", "tạo việc nhắc tôi…" | P2 | Nối vào bộ tool trợ lý sẵn có (T25–T29) |

### Nhóm G — Tìm kiếm, lọc, Việc của tôi

| Mã | Tính năng | Ưu tiên | Ghi chú |
|---|---|---|---|
| G-01 | Lọc trong list: theo PIC, tag, độ ưu tiên, hạn, cột, trạng thái | P0 | |
| G-02 | Tìm theo tiêu đề / mô tả trong list | P0 | |
| G-03 | Màn "Việc của tôi": gom task mình phụ trách từ MỌI list, nhóm theo hạn | P1 | Khác tab Việc cần làm: tab kia là chứng từ + cảnh báo toàn hệ, màn này là task của phân hệ |
| G-04 | Lưu bộ lọc hay dùng | P2 | |

### Nhóm H — Quản trị

| Mã | Tính năng | Ưu tiên | Ghi chú |
|---|---|---|---|
| H-01 | Quyền hệ thống gác cửa phân hệ (entity mới trong RBAC — §5.1) | P0 | |
| H-02 | Vai trò trong từng list: Chủ / Quản trị / Thành viên / Khách xem | P0 | Ma trận ở §5.2 |
| H-03 | Quản trị hệ thống xem được danh sách MỌI list (không tự động xem nội dung) | P1 | Xem Q4 — riêng tư của list |
| H-04 | Xuất Excel danh sách việc của một list | P2 | Qua khung export chung khi Đ-13 làm xong |

---

## 4. Đối chiếu ảnh Lark — cái gì có, cái gì không

| Thấy trong ảnh Lark | Bản đầu (P0) | Ghi chú |
|---|---|---|
| Sidebar các task list chia nhóm | Có | A-05, A-08 — bên ta nhóm còn chia sẻ được (A-09), Lark thì nhóm sidebar là sắp xếp cá nhân |
| Kanban cột tùy biến, kéo thả | Có | D-01, B-07 |
| PIC trên thẻ | Có | B-02 |
| Tag | Có | B-05 |
| Độ ưu tiên P1–P4 | Có | B-04 |
| Trường "Phiên bản" | CÓ | Bản 1.1: nhãn tùy biến kiểu chọn (B-08); kiểu chữ/số/ngày vẫn để sau (B-13) |
| Tiến độ việc con 0/5 trên thẻ | Có | C-02 |
| Số bình luận trên thẻ | Có | E-01 |
| Gantt / Dashboard / Activities (tab trên cùng) | KHÔNG | D-05, D-06 để sau |
| Automation, rule tự động | KHÔNG | Ngoài phạm vi, chưa bàn |

---

## 4b. Đối chiếu tài liệu QLDA của Công cụ Văn thư (bản 1.4)

Nguồn: `danh-sach-tinh-nang-quan-ly-du-an.md` (`DMS-PM-FEATURES` v1.0) — bản kiểm kê 59
tính năng của module Quản lý dự án ĐANG CHẠY trong Công cụ Văn thư (DMS), nền
dhtmlx-gantt; tài liệu chuyển từ máy khác sang, mã nguồn KHÔNG nằm trong repo này. Đừng
lẫn ba sản phẩm: **DMS-QLDA** (đang chạy, dự án → đầu việc nhiều cấp) · **Project-M**
(Báo cáo Dự án cho Ban điều hành — v2.0 đã BỎ hướng gantt/đầu việc) · **phân hệ Công
việc này** (clone Lark, lớp thực thi). QĐ-T1 giữ nguyên.

**QĐ-T2 (chốt 28/08/2026):** khái niệm "Dự án đứng trên task" của bên đó nhận vào bằng
**list kiểu dự án** (A-10) — thêm cờ + hồ sơ lên `tab_work_list`, KHÔNG dựng cặp bảng
project/task riêng. DB làm theo khuôn `tab_work_*` của mình (chốt của người dùng: "về
db mình phải làm theo kiểu, logic của mình").

| Bên QLDA (nhóm) | Bên mình | Xử lý |
|---|---|---|
| A. Dự án (`tab_project`: ngày, trạng thái, thành viên N-N, tiến độ = trung bình % các đầu việc) | A-10 list kiểu dự án | NHẬN, P1 — tiến độ tự tính từ đếm task xong/tổng, không bắt nhập % tay |
| B. Đầu việc cây nhiều cấp không giới hạn, % tiến độ nhập tay, effort ngày công | Task + việc con 2 cấp, tick n/m | GIỮ CỦA MÌNH — 2 cấp + đếm tick đơn giản, khỏi cãi nhau "80% là bao nhiêu" (C-05, Q10) |
| B. Trạng thái "Quá hạn" tự động chuyển | — | NHẬN Ý, KHÁC CÁCH: quá hạn là giá trị DẪN XUẤT lúc đọc (`due_date` < hôm nay và chưa DONE), KHÔNG lưu thành trạng thái — lưu là phải có job đổi qua đổi lại |
| C. Gantt dhtmlx: milestone, phụ thuộc 4 loại FS/SS/FF/SF, baseline, critical path | D-05 (P2) + B-14, B-15 mới | **ĐÃ LÀM 31/08/2026 (CR-226)** — milestone và phụ thuộc đủ 4 loại, có chặn vòng lặp (bên kia tự ghi nhận chưa chặn). **Baseline và critical path vẫn CHƯA** — chưa ai đòi; critical path còn cần `lag_days` tham gia tính toán, mà bộ dời lịch dây chuyền cũng chưa làm. Tự dựng chứ không cài `dhtmlx-gantt` (GPLv2 — 05 §10) |
| D. Kanban theo trạng thái cố định | D-01 kanban cột tùy biến | GIỮ CỦA MÌNH — cột tự đặt kiểu Lark mạnh hơn cột = trạng thái |
| E. OKR check-in (chỉ tiêu — kết quả — nhật ký tiến độ) | — | KHÔNG NHẬN — §9 vẫn ngoài phạm vi; ai đòi thật thì mở CR riêng ở W5 |
| F. Lịch làm việc + ngày nghỉ (nghỉ lễ VN tự sinh, tính ngày kết thúc theo ngày công) | — | **KHÔNG LÀM BÂY GIỜ** (chốt người dùng 28/08/2026) — ghi vào W5 làm sau. Lý do: chỉ cần khi tính ngày kết thúc theo effort / Gantt trừ ngày nghỉ (đều P2); lịch làm việc là dữ liệu cấp CÔNG TY, chỗ đúng là nền HRM dùng chung — làm riêng trong phân hệ này thì HRM ra đời lại phải dời |
| G. Cộng tác, phân quyền theo dự án | §5 hai tầng + nhóm E, H | ĐÃ PHỦ — ma trận OWNER/ADMIN/MEMBER/VIEWER + kế thừa nhóm của mình chi tiết hơn |

**KHÔNG bê DB của bên đó** — các điểm phạm luật nhà nếu chép nguyên: trạng thái lưu CHỮ
tiếng Việt ("Đang thực hiện"…) phạm R2/QĐ-11; `custom_fields` JSON tự do (mình dùng bảng
nhãn có khuôn — B-08); tên bảng `tab_task` trần đụng vùng approval engine (§5.1); xóa dự
án CASCADE cứng (mình lưu trữ + xóa mềm — A-01, B-09); cây đầu việc không giới hạn cấp
(mình chốt 2 cấp).

---

## 5. Phân quyền — hai tầng

> Bản tóm tắt. Chi tiết đầy đủ (seed, SCOPE_FIELDS, kiểm thử bắt buộc) ở
> [`04-phan-quyen.md`](./04-phan-quyen.md).

### 5.1 Tầng hệ thống (RBAC hai trục sẵn có)

- Thêm entity mới vào `ENTITIES` — **đề xuất đặt `work_task`** (kèm `task_list` nếu cần
  tách). CẢNH BÁO đặt tên: chữ "task" trần đã bị chiếm hai chỗ trong mã nguồn — task của
  bộ máy duyệt (`approval/task_service`) và `/api/dashboard/tasks` (Việc cần làm CR-215).
  Route đề xuất `/api/work/...`, module backend `app/modules/work/`, tránh `/api/tasks`.
- Quyền hành động vẫn theo ma trận role chuẩn: ai có `work_task.read` mới thấy thẻ phân
  hệ, `work_task.create` mới tạo được list/task. Mặc định đề xuất: MỌI vai trò đều có
  read + create (đây là công cụ toàn dân, như Diễn đàn) — chốt ở Q1.
- **Điểm lệch khuôn phải xử lý:** phạm vi dữ liệu KHÔNG theo phòng ban như `SCOPE_FIELDS`
  thường, mà theo TƯ CÁCH THÀNH VIÊN: chỉ thấy list mình được mời vào. Nghĩa là entity này
  vào `SCOPE_FIELDS` theo dạng đặc thù (lọc qua bảng thành viên), viết rõ ở tài liệu thiết
  kế bảng — làm ẩu chỗ này là dính đúng lỗ B-07 từng vá.
- Mọi bảng có `company_id` theo luật chung; người thuộc pháp nhân nào thấy list pháp nhân đó.

### 5.2 Tầng trong từng list (membership)

| Việc | Chủ (owner) | Quản trị (admin) | Thành viên (member) | Khách xem (viewer) |
|---|---|---|---|---|
| Xem list + task | x | x | x | x |
| Tạo / sửa task, kéo thả, bình luận | x | x | x | — |
| Xóa task bất kỳ | x | x | Chỉ task mình tạo | — |
| Sửa cột (section), tag của list | x | x | — | — |
| Mời / gỡ thành viên, đổi vai trò | x | x | — | — |
| Sửa tên list, lưu trữ list | x | — | — | — |
| Chuyển quyền sở hữu | x | — | — | — |

Mỗi list đúng một Chủ. Vai trò lưu trên bảng thành viên, là dữ liệu của phân hệ —
KHÔNG đẻ role hệ thống mới cho từng list.

Bảng vai trò trên áp cho cả NHÓM (A-09): gán ở nhóm thì vai trò kế thừa xuống mọi list
bên trong; một người vừa kế thừa vừa được mời riêng vào list thì lấy vai trò cao hơn
(chờ chốt Q9).

---

## 6. Ràng buộc kỹ thuật kế thừa (không bàn lại)

1. Trạng thái, độ ưu tiên lưu `SMALLINT` + `IntEnum`, khai ở `status_catalog.py` +
   `code_sets.py`, FE lấy từ `gen_status_ts.py` (luật R2/QĐ-11 — đây là chức năng MỚI,
   không dính ngoại lệ Thu mua).
2. Bảng mới có `company_id`; model đăng vào `all_models.py` kẻo autogenerate bỏ sót.
3. FE: phân hệ mới `src/modules/work/`, đăng ở `module-registry.ts`; bảng phẳng dùng
   `DataTable`; query key vào `shared/constants/query-keys.ts`; icon lucide, không emoji.
4. Định danh tiếng Anh, chuỗi hiển thị tiếng Việt.
5. Đính kèm đi qua kiểm quyền tệp, không có URL công khai (PQ13).
6. Thông báo: dev tắt email như chuẩn hệ (bell-only), prod theo cấu hình chung.

---

## 7. Các câu hỏi — ĐÃ CHỐT HẾT 28/08/2026

Người dùng chốt hướng "clone từ Lark, mọi thứ theo đề xuất của AI". Đáp án cuối:

| # | Câu hỏi | Chốt |
|---|---|---|
| Q1 | Ai được TẠO task list? | **Toàn dân** — công cụ càng ít rào càng sống |
| Q2 | Mô hình hai tầng trạng thái (cột kanban tùy biến + trạng thái hệ thống SMALLINT)? | **Chốt như §2** — tự do như Lark, giữ luật R2 |
| Q3 | Trường tùy chỉnh bản đầu? | **Nhãn tùy biến kiểu chọn có từ bản đầu** (B-08); kiểu chữ/số/ngày/người để sau (B-13) |
| Q4 | Quản trị hệ thống xem được gì? | **Chỉ thấy DANH SÁCH list** (tên, chủ, số thành viên), không đọc nội dung; cần thì tự thêm mình vào — có ghi nhật ký |
| Q5 | Một hay nhiều PIC? | **Nhiều PIC được, như Lark** (bảng gắn nhiều người) — giao diện khuyến khích một người chính; người theo dõi không giới hạn |
| Q6 | Gắn task vào chứng từ ERP ngay bản đầu? | **Không** — để P2 (B-12) |
| Q7 | Mời cả phòng ban? | **P1** — bản đầu mời từng người |
| Q8 | Tên phân hệ? | **"Công việc"** |
| Q9 | Kế thừa quyền từ nhóm? | **Có kế thừa** xuống mọi list bên trong (list mới tạo trong nhóm cũng tự có); một người vừa kế thừa vừa được mời riêng thì **lấy vai trò cao hơn** |
| Q10 | Việc con có toggle hiện ra kanban? | **Bản đầu tuyệt đối ẩn** (C-05); toggle để P2 nếu có người đòi |

---

## 8. Phác lộ trình (không đặt mốc thời gian)

> Bản tóm tắt. Phạm vi từng phase theo mã tính năng + điều kiện cần/đủ ở
> [`03-lo-trinh-phase.md`](./03-lo-trinh-phase.md).

| Phase | Nội dung | Điều kiện đủ |
|---|---|---|
| W0 | Chốt §7 → thiết kế bảng dữ liệu + API (tài liệu 02) | Các câu Q1–Q8 có đáp án, bảng dữ liệu được duyệt |
| W1 | Backend: bảng + CRUD nhóm/list/section/task/subtask/member/nhãn tùy biến + phân quyền hai tầng (kèm kế thừa từ nhóm) + test | API chạy, test membership-scope + kế thừa nhóm xanh |
| W2 | FE: sidebar cây nhóm → list, kanban kéo thả, panel chi tiết task (kèm nhãn tùy biến), khung nhìn danh sách | Một đội dùng thử được trọn vòng: tạo nhóm → tạo list → mời → giao việc → kéo cột → xong |
| W3 | Bình luận + nhật ký + thông báo giao việc + tab Việc cần làm (`job:{id}`) | Giao việc là chuông kêu; task hiện trong Việc cần làm và dismiss được |
| W4 | Lọc/tìm, Việc của tôi, nhắc hạn Celery, thùng rác, mời theo phòng ban | Các mục P1 xong |
| W5 | Cân nhắc P2 theo nhu cầu thật: custom field, lịch, gantt, gắn chứng từ, tool AI | Chỉ làm cái có người đòi |

---

## 9. Ngoài phạm vi (chưa bàn ở bản này)

- Automation / rule tự động (Lark có, ta chưa cần).
- OKR, chấm công theo task, time tracking (DMS-QLDA có OKR check-in — xem §4b, vẫn không nhận).
- Lịch làm việc + ngày nghỉ (nhóm F của tài liệu QLDA) — dời W5, ưu tiên chờ nền HRM dùng chung (§4b).
- Đồng bộ hai chiều với Lark hoặc công cụ ngoài.
- Tách app/domain riêng — phân hệ này nằm trong ERP, không như Diễn đàn/Help Center.
