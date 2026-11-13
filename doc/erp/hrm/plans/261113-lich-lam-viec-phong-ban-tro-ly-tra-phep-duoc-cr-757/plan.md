# Lịch làm việc theo phòng ban + trợ lý AI tra phép (duoc-CR-757)

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 13/11/2026 |
| Người phụ trách | Anh Được |
| Trạng thái | Hiệu lực |
| Trạng thái kế hoạch | đang làm |
| CR liên quan | duoc-CR-757 (nền: duoc-CR-589 lịch làm việc, duoc-CR-715/717 quỹ phép) |

## Bối cảnh

Yêu cầu: cấu hình lịch làm việc riêng cho từng phòng ban; nghỉ phép tính theo lịch đó; bot AI / MCP trả được số ngày
được phép và số ngày đã nghỉ.

Soát ngày 13/11/2026: lịch theo 4 cấp (nhân sự > phòng ban > pháp nhân > hệ thống) và tính ngày nghỉ theo lịch của người
nghỉ ĐÃ CÓ từ duoc-CR-589 (`work_schedule/resolver.py`, `leave/workday_service.py`, mọi đường lập đơn đều truyền
`employee=`). Còn thiếu:

1. Trợ lý không biết lịch làm việc của người hỏi.
2. "Đã nghỉ bao nhiêu ngày" chỉ có `used_days` của loại trừ quỹ; loại không trừ quỹ (không lương, ốm...) không tổng hợp.
3. Trợ lý không tra được phép của người khác (HR, trưởng phòng).
4. Trang phòng ban không cho thấy phòng đang áp lịch nào.

Người chủ chọn: bot tra cả người khác theo quyền; thêm tab Lịch làm việc ở trang phòng ban.

## Các pha

| Pha | Nội dung | Chủ | Trạng thái |
|---|---|---|---|
| P1 | Backend: `my_leave_summary` thêm `work_schedule` + `taken_by_type`; năm mặc định theo `vn_today()` | ai-mcp | xong (sửa theo rà mã) |
| P2 | Backend: công cụ mới `employee_leave_summary` (tra quỹ + ngày đã nghỉ của nhân sự khác, phạm vi `leave_balance.read`), khai đủ sổ công cụ | ai-mcp | xong (sửa theo rà mã) |
| P3 | Backend: `GET /api/work-schedules/tools/effective-department` (lịch hiệu lực của phòng + nguồn kế thừa + lịch sử gán cấp phòng) | ai-mcp | xong (sửa theo rà mã) |
| P4 | Giao diện: tab **Lịch làm việc** ở `/hr/departments/:id`, nút gán lịch cho phòng (điền sẵn cấp + đối tượng) | giao-dien-v2 | xong |
| P5 | Tài liệu: `03-lich-lam-viec.md`, `api.md`, cẩm nang AI, HDSD, nhật ký task | tai-lieu-kiem-thu | xong (RAG nạp lại trên dev) |

## Lượt 2 (13/11/2026, sau buổi thử trên local)

Thử trên local: lịch riêng cho phòng Kế toán và lịch riêng một người đều tính ngày nghỉ đúng. Hai chỗ thiếu: Trưởng phòng
không đổi được lịch cho nhân viên (403, quyền sửa lịch chỉ HR có, và nếu chỉ tick `work_schedule.create` thì họ sửa được
mẫu lịch + gán cấp phòng/pháp nhân/toàn hệ thống cho bất kỳ ai); Trưởng phòng hỏi bot phép của nhân viên ra rỗng (quỹ phép
bậc `own`), còn bậc `dept` của `leave_balance` thực chất là cả công ty (G6).

Người chủ chốt: (Q1) Trưởng phòng ĐƯỢC gán lịch RIÊNG cho nhân viên phòng mình, giới hạn: chỉ cấp Nhân sự, chỉ chọn mẫu HR
tạo sẵn, không sửa mẫu, không gán cấp phòng / pháp nhân / toàn hệ thống. (Q2) Trưởng phòng xem quỹ phép CHỈ người phòng
mình — siết bậc `dept` của `leave_balance` về đúng phòng rồi cấp cho vai trò Trưởng phòng.

| Pha | Nội dung | Chủ | Trạng thái |
|---|---|---|---|
| P6 | Backend: khóa quyền mới `work_schedule_personal` (gán lịch riêng cho nhân sự trong phạm vi, không cho chính mình); chốt cấp + mẫu ở `assignment_controller`; bậc `dept` của `leave_balance` lọc theo phòng của hồ sơ nhân sự; seed vai trò Trưởng phòng | backend | đang làm |
| P7 | Giao diện: nút thêm lịch riêng cho người có khóa mới, ô cấp khóa về Nhân sự, ô đối tượng chỉ người trong phạm vi | giao-dien-v2 | chưa |
| P8 | Tài liệu + HDSD + sổ việc tick tay trên prod (D-018) | tai-lieu-kiem-thu | xong (HDSD + cẩm nang nạp local; RAG nạp lại trên dev) |
| P9 | Trợ lý AI / bot / MCP TUYỆT ĐỐI không trả lương của người khác (kể cả admin, HR, giám đốc hỏi); chỉ chính nhân sự hỏi lương của mình, và chỉ trong cửa trò chuyện riêng (không trong nhóm). Rà mọi công cụ, chốt qua `employee/sensitive.mask` | ai-mcp | đang làm |

Chốt thêm 13/11/2026 (người chủ giao "xong rồi commit + push", dùng đề xuất mặc định): Trưởng phòng chỉ sửa / xóa dòng
lịch do chính mình gán, ngày hiệu lực từ hôm nay; dòng ĐÃ BẮT ĐẦU chỉ đặt được ngày kết thúc (≥ hôm qua), không xóa,
không đổi mẫu / người; dòng nối lại lịch HR giữ người tạo của dòng HR gốc; ô chọn nhân sự của Trưởng phòng chỉ liệt kê
người họ gán được. Lương qua MCP: chặn cả lương của chính mình; `my_salary` chỉ trả lương trên hồ sơ.

Người chủ chốt P9 ngày 13/11/2026: *"khi ai hỏi lương của 1 user thì bảo không được, trừ khi bản thân mình hỏi"*.

Bước bắt buộc trên dev/prod (phát hiện khi thử local): vai trò admin phải có khóa `work_schedule_personal` TRƯỚC
(`SEED_FORCE_SYNC=true` một lần hoặc script thêm dòng quyền) — không thì luật chống tự nâng quyền chặn admin tick khóa
đó cho vai trò Trưởng phòng.

## Sổ việc deploy dev / prod (P8, D-018)

Bản đủ (kèm câu SQL) ở [`../../03-lich-lam-viec.md` §21](../../03-lich-lam-viec.md); tóm tắt thứ tự:

1. Trước deploy: đếm vai trò có `leave_balance` bậc `dept` (sẽ HẸP từ cả công ty về người thuộc phòng mình) và người có ô
   **Phòng ban được xem** (`tab_user_scope`, `dim = 'department'`, `is_exclude = 0`) trên vai trò có `leave_balance.read`
   (ô đó nay mở thêm quỹ phép của phòng, cùng công ty). Báo người chủ danh sách.
2. Deploy, khởi động lại api. ERP và dịch vụ AI dựng lại CÙNG đợt (chuỗi ký cổng B đổi khuôn).
3. Cấp `work_schedule_personal` cho vai trò admin TRƯỚC (`SEED_FORCE_SYNC=true` một lần rồi trả `false`, hoặc script thêm dòng
   quyền) — không thì luật chống tự nâng quyền chặn admin tick khóa đó cho người khác.
4. Tick `dept_head`: **Nhân sự › Lịch làm việc riêng (Trưởng phòng gán)** Xem / Tạo / Sửa / Xóa bậc Phòng ban;
   **Nghỉ phép › Quỹ phép năm** Xem bậc Phòng ban; **Nghỉ phép › Đơn nghỉ phép** Xem bậc Phòng ban.
5. Chạy `seed_help_nhan_su.py`, `publish_handbook_update.py --only nghi-phep,nhan-su-ho-so`, `reindex_help_rag.py`.

## Hợp đồng API P3

`GET /api/work-schedules/tools/effective-department?department_id=<id>&on_date=<YYYY-MM-DD, mặc định hôm nay VN>`

`data` = các khóa y hệt `resolver.effective_for_employee` (`schedule_id, schedule_name, is_fallback, days[7],
weekly_workdays, level, level_label, target_name, assignment_id, effective_from, effective_to`) cộng
`department_id, department_name, company_id, assignments[]` (dòng gán CẤP PHÒNG BAN của phòng này, khuôn
`assignment_service.serialize_many`, mới nhất trước). `level` cho biết lịch đến từ đâu (mã `WorkScheduleLevel`): 3 phòng ban · 2 pháp nhân ·
1 toàn hệ thống · 0 khi `is_fallback = true` (mặc định T2–T7). Phòng dùng chung (`company_id = 0`) không có cấp pháp
nhân để kế thừa.

## Luật giữ nguyên

- Một nơi đếm ngày nghỉ: `workday_service`. Một nơi tính số còn lại: `balance_service.available_days(_map)`.
- Công cụ AI chỉ đọc, không gọi `ensure_balance`. Số truy vấn cố định, có bài đếm.
- Tra người khác đi đúng bộ lọc phạm vi của màn Quỹ phép (`leave_balance.read`), không mở rộng.
