# duoc-CR-687 — HDSD Báo cáo Nhân sự đợt 2 (tai-lieu-kiem-thu, 27/10/2026)

## Kết quả
Thẻ «Hướng dẫn sử dụng Báo cáo Nhân sự» từ 1 + 7 thành **1 + 9 bài**. Seed chạy 3 lần trên local, lần nào cũng xóa cây cũ rồi dựng lại 10 bài, không lỗi. Cả 10 trang mở được trên :8082, liên kết chéo đúng slug. Không có tên mã nào (`employee_sensitive`, `.read`…) hay dấu ngoặc nhọn sót trong nội dung.

## Thay đổi
- `backend/scripts/seed_help_bao_cao_nhan_su.py`
  - Bài MỚI «Báo cáo Nhân sự — Xuất Sổ quản lý lao động»: luật 30 ngày (giấy hoặc điện tử), ai có trong sổ, 4 thẻ số, người «Đã nghỉ» thiếu ngày nghỉ bị loại, các chiều Xem theo, các cột của danh sách (không có CCCD/BHXH/lương), các bước bấm «Xuất sổ (Excel)», mỗi pháp nhân một sheet, dòng tô vàng + cột «Thiếu thông tin bắt buộc», bảng cột hệ thống điền / Nhân sự điền tay, cột Nâng lương, ngày nghỉ, cách chọn hợp đồng, quyền cần có.
  - Bài MỚI «Báo cáo Nhân sự — Lập báo cáo sử dụng lao động mẫu 01/PLI nộp Sở Nội vụ»: thẻ số và cột, luật suy nhóm vị trí việc làm (Phó phòng trở lên / ĐH-SĐH / TC-CĐ / Khác), chọn kỳ (Năm nay; Tùy chọn khoảng ngày 01/01–30/06 → Áp dụng), «Xuất mẫu 01/PLI», bố cục tệp, cột phải điền tay (13–15, 17, 18–19, 25–26), so tiêu đề bảng với mẫu chính thức, hạn 05/6 · 05/12, Sở Nội vụ qua Cổng DVC quốc gia, rồi báo BHXH khu vực.
  - Bài «Đọc báo cáo Biến động nhân sự»: thêm 4 chiều Xem theo (Nhóm tuổi · Trình độ · Địa điểm làm việc · Nhóm vị trí việc làm), dòng «(Chưa gắn)», che số nhóm tuổi dưới 3 người («—», không có nút Xem, có trong tệp Xuất Excel), danh sách theo nhóm tuổi cần quyền xem thông tin nhạy cảm; thêm câu về «Kỳ này chưa có dữ liệu» / «Xem cả năm nay».
  - Bài quản trị: bảng quyền thêm dòng khóa 19/20 (cần thêm 2 quyền), câu về quyền xuất, giao 4 báo cáo mới, cảnh báo hai báo cáo có CCCD/BHXH/ngày sinh/địa chỉ/lương nên chỉ giao trưởng phòng Nhân sự và Ban Giám đốc.
  - Thẻ gốc: 7 báo cáo, thêm 2 dòng bảng. `EXPECTED_ARTICLES` 8 → 10. Docstring khai CR-687 và mục A2/B2/B3.
- `doc/tai-lieu-chuc-nang/README.md`, `00-muc-luc.md` (mục 36): thêm 2 báo cáo, 2 đường, CR-687.

## Nguồn nhãn (soát trên :8083, admin)
Tiêu đề trang, «Xuất sổ (Excel)», «Xuất mẫu 01/PLI», tên thẻ số và cột, Xem theo (sổ/01-PLI: Công ty · Phòng ban · Nhóm vị trí việc làm; Biến động: 11 chiều), nút kỳ («Năm nay», «Tùy chọn khoảng ngày», «Áp dụng»): lấy từ màn thật và từ `meta`/`notes` của `/summary`. Câu báo 403 nhóm tuổi chép từ `report_headcount_privacy.py`.

## Chưa làm / bỏ qua
- RAG: AI_RAG_ENABLED đang tắt ở local, nên chưa chạy `reindex_help_rag.py`. Khi seed lên dev phải chạy `--purge-orphans`.
- Không seed lên dev hay prod. Không commit.
- Chưa ghi `nhat-ky-task.md` và `change-log-bao.md`: đề bài không giao, và hai tệp đang có thay đổi dở của chủ CR-687.
- Chưa kiểm được trên trình duyệt việc che nhóm tuổi và câu báo thiếu quyền, vì admin có đủ quyền. Bài viết theo mã và bài kiểm đơn vị.

## Lệch giữa tài liệu kỹ thuật và mã (không thuộc khu em sửa)
`doc/erp/hrm/05-bao-cao-nhan-su.md` vẫn ghi A2/B2/B3 là «đề xuất». Ngoài ra:
- B3 ghi «danh sách lấy người đang làm tại ngày cuối kỳ», nhưng mã lấy mọi người làm việc trong kỳ, người nghỉ có ghi chú ở cột 27.
- B3 ghi «mỗi pháp nhân một tệp», nhưng mã xuất một tệp, mỗi pháp nhân một sheet.

Bài HDSD viết theo mã. Chủ tệp 05 cần sửa lại cho khớp.

## Câu hỏi còn mở
1. Câu báo 403 của sổ/01-PLI có hiện tên mã quyền (`employee_sensitive.read`, `labor_contract.read`) cho người dùng không? Có nên bỏ phần mã trong ngoặc ở `report_inputs.py` (khu Agent 4) không?
2. «Năm nay» chỉ chạy từ 01/01 đến hôm nay. Báo cáo năm nộp trước 05/12 dùng kỳ này có đúng ý không, hay cần hướng dẫn chọn đến 30/11 / 31/12?
3. Nhãn tiêu đề 27 cột chưa đối chiếu từng chữ với bản mẫu chính thức. Bài đã dặn Nhân sự so lại trước khi nộp.

**Status:** DONE_WITH_CONCERNS
**Summary:** Đã thêm 2 bài, sửa bài Biến động và bài quản trị. Seed local 10 bài chạy lại được, :8082 hiện đủ. Đã cập nhật hai dòng mục lục và README.
**Concerns/Blockers:** Chưa kiểm được trên trình duyệt việc che nhóm tuổi và câu báo thiếu quyền. Tài liệu 05 lệch mã ở B3. Chưa ghi sổ và change-log, chưa nạp RAG.
