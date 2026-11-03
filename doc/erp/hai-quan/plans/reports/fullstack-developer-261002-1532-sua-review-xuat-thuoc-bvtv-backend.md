# Sửa review BACKEND — xuất Excel «Thuốc BVTV» (chưa commit, erp-v2)

Tiếp quản code của agent trước. Mỗi lỗi viết test TÁI HIỆN trước (xác nhận lỗi có thật bằng cách
đọc code/thực nghiệm openpyxl), rồi sửa cho xanh.

## Tệp thay đổi

**Mới:**
- `backend/app/modules/customs/pesticide_export_marker.py` (43 dòng) — sheet ẩn `_xuat` (C1).
- `backend/app/modules/customs/pesticide_export_safety.py` (36 dòng) — lọc ký tự cấm XML + ép
  chuỗi `=`/`+`/`-`/`@` thành dạng chuỗi (H1 + C3).
- `backend/app/modules/customs/pesticide_export_lock.py` (46 dòng) — khóa chặn bấm dồn liên tiến
  trình (M1), tách riêng khỏi `pesticide_export_service.py` để tệp đó không phình quá mức.
- `backend/app/modules/customs/pesticide_merge_service.py` (75 dòng) — nạp CẬP NHẬT theo trang
  (C1).

**Sửa:**
- `backend/app/modules/customs/pesticide_reader.py` (236→274 dòng) — C2 (lọc id≤0 + từ chối id
  trùng), H2 (cột `quan_ly_tinh_khang_raw`), M3 (dời `MAX_UPLOAD_BYTES` về đây), M5 (thêm chú
  thích, không sửa hành vi), mode nạp (`read_file_with_mode`).
- `backend/app/modules/customs/pesticide_export_columns.py` (viết lại từ bản của agent trước) —
  C2 (`export_id` nhận `dup_source_ids`), H2 (cột raw), bỏ `MANUAL_MARKER_COLUMN`.
- `backend/app/modules/customs/pesticide_export_service.py` (viết lại, 269→228 dòng sau khi tách
  lock) — C1/C2/H1/C3/M2/M3/L2/L6 lắp vào `export_to_tempfile`/`_write_file`.
- `backend/app/modules/customs/pesticide_service.py` (+1 dòng) — `replace_catalog` trả thêm
  `"mode": "replace"`.
- `backend/app/modules/customs/pesticide_controller.py` — `/import` phân nhánh replace/merge,
  dùng `pesticide_reader.MAX_UPLOAD_BYTES` (bỏ hằng số khai lại).
- `backend/app/modules/export_log/registry.py` + `controller.py` (L2) — `ENTITY_LABELS_EXTRA`
  cho nhãn `/system/exports` của entity không đăng ký `EXPORT_ADAPTERS`.
- `backend/app/core/action_catalog.py` (+3 dòng) — khai mã hành động `catalog_merge` (phát hiện
  lúc kiểm thủ công trên DB local, xem mục Concerns).
- `test/backend/test_thuoc_bvtv_xuat_excel.py` (231→627 dòng) — +19 bài mới.

## Từng lỗi → cách sửa → test

**C1 (nạp lại tệp xuất theo trang là CẬP NHẬT).** Thêm sheet ẩn `_xuat` (`pesticide_export_
marker.write_marker`): `scope=page` → `detect_mode()` trả `"merge"`; `scope=all` hoặc KHÔNG có
sheet (bản cào gốc) → `"replace"`. `pesticide_reader.read_file_with_mode()` (mới, song song
`read_file` cũ — KHÔNG đổi chữ ký `read_file`/`read_json`/`read_xlsx` để 20+ bài test cũ của
`test_hai_quan_thuoc_bvtv*.py` không phải sửa). `pesticide_merge_service.merge_catalog`: khớp
theo `source_id`, GIỮ nguyên `id` DB (update Core, không xóa-chèn-lại), thêm thuốc chưa có, chạy
LẠI TOÀN BỘ `retag_all` (không tách — tagger suy alias từ TOÀN BỘ `active_ingredient`, tách theo
phần đổi có thể bỏ sót dòng dùng alias mới sinh/mất — nêu rõ trong docstring, không coi là lỗi).
Controller `/import` trả thêm `mode` + câu khác nhau. Test: `test_nap_tep_xuat_theo_trang_da_sua_
chi_cap_nhat_dung_cac_thuoc_do` (tệp đính kèm bằng `FileLink`/`StoredFile` thật — còn nguyên sau
merge), `test_che_do_nap_theo_tung_loai_tep`, `test_tep_xlsx_khong_co_sheet_xuat_la_ban_cao_goc_
thi_thay_toan_bo`, `test_nap_tep_xuat_toan_bo_van_la_thay_toan_bo_qua_http` (qua HTTP thật).

**C2 (id thủ công / trùng source_id không bao giờ đụng id dương khác).** `export_id()` trả
`-p.id` cho (1) thuốc thủ công, (2) thuốc nguồn mà `source_id` đang bị HAI thuốc dùng chung
(`_duplicate_source_ids`, DB local hiện **0** trùng — đã `SELECT` kiểm, xem Concerns). Bộ đọc bỏ
MỌI dòng id≤0 ở CẢ HAI sheet, và TỪ CHỐI (ValueError) nếu hai dòng list-sheet cùng id DƯƠNG.
Thay luôn `MANUAL_MARKER_COLUMN` (cơ chế riêng cho thủ công) bằng CHÍNH quy tắc id≤0 — gọn, một
cơ chế, đúng gợi ý "giữ một cơ chế" của đề bài. Quyết định cho câu hỏi "2 thuốc nguồn trùng
source_id": xuất CẢ HAI với id âm (không chọn ai thắng — đơn giản hơn, phần còn lại của danh mục
không bị ảnh hưởng), nạp lại bỏ cả hai, admin tự xử lý trùng ở DB. Test tái hiện bằng cách dựng
TRỰC TIẾP state DB (chèn tay một thuốc thủ công mang `id` = `source_id` của thuốc nguồn khác) —
`test_thuoc_tu_them_co_id_trung_source_id_khac_khong_bi_gop_nham_pham_vi`: xác nhận bằng tay (script
Python độc lập mô phỏng `read_xlsx` CŨ) rằng dòng phạm vi của thuốc thủ công LỌT vào thuốc nguồn
nếu không sửa — xem Concerns. Thêm `test_export_id_tra_am_...` (đơn vị), `test_hai_thuoc_nguon_
trung_source_id_...`, `test_doc_tep_co_hai_dong_thuoc_cung_id_duong_bi_tu_choi`, `test_doc_bo_qua_
moi_dong_id_am_hoac_bang_khong`.

**C3 + H1 (ô Excel an toàn).** `pesticide_export_safety.safe_row/safe_cell`: lọc
`ILLEGAL_CHARACTERS_RE` trước, rồi nếu chuỗi bắt đầu `=`/`+`/`-`/`@`/tab/CR → `WriteOnlyCell` +
`data_type="s"`. Thực nghiệm xác nhận TRƯỚC khi sửa: `Workbook(write_only=True).append(["=1+1"])`
tự suy `data_type='f'`; `.append(["bad\x00"])` ném `IllegalCharacterError` ngay (export CRASH,
không phải "tệp hỏng âm thầm" như đoán ban đầu — cùng nghiêm trọng, chặn HẲN việc xuất). Test:
`test_chuoi_bat_dau_bang_dau_bang_ghi_dang_chuoi_khong_phai_cong_thuc` (kiểm cả `data_type` lẫn
round-trip), `test_ky_tu_dieu_khien_cam_khong_lam_vo_luot_xuat`.

**H2 (cột nguyên văn `quan_ly_tinh_khang_raw`).** Thêm cột mới, bộ đọc ưu tiên nếu có+không rỗng.
Tái hiện: `resistance = "A: 1 | 2; B; C: x:y|z"` (chữ tự do có `;`/`:` không phải dấu phân tách)
— dò tay qua `_resistance()`/partition logic CŨ: mục `B` (không có `: `) bị **lọc rỗng mất hẳn**,
mục `C: x:y|z` đổi khoảng trắng. Cột raw bỏ qua bước tách-ghép, trả nguyên văn. Test:
`test_resistance_tu_do_co_hai_cham_va_cham_phay_round_trip_nguyen_van`.

**M1 (khóa chặn bấm dồn qua nhiều tiến trình).** `pesticide_export_lock.export_lock`: giữ set
trong-tiến-trình (nhanh, đủ cho SQLite/test) + thêm `GET_LOCK('pesticide_export_<uid>', 0)` trên
kết nối MySQL riêng (giống `_import_lock`), nhả trong `finally`. Test dựng `_FakeMySQLServer` có
TRẠNG THÁI THẬT (không phải Mock vô tri) để hai `_FakeDb` (giả lập hai tiến trình, mỗi cái XÓA
entry của mình trong set trong-tiến-trình) vẫn thấy khóa của nhau qua "MySQL" dùng chung —
`test_khoa_xuat_dung_vung_qua_nhieu_tien_trinh_uvicorn` (RED trên code cũ: hàm `_export_lock`
với 2 tham số không tồn tại ở bản cũ — `_busy_guard(user_id)` không nhận `db`, không có nhánh
MySQL nào để kiểm). `test_khoa_mysql_duoc_nha_trong_finally_du_than_lenh_nem_loi` kiểm nhả khóa
khi thân lệnh ném lỗi.

**M2 + M3 (dọn tệp tạm khi lỗi sau khi ghi, trần kích thước xuất).** `export_to_tempfile` bọc
`getsize`/`_check_output_size`/`_record_log` trong try/except xóa-rồi-ném-lại. `_check_output_
size` so với `reader.MAX_UPLOAD_BYTES` (dời từ `pesticide_controller.py` về `pesticide_reader.py`
— "một chỗ dùng chung", M3 yêu cầu). Test spy `_write_file` lấy `path` thật rồi ép lỗi ở bước sau
(`_record_log` ném `RuntimeError`, hoặc trần kích thước giả `10` byte) — xác nhận tệp bị xóa.

**L2 (nhãn đọc được ở `/system/exports`).** `filter_summary` đổi từ `"scope=all"` thô thành
`"Thuốc BVTV — toàn bộ"` / `"Thuốc BVTV — trang N (lọc: ...)"`. `entity_label` của `customs_
price` (chỉ pesticide export dùng entity này — đã `grep` xác nhận không ai khác ghi `ExportLog`
với entity này) đọc qua `ENTITY_LABELS_EXTRA` MỚI ở `export_log/registry.py` — **KHÔNG** đăng ký
vào `EXPORT_ADAPTERS` (không bật nút "Xuất" chung/`run_export()`), đúng "cách ít đụng nhất".

**L6 (giờ VN dùng chung).** `pesticide_export_service.py` đổi từ tự khai `VN_OFFSET =
timedelta(hours=7)` sang `from app.core.export_xlsx import VN_OFFSET` — hằng đó ĐÃ được 3 module
khác import sẵn (`report_period.py`, `employee/report_headcount_events.py`,
`approval/report_service.py`), xác nhận là "helper có sẵn" đúng nghĩa (import được, không phải
chỉ là một dòng lặp lại ở nhiều nơi — rà cả repo thấy một nửa số module VẪN tự khai local, nhưng
có nguồn gốc import được thì nên dùng, không nhân bản thêm). Test `is` identity — RED trên code
cũ vì hai `timedelta(hours=7)` tạo riêng không `is` nhau.

**M5 (KHÔNG sửa).** Thêm một dòng chú thích ở `_text()` giải thích hành vi gộp khoảng trắng/
xuống dòng là SẴN CÓ, không đổi gì. Không viết test (đề bài yêu cầu không sửa).

## Phát hiện phụ lúc kiểm thủ công (ngoài 11 mục đề bài)

Chạy `merge_catalog` thật trên DB local in ra cảnh báo: `Mã hành động chưa khai trong
ACTION_CATALOG: 'catalog_merge'`. Thêm `ActionCode("catalog_merge", ...)` vào
`backend/app/core/action_catalog.py` (cạnh `catalog_import` đã có) — không có việc này thì nhật
ký thao tác (KHÁC `tab_export_log`) hiện nhóm "Không rõ" cho mọi lượt nạp CẬP NHẬT.

## Test

```
docker compose exec -T api python -m pytest test/backend/test_thuoc_bvtv_xuat_excel.py \
  test/backend/test_hai_quan_thuoc_bvtv.py test/backend/test_hai_quan_thuoc_bvtv_crud.py \
  test/backend/test_hai_quan_thuoc_bvtv_lien_quan.py test/backend/test_pham_vi_khai_du_b07.py \
  test/backend/test_hai_quan_doi_chieu_hoat_chat_cam.py test/backend/test_pham_vi_luat_bat_bien.py \
  test/backend/test_export_data.py test/backend/test_import_catalog.py \
  test/backend/test_bo_ma_hanh_dong_cr358.py test/backend/test_nhat_ky_lop_may_cr312.py \
  test/backend/test_nhat_ky_p6_cr448.py test/backend/test_va_nhat_ky_thao_tac.py -q
```
→ **355 passed, 0 failed** (27 bài trong `test_thuoc_bvtv_xuat_excel.py`: 8 cũ + 19 mới).

Bốn bài cuối (`test_export_data`, `test_import_catalog`, `test_bo_ma_hanh_dong_cr358`,
`test_nhat_ky_*`) chạy thêm vì tôi đụng `export_log/registry.py`+`controller.py` và
`action_catalog.py` — không nằm trong lệnh gốc đề bài nhưng cần để chắc không vỡ gì ở hai module
dùng chung đó.

## Kiểm thủ công trên DB local (đã làm, đã trả về như cũ)

1. Xuất `scope=all` (2,35s, 2 794 290 byte) → lưu làm bản khôi phục.
2. Nạp lại bản đó: `mode=replace`, `thuoc=6919` (không đổi), `pham_vi=15309` (không đổi),
   `dropped=0`.
3. Xuất `scope=page` (trang 1, cỡ 20) → sửa tay TÊN của thuốc đầu trang bằng openpyxl → nạp lại:
   `mode=merge`, `updated=20, added=0` (cả 20 dòng trong trang đều "cập nhật" vì đã có sẵn, dù
   chỉ 1 ô thực sự đổi giá trị — `merge_catalog` không so sánh cũ/mới để chỉ đếm dòng NÀO thay
   đổi, chỉ đếm "khớp = update, không khớp = add" — xem Concerns), tổng `thuoc=6919` KHÔNG đổi,
   tên đã đổi đúng 1 thuốc (`source_id=2815`).
4. Nạp lại bản khôi phục ở bước 1 → tên về lại nguyên, `thuoc=6919`, `pham_vi=15309` — **DB local
   đã về đúng như trước khi kiểm**.

## Hợp đồng API cuối (đổi so với bản của agent trước)

`POST /api/customs/pesticides/import` — giữ NGUYÊN các trường cũ (`pesticides`, `uses`,
`kept_manual`, `dropped`, `retag`) + trường MỚI `mode: "replace" | "merge"` (+ `updated`/`added`
chỉ có khi `mode="merge"`, FE có thể bỏ qua). Câu `message`:
- `mode="replace"`: `"Đã thay toàn bộ danh mục: N thuốc"` (cũ: `"Đã nạp N thuốc BVTV"` — ĐỔI
  chữ, agent FE cần biết nếu đang so khớp chuỗi message).
- `mode="merge"`: `"Đã cập nhật N thuốc (thêm mới M), giữ nguyên phần còn lại"`.

`GET /api/customs/pesticides/export` — không đổi tham số/response shape; tệp `.xlsx` xuất ra giờ
có thêm sheet ẩn `_xuat` + cột `quan_ly_tinh_khang_raw` (FE không cần biết, chỉ ảnh hưởng
nạp lại). Cột `thuoc_tu_them` (cũ) KHÔNG còn trong tệp — nếu FE có code soi cột này (không thấy
grep ra gì) thì cần gỡ.

## Concerns

- "2 thuốc nguồn trùng source_id" KHÔNG xảy ra trên DB local hiện tại (đã `SELECT ... GROUP BY
  source_id HAVING COUNT>1` → 0 dòng) — code C2 cho ca này là phòng xa theo đúng yêu cầu đề bài,
  chưa có dữ liệu thật để xác nhận thêm.
- `merge_catalog` không phân biệt "update vì giá trị thực sự đổi" với "update vì khớp source_id
  nhưng y hệt cũ" — cả hai đều tính vào `updated`. Đúng ý "chỉ cập nhật đúng các thuốc có trong
  tệp" của đề bài (tệp theo trang luôn chỉ chứa thuốc trong trang đó), không phải lỗi, nhưng số
  `updated` trả về KHÔNG phải "số ô thực sự đổi" — nêu rõ ở đây để FE không hiểu nhầm con số.
- Chưa ghi mục vào `doc/tai-lieu-ky-thuat/nhat-ky-task.md` — theo đúng quyết định của agent
  trước, việc này thuộc tầng điều phối, không nằm trong phạm vi được giao.
- Không commit (đúng yêu cầu).

**Status:** DONE
