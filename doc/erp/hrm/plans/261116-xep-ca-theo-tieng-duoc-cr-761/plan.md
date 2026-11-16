# Xếp ca theo tiếng cho từng ngày (duoc-CR-761)

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 16/11/2026 |
| Người phụ trách | Anh Được |
| Trạng thái | Hiệu lực |
| Trạng thái kế hoạch | xong (mã, tài liệu, HDSD xong ở local; chờ commit và deploy dev theo `03-lich-lam-viec.md` §22.11) |
| CR liên quan | duoc-CR-761 (nền: duoc-CR-589 lịch làm việc, duoc-CR-757 Trưởng phòng gán lịch riêng) |

## Yêu cầu

Trưởng phòng xem lịch làm việc của cả phòng và xếp lại ca theo tiếng cho từng nhân viên; có việc đặc thù làm không liền
(livestream bán hàng) nên một ngày chia nhiều khung giờ. Chỉ XẾP CA, không chấm công (chốt 16/10/2026 vẫn giữ).

## Chốt của người chủ (16/11/2026)

| # | Câu | Chốt |
|---|---|---|
| Q1 | Cách xếp | Theo TỪNG NGÀY cụ thể (người × ngày) trên lưới của phòng + chép nhanh (sang ngày khác, chép tuần trước). Ngày không xếp → theo mẫu lịch tuần như cũ |
| Q2 | Đơn vị | Tiếng tròn, 00:00–24:00 |
| Q3 | Tính phép | Ngày có ca = 1 ngày công: nghỉ cả ngày trừ 1; nửa ngày: khung trước 12:00 là sáng, từ 12:00 là chiều (nửa không có khung → 0); theo giờ = giờ nghỉ ∩ khung ÷ tổng giờ ca ngày đó |
| Q4 | Nhân viên | Thấy ca của mình (Trang cá nhân, trợ lý) + chuông báo khi ca được xếp / đổi |

Chốt thêm sau rà mã (16/11/2026):

| # | Câu | Chốt |
|---|---|---|
| Q5 | Giao diện hộp Xếp ca | Danh sách khung giờ (Từ → Đến, HH:MM) + thanh xem trước 00:00–24:00 + mẫu nhanh; bỏ dãy 24 số trần |
| Q6 | Đổi ca ngày đã có đơn nghỉ chờ duyệt / đã duyệt | CHẶN, báo rõ mã đơn; xếp hàng loạt từ chối cả lượt, chép tuần bỏ qua ô đó và liệt kê |
| Q7 | Tự xếp ca / nghỉ bù | Không ai tự xếp ca cho chính mình (kể cả HR). Nghỉ bù không nhận ngày *nghỉ do xếp ca* nếu ca đó được ghi vào hoặc sau chính ngày đó |
| Q8 | Nửa ngày khi cả ca nằm trong buổi đó | Trừ 1 ngày (ca chỉ sáng + nghỉ sáng = 1); ca ở cả hai buổi thì nửa ngày vẫn 0,5 |

| Q9 | Ai thấy ai trên màn Lịch làm việc (16/11/2026) | HR (`work_schedule.write`) và quản trị: theo phạm vi xem nhân sự; Trưởng phòng (`work_schedule_personal`): CHỈ nhân viên phòng mình (gồm phòng kiêm nhiệm) + bản thân; nhân viên thường: CHỈ bản thân. Áp cho lưới, danh sách ca và công cụ AI |
| Q10 | Giám đốc / quản lý cấp cao (16/11/2026) | Vai trò `company_head` và `MANAGER` được `work_schedule_personal` CHỈ XEM bậc Công ty → xem lịch cả pháp nhân của mình, không sửa. Quản lý thu mua, Văn thư: chỉ bản thân. Hệ đang chạy phải tick tay (D-018) |

## Thiết kế

**Dữ liệu.** `tab_work_shift_day` (employee_id, work_date, note, AuditMixin; UNIQUE(employee_id, work_date)) +
`tab_work_shift_segment` (shift_day_id, start_hour SMALLINT 0–23, end_hour SMALLINT 1–24, sort_order). Ngày có dòng mà
không khung = NGHỈ do xếp ca. Khung không chồng, start < end, tối đa 12 khung / ngày.

**Phân giải.** Ca theo ngày THẮNG mọi cấp gán (nhân sự > phòng > pháp nhân > hệ thống). `DaySpec` thêm `segments`;
`resolver.load_day_plans` / `resolver_many` nạp ca theo khoảng ngày bằng số truy vấn cố định. `workday_service` áp Q3 cho
ngày có ca; ngày lễ vẫn bỏ qua như cũ.

**Quyền.** HR (`work_schedule.write`): mọi người trong phạm vi `employee`, mọi ngày. Trưởng phòng (`work_schedule_personal`):
nhân viên trong phạm vi khóa đó (như CR-757), không cho chính mình, chỉ ngày ≥ hôm nay (giờ VN). Xem: màn Xem lịch như cũ
(`employee.read` + lớp nghỉ phép); nhân viên luôn xem được ca của chính mình.

**API** (`/api/work-shifts`): đọc theo khoảng (≤ 42 ngày) + phòng / người; đặt ca một ngày (thay cả danh sách khung);
xóa = về mẫu tuần; áp một bộ khung cho nhiều người × nhiều ngày; chép tuần (nguồn → đích). Trần số ô mỗi lượt.

**Thông báo.** Mỗi lượt lưu gom MỘT chuông cho mỗi nhân viên bị đổi (khoảng ngày), không chuông cho chính người bấm.

**Giao diện.** Lưới Xem lịch: ô có ca hiện khung giờ đủ HH:MM, là NGOẠI LỆ nên nổi màu (luật lưới lịch đã chốt); bấm ô →
hộp xếp ca (bản đầu là 24 ô tiếng bấm / kéo chọn; đã thay theo Q5 bằng danh sách khung Từ → Đến + thanh xem trước + mẫu nhanh), nút Nghỉ cả ngày / Về mẫu tuần / Áp cho các ngày khác; thanh công cụ Chép tuần
trước. Trang cá nhân: thẻ Ca làm việc tuần này. Trợ lý: công cụ ca của tôi.

## Các pha

| Pha | Nội dung | Chủ | Trạng thái |
|---|---|---|---|
| P1 | Backend: bảng + migration, phân giải, tính phép Q3, API, quyền, chuông, roster trả ca | backend | xong |
| P2 | Giao diện: lưới + hộp xếp ca + chép nhanh + thẻ Trang cá nhân | giao-dien-v2 | xong |
| P3 | Trợ lý + cổng MCP: công cụ ca của tôi + ca của nhân viên (người có quyền xem), khai đủ sổ công cụ / nhóm MCP / bộ lọc; cẩm nang AI (bản mới) | ai-mcp | xong |
| P4 | Rà mã, tài liệu, HDSD (bài mới trên Trung tâm trợ giúp), nạp lại chỉ mục RAG, commit | điều phối + tai-lieu-kiem-thu | tài liệu + HDSD xong (local, 16/11/2026); RAG local tắt — chạy trên dev; commit do điều phối |

Người chủ dặn thêm 16/11/2026: *"cập nhật rag, hdsd, mcp nha"* — ba việc trên là BẮT BUỘC của CR này, không để sau.
RAG local đang tắt (`AI_RAG_ENABLED`), nên nạp lại chỉ mục chạy được ở local thì chạy, không thì ghi vào sổ việc deploy để
chạy trên dev ngay sau khi lên bản.

Tài liệu rút ý (luật 8): [`../../03-lich-lam-viec.md` §22](../../03-lich-lam-viec.md), [`../../02-nghi-phep.md` §18](../../02-nghi-phep.md), CN-HRM-05, PCN-HRM-18…21.
