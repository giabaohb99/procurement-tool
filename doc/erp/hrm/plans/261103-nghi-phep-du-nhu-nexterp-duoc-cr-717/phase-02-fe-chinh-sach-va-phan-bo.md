# Phase 02 — FE: màn Chính sách nghỉ phép + Phân bổ chính sách

## Context
- API: phase 01 (bảng API). Mẫu FE: `hr/config/leave-type-crud.tsx` (`detailLayout: 'flat'`, `tabs`),
  `hr/components/leave-type-quota-card.tsx` (bảng sửa-cả-danh-sách), `hr/config/leave-block-crud.tsx` + 2 trang mỏng,
  `hr/components/leave-section-tabs.tsx`, `hr/routes.tsx` (nhóm **Nghỉ phép**), `shared/ui/employee-multi-select.tsx`,
  `hr/hooks/use-employees`. Luật: `frontend-v2/.claude/rules/*`, `.claude/rules/frontend-v2-ui-conventions.md`, `docs/ui/table.md`.
- Memory: gác điều hướng mặc định MỞ → route mới phải có mục menu (ẩn nếu cần) mang `entity`.

## Tổng quan
Ưu tiên P2. Theo D7(a): thẻ **Chính sách nghỉ phép** trong Thiết lập (CRUD khai báo) + mục con **Phân bổ chính sách** trong
menu Nghỉ phép (danh sách viết tay + hộp phân bổ một người + trang phân bổ hàng loạt kiểu Leave Control Panel).

## Giao diện
1. **Chính sách** `/hr/leave-policies` (+ `/new`, `/:id`) — CrudConfig `entity: 'leave_type'`, `apiPath:
   '/api/leave-policies'`, `detailLayout: 'flat'`, `createRoute` trang riêng. Cột: Mã · Tên · Trạng thái · Ghi chú. Tab chi
   tiết (chỉ khi đã tạo): *Thông tin* · *Loại nghỉ & số ngày* (`LeavePolicyLinesCard`: ô Loại nghỉ (chỉ loại trừ quỹ,
   không phải nghỉ bù) · Số ngày mỗi năm (bước 0,5), Thêm dòng, Lưu = PUT cả danh sách) · *Đang phân bổ* (bảng chỉ đọc
   `GET /api/leave-policy-assignments?policy_id=`, gác `can('leave_balance','read')`, bấm dòng sang danh sách phân bổ đã lọc).
   Câu giải thích trên tab dòng: **Sửa số ngày chỉ áp cho lần cấp quỹ sau hoặc khi phân bổ có tick Tính lại; quỹ đã cấp giữ
   nguyên. Loại nghỉ không có ở đây vẫn cấp theo hạn mức của loại nghỉ.**
2. **Phân bổ chính sách** `/hr/leave-policy-assignments` — `DataTable`: Nhân sự (mã + tên) · Chính sách · Từ ngày · Đến
   ngày (**Không thời hạn**) · Trạng thái (Sắp tới / Đang hiệu lực / Đã kết thúc — đọc `state` backend, không tự so ngày ở TS)
   · Ghi chú. Bộ lọc: chính sách, trạng thái hiệu lực hôm nay, pháp nhân, tìm tên/mã. Nút (gác `can('leave_balance','write')`):
   *Phân bổ* (hộp) · *Phân bổ hàng loạt* (trang). Dòng: *Kết thúc* (sửa `effective_to`) · *Xóa* (hộp xác nhận có ô
   **Tính lại hạn mức năm nay**).
3. **Hộp Phân bổ một người** `LeavePolicyAssignDialog`: Nhân sự (ô chọn một) · Chính sách (chỉ đang dùng) · Từ ngày (nút
   nhỏ **Từ ngày vào làm**) · Đến ngày (trống = không thời hạn) · Ghi chú · ô **Tính lại hạn mức năm nay cho quỹ đã cấp**
   (mặc định theo D3) · ô **Kết thúc chính sách đang hiệu lực** (chỉ hiện khi preview báo `overlap`). Trước nút Lưu gọi
   `/preview` với `employee_ids=[id]` → bảng nhỏ **Loại nghỉ · Hiện tại → Sau phân bổ**. `conflict='self'` → khóa nút, câu
   **Không tự phân bổ chính sách cho chính mình**.
4. **Trang Phân bổ hàng loạt** `/hr/leave-policy-assignments/bulk` (Leave Control Panel): khối 1 — chính sách, từ/đến,
   hai ô tick như hộp; khối 2 — lọc pháp nhân · phòng ban · hình thức NV · cấp bậc · **Chỉ người chưa có chính sách hiệu
   lực** (mặc định bật) → nút *Xem danh sách* gọi `/preview`; khối 3 — `DataTable` có ô chọn: Mã · Tên · Phòng · Ngày vào
   làm · Chính sách hiện tại · Thay đổi quỹ năm nay (tóm tắt **Phép năm 12 → 15**) · Lý do không phân bổ được (dòng có
   `conflict` bị khóa ô chọn). `truncated` → câu **Chỉ hiện 500 người đầu, thu hẹp bộ lọc**. Nút *Phân bổ N người* → `/bulk`
   → khung kết quả: **Đã phân bổ X · Bỏ qua Y** + danh sách bỏ qua kèm lý do + số dòng quỹ tạo / tính lại.
   Chặn bấm đúp: `useSingleFlight` (đã có từ CR-715).
5. **Chi tiết dòng quỹ** `leave-balance-detail-page.tsx`: thêm dòng nhỏ **Chính sách đang áp: P (từ … đến …)** hoặc **Theo
   hạn mức của loại nghỉ** — `LeaveBalancePolicyNote` gọi `GET /api/leave-policy-assignments?employee_id=&active_on=`.
6. Menu (`routes.tsx`): **Nghỉ phép** thêm con **Phân bổ chính sách** (`entity: 'leave_balance'`) sau **Quỹ phép năm**;
   `matchPaths` của nhóm + của **Thiết lập** thêm đường chính sách; mục ẩn (`hidden: true`) cho `/hr/leave-policies`
   (`entity: 'leave_type'`) và cho trang bulk (`entity: 'leave_balance'`). `LeaveSectionTabs` thêm thẻ thứ 4 **Chính sách
   nghỉ phép** (`can('leave_type','write')`).

## Kiểu dữ liệu (`hr/types/leave-policy.ts`, gõ tay)
`LeavePolicy`, `LeavePolicyLine`, `LeavePolicyAssignment` (`state: 1|2|3` + nhãn ở `LEAVE_POLICY_ASSIGNMENT_STATE_LABELS`),
`PolicyPreviewItem`, `PolicyBalanceChanges`, `PolicyBulkResult`. Trạng thái khớp IntEnum backend — có bài kiểm số mục.

## Tệp
Tạo (`frontend-v2/src/modules/hr/`): `types/leave-policy.ts` · `api/leave-policy-api.ts` · `hooks/use-leave-policy.ts`
(TanStack Query; khóa query riêng, mutation phân bổ làm mới cả khóa quỹ phép) · `config/leave-policy-crud.tsx` ·
`components/leave-policy-lines-card.tsx` · `components/leave-policy-assignments-tab.tsx` ·
`components/leave-policy-assign-dialog.tsx` · `components/leave-policy-balance-changes.tsx` (bảng trước→sau dùng chung
hộp + trang) · `components/leave-balance-policy-note.tsx` · `pages/leave-policy-list-page.tsx` ·
`pages/leave-policy-detail-page.tsx` · `pages/leave-policy-assignment-list-page.tsx` ·
`pages/leave-policy-bulk-assign-page.tsx` + `*.test.tsx` cạnh từng tệp có logic.
Sửa: `hr/routes.tsx` · `hr/components/leave-section-tabs.tsx` (+ test) · `hr/pages/leave-balance-detail-page.tsx` ·
`shared/constants/app-routes.ts` (`hr.leavePolicies`, `leavePolicyNew`, `leavePolicyDetail(id)`,
`leavePolicyAssignments`, `leavePolicyBulkAssign`).
KHÔNG đụng: `hr/pages/leave-balance-page.tsx`, `hr/api/leave-api.ts`, `modules/report/*` (thuộc phase 04).

## Các bước
1. Kiểu + API + hook (+ test hook bằng mock `httpClient`). 2. CRUD chính sách + thẻ dòng + tab đang phân bổ.
3. Danh sách phân bổ. 4. Hộp một người (preview → lưu). 5. Trang hàng loạt. 6. Ghi chú trên chi tiết quỹ. 7. Menu + thẻ.
8. Cổng: `npm run typecheck` (host) · `npx eslint src/modules/hr` · `npx vitest run src/modules/hr`.

## Bài kiểm (vitest)
- `leave-section-tabs.test.tsx`: thẻ **Chính sách nghỉ phép** hiện khi `leave_type.write`, ẩn khi thiếu.
- `leave-policy-lines-card`: thêm dòng trùng loại → ghi đè; chỉ liệt kê loại trừ quỹ không phải nghỉ bù; Lưu gửi cả danh sách.
- `leave-policy-assign-dialog`: preview hiện trước→sau; `conflict='overlap'` hiện ô **Kết thúc…**; `self` khóa Lưu; mặc định
  ô tính lại đúng D3.
- `leave-policy-bulk-assign-page`: dòng có `conflict` không chọn được; nút đếm đúng số người chọn; khung kết quả liệt kê bỏ qua.
- Danh sách: trạng thái đọc nhãn từ `state`; người không có `leave_balance.write` không thấy nút.

## Xong khi
- Typecheck 0 lỗi, eslint 0 lỗi (không thêm cảnh báo), vitest `src/modules/hr` xanh.
- Trên `localhost:8083`: tạo chính sách → phân bổ 1 người → mở chi tiết quỹ thấy **Chính sách đang áp** và số mới; phân bổ
  hàng loạt 3 người (1 chồng ngày) → kết quả 2/1. Kiểm khổ 390px bằng emulate (không resize — memory).

## Rủi ro
| Rủi ro | K×T | Giảm |
|---|---|---|
| Route mới không có mục menu → ai cũng vào | TB × TB | mục ẩn mang `entity` cho từng đường |
| Preview lệch số lúc lưu (dữ liệu đổi giữa chừng) | Thấp × Thấp | kết quả lưu trả số thật, khung kết quả hiện số đó |
| `defaultHidden`/layout cũ trong localStorage | Thấp × Thấp | `storageKey` mới, không dùng lại khóa cũ |
