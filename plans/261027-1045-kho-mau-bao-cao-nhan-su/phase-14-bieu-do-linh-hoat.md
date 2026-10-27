# Phase 14 — Biểu đồ linh hoạt (dùng chung mọi báo cáo)

**Chủ:** FE-a · **Tài liệu:** `doc/erp/hrm/05-bao-cao-nhan-su.md` §3.4 · không cần backend.

- Một thẻ «Biểu đồ» trong `ReportAnalyticsPage` thay khối xu hướng hiện tại, MẶC ĐỊNH trông như cũ (đường xu hướng chỉ số đang chọn).
- Người xem chọn: **Vẽ theo** «Thời gian» (dữ liệu `trend`) hoặc «<chiều đang Xem theo>» (dữ liệu `groups`); **Kiểu**: Thời gian → đường / cột; Nhóm → cột ngang (mặc định, xếp lớn → nhỏ) / cột / vành khuyên (chỉ khi ≤ 6 nhóm có số) ; **Top N** 5 / 10 / 20 / tất cả (phần dư gộp «Khác»); chỉ số = thẻ KPI đang chọn (đã có). Chỉ số thời điểm hoặc `hideTrend` → mặc định «Vẽ theo nhóm».
- Bỏ qua giá trị `null` (nhóm bị che) và nhóm `__other__` khi vẽ; ghi chú nhỏ «N nhóm bị che không vẽ».
- Bấm một cột / một miếng → mở ngăn «Danh sách» của nhóm đó (nếu báo cáo có drilldown và chỉ số có trong `drilldown_metrics`).
- Nút «Tải ảnh PNG» (SVG → canvas → PNG, tên `bieu-do-<slug>-<từ>-<đến>.png`).
- Lựa chọn nằm trên URL (`chart_by`, `chart_type`, `chart_top`) để gửi đường dẫn mở đúng góc nhìn.
- Recharts (đã có). Test vitest: chọn kiểu theo dữ liệu, bỏ null, Top N gộp «Khác», giới hạn vành khuyên, URL state.
