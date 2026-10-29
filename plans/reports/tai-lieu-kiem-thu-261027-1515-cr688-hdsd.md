# duoc-CR-688 — bài HDSD Báo cáo Nhân sự đợt 3 (local)

Ngày 27/10/2026 · Agent 2 (tài liệu và kiểm thử) · nhánh `erp-v2` · CHƯA commit

## Kết quả
Seed `backend/scripts/seed_help_bao_cao_nhan_su.py` mở rộng từ 1 thẻ + 9 bài lên **1 thẻ + 14 bài**. Đã chạy trên local
hai lần liền, cả hai đều sạch (lần 2 xóa 15 dựng 15, gốc id=400). Mọi liên kết chéo (`ref`) trỏ đúng bài đang có, không
có khóa hay chuỗi bí mật, tiêu đề không trùng bài khác. **Không chạy reindex RAG**: RAG trên local đang tắt.

## Bài mới (5)
| Tiêu đề | Nội dung chính |
|---|---|
| Báo cáo Nhân sự — Đổi kiểu biểu đồ, chọn nhóm để vẽ và tải ảnh biểu đồ | Bài chung cho mọi báo cáo: bấm thẻ để đổi chỉ số, «Vẽ theo» Thời gian / chiều «Xem theo», kiểu Đường·Cột / Cột ngang·Cột·Vành khuyên (≤ 6 nhóm, chỉ số cộng dồn được), Top 5/10/20/Tất cả gộp «Khác (… nhóm)», nhóm bị che / bằng 0 không vẽ, bấm cột/lát ra danh sách (cột Khác không bấm được), Tải ảnh PNG, đường dẫn giữ biểu đồ, phần chưa làm |
| … Đọc báo cáo Quỹ lương theo pháp nhân | Lương thỏa thuận trên HĐ (không phải lương thực trả), 4 thẻ + cột thấp nhất/cao nhất, xu hướng theo tháng (chọn Năm nay), so cùng chức vụ giữa các công ty, che nhóm < 3 người với mọi người xem, danh sách lương từng người, AI không đọc, chưa có kế hoạch / BHXH công ty |
| … Lập danh sách nhận quà và dự trù kinh phí theo dịp | Ví dụ 8/3 (300.000đ / 500.000đ, tính tay 6.800.000đ), bảng 7 dịp có sẵn (1/6 con ≤ 14, Trung thu con ≤ 15 chọn ngày tay, Tết chọn ngày tay, Sinh nhật tháng, Kỷ niệm 1/3/5/10 năm cùng tháng vào làm), dải «Đang lọc:» + «Bỏ hết điều kiện», bảng ô lọc, khoán/CTV không tính, không lưu đợt, quyền nhạy cảm, tệp ký nhận mỗi pháp nhân một sheet |
| … Rà cơ cấu quản lý và người chưa gán quản lý trực tiếp | 4 thẻ + 3 cột, Xem theo «Quản lý», gán quản lý cho người thiếu, người nghỉ dưới quyền từng quản lý, lưu ý phạm vi và hồ sơ hiện tại |
| … Theo dõi điều chuyển, bổ nhiệm và kiêm nhiệm | 4 thẻ + các cột còn lại, «Phòng đi → Phòng đến», danh sách chỉ ghi Số quyết định (không mở tệp), kiêm nhiệm hết trong 30 ngày, bộ lọc theo hồ sơ hiện tại |

## Bài sửa
- Thẻ gốc: thêm 4 dòng báo cáo vào bảng, «bảy» thành «mười một», thêm ý biểu đồ, nối bài biểu đồ.
- Bài chung (lọc + danh sách): Phúc lợi không có nút kỳ mà có ô «Ngày dịp»; cách thứ ba mở danh sách là bấm vào biểu đồ.
- Quỹ phép năm: «không có biểu đồ xu hướng» thành «không có biểu đồ theo thời gian; biểu đồ vẽ theo nhóm».
- Bài quản trị: thêm 3 dòng vào bảng quyền phân hệ gốc (21: xem HĐLĐ; 22: xem hồ sơ, lọc tuổi/con cần thêm quyền nhạy cảm;
  23–24: xem hồ sơ), quyền xuất danh sách ký nhận, bảng 8 báo cáo mới lúc đầu chỉ admin thấy kèm gợi ý giao cho ai, đoạn
  ⚠️ về Quỹ lương là số lương (giao từng người, không giao theo phòng / vai trò đông người; lọc hẹp thì Tổng = lương người đó).
  Bảng **không in số khóa 17–24** vì tab «Báo cáo» trên màn không hiện số (luật không viết mã trong bài).
- Thêm chặn `summary` > 255 ký tự trong `check_unique_titles()`: lần chạy đầu vỡ ở MySQL vì hai tóm tắt dài 264/274 ký tự
  (giao dịch rollback, cây cũ 10 bài còn nguyên); đã rút gọn rồi chạy lại.

## Nguồn nhãn
Mã màn `frontend-v2/src/modules/report/` (4 trang, `benefit-*`, `benefit-occasion-presets.ts`, `report-flexible-chart*`,
`report-flexible-chart-options.ts`, `-series.ts`), `meta` / `notes` của 4 đường `/summary` gọi trên local bằng admin, câu
lỗi + cột danh sách / tệp Excel ở backend (`benefit_report_*`, `payroll_report_service.py`, `management_report_service.py`,
`work_move_report_service.py`, `report_access/seed_defaults.py`, `assistant/tools/report_summary_tool.py`).
**Chưa soát trên màn thật bằng trình duyệt** (khung trình duyệt chung đang dùng cho việc biểu đồ).

## Điểm cần đối chiếu khi soát màn
- Biểu đồ linh hoạt đang được Agent giao diện hoàn thiện: soát lại nhãn «Vẽ theo», «Thời gian», kiểu, «Top …», «Tải ảnh PNG»,
  câu gợi ý bấm nhóm, câu nhóm bị che. Docstring seed đã ghi chú việc này.
- Quỹ lương: thẻ đầu trên màn ghi đúng «Quỹ lương (lương + phụ cấp)» (nhãn backend), không phải «Quỹ lương».
- Biểu đồ Quỹ lương mặc định vẽ «Quỹ lương» nên **không bấm ra danh sách**; phải bấm thẻ «Số người hưởng lương» trước
  (chỉ chỉ số này có danh sách). Bài chung đã nói điều kiện «chỉ số có danh sách».
- Phúc lợi: không có ô nào cho tính thêm khoán / CTV (tham số chỉ có trên URL); bài ghi «màn chưa có ô».

## Việc chưa làm (ngoài phạm vi giao)
- Không viết `doc/tai-lieu-chuc-nang/<số>-*.md`: Báo cáo Nhân sự từ CR-686/687 vẫn dùng `doc/erp/hrm/05-bao-cao-nhan-su.md`
  làm tài liệu song song (docstring seed đã nối các mục A3, A5, D1, H1, §3.4).
- Không ghi sổ `nhat-ky-task.md` / `change-log-bao.md` (đã có mục duoc-CR-688 của điều phối), không sync, không commit.
- Dev: chưa seed / reindex (chờ đợt đẩy dev).

## Câu hỏi còn mở
1. Có cần tách tài liệu chức năng riêng cho cụm Báo cáo Nhân sự ở `doc/tai-lieu-chuc-nang/`, hay giữ `doc/erp/hrm/05` làm nơi duy nhất?
2. Bảng giao quyền: gợi ý «Phúc lợi & sự kiện» giao cho Nhân sự, Hành chính là em tự đề xuất — đại ca/điều phối chốt lại?

**Status:** DONE_WITH_CONCERNS
**Summary:** Seed Báo cáo Nhân sự lên 1 thẻ + 14 bài (5 bài mới cho CR-688 + sửa thẻ gốc, bài chung, Quỹ phép, bài quản trị), chạy local hai lần sạch, link chéo đúng; RAG local tắt nên bỏ reindex.
**Concerns/Blockers:** Chưa soát màn thật trên trình duyệt; nhãn biểu đồ linh hoạt cần đối chiếu lại khi màn chốt.
