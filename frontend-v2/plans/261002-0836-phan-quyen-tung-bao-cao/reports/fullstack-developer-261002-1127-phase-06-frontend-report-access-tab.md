# Phase 06 — FE tab «Báo cáo» ở Phân quyền tài khoản

Plan: `plans/261002-0836-phan-quyen-tung-bao-cao/`. Phạm vi: phase 06 (chỉ `src/modules/system/**`
+ 1 khóa trong `query-keys.ts`). Không đụng `src/modules/report/**`, `src/app/router/**`,
`src/core/auth/**` (sở hữu của agent phase 05 chạy song song). Không commit.

## Việc đã làm
- `types/report-access.ts`, `api/report-access-api.ts`, `hooks/use-report-access.ts` — đúng hợp
  đồng phase-02 (`GET /api/report-access`, `POST .../grants`, `DELETE .../grants/{id}`). Hook gán
  báo `skipped` qua toast riêng (cùng tiền lệ `useGrantFolderAccessBulk`), cả gán/thu hồi đều
  invalidate `auth.me` phòng admin tự cấm/gán chính mình (`report_keys` nằm trong `/auth/me`).
- `components/report-access-tab.tsx` — `DataTable` 13 dòng tĩnh (không phân trang), cột Phân hệ ·
  Báo cáo · Được xem (chip) · Bị cấm (Badge destructive) · nút Sửa (ẩn hẳn, không chỉ khóa, khi
  thiếu `role.write`). 0 dòng cho phép → "Chưa ai xem được".
- `components/report-access-dialog.tsx` + `components/report-access-grant-list.tsx` (tách riêng
  theo gợi ý phase vì hộp phình) — khối 1 liệt kê + thu hồi (dùng `ConfirmIconButton` có sẵn, lý do
  rỗng — cùng tiền lệ `folder-share-people-list.tsx`/`document-share-access-list.tsx`, không bắt gõ
  lại câu mỗi lần thu hồi), khối 2 `AccessSubjectPicker` + Cho phép/Cấm + lý do (đếm ký tự, chặn ở
  cả `maxLength` lẫn `slice` trong state).
- Gắn `<TabsTrigger value="reports">` + `<TabsContent>` vào `role-permission-page.tsx`, gác
  `can('role','read')` cho cả tab trigger lẫn content (không chỉ ẩn trigger mà còn không dựng nội
  dung) — trang chỉ +10 dòng (244 → 254), không tách lại tab Vai trò theo đúng giới hạn phase.
- Thêm 1 khóa `queryKeys.system.reportAccess()`.

## Quyết định khác với mô tả gốc (và vì sao)
- Thu hồi dùng `ConfirmIconButton` với `reason: ''` — KHÔNG mở thêm ô nhập lý do riêng. Mô tả gốc
  đọc "nút thu hồi có ô lý do, dùng ConfirmIconButton" nhưng chính `ConfirmIconButton` không có ô
  nhập; hai nơi gần nhất trong codebase làm việc tương tự
  (`folder-share-people-list.tsx` → `REVOKE_REASON` hằng số, `document-share-access-list.tsx` →
  `confirm()` không hỏi lý do) đều KHÔNG bắt gõ lý do khi thu hồi — giữ nhất quán, tránh thêm UI
  không ai dùng (YAGNI). Test vẫn khẳng định đúng `{accessId, reason: ''}`.
- Không gửi `valid_from`/`valid_to` trong payload gán (dù hợp đồng cho phép) — thiết kế phase 06
  không yêu cầu ô hiệu lực từ–đến cho báo cáo, thêm vào là lố so với đặc tả (KISS).

## Tests
- `report-access-tab.test.tsx` (6 bài): 0 cho phép → "Chưa ai xem được"; tách cột cho phép/cấm;
  không `role.write` → ẩn nút Sửa; có `role.write` → bấm Sửa mở đúng báo cáo; API lỗi → trạng thái
  lỗi; danh sách rỗng thật → "Chưa có báo cáo nào.". Phải bọc `QueryClientProvider` vì `DataTable`
  tự gọi `useQueryClient` (nút Tải lại).
- `report-access-dialog.test.tsx` (7 bài): chọn 2 chủ thể + Cấm + lý do → gọi gán đúng
  `{subjects:[...2], effect:2, reason}`; nút Thêm vô hiệu khi chưa chọn ai; lý do 501 ký tự bị cắt
  về 500; thu hồi gọi đúng `{accessId, reason:''}`; dòng Cấm/Cho phép phân biệt theo CHỮ trong
  `within(list)` (khối 2 cũng có radio "Cho phép"/"Cấm" nên phải khoanh vùng khối 1 để tránh trùng
  chữ); report=null không dựng nội dung; chưa gán ai → câu rõ nghĩa.
- `role-permission-page.test.tsx`: thêm biến `canOverride` để tắt riêng `role.read` (mock cũ là hằng
  số `() => true`, không chỉnh được per-test) + mock `ReportAccessTab: () => null`; 2 bài mới: có
  `role.read` → hiện tab; không có → ẩn hẳn tab (không chỉ khóa).

## Cổng
- `typecheck`: 0 lỗi (cả cây).
- `lint`: 0 lỗi, 29 cảnh báo — toàn bộ nằm NGOÀI tệp vừa sửa (so khớp từng dòng với baseline phase
  04 báo lại), không thêm cảnh báo mới.
- `vitest run src/modules/system src/shared/access-subject`: 29 tệp / 298 passed + 1 expected fail
  (pre-existing `test.fails` trong `user-scope-dialog.test.tsx`, không liên quan phase này).

## File đã tạo/sửa
Tạo: `src/modules/system/{types/report-access.ts, api/report-access-api.ts,
hooks/use-report-access.ts, components/report-access-tab.tsx, components/report-access-dialog.tsx,
components/report-access-grant-list.tsx}` + 2 tệp test
(`components/report-access-{tab,dialog}.test.tsx`). Sửa: `pages/role-permission-page.tsx` (+10
dòng), `pages/role-permission-page.test.tsx` (+mock, +2 bài), `src/shared/constants/query-keys.ts`
(+1 khóa `system.reportAccess`).

Không đụng `src/modules/report/**`, `src/app/router/**`, `src/core/auth/**`,
`src/core/authorization/**` — xác nhận qua `git status` chỉ thấy các tệp trên trong phạm vi của
tôi; mọi thay đổi khác trong working tree là của agent phase 05 / phiên backend khác.

**Status:** DONE
**Summary:** Tab «Báo cáo» hoàn chỉnh — bảng 13 báo cáo nhóm theo phân hệ (nhãn/nhóm từ API, không
import `modules/report`), hộp gán/thu hồi 4 loại chủ thể, gác `role.read`/`role.write` đúng yêu
cầu. 3 cổng xanh, không chạm file ngoài phạm vi.
**Concerns:** Không có — không có câu hỏi treo.
