# Đối chiếu menu Nghỉ phép ERPNext (hrms) ↔ DEGO — duoc-CR-717

Ngày 03/11/2026. Nguồn ERPNext: `nexterp/hrms/hrms/hr/doctype/*`, `hr/report/*`, `workspace_sidebar/leaves.json`,
`leaves/workspace/leaves/leaves.json`. Nguồn DEGO: `backend/app/modules/leave/*` (gồm CR-715 chưa commit),
`doc/erp/hrm/02-nghi-phep.md` §5, §13, `.claude/rules/hr-leave.md`.

Ký hiệu: **Có** · **Thiếu** (làm ở CR-717) · **Hở nhỏ** (đóng trong CR-717) · **Không làm**.

| # | Mục menu ERPNext | ERPNext làm gì (mã) | DEGO hiện có | Kết luận CR-717 |
|---|---|---|---|---|
| 1 | Leave Policy | Gói tên + bảng con (loại nghỉ, `annual_allocation`); chặn vượt `max_leaves_allowed` của loại (`leave_policy.py`) | Không có gói. Hạn mức theo hình thức / cấp bậc nằm trên từng loại (`tab_leave_type_quota`) | **Thiếu** → bảng `tab_leave_policy` + `tab_leave_policy_line` (phase 01/02) |
| 2 | Leave Policy Assignment | Gán gói cho 1 người, `effective_from/to` (theo Kỳ phép hoặc ngày vào làm); chặn chồng ngày; gửi = tạo Leave Allocation từng loại, tỷ lệ theo ngày vào làm; gán hàng loạt từng người trong savepoint, báo danh sách lỗi (`leave_policy_assignment.py:57-70,111,505,523`) | Không có | **Thiếu** → `tab_leave_policy_assignment`, áp ngay vào quỹ năm nay, gán hàng loạt (phase 01/02) |
| 3 | Leave Period | Kỳ phép (from/to, công ty, is_active), chặn chồng; dùng làm mốc cho gán gói / cấp quỹ | Năm dương lịch cứng (`tab_leave_balance.year`) | **Không làm (anh Được bỏ 03/11/2026)** — quỹ vẫn theo năm dương lịch |
| 4 | Employees working on a holiday | Chấm công (trừ Vắng / Nghỉ) rơi vào ngày của Holiday List (gồm cả ngày nghỉ tuần); lọc từ–đến, Holiday List, phòng, công ty; cột NV, ngày, trạng thái, tên ngày lễ | Không có chấm công (chốt 16/10/2026). Có phiếu nghỉ bù CR-715 kiểm **ngày lễ HOẶC ngày nghỉ theo lịch** | **Thiếu** → báo cáo khóa 30 đọc phiếu nghỉ bù (phase 03/04) |
| 5 | Leave Allocation | Cấp N ngày loại X cho 1 người 1 kỳ: `new_leaves_allocated`, `carry_forward`/`unused_leaves`, `total_leaves_allocated`, link `leave_policy_assignment`, `compensatory_request`, `expired` | Dòng quỹ (người × năm × loại): `allocated` · `seniority` · `carried` · `adjusted` · `comp` · `used` · `pending` · `carried_out` · `carried_expired`; nút **Cấp quỹ năm** (cả phạm vi, mọi loại) | **Có**. Hở nhỏ: không chọn được loại / nhóm người khi cấp → hộp **Cấp quỹ** có lọc (phase 03/04) |
| 6 | Leave Control Panel | Lọc NV (công ty, hình thức, chi nhánh, phòng, chức danh, grade), chỉ lấy người chưa có quỹ, cấp N ngày một loại HOẶC gán gói | **Cấp quỹ năm** không lọc | **Hở nhỏ** → màn **Phân bổ hàng loạt** (gói) + hộp **Cấp quỹ** có lọc (loại) |
| 7 | Leave Application Dashboard | Workspace: thẻ số **đang nghỉ hôm nay / tháng này**, **ngày lễ trong tháng**, biểu đồ tròn đơn duyệt theo loại | Thẻ glance Trang chủ (`use-hr-leave-glance`), Lịch nghỉ, báo cáo **Tình hình nghỉ phép** có cơ cấu theo loại | **Có** — không làm thêm |
| 8 | Holiday List | Danh sách ngày lễ + ngày nghỉ tuần, nhiều danh sách | `tab_holiday` theo pháp nhân (0 = chung), lặp hằng năm; ngày nghỉ tuần ở Lịch làm việc | **Có** |
| 9 | Holiday List Assignment | Gán danh sách ngày lễ cho người / công ty từ ngày X | Lịch làm việc gán 4 cấp (hệ thống > pháp nhân > phòng > người) có hiệu lực từ–đến; ngày lễ theo pháp nhân | **Có** — ngày lễ riêng từng người: YAGNI, không ai yêu cầu |
| 10 | Leave Type | Cờ luật: không lương, earned (tháng/quý/nửa năm/năm), carry forward + hết hạn, cho âm, nghỉ bù, encashment, sau N ngày | Đủ các cờ dùng được (CR-715: `accrual_mode`, `applicable_after_days`, `max_negative_days`, `is_compensatory`; kết sổ 3 nước + hết hạn) | **Có** — earned theo quý/nửa năm: không làm (chưa có nhu cầu) |
| 11 | Leave Block List | Ngày cấm theo công ty / phòng, người được miễn | `tab_leave_block_period` + vai trò miễn ở Cài đặt nhân sự (CR-715) | **Có** |
| 12 | Employee Leave Balance (báo cáo) | Mỗi NV × loại trong khoảng ngày: đầu kỳ · cấp · đã nghỉ · hết hạn · cuối kỳ | Báo cáo **Quỹ phép năm** (khóa 8): được cấp, đã dùng, giữ chỗ, còn lại, cơ bản, thâm niên, chuyển sang, điều chỉnh, chuyển hết hạn | **Có**. Hở nhỏ: thiếu chỉ số riêng **Nghỉ bù cộng thêm** (`comp_days` đang lẫn trong **Được cấp**) |
| 13 | Employee Leave Balance Summary (báo cáo) | Ma trận: mỗi NV một dòng, mỗi loại nghỉ một cột = số còn lại tại ngày | Không có ma trận; báo cáo khóa 8 chỉ có **Top loại nghỉ** ở Tổng, màn Quỹ phép là mỗi (người × loại) một dòng | **Hở nhỏ** → **Tổng hợp theo người** trên màn Quỹ phép + xuất Excel |
| — | Leave Application | Đơn nghỉ, không giữ chỗ | Đơn nhiều loại + nhiều khoảng, giữ chỗ khi gửi | **Có** (DEGO tốt hơn, giữ nguyên) |
| — | Leave Encashment | Quy đổi phép ra tiền | — | **Không làm** (ngoài phạm vi: lương) |

## Hành vi ERPNext đáng chép / đáng bỏ

- Gán gói = **tự cấp quỹ** ngay (`on_submit → grant_leave_alloc_for_employee`). Chép: phân bổ xong áp ngay vào quỹ năm nay.
- ERPNext cấp **đủ `annual_allocation` cho mọi kỳ gán**, chỉ tỷ lệ theo ngày vào làm (`calculate_pro_rated_leaves`) →
  đổi gói giữa năm là được cấp thêm nguyên một quỹ mới. Không chép: DEGO chia theo tháng (DECISION D2).
- Loại nghỉ không có trong gói → ERPNext không cấp gì. DEGO đề xuất rơi về luật của loại (DECISION D1) để không ai mất quỹ
  vì gói khai thiếu.
- Gán hàng loạt: mỗi người một savepoint, lỗi một người không hỏng cả lô, cuối cùng báo danh sách thất bại. Chép nguyên.
- Chặn chồng ngày giữa hai lượt gán của cùng người. Chép, kèm tùy chọn tự đóng lượt cũ (DECISION D6).
- Báo cáo **làm ngày lễ** của ERPNext dựa chấm công; Holiday List của ERPNext **gồm cả ngày nghỉ tuần**, nên **ngày lễ** ở đó
  thực chất là **ngày không phải làm**. Phiếu nghỉ bù DEGO đã kiểm đúng điều kiện đó → nguồn tương đương (DECISION D8).

## Tín hiệu "đi làm ngày lễ" đã cân nhắc và bỏ

| Nguồn | Vì sao bỏ |
|---|---|
| Đặt xe / công tác ngày lễ | Có chuyến không chứng minh đi làm; nhiều chuyến là việc riêng được duyệt |
| Việc (task) hoàn thành ngày lễ | Bấm **xong** lúc ở nhà cũng tính → nhiễu |
| Đặt phòng họp ngày lễ | Hiếm, nhiễu |
| Lịch làm việc cá nhân có ngày lễ là ngày làm | Ngày lễ luôn thắng lịch (`count_leave_days`), không có **lịch trực** |

Giới hạn phải nói trên báo cáo: chỉ thấy người **đã lập phiếu nghỉ bù**; dữ liệu bắt đầu từ CR-715 (02/11/2026).

## Câu hỏi treo
1. Tên báo cáo: giữ đúng **Nhân viên làm việc vào ngày lễ** như ERPNext (đề xuất) hay **Làm việc vào ngày lễ, ngày nghỉ**.
