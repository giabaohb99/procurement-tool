# Giao việc bao-CR-496 — Lưu bộ lọc riêng từng người + log từng dòng khi nạp (Tra cứu giá hải quan)

> Bản giao việc cho phiên **Erp Agent 3** (đại ca chốt 25/09/2026: «chia cho agent 3 nó làm phần lưu lọc»).
> Bối cảnh đầy đủ: [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md) §11 (nhóm Y, dòng Y-12 · Y-13),
> [`02-thiet-ke-ky-thuat.md`](./02-thiet-ke-ky-thuat.md), tệp yêu cầu gốc của phòng Thu mua
> `C:\Users\Dego Admin\Downloads\YÊU CẦU TÍNH NĂNG TRA CỨU GIÁ HS CODE-NOTE 250926.xlsx` (sheet 2 dòng F07, F01 ghi chú 25/09).
> Số CR **đã đặt chỗ**: `bao-CR-496-hai-quan-luu-bo-loc-log-dong` (dòng có sẵn trong `change-log-bao.md`). Số kế tiếp cho việc khác: 497.

## Luật làm việc (bắt buộc đọc)

- Nhiều phiên đang cùng sửa `erp-v2`. **Làm trong worktree riêng** từ `origin/erp-v2` mới nhất (`git worktree add ../procurement-customs-3 -b customs-496 origin/erp-v2`), KHÔNG sửa cây `procurement-tool` (cây chung).
- Chờ **bao-CR-493** (ERP Agent 2, đợt 1) và **bao-CR-494/495** (Erp Agent 1) gộp vào `erp-v2` rồi mới cắm giao diện vào `customs-price-page.tsx` — backend, bảng, migration làm ngay được. Ba phiên đều đang sửa `customs/service.py`, `controller.py`, `customs-price-page.tsx`: thêm HÀM MỚI / TỆP MỚI, đừng sắp lại mã cũ.
- Luật chung của repo: `CLAUDE.md` gốc; mã tiếng Anh, chuỗi/comment tiếng Việt; trạng thái mới lưu SMALLINT + IntEnum (luật R2); không emoji; mỗi CR một commit và **chỉ commit khi đại ca bảo**; ghi `change-log-bao.md` + `nhat-ky-task.md` (luật viết mô tả ở đầu tệp sổ) rồi chạy `python backend/scripts/sync_task_journal.py` (cần tệp `backend/scripts/.task_sync.env`, chép từ cây `procurement-tool`, tệp này gitignore).
- Cổng kiểm: backend `pytest` chỉ tệp vừa sửa; v2 `npm run typecheck` (0 lỗi) + `npm run lint` (0 lỗi) + `npx vitest run src/modules/procurement`. Stack local mount cây `procurement-tool`, nên ở worktree chạy bằng `docker run` mount worktree:
  `MSYS_NO_PATHCONV=1 docker run --rm -v "<worktree>/backend:/app" -v "<worktree>/test:/app/test" -w /app procurement-tool-api:latest sh -c "pip install -q pytest; python -m pytest test/backend/<tệp> -q"` và
  `MSYS_NO_PATHCONV=1 docker run --rm --cpus 2 -v "<worktree>/frontend-v2:/app" -v /app/node_modules -w /app procurement-tool-erp:latest sh -c "npm run -s typecheck; npx eslint .; npx vitest run src/modules/procurement"`.

## Việc 1 — Lưu bộ lọc riêng từng người (F07)

**Đại ca chốt:** lưu RIÊNG từng người; bảng có sẵn cột «dùng chung» mặc định tắt để sau này mở thành bộ lọc chung mà không làm lại. Người dùng đặt tên một tổ hợp điều kiện đang áp (ví dụ «Abamectin 3.6 EC»), lần sau chọn lại một phát là màn hình về đúng trạng thái đó.

- Bảng mới `tab_customs_saved_filter`: `id`, `user_id` (tài khoản, KHÔNG phải employee_id), `name` (String 120, schema phải khai `max_length` — luật duoc-CR-316), `params` (JSON: đúng bộ tham số của `CustomsFilters` ở `frontend-v2/src/modules/procurement/types/customs.ts` — sau bao-CR-493 gồm q, hs_code, origin, unit, formulation, importer_id, importer_name, partner_id, partner_name, date_from, date_to, currency, incoterm, batch_id, price_min/max, qty_min/max, rate_min/max, tab; sau bao-CR-494/495 thêm product_kind và từ khóa AND/NOT — lưu NGUYÊN chuỗi tham số URL là gọn nhất), `is_shared` (Boolean, mặc định False, chưa dùng), `created_at`/`updated_at`. Trần 50 bộ lọc / người, trần kích thước JSON.
- API dưới `/api/customs/saved-filters`: list (chỉ của tôi, sau này + `is_shared`), create, rename, delete — quyền `customs_price.read` là đủ (đọc được màn thì lưu được bộ lọc của mình); người khác không xóa được của tôi (`user_id` phải khớp, 404 nếu không).
- Giao diện v2: ở thanh lọc của `customs-price-page.tsx` thêm ô «Bộ lọc đã lưu» (chọn → nạp tham số lên URL bằng `setUrlParams`) + nút «Lưu bộ lọc này» (hộp thoại đặt tên; đang chọn một bộ lọc thì có «Cập nhật» / «Xóa»). Đừng lưu vào localStorage: đổi máy là mất (đại ca chốt).
- v1 (`frontend/src/pages/CustomsPrices.tsx`): đại ca 25/09 bảo hải quan bê sang v1 luôn — ERP Agent 2 đang bê đợt 1; việc lưu bộ lọc làm v2 trước, v1 theo sau nếu kịp, ghi rõ trong sổ.
- Bài kiểm backend: người A không thấy/không xóa được của B; trần 50; tên quá dài → 422 ở schema (không phải 500). v2: util dựng/đọc tham số + test.

## Việc 2 — Log từng dòng khi nạp (F01 ghi chú 25/09)

**Đại ca chốt:** dữ liệu GTT02 KHÔNG có số tờ khai, nên không có trạng thái «Cập nhật». Log từng dòng chỉ có ba trạng thái: **Thêm mới · Lỗi · Bỏ qua (trùng trong cùng lô)**.

- Đường nạp ở `backend/app/modules/customs/reader.py` + `importer.py`; nhật ký hiện chỉ ghi dòng cảnh báo/lỗi qua `add_log` của `import_tool` (mức `LogLevel`). Yêu cầu: sau khi nạp, xem được **danh sách đủ mọi dòng** kèm cột trạng thái. Cách gọn: thêm cột `row_status` (SMALLINT + IntEnum `ImportRowStatus`: 1 Thêm mới · 2 Lỗi · 3 Bỏ qua) vào bảng nhật ký dòng hiện có, hoặc bảng mới nếu bảng nhật ký chung của `import_tool` không nên đổi — đọc `import_tool/model.py` rồi tự chọn, ghi lý do vào sổ quyết định `doc/erp/hai-quan/02`.
- «Trùng trong cùng lô» = hai dòng trong CÙNG một tệp giống hệt nhau 32 cột (tệp mẫu có 806 cặp như vậy, xem `01` N-04) — chỉ đánh dấu, KHÔNG được xóa dòng vì đó có thể là hai lô hàng thật; lấy chốt hiện tại của `reader.py` làm chuẩn, đừng đổi luật đếm.
- Giao diện: thẻ «Lịch sử nạp» (v2 sau bao-CR-493 là `customs-history-panel.tsx`) → hộp «Nhật ký lô» thêm ô lọc theo trạng thái và cột trạng thái; tổng số theo từng trạng thái hiện ở đầu hộp.
- Hiệu năng: tệp ~18.000 dòng → ghi log theo lô (bulk insert), không ghi từng dòng một.

## Bàn giao

Xong thì nhắn ERP Agent 2 (phiên «ERP Agent 2 (backup)») và Erp Agent 1 qua SendMessage: mã commit (nếu đại ca cho commit), tệp đã đụng, kết quả cổng kiểm, chỗ nào cần cắm vào trang chính.
