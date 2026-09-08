# HRM — HỒ SƠ NHÂN SỰ: DANH SÁCH TRƯỜNG VÀ CHỨC NĂNG

| | |
|---|---|
| Thuộc bộ | Phân hệ Nhân sự (HRM) — ERP v2 |
| Bản | 1.0 — 07/09/2026 |
| Dùng để làm gì | Chốt danh sách trường của hồ sơ nhân viên (mở rộng `tab_employee`), hai bảng con, chức năng màn hình, và phần tài khoản đăng nhập đi kèm |
| Ai đọc | Đội phần mềm, người chủ trì |
| Nguồn đối chiếu | [tham-khao-hrm/01-nhan-su.md](../tham-khao-hrm/01-nhan-su.md) (NS1, ~90 trường/7 nhóm), [tham-khao-hrm/10-de-xuat-ap-dung.md](../tham-khao-hrm/10-de-xuat-ap-dung.md) (V1-2, V1-3, V1-4), và **Phiếu thông tin nhân viên BM00../QT01/NS** (mẫu công ty đang dùng khi nhận việc, ban hành 01/06/2025) |

---

## 1. Nguyên tắc

1. **Chỉ thêm cột, không sửa cột đang có** trên `tab_employee` (quy tắc 1 của bộ ERP). Các cột hiện hữu (`code`, `full_name`, `email`, `phone`, `company_id`, `department_id`, `position`, `status`, `is_active`, `hire_date`, `gender`) giữ nguyên.
2. Trường phân loại mới lưu **SMALLINT + IntEnum**, không lưu chuỗi — theo đúng luật đang áp cho chức năng mới (phân hệ Nghỉ phép, Công việc đều đi khuôn này). `status` cũ của nhân sự đang là mã chuỗi tiếng Anh — ngoại lệ lịch sử, không đổi.
3. Lấy ~30 trường thiết yếu, **không lấy đủ 90 trường** của HrOnline. Bỏ hẳn nhóm 6 (Đảng/đoàn/quân sự). Nhu cầu lẻ tẻ sau này đi vào một cột JSON `extra_fields`.
4. **Nhóm trường nhạy cảm khai cứng ngay từ đầu** và cần quyền riêng để xem (mục 5.2). Thêm phân quyền sau khi dữ liệu đã nhập là việc đắt.
5. Mẫu phiếu BM00../QT01/NS là mẫu nhập liệu thực tế của công ty — mọi trường trên phiếu phải có chỗ chứa trong hệ thống, để sau này nhân viên khai online thay vì điền giấy.

---

## 2. Trường trên `tab_employee`

Ký hiệu: **[CÓ]** = cột đang có sẵn; **[THÊM]** = cột mới. Cột "NC" = thuộc nhóm nhạy cảm (cần quyền riêng để xem). Cột "Nguồn": HRO = tài liệu tham khảo HrOnline, PHIẾU = mẫu BM00../QT01/NS.

### Nhóm 1 — Thông tin cá nhân

| | Trường | Cột | Kiểu | NC | Nguồn |
|---|---|---|---|---|---|
| [CÓ] | Họ và tên | `full_name` | VARCHAR(255) | | |
| [CÓ] | Giới tính | `gender` | SMALLINT (0 chưa khai / 1 nam / 2 nữ) | | |
| [THÊM] | Ngày sinh | `date_of_birth` | DATE NULL | x | HRO + PHIẾU |
| [THÊM] | Nơi sinh | `place_of_birth` | VARCHAR(255) | | PHIẾU |
| [THÊM] | Dân tộc | `ethnicity` | VARCHAR(50), mặc định rỗng | | PHIẾU |
| [THÊM] | Tôn giáo | `religion` | VARCHAR(50), mặc định rỗng | | PHIẾU |
| [THÊM] | Tình trạng hôn nhân | `marital_status` | SMALLINT (0 chưa khai / 1 độc thân / 2 có gia đình / 3 ly hôn) | | HRO + PHIẾU |
| [THÊM] | Số con | `children_count` | SMALLINT, mặc định 0 | | PHIẾU |
| [THÊM] | Email cá nhân | `personal_email` | VARCHAR(255) | | PHIẾU (email trên phiếu là email cá nhân) |
| [THÊM] | MST cá nhân | `tax_code` | VARCHAR(20) | x | HRO + PHIẾU |
| [THÊM] | Trình độ học vấn | `education_level` | SMALLINT (0 chưa khai / 1 phổ thông / 2 trung cấp / 3 cao đẳng / 4 đại học / 5 sau đại học) | | HRO |
| [THÊM] | Chuyên ngành | `major` | VARCHAR(255) | | HRO |

### Nhóm 2 — Công việc

| | Trường | Cột | Kiểu | NC | Nguồn |
|---|---|---|---|---|---|
| [CÓ] | Mã nhân viên | `code` | VARCHAR(25) unique | | |
| [CÓ] | Pháp nhân | `company_id` | BIGINT | | |
| [CÓ] | Phòng ban | `department_id` | BIGINT | | |
| [CÓ] | Chức vụ (chữ) | `position` | VARCHAR(100) | | |
| [CÓ] | Trạng thái | `status` | mã chuỗi `EMPLOYEE_STATUS` (ngoại lệ lịch sử) | | |
| [CÓ] | Ngày vào làm | `hire_date` | DATE NULL — mốc thâm niên, phân hệ Nghỉ phép đang dùng | | |
| [THÊM] | **Người quản lý trực tiếp** | `manager_id` | BIGINT, trỏ `tab_employee.id`, 0 = chưa gán | | HRO (V1-3) |
| [THÊM] | Hình thức nhân viên | `employment_type` | SMALLINT (0 chưa khai / 1 full time / 2 part time / 3 thời vụ / 4 cộng tác viên / 5 thử việc / 6 thực tập) | | HRO |
| [THÊM] | Cấp bậc | `job_level` | SMALLINT (0 chưa khai / 1 nhân viên / 2 tổ trưởng / 3 phó phòng / 4 trưởng phòng / 5 giám đốc khối / 6 ban tổng giám đốc) | | HRO |
| [THÊM] | Nơi làm việc | `work_location` | VARCHAR(255) | | HRO |
| [THÊM] | Ngày nghỉ việc | `resign_date` | DATE NULL — đi cặp trạng thái nghỉ việc | | HRO |

`manager_id` không phải trường hiển thị cho đẹp: đây là dữ liệu mà **vai tương đối "người quản lý trực tiếp" của bộ máy duyệt** sẽ đọc (thêm loại approver `APPROVER_DIRECT_MANAGER` bên module `approval`, bên cạnh `APPROVER_DEPT_HEAD` đang có). Sai trường này thì đơn từ chạy sai đường một cách im lặng.

### Nhóm 3 — Liên hệ

| | Trường | Cột | Kiểu | NC | Nguồn |
|---|---|---|---|---|---|
| [CÓ] | Điện thoại di động | `phone` | VARCHAR(25) | | |
| [THÊM] | Địa chỉ thường trú | `permanent_address` | VARCHAR(500), 1 trường chữ gộp (không tách tỉnh/phường như HrOnline) | x | HRO + PHIẾU |
| [THÊM] | Địa chỉ hiện nay (tạm trú) | `current_address` | VARCHAR(500) | x | PHIẾU |

Người báo tin khẩn cấp KHÔNG nằm phẳng trên hồ sơ — phiếu công ty cho khai **nhiều người** (cha, mẹ...), mỗi người có địa chỉ riêng. Xem bảng con ở mục 3.1.

### Nhóm 4 — Ngân hàng (nhận lương)

| | Trường | Cột | Kiểu | NC | Nguồn |
|---|---|---|---|---|---|
| [THÊM] | Số tài khoản | `bank_account_no` | VARCHAR(50) | x | HRO + PHIẾU |
| [THÊM] | Tên chủ tài khoản | `bank_account_name` | VARCHAR(255) | x | HRO |
| [THÊM] | Ngân hàng | `bank_name` | VARCHAR(100) | x | HRO + PHIẾU |
| [THÊM] | Chi nhánh | `bank_branch` | VARCHAR(255) | x | HRO |

### Nhóm 5 — Giấy tờ và BHXH/BHYT

| | Trường | Cột | Kiểu | NC | Nguồn |
|---|---|---|---|---|---|
| [THÊM] | Số CCCD | `id_number` | VARCHAR(20) | x | HRO + PHIẾU |
| [THÊM] | Ngày cấp CCCD | `id_issue_date` | DATE NULL | x | HRO + PHIẾU |
| [THÊM] | Nơi cấp CCCD | `id_issue_place` | VARCHAR(255) | x | HRO + PHIẾU |
| [THÊM] | Ngày hết hạn CCCD | `id_expiry_date` | DATE NULL | x | HRO |
| [THÊM] | Ảnh CCCD mặt trước | `id_front_image` | VARCHAR(500), đường dẫn tệp | x | HRO |
| [THÊM] | Ảnh CCCD mặt sau | `id_back_image` | VARCHAR(500) | x | HRO |
| [THÊM] | Số sổ BHXH | `social_insurance_no` | VARCHAR(20) — chỉ LƯU số phục vụ hồ sơ; nghiệp vụ báo tăng/giảm BHXH nằm ngoài phạm vi (NS4 đã quyết không lấy) | x | HRO + PHIẾU |
| [THÊM] | Nơi đăng ký KCB BHYT | `health_care_place` | VARCHAR(255) — tên bệnh viện | | PHIẾU |
| [THÊM] | Mã nơi KCB BHYT | `health_care_code` | VARCHAR(20) | | PHIẾU |

Tình trạng sổ BHXH (dùng sổ cũ / cấp mới) trên phiếu KHÔNG cần cột riêng: có `social_insurance_no` nghĩa là dùng sổ cũ, rỗng nghĩa là chưa có/cấp mới.

### Nhóm 7 — Tùy biến

| | Trường | Cột | Kiểu | Nguồn |
|---|---|---|---|---|
| [THÊM] | Trường tùy biến | `extra_fields` | JSON, mặc định `{}` | HRO (nhóm 7) |

Một cột JSON duy nhất, chỉ mở cho hồ sơ nhân viên, có trần số khóa (đề xuất 20). Chứa nhu cầu lẻ: size áo, hộ chiếu, tình trạng tiêm vắc xin... KHÔNG sinh cột động kiểu `vanbanngan17_5_0` của HrOnline.

**Tổng: 11 cột đang có + 27 cột thêm + 1 JSON.** Hai trường đọc ké từ tài khoản (`avatar`, `signature` qua `tab_user`) giữ nguyên như hiện tại — một nguồn dữ liệu, không nhân bản.

---

## 3. Hai bảng con (theo phiếu BM00../QT01/NS)

### 3.1 `tab_employee_contact` — Người báo tin trong trường hợp cần thiết

Phiếu ghi rõ **bắt buộc**, và cho khai nhiều người. Toàn bảng thuộc nhóm nhạy cảm.

| Cột | Kiểu | Nghĩa |
|---|---|---|
| `employee_id` | BIGINT FK `tab_employee` | |
| `full_name` | VARCHAR(255) | Họ tên người báo tin |
| `relation` | VARCHAR(50) | Mối quan hệ (cha, mẹ, vợ/chồng...) — chữ tự do |
| `address` | VARCHAR(500) | Địa chỉ |
| `phone` | VARCHAR(25) | Điện thoại |
| `sort_order` | SMALLINT | Thứ tự hiển thị |

### 3.2 `tab_employee_family` — Thành viên hộ gia đình

Phục vụ kê khai BHXH khi ký hợp đồng chính thức (ghi chú in đậm trên phiếu). Toàn bảng thuộc nhóm nhạy cảm.

| Cột | Kiểu | Nghĩa |
|---|---|---|
| `employee_id` | BIGINT FK `tab_employee` | |
| `full_name` | VARCHAR(255) | Họ tên |
| `relation` | VARCHAR(50) | Quan hệ với chủ hộ (chủ hộ, vợ, con...) |
| `gender` | SMALLINT | Cùng quy ước với `Employee.gender` |
| `date_of_birth` | DATE NULL | |
| `phone` | VARCHAR(25) | |
| `id_number` | VARCHAR(20) | Số CCCD |
| `sort_order` | SMALLINT | |

Hai bảng đều là chi tiết của hồ sơ (không có màn danh sách riêng), sửa trong tab của màn chi tiết nhân viên. Cả hai phải khai `SCOPE_FIELDS` theo hồ sơ cha.

---

## 4. Trường KHÔNG lấy — ghi rõ để khỏi bàn lại

| Không lấy | Lý do |
|---|---|
| Nhóm 6 HrOnline (ngày vào Đảng, công đoàn, đoàn, nghĩa vụ quân sự, thương binh, liệt sĩ...) | Tài liệu tham khảo tự khuyến nghị bỏ; cần thật thì đi vào `extra_fields` |
| Cụm hộ chiếu (5 trường) | Ít người có; đi vào `extra_fields` khi cần |
| Mã chấm công, mã phân ca, 6 cờ phân quyền chấm công (GPS/wifi/máy/chấm hộ...) | Chờ quyết định C2 về chấm công; thêm bây giờ là trường chết |
| Loại HĐLĐ, ngày chấm dứt HĐLĐ | Thuộc module Hợp đồng lao động (bước sau); hồ sơ đọc ké qua quan hệ, không lưu 2 chỗ |
| Đơn vị/phòng ban/chức danh kiêm nhiệm | Để dành cho phiếu Quyết định điều chuyển/bổ nhiệm (V1-8) |
| Nguyên quán, tên thường gọi, quốc tịch, Skype, Facebook, tình trạng tiêm vắc xin | Không có nhu cầu nghiệp vụ; `extra_fields` nếu cần |
| Tách địa chỉ thành tỉnh/phường/địa chỉ (3 trường × 3 loại) | 1 trường chữ gộp là đủ; phiếu công ty cũng ghi 1 dòng |

---

## 5. Chức năng

### 5.1 Màn hình

| # | Chức năng | Mô tả |
|---|---|---|
| C1 | Danh sách nhân sự (đã có, mở rộng) | Thêm cột/lọc: hình thức nhân viên, cấp bậc, người quản lý trực tiếp. Giữ lọc theo pháp nhân, phòng ban, trạng thái |
| C2 | **Form tạo nhanh ~10 trường** | Chỉ hỏi: mã, họ tên, pháp nhân, phòng ban, chức vụ, ngày vào làm, giới tính, ngày sinh, SĐT, email. Học đúng bài "hộp tạo nhanh 12 trường" của HrOnline — bắt điền đủ 30+ trường ngay từ đầu thì không ai nhập |
| C3 | Màn chi tiết xếp tab | Tab **Chung** (nhóm 1+2) / **Liên hệ & Ngân hàng** (nhóm 3+4, kèm bảng người báo tin) / **Giấy tờ & BHXH** (nhóm 5, upload 2 ảnh CCCD, kèm bảng hộ gia đình) / **Quỹ phép** (link sang phân hệ Nghỉ phép sẵn có) / **Tài khoản** (mục 6). Sau này thêm tab Hợp đồng lao động, Lịch sử điều chuyển |
| C4 | Upload ảnh CCCD | 2 tệp ảnh, đi theo cơ chế upload tệp sẵn có, đường dẫn lưu vào 2 cột |
| C5 | In "Phiếu thông tin nhân viên" | Xuất bản in theo đúng khuôn BM00../QT01/NS từ dữ liệu đã nhập — thay thế việc điền giấy; dùng cơ chế bản in sẵn có |
| C6 | Nhân viên tự khai | Giai đoạn 2 (không làm ngay): nhân viên đăng nhập tự điền phần thông tin cá nhân của chính mình, nhân sự duyệt lại. Nền tảng scope `self` của hệ phân quyền đã đỡ được |
| C7 | Xuất CSV | Đã có xuất CSV danh sách; KHÔNG xuất các cột nhạy cảm trừ khi người xuất có quyền xem nhóm nhạy cảm |

### 5.2 Phân quyền

Hệ đang có đối tượng `employee` với `read`/`write` + phạm vi (all / company / dept / self). Giữ nguyên, thêm MỘT quyền mới:

| Quyền | Nghĩa |
|---|---|
| `employee.read` | Xem hồ sơ phần thường (nhóm 1 phần thường + nhóm 2 + KCB BHYT) — như hiện tại |
| `employee.write` | Sửa hồ sơ — như hiện tại |
| **`employee_sensitive.read`** (mới) | Xem nhóm nhạy cảm: ngày sinh, MST, số BHXH, địa chỉ, ngân hàng (4), CCCD (6), 2 bảng con. Không có quyền này thì serializer trả rỗng/che các trường đó, KHÔNG chỉ giấu trên giao diện |
| Ngoại lệ `self` | Nhân viên luôn xem được đầy đủ hồ sơ CỦA CHÍNH MÌNH (kể cả nhóm nhạy cảm), không cần `employee_sensitive.read` |

Bản đầu khai cứng danh sách trường nhạy cảm trong mã nguồn (một tuple trong module employee), chưa cần màn cấu hình. Che ở tầng serializer để API, CSV, và trợ lý AI cùng ăn một luật.

### 5.3 Việc kỹ thuật đi kèm

| # | Việc |
|---|---|
| K1 | 1 migration thêm cột `tab_employee` + tạo 2 bảng con. Nhớ nhập model mới vào `all_models.py` |
| K2 | Khai `SCOPE_FIELDS` cho `employee_contact`, `employee_family` (theo hồ sơ cha) — test đếm entity (b07) sẽ tăng từ 50 lên 52, sửa số đếm trong test |
| K3 | Thêm `APPROVER_DIRECT_MANAGER` vào `approval/flow_model.py` + nhánh suy trong `approver_resolver.py`: đọc `Employee.manager_id` của người nộp; chưa gán thì lùi về trưởng bộ phận (`APPROVER_DEPT_HEAD`) để đơn không kẹt |
| K4 | Seed quyền `employee_sensitive` trong `seed.py`/`seed_prod.py`: mặc định chỉ vai trò nhân sự và quản trị có |
| K5 | Màn danh sách cảnh báo hồ sơ thiếu `manager_id` (giống cách Quỹ phép cảnh báo thiếu `hire_date`) — vì bộ máy duyệt sẽ dựa vào trường này |

---

## 6. Phần tài khoản đăng nhập (User) — đề xuất

Hiện trạng: `tab_user.employee_id` trỏ về nhân sự; avatar + chữ ký lưu MỘT chỗ ở `tab_user`, hồ sơ đọc ké; email nhân sự đổi thì đồng bộ sang email đăng nhập (đã có cơ chế, không đụng handle admin/TESTREQ); ô "Vai trò" trên màn nhân sự đã bỏ từ CR-022 — quyền chỉ gán ở màn Phân quyền tài khoản.

Đề xuất phần làm thêm, nằm trong tab **Tài khoản** của màn chi tiết nhân viên:

| # | Chức năng | Mô tả |
|---|---|---|
| U1 | Hiện trạng thái liên kết | Nhân viên này đã có tài khoản chưa; có thì hiện handle, email đăng nhập, lần đăng nhập cuối, trạng thái khóa/mở |
| U2 | **Nút "Cấp tài khoản"** | Tạo `tab_user` gắn `employee_id`, handle đề xuất từ mã nhân viên, email đăng nhập lấy từ email công việc. Mật khẩu tạm sinh ngẫu nhiên, hiện MỘT lần cho người cấp, bắt đổi ở lần đăng nhập đầu. KHÔNG gán vai trò ở bước này — gán quyền vẫn đi qua màn Phân quyền tài khoản (giữ đúng bài học CR-022) |
| U3 | Khóa tài khoản khi nghỉ việc | Chuyển trạng thái nhân viên sang "Đã nghỉ việc" thì đề nghị khóa tài khoản kèm theo. TRƯỚC khi khóa phải chạy màn kiểm tra V0-4: người này có đang là bước duyệt của quy trình nào, đang giữ chứng từ nào chờ duyệt — hiện danh sách ra, xử lý xong mới khóa. Khóa là `is_active = False`, KHÔNG xóa |
| U4 | Đồng bộ email | Giữ cơ chế sẵn có: đổi email công việc trên hồ sơ thì cập nhật email đăng nhập (chỉ khi khớp luật đồng bộ hiện hành) |
| U5 | Một nhân viên — một tài khoản | Ràng buộc nghiệp vụ: không cấp tài khoản thứ hai cho nhân viên đã có; tài khoản mồ côi (không gắn nhân viên) chỉ dành cho tài khoản hệ thống/demo |

---

## 7. Thứ tự làm

1. **Đợt 1 — nền dữ liệu**: K1 migration + model + schema + serializer che nhạy cảm + K2 SCOPE_FIELDS + K4 seed quyền.
2. **Đợt 2 — màn hình**: C2 form tạo nhanh, C3 màn chi tiết tab, C4 upload CCCD, C1 mở rộng danh sách + K5 cảnh báo thiếu quản lý.
3. **Đợt 3 — duyệt và tài khoản**: K3 approver mới + U1/U2/U3 tab Tài khoản.
4. **Đợt 4 — tiện ích**: C5 in phiếu, C7 chặn cột nhạy cảm khi xuất. C6 (tự khai) để giai đoạn sau.

Các bước tiếp theo của phân hệ (ngoài tài liệu này): Hợp đồng lao động + cảnh báo hết hạn (V1-5), Quyết định điều chuyển/bổ nhiệm (V1-8), Sơ đồ tổ chức vẽ từ dữ liệu (V2-6).
