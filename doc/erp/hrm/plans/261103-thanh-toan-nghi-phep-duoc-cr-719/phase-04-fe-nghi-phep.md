# Phase 04 — FE Nghỉ phép: phiếu thanh toán, loại nghỉ, quỹ

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | giao-dien-v2 | Nháp | duoc-CR-719 |

## Context
- API ở [phase-03](phase-03-be-phieu-thanh-toan-nghi-phep.md). Khuôn chép nguyên bộ phiếu nghỉ bù: `pages/leave-comp-request-
  {list,detail}-page.tsx`, `components/leave-comp-{request-form,request-summary,decision-actions,approval-timeline}.tsx`,
  `api/leave-comp-api.ts`, `hooks/use-leave-comp.ts`, `types/leave-comp.ts`, `hooks/use-single-flight.ts`.
- Luật: `frontend-v2/.claude/rules/*.md`, `.claude/rules/frontend-v2-ui-conventions.md`, `frontend-v2/docs/ui/table.md`.
  Memory: gác điều hướng mặc định MỞ (mục menu có `entity` là hàng rào của route).

## Việc
1. **Hằng dùng chung (làm TRƯỚC, commit riêng — phase 05 cần)**: `shared/constants/app-routes.ts` `hr.leaveEncashments`,
   `leaveEncashmentNew`, `leaveEncashmentDetail(id)`; `shared/constants/query-keys.ts` `hr.leaveEncashments(params)`,
   `hr.leaveEncashment(id)`, `hr.leaveEncashmentPreview(params)`; `core/authorization/permission-types.ts` thêm `'leave_encashment'`.
2. **Kiểu + mã** `types/leave-encashment.ts`: trạng thái 1–6, lý do 1–2 (gõ tay như `leave-comp.ts` — bộ mã số của nghỉ phép
   không qua `gen_status_ts.py`), kiểu phiếu, kiểu `payment` (`status` chuỗi YCTT + nhãn backend gửi, `total?`). Test `.test.ts`.
3. **API + hook**: `api/leave-encashment-api.ts`, `hooks/use-leave-encashment.ts` (danh sách, chi tiết, preview, 7 thao tác;
   thao tác xong nạp lại `queryKeys.hr.all`).
4. **Màn**: `pages/leave-encashment-list-page.tsx` (DataTable: mã, người, loại, năm, lý do, số ngày, trạng thái, trạng thái chi;
   ba tab như nghỉ bù: Cần tôi duyệt / Phiếu của tôi / Tất cả theo phạm vi), `pages/leave-encashment-detail-page.tsx` (mới + xem +
   sửa). Form `components/leave-encashment-form.tsx`: người nhận (ẩn khi không lập hộ được), loại nghỉ (chỉ loại
   `allow_encashment`), năm quỹ (năm nay / năm trước), lý do, số ngày (bước 0,5) + hộp **Số được thanh toán** từ `/preview`
   (số dư · phần mang sang không tính · phải giữ lại · trần năm còn · được thanh toán — mỗi dòng một câu, không bắt người dùng tự
   trừ). Khối **Thanh toán** ở chi tiết: mã YCTT (link sang Tài chính chỉ khi `can('payment_request','read')`), trạng thái chi,
   số tiền chỉ khi API trả `total`; YCTT Đã từ chối → băng vàng *Kế toán từ chối chi — hủy phiếu để trả lại ngày phép* (D7a).
   Chặn bấm đúp bằng `useSingleFlight`. Bốn bẫy biểu mẫu + ô chỉ xem theo `frontend-v2-ui-conventions.md`.
5. **Menu + route** `routes.tsx`: mục con **Thanh toán nghỉ phép** (icon `Banknote`, `entity: 'leave_encashment'`) sau **Nghỉ bù**,
   thêm vào `matchPaths` và `entities` của mục cha; ba route list / new / `:id`. `app/router/module-visibility.test.ts`: ca
   `/hr/leave-encashments*` — có `leave_encashment.read` vào được, chỉ `leave_request` thì không.
6. **Loại nghỉ** `config/leave-type-crud.tsx` (497 dòng — tách nhóm trường mới ra `config/leave-type-encashment-fields.tsx`):
   công tắc **Cho phép thanh toán nghỉ phép** (chỉ bật khi **Trừ vào quỹ phép** bật), **Tối đa mỗi năm (ngày)** (0 = không trần),
   **Số ngày phải giữ lại** — hiện khi công tắc bật; câu giải thích ngắn kèm ví dụ (dư 10, giữ lại 4 → được 6).
7. **Quỹ phép**: `types/leave.ts` `encashed_days?: number`; `components/leave-balance-columns.tsx` cột **Đã thanh toán ra tiền**
   (`defaultHidden`); `utils/group-leave-balances.ts` cộng khóa mới; `components/leave-balance-breakdown-card.tsx` ô cùng tên khi
   khác 0; `components/leave-balance-card.tsx` phần đuôi `N đã thanh toán`. Sửa test so chuỗi cùng commit.
8. **Phê duyệt + phân quyền**: `modules/approval/helpers/entity-link.ts` nhãn + link; `modules/approval/hooks/use-approvals.ts`
   `leave_encashment: queryKeys.hr.all`; `modules/system/config/permission-groups.ts` thêm khóa vào nhóm Nghỉ phép.

## Tệp sở hữu
Tạo: `frontend-v2/src/modules/hr/{types/leave-encashment.ts,types/leave-encashment.test.ts,api/leave-encashment-api.ts,
hooks/use-leave-encashment.ts,pages/leave-encashment-list-page.tsx,pages/leave-encashment-detail-page.tsx,
components/leave-encashment-form.tsx,components/leave-encashment-form.test.tsx,components/leave-encashment-preview-box.tsx,
components/leave-encashment-payment-card.tsx,config/leave-type-encashment-fields.tsx}`.
Sửa: `frontend-v2/src/shared/constants/{app-routes,query-keys}.ts`, `frontend-v2/src/core/authorization/permission-types.ts`,
`frontend-v2/src/modules/hr/{routes.tsx,config/leave-type-crud.tsx,types/leave.ts,components/leave-balance-columns.tsx,
components/leave-balance-columns.test.tsx,components/leave-balance-breakdown-card.tsx,components/leave-balance-card.tsx,
components/leave-balance-card.test.tsx,utils/group-leave-balances.ts,utils/group-leave-balances.test.ts}`,
`frontend-v2/src/modules/approval/{helpers/entity-link.ts,hooks/use-approvals.ts}`,
`frontend-v2/src/modules/system/config/permission-groups.ts`, `frontend-v2/src/app/router/module-visibility.test.ts`.

## Xong khi
`npm run typecheck` (host) 0 lỗi; `npx eslint src/modules/hr src/modules/approval src/modules/system src/app src/shared src/core`
0 lỗi; `npx vitest run src/modules/hr src/modules/approval src/app/router` xanh; soát tay `localhost:8083` khổ 390px bằng emulate
(memory): lập → gửi → duyệt → thấy mã YCTT; quỹ trừ đúng.

## Rủi ro
| Rủi ro | K × T | Giảm |
|---|---|---|
| Lộ số tiền cho người duyệt Nhân sự | Thấp × Cao | Chỉ vẽ khi API trả `total` — không tự tính, không gọi API YCTT |
| `defaultHidden` không áp cho người đã chỉnh menu Cột | Cao × Thấp | Đã biết (hr-leave.md); ghi trong HDSD |
