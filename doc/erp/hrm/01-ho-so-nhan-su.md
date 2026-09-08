# HRM — HỒ SƠ NHÂN SỰ: DANH SÁCH TRƯỜNG VÀ CHỨC NĂNG

| | |
|---|---|
| Thuộc bộ | Phân hệ Nhân sự (HRM) — ERP v2 |
| Bản | 1.3 — 08/09/2026 (**Đợt 1 + Đợt 2 xong**; §7.7 thêm danh mục Chức vụ, đếm ngược người giữ và tab «Người đang giữ») |
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

**Tổng: 11 cột đang có + 30 cột thêm + 1 JSON.** Hai trường đọc ké từ tài khoản (`avatar`, `signature` qua `tab_user`) giữ nguyên như hiện tại — một nguồn dữ liệu, không nhân bản.

> _(đính chính 08/09/2026)_ Bản 1.0 ghi **27** là đếm hụt: cộng lại các dòng `[THÊM]` ở trên ra **30** (10 + 5 + 2 + 4 + 9). Migration `a3f8e9d62714` thêm đúng 30 cột + `extra_fields`.

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
| K2 | ~~Khai `SCOPE_FIELDS` cho `employee_contact`, `employee_family` (theo hồ sơ cha) — test đếm entity (b07) sẽ tăng từ 50 lên 52~~ **ĐÃ ĐỔI 08/09/2026 — xem §5.4.** Hai bảng con KHÔNG thành entity; ENTITIES đi từ **53 → 54** (chỉ thêm `employee_sensitive`) |
| K3 | Thêm `APPROVER_DIRECT_MANAGER` vào `approval/flow_model.py` + nhánh suy trong `approver_resolver.py`: đọc `Employee.manager_id` của người nộp; chưa gán thì lùi về trưởng bộ phận (`APPROVER_DEPT_HEAD`) để đơn không kẹt |
| K4 | Seed quyền `employee_sensitive` trong `seed.py`/`seed_prod.py`: mặc định chỉ vai trò nhân sự và quản trị có |
| K5 | Màn danh sách cảnh báo hồ sơ thiếu `manager_id` (giống cách Quỹ phép cảnh báo thiếu `hire_date`) — vì bộ máy duyệt sẽ dựa vào trường này |

### 5.4. Hai bảng con KHÔNG có khóa phân quyền riêng (đổi so với bản 1.0)

Bản 1.0 nói khai `SCOPE_FIELDS` cho `employee_contact` / `employee_family` "theo hồ sơ cha". Lúc làm mới thấy câu đó **không thực hiện được như viết**, và cố làm thì hại nhiều hơn lợi. Ba lý do, đủ để chốt:

1. **Không có cột để lọc.** Khuôn `apply_scope` lọc theo MỘT cột mỗi chiều (`company_id`, `department_id`, `created_by`…). Hai bảng con chỉ có `employee_id`. "Theo hồ sơ cha" là một phép nối, không phải một cột — `SCOPE_FIELDS` không diễn đạt được.
2. **Không có màn hình riêng.** Luật **một khóa = một màn hình** (CR-157) đặt ra đúng để tránh khóa ma. Hai bảng này sửa trong tab của màn hồ sơ; một khóa không có màn nào bật/tắt là một dòng trong ma trận phân quyền mà không ai biết tick để làm gì.
3. **D-018 biến nó thành lỗi im lặng.** Seed không ghi đè vai trò trên hệ đang chạy, nên hai khóa mới sẽ **không vai trò cũ nào có**. Kết quả: mở tab ra thấy trống, không báo lỗi, và không ai đoán ra là do thiếu quyền.

**Thay bằng:** chốt của bảng con = chốt của hồ sơ CHA, hai lớp và cả hai đều phải qua —

```
1. get_scoped(Employee, "employee", eid, ...)   → hồ sơ này có trong phạm vi mình không (404 nếu không)
2. employee_sensitive.read                       → có được xem NỘI DUNG không (403 nếu không)
```

Nên `ENTITIES` chỉ tăng **53 → 54**, không phải 56. Ghi lại trong `test_pham_vi_khai_du_b07.py`.

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

1. **Đợt 1 — nền dữ liệu**: ✅ **XONG 08/09/2026.** K1 migration + model + schema + serializer che nhạy cảm + K2 SCOPE_FIELDS + K4 seed quyền. Chi tiết ở §7.1.
2. **Đợt 2 — màn hình**: ✅ **XONG 08/09/2026.** C2 form tạo nhanh, C3 màn chi tiết tab, C4 upload CCCD, C1 mở rộng danh sách + K5 cảnh báo thiếu quản lý. Chi tiết ở §7.2.
3. **Đợt 3 — duyệt và tài khoản**: K3 approver mới + U1/U2/U3 tab Tài khoản.
4. **Đợt 4 — tiện ích**: C5 in phiếu, C7 chặn cột nhạy cảm khi xuất. C6 (tự khai) để giai đoạn sau.

Các bước tiếp theo của phân hệ (ngoài tài liệu này): Hợp đồng lao động + cảnh báo hết hạn (V1-5), Quyết định điều chuyển/bổ nhiệm (V1-8), Sơ đồ tổ chức vẽ từ dữ liệu (V2-6).

### 7.1. Đợt 1 — đã làm những gì (08/09/2026)

Migration **`a3f8e9d62714`** (30 cột + `extra_fields` + 2 bảng con). Tệp migration được **cắt tay**: `--autogenerate` trên máy local quét ra thêm một đống thay đổi của bốn phân hệ khác (bảng diễn đàn, cột phân bổ của Yêu cầu thanh toán, một loạt `NOT NULL` của mailbox/ticket/vehicle) — đó là độ lệch tích lũy giữa model và DB local, không phải việc của đợt này. **Ai chạy `--autogenerate` ở đây lần sau nhớ đọc lại file trước khi commit.**

| Tệp | Việc |
|---|---|
| `employee/constants.py` (mới) | Bốn bộ mã SỐ (hôn nhân · học vấn · hình thức · cấp bậc) theo R2/QĐ-11 + `MAX_EXTRA_FIELDS` |
| `employee/model.py` | 30 cột + `extra_fields` (JSON) + quan hệ `direct_manager` + 4 property nhãn |
| `employee/contact_model.py` (mới) | `EmployeeContact` · `EmployeeFamily`, FK `ondelete=CASCADE` |
| `employee/sensitive.py` (mới) | `SENSITIVE_FIELDS` (15 trường) + `can_read_sensitive` / `mask` / `mask_many` |
| `employee/contact_service.py` (mới) | Đọc + đặt lại một lượt hai bảng con |
| `employee/service.py` | `block_manager_cycle` (chống vòng quản lý) + dọn `manager_id` và bảng con khi xóa hồ sơ |
| `employee/controller.py` | Che nhóm nhạy cảm ở **mọi** cửa ra (kể cả cửa GHI) + 4 endpoint bảng con + upload ảnh CCCD |
| `core/permissions.py` · `core/scoping.py` | `employee_sensitive` (PUBLIC — cổng `require()` thuần) |
| `seed.py` | Vai trò mẫu **`hr_profile`** = "Nhân sự — Hồ sơ nhân viên"; `employee_sensitive` vào `_SYS_ENTITIES` |
| `frontend-v2/.../permission-types.ts` | Thêm khóa để `test_dong_bo_giao_dien_v2` khớp backend |
| `test_ho_so_nhan_su_dot1.py` (mới) | **27 ca** |

**Bảy quyết định lúc làm, không có trong bản 1.0:**

1. **Hai bảng con không thành entity** — xem §5.4.
2. **Vai trò mẫu `hr_profile`.** K4 nói "chỉ vai trò nhân sự và quản trị có", nhưng ngoài `admin` thì hệ **không có vai trò nhân sự nào** để gán — `hr_leave` là quản lý nghỉ phép, việc khác. Tách hai vì hai người khác nhau làm: người cấp quỹ phép không nhất thiết được xem CCCD.
3. ⚠️ **`employee_sensitive` phải vào `_SYS_ENTITIES`.** `_PUR_MANAGER_PERMS` là `{e: ALL for e in ENTITIES if e not in _SYS_ENTITIES}` — quên một dòng là **Quản lý thu mua đọc được CCCD + tài khoản ngân hàng của toàn công ty**, và không một dòng mã nào nói ra chuyện đó. Có test canh.
4. **Cửa GHI cũng che.** `employee.write` mà không có `employee_sensitive.read` là tổ hợp có thật (hành chính sửa số điện thoại); không che thì họ PATCH một ô vô hại rồi đọc số tài khoản ngân hàng trong chính câu trả lời.
5. **Chống vòng quản lý (`block_manager_cycle`).** `manager_id` là thứ `APPROVER_DIRECT_MANAGER` sẽ đọc. A quản lý B, B quản lý A — hai ô nhìn riêng đều hợp lý, nhưng mọi vòng dò cấp trên chạy mãi không dừng, và **nó nổ lúc ai đó nộp đơn nghỉ phép**, ở một tệp không có chữ `employee` nào. Chặn cả vòng dài (A→B→C→A).
6. **Xóa hồ sơ thì gỡ `manager_id` của cấp dưới về `0`.** Để nguyên là id trỏ vào hư không và bộ máy duyệt lùi về trưởng bộ phận **im lặng**; `0` thì màn danh sách cảnh báo được (K5).
7. **Hai ô ảnh CCCD không nằm trong `EmployeeUpdate`** — chỉ đặt qua `POST /employees/{id}/id-image/{side}`. Nhận chuỗi đường dẫn từ client là để người ta trỏ ô ảnh vào URL ngoài, rồi màn hồ sơ và bản in tải về hộ.

**Một lỗi thật đã vá trong lúc làm:** `EmployeeOut.model_validate()` ném **26 lỗi cùng lúc** với bản ghi `Employee(...)` chưa flush — `default=""` / `default=0` là mặc định lúc INSERT, không phải lúc dựng đối tượng. Triệu chứng ở chạy thật sẽ là **cả màn danh sách nhân sự trả 500** vì một ô chưa ai nhập. Vá bằng hai validator `mode="before"` trong `EmployeeBase`, cùng bài học với `_gender_none_is_unknown` của QĐ-NP3.

⚠️ **Trên hệ ĐANG CHẠY, `employee_sensitive` không tự về với vai trò cũ** (D-018 — seed không ghi đè). `admin` có ngay vì `ensure_admin_role` chạy mỗi lần khởi động và chỉ THÊM entity còn thiếu; các vai trò khác phải **tick tay ở màn Phân quyền**, hoặc đặt `SEED_FORCE_SYNC=true` một lần rồi trả về `false`.

**Còn nợ sang đợt sau:** C7 (chặn cột nhạy cảm khi xuất CSV/XLSX) — hiện **chưa cần vá**, vì bộ cột đang xuất không có trường nhạy cảm nào; phải làm ngay khi ai đó thêm cột vào `headers_map`.

### 7.2. Đợt 2 — màn hình (08/09/2026)

Toàn bộ ở `frontend-v2`. Backend chỉ đụng **một dòng**: mở `FILTERABLE` cho `employment_type` · `job_level` · `manager_id` · `company_id`.

| Tệp | Việc |
|---|---|
| `types/employee.ts` | 30 trường mới + `EmployeeContact` · `EmployeeFamily` |
| `types/employee-codes.ts` (mới) | Bốn bộ mã số gõ tay + `codeLabel` + bộ options cho ô lọc |
| `schemas/employee-schema.ts` | `employeeProfileSchema` (đầy đủ) tách khỏi `employeeSchema` (tạo nhanh) + **`pickWritableProfile`** |
| `api/employee-api.ts` | 5 cửa mới (contacts ×2 · families ×2 · id-image) + `toEmployeePayload` xử lý 5 ô ngày |
| `hooks/use-employee-profile.ts` (mới) | `useCanReadSensitive` + hook hai bảng con + upload CCCD |
| `components/employee-form-fields.tsx` (mới) | 4 helper ô nhập + `SensitiveFieldsNotice` |
| `components/employee-people-editor.tsx` (mới) | Bảng người-gắn-với-hồ-sơ, dùng chung cho CẢ HAI bảng con |
| `components/employee-id-card-uploader.tsx` (mới) | Hai ô ảnh CCCD + lightbox |
| `components/employee-tab-{general,contact,documents,leave}.tsx` (mới) | Bốn tab |
| `pages/employee-detail-page.tsx` | Dựng lại thành **5 tab**, tab nhớ ở URL (`?tab=`) |
| `pages/employee-list-page.tsx` | 3 cột mới + cảnh báo K5 |
| `components/employee-form-dialog.tsx` | +4 ô (pháp nhân · ngày vào làm · ngày sinh · giới tính), phòng ban lọc theo pháp nhân |
| `config/hr-filter-fields.ts` | 3 trường lọc mới |
| `shared/ui/date-picker.tsx` | Nhận thêm `id` để `<label htmlFor>` nối được vào |

**Bảy quyết định lúc làm:**

1. ⚠️ **`pickWritableProfile` — chốt chống MẤT DỮ LIỆU, và là thứ quan trọng nhất của đợt này.** Backend che trường nhạy cảm bằng **chuỗi rỗng**; hành chính có `employee.write` mà không có `employee_sensitive.read` mở hồ sơ ra sửa số điện thoại rồi bấm Lưu là PATCH rỗng đè lên số tài khoản ngân hàng — không ai biết cho tới kỳ trả lương. Backend **cố ý không tự chặn**: nó không phân biệt được "gửi rỗng vì bị che" với "gửi rỗng vì muốn xóa ô đó". Chỗ duy nhất biết là nơi dựng form. Danh sách 13 trường ở `SENSITIVE_PROFILE_FIELDS` phải khớp `sensitive.py`.
2. **MỘT form cho cả 4 tab đầu.** Radix hủy mount tab ẩn nhưng react-hook-form giữ giá trị trong `useForm` chứ không trong DOM, nên sửa ở tab này rồi bấm Lưu ở tab kia vẫn gửi đủ. Tách bốn form là bốn nút Lưu và bốn lần người dùng quên bấm.
3. **Hai bảng con + ảnh CCCD KHÔNG nằm trong form đó** — chúng đi cửa API riêng, gác bằng khóa quyền khác, nên có nút Lưu riêng. Ảnh CCCD lưu NGAY khi chọn, có dòng chữ nói rõ để người dùng không tưởng còn phải bấm Lưu.
4. **Hai schema tách bạch.** Gộp một thì hộp thoại tạo nhanh gửi thừa 20 ô rỗng lên backend, tức ghi đè dữ liệu người khác vừa nhập.
5. **`SensitiveFieldsNotice` là bắt buộc, không phải trang trí.** Ô bị che trông y hệt ô chưa ai nhập — không có dòng đó thì người dùng đọc hồ sơ và tin rằng công ty chưa có số tài khoản ngân hàng của người đó.
6. **Chọn pháp nhân ở form tạo thì XÓA phòng ban đang chọn.** Không làm vậy thì hồ sơ ra đời đã lệch: công ty A, phòng ban của công ty B, và không màn nào báo cho tới lúc phạm vi dữ liệu chạy sai.
7. **Ô chọn quản lý trực tiếp bỏ CHÍNH MÌNH** — backend chặn bằng 400, thà đừng bày ra để chọn.

**Hai lỗi thật đã vá trong lúc thử trên trình duyệt:**

- **Nhãn trong bảng con không nối vào ô nhập** (`<label>` trần, không `htmlFor`). Nhãn hiện ra bằng mắt nhưng trình đọc màn hình đọc ô đó là "textbox" không tên, và bấm vào chữ không nhảy được vào ô — nhân lên 5 cột × N dòng. Vá bằng `useId`, và `DatePicker` được bổ sung prop `id` để dùng chung.
- **Cảnh báo React** *"Calling setState synchronously within an effect"* ở bảng con. Thay `useEffect` bằng khuôn "điều chỉnh state khi prop đổi" — vừa hết cảnh báo vừa bỏ được một khung hình vẽ bằng dữ liệu cũ.

⚠️ **BẪY LÚC NGHIỆM THU:** người đang đăng nhập **giữ map quyền CŨ** cho tới khi đăng xuất/đăng nhập lại. Đã dính ngay lúc thử: admin có `employee_sensitive` ở API nhưng màn hình vẫn hiện «bạn không có quyền xem». Không phải lỗi của đợt này (cơ chế sẵn có), nhưng phải nói với người nghiệm thu, kẻo họ báo lỗi nhầm.

**Đã thử thật trên `localhost:8083`:** danh sách (3 cột mới + cảnh báo K5) · 5 tab · lưu tab Chung (gồm ô nhạy cảm + ô mã số) · thêm/lưu dòng hộ gia đình (tiếng Việt không mojibake) · ngoại lệ `self` · bảng con trả 403 đúng người. Test: `employee-schema.test.ts` (17 ca) + `employee-codes.test.ts` (8 ca).

### 7.3. Rà cực đoan trước khi sang Đợt 3 (duoc-CR-316, 08/09/2026)

Bắn ca cực đoan thẳng vào **MySQL thật**, không qua SQLite. Kết quả: **12 ca trả 500** «Hệ thống gặp lỗi không lường trước». Không ca nào là lỗi logic — tất cả chỉ vì tầng schema không khai giới hạn, nên **MySQL là chỗ đầu tiên phản đối**.

| # | Ca | Trước | Sau |
|---|---|---|---|
| 1 | Chuỗi dài hơn cột (22 trường, **gồm cả 4 trường CŨ** `full_name`·`email`·`phone`·`position`) | **500** | 422 «tối đa n ký tự» |
| 2 | `extra_fields` một khóa 2MB | lưu OK → mọi màn đọc hồ sơ đó đứng hình | 422 |
| 3 | `extra_fields` lồng sâu 100 tầng | **500** | 422 |
| 4 | `extra_fields` khóa dài 10 000 ký tự | lưu OK | 422 |
| 5 | `date_of_birth` năm 0001 / 9999 | lưu OK → **thâm niên hai nghìn năm** | 422 |
| 6 | `resign_date` trước `hire_date` | lưu OK | 422 |
| 7 | `PUT` 5000 dòng người báo tin | lưu OK (`sort_order` SMALLINT sẽ tràn ở dòng 32768) | 422, trần **30** |
| 8 | Họ tên bảng con 5000 ký tự | **500** | 422 |
| 9 | Chuỗi quản lý sâu hơn trần dò rồi khép vòng | **LỌT** → vòng lặp vô hạn ở bộ máy duyệt | 400 |

**Lỗi số 9 là nặng nhất và khó thấy nhất.** `block_manager_cycle` dò ngược tối đa 50 cấp rồi rơi ra khỏi vòng lặp và **trả về im lặng** — tức *"dò không thấy vòng"* bị hiểu thành *"không có vòng"*. Chuỗi dài hơn 50 cấp mà khép vòng ở cấp cuối sẽ lọt, và cái lọt đó không nổ lúc lưu hồ sơ: nó nổ lúc ai đó **nộp đơn nghỉ phép**, ở một tệp không có chữ `employee` nào. Nay chạm trần là **chặn**, kèm câu nói rõ phải đi kiểm ô nào. Đánh đổi đã ghi trong test: chặn nhầm sơ đồ sâu hơn 50 cấp — thứ không tồn tại ở doanh nghiệp thật.

**Hai giới hạn frontend lệch cột** cũng lộ ra: `code` cho 50 nhưng cột `String(25)`, `phone` cho 30 nhưng cột `String(25)` — người dùng gõ hết ô, không thấy lỗi nào, bấm Lưu mới ăn 422 tiếng Anh từ backend. Nay có test đối chiếu **23 cặp** giới hạn form ↔ độ rộng cột, lệch chiều nào cũng đỏ.

Tệp mới: `backend/app/modules/employee/field_limits.py` (bí danh `Str<n>` + dải ngày + ràng buộc `extra_fields` + trần dòng bảng con). Test: `test_ho_so_nhan_su_cuc_doan.py` (**65 ca**) + `employee-schema-stress.test.ts` (**51 ca**).

⚠️ **SQLite không ép độ dài `VARCHAR`**, nên ca tràn độ dài phải kiểm ở tầng SCHEMA. Ghi xuống DB rồi khẳng định là bài kiểm **xanh giả** — đúng lý do lỗ hổng này sống được tới hôm nay.

### 7.4. Rà cực đoan trên TRÌNH DUYỆT (duoc-CR-317, 08/09/2026)

§7.3 bắn vào API. Vòng này bấm tay trên `localhost:8083` bằng Chrome DevTools — và đó là chỗ duy nhất tìm ra được năm lỗi dưới đây, vì cả năm đều nằm ở **tương tác**, không ở dữ liệu.

| # | Lỗi | Vì sao tệ |
|---|---|---|
| 1 | Nhấn **Enter** trong ô bảng con → `PATCH` **lưu hồ sơ**, còn dòng đang gõ thì không | Toast báo «Đã cập nhật nhân sự» → **thao tác sai nhưng báo thành công** |
| 2 | Nút **Xóa** thiếu `type="button"` → bấm là form **lưu bản ghi** rồi hộp xác nhận mới mở | Bấm Hủy thì bản ghi đã lưu rồi; lịch sử có một dòng «Cập nhật» không ai làm. **Component dùng chung, lỗi có sẵn ở ~11 màn** |
| 3 | UI cho thêm **35 dòng** bảng con dù trần là 30 | Gõ hết rồi bấm Lưu mới ăn 422 **tiếng Anh**, mất trắng công gõ |
| 4 | Ô sai ở **tab đang ẩn** → bấm Lưu **không có gì xảy ra** | Không toast, không lỗi, không API. Nút Lưu đọc ra như hỏng — im lặng tuyệt đối |
| 5 | Bấm Lưu 5 lần → **5 `PATCH`** | `disabled={isPending}` là state React nên chỉ đúng ở lần render sau; bấm đúp ra 2 dòng nhật ký |

**Lỗi #4 là hậu quả trực tiếp của thiết kế 5 tab** ở §7.2: Radix hủy mount tab ẩn, nên `FormMessage` của ô sai không có chỗ nào để hiện. Vá bằng `onInvalid` + bảng `utils/profile-field-tab.ts` (trường → tab) để nhảy thẳng tới tab chứa ô đó rồi toast. Bảng đó có test **đối chiếu với chính schema**, nên thêm ô mới mà quên khai là đỏ chứ không im lặng.

**Lỗi #2 là lỗi CÓ SẴN** của `shared/ui/delete-confirm-button.tsx`, không thuộc đợt này — nhưng nó là một dòng vá và ảnh hưởng mọi màn chi tiết có form (YCMH, YCBG, ĐMH, YCTT, công ty, phòng ban…), nên vá luôn.

**Lỗi #5 là lỗ của KHUÔN CHUNG** (`disabled={mutation.isPending}` dùng khắp các màn). Ở đây vá khu trú bằng `useRef`; sửa cả khuôn là việc riêng, cần rà từng màn.

Test: `profile-field-tab.test.ts` (17 ca).

### 7.5. Ba chỉnh theo phản hồi khách (duoc-CR-318, 08/09/2026)

1. **Ô «Quan hệ» thành Ô CHỌN**, không gõ tay nữa — ở CẢ hai bảng con. Chữ tự do làm mỗi người gõ một kiểu («vợ» · «Vợ» · «v/c» · «vo») nên không lọc được, không đếm được, bản in ra không đều.
   Thành danh sách cố định thì **R2/QĐ-11 áp dụng**: cột `relation` đổi từ `VARCHAR(50)` sang **`SMALLINT`** (migration `b7c1d4e90a52`, bộ mã ở `constants.RELATION_LABELS`). Đổi ngay vì hai bảng con **chưa lên prod** — đây là lúc rẻ nhất; để có dữ liệu thật rồi mới đổi thì phải viết migration đoán ý từng chuỗi người gõ.
   Danh sách **dùng chung, không lọc theo giới tính** (khách chốt): Chủ hộ · Cha · Mẹ · Vợ · Chồng · Con trai · Con gái · Anh trai · Chị gái · Em trai · Em gái · Ông · Bà · Khác. Mã «Khác» là **99** chứ không phải 14 — chừa chỗ cho quan hệ thêm về sau, và «Khác» luôn đứng cuối.
2. **Ô «Số con» ẩn khi Tình trạng hôn nhân = Độc thân.** ⚠️ CHỈ ẩn với *Độc thân* — không ẩn với *Ly hôn* (ly hôn rồi vẫn có con) và không ẩn khi *chưa khai*. Ẩn/hiện chỉ là chuyện hiển thị, giá trị vẫn trong form và vẫn gửi lên; cố ý **không tự xóa về 0**, vì tự ý xóa dữ liệu người ta đã nhập nguy hiểm hơn nhiều so với việc giữ một con số không hiện ra.
3. **Viết lại toàn bộ chữ trên màn cho nhẹ giọng.** Bản đầu viết như ghi chú kỹ thuật: *«Số gọi khi có tai nạn lao động. Phiếu thông tin nhân viên ghi rõ BẮT BUỘC…»*, *«Chỉ để lọc và làm báo cáo cơ cấu — KHÔNG dùng để suy ra người duyệt»*, *«Đi CẶP với Tình trạng làm việc — điền ngày mà quên đổi trạng thái thì mọi màn khác vẫn coi người này đang làm»*. Đó là chữ dành cho lập trình viên, không phải cho người dùng. Nay: *«Người thân để liên hệ khi cần. Có thể khai nhiều người.»*, *«Người ký duyệt đơn từ của nhân viên này. Bỏ trống thì đơn chuyển cho trưởng bộ phận.»*, *«Điền ngày này thì nhớ đổi cả ô Tình trạng làm việc.»* Lý lẽ kỹ thuật vẫn giữ nguyên — nhưng ở **bình luận mã nguồn**, đúng chỗ của nó.

### 7.6. Ba chỉnh tiếp theo trên tab «Chung» (duoc-CR-319, 08/09/2026)

1. **Giới tính có thêm mục «Khác»** — mã **`3`**, khai ở `employee/constants.py` (`GENDER_OTHER`), bản TypeScript ở `hr/types/employee.ts`. Áp cho cả hồ sơ nhân viên lẫn dòng thành viên hộ gia đình (cùng một bộ nhãn).
   ⚠️ **`3` KHÔNG có ở bộ lọc của LOẠI NGHỈ** (`leave/constants.GENDER_LABELS` giữ nguyên 3 mục): một loại nghỉ *"chỉ dành cho giới Khác"* không định nghĩa được. Có test canh mã `3` không lọt vào bảng nhãn bên đó.
   ⚠️ Hệ quả ở nghỉ phép, **có chủ ý**: `check_gender` so `want != got`, nên người khai «Khác» **bị chặn** khỏi loại nghỉ giới hạn nam/nữ (thai sản) — khác hẳn `0` (*chưa khai* thì không chặn). Cần ngoại lệ thì Nhân sự sửa ô giới tính, đừng nới luật ở `request_service`.
   Ba bản chép của validator giới tính (Create · Update · hộ gia đình) gom về một hàm `_check_gender_value` — thêm đúng một mã đã lộ ra rằng có ba chỗ phải nhớ sửa.
2. **Ô «Số con» đổi chiều: CHỈ hiện khi «Có gia đình»** (khách chốt, thay luật ở §7.5 mục 2). Trước đó là *ẩn khi Độc thân*, tức *Ly hôn* và *chưa khai* vẫn thấy ô đó.
   ⚠️ Hệ quả phải biết: hồ sơ **Ly hôn** có sẵn số con thì **không sửa được qua màn này nữa** — con số cũ vẫn nguyên trong DB và vẫn được gửi lên khi lưu (ẩn/hiện vẫn chỉ là chuyện hiển thị, không tự xóa về 0), muốn sửa thì đổi ô hôn nhân trước. Hằng số đổi từ `MARITAL_SINGLE` sang **`MARITAL_MARRIED`**, test đổi theo.
3. **Xếp lại thứ tự ô của khối «Thông tin cá nhân»** — cũ là *…Tôn giáo | Tình trạng hôn nhân · Số con | Email…*, nên «Số con» rơi xuống **nửa hàng bên trái, dưới «Tôn giáo»**, đứng rời khỏi ô hôn nhân sinh ra nó. Nay xếp theo nhóm nghĩa, mỗi hàng một cặp đi với nhau: *Mã NV | Họ tên* · *Giới tính | Ngày sinh* · *Nơi sinh (cả hàng — thực tế nhập nguyên một địa chỉ)* · *Dân tộc | Tôn giáo* · *Tình trạng hôn nhân | Số con* · *Trình độ học vấn | Chuyên ngành* · *Mã số thuế | Email cá nhân*.
   ⚠️ Ô ẩn được thì phải **chừa chỗ trống**: lưới 2 cột xếp ô lần lượt, nên bỏ hẳn một ô là mọi cặp phía dưới lệch sang nửa hàng bên kia — chính là lỗi bố cục đang phải sửa ở đây. «Số con» khi ẩn được thay bằng một ô rỗng `aria-hidden`.

### 7.7. Danh mục CHỨC VỤ (duoc-CR-320, 08/09/2026)

Khách chốt: ô «Vị trí / Chức vụ» phải **lấy từ một danh mục quản lý được**, không gõ tay nữa. Trước đợt này nó là chữ tự do, nên cùng một chức vụ hiện ra bốn cách viết («Trưởng phòng» · «TP.» · «truong phong» · «Trưởng Phòng ») trên **bản in phiếu, tệp Excel xuất ra và hồ sơ mà trợ lý AI đọc** — ba nơi khách nhìn thấy.

**Bảng mới `tab_job_position`** (`employee/position_model.py`): mã · tên · đang dùng · thứ tự · ghi chú · phòng ban thường giữ. Màn hình `/hr/job-positions` dựng bằng khung CRUD khai báo. ⚠️ **Hai cột cuối cùng KHÔNG lên giao diện** — xem mục *Giao diện* bên dưới; chúng còn dưới DB nhưng người dùng không thấy, đừng lấy danh sách cột này làm danh sách ô nhập.
⚠️ Đây là **DANH MỤC, không phải bộ mã** — R2/QĐ-11 không áp: người dùng tự thêm bớt trên giao diện, như phòng ban hay phòng họp. Cũng **khác `job_level` (Cấp bậc)**: cấp bậc là thang bậc cố định bảy mức khai trong mã nguồn, chức vụ là chức danh cụ thể in trên phiếu.

**Khóa quyền mới `job_position`** (ENTITIES **54 → 55**, PUBLIC ở `SCOPE_FIELDS`). Seed cấp `read` cho **mọi** vai trò — thiếu nó thì ô chọn chức vụ rỗng sạch và người dùng đọc ra "công ty chưa khai chức vụ nào" trong khi thứ họ gặp là một 403 bị nuốt. Quyền SỬA nằm ở vai trò `hr_profile`.
⚠️ Trên hệ ĐANG CHẠY, vai trò cũ **không tự có** khóa này (D-018): tick ở màn Phân quyền, hoặc `SEED_FORCE_SYNC=true` một lần.

**HAI CỘT CHO MỘT SỰ THẬT — đọc kỹ trước khi sửa.** `tab_employee.position_id` là khóa (sự thật), `tab_employee.position` là **nhãn đã chép**. Giữ cột chữ vì mười chỗ đang đọc thẳng nó (`purchase_request/service.py`, `survey_request/service.py`, `core/audit.py`, `export_log/registry.py`, `assistant/service.py`…) và vì hồ sơ cũ chưa map phải giữ nguyên chữ người ta đã gõ. Cái giá là nhãn **trôi** nếu không ai đồng bộ, nên toàn hệ chỉ có **đúng hai đường ghi** vào `position`, cả hai trong `position_service.py`:

1. `sync_label` — lưu hồ sơ có đụng `position_id`;
2. `propagate_rename` — đổi tên một dòng danh mục → chép tên mới sang **mọi** hồ sơ đang giữ.

⚠️ Thiếu (2) thì sửa lỗi chính tả trong danh mục xong, màn hình hiện tên mới (nó đọc theo id) còn **bản in đưa cho khách vẫn ra tên cũ** — sai lệch lộ ra ở tờ giấy, muộn nhất có thể. Thêm một đường ghi thứ ba ở chỗ khác là mở lại đúng mớ dữ liệu đợt này đang dọn.

**Bốn chốt, và lý do từng cái:**

- **Không xóa chức vụ đang có người giữ** (`before_delete`) — xóa là để lại hồ sơ trỏ vào id không tồn tại: ô chọn hiện trống còn cột nhãn vẫn giữ chữ cũ, hai chỗ nói hai điều khác nhau về một người. Muốn dẹp thì bỏ tick «Đang dùng».
- **Không gán id chết** — cột không có khóa ngoại cứng (cùng quy ước `department_id` / `manager_id`), không kiểm ở tầng dịch vụ thì `position_id = 99999` ghi xuống êm ru.
- **Không gán MỚI chức vụ đã ngừng dùng**, nhưng ⚠️ **hồ sơ đang giữ nó vẫn lưu được**: màn hồ sơ gửi lại mọi ô mỗi lần lưu, nên không có ngoại lệ này thì người đó **không sửa nổi ô nào khác** cho tới khi ai đó đi đổi chức vụ của họ.
- **Mã không sửa được sau khi tạo** — mã đi vào tệp CSV đã phát ra ngoài.

⚠️ **Luật "khóa = 0 thì xóa nhãn" CHỈ đúng ở đường CẬP NHẬT** (người dùng vừa bỏ chọn). Áp cả vào lúc TẠO thì đường nhập CSV, seed và mã cũ — những nơi chỉ truyền `position` chữ — làm hồ sơ **mất chức danh ngay khi ra đời**, im lặng. Lỗi thật đã dính khi làm đợt này; `test_employee_position.py` bắt được.

**Migration `c5e2a8b31d47`** tạo bảng, thêm cột, và **nạp lại dữ liệu cũ**: gom các giá trị `position` phân biệt (bỏ khoảng trắng thừa, **không phân biệt hoa thường**) thành dòng danh mục rồi trỏ `position_id` của từng hồ sơ vào. Chạy thật trên MySQL local: 13 chức vụ dựng từ dữ liệu đang có, không hồ sơ nào mồ côi. ⚠️ Gom bỏ qua hoa thường là có chủ ý — dữ liệu thật có «Trưởng phòng» và «Trưởng Phòng» của cùng một chức vụ, gom phân biệt thì ô chọn hiện hai dòng trông giống hệt nhau và không ai bấm đúng được cái nào.

**Nhập CSV** khớp tên vào danh mục (bỏ qua hoa thường / khoảng trắng thừa), không khớp thì **giữ chữ, `position_id = 0`** — cố ý **không tự tạo** dòng danh mục mới, vì tự tạo thì mỗi lỗi gõ trong một tệp CSV đẻ ra một chức vụ và danh mục vừa dọn lại đầy rác.

**Bộ lọc** danh sách nhân sự đổi từ ô chữ sang ô chọn theo **`position_id`**: lọc bằng chữ thì đổi tên một chức vụ là mọi bộ lọc đã lưu trượt sạch, và `contains` còn khớp chuỗi con («Phó phòng» lọt vào kết quả tìm «Trưởng phòng»). Cột trong bảng vẫn đọc nhãn — một câu truy vấn là đủ.

Test: `test_danh_muc_chuc_vu.py` (**20 ca**) + sửa số đếm entity ở `test_pham_vi_khai_du_b07.py` (54→55) và `test_pham_vi_luat_bat_bien.py` (BB3 + BB4).

**Giao diện — bỏ hai ô, dời nút Thêm sang trang riêng** (08/09/2026, sau khi khách bấm thử).

- **Bỏ cột + ô «Thứ tự hiển thị».** Người dùng cuối không có khái niệm đó: bảng hiện một cột toàn 10·20·130 mà không chỗ nào nói số ấy nghĩa gì. Nặng hơn, `hint` cũ hứa *"số nhỏ lên trước trong ô chọn"* — **lời hứa sai**, vì `make_crud_router` mặc định sắp theo `id desc` và chưa từng có ai sắp theo cột này. Nay ô chọn sắp theo **TÊN** (`sort_by=name` khai thẳng trong `use-job-positions.ts` và trong ô lọc ở `hr-filter-fields.ts`) — bỏ trống thì danh sách đổ ra theo thứ tự người ta gõ vào và **tự đổi chỗ mỗi lần có ai thêm một dòng**. Cột `sort_order` giữ nguyên dưới DB, migration vẫn nạp số.
- **Bỏ ô «Phòng ban thường giữ».** Nó không chặn gì cả — gán chức vụ đó cho người phòng khác vẫn được, và chính `hint` của nó phải thú nhận điều ấy. Một ô bắt chọn rồi tự nói chọn xong cũng chẳng để làm gì thì thà đừng hỏi. Cột `department_id` giữ nguyên dưới DB và vẫn lọc được qua API.
- **Nút «Thêm chức vụ» mở TRANG RIÊNG** `/hr/job-positions/new` (`CrudConfig.createRoute`, cùng khuôn với Loại nghỉ · Phòng họp · Ngày lễ · Xe · Tài xế) thay cho hộp thoại. Không phải vì form dài — còn 4 ô — mà vì mỗi ô kéo theo một hệ quả phải đọc TRƯỚC khi gõ: mã không sửa lại được, còn đổi tên là đổi luôn chức danh in trên phiếu của mọi người đang giữ. Hộp thoại buộc cắt ngắn những câu đó cho vừa khung.
- **Tên đứng trước Mã** trong form: tên là thứ người khai đang nghĩ tới, mã thì bỏ trống được vì hệ thống tự sinh. Bắt gõ mã trước là chặn người ta ngay ở ô lẽ ra được phép bỏ qua.

**Đếm ngược người giữ + cụm ảnh xếp chồng** (duoc-CR-322, 08/09/2026). Câu hỏi thật của người quản lý danh mục trước khi sửa hay dẹp một chức vụ là *ai đang mang chức danh này* — không có nó thì việc duy nhất làm được là bấm Xóa rồi đọc câu từ chối.

`GET /api/job-positions/stats` trả `{position_id, total, departments[{id, name, count}], holders}`. Hai truy vấn cho **cả bảng**: một `GROUP BY (position_id, department_id)` để đếm, một `outerjoin` sang `tab_user` + `tab_file` để lấy vài gương mặt.

- ⚠️ **Tách endpoint riêng, không thêm `employee_count` vào `JobPositionResponse`** — serializer chạy cho từng dòng nên đếm ở đó là một truy vấn mỗi dòng, và nó chạy cả ở những chỗ chỉ cần tên chức vụ.
- ⚠️ **`Employee.avatar` và `User.avatar` đều là `@property`, không phải cột.** Đưa vào `with_entities` là `ArgumentError` ngay lúc chạy (đã dính). Ảnh thật nằm ở `tab_file`, nối qua `tab_user.avatar_file_id`, và phải dựng lại đúng thứ tự ưu tiên `thumb_url or url` mà property kia đang dùng.
- ⚠️ **Số bày cho người xem thì LỌC theo phạm vi dữ liệu** (`apply_scope` trên entity `employee`); **chốt chặn xóa thì KHÔNG** — đó là toàn vẹn dữ liệu, lọc theo phạm vi thì người chỉ thấy phòng mình xóa được chức vụ mà phòng khác đang giữ. Hai số lệch nhau được, nên câu chặn xóa nói rõ **«trên toàn công ty»**.
- ⚠️ **Thiếu `employee.read` thì backend không ném 403** — nó lọc rồi trả rỗng. Giao diện phải tự tắt cột (`enabled: can(...)`), không thì mọi dòng hiện 0 và người đọc kết luận "chưa ai giữ chức vụ nào". Dấu «—» nói *không có thông tin*, chữ «Chưa ai giữ» nói *không có người*.
- ⚠️ **«+N» tính từ `total`, không từ `holders.length`** — backend chỉ gửi 6 gương mặt mẫu; lấy độ dài mảng làm tổng thì chức vụ 40 người hiện ra «+2».
- ⚠️ **Đè ảnh nông lại `-space-x-1`** (mặc định của `AvatarGroup` là `-space-x-2`): vòng `size-6` đè 8px thì chỉ còn 16px lộ ra, **không đủ cho hai chữ viết tắt** — cả cụm đọc thành một vệt chữ dính nhau. Ảnh thật đè sâu vẫn đẹp, nhưng phần lớn hồ sơ **chưa có ảnh** (phải được cấp tài khoản mới có) nên chữ viết tắt là trường hợp thường gặp. Nền `bg-primary/10` vì viền của `AvatarGroup` là `ring-background`, tức trắng trên nền hàng trắng.
- ⚠️ **Cột «Phòng ban đang giữ» xếp ảnh của PHÒNG BAN, không phải của người trong phòng** (sửa 08/09/2026, khách bấm thử). Bản đầu xếp gương mặt từng nhân viên theo phòng, và trên cùng một dòng nó **lặp lại đúng nhóm mặt của cột «Đang giữ» ngay bên cạnh** — hai cột nói cùng một điều, còn câu hỏi riêng của cột này (*phòng nào*) thì mất. Nay mỗi phòng là một vòng tròn mang chữ viết tắt tên phòng; tên đầy đủ ở `title` và ở tab «Người đang giữ». Kéo theo: `departments[].holders` bỏ khỏi API và `list_holder_faces` gom lại theo chức vụ (bản tách theo cặp *chức vụ × phòng ban* không còn ai đọc).
- ⚠️ **Tab «Người đang giữ» phân trang THẬT** (sửa 08/09/2026). Bản đầu lấy 200 dòng một lượt rồi chỉ ghi một dòng chú thích khi vượt — nghĩa là chức vụ đông người thì phần đuôi **không xem được từ màn này**, phải sang màn Nhân sự lọc lại từ đầu; mà «Nhân viên» là chức vụ cả công ty cùng mang. Thanh công cụ của bảng có **ô tìm kiếm** (quét đồng thời mã NV · họ tên · email · SĐT qua `apply_keyword_search`, hoãn 350ms) + **ô lọc phòng ban** + **ô lọc tình trạng làm việc**, tất cả gom chung MỘT thẻ với bảng. Bản chip-một-thẻ-riêng đã bỏ: nó chiếm nguyên một khối chỉ để nói con số mà chân bảng đã nói, và dãy chip dài ra theo số phòng ban. ⚠️ Ô lọc tình trạng phải gửi **MÃ** chứ không phải nhãn — cột `status` lưu mã chuỗi (B-03); gửi nhãn thì backend vẫn nhận câu lọc, chỉ là trả về 0 dòng mà không báo lỗi gì (đúng bẫy CR-118). ⚠️ Câu «bảng rỗng» phải phân biệt *rỗng vì bộ lọc* với *rỗng vì thật sự chưa ai giữ*: một câu chung cho cả hai thì người vừa gõ nhầm một chữ đọc ra «chức vụ này chưa ai giữ» và tin là vậy.
- ⚠️ Sentinel «mọi phòng ban» của ô lọc đó là **`-1`, không phải `0`** — nhóm giả «(Chưa gắn phòng ban)» mang đúng `id = 0`, lấy `0` làm «tất cả» thì chọn chính nhóm đó lại ra toàn bộ, và hồ sơ chưa gắn phòng thành thứ duy nhất không lọc ra được. Đổi **bất kỳ** bộ lọc nào cũng phải kéo trang về 1, nếu không đang đứng ở trang 4 mà lọc còn 3 người thì backend trả rỗng và người đọc hiểu là «phòng này không có ai». Dùng `usePageResetOnFilterChange` chứ không `useEffect(() => setPage(1), [...])`: effect chạy SAU khi commit nên lượt render đầu vẫn gọi API với số trang cũ — một request thừa vào trang không còn tồn tại; ESLint cũng chặn `setState` trong effect. Và theo dõi giá trị tìm kiếm **đã hoãn**, không theo ô nhập thô — theo ô nhập thì mỗi ký tự gõ ra một lần đặt lại trang, kể cả khi truy vấn chưa hề đổi.
- Trang chi tiết chạy **hết bề ngang** (`detailMaxWidth: 'max-w-none'`, cùng khuôn Sản phẩm · Nhà cung cấp · Phòng họp) — bó ở mức mặc định `max-w-5xl` thì bảng 4 cột nằm giữa hai khoảng trắng rộng bằng chính nó.
- ⚠️ **Chữ viết tắt tên phòng lấy hai từ ĐẦU**, ngược với tên người (`nameInitials` lấy hai từ cuối) — và đó không phải bất nhất: tên người Việt xếp họ trước nên phần phân biệt nằm ở cuối, còn tên phòng đọc xuôi nên phần phân biệt nằm ngay đầu. Lấy hai từ cuối thì «Công nghệ thông tin» ra «TT», trùng với «Truyền thông». Cũng bỏ tiền tố *Phòng / Ban / Bộ phận…* trước khi viết tắt, không thì vòng tròn nào cũng bắt đầu bằng «P». Xem `shared/utils/name-initials.ts`.
- **Bộ lọc nâng cao** (`filterConfig`: tên · mã · ghi chú · trạng thái). ⚠️ Mọi `name` phải nằm trong `filterable=[...]` của controller — tên ngoài danh sách bị `apply_filters` **bỏ qua trong im lặng**: người dùng đặt điều kiện, bấm Áp dụng, và nhận về nguyên danh sách cũ mà không có lỗi nào để lần.
- `authorInitials` của diễn đàn dời lên `shared/utils/name-initials.ts` (6 tệp forum đổi import). Lấy hai chữ **cuối** vì họ người Việt đứng trước — "NV" trùng nhau ở nửa danh bạ công ty.
- Bài kiểm bất biến **BB4 bắt được một việc thật**: `employee/position_controller.py` nay gọi `apply_scope`, nên phải rút tên nó khỏi danh sách miễn trừ.

**Tài liệu cho trợ lý AI** (08/09/2026). Chia đôi theo đúng luật của
`assistant/packs/README.md` — gói giữ **luật**, Help Center giữ **các bước bấm nút**:

| Nơi | Nội dung | Vì sao ở đó |
|---|---|---|
| `assistant/packs/60-nhan-su-ho-so.md` (~1 260 token) | Luật trợ lý **không được nói sai** + nhóm trường cấm đọc | Gói đi vào **mọi** câu hỏi, kể cả câu chẳng liên quan — nên chỉ nhét thứ mà nói sai là người dùng làm hỏng dữ liệu thật |
| Bài HDSD *«Chức vụ & Hồ sơ nhân sự»* (`tab_help_article` id 139) | Các bước thêm · sửa tên · dẹp · nhập CSV · vì sao có ô không xem được | Chỉ nạp khi đúng chủ đề, qua `search_docs` |

⚠️ Hai điều **chưa xong**, không phải sót:
- **Chưa lập chỉ mục RAG cho bài đó.** `qdrant-client==1.12.1` có trong `requirements.txt` nhưng **chưa cài trong image `api` đang chạy** (image cũ hơn tệp requirements), nên `indexer.reindex_source` ném `ModuleNotFoundError`. Phải `docker compose up --build api` rồi gọi `POST /api/assistant/rag/reindex`. Trước khi làm việc đó, trợ lý **không** tra ra bài này bằng `search_docs` — nó chỉ biết phần luật trong gói.
- **Bài HDSD mới chỉ nằm ở DB local.** Đưa sang dev-UAT/prod bằng cặp `scripts/hdsd_dump.py` → `hdsd_load.py` có sẵn, không cần viết script mới.

⚠️ Trợ lý đọc hồ sơ nhân sự **chỉ 5 trường** của chính người hỏi (`assistant/service.py`, hàm dựng chân dung: họ tên · mã NV · **chức vụ** · phòng ban · công ty) và `full_name` của người duyệt. Không trường nhạy cảm nào, nên đường này không cần `sensitive.mask` — nhưng **thêm trường vào chân dung người hỏi thì phải kiểm lại đúng chỗ đó**. Lưu ý ô «chức vụ» nó đọc là `emp.position`, tức **nhãn đã chép**, không phải khóa.

