# Phase 04 + 05 — FE Nghỉ phép + Tài chính (duoc-CR-719)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | giao-dien-v2 | Hiệu lực | duoc-CR-719 |

Trạng thái: xong, chưa commit. Làm tiếp phần dở của lượt trước (không làm lại từ đầu). Không đụng backend, migration, `.claude/rules`.

## Tệp (frontend-v2/src)
Tạo — `modules/hr/`: `api/leave-encashment-api.ts` · `hooks/use-leave-encashment.ts` · `types/leave-encashment.ts` (+ `.test.ts`) ·
`utils/leave-encashment-form-values.ts` · `pages/leave-encashment-{list,detail}-page.tsx` · `components/leave-encashment-{columns,
decision-actions,form,form.test,payment-card,payment-card.test,preview-box,summary,target-fields}.tsx` ·
`components/leave-engine-decision-actions.tsx` (khung ba nút duyệt theo phiên, dùng chung với nghỉ bù) · `config/leave-type-encashment-fields.ts`.
`modules/finance/components/`: `payment-request-leave-encashment-{view,view.test,info-card}.tsx`.

Sửa: `shared/constants/{app-routes,query-keys}.ts` · `core/authorization/permission-types.ts` · `modules/hr/{routes.tsx,
config/leave-type-crud.tsx,types/leave.ts,components/leave-balance-{columns,breakdown-card,card}(+test).tsx,utils/group-leave-balances(+test).ts,
components/leave-comp-approval-timeline.tsx (Pick dùng chung),components/leave-comp-decision-actions.tsx (chuyển sang khung chung)}` ·
`modules/approval/{helpers/entity-link.ts,hooks/use-approvals.ts}` · `modules/system/config/permission-groups.ts` ·
`app/router/module-visibility.test.ts` · `modules/finance/{types/payment-request.ts,hooks/use-payment-requests.ts,
pages/payment-request-detail-page.tsx (rẽ sớm ở cấp component),pages/payment-request-print-page.tsx}`.

## Lượt này làm thêm / sửa
1. Công tắc **Cho phép thanh toán nghỉ phép** ở Loại nghỉ: bỏ `showWhen`. Khung CRUD vẫn gửi giá trị ô bị ẩn, nên ẩn công tắc khi tắt
   **Trừ vào quỹ phép năm** thì `true` cũ vẫn lên và ăn 422 mà người dùng hết chỗ gạt về tắt. Hai ô số vẫn ẩn theo công tắc.
2. Form phiếu 329 dòng → tách `leave-encashment-target-fields.tsx` (người · loại · năm), form còn 226 dòng.
3. Bài kiểm mới `leave-encashment-payment-card.test.tsx` (5 ca): không vẽ số tiền khi API trả `total: null`; 0 → *Kế toán chưa nhập*;
   link YCTT chỉ khi có `payment_request.read`; câu chặn hủy; khối rỗng.
4. Lặt vặt: ghép class bằng `cn` thay ba ngôi (bản chỉ xem, ô tiền YCTT); nút Từ chối YCTT có `disabled` khi đang gửi; câu hướng dẫn
   trên YCTT nghỉ phép nói đúng luật (Nháp → nhờ Nhân sự hủy phiếu; đã gửi duyệt → Từ chối — backend chỉ cho từ chối từ Chờ duyệt).

## Cổng kiểm
- `npm run typecheck` (host): 0 lỗi.
- `npx eslint` các khu đã đụng: 0 lỗi, 3 cảnh báo đều có sẵn (`print-page` `any` dòng 108, `unified-room-booking-table`, …).
- vitest trong container, từng thư mục: `src/modules/hr` 146 tệp / 1580 bài xanh · `src/modules/finance` 8 / 81 xanh ·
  `src/app/router` 3 / 106 xanh · `src/modules/approval src/modules/system` 54 / 450 xanh (+1 expected fail có sẵn).
- Không có ngoặc góc trong mã thêm mới.

## Soát trên trình duyệt (localhost:8083, admin local, 1440 và 390 bằng emulate)
- Trước khi có quyền: `/hr/leave-encashments` ra 403 — hàng rào route theo mục menu chạy đúng.
- Lập hộ Trần Viết Vỹ (NSU002), Phép năm 2026: hộp xem trước ghi *còn 11 · giữ lại 2 · tối đa 9*; nhập 1,5 → Gửi duyệt → duyệt thẳng
  (chưa khai luồng) → khối Thanh toán hiện YCTT00196 Nháp, *Kế toán chưa nhập*; quỹ: đã thanh toán 1,5, còn 9,5.
- YCTT00196: nhãn nguồn **Thanh toán nghỉ phép**, Gửi duyệt khóa ở 0, không Xóa / Cập nhật theo công nợ; nhập 1.500.000 → Lưu → in:
  người nhận *Trần Viết Vỹ (NSU002)*, nội dung *Thanh toán tiền nghỉ phép năm 2026 — 1,5 ngày*. Nhân sự này chưa khai STK nên in chấm;
  giả `bank_hidden: true` ngay trên trang (không đụng dữ liệu) → in *kế toán tự điền* ở Số TK và Ngân hàng.
- Gửi duyệt YCTT → phiếu nghỉ phép ẩn nút Hủy kèm câu *YCTT … đang ở Chờ duyệt — kế toán từ chối YCTT trước*. Từ chối YCTT → băng vàng
  **Kế toán từ chối chi** (D7a) + nút Hủy mở lại → Hủy → phiếu Đã hủy, quỹ về 11, đã thanh toán 0. Danh sách YCTT lọc nguồn mới ra đúng dòng.
- Không có lỗi console.

## Dữ liệu local để lại (đều ghi TEST CR-719)
- TTP001 (Đã hủy) và YCTT00196 (Đã từ chối) — không xóa được bằng giao diện (đúng luật), chỉ là bản ghi thử ở local.
- Loại nghỉ Phép năm: bật **Cho phép thanh toán nghỉ phép**, giữ lại 2 ngày (cấu hình local, để kiểm tiếp).
- Vai trò admin local được bổ sung quyền `leave_encashment` bằng cách gọi một lần `seed.ensure_admin_role` (việc api tự làm mỗi lần khởi động).

## Câu hỏi mở
1. Người chỉ có `leave_encashment.create` (không `write`) vẫn thấy nút **Gửi duyệt** trên form lập mới; bấm sẽ lưu nháp rồi ăn 403 ở bước gửi.
   Giữ như khuôn nghỉ bù hay ẩn nút theo `write`?
2. Link YCTT bên phiếu nghỉ phép chỉ dựa vào `can('payment_request','read')`; người có quyền đó nhưng ngoài phạm vi D1a vẫn thấy link (mở ra 404).
   Muốn chặt hơn cần backend gửi cờ `can_open` trong khối `payment`.
3. Trên YCTT nghỉ phép, kế toán không tự bỏ được phiếu còn Nháp (không Xóa, không Từ chối từ Nháp) — phải nhờ Nhân sự hủy. Đúng ý D7?

**Status:** DONE
**Summary:** Phiếu thanh toán nghỉ phép (danh sách, lập, chi tiết, duyệt, hủy theo YCTT, băng D7) và YCTT nghỉ phép bên Tài chính (nhập một
số tiền, chặn gửi ở 0, bản in người nhận / kế toán tự điền) chạy đủ vòng trên local; typecheck 0, lint 0 lỗi, vitest bốn khu xanh.

## Đổi giao diện sang bố cục phẳng (03/11/2026, theo phản hồi của chủ dự án)
- Trang lập và trang chi tiết phiếu thanh toán nghỉ phép bỏ thẻ trắng trên nền xám, chuyển sang mặt phẳng trắng như trang
  Loại nghỉ / Chính sách nghỉ phép: hàng tiêu đề dính (mũi tên lùi, mã phiếu, nhãn trạng thái + lý do, nút bên phải),
  các nhóm Thông tin · Số ngày · Thanh toán · Luồng duyệt · Hoạt động ngăn bằng đường kẻ, gập được.
- Lưu nháp / Gửi duyệt / Duyệt / Từ chối / Hủy lên góc phải hàng tiêu đề; ở điện thoại nút chính trải hết một hàng.
- Dòng chú thích xám dưới từng ô thu vào biểu tượng (i); câu Phiếu chỉ ghi số ngày nằm trong (i) của ô Số ngày thanh toán.
- Ô nhập nền xám không viền; ô chỉ xem là hộp xám nhạt. Người được thanh toán nằm chung lưới 2 cột với Loại nghỉ / Năm quỹ
  phép / Lý do; Số ngày thanh toán nửa bề ngang; Ghi chú trải hết.
- Hộp xanh Số ngày được thanh toán thành một dải nền xám nhạt, mỗi dòng nhãn : số.
- Băng Kế toán từ chối chi thành dải cảnh báo mảnh ngay dưới hàng tiêu đề. Thêm nhóm Hoạt động (nhật ký phiếu).
- Ảnh: `ui-flat-form.png` (khổ 1440). Hành vi giữ nguyên: kiểm hợp lệ, chặn bấm đúp, quyền, làm mới dữ liệu, che số tiền.
