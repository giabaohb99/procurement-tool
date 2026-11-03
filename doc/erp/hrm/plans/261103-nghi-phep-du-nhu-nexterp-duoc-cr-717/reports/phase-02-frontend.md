# Phase 02 FE — Chính sách nghỉ phép + Phân bổ chính sách (duoc-CR-717)

Status: DONE. Chưa commit / push. Bám hợp đồng as-built ở `phase-01-backend.md` (gồm sửa của lead: phạm vi nhân sự = phạm vi XEM `employee`).

## Màn đã làm
- **Chính sách nghỉ phép** `/hr/leave-policies` (+ `/new`, `/:id`) — khung CRUD `detailLayout: 'flat'`, thẻ thứ 4 của Nghỉ phép › Thiết lập (`can('leave_type','write')`). Cột Mã · Tên · Trạng thái · Ghi chú. Chi tiết 3 tab: Thông tin · Loại nghỉ & số ngày (chỉ loại đang dùng + trừ quỹ + không phải nghỉ bù; trùng loại ghi đè; bước 0,5; nút **Lưu số ngày** = PUT cả danh sách; câu giải thích theo spec) · Đang phân bổ (bảng chỉ đọc, gác `leave_balance.read`, bấm dòng sang danh sách phân bổ lọc `policy_id` + mã NV).
- **Phân bổ chính sách** `/hr/leave-policy-assignments` — mục con mới sau **Quỹ phép năm** (`entity: leave_balance`). DataTable: Nhân sự · Chính sách · Từ · Đến (**Không thời hạn**) · Trạng thái (đọc `state`) · Ghi chú · Thao tác. Lọc: tìm tên/mã (`search`), chính sách, **Đang hiệu lực hôm nay** (`active_on`), pháp nhân. Nút Phân bổ / Phân bổ hàng loạt / Kết thúc / Xóa gác `leave_balance.write`. Khổ < 768px dùng thẻ (có nút).
- **Hộp phân bổ một người**: chọn NV (cần `employee.read`, không có thì báo và không gọi danh bạ), chính sách đang dùng, Từ ngày (+ **Từ ngày vào làm**), Đến ngày (trống = không thời hạn), ghi chú, **Tính lại…** mặc định BẬT. Tự xem trước (`/preview`, `staleTime 0`) trước → sau; `overlap` hiện ô **Kết thúc chính sách đang hiệu lực** (giữ hiện sau khi tick); `self`/`inactive` khóa Lưu. Chặn bấm đúp `useSingleFlight`.
- **Hộp Kết thúc** (PATCH `effective_to`, recalc mặc định bật) và **hộp Xóa** (ô recalc mặc định bật, D3a — khác mặc định `false` của backend, FE luôn gửi tường minh).
- **Phân bổ hàng loạt** `/hr/leave-policy-assignments/bulk` (mục ẩn gác `leave_balance` + `write`): khối 1 chính sách/ngày/2 ô tick, khối 2 lọc pháp nhân · phòng · hình thức · cấp bậc · **Chỉ người chưa có chính sách** (mặc định bật), **Xem danh sách** → bảng có ô chọn (dòng vướng bị khóa + lý do), cảnh báo `truncated`, đổi ô ảnh hưởng xem trước (trừ recalc) → khóa nút tới khi xem lại, **Phân bổ N người** → khung kết quả (đã phân bổ / bỏ qua + lý do + số dòng quỹ tính lại).
- **Chi tiết dòng quỹ**: dòng **Chính sách đang áp: P (từ → đến)** (link tới chính sách nếu có `leave_type.read`) + **khai X ngày/năm cho loại này** hoặc **không khai loại này nên theo hạn mức của loại nghỉ**; không có phân bổ → **theo hạn mức của loại nghỉ**.

## Tệp
Mới (`frontend-v2/src/modules/hr/`): `types/leave-policy.ts`(+test) · `api/leave-policy-api.ts` · `hooks/use-leave-policy.ts` · `config/leave-policy-crud.tsx` · `config/leave-policy-assignment-columns.tsx` · `components/leave-policy-{lines-card(+test), assignments-tab, assign-dialog(+test), assign-preview, assignment-end-dialog, assignment-delete-dialog, assignment-state-badge, assignment-mobile-card, balance-changes, bulk-settings-form, bulk-preview-table, bulk-result}.tsx` · `components/leave-balance-policy-note.tsx`(+test) · `pages/leave-policy-{list,detail,assignment-list(+test),bulk-assign(+test)}-page.tsx` · `utils/leave-policy-display.ts`(+test) · `utils/leave-policy-bulk.ts`(+test).
Sửa: `hr/routes.tsx` (mục **Phân bổ chính sách**, 2 mục ẩn, 5 route, matchPaths) · `hr/components/leave-section-tabs.tsx`(+test) · `hr/pages/leave-balance-detail-page.tsx` (1 dòng gắn ghi chú) · `shared/constants/app-routes.ts` (5 đường) · `shared/constants/query-keys.ts` (3 khóa `hr.leavePolicy*`, thêm thuần).
Ngoài danh sách sở hữu, bắt buộc để cổng xanh: `src/app/router/module-visibility.test.ts` — 2 kỳ vọng menu thêm **Phân bổ chính sách** + 2 bài mới canh gác route (`/hr/leave-policies*` cần `leave_type` quản lý; `/bulk` cần `leave_balance.write`, chỉ đọc bị chặn).
Không đụng: `leave-api.ts`, `use-leave.ts`, `types/leave.ts`, `leave-balance-page.tsx`, hộp Cấp quỹ, `modules/report/*`.

## Cổng
- `npm run typecheck` (host): 0 lỗi.
- `npx eslint` trên mọi tệp đã đụng: 0 lỗi, 0 cảnh báo.
- `vitest run src/modules/hr src/app/router` (container): 146 tệp / 1636 bài xanh (mới: 7 tệp, ~40 bài).
- Trình duyệt localhost:8083 (admin): tạo **TEST CR-717 Cấp quản lý** (Phép năm 15) → sửa ghi chú (PATCH ok) → phân bổ Triệu Nam Lộc từ 03/11/2026: xem trước 12 → 12,5, lưu, chi tiết quỹ hiện **Chính sách đang áp … khai 15 ngày/năm**, hạn mức 12.5, nhật ký có dòng **12 → 12.5** → hàng loạt phòng **Sản xuất -Thu mua** bỏ **Chỉ người chưa có…**: 26 người, dòng Triệu Nam Lộc khóa + lý do chồng ngày, chọn 2 → **Đã phân bổ 2 · Bỏ qua 0** → Kết thúc 1 phân bổ (toast **tính lại 1 dòng quỹ**). Khổ 390px bằng emulate: danh sách ra thẻ có nút, trang hàng loạt xếp dọc. **Đã dọn**: xóa 3 phân bổ kèm tính lại (quỹ 3 người về 12), xóa chính sách. Còn lại dòng nhật ký audit (bình thường).

## Ghi chú / hở
- **Phân bổ hàng loạt 3 người, 1 chồng ngày → kết quả 2/1** trong **Xong khi**: trên giao diện dòng chồng ngày bị khóa ô chọn nên không gửi lên → kết quả thực tế 2/0. Nhánh **bỏ qua** chỉ xảy ra khi dữ liệu đổi giữa lúc xem và lúc bấm; đã có bài kiểm khung kết quả liệt kê người bỏ qua.
- `FilterSelect` trong `leave-policy-bulk-settings-form.tsx` trùng khuôn với hộp Cấp quỹ (của phase 04) — để sau gộp ra `hr/components` khi phase 04 xong (tránh đụng tệp của người khác).
- Bảng xem trước hàng loạt không dùng `createSelectionColumn` vì nó không có nhánh khóa từng dòng; nếu muốn dùng chung thì thêm prop `isRowSelectable` ở `shared/data-table/selection-column.tsx` (thêm thuần).
- Trạng thái lọc chỉ có **Đang hiệu lực hôm nay** (backend chỉ có `active_on`, không lọc theo `state`).
- Docs / HDSD / change-log / sổ nhật ký: chưa động (ngoài phạm vi).

Unresolved: không.
