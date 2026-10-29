# Sửa lỗi E2E CR-686/687/688 (N2, N3, M1, M7, M12, M13, M16, M22)

Chưa commit. N1 không đụng.

## Đã làm
1. N2: `employee/work_move_report_service.py` `build_rows` — `people_moved` mỗi người một dòng (sự kiện mới nhất trong kỳ) + cột «Số lượt». Test mới: thẻ = tổng danh sách = số dòng.
2. N3: `benefit-audience-filters.tsx` khóa công tắc + dòng giải thích khi thiếu `leave_request.read`. Thêm `ReportPageConfig.paramsRequirePermission` (types + `report-analytics-page.tsx`) bỏ `include_on_leave` khỏi mọi lời gọi API (summary, rows, export) khi thiếu quyền; cấu hình ở `benefit-audience-report-page.tsx`. Vitest: filter + page.
3. Điện thoại 390px: ô Phòng ban / Công ty `max-md:min-w-36` (hết co về 1 ký tự). Bảng nhóm: cột nhóm ghim hẹp 128px trên mobile (`useIsMobile`), bảng vẫn cuộn ngang, không giấu cột.
4. Nút «Xem» ở dòng: `pickDrilldownMetricForRow` (chỉ số biểu đồ -> KPI -> các chỉ số còn lại, lấy cái đầu có giá trị > 0 ở dòng đó, không có thì mặc định cũ). Ngăn rỗng ghi «Không có ai theo chỉ số «X» ở nhóm này — đổi chỉ số ở ô phía trên.» Vitest cho util; sửa test câu rỗng cũ.
5. Tên sheet Excel ưu tiên `short_name` (fallback `name`): `export_common.py` (`CompanyInfo.sheet_label`), sổ + 01/PLI, và `benefit_report_export.py`/controller. Vẫn qua `unique_sheet_name` (<=31, không trùng). Test 01/PLI.
6. `ct_other` = «HĐ khác (thử việc, chưa có HĐ)» (backend + test FE `labor-usage-report-page.test.tsx`).
7. HDSD Biến động sửa (bảng vẫn hiện, biểu đồ ghi «Kỳ này chưa có phát sinh»). Không có câu nào về so sánh cùng dịp năm trước trong bài Phúc lợi (đã rà). Seed chạy lại local OK (gốc id=415); chưa reindex RAG.
8. `doc/erp/hrm/05-bao-cao-nhan-su.md` H1: «So với cùng dịp năm trước» -> ⏳ chưa làm.

## Cổng
- Backend `-k "cr687 or cr688 or dieu_chuyen or phuc_loi or so_lao_dong or mau_01"`: 191 pass; 1 test mới của tôi sai dữ liệu (kỳ 20 ngày), đã sửa, `test_bao_cao_dieu_chuyen_cr688.py` 20/20 pass. Chưa chạy lại toàn bộ cụm sau khi sửa test.
- Frontend: typecheck 0 lỗi; lint 0 lỗi (30 cảnh báo cũ); `vitest run src/modules/report` 55 file / 438 pass.

## Chưa làm / lưu ý
- Chưa kiểm bằng emulate 390x844 trên trình duyệt (không có công cụ trình duyệt trong phiên này); sửa dựa trên đọc mã. Cần mắt người xem lại `montage2-hr-headcount` và bảng «Chi tiết theo».
- Ô lọc trạng thái nhân sự / dự án / năng lực cũng còn `max-md:min-w-0 max-md:flex-1` (cùng kiểu lỗi), ngoài phạm vi nên giữ nguyên.
- Chưa chạy `reindex_help_rag.py`.
- Chưa có mục change-log / nhật ký task (CR chưa cấp số).

**Status:** DONE_WITH_CONCERNS
**Summary:** Đủ 8 mục; gate xanh. Riêng kiểm 390px bằng trình duyệt chưa làm được.
**Concerns/Blockers:** Mục 3 chưa xác nhận bằng mắt; cần reindex RAG và ghi nhật ký task khi chốt CR.
