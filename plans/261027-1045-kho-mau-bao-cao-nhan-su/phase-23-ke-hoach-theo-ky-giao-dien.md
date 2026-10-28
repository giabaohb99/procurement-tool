# Phase 23 — Kế hoạch nhân sự theo kỳ: giao diện (duoc-CR-690)

Thiết kế: `doc/erp/hrm/06-ke-hoach-nhan-su.md` (§2 bố cục form, §3 loại kỳ, §4 khoản chi phí). Hợp đồng API: `phase-22-ke-hoach-theo-ky-backend.md`.
Ưu tiên P1 · Chủ: FE-d · Trạng thái: pending · Chạy song song phase 22 (dựng theo hợp đồng API, nối thật khi backend xong).

## Màn
1. **Nhóm chi phí** `/hr/hr-cost-groups` — CRUD khai báo (`shared/crud`), menu Nhân sự ▸ Danh mục.
2. **Mẫu khoản chi phí** `/hr/hr-cost-templates` (+ `/new`, `/:id`) — trang riêng; bảng khoản sửa tại chỗ: Mã, Tên, Nhóm, Cách tính, các ô phụ
   thuộc cách tính (% / hệ số / trần / số tiền / khoản gốc nhiều lựa chọn / tháng rơi vào nhiều lựa chọn), Áp cho (+ chọn vị trí), Lấy thực tế từ,
   kéo thứ tự. Nút «Nhân bản mẫu».
3. **Kế hoạch nhân sự** `/hr/headcount-plans` — danh sách lọc Năm · Loại kỳ · Pháp nhân · Phòng; cột: Kỳ (vd «Q3-2026»), Pháp nhân, Phòng,
   Định biên cuối kỳ, Tổng chi phí (— khi bị che), Căn cứ. Thêm / mở = **trang riêng** `/hr/headcount-plans/new`, `/:id` (form dài, KHÔNG hộp thoại).
4. **Trang kế hoạch** — bốn khối theo §2 của tài liệu:
   - Kỳ & Căn cứ: Loại kỳ (Năm/Bán niên/Quý/Tháng) → ô Kỳ đổi theo; Pháp nhân; Phòng (mọi phòng + «Toàn pháp nhân»); Mẫu (chỉ khi tạo);
     Số căn cứ, Ngày, Người duyệt (chọn nhân sự), **Văn bản liên kết** (tìm và chọn văn bản ở phân hệ Văn bản — dùng lại ô chọn/tra văn bản
     sẵn có ở `modules/document`; hiện số/ký hiệu, trích yếu, trạng thái, nút mở; mục `can_read:false` hiện «Văn bản bạn chưa được xem»),
     Tệp đính kèm (khuôn attachment sẵn có), Lý do.
   - Khoản chi phí của kế hoạch: cùng bảng sửa như màn Mẫu (component dùng chung trong `modules/hr/components/`).
   - Định biên theo vị trí: số cột định biên = số kỳ con theo loại kỳ; «Đang có» + gợi ý bình quân lấy `/position-stats`; cột «Cần tuyển» tự tính;
     **mọc một cột cho mỗi khoản PER_HEAD_MONTH**; thêm vị trí (danh mục Chức vụ), dòng «Không theo vị trí».
   - Hệ thống tự tính: gọi `POST /api/headcount-plans/compute` (debounce ~400ms) khi form đổi; bảng nhóm (mở ra từng khoản) × kỳ con + Tổng kỳ,
     dòng Định biên cuối kỳ con, Bình quân / người. Lỗi kiểm hợp lệ hiện tại khối khoản.
   - Thiếu quyền xem tiền: ẩn mọi ô/cột tiền, hiện ghi chú vì sao (khuôn `SensitiveFieldsNotice`); vẫn sửa được định biên. Thiếu quyền ghi: chỉ xem.
5. Bỏ màn CRUD đợt 4 (`headcount-plan-crud.tsx`, hộp thoại) và bộ nhập CSV kiểu cũ; thay bằng: xuất danh sách CSV, xuất một kế hoạch xlsx,
   nhập CSV dòng vị trí ở trang kế hoạch.

## Luật bắt buộc
- Đọc `frontend-v2/.claude/rules/*.md`, `.claude/rules/frontend-v2-ui-conventions.md` (LinesTable, bốn bẫy biểu mẫu), `docs/ui/table.md`.
- Mã số loại kỳ / cách tính / áp cho / nguồn thực tế lấy từ tệp do `backend/scripts/gen_status_ts.py` sinh (chạy trên host sau khi backend khai);
  KHÔNG gõ tay danh sách trong TS.
- Gọi API bằng `apiGet/apiPost/...`; TanStack Query; key ở `shared/constants/query-keys.ts`; route ở `app-routes.ts`; khóa quyền `headcount_plan`.
- Tiền định dạng bằng helper sẵn có; ô nhập số tiền dùng ô tiền sẵn có.

## Cổng kiểm
`cd frontend-v2 && npm run typecheck` (trên host — trong container bị OOM) · `npx eslint src/modules/hr` · `docker compose exec -T erp npx vitest run src/modules/hr`.
Bài kiểm cạnh tệp: cột động theo khoản, số cột theo loại kỳ, che tiền, văn bản không xem được, payload gửi đi.
