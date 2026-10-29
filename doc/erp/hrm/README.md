# Phân hệ NHÂN SỰ (HRM): đọc ở đây trước

| | |
|---|---|
| Bản | 1.3 — 27/10/2026 (thêm `05-bao-cao-nhan-su.md`: kho mẫu báo cáo Nhân sự) · 1.2 — 26/10/2026 (§5: gỡ «In Phiếu» và «Nhân viên tự khai» đã xong ở duoc-CR-676, gỡ «luồng duyệt chỉ đọc loại chính» vì đã chốt bỏ ở duoc-CR-683) · 1.1 — 23/10/2026 (thêm `04-hop-dong-lao-dong.md`, hết bảng «chưa có tài liệu riêng» — duoc-CR-673) · 1.0 — 22/10/2026 (duoc-CR-658: gom tài liệu chức năng Nhân sự về một thư mục) |
| Dùng để làm gì | Cửa vào duy nhất cho người mới nhận việc ở phân hệ Nhân sự: đã có gì, nằm ở đâu, luật nào không được phá, việc nào đang cần người làm tiếp |
| Ai đọc | Người (hoặc trợ lý AI) sắp sửa mã hay viết tài liệu cho phân hệ Nhân sự |
| Giao diện | Chỉ có trên `frontend-v2/` (cổng 8083), menu *Nhân sự*. `frontend/` cũ đã đóng băng, không thêm màn nhân sự ở đó |

---

## 1. Đọc theo thứ tự này

1. **Tệp này**: biết bản đồ và các luật đã chốt.
2. **Tài liệu của đúng chức năng sắp đụng** (bảng §2).
3. **Tệp luật cho trợ lý AI** ở `.claude/rules/hr-*.md` (bảng §4): đây là những bẫy đã có người dẫm, ngắn hơn tài liệu chức năng nhiều.
4. Cần bối cảnh vì sao làm thế này thì mới đọc tài liệu lộ trình (§3).

## 2. Tài liệu chức năng trong thư mục này

| Tệp | Chức năng | Màn chính | Mã nguồn backend |
|---|---|---|---|
| [`01-ho-so-nhan-su.md`](01-ho-so-nhan-su.md) | **Hồ sơ nhân sự**: ~38 trường của `tab_employee`, hai bảng con (người báo tin, thành viên hộ gia đình), nhóm trường nhạy cảm (`employee_sensitive`), danh mục **Chức vụ** (§7.7), tự sửa liên hệ ở Trang cá nhân (§7.9), **Quá trình công tác** (§7.11), **Sơ đồ tổ chức** (§7.12), **việc treo trước khi khóa tài khoản** (§7.13) | `/hr/employees` · `/hr/job-positions` | `modules/employee/` |
| [`02-nghi-phep.md`](02-nghi-phep.md) | **Nghỉ phép**: đơn nghỉ (nhiều loại nghỉ trong một đơn, nửa ngày, theo giờ), quỹ phép năm và kết sổ cuối năm, loại nghỉ, lịch ngày lễ, duyệt, bốn khóa phân quyền | `/hr/leave-requests` · `/hr/leave-balances` · `/hr/leave-calendar` · `/hr/leave-types` · `/hr/holidays` | `modules/leave/` |
| [`03-lich-lam-viec.md`](03-lich-lam-viec.md) | **Lịch làm việc**: mẫu lịch tuần, gán theo bốn cấp (hệ thống, pháp nhân, phòng ban, nhân sự), xem ai làm ai nghỉ, và **nối vào cách tính số ngày nghỉ phép** | `/hr/work-roster` · `/hr/work-schedules` · `/hr/work-schedule-assignments` | `modules/work_schedule/` |
| [`04-hop-dong-lao-dong.md`](04-hop-dong-lao-dong.md) | **Hợp đồng lao động** (mẫu Word theo pháp nhân, biến mẫu, sinh tệp, ký, bản lưu trữ ở Văn bản, cảnh báo sắp hết hạn, «Hợp đồng của tôi») · **Quyền mặc định theo chức vụ** · **Nhập Excel nhân sự** | `/hr/employees/:id?tab=labor-contracts` · `/hr/labor-contract-templates` · `/hr/job-positions/:id` (tab «Quyền mặc định») · nút «Nhập Excel» ở `/hr/employees` | `modules/labor_contract/` · `modules/employee/position_role_*.py` · `modules/import_tool/employee_import*.py` |
| [`05-bao-cao-nhan-su.md`](05-bao-cao-nhan-su.md) | **Kho mẫu báo cáo Nhân sự**: 8 nhóm, 19 mẫu (3 đã có: Biến động nhân sự, Tình hình nghỉ phép, Quỹ phép năm; còn lại là đề xuất, chưa chốt), chỗ thiếu của 3 báo cáo đang chạy, phiếu khai một mẫu báo cáo | `/report` nhóm «Nhân sự» | `modules/employee/report_*.py` · `modules/leave/*report*` |
| [`06-ke-hoach-nhan-su.md`](06-ke-hoach-nhan-su.md) | **Kế hoạch nhân sự** (thiết kế 28/10/2026, chưa code): kỳ Năm / Bán niên / Quý / Tháng, định biên theo vị trí, khoản chi phí do người dùng tự định nghĩa theo mẫu, căn cứ duyệt, so với thực tế từ HĐLĐ | `/hr/headcount-plans` | `modules/headcount_plan/` |

**Hai tệp `02` và `03` dời từ `doc/tai-lieu-chuc-nang/` sang đây ngày 22/10/2026** (trước là `17-nghi-phep.md` và `21-lich-lam-viec.md`). Tệp cũ chỉ còn một dòng trỏ sang đây để các liên kết trong sổ thay đổi và kế hoạch cũ khỏi gãy. Viết tài liệu Nhân sự mới thì đặt vào thư mục này, đánh số tiếp `04`, `05`…

### Báo cáo nhân sự

Biến động nhân sự, tình hình nghỉ phép, quỹ phép năm thuộc **phân hệ Báo cáo**; tổng hợp kèm đề xuất báo cáo mới ở [`05-bao-cao-nhan-su.md`](05-bao-cao-nhan-su.md), khung báo cáo chung ở `doc/tai-lieu-chuc-nang/08-he-thong-bao-cao.md`; mã ở `modules/employee/report_*.py` và `modules/leave/*report*`. Mỗi báo cáo gác kép: quyền của phân hệ gốc và quyền xem từng báo cáo (`require_report`).

Bảng «Chức năng đã có mã nhưng chưa có tài liệu riêng» của bản 1.0 đã hết dòng: Hợp đồng lao động, Quyền mặc định theo chức vụ và Nhập Excel nhân sự nay ở `04` (23/10/2026, duoc-CR-673).

## 3. Tài liệu lộ trình và tham khảo (ở thư mục cha `doc/erp/`)

| Tệp | Đọc khi nào |
|---|---|
| [`../00-ke-hoach-theo-module.md`](../00-ke-hoach-theo-module.md) mục HRM | Kế hoạch còn lại của phân hệ Nhân sự, chia phase, cùng bộ với các phân hệ khác (thay `01`, `06`, `10`, `19` cũ đã xóa 22/10/2026) |
| [`03-cau-hoi-khao-sat-hrm.md`](03-cau-hoi-khao-sat-hrm.md) | Bộ câu hỏi phỏng vấn phòng Nhân sự |
| [`../tham-khao-hrm/`](../tham-khao-hrm/README.md) | Khảo sát phần mềm HrOnline: 59 chức năng, mỗi chức năng có danh sách trường. **Là bảng đối chiếu, không phải yêu cầu** |

## 4. Luật đã chốt, đừng phá

- **KHÔNG làm chấm công, KHÔNG làm lương / phiếu lương** (đại ca chốt 16/10/2026, cùng lúc giao duoc-CR-620). Lộ trình cũ có hai mục này, coi như đã bỏ.
- **Trạng thái, loại, cấp lưu số `SMALLINT` theo `IntEnum`** (luật R2 trong `CLAUDE.md`), chữ tiếng Việt chỉ ở tầng hiển thị. Cột `status` cũ của nhân sự là mã chuỗi tiếng Anh, là ngoại lệ lịch sử, không bắt chước.
- **Trường nhạy cảm** (CCCD, ngân hàng, lương…) chỉ trả ra khi có quyền `employee_sensitive.read`, che ở tầng serializer. Thêm trường nhạy cảm mới thì phải khai vào nhóm đó ngay.
- **Số ngày nghỉ chỉ tính ở `workday_service.count_leave_days()`** và **phải truyền `employee=`**, nếu không sẽ tính theo lịch mặc định cho người có lịch riêng mà không báo lỗi.
- **Nghỉ phép có bốn khóa phân quyền tách riêng** (`leave_request` · `leave_balance` · `leave_type` · `holiday`). Đừng gộp: ghi được `leave_balance` nghĩa là tặng ngày phép cho bất kỳ ai.
- **Biến mẫu hợp đồng lao động:** thêm / sửa / xóa phải có phạm vi «tất cả pháp nhân»; `custom_values` gán dict mới chứ không sửa tại chỗ.

Chi tiết từng luật ở các tệp luật cho trợ lý AI (tự nạp khi đụng đúng thư mục):

| Tệp | Nội dung |
|---|---|
| `.claude/rules/hr-employee-profile.md` | Hồ sơ mở rộng, `employee_sensitive`, danh mục Chức vụ, Quá trình công tác, Nhập Excel nhân sự, Quyền mặc định theo chức vụ |
| `.claude/rules/hr-leave.md` | Khóa quyền nghỉ phép, giữ chỗ quỹ, đơn nhiều loại nghỉ, duyệt ngay trong màn |
| `.claude/rules/hr-labor-contract-variables.md` | Danh mục biến mẫu HĐLĐ, `custom_values`, `json_extract`, mặc định sao lúc lập |

## 5. Việc đang mở, cần người phụ

Đối chiếu với mã nguồn ngày 22/10/2026 từ `01` §7.10, `02` §10 và các CR gần nhất.

| Việc | Chỗ ghi gốc | Tình trạng |
|---|---|---|
| **Che cột nhạy cảm khi xuất CSV / Excel** (việc C7) | `01` §7 Đợt 4 | Mã đã xong và đã rà (duoc-CR-660, HR1-1): xuất đòi quyền `export`, cột nhạy cảm để rỗng khi thiếu `employee_sensitive.read`. Đã commit 23/10/2026; lên prod phải tick lại quyền Xuất cho vai trò đang chỉ có Xem |
| **Nhập bù `hire_date`** cho hồ sơ cũ | `02` §10 | Việc dữ liệu, không phải việc mã; thiếu thì thâm niên phép tính bằng 0 và báo cáo biến động lấy ngày tạo hồ sơ thay ngày vào làm. Cách nhanh nhất: cột «Ngày vào làm» của Nhập Excel (`04` §C.3). Nên xong trước khi cấp quỹ phép năm 2027 |
| **Phiếu Quyết định đầy đủ (V1-8)**: một phiếu nhiều người, tờ trình, duyệt | `01` §4 | Mới có bản gọn ghi tay theo từng người (duoc-CR-585) |

**Vừa xong (22–26/10/2026), đã gỡ khỏi bảng trên:**

| Việc | Mã | Kết quả |
|---|---|---|
| Một đơn nghỉ khai nhiều khoảng ngày không liền kề; **bỏ** việc «luồng duyệt đọc đủ loại nghỉ» (HR3-3) | duoc-CR-683 (26/10/2026) | Nút «+ Thêm khoảng ngày», bảng con `tab_leave_request_period`, đầu đơn là bao ngoài; luồng duyệt coi mọi đơn là nghỉ phép, không rẽ nhánh theo loại (đã chốt bỏ). Chi tiết `02` §7.3, §7.1 |
| **In «Phiếu thông tin nhân viên»** theo mẫu BM00../QT01/NS (C5) | duoc-CR-676 (HR2-2, 23/10/2026) | In từ hồ sơ hoặc Trang cá nhân; khuôn dựng theo danh sách trường vì chưa có tệp mẫu gốc (thay khi có mẫu). Chi tiết `01` §7.14 |
| **Nhân viên tự khai hồ sơ** (C6) | duoc-CR-676 (HR2-2, 23/10/2026) | Bốn nhóm Cá nhân · Ngân hàng · Giấy tờ · Hộ gia đình đi qua đề nghị, phòng Nhân sự duyệt rồi mới áp; nhóm Liên hệ áp ngay. Chi tiết `01` §7.9, §7.14 |
| Tài liệu Hợp đồng lao động, quyền theo chức vụ, nhập Excel | duoc-CR-673 (HR1-5, phần tài liệu) | Tệp `04-hop-dong-lao-dong.md`; hai mục HĐLĐ cuối `01` chuyển về đó |
| Cờ «Bắt buộc đính kèm» của loại nghỉ | duoc-CR-661 (HR1-2) | Có tác dụng: đơn thiếu tệp bị chặn **lúc Gửi duyệt** (lưu nháp không chặn). Chi tiết `02` |
| Báo cáo đối chiếu trước / sau kết sổ phép cuối năm | duoc-CR-664 (HR2-3) | Hộp «Đối chiếu kết sổ phép năm …» tự mở sau kết sổ, nút mở lại, Xuất Excel. Số cũ tính lại lúc xem, không chụp ảnh. Chi tiết `02` |
| Sơ đồ tổ chức vẽ từ dữ liệu (V2-6) | duoc-CR-669 (HR2-5) | Menu Nhân sự ▸ Danh mục ▸ Sơ đồ tổ chức, lọc theo phạm vi người xem. Chi tiết `01` §7.12 |
| **Việc treo khi khóa tài khoản / cho nghỉ việc** (V0-4) | duoc-CR-665 (HR1-4) | Hộp «việc đang giữ»: chuyển từng việc / chuyển hết, còn treo vẫn khóa được sau xác nhận. Chi tiết `01` §7.13 |

Bảng trên chỉ là việc dở trong các chức năng **đã có**. Các **khối lớn chưa làm** (tuyển dụng, đánh giá, nhận việc / nghỉ việc, tài sản cấp phát, bảo hiểm…) và thứ tự đề xuất nằm ở [`../tham-khao-hrm/10-de-xuat-ap-dung.md` §0 và §0.1](../tham-khao-hrm/10-de-xuat-ap-dung.md).

Nhận việc nào thì: đặt chỗ một dòng CR ở `doc/tai-lieu-ky-thuat/change-log.md` và một mục ở `doc/tai-lieu-ky-thuat/nhat-ky-task.md` ngay khi nhận, rồi sửa dòng tương ứng ở bảng trên khi xong.

## 6. Trước khi giao

- Backend: chỉ chạy bài kiểm của phần vừa sửa, ví dụ `docker compose exec -T api python -m pytest test/backend -q -k "nghi_phep or ho_so or nhan_su or hdld or lich_lam"`. Thêm controller mới thì chạy thêm `test/backend/test_pham_vi_luat_bat_bien.py` (bài BB4 bắt controller không lọc phạm vi mà chưa khai lý do).
- Frontend v2: `npm run typecheck` và `npm run lint` cả cây, rồi `npx vitest run src/modules/hr`. Vitest **không kiểm kiểu**, nên thêm trường bắt buộc vào một kiểu dùng chung mà chỉ chạy vitest thì sẽ không thấy lỗi build.
- Sửa chức năng nào thì sửa luôn tài liệu của chức năng đó trong thư mục này, tăng số bản ở bảng đầu tệp.
