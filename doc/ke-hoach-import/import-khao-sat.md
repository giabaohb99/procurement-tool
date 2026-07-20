# MÔ TẢ CHỨC NĂNG: IMPORT KHẢO SÁT (Phiếu khảo sát) — BẢN CHỐT

Nguồn: sheet **3** (Đánh giá NCC) + sheet **4** (Đánh giá SP/lấy mẫu). Header dòng 5, data từ dòng 6.

## 1. Mục tiêu
Nạp khảo sát cũ vào **Phiếu khảo sát (Survey)**. Chạy nền (Celery), upsert theo khoá tái tạo,
báo chuông khi xong, có màn quản lý + log, và **revert (hoàn tác) một lần import**.

## 2. Tái tạo "Mã yêu cầu" (khoá liên kết)
Data cũ không có Mã yêu cầu → **tự sinh** cho mỗi dòng:
- `viết_tắt` = map(`BP/Người YC` cột D) theo bảng:
  `Nhà máy Dego→NM · SX - Ms Ly→SX · Lab→LAB · KD ABA→AB · KD ICARE→IC · KD DR XANH→DR · KD IDA→ID · SX - Ms Hương→SX · TM - Ms Quyên→TM · KD N2SBIO→N2 · QLTM_Ms Ngân→QLTM_MS NGÂN`. Không khớp → **`KC`**.
- `ngày` = Ngày tiếp nhận (cột B) → `ddmmyyyy`.
- `seq` = STT của (Phân loại + Chi tiết thông số) duy nhất trong ngày → **CHỈ hiển thị**.
- **Mã hiển thị** = `PYC.{viết_tắt}.{ddmmyyyy}.{seq}`.
- **KHOÁ THẬT (so khớp)** = chuẩn hoá `(viết_tắt + ngày + Phân_loại + Chi_tiết_thông_số)` (bỏ khoảng trắng thừa, không phân biệt hoa/thường).

> BP là một phần khoá: cùng ngày + cùng SP nhưng khác BP = 2 yêu cầu riêng.

## 3. Gom phiếu — 2 loại
Từ khảo sát SP (sheet 4), nhóm theo Mã yêu cầu:
- **Loại 1** — `Mã VTBB/NL/BTP (nội bộ)` (cột P) **CÓ** trong danh mục sản phẩm → gom thành phiếu theo **Mã VTBB** (`import_key = "VTBB::<mã>"`). Nhiều yêu cầu/NCC cùng Mã VTBB → **1 phiếu** (so sánh NCC).
- **Loại 2** — **không** có Mã VTBB (hoặc không khớp danh mục) → **phiếu riêng theo Mã yêu cầu** (`import_key = "REQ::<mã yêu cầu>"`).

NCC (theo tên viết tắt/MST) **chưa có trong danh mục → tự tạo NCC** (từ data sheet 3).

## 4. Dòng trong phiếu — khoá `(Mã yêu cầu + MST)`
- **Dòng SP** (SurveyProductLine) và **dòng NCC** (SurveySupplierLine): khoá idempotent = `(Mã yêu cầu + MST của NCC)`.
- Nhờ vậy: **cùng NCC + cùng SP nhưng khảo sát nhiều lần** (khác ngày/BP → khác Mã yêu cầu) → **giữ riêng từng dòng**, không gộp.
- **Phân phối dòng NCC** (sheet 3) vào phiếu: gen Mã yêu cầu như trên → tìm phiếu chứa dòng SP có `(MST + Mã yêu cầu)` khớp:
  - đúng 1 phiếu → bỏ vào;
  - nhiều phiếu → bỏ **phiếu đầu** + log cảnh báo;
  - không có → tạo **phiếu trống riêng** (chỉ có dòng NCC) + log.

## 5. Chuẩn hoá giá trị (đối chiếu danh mục)
- `Phân loại`, `ĐVT` → về đúng text danh mục (khớp không phân biệt hoa/thường); lạ → giữ text + log `value_unmatched`.
- `VAT` thập phân (0.08) → phần trăm (8). Cột Duyệt → bộ chuẩn (Đã duyệt/Không duyệt/Chờ duyệt/Thiếu thông tin).
- `supplier_code` → về đúng mã danh mục (để UI khớp tên pháp lý). Ngày/số rác → trống/0.

## 6. Chạy nền + chuông + log
Upload → `ImportBatch(running)` → Celery `run_import` → parse/gom/phân phối/upsert → ghi `import_log` → xong `done` + **chuông** cho người import. Dry-run: tính + log nhưng rollback (không ghi).

## 7. Revert (hoàn tác 1 lần import)  ← MỚI
- Mỗi lần **Apply**, ghi lại thay đổi ở mức PHIẾU vào `tab_import_change`: mỗi phiếu bị đụng → `was_new` (phiếu mới do batch tạo) + `snapshot` (JSON phiếu + dòng NCC + dòng SP TRƯỚC khi sửa, rỗng nếu was_new).
- Nút **"Hoàn tác"** ở trang chi tiết Import (chỉ batch Apply chưa revert):
  - phiếu `was_new` → **xoá** phiếu (+ dòng);
  - phiếu cũ → **khôi phục** từ snapshot (xoá dòng hiện tại, dựng lại theo snapshot);
  - xong → batch `status = reverted`.
- Ràng buộc: nên revert theo thứ tự **mới→cũ**; nếu phiếu đã bị batch sau sửa tiếp thì cảnh báo (revert best-effort). Quyền: vai trò có `survey delete`/admin (hoặc DEV_MODE).

## 8. Update (re-import)
Tìm lại phiếu theo `(Mã VTBB | Mã yêu cầu)`, dòng theo `(Mã yêu cầu + MST)` → cập nhật đúng, không nhân đôi.
