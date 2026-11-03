# Phase 04 FE — báo cáo "Làm việc vào ngày lễ, ngày nghỉ" + Theo nhân sự + hộp Cấp quỹ (duoc-CR-717)

Status: DONE. Không commit. Theo hợp đồng as-built ở `phase-03-backend.md`.

## Đã làm
1. **Báo cáo khóa 30** `/report/holiday-work`: mục ở `report-catalog-hr.ts` (nhãn = `REPORT_KEY` sinh tự động, gác
   `leave_comp_request`, nguồn **Nghỉ bù**, icon `CalendarCheck`, `overviewKpis: ['lines']`). Trang `holiday-work-report-page.tsx`:
   KPI `lines · people · holiday_lines · comp_days`, bảng thêm `offday_lines` + `pending_lines` (chỉ hiện khi bật chờ duyệt — bảng
   tự bỏ cột vắng khỏi meta), xu hướng `lines`, nhóm mặc định phòng ban, kỳ mặc định năm nay, drilldown `/summary/rows`.
   Ô lọc `holiday-work-report-filters.tsx`: phòng ban (dùng chung) · Loại ngày (`day_kind` 0/1/2, mặc định không ghi URL) ·
   công tắc **Gồm phiếu chờ duyệt** (`include_pending=1`; công tắc đọc đúng bộ chữ backend coi là bật 1/true/yes/on).
2. **Quỹ phép năm (báo cáo khóa 8)**: `tableMetrics: ['comp']` → cột **Nghỉ bù cộng thêm** hiện sẵn ở bảng.
3. **Màn Quỹ phép — hai thẻ** **Theo dòng quỹ | Theo nhân sự** (`?view=people`). Đổi thẻ ghi URL một lượt: giữ tìm + năm, bỏ ô lọc
   riêng của thẻ cũ. Thẻ dòng quỹ tắt truy vấn 5000 dòng khi đang ở thẻ nhân sự. Ma trận `leave-balance-matrix-table.tsx`:
   `DataTable` phân trang backend theo người, cột động theo `columns` (khóa `cells` CHUỖI), ô vắng **—**, số âm đỏ, cột Tổng,
   lọc tìm/phòng ban/trạng thái NV/năm (thẻ trượt ở khổ hẹp), Xuất Excel gác `leave_balance.export` + chặn bấm đúp bằng
   `useSingleFlight`, thẻ khổ hẹp riêng.
4. **Hộp Cấp quỹ** `leave-balance-allocate-dialog.tsx` thay nút bấm-là-chạy: năm khóa theo năm đang xem · loại nghỉ chọn nhiều
   (chỉ loại có trừ quỹ; trống = mọi loại) · pháp nhân · phòng ban (lọc theo pháp nhân, đổi pháp nhân thì về **mọi phòng**) ·
   hình thức NV · cấp bậc. Ô trống KHÔNG gửi. Chặn bấm đúp. Kết quả vẫn báo qua thông báo cũ của `useAllocateLeaveBalance`.
5. Tách `leave-balance-year-select.tsx` dùng chung hai thẻ.

## Tệp
Tạo (`frontend-v2/src/`): `modules/report/pages/holiday-work-report-page.tsx` · `modules/report/components/holiday-work-report-filters.tsx`
(+ test) · `modules/hr/components/leave-balance-matrix-table.tsx` (+ test) · `leave-balance-matrix-columns.tsx` ·
`leave-balance-matrix-card.tsx` · `leave-balance-matrix-day-cell.tsx` · `leave-balance-allocate-dialog.tsx` (+ test) ·
`leave-balance-year-select.tsx` · `modules/hr/api/leave-balance-matrix-api.ts` · `modules/hr/hooks/use-leave-balance-matrix.ts`.
Sửa: `report/config/report-catalog-hr.ts` (+ test) · `report/pages/leave-balance-report-page.tsx` · `hr/pages/leave-balance-page.tsx`
· `shared/constants/app-routes.ts` (+`report.holidayWork`) · `shared/constants/query-keys.ts` (+`hr.leaveBalanceMatrix`) ·
`hr/api/leave-api.ts` (chỉ thêm kiểu `LeaveBalanceAllocatePayload`) · `hr/hooks/use-leave.ts` (chỉ đổi kiểu tham số allocate).
`statuses.ts` không sửa tay (đã sinh ở phase 03). Không đụng routes.tsx / leave-section-tabs / tệp chính sách.

## Kiểm
- typecheck (host) 0 lỗi · eslint các tệp đã đụng 0 lỗi 0 cảnh báo.
- `vitest run src/modules/report src/modules/hr`: 192 tệp / 1954 bài xanh (trước lượt sửa cuối); lượt sau chạy lại riêng các tệp
  đụng: xanh. Bài **loads a component** nạp động trang báo cáo chập chờn quá trần 5 giây khi máy bận (cả bài **đợt 4** có sẵn) —
  bài mới đặt trần 20 giây.
- Trình duyệt localhost:8083 (1440 + 390 giả lập điện thoại): ma trận ra đúng 256 người/2 cột; hộp Cấp quỹ năm 2027 lọc phòng
  **Hành chính** → **thêm 40 dòng**, ma trận 2027 chỉ có 20 người Hành chính; báo cáo khóa 30 ra KPI, bật chờ duyệt có cột **Đang
  chờ duyệt**, danh sách drilldown đúng cột; báo cáo Quỹ phép có cột **Nghỉ bù cộng thêm**. Sửa hai lỗi thấy khi soát: cột **ID**
  trống tự chèn ở ma trận rỗng (tắt `idColumn`), nút Xuất Excel ép ô tìm ở 390px (khổ hẹp chỉ còn biểu tượng).

## Ghi chú / hở
- Đã `docker compose restart api` để `ensure_report_access_defaults` cấp khóa 30 cho admin; phiên trình duyệt đăng nhập sẵn vẫn
  giữ `report_keys` cũ (403) tới khi đăng nhập lại — đã kiểm bằng phiên riêng. Cần ghi vào HDSD (phase 05).
- DB local nay có 40 dòng quỹ năm 2027 của phòng Hành chính (do thử hộp Cấp quỹ).
- Chưa thử ca **phiếu nghỉ bù ngày lễ → duyệt → ra đúng tên lễ** trên giao diện (local chỉ có 1 phiếu ngày nghỉ theo lịch); backend
  đã có bài kiểm.

## Câu hỏi còn mở
- Không.
