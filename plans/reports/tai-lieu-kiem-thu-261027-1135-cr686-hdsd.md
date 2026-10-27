# HDSD duoc-CR-686 — Báo cáo Nhân sự (local)

Kết quả: thẻ mới «Hướng dẫn sử dụng Báo cáo Nhân sự» + 7 bài đã seed trên LOCAL, chạy lại lần hai sạch, portal :8082 mở được. Kho vector chưa nạp vì local tắt RAG.

## Tệp
- MỚI `backend/scripts/seed_help_bao_cao_nhan_su.py` — khuôn `help_seed_common.rebuild_tree`, thêm `check_unique_titles()` so theo slug với mọi bài đang có.
- SỬA `doc/tai-lieu-chuc-nang/00-muc-luc.md` (dòng 36) + `README.md` (1 dòng) — trỏ sang `doc/erp/hrm/05-bao-cao-nhan-su.md`, giống nếp của Nghỉ phép / Lịch làm việc. Không tạo tài liệu chức năng riêng.

## Cây bài (gốc id=337 local, thẻ trang chủ sort_order=13)
1. Lọc theo phòng ban và xem danh sách sau mỗi con số (Phòng ban / kỳ / Công ty, Xem danh sách, Xem, ngăn Danh sách, ô Chỉ số, 500 dòng, bảng lỗi thường gặp)
2. Đọc báo cáo Biến động nhân sự (có ghi chú thiếu ngày vào làm)
3. Đọc báo cáo Tình hình nghỉ phép (chia ngày theo kỳ, 3 cột mới, tìm đơn treo)
4. Đọc báo cáo Quỹ phép năm (Trạng thái nhân sự, Chưa được cấp quỹ, các cột tách quỹ)
5. Theo dõi hợp đồng lao động sắp hết hạn (mới)
6. Tìm hồ sơ và tài khoản còn thiếu (mới, theo nhóm quyền)
7. Dành cho quản trị: giao quyền xem báo cáo (tab «Báo cáo», hai lớp quyền)

Mọi tiêu đề có tiền tố «Báo cáo Nhân sự —», không trùng slug. Liên kết chéo 13/13 đúng slug (gồm 3 bài cũ: Cấp và điều chỉnh quỹ phép, Hiểu số ngày phép còn lại, Khóa tài khoản…).

## Nguồn nhãn
Màn thật localhost:8083 (admin): menu Báo cáo ▸ Nhân sự, «Xem bảng chi tiết», «Xuất Excel», «Phòng ban», «Tháng này», «Công ty», «Cách tính số liệu (N lưu ý)», «Xem danh sách», bảng «Chi tiết theo …» / «Xem theo» / cột «Danh sách» / nút «Xem», ngăn «Danh sách» + ô «Chỉ số». Tên chỉ số + cột danh sách + lưu ý: `meta.metrics`, `/summary/rows`, `notes` của 5 đường API local. Tab quyền: `report-access-tab.tsx`, `report-access-dialog.tsx`.

## Kiểm
- Seed 2 lần: 8 bài → xóa 8, dựng lại 8. Không khóa, không mật khẩu trong bài.
- `http://localhost:8082/bao-cao-nhan-su-theo-doi-hop-dong-lao-dong-sap-het-han` hiện đủ 3 mục h2 + bảng; thẻ gốc nằm trong menu trái.
- `reindex_help_rag.py --purge-orphans`: dừng với «AI_RAG_ENABLED đang tắt» — không tự bật cờ.

## Lệch giữa tài liệu 05 và mã (bài HDSD viết theo MÃ)
- B1 ghi «Chờ chốt: có hiện lương không. Mặc định là **không hiện**» nhưng danh sách HĐLĐ đang trả Lương cơ bản / Lương đóng BHXH / Phụ cấp cho mọi người có `labor_contract.read`. Bài HDSD ghi cảnh báo «chỉ giao cho người được xem lương».
- B1 đánh ✅ «Tô đỏ khi còn ≤ 15 ngày», «HĐ gia hạn», «Tỷ lệ qua thử việc» — màn và API chưa có. Bài HDSD không nhắc.
- E1 đánh ✅ «chưa được gán lịch làm việc», xem theo «Loại thông tin còn thiếu» — API chỉ có chiều Công ty / Phòng ban (+ khối «Theo loại còn thiếu»), không có chỉ số lịch làm việc. Bài HDSD không nhắc.

## Chưa làm (để điều phối quyết)
- Sổ `nhat-ky-task.md` / `change-log.md`: mục duoc-CR-686 do điều phối giữ, tệp đang bẩn việc của người khác → em không sửa. Đề nghị thêm 1 câu vào mục đó: «Viết bộ hướng dẫn Báo cáo Nhân sự trên Trung tâm trợ giúp (1 thẻ, 7 bài), đã seed local. Mã nguồn: backend/scripts/seed_help_bao_cao_nhan_su.py».
- Dev: chưa seed (đề bài chỉ cho local). Lên dev thì chạy seed + `reindex_help_rag.py --purge-orphans` theo bước 7 skill `viet-hdsd`.
- Chưa commit.

## Câu hỏi mở
1. Lương trong danh sách HĐLĐ: giữ như mã (hiện) rồi sửa tài liệu 05, hay ẩn theo «mặc định không hiện»? Đổi thì phải sửa bài HDSD số 5 và 7.
2. Có bật RAG ở local để nạp thử, hay chỉ nạp khi lên dev?

**Status:** DONE_WITH_CONCERNS
**Summary:** Seed 1 thẻ + 7 bài HDSD Báo cáo Nhân sự trên local, chạy lại được, portal hiện đúng; mục lục/README tài liệu chức năng trỏ sang doc 05.
**Concerns/Blockers:** RAG local tắt nên chưa nạp kho vector; doc 05 lệch mã ở B1 (lương, tô đỏ, gia hạn) và E1 (lịch làm việc); sổ nhật ký để điều phối ghi.
