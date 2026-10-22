# Phân hệ NHÂN SỰ (HRM): đọc ở đây trước

| | |
|---|---|
| Bản | 1.0 — 22/10/2026 (duoc-CR-658: gom tài liệu chức năng Nhân sự về một thư mục) |
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
| [`01-ho-so-nhan-su.md`](01-ho-so-nhan-su.md) | **Hồ sơ nhân sự**: ~38 trường của `tab_employee`, hai bảng con (người báo tin, thành viên hộ gia đình), nhóm trường nhạy cảm (`employee_sensitive`), danh mục **Chức vụ** (§7.7), tự sửa liên hệ ở Trang cá nhân (§7.9), **Quá trình công tác** (§7.11). Cuối tệp có thêm hai mục của **Hợp đồng lao động**: bản lưu trữ ở phân hệ Văn bản (duoc-CR-629) và danh sách biến của mẫu hợp đồng (duoc-CR-630) | `/hr/employees` · `/hr/job-positions` | `modules/employee/` · `modules/labor_contract/` |
| [`02-nghi-phep.md`](02-nghi-phep.md) | **Nghỉ phép**: đơn nghỉ (nhiều loại nghỉ trong một đơn, nửa ngày, theo giờ), quỹ phép năm và kết sổ cuối năm, loại nghỉ, lịch ngày lễ, duyệt, bốn khóa phân quyền | `/hr/leave-requests` · `/hr/leave-balances` · `/hr/leave-calendar` · `/hr/leave-types` · `/hr/holidays` | `modules/leave/` |
| [`03-lich-lam-viec.md`](03-lich-lam-viec.md) | **Lịch làm việc**: mẫu lịch tuần, gán theo bốn cấp (hệ thống, pháp nhân, phòng ban, nhân sự), xem ai làm ai nghỉ, và **nối vào cách tính số ngày nghỉ phép** | `/hr/work-roster` · `/hr/work-schedules` · `/hr/work-schedule-assignments` | `modules/work_schedule/` |

**Hai tệp `02` và `03` dời từ `doc/tai-lieu-chuc-nang/` sang đây ngày 22/10/2026** (trước là `17-nghi-phep.md` và `21-lich-lam-viec.md`). Tệp cũ chỉ còn một dòng trỏ sang đây để các liên kết trong sổ thay đổi và kế hoạch cũ khỏi gãy. Viết tài liệu Nhân sự mới thì đặt vào thư mục này, đánh số tiếp `04`, `05`…

### Chức năng đã có mã nhưng CHƯA có tài liệu riêng

Đây là chỗ cần người viết tiếp. Mỗi dòng ghi chỗ đang giữ thông tin tạm, để người viết khỏi phải đọc lại mã từ đầu.

| Chức năng | Thông tin đang nằm ở | Ghi chú |
|---|---|---|
| **Hợp đồng lao động** (lập theo mẫu Word của từng pháp nhân, sinh tệp, tải bản ký, cảnh báo sắp hết hạn, «Hợp đồng của tôi» ở Trang cá nhân) | Cuối `01-ho-so-nhan-su.md` · `.claude/rules/hr-labor-contract-variables.md` · dòng duoc-CR-606, 620, 629, 629b, 630, 632, 633, 640, 643, 652 trong `doc/tai-lieu-ky-thuat/change-log.md` · kế hoạch `frontend-v2/plans/261005-1537-hop-dong-lao-dong-mau-theo-phap-nhan/`, `plans/261019-*-cr629`, `plans/261019-1100-bien-mau-hdld-crud-cr630`, `plans/261020-1545-hdld-cua-toi-cr652` | Nên tách thành `04-hop-dong-lao-dong.md`, rồi rút hai mục HĐLĐ ở cuối `01` về đó |
| **Quyền mặc định theo chức vụ** (mỗi chức vụ một gói vai trò, tự cấp khi tạo tài khoản hoặc đổi chức vụ) | `.claude/rules/hr-employee-profile.md` mục cuối · dòng duoc-CR-653 trong `change-log.md` · `plans/261020-1545-quyen-mac-dinh-theo-chuc-vu-cr653/` | Có thể là một mục trong `01` §7.7 (Chức vụ) |
| **Nhập Excel nhân sự** (chạy thử → ghi thật → hoàn tác, qua `import_tool`) | `.claude/rules/hr-employee-profile.md` mục «Nhập Excel nhân sự» · dòng duoc-CR-628 trong `change-log.md` · `plans/261019-0935-nhap-excel-nhan-su-cr628/` | |
| **Báo cáo nhân sự** (biến động nhân sự, tình hình nghỉ phép, quỹ phép năm) | `doc/tai-lieu-chuc-nang/08-he-thong-bao-cao.md` · `modules/employee/report_*.py` · `modules/leave/*report*` | Thuộc phân hệ Báo cáo, có gác kép theo từng báo cáo (`require_report`) |

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
| **Viết tài liệu Hợp đồng lao động** thành `04-hop-dong-lao-dong.md` | §2 tệp này | Chưa có ai nhận. Mã nguồn đã xong ~10 CR |
| **In «Phiếu thông tin nhân viên»** theo mẫu BM00../QT01/NS (việc C5) | `01` §7.10 | Chưa làm |
| **Che cột nhạy cảm khi xuất CSV / Excel** (việc C7) | `01` §7 Đợt 4 | Hiện an toàn chỉ vì bộ cột xuất chưa có trường nhạy cảm; chưa có cơ chế che. Thêm cột xuất mới là hở ngay |
| **Nhân viên tự khai hồ sơ** (việc C6) | `01` §7.9 | Mới mở nhóm Liên hệ; các nhóm còn lại chưa |
| **Cờ «Bắt buộc đính kèm» của loại nghỉ không có tác dụng** | `02` §10 | `request_service` không đọc `require_attachment` lúc gửi duyệt, nên đơn Nghỉ ốm không kèm giấy vẫn gửi được |
| **Báo cáo đối chiếu trước / sau kết sổ phép cuối năm** | `02` §10 | Hiện chỉ có câu thông báo đếm dòng |
| **Luồng duyệt chỉ đọc loại nghỉ CHÍNH** của đơn nhiều loại nghỉ | `02` §7.1 | Hạn chế đã biết, chưa có phương án |
| **Nhập bù `hire_date`** cho hồ sơ cũ | `02` §10 | Việc dữ liệu, không phải việc mã; thiếu thì thâm niên tính bằng 0 |
| **Phiếu Quyết định đầy đủ (V1-8)**: một phiếu nhiều người, tờ trình, duyệt | `01` §4 | Mới có bản gọn ghi tay theo từng người (duoc-CR-585) |
| **Sơ đồ tổ chức vẽ từ dữ liệu** (V2-6) | `01` bước kế tiếp | Chưa làm |

Bảng trên chỉ là việc dở trong các chức năng **đã có**. Các **khối lớn chưa làm** (tuyển dụng, đánh giá, nhận việc / nghỉ việc, tài sản cấp phát, bảo hiểm…) và thứ tự đề xuất nằm ở [`../tham-khao-hrm/10-de-xuat-ap-dung.md` §0 và §0.1](../tham-khao-hrm/10-de-xuat-ap-dung.md).

Nhận việc nào thì: đặt chỗ một dòng CR ở `doc/tai-lieu-ky-thuat/change-log.md` và một mục ở `doc/tai-lieu-ky-thuat/nhat-ky-task.md` ngay khi nhận, rồi sửa dòng tương ứng ở bảng trên khi xong.

## 6. Trước khi giao

- Backend: chỉ chạy bài kiểm của phần vừa sửa, ví dụ `docker compose exec -T api python -m pytest test/backend -q -k "nghi_phep or ho_so or nhan_su or hdld or lich_lam"`. Thêm controller mới thì chạy thêm `test/backend/test_pham_vi_luat_bat_bien.py` (bài BB4 bắt controller không lọc phạm vi mà chưa khai lý do).
- Frontend v2: `npm run typecheck` và `npm run lint` cả cây, rồi `npx vitest run src/modules/hr`. Vitest **không kiểm kiểu**, nên thêm trường bắt buộc vào một kiểu dùng chung mà chỉ chạy vitest thì sẽ không thấy lỗi build.
- Sửa chức năng nào thì sửa luôn tài liệu của chức năng đó trong thư mục này, tăng số bản ở bảng đầu tệp.
