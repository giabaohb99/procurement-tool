# Kế hoạch rà soát code API (hiệu năng + đúng đắn truy vấn)

Trạng thái: ĐANG LÀM · Mở ngày: 21/08/2026 · Chủ đề: đi soát lại toàn bộ
endpoint API ở MỌI phân hệ, tập trung các mẫu truy vấn dễ vỡ khi dữ liệu lớn.

## 1. Vì sao có plan này

Test lại **báo cáo khảo sát** (`survey/service.py::report_rows`) phát hiện câu query
dài bất thường: code gom `sids = list(surveys.keys())` rồi `.in_(sids)` → khi có 2666
phiếu (dữ liệu import lịch sử), SQLAlchemy render `IN (1,2,3,…,2666)` — hàng nghìn
tham số nhồi thẳng vào SQL. Đã đổi sang subquery `WHERE survey_id IN (SELECT id …)`.

Một lỗi kiểu này lộ ra thì gần như chắc còn ở các endpoint list/report/export khác —
lúc data còn nhỏ không ai thấy, tới lúc lớn mới sập. Nên đi rà **có hệ thống** thay vì
chờ gặp đâu vá đó.

## 2. Bộ tiêu chí soát (checklist cho từng endpoint)

Mỗi endpoint (ưu tiên `list` / `report` / `export`) soi qua các mẫu sau:

| # | Mẫu lỗi | Dấu hiệu | Cách sửa |
|---|---|---|---|
| C1 | **IN(list id) dựng từ Python** | `list(...keys())` / `[x.id for x in ...]` rồi `.in_(ids)` | Đổi sang subquery `.with_entities(Model.id)` hoặc JOIN |
| C2 | **N+1 query trong vòng lặp** | `db.query(...)` hoặc lazy-load attr NẰM TRONG `for` | Query gộp trước vòng lặp; `selectinload`/`joinedload` |
| C3 | **Nạp hết vào RAM** | `.all()` toàn bảng rồi xử lý; giữ dict/list khổng lồ | Giới hạn phạm vi + phân trang; xử lý theo lô |
| C4 | **Trả không phân trang / không trần** | endpoint trả toàn bộ, không `page/page_size`, không chặn trần | Bắt buộc phân trang hoặc chặn trần + yêu cầu lọc hẹp |
| C5 | **Lấy full ORM object khi chỉ cần vài cột** | `.all()` cả entity nhưng chỉ đọc 5–6 field | `with_entities` / `load_only` |
| C6 | **Thiếu index** cho cột lọc/join/sort | cột `*_id`, cột hay lọc/sort không `index=True` | Thêm index (migration) |
| C7 | **Sort bị tầng service ghi đè** | controller `apply_sort_from_request` nhưng service lại `order_by(id.desc())` | Bỏ order_by cứng, để sort từ request quyết |
| C8 | **Xuất file lớn không stream** | build list khổng lồ rồi mới ghi Excel/CSV | `.yield_per(N)` + ghi dần |
| C9 | **Whitelist lọc/sort** | `FILTERABLE` / cột sort có kiểm để chống injection và tránh lọc "câm" | Đối chiếu field FE gửi với whitelist BE |
| C10 | **Range/khoảng ngày quét full** | lọc ngày bằng chuỗi, không tận dụng index | Chuẩn hóa cột ngày + index |

## 3. Phạm vi theo phân hệ (bảng tiến độ)

Đánh dấu khi soát xong từng phân hệ. Ưu tiên endpoint danh sách + báo cáo + xuất file.

| Phân hệ | Endpoint trọng điểm | Tình trạng soát | Ghi chú |
|---|---|---|---|
| Thu mua | PYC list, ĐMH list, YCBG list, Khảo sát list + **report_rows**, các báo cáo | Một phần | `report_rows` + `list_surveys` đã vá C1; C9 đã vá ở 4 màn (CR-127). `report_rows` còn C3/C4/C5; các báo cáo còn lại chưa soát |
| Sản xuất | HĐ, NCC, SP, Nhóm hàng, ĐVT (list) | Một phần | NCC + SP đã vá C7; HĐ đã vá C9 (CR-127). Chưa soát C1..C5 |
| Tài chính | YCTT, công nợ, phân bổ thanh toán, payment-request | Chưa | công nợ dễ dính C2/C3 |
| Kho | list + báo cáo tồn/nhập/xuất | Chưa | báo cáo tổng hợp dễ C3 |
| Nhân sự | danh sách nhân sự, phòng ban | Chưa | |
| Văn thư | danh sách văn bản, phạm vi áp dụng (CR-117) | Chưa | by-companies gộp 2 nguồn, soi C2 |
| Hệ thống | nhật ký kiểm toán (audit log), sao lưu | Chưa | audit log lớn dần theo thời gian → C3/C4 |
| Phiếu hỗ trợ | danh sách ticket | Chưa | |
| Diễn đàn | feed, thread box, **posts/search** | Chưa | `posts/search` có ghi chú sẵn ở §5 (LIKE full-scan) |

## 4. Cách làm

1. Đi từng phân hệ theo bảng §3, mỗi endpoint chấm qua checklist §2.
2. Mỗi phát hiện → tách **CR nhỏ** riêng (kèm test tái hiện: dựng data lớn/nhiều dòng,
   khẳng định số query / thời gian / hình dạng SQL), ghi vào `change-log.md`.
3. Công cụ xác nhận:
   - Bật `echo=True` (hoặc `SQLALCHEMY_ECHO`) tạm ở dev để xem SQL thực.
   - `EXPLAIN` câu nghi ngờ xem có ăn index không.
   - Slow query log của MySQL để bắt câu chậm thật.
4. **Không** tối ưu mù: chỉ sửa chỗ có bằng chứng (SQL/EXPLAIN/thời gian), tránh đổi
   code làm phức tạp mà không đo được lợi ích.

## 5. Đã biết trước (đưa thẳng vào danh sách việc)

- `survey/service.py::report_rows` — **đã vá** C1 (IN(list) → subquery), commit `96158d1`.
  Còn tồn: nạp hết Survey vào RAM + trả không phân trang (C3/C4), lấy full object (C5).
- `survey/controller.py::list_surveys` — **đã vá** C1 (CR-127): ô tìm kiếm gom `survey_id`
  của bảng dòng SP ra list Python rồi `.in_(list)`, trong khi bảng thật đã hơn 5000 dòng.
  Tách thành `search_condition()` dùng `IN (SELECT ...)`. Đây là bằng chứng cho §1: một mẫu
  lỗi lộ ra ở endpoint này thì gần như chắc còn nguyên ở endpoint khác cùng phân hệ.
- `supplier/service.py::list_suppliers` và `product/service.py::list_products` —
  **đã vá** C7 ở `96158d1`: `order_by(id.desc())` giờ chỉ là nhánh lùi khi query chưa có
  `order_by`, không đè `apply_sort_from_request` nữa. Trùng với việc dựng sort ở
  [14-filter-sort-man-danh-sach-v2.md](../erp/14-filter-sort-man-danh-sach-v2.md).
- `forum/service.py::search_posts` — **chưa cần sửa, ghi để canh ngưỡng** (03/09/2026, bao-CR-273.1): tìm bài dùng `LIKE '%kw%'` trên `title` + `body` (wildcard đầu chuỗi → không ăn index, quét toàn bảng) và `count()` chạy quét lần hai. Dữ liệu hiện vài chục bài nên vô hại, nhưng từ bao-CR-273.1 ô tìm header sổ gợi ý khi gõ → tần suất gọi tăng theo người dùng. **Ngưỡng hành động: bài đông cỡ chục nghìn** thì (1) FULLTEXT index ngram parser cho MySQL 8 thay LIKE, (2) quick search bỏ `count()` chính xác — lấy `limit+1` để biết còn nữa, (3) cân nhắc bóc chữ trơn ra cột riêng để khỏi so chữ trên markup HTML của bài rich (giờ tìm "strong" khớp oan tên thẻ). Phía FE đã chặn sẵn: min 2 ký tự, debounce 250ms, cache 30s, per_page=5.
- **C9 (lọc "câm") có ca thật, không phải lo xa** — xem CR-127: whitelist của bộ lọc điều kiện
  dùng chung với whitelist param trần, nên field FE khai mà backend loại đi thì bị bỏ qua
  KHÔNG báo lỗi. Soát C9 ở phân hệ nào cũng phải đối chiếu danh sách field FE gửi với
  whitelist BE, đừng chỉ đọc code backend.

## 6. Phạm vi / ràng buộc

- Plan này là **rà soát + sửa theo bằng chứng**, không phải viết lại. Giữ hành vi
  API không đổi với người dùng.
- Tách CR nhỏ, mỗi CR một mẫu lỗi / một endpoint để dễ kiểm và dễ lùi.
- Chưa đặt mốc thời gian — chèn vào giữa các đợt tính năng khi có chỗ trống.
