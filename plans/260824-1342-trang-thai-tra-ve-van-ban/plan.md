# Văn bản — tách trạng thái «Trả về» và «Đã từ chối»

Trạng thái: XONG (CR-143, CR-144) · Nhánh `erp-v2` · CR mới (đánh số khi ghi change-log)

## Vì sao

Hôm nay cả ba nhịp kết thúc phiên duyệt (**từ chối · trả lại · rút phiếu**) đều gọi
`service.reject()` → văn bản về **Nháp (1)**. Hệ quả:

- Mở văn bản ra thấy «Nháp» y như bản chưa từng gửi duyệt — không biết nó **vừa bị trả**.
- Lý do trả nằm trong `version.change_reason` (`[Trả lại] …`) và dấu vết tab *Phê duyệt*;
  băng `DocumentApprovalBanner` **trả `null`** khi phiên không còn chạy nên **không hiện gì**.
- «Từ chối» và «trả lại» không phân biệt được, dù một cái là *sửa đi gửi lại*, cái kia là *dẹp*.

## Quyết định (đã chốt với người dùng 24/08/2026)

| Câu hỏi | Chốt |
| --- | --- |
| Từ chối có trạng thái riêng? | **Có** — `9 = Trả về`, `10 = Đã từ chối` |
| Bản 2.0+ bị trả (văn bản vẫn Có hiệu lực)? | Thêm trạng thái cho **PHIÊN BẢN**: `5 = Trả về`, `6 = Đã từ chối` |
| Văn bản ở «Trả về» xóa được? | **Được**, y như Nháp (chưa cấp số thì không thủng sổ) |

Rút phiếu (người nộp tự rút) **vẫn về Nháp** — không phải bị trả.

## Luật sau khi sửa

- **Trả về**: phiên bản → `Trả về (5)`, vẫn **giữ `open_slot`** nên sửa được và
  **Gửi duyệt** lại được. Bản đầu → văn bản `Trả về (9)`; bản 2.0+ → văn bản giữ
  nguyên `Có hiệu lực`.
- **Đã từ chối**: phiên bản → `Đã từ chối (6)`, **nhả `open_slot`** (mở được bản mới);
  bản đầu → văn bản `Đã từ chối (10)` và **khóa sửa** (muốn làm lại thì *Sao chép*).
- Xóa: `Nháp` hoặc `Trả về`, và vẫn phải chưa cấp số.

## Tệp phải sửa

Backend
- `modules/document/model.py` — thêm 9/10 + nhãn + `EDITABLE_STATUSES`
- `modules/document/version_model.py` — thêm 5/6 + nhãn, `OPEN_STATUSES`, cột sinh `open_slot` (`IN (1,2,5)`)
- `migrations/versions/*` — sửa biểu thức cột sinh (drop unique → modify → add lại)
- `modules/document/service.py` — tách `reject()` thành `tra_lai · tu_choi · rut_phieu`;
  `submit()` nhận từ `Trả về`; `delete_document` nhận `Trả về`; `chan_sua_khi_dang_duyet` khóa cả `Đã từ chối`
- `modules/document/version_service.py` — `chan_khi_dang_duyet` khóa cả phiên bản `Đã từ chối`
- `modules/document/approval_bridge.py` — 3 hook trỏ đúng 3 hàm mới
- `modules/document/clone_lifecycle_service.py` — `Trả về → CLONE_DRAFTING`, `Đã từ chối → CLONE_REJECTED`
- `modules/document/dashboard_service.py` — thêm dòng việc *Bị trả về, chờ sửa*
- `modules/document/controller.py` — route một bước `/reject` = **trả về**

Frontend (`frontend-v2`)
- `modules/document/types/document-record.ts` — 4 mã mới + nhãn + `variant`
- `modules/document/pages/document-detail-page.tsx` — `isDraft`/`isRemovable` nhận `Trả về`
- `modules/document/components/document-approval-banner.tsx` — hiện băng **Bị trả về / Đã từ chối** kèm lý do
- `modules/document/components/document-version-row.tsx` — sửa câu chú thích «về Nháp»

Kiểm
- `test/backend/test_van_ban_tra_ve_trang_thai.py` (mới)
- `frontend-v2/.../document-approval-banner.test.tsx` (thêm ca)
- `doc/tai-lieu-ky-thuat/change-log.md` — ghi CR

## Todo

- [x] Backend: hai thang trạng thái + migration cột sinh (`c7a1e93b4d20`)
- [x] Backend: tách `tra_lai · tu_choi · rut_phieu` + các chốt sửa/xóa
- [x] Backend: clone lifecycle + dashboard + bridge
- [x] Frontend: mã trạng thái, gating chi tiết, băng lý do
- [x] Test backend (1361 xanh, 3 lỗi CÓ SẴN của B-06) + `npm run check` xanh (532 test)
- [x] Ghi change-log CR-143 + CR-144

## Rủi ro

- **Cột sinh `open_slot` có UNIQUE**: MySQL không đổi biểu thức khi còn index → phải
  drop `uq_one_open_version`, `MODIFY COLUMN`, rồi tạo lại. SQLite (test) dựng bảng
  từ model nên không cần nhánh riêng.
- Dữ liệu cũ **không cần backfill**: văn bản đã về Nháp trước đây cứ để là Nháp.

## Phát sinh trong lúc làm (đã vá)

1. **`open_new_version` đánh số từ bản ĐANG DÙNG** → bản 2.0 bị từ chối nằm lại thì
   nó tạo lại đúng số 2.0, đâm `uq_version_no`, mà lỗi báo sai thành *"một bản nháp
   khác vừa được mở"*. Nay đếm từ **số cao nhất đã từng dùng**; helper `soBanKeTiep`
   bên FE sửa khớp (nó vẽ câu "lên bản …" trong hộp thoại).
2. **Bấm Trả lại xong nhãn trạng thái không đổi tới khi F5** — hộp thoại duyệt chỉ
   nạp lại cụm `approval`. `useApprovalAction` nay nhận `entity` và nạp lại luôn họ
   query của chứng từ.
3. **Bản đã từ chối vẫn hiện nút *Lưu nội dung*** — `is_locked` chỉ bật lúc duyệt
   xong nên không suy ra được; nay khóa theo trạng thái bản đang xem.

## Việc KHÔNG thuộc phạm vi này nhưng phát hiện được

- **Alembic đang có HAI head** trên `erp-v2`: `62398fdb8563` (đã áp) và
  `b6e9c4801fa2` (nhánh B-06 chưa nhập) → `alembic upgrade head` **hỏng**, tức
  `start.sh` không migrate được. Migration của đợt này cắm vào head đã áp và chạy
  đích danh. Muốn sửa phải có một revision `merge` — việc của người mở nhánh B-06.
- Ba bài kiểm **đỏ sẵn** trên nhánh: `test_expected_date_sync.py::test_dong_huy_don_khong_tinh`
  và hai bài `test_luong_duyet_thu_mua.py` (`'approved' == 'Duyệt'` — đúng nhánh B-06).
