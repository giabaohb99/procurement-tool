# Báo cáo tổng quan phân hệ Dự án cho người quản lý (duoc-CR-782)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1.0 | 18/11/2026 | Anh Được | Hiệu lực | duoc-CR-782 |

Trạng thái kế hoạch: xong

## Yêu cầu

Anh Được: *"cái báo cáo tổng quan chưa đủ, chưa có đối chiếu user chưa có gì hết xáo rỗng, cần thêm, em hãy tưởng tượng em
là xếp và cần những thông tin nào khi nhìn vào report"*.

## Nguyên nhân "rỗng"

Phân hệ lấy ranh giới là tư cách thành viên (`visible_list_ids`); xếp không được mời vào dự án nào nên màn Tổng quan ra
toàn 0, kể cả admin.

## Quyết định của anh Được (18/11/2026)

- **Phạm vi:** ai xem được báo cáo Công việc & Dự án (`ReportKey.WORK`, gán ở tab Báo cáo; admin có sẵn) thì Tổng quan
  đếm trên mọi dự án; còn lại giữ luật thành viên. Chỉ nới phần đọc số liệu — dự án / việc không là thành viên vẫn không
  mở được (máy chủ trả `can_open = false`, giao diện không dẫn link).
- **Các khối:** bảng đối chiếu theo người, sức khỏe từng dự án, cần xử lý ngay. Bỏ khối xu hướng 8 tuần.

## Cách làm

- Backend `app/modules/work/`: `overview_scope.py` (phạm vi + dự án mở được), `overview_people.py` (bảng theo người,
  một câu SQL `SUM(CASE …)` nhóm theo người phụ trách + việc của một người), `overview_projects.py` (sức khỏe dự án,
  `ProjectHealth` 0–3 suy ra, trả mã + nhãn), `overview_attention.py` (quá hạn kèm người giữ + số ngày trễ, chưa ai nhận,
  chưa đặt hạn); `overview_service.overview` thêm `period_days`, chỉ số trong kỳ (tạo mới, xong, % đúng hạn). Đường mới
  `GET /api/work/overview/people/{employee_id}/tasks`.
- Bài canh phạm vi phân hệ Công việc (`test_pham_vi_bo_may_duyet_xuyen_suot.py`) khai thêm cửa gác `overview_list_ids`
  kèm lý do.
- Giao diện `modules/work/`: trang Tổng quan dựng lại (nút kỳ, 6 thẻ số, ba danh sách cần xử lý, bảng theo người + hộp
  việc của một người, bảng sức khỏe dự án, cơ cấu ưu tiên + việc của tôi). Bỏ biểu đồ việc chưa xong theo dự án (bảng sức
  khỏe nói đủ hơn).

## Biểu đồ (anh Được bổ sung cùng ngày)

*"nên thêm chart để biểu diễn nữa"*, rồi *"cân nhắc biểu đồ cột + line thay vì ngang ngang"*.

- **Tình trạng việc đang mở** (vòng): quá hạn / đến hạn 7 ngày / còn hạn / chưa đặt hạn — backend thêm `task_due_soon`.
- **Dự án** và **Theo người**: cột đứng chồng (việc mở, phần đỏ quá hạn) + đường việc xong TRONG KỲ, MỘT trục (cùng đơn
  vị "việc"; không làm hai trục). Component dùng chung `shared/ui/stacked-column-line-chart.tsx`. Backend thêm
  `done_in_period` theo dự án — bản đầu vẽ đường bằng tổng việc xong từ trước tới nay, lớn gấp nhiều lần việc mở nên cột
  bị bẹp.
- Màu chạy bộ kiểm dataviz (`validate_palette.js`) ở nền sáng và tối: đường xanh lá trạng thái trượt ở nền tối (đỏ ↔ xanh
  lá ΔE 5,0 với mù màu đỏ-lục) nên đổi sang `chart-3` (xanh ngọc), đạt mọi mục.

## Theo dõi từng dự án / từng người (anh Được hỏi thêm cùng ngày)

*"biểu đồ có thể theo dõi được từng dự án ko, theo dõi hiệu suất của từng user ko"*. Các biểu đồ trên là ảnh chụp tại
thời điểm này; khối mới chọn MỘT dự án / MỘT người → dải số riêng + diễn biến theo ngày (kỳ ≤ 31 ngày) hoặc tuần: cột việc
xong (đúng hạn / trễ / không hạn), đường việc mới giao. Backend `overview_trend.py` (2 câu SQL gom theo ngày giờ VN, chia
tuần ở Python), đường `GET /api/work/overview/trend?kind=project|person&id=&period_days=`, cùng cửa gác phạm vi.

## Bố cục chia tab (anh Được chốt cùng ngày)

Bản xếp dọc chín khối dài và rời. Anh chọn chia tab và dặn *"cái nhìn vô đầu tiên phải là cái chart, rồi mấy cái sau thì để
user mò"*, rồi *"các mục quan trọng nên đưa vào tổng quan"*: trên cùng nút kỳ + sáu thẻ số; tab **Tổng quan** (mặc định)
biểu đồ đứng đầu, ngay dưới ba danh sách cần xử lý + cơ cấu ưu tiên + việc của tôi; **Dự án** (thẻ sức khỏe từng dự án + theo dõi
một dự án); **Nhân sự** (bảng đối chiếu + theo dõi một người). Tab trên URL `?tab=`. Bảng sức khỏe dự án đổi thành lưới thẻ (anh chê bảng "xấu": chín dòng dự án trống toàn số 0,
chữ "chưa là thành viên" lặp từng dòng) — dự án trống gom thành một dòng chữ, chưa là thành viên chỉ còn biểu tượng ổ khóa.

## Báo cáo riêng từng dự án + nút quay lại (anh Được bổ sung cùng ngày)

- Màn chi tiết một dự án có nút quay lại danh sách dự án (trước đây phải bấm "Dự án" trên menu trái).
- Tab thứ năm **Báo cáo** trong chi tiết dự án: `/api/work/overview?list_id=` (lọc trong phạm vi xem — dự án ngoài phạm vi ra
  bộ số rỗng) + biểu đồ diễn biến `kind=project`. Khổ 390px siết đệm tab để năm tab vừa một hàng.
- Bố cục tab Báo cáo: anh chê bản xếp dọc một cột (cây dự án bóp hẹp, sáu thẻ số gãy chữ) và chọn **cột phải cố định**.
  Cột trái là nút kỳ, biểu đồ diễn biến, biểu đồ theo người, bảng đối chiếu. Cột phải rộng 18rem gồm thẻ tóm tắt (% hoàn thành
  lớn + sức khỏe + các số xếp dọc), vòng tình trạng việc mở và thẻ **Cần xử lý** gom ba nhóm (quá hạn / chưa nhận / chưa hạn)
  vào một khung có nút chuyển, mở sẵn nhóm đầu tiên có việc. Chia cột theo bề rộng của khung (`@container`, mốc 768px), không
  theo màn hình: 1440px và 1366px đều ra hai cột dù cây dự án đang mở. Khung hẹp thì xếp một cột, thẻ tóm tắt lên đầu.

## Chỉnh giao diện kèm theo (anh Được góp cùng ngày)

- Cây dự án bên trái: con của nhóm treo trên đường gióng dọc, dự án lẻ có tiêu đề "Chưa thuộc nhóm", dòng đang mở tô
  `bg-primary/10` chữ đậm (nền `accent` cũ gần trùng nền cây).
- Ô tìm của bảng việc lúc thu gọn là nút có viền + chữ "Tìm việc" (bản cũ là kính lúp xám không viền).
- Màn danh sách dự án: ô tìm + nhóm thành nút lọc có số (kèm bánh răng quản lý nhóm) + nút "Lưu trữ", một hàng trên
  bảng. Dải bốn số tổng thử thêm rồi bỏ theo ý anh.

## Kiểm

- Backend: 14 bài mới `test/backend/test_bao_cao_tong_quan_du_an_cr782.py` + 6 bài `test_du_an_dien_bien_cr782.py`
  (mốc ngày / tuần, tách đúng hạn / trễ / không hạn, ngoài phạm vi rỗng, chỉ việc phụ trách, số câu SQL cố định) (phạm vi, từng chỉ số theo người, người theo dõi
  không tính, bốn phần tình trạng việc mở, xong trong kỳ theo dự án, % đúng hạn rỗng, ngưỡng sức khỏe, dự án trống / lưu trữ, cần xử lý, việc của một người, `can_open`, số câu SQL
  không tăng theo số người); bài cũ tổng quan sửa theo hợp đồng mới; bộ bài phân hệ Công việc xanh (bài nghỉ phép
  `test_nghi_nhieu_khoang_ngay_cr683::test_p3_roster…` đỏ sẵn, không do CR này); ruff sạch.
- Giao diện: typecheck, lint sạch; vitest `src/modules/work` + `src/shared/ui` xanh (thêm `work-overview-charts.test.tsx`, `work-overview-tracker.test.tsx`,
  `work-overview-project-health-cards.test.tsx`, `work-project-attention-card.test.tsx`); trình duyệt khổ 1440, 1366 và 390, biểu đồ soát với một dự án thử tạm (đã xóa) có việc quá hạn.

## Chưa làm

- Cẩm nang Trợ lý (`seed_handbook/30-du-an-cong-viec.md`) và công cụ MCP chưa trả các số liệu mới.
- Xu hướng theo tuần (anh bỏ khỏi đợt này).
