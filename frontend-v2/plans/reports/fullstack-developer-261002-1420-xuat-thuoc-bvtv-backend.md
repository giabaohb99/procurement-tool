# Backend — xuất Excel «Thuốc BVTV» (round-trip với «Nạp danh mục»)

Nhánh `erp-v2`, chưa commit (theo yêu cầu).

## Việc đã làm

1. `backend/app/modules/customs/pesticide_reader.py` (+10 dòng) — thêm `MANUAL_MARKER_COLUMN =
   "thuoc_tu_them"` (cột THÊM ở cuối sheet «Danh sach thuoc», bản cào gốc không có) + bỏ qua dòng
   có cột này = "1" trong `read_xlsx`. Giải quyết vấn đề thuốc tự thêm (`is_manual`) luôn mang
   `source_id = 0`: nhiều thuốc tự thêm xuất ra cùng id 0 sẽ đụng khóa nối hai sheet nếu nạp lại
   coi chúng là thuốc nguồn — đánh dấu + bỏ qua là cách an toàn nhỏ nhất (gợi ý trong đề bài),
   KHÔNG đổi gì ở đường đọc JSON/tệp cào gốc (tệp gốc không có cột này nên luôn đọc rỗng = không
   ảnh hưởng gì khi nạp tệp cào thật).
2. `backend/app/modules/customs/pesticide_service.py` (+11 dòng) — thêm `export_query(db, q,
   status, pest_group, sector, banned_only, banned_regulation_id)`: câu truy vấn đã lọc+sắp xếp Y
   HỆT `list_pesticides` (dùng lại `_filtered`/`_banned_ids`/`banned_match`), chưa phân trang —
   `scope=page` dùng lại đúng hàm này, không chép logic lọc.
3. `backend/app/modules/customs/pesticide_export_columns.py` (MỚI, 80 dòng) — khai `LIST_HEADER`
   (26 cột: đúng 25 cột gốc bản cào + cột đánh dấu thủ công) và `USE_HEADER` (12 cột gốc), hàm
   `export_id()` (id xuất = `source_id` cho thuốc nguồn, `id` hệ thống cho thuốc tự thêm — tránh
   đụng 0), `list_row()`/`use_rows()` dựng một dòng Excel từ ORM object, `_dedupe_join()` gộp
   cây trồng/dịch hại duy nhất giữ thứ tự xuất hiện (khớp cách bản cào gộp cột).
4. `backend/app/modules/customs/pesticide_export_service.py` (MỚI, 188 dòng) — lõi nghiệp vụ:
   - `scope=all`: đếm tổng (COUNT, không `.all()`) → so trần `pesticide_reader.MAX_RECORDS`/
     `MAX_USE_ROWS` (đọc thuộc tính module, không chép hằng số) → 422 nếu vượt; ghi THEO LÔ 1.000
     bằng `Workbook(write_only=True)` ra tệp tạm `tempfile.mkstemp`, `db.expunge_all()` mỗi lô.
   - `scope=page`: gọi `export_query` + `.offset().limit()`, viết trực tiếp (đã bị chặn bởi
     `page_size` nên không cần theo lô).
   - Chặn bấm dồn `scope=all`: `_busy_guard` — `set[int]` trong tiến trình theo `user.id`, lồng
     trong `try/finally` (cùng tinh thần `_import_lock` nhưng không cần khóa MySQL — xem lý do
     trong docstring).
   - Ghi `tab_export_log` (entity=`customs_price`, fmt=`xlsx`, row_count=số thuốc, `file_id=0` —
     xem quyết định ở mục dưới), KHÔNG đăng ký vào `export_log.registry.EXPORT_ADAPTERS`.
5. `backend/app/modules/customs/pesticide_controller.py` — thêm `GET /export` (đặt TRƯỚC
   `/{pesticide_id}` và `/{pesticide_id}/related`), gác `require("customs_price", "export")`,
   trả `FileResponse` + `BackgroundTask(os.remove, path)` xóa tệp tạm sau khi gửi xong.
6. `test/backend/test_hai_quan_thuoc_bvtv.py` — vá `test_every_route_is_guarded` (route mới phải
   có mặt, test này soi ĐỦ các route của router, không vá là đỏ ngay).
7. `test/backend/test_thuoc_bvtv_xuat_excel.py` (MỚI) — 8 bài, xem mục Test dưới.

## Quyết định ghi nhật ký xuất (theo luật `doc/erp/16-...md` §2.1/§9.2, như đề bài yêu cầu nói rõ)

**Có ghi** một dòng vào `tab_export_log` cho MỌI lần gọi `/export` (QĐ-I5 "ghi nhận MỌI endpoint
export"), nhưng **KHÔNG** đăng ký vào khung `export_log.registry.EXPORT_ADAPTERS`/`run_export()`.
Lý do: khung đó (Đ-13b, đã triển khai thật ở `export_log/service.py`) xuất MỘT bảng phẳng bằng cột
chung (`export_xlsx.Col`, nhãn đẹp tiếng Việt, build cả workbook trong bộ nhớ qua `Workbook()`
thường, trần 100.000 dòng). Mục Thuốc BVTV cần HAI sheet lồng nhau (thuốc + phạm vi sử dụng) với
**tên cột cố định đúng hệt bản cào gốc** (không phải nhãn đẹp) để `pesticide_reader` nạp lại
được, và phải ghi theo lô ra đĩa (không build trong bộ nhớ) vì đây là nguồn duy nhất bắt buộc
round-trip + có thể lớn dần theo thời gian. Ép vào khung chung sẽ phá vỡ MỘT trong hai yêu cầu đó.
Giải pháp: tách endpoint riêng (đúng tinh thần Đ-13b vẫn cho phép — nhiều export viết tay khác
như `employee/controller.py` export CSV cũng đứng ngoài khung này), chỉ **dùng chung bảng nhật
ký** `tab_export_log` để vẫn truy vết được ai xuất gì — không lưu `file_id` (không có "tải lại
đúng file đã xuất" như `/api/exports/{id}/file`): đọc hết tệp tạm vào bộ nhớ lần nữa chỉ để lưu
lại lên storage là triệt tiêu đúng lợi ích streaming-ra-đĩa; xuất lại thì gọi lại API.

## Xử lý thuốc tự thêm (is_manual) — không nhân đôi, không gộp nhầm id 0

Chọn phương án "đánh dấu nguồn ở một cột, bộ đọc bỏ qua" (phương án 1 trong hai gợi ý của đề bài).
Cột `thuoc_tu_them` ở cuối sheet «Danh sach thuoc» (không có trong bản cào gốc, nên tệp cào thật
không bao giờ có cột này → không ảnh hưởng gì khi nạp tệp cào). `export_id()` dùng `id` hệ thống
(không phải `source_id = 0`) cho dòng thuốc tự thêm khi ghi vào CẢ HAI sheet — vẫn join đúng giữa
hai sheet trong tệp xuất (để người dùng xem/đối chiếu phạm vi của từng thuốc tự thêm), nhưng vì
dòng đó bị bộ đọc bỏ hẳn trước khi dùng `id` để nối gì cả, nên dù hai thuốc tự thêm có id trùng
nhau (về lý thuyết — thực tế không trùng vì là PK auto-increment) cũng không ảnh hưởng. Test
`test_export_all_then_reimport_is_a_pure_round_trip` dựng ĐÚNG ca "hai thuốc tự thêm cùng
`source_id = 0`" và xác nhận nạp lại không nhân đôi, không đụng id.

## Kiểm tra dữ liệu lớn (thủ công, trên DB local thật — không phải SQLite test)

```
thuoc: 6919   pham_vi: 15309   tu_them: 0
```
Xuất `scope=all`: 1.96s, tệp 2.69 MB, bộ nhớ tăng ~13 MB (`ru_maxrss` trước/sau, trần container
2 GB — an toàn nhiều). Đọc lại (`pesticide_reader.read_file`) ra ĐÚNG **6919 thuốc / 15309 dòng
phạm vi** — khớp 100% số liệu đề bài nêu. (Không chạy `replace_catalog` thật trên DB local để
tránh đụng dữ liệu không cần thiết — tính đúng đắn của việc nạp lại đã được bài test round-trip ở
dưới xác nhận bằng dữ liệu tổng hợp đa dạng hơn DB thật lúc này, vì DB thật hiện chưa có thuốc tự
thêm/ngày rỗng/trạng thái hết hiệu lực để thử.)

## Tests

`docker compose exec -T api python -m pytest test/backend/test_thuoc_bvtv_xuat_excel.py
test/backend/test_hai_quan_thuoc_bvtv.py test/backend/test_hai_quan_thuoc_bvtv_crud.py
test/backend/test_hai_quan_thuoc_bvtv_lien_quan.py test/backend/test_pham_vi_khai_du_b07.py
test/backend/test_hai_quan_doi_chieu_hoat_chat_cam.py -q` → **146 passed**. Chạy thêm lưới rộng
hơn `-k "customs or pesticide or thuoc_bvtv or export_log or xuat_du_lieu"` → **122 passed**
(không trùng tập trên 100%, phủ thêm `export_log`).

8 bài mới trong `test_thuoc_bvtv_xuat_excel.py`:
- `test_export_all_then_reimport_is_a_pure_round_trip` — 3 thuốc nguồn (bình thường/hết hiệu
  lực/ngày rỗng + tên có HTML entity `&amp;`) + 2 thuốc tự thêm CÙNG `source_id=0`; so trực tiếp
  `R.read_file(exported) == R.read_json(original_raws)` (sau khi loại thuốc tự thêm) — khớp từng
  trường (tên, hoạt chất, ngày, trạng thái, **độc tính, kháng thuốc nhiều hoạt chất, tóm tắt, url,
  phạm vi sử dụng**); rồi `replace_catalog` lại → danh mục không đổi, thuốc tự thêm không nhân
  đôi, id không bị cấp lại; nạp LẦN NỮA vẫn không nhân đôi.
- `test_export_logs_one_row_per_call` — `tab_export_log` có đúng 1 dòng, `row_count`/`fmt` đúng.
- `test_export_page_matches_list_filter_sort_and_page` — lọc `q="Omega"` + trang 2 cỡ 2 khớp
  Y HỆT `list_pesticides` (và loại đúng thuốc không khớp lọc).
- `test_khong_co_quyen_export_thi_403` / `test_co_quyen_export_tra_ve_file_xlsx_qua_http` — qua
  HTTP thật (`TestClient` + `cap_quyen`), đúng khóa `customs_price.export`.
- `test_vuot_tran_so_thuoc_la_422` / `test_vuot_tran_so_dong_pham_vi_la_422` — monkeypatch
  `pesticide_reader.MAX_RECORDS`/`MAX_USE_ROWS` nhỏ → 422, câu tiếng Việt có "vượt trần".
- `test_bam_don_xuat_toan_bo_la_429` — lượt hai của CHÍNH người đó trong lúc lượt đầu còn "đang
  chạy" (giả lập bằng cách tự thêm vào `_EXPORTING_ALL`) → 429; khóa được dọn đúng ở `finally`.

Type check: không có mypy/ruff cấu hình cho backend (đã rà `pyproject.toml`/`.flake8`/`ruff.toml`
— không có tệp nào) — cổng duy nhất là pytest, đã xanh.

## Hợp đồng API — khớp đề bài, không lệch

`GET /api/customs/pesticides/export?scope=page|all` + `q, status, pest_group, sector,
banned_only, banned_regulation_id, page, page_size` (param phân trang chuẩn `pagination()` —
đúng tên FE đang dùng cho list). Trả `.xlsx`, `Content-Disposition: attachment`,
`thuoc-bvtv-toan-bo-YYYYMMDD-HHMM.xlsx` / `thuoc-bvtv-trang-<n>-YYYYMMDD-HHMM.xlsx` (giờ VN).
Gác `require("customs_price", "export")` — action `export` ĐÃ có sẵn trong ma trận quyền
(`ACTIONS`), và vai trò `market_lookup` (seed, bao-CR-557) ĐÃ có `export` trên `customs_price` từ
trước — không cần sửa seed. Lỗi 422/403/429 theo phong bì JSON chuẩn (qua handler toàn cục của
`main.py`, không cần controller tự bọc).

## Hạn chế / lưu ý cho đợt sau

- `pesticide_reader.py` (236 dòng) và `pesticide_service.py` (218 dòng) đã VƯỢT 200 dòng — CẢ HAI
  đã gần/vượt ngưỡng này TRƯỚC khi tôi sửa (227/208 dòng), tôi chỉ thêm 10-11 dòng mỗi tệp cho
  tính năng này. Không tách thêm module trong đợt này để tránh xáo trộn hai tệp lõi đang được
  nhiều test khác phụ thuộc trực tiếp — để lại cho một đợt dọn riêng nếu cần.
- Chưa ghi mục vào `doc/tai-lieu-ky-thuat/nhat-ky-task.md` (luật ghi nhật ký mỗi phiên làm việc)
  — đây là việc của tầng điều phối (main session / `project-manager`), không nằm trong phạm vi
  file được giao cho tác vụ backend này.
- Nút bấm/UI phía `frontend-v2` do agent khác làm song song theo đúng hợp đồng trên — không đụng.

## Không giải quyết / câu hỏi còn treo

- Không có.
