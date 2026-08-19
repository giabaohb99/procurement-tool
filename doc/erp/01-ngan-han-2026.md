# NGẮN HẠN — DANH SÁCH CÔNG VIỆC ĐẾN 31/12/2026

| | |
|---|---|
| Bản | **1.5 — 12/08/2026** (bản 1.4, 1.3, 1.2 cùng ngày, bản 1.1 ngày 11/08/2026, bản 1.0 ngày 10/08/2026) |
| Đối tượng đọc | Đội phần mềm · Gia Bảo · Được |
| Trả lời câu hỏi | Từ nay đến cuối năm làm những việc gì, theo thứ tự nào |
| Chưa có trong bản này | Số người, số người-ngày, ngày giao cam kết |
| Liên quan | [`02` Dài hạn](./02-dai-han.md) · [`03` Câu hỏi khảo sát HRM](./03-cau-hoi-khao-sat-hrm.md) · [`04` Danh mục chờ quyết](./04-danh-muc-cho.md) · **[`06` Lộ trình nền tảng và HRM](./06-lo-trinh-nen-tang-va-hrm.md)** · **[`07` Kiến trúc vỏ ERP](./07-kien-truc-vo-erp.md)** · **[`08` Danh sách task củng cố code base](./08-danh-sach-task-cung-co.md)** |
| Bắt tay vào làm thì mở tệp nào | Tệp này cho **thứ tự theo lịch**; [`08`](./08-danh-sach-task-cung-co.md) cho **điều kiện cần và điều kiện đủ của từng task củng cố**, kiểm chứng lại được |

**Bản 1.1 sửa bốn chỗ**, sau khi [`06`](./06-lo-trinh-nen-tang-va-hrm.md) đọc lại mã nguồn ngày 11/08/2026 và có số liệu đếm được:

| # | Chỗ sửa | Bản 1.0 | Bản 1.1 |
|---|---|---|---|
| 1 | Bộ máy duyệt dùng chung | Là **một dòng HR7 nằm trong bước 4 (HRM)**, làm ở nửa đầu T11 | Tách thành **bước 3b riêng, làm trước HRM**, sáu việc DUY1–DUY6. Nó không phải việc của HRM — nó là phần nền mà HRM đứng lên trên |
| 2 | Điều kiện chặn trước HRM | Chỉ có PQ4 + PQ5 (vá lỗ hổng phạm vi) | Thêm **PQ9 thu hồi token** và **PQ10 bộ đệm quyền dùng chung**. Khóa một tài khoản hiện chưa có hiệu lực thật, và sửa quyền chỉ tác dụng ở một trong hai tiến trình |
| 3 | Đa pháp nhân | Chỉ có DB4 (quy tắc công ty) và DB5 (cột công ty cho kho) | Thêm **DB10–DB13**. 17 trên 31 bảng chưa có cột pháp nhân *(con số này **sai**, xem dòng 15 bên dưới — thật ra là 42/57)*; chưa có đánh số chứng từ theo pháp nhân; chưa trả lời một người làm nhiều pháp nhân thì mấy hồ sơ |
| 4 | Vị trí của webhook | Xếp cuối, nửa đầu T12 | **Không chặn HRM nên chạy song song được.** Giữ nguyên nội dung WH1–WH11, chỉ bỏ ràng buộc phải đợi tới cuối |

**Bản 1.2 thêm hai nhóm việc**, sau khi [`06`](./06-lo-trinh-nen-tang-va-hrm.md) bản 2.0 đo mức lặp trong mã nguồn ngày 12/08/2026:

| # | Thêm gì | Vì sao |
|---|---|---|
| 5 | **DB14** — sinh tệp enum của giao diện từ máy chủ, CI so sánh hai đầu | Bản 1.1 viết "giao diện lấy qua API". Đánh giá lại thì không đáng: trạng thái đổi vài lần một năm, mà mỗi lần đổi đằng nào cũng phải sửa giao diện. Sinh tệp thì vừa giữ được kiểm tra kiểu lúc viết mã, vừa không lệch được |
| 6 | **LC1–LC5** — lớp dùng chung cho tầng nghiệp vụ (mục 4.2 mới) *(bản 1.5 thêm **LC6**)* | Đo được: 247 chỗ ném lỗi thô *(đếm lại 12/08 được **259**)*, 92 chỗ ghi nhật ký tay, **38 chỗ áp phạm vi tay**, 25 endpoint danh sách chép cùng khuôn, bộ sinh router chung chỉ 1 trên 33 module dùng *(đếm lại: **1 trên 36**)*. HRM sẽ sinh hơn mười module mới — gom trước thì mười module đó được lợi, gom sau thì phải đi dọn lại |

**Bản 1.3 sửa ba chỗ ở bước 2**, gộp về từ [`07`](./07-kien-truc-vo-erp.md) — bản kiến trúc chi tiết viết ngày 12/08/2026 sau khi đọc lại mã nguồn giao diện:

| # | Chỗ sửa | Bản 1.2 | Bản 1.3 |
|---|---|---|---|
| 7 | **FE5 tiền tố đường dẫn** | Đổi hết đường dẫn Thu mua sang `/thu-mua/...`, tuyến bắt-tất-cả thành `:module/:entity` | **Chỉ phân hệ mới có tiền tố.** Thu mua giữ nguyên đường dẫn vĩnh viễn. Lý do đo được: `notification.link` là cột `String(500)` đang chứa hàng nghìn đường dẫn thật của thông báo đã gửi |
| 8 | **FE6 chuyển hướng link cũ** | Một việc riêng phải làm | Không đổi thì không phải chuyển hướng. Thu lại thành một phép thử: mở link cũ lấy từ dữ liệu thật vẫn vào đúng chỗ |
| 9 | **FE7 tách `cruds.tsx`** | Nằm trong bước 2 | Không phải điều kiện của vỏ, đẩy tới khi thêm phân hệ thứ hai — lúc đó mới biết cắt theo đường nào |

Kèm **ba mã việc mới FE13, FE14, FE15**, và sửa số entity từ 29 thành **28** (đếm lại ở `core/permissions.py` ngày 12/08/2026).

**Bản 1.4 gộp về từ [`06`](./06-lo-trinh-nen-tang-va-hrm.md) bản 2.1** — bản đếm lại toàn bộ số liệu theo **bảng** thay vì theo tệp model, cộng bốn quyết định người chủ trì chốt ngày 12/08/2026:

| # | Chỗ sửa | Bản 1.3 | Bản 1.4 |
|---|---|---|---|
| 10 | **Lỗ hổng phạm vi** | Xếp trong PQ4, PQ5 — làm ở nửa sau T10 | **Đang hở thật, không phải rủi ro tương lai.** Tách phần vá gấp thành **PQ11** làm ngay ở nửa sau T8: `GET /api/employees/{id}` và **cả 11 endpoint xuất/nhập tệp** không gọi `apply_scope`, dù `employee` đã khai đủ phạm vi |
| 11 | **Quyền và nhật ký khi xuất dữ liệu** | Một câu phụ trong LC4 | Thành yêu cầu bắt buộc trong **PQ11**: kiểm quyền `export` ở cả 11 endpoint (hiện chỉ **1/11** kiểm), và **ghi một dòng nhật ký cho mỗi lần xuất**. Chốt Đ9 ở [`04`](./04-danh-muc-cho.md) |
| 12 | **Phân quyền mức trường** | Không có mã việc nào | Thành **PQ12**. Hệ hiện tại chỉ biết "được đọc loại dữ liệu này" hay "không", không có mức "đọc được hồ sơ nhưng không thấy cột lương". **Chặn HR3.** Chốt Đ10 |
| 13 | **Phạm vi phòng ban** | Không nhắc | Thành **DB15**. `apply_scope` đang lọc phòng ban bằng **so bằng chuỗi tiếng Việt** — đổi tên một phòng là chứng từ cũ rơi khỏi phạm vi, im lặng. Chuyển sang `dept_id`. Chốt Đ8 |
| 14 | **Cây phòng ban nhiều cấp** | Nằm trong HR1, HR5 và điều kiện vào của bước 3b | **Bỏ khỏi năm nay.** Chốt Đ7 — không phải để tiết kiệm công, mà vì cây thật buộc "phạm vi phòng ban" đổi nghĩa thành "phòng mình và các phòng con", khiến trưởng phòng cấp trên trong Thu mua **đột nhiên thấy nhiều chứng từ hơn hôm trước** |
| 15 | **Số bảng thiếu cột pháp nhân** | 17 trên 31 | **42 trên 57.** Bản cũ đếm theo **tệp model**, mà một tệp khai nhiều bảng. DB10 nâng cỡ và phải chia đợt theo module |

Chi tiết vì sao từng chỗ, kèm số liệu đếm được ở mã nguồn: [`06` mục 2 đến mục 5](./06-lo-trinh-nen-tang-va-hrm.md) và [`07`](./07-kien-truc-vo-erp.md).

**Bản 1.5 gộp về từ [`06`](./06-lo-trinh-nen-tang-va-hrm.md) bản 2.2 và [`08`](./08-danh-sach-task-cung-co.md)** — lần rà riêng **tầng middleware và tầng dùng chung**, ngày 12/08/2026:

| # | Chỗ sửa | Bản 1.4 | Bản 1.5 |
|---|---|---|---|
| 16 | **Tệp đính kèm** | Không có mã việc nào. `06` bản 2.1 chấm "Tạm" và mô tả là "liên kết ký hạn 10 phút" | Thành **PQ13**, xếp cùng hàng "ngay bây giờ" với PQ11. Đọc lại mã: hàm ký hạn **chỉ dùng ở một chỗ** là tải bản sao lưu; mọi tệp còn lại lưu và trả về **liên kết công khai vĩnh viễn**, và mount tệp tĩnh `/api/uploads` **không kiểm quyền**. HRM sẽ đính kèm căn cước và hợp đồng lao động vào đúng đường này |
| 17 | **Nhật ký thao tác** | Coi là phần đã có, chấm "đã ghi mọi thay đổi dữ liệu" | Thành **PQ14** (chặn quyền, làm ngay) và **HT13** (nhật ký truy cập). Endpoint đọc nhật ký chỉ kiểm **đã đăng nhập**; để trống mã bản ghi thì trả nhật ký của **mọi** bản ghi thuộc loại đó. Nhật ký chứa giá trị trước và sau, nên đây là **đường vòng đọc được dữ liệu mà phạm vi đang che** |
| 18 | **Nội dung PQ11** | Ba phần (a)(b)(c) | Thêm phần **(d)**: hàm dựng điều kiện phạm vi tra khóa `dept_name` và `owner`, còn bảng nhân sự khai `dept_id` và `self` — tra không thấy thì **bỏ qua im lặng**. Nghĩa là màn hình cấp quyền cho chọn "trừ phòng Nhân sự", lưu được, mà câu truy vấn **không có mệnh đề nào tương ứng**. Và phần **(b)** đổi thứ tự: chỉ bật chặn `export` **sau khi HT13 đã thu thập đủ hai tuần** |
| 19 | **Lớp dùng chung** | LC1–LC5 | Thêm **LC6** — gói ngữ cảnh yêu cầu ở `core/deps.py` (phiên, hồ sơ quyền, `db` trong một đối tượng), là thứ LC2 và LC3 đứng lên trên. Và ghi rõ **thứ tự bắt buộc**: LC1 → LC6 → LC2 → LC3 → **vá rồi viết lại bộ sinh router (LC4)** → chuyển module. Bộ sinh router hiện **không áp phạm vi ở bất kỳ đâu**, cho module kế thừa trước khi vá là nhân một lỗ hổng ở 1 chỗ thành 36 chỗ |
| 20 | **Middleware** | PQ9 và HT10 rải rác | Thành **HT13** gọn một mối. Toàn hệ có **đúng một middleware là CORS**; không có bộ xử lý lỗi chưa bắt nên lỗi 500 **trả sai vỏ envelope** giao diện đang dựa vào; và `default_limits=["300/minute"]` là **cấu hình chết** — `SlowAPIMiddleware` không được nạp, thực tế chỉ **4/265 route** bị giới hạn |
| 21 | **Số đếm ở LC1** | "`error()` gọi đúng 2 lần trong 36 module" | **0 lần trong module.** Hai chỗ dùng nó đều ở `main.py`, tức ở bộ xử lý lỗi chứ không phải ở module. Sửa theo đúng quy tắc của R9 |
| 22 | **Số rủi ro** | Chín | **Mười** — thêm **R10**: cấu hình bảo mật có màn hình nhưng không có tác dụng. Đã có hai ca thật, cả hai đều không có dấu hiệu nào |

Danh sách task thực thi của phần củng cố, mỗi task có **điều kiện cần** và **điều kiện đủ**: [`08`](./08-danh-sach-task-cung-co.md), 30 task mã CC chia 6 đợt.

> **Cảnh báo về lịch, thêm ở bản 1.4.** Lộ trình này **chưa trừ phần công bảo trì Thu mua đang chạy thật** ra khỏi bốn tháng rưỡi. Đo được: CR-034 đến CR-061 rơi gọn trong khoảng năm ngày làm việc, tức **xấp xỉ một yêu cầu thay đổi mỗi ngày**. Đã thành câu hỏi **C15** ở [`04`](./04-danh-muc-cho.md). Chưa trả lời C15 thì mọi mốc ở mục 10 phải đọc là **thứ tự**, không phải **ngày**.

---

## 1. Tóm tắt một trang

Mục tiêu cuối năm: vào web thấy **lưới biểu tượng phân hệ**, bấm Thu mua vào màn hình thu mua, bấm Nhân sự vào HRM, ai có quyền tới đâu thấy tới đó. Có **module quản lý webhook** chạy được, làm nền cho đồng bộ dữ liệu sau này.

> **Trước cả bước 0 — thêm ở bản 1.5.** Có bốn chỗ **đang hở thật trên hệ chạy thật**, không chờ duyệt lộ trình, không chờ khảo sát: **PQ11** (hồ sơ nhân sự đọc được bằng cách đoán id; 11 endpoint xuất/nhập không lọc phạm vi; cấu hình loại trừ phòng ban trên dữ liệu nhân sự lưu được mà không có tác dụng), **PQ13** (tệp đính kèm tải được bằng liên kết công khai vĩnh viễn, không cần đăng nhập), **PQ14** (nhật ký thao tác đọc tự do, mà nhật ký chứa giá trị trước và sau của mọi lần sửa), và **HT13** (toàn hệ có đúng một middleware; lỗi 500 trả sai vỏ envelope nên làm hỏng màn hình người dùng; chưa có nhật ký truy cập). Ba trong bốn chỗ này sẽ dẫn thẳng vào lương và căn cước khi HRM lên. Cỡ vài ngày công.

Năm bước, làm tuần tự. Hai nhóm chạy song song xuyên suốt.

| | Bước | Ra cái gì |
|---|---|---|
| Bước 0 | Khảo sát nghiệp vụ | Danh mục nghiệp vụ toàn công ty, và bản mô tả chi tiết nghiệp vụ Nhân sự |
| Bước 1 | Quy ước dữ liệu, **sẵn sàng đa pháp nhân**, và **lớp dùng chung** | Bảng mới đặt đúng khuôn, mọi bảng nghiệp vụ có pháp nhân, và viết module mới chỉ còn vài chục dòng. **Không đụng bảng cũ** |
| Bước 2 | Chia giao diện | Lưới biểu tượng, menu theo phân hệ |
| Bước 3 | Chia quyền | Quyền nào vào được màn hình nào |
| **Bước 3b** | **Bộ máy duyệt dùng chung** | Khai cấu hình là thêm được loại chứng từ mới, không viết mã |
| Bước 4 | Viết HRM | Phân hệ thứ hai chạy thật |
| Bước 5 | Module webhook | Nền cho đồng bộ dữ liệu. **Không chặn HRM, chạy song song được** |
| Song song | Tối ưu hạ tầng | Không ai nhìn thấy, thiếu là chết |
| Song song | Bảo trì Thu mua | Đang chạy thật, không dừng được |

Sau HRM là MFM — xem [`02` Dài hạn](./02-dai-han.md).

---

## 2. Ba quy tắc của đợt này

**Quy tắc 1 — Cơ sở dữ liệu cũ: chỉ thêm, không sửa.**

| Được làm | Không được làm |
|---|---|
| Tạo bảng mới | Đổi tên cột |
| Thêm cột mới, cho phép rỗng | Đổi kiểu dữ liệu cột |
| Thêm chỉ mục | Sửa dữ liệu cũ hàng loạt |
| | Xóa bảng, xóa cột |

Đây là quyết định của người chủ trì, ghi lại để về sau không ai hỏi tại sao. Lý do: Thu mua đang chạy thật, không có cửa sổ dừng hệ thống.

**Ba hệ quả phải chấp nhận, ghi ra để không ai bất ngờ:**

| Hệ quả | Cách sống chung |
|---|---|
| Trạng thái tồn tại hai kiểu: chuỗi tiếng Việt trong bảng cũ (`"Hủy đơn"`), mã tiếng Anh trong bảng mới (`"draft"`) | Phân hệ mới **bắt buộc dùng mã**. Viết bảng quy đổi ở tầng code cho báo cáo liên phân hệ |
| Cột `created_by` / `updated_by` ở bảng cũ không nói rõ là tài khoản hay nhân sự | Bảng mới đặt tên lộ ra: `*_user_id` hoặc `*_employee_id`. Không sửa bảng cũ, chỉ ghi vào từ điển dữ liệu |
| Kho chưa gắn công ty | Thêm cột mới cho phép rỗng — vẫn hợp quy tắc. Rỗng nghĩa là dùng chung toàn tập đoàn |

**Quy tắc 2 — Thu mua không được gián đoạn.** Mọi thay đổi giao diện phải có đường lui, mọi đường dẫn cũ phải chuyển hướng được.

**Quy tắc 3 — Khai một chỗ, dùng nhiều chỗ.** Danh sách phân hệ, danh sách entity, danh sách sự kiện webhook đều khai báo ở đúng một nơi trong code. Không gõ lại lần thứ hai ở giao diện.

---

## 3. Bước 0 — Khảo sát nghiệp vụ

**Vì sao làm trước:** viết phần mềm cho một nghiệp vụ chưa ai mô tả được thành văn bản là viết mò. Bước này ghi ra công ty **đang** làm gì, chưa bàn nên làm gì.

Viết ở mức **đầu mục**, không chia task chi tiết. Số việc chi tiết chỉ biết được sau khi khảo sát xong.

### 3.1 Danh mục nghiệp vụ toàn công ty

Lập trước một lần. Đây là bản đồ để biết ERP sẽ có những gì, và đang thiếu gì.

| Phân hệ | Đầu mục nghiệp vụ |
|---|---|
| **Nhân sự (HRM)** | Tuyển dụng · Hồ sơ nhân sự · Hợp đồng lao động · Phân công và điều chuyển · Chấm công · Nghỉ phép · Lương và phúc lợi · Bảo hiểm · Đánh giá · Đào tạo · Nghỉ việc |
| **Thu mua** | Yêu cầu mua hàng · Yêu cầu báo giá · Khảo sát giá · Đơn mua hàng · Nhận hàng · Công nợ phải trả · Yêu cầu thanh toán · Hợp đồng nhà cung cấp · Đánh giá nhà cung cấp |
| **Sản xuất và kho (MFM)** | Danh mục sản phẩm · Định mức nguyên vật liệu (BOM) · Kế hoạch sản xuất · Lệnh sản xuất · Xuất nguyên liệu · Nhập thành phẩm · Tồn kho · Luân chuyển kho · Kiểm kê · Chất lượng |
| **Bán hàng (CRM)** | Khách hàng · Cơ hội bán hàng · Báo giá bán · Đơn bán hàng · Giao hàng · Công nợ phải thu · Chăm sóc sau bán |
| **Kế toán** | Bút toán · Công nợ phải trả · Công nợ phải thu · Thu chi · Tài sản cố định · Giá thành |
| **Dùng chung** | Công ty và phòng ban · Danh mục · Phân quyền · Thiết bị · Dự án · Phiếu hỗ trợ · Báo cáo |

Với mỗi đầu mục, đánh dấu ba trạng thái: **đã có trên hệ thống** · **đang làm tay** · **chưa có ai làm**. Cột thứ ba thường là chỗ phát sinh việc lớn nhất, phải lộ ra sớm.

### 3.2 Chọn nghiệp vụ khảo sát chi tiết trước

Đợt này chọn **Nhân sự**. Khảo sát chi tiết toàn bộ đầu mục HRM, cộng một vòng lướt qua MFM ở mức danh mục để biết bước 1 phải chừa chỗ cho cái gì.

Lý do chọn Nhân sự: `tab_employee` đã có sẵn công ty, phòng ban, và đã nối với tài khoản đăng nhập. Đây là phân hệ có nền sẵn nhiều nhất.

**Bộ câu hỏi mang đi phỏng vấn: xem [`03` Câu hỏi khảo sát HRM](./03-cau-hoi-khao-sat-hrm.md).**

### 3.3 Mỗi đầu mục khảo sát ghi lại những gì

Bảy mục, dùng chung một khuôn cho mọi nghiệp vụ về sau:

| | Ghi lại |
|---|---|
| 1 | **Ai làm** — bộ phận nào, vị trí nào, mấy người |
| 2 | **Bắt đầu từ đâu** — cái gì kích hoạt nghiệp vụ này |
| 3 | **Các bước** — làm gì, theo thứ tự nào, mất bao lâu |
| 4 | **Ai duyệt** — mấy cấp, ai ký, điều kiện nào thì phải lên cấp trên |
| 5 | **Biểu mẫu và quy định đang dùng** — xin bản mềm, không chép lại bằng miệng |
| 6 | **Kết quả ra cái gì** — chứng từ, file, hay chỉ là trạng thái đổi |
| 7 | **Đau ở đâu** — chỗ nào chậm, chỗ nào sai nhiều, chỗ nào phải nhập lại hai lần |

Mục 5 và mục 7 hay bị bỏ. Mục 5 cho ra danh sách trường dữ liệu mà không phải ngồi nghĩ. Mục 7 cho ra thứ tự ưu tiên làm.

### 3.4 Cách đi khảo sát

- Phỏng vấn **người đang làm việc đó hằng ngày**, không phải chỉ trưởng bộ phận. Hai bên thường mô tả khác nhau, và chỗ khác nhau đó là thông tin.
- Xin **file thật đang dùng**: Excel, biểu mẫu giấy, mẫu email. Đây là nguồn chính xác nhất cho danh sách trường.
- Ghi thành **biên bản có xác nhận** của bộ phận. Không có xác nhận thì đến lúc nghiệm thu phần mềm sẽ tranh cãi.
- Hỏi rõ chỗ nào là **quy định bắt buộc theo luật**, chỗ nào là thói quen nội bộ. Loại một không được sửa, loại hai là chỗ chuẩn hóa được.

### 3.5 Bước 0 kết thúc khi có đủ ba thứ

1. **Danh mục nghiệp vụ toàn công ty** ở mức đầu mục, có đánh dấu ba trạng thái.
2. **Bản mô tả chi tiết nghiệp vụ Nhân sự** theo khuôn bảy mục, có xác nhận của phòng Nhân sự.
3. **Bảng chốt phạm vi HRM bản 1**: giữ đầu mục nào, bỏ đầu mục nào, làm sau đầu mục nào — có chữ ký duyệt.

Thứ ba là cái chặn cả bước 4. Đặc biệt phải chốt rõ **có làm lương không** và **có làm chấm công không**.

---

## 4. Bước 1 — Quy ước dữ liệu và lớp dùng chung (không đổi bảng cũ)

| Mã | Việc | Xong là thế nào |
|---|---|---|
| DB1 | **Viết quy ước bảng thành văn bản**, đưa vào `ke-hoach/03-nguyen-tac-ky-thuat.md`. Quy ước hiện đã nhất quán trong code (tất cả `tab_*`, tất cả có `id` / `created_at` / `created_by` / `updated_at` / `updated_by`) nhưng chỉ tồn tại trong đầu người viết | Một mục trong file `03`, có ví dụ đúng và ví dụ sai |
| DB2 | **Chốt quy ước đặt tên cột người** cho bảng mới: `*_user_id` là tài khoản, `*_employee_id` là nhân sự. Ghi rõ vì sao — đã có tiền lệ hiểu nhầm với `assignee_id` | Ghi trong DB1 |
| DB3 | **Chốt quy ước trạng thái** cho bảng mới: lưu **`SMALLINT` theo `IntEnum`**, không lưu chuỗi. Nhãn hiển thị tra bảng, khai trong `core/enums.py`. Kèm bảng quy đổi sang chuỗi tiếng Việt của bảng cũ. Đã có tiền lệ đúng trong mã nguồn: module nhập dữ liệu. Lý do và số liệu ở [`06` R2](./06-lo-trinh-nen-tang-va-hrm.md) | Ghi trong DB1; **một tệp `core/enums.py`** khai đủ enum của bảng mới, kèm nhãn tiếng Việt |
| DB4 | **Chốt quy tắc công ty**: bảng nào dùng chung toàn tập đoàn, bảng nào tách theo công ty | Một bảng phân loại |
| DB5 | **Thêm cột công ty cho kho** (cho phép rỗng). Rỗng = dùng chung | Migration chỉ thêm cột |
| DB6 | **Tầng sản phẩm cha** — bảng mới ở trên `tab_product`. Bắt buộc cho BOM. Theo đúng D-025: cấm thêm bảng biến thể ở dưới, cấm đổi hoặc tái dùng `product_code`, cấm đặt cột giá lên sản phẩm | Bảng mới, `tab_product` không đổi một dòng |
| DB7 | **Từ điển dữ liệu sinh tự động** từ model, đăng lên Help Center. Ghi cả các chỗ "biết là chưa chuẩn nhưng cố ý giữ" | Trang trong Help Center, tự cập nhật khi model đổi |
| DB8 | **Nâng danh mục dùng chung ra khỏi Thu mua**. Đơn vị tính, phân loại, thương hiệu, kho đang nằm trong `modules/catalog` thuộc Thu mua | Đổi chỗ code, **không đổi bảng, không đổi dữ liệu** |
| DB9 | **Gom việc đánh số chứng từ về một dịch vụ chung**. Hiện gọi rải rác ở 4 module, cộng 2 chỗ viết tay riêng. Có phần chống trùng khi hai người bấm cùng lúc | Một hàm dùng chung |
| **DB14** | **Sinh tệp enum của giao diện từ `core/enums.py`.** Một kịch bản sinh ra `frontend/src/config/enums.ts`, tệp sinh ra **lưu vào mã nguồn** nên giao diện có kiểm tra kiểu đầy đủ. CI chạy lại kịch bản và so sánh. **Không dựng endpoint lấy động** — lý do ở [`06` H2](./06-lo-trinh-nen-tang-va-hrm.md). Gom luôn 9 tệp giao diện đang chép lại danh sách trạng thái về đúng tệp này | Thêm một trạng thái ở máy chủ mà quên sinh lại tệp thì **CI hỏng**, không phải chờ người dùng phát hiện |

Mười việc này **không cái nào đụng dữ liệu đang chạy**. DB8, DB9, DB14 chỉ đổi code.

### 4.1 Sẵn sàng đa pháp nhân — bốn việc thêm ở bản 1.1, cộng DB15 ở bản 1.4

**Vì sao đưa vào bước 1 chứ không để sau:** thêm cột pháp nhân vào bảng đã có vài chục nghìn dòng thì phần khó không phải là thêm cột, mà là trả lời câu **"dòng cũ thuộc pháp nhân nào"**. Lúc đó thường không còn thông tin để trả lời, và câu trả lời hay dùng là gán hết vào pháp nhân mặc định — sai vĩnh viễn, không sửa lại được.

Đếm lại ở mã nguồn ngày 12/08/2026: `company_id` có ở **15 trên 57 bảng** — **42 bảng còn thiếu**.

> **Bản 1.1 ghi "14 trên 31" là đếm nhầm đơn vị**, không phải đếm nhầm số: đó là 14 trên 31 **tệp model**, mà một tệp thường khai nhiều bảng. Phân quyền và phạm vi chạy theo **bảng**, nên mọi số liệu loại này phải đếm theo bảng. Trong 42 bảng thiếu có bảng lớn: khảo sát, nhà cung cấp, sản phẩm, dòng đơn mua hàng, dòng yêu cầu mua hàng, kho, đơn vị tính, nhóm hàng, thương hiệu, tài khoản, vai trò. **Khối lượng thật của DB10 lớn hơn gần hai lần rưỡi so với bản 1.1**, nên phải chia đợt theo module chứ không làm một lần.

| Mã | Việc | Xong là thế nào |
|---|---|---|
| DB10 | **Thêm cột pháp nhân cho mọi bảng nghiệp vụ còn thiếu** — **42 bảng**, cho phép rỗng nên vẫn hợp quy tắc 1. **Chia thành nhiều đợt theo module**, một đợt một nhóm bảng, không làm một lần. Điền cho dòng cũ **theo dữ liệu suy được** (theo người tạo, theo chứng từ cha). Chỗ nào không suy được thì **để rỗng và ghi lại**, không đoán | Migration chỉ thêm cột; có một bảng liệt kê số dòng không suy được, kèm cách xử lý từng nhóm |
| DB11 | **Đánh số chứng từ theo pháp nhân**: mã chứng từ có phần pháp nhân, bộ đếm riêng từng pháp nhân. Làm cùng DB9 vì cùng đụng một dịch vụ | Hai pháp nhân cùng tạo chứng từ trong một ngày thì không trùng số, và nhìn mã biết được của pháp nhân nào |
| DB12 | **Chốt quy tắc dữ liệu dùng chung và dữ liệu riêng**: danh mục sản phẩm, nhà cung cấp, đơn vị tính dùng chung toàn tập đoàn; chứng từ, nhân sự, hợp đồng thuộc về một pháp nhân. Đây là DB4 mở rộng, ghi chung một chỗ | Một bảng phân loại đủ **57 bảng**, không bảng nào để trống |
| DB13 | **Trả lời trước: một người làm cho nhiều pháp nhân thì một hồ sơ hay nhiều hồ sơ.** Không phải việc viết mã, là việc phải chốt — nhưng phải chốt **trước HR1** vì không sửa được sau khi đã nhập dữ liệu. Đã đưa vào [`04` mục 2b, C13](./04-danh-muc-cho.md) | Có câu trả lời bằng văn bản của phòng Nhân sự trước khi tạo bảng hồ sơ |
| **DB15** | **Phạm vi phòng ban khóa theo `dept_id`** (chốt Đ8, chi tiết ở [`06` H16](./06-lo-trinh-nen-tang-va-hrm.md)). Hiện `apply_scope` lọc phòng ban bằng **so bằng chuỗi tiếng Việt**: chứng từ lưu cột `department` kiểu `String(255)`, đem so đúng bằng với `dept_name` trong hồ sơ quyền. Thêm cột `dept_id` cho ba bảng chứng từ đang dùng tên (yêu cầu mua hàng, yêu cầu khảo sát, đơn mua hàng); điền theo tên hiện có, **tên nào không khớp phòng nào thì để rỗng và ghi ra bảng lỗi, không đoán**; chuyển `apply_scope` sang so theo id; giữ cột tên chạy song song rồi mới bỏ. Cùng khuôn sáu bước của [`06` mục 4](./06-lo-trinh-nen-tang-va-hrm.md) | **Đổi tên một phòng ban không làm ai mất dữ liệu đang thấy.** Có bảng liệt kê số dòng không khớp được tên nào |

**Kiểm chứng cả nhóm:** tạo thêm một pháp nhân thứ hai trên môi trường thử, nhập vài chứng từ, và không màn hình nào lẫn dữ liệu giữa hai pháp nhân.

### 4.2 Lớp dùng chung ở tầng nghiệp vụ — năm việc thêm ở bản 1.2

**Vì sao đưa vào đây chứ không để sau HRM:** giá của nhóm này tỷ lệ thuận với **lượng mã còn chưa viết**. HRM sẽ sinh hơn mười module mới. Làm trước thì mười module đó được lợi; làm sau thì phải đi dọn lại chính những module vừa viết, và lúc đó chúng đã chạy thật nên dọn khó hơn nhiều.

Đo ở mã nguồn ngày 12/08/2026:

| Đo cái gì | Con số | Hậu quả |
|---|---|---|
| Ném lỗi bằng `HTTPException` thô | **259 chỗ** *(bản 1.2 ghi 247 — chênh do CR-060, CR-061 vào sau)* | Mã lỗi trả ra chỉ là con số HTTP, giao diện muốn rẽ nhánh phải so chuỗi tiếng Việt |
| **Áp phạm vi dữ liệu bằng tay** | **38 chỗ** | Quên một chỗ là lộ dữ liệu. Đây là PQ4 nhìn từ góc khác — và **đã quên 3 chỗ rồi**, xem PQ11 |
| Ghi nhật ký thao tác bằng tay | **92 chỗ** | Quên một chỗ là mất dấu vết |
| Endpoint danh sách chép cùng khuôn | **25 chỗ** | Sửa cách phân trang là sửa 25 chỗ |
| Bộ sinh router chung `make_crud_router` | dùng ở **1 trên 36** module (chỉ `catalog`) | 35 module tự viết lại năm endpoint giống hệt |
| Endpoint xuất và nhập tệp tự viết | **11 endpoint** trên 6 module | Không endpoint nào áp phạm vi, chỉ 1 kiểm quyền `export` |
| **Endpoint đọc so với chỗ áp phạm vi** *(thêm ở bản 1.5)* | **97 endpoint đọc / 38 chỗ áp phạm vi** | Đây là con số nói rõ nhất vì sao phải gom: `apply_scope` **đã là** một hàm dùng chung viết đúng. Vấn đề không phải thiếu hàm, mà là **hàm đó có thể quên gọi** |
| Middleware toàn hệ *(thêm ở bản 1.5)* | **1** — chỉ CORS | Không mã định danh request, không nhật ký truy cập, không bộ xử lý lỗi chưa bắt. Xem HT13 |
| Route có giới hạn tần suất *(thêm ở bản 1.5)* | **4 trên 265** | `default_limits=["300/minute"]` khai rồi nhưng middleware không được nạp — **cấu hình chết**, đọc mã lại tưởng cả hệ được bảo vệ |

Phần đang làm đúng thì **giữ nguyên**: controller mỏng, nghiệp vụ nằm ở `service.py`, bảy tệp hạ tầng ở `core/` đúng chỗ. Vấn đề không phải thiếu lớp dùng chung, mà là **lớp dùng chung đang dừng ở mức hàm rời rạc** nên mỗi module vẫn phải tự lắp lại đủ bảy bước.

| Mã | Việc | Xong là thế nào |
|---|---|---|
| **LC1** | **Hàm trả lỗi dùng chung.** `core/response.py` đã có sẵn hàm `error(...)` đúng chuẩn nhưng trong 36 module **gọi 0 lần** *(bản 1.4 ghi "đúng 2 lần" — đếm gộp nhầm hai chỗ dùng ở `main.py`, tức ở bộ xử lý lỗi chứ không phải ở module)*. Viết `core/errors.py`: `ErrorCode` là `StrEnum`, bảng `MESSAGES` khai câu chữ một chỗ, lớp `AppError(code, status, **ctx)`. Bộ xử lý tập trung dựng ra `{code, message, details, request_id}`. Giữ bộ xử lý cũ chạy song song, **module mới bắt buộc dùng cái mới**, 259 chỗ cũ chuyển dần theo từng module | Giao diện rẽ nhánh theo `code` chứ không theo chữ tiếng Việt; sửa câu `"Ngoài phạm vi được phép xem"` là sửa **1 dòng** thay vì 10 chỗ; người dùng đọc `request_id` qua điện thoại là tra ra đúng dòng nhật ký |
| **LC2** | **Hàm danh sách chuẩn.** Gộp sáu bước đang lắp tay ở 25 chỗ: lọc → **áp phạm vi** → sắp xếp → đếm → phân trang → chuyển schema. Module gọi một dòng thay vì bảy | **Áp phạm vi trở thành mặc định**; muốn không áp thì phải ghi rõ ra. Đây là fail-closed của PQ4 áp thêm một lần nữa ở tầng controller |
| **LC3** | **Lớp dịch vụ nền.** `get_or_404`, tạo, sửa, xóa; **tự ghi nhật ký thao tác**, tự gán người tạo và người sửa. Module kế thừa rồi chỉ viết phần riêng | 92 chỗ ghi nhật ký tay và 53 chỗ ném lỗi "không tìm thấy" tay biến mất. Quên gắn nhật ký thành chuyện không thể xảy ra |
| **LC6** *(thêm ở bản 1.5)* | **Gói ngữ cảnh yêu cầu — `core/deps.py`.** Hiện mỗi endpoint tự khai ba, bốn phụ thuộc rời: `db`, `user`, rồi tự gọi `get_perm_profile` (42 chỗ). Gộp thành **một** đối tượng ngữ cảnh: phiên cơ sở dữ liệu, tài khoản, hồ sơ quyền, mã định danh request. Endpoint nhận đúng một tham số. **Đây là tệp mà LC2 và LC3 đứng lên trên** — có ngữ cảnh thì hàm danh sách mới tự áp được phạm vi mà không cần người viết truyền tay | Endpoint mới không có cách nào lấy được dữ liệu mà **không** đi qua ngữ cảnh, nên cũng không có cách nào bỏ sót hồ sơ quyền |
| **LC4** | **Vá rồi mới mở rộng bộ sinh router chung.** *(Thêm ở bản 1.5 — phần vá.)* Bộ sinh router hiện tại **không gọi `apply_scope` ở bất kỳ đâu**; endpoint xuất tệp nó sinh ra chỉ kiểm quyền `read` chứ không kiểm `export`; nhánh nhập tệp gọi một hàm **chưa nhập khẩu ở phạm vi đó nên chạy tới là lỗi tên**; nhập tệp **không ghi nhật ký, không giới hạn số dòng**. Vá xong mới mở rộng để nhận thêm phạm vi dữ liệu, xuất tệp, đính kèm, bình luận; rồi chuyển các module danh mục thuần sang dùng. Kèm **một cơ chế xuất tệp dùng chung** thay 11 endpoint tự viết, khai cột theo dữ liệu, gắn sẵn **ba thứ đã chốt ở PQ11**: kiểm quyền `export` / `import`, áp phạm vi dữ liệu, và ghi nhật ký mỗi lần xuất | Khoảng một nửa số module hiện tại chạy trên bộ sinh chung; xuất tệp thống nhất một kiểu, và **không cửa nào xuất được dữ liệu ngoài phạm vi** |
| **LC5** | **Bộ khung module mới** — thư mục mẫu để tạo module đúng chuẩn ngay từ đầu, có sẵn LC1 đến LC4 và LC6 | **Viết một module danh mục mới từ đầu tới lúc chạy được dưới 50 dòng mã**, và module đó tự có phân quyền, phạm vi, nhật ký, phân trang, sắp xếp, xuất tệp, mã lỗi chuẩn |

**Thứ tự bắt buộc, thêm ở bản 1.5:** **LC1 → LC6 → LC2 → LC3 → LC4 (vá trước, mở rộng sau) → chuyển từng module → LC5**. Mỗi bước đứng trên bước trước. Riêng chỗ LC4 là bắt buộc chứ không phải khuyến nghị: bộ sinh router đang **không có phạm vi**, cho module kế thừa trước khi vá là **nhân một lỗ hổng ở 1 chỗ thành lỗ hổng ở 36 chỗ**.

**Nguyên tắc gom, để không gom quá tay:** chỉ gom cái đã lặp **từ ba lần trở lên** và lặp **giống hệt nhau**. Gom hai cái hơi giống nhau thành một lớp cha có năm tham số điều kiện thì khó đọc hơn là để nguyên.

**Nguyên tắc thứ hai, quan trọng hơn — thêm ở bản 1.5:** *đừng viết hàm tiện ích để người ta nhớ mà gọi; hãy làm cho **đường đi lấy dữ liệu duy nhất** đã có sẵn phạm vi bên trong, ai muốn không lọc thì phải ghi rõ `public=True`.* Căn cứ là bảng đo phía trên: **97 endpoint đọc, 38 chỗ áp phạm vi**. `apply_scope` vốn là hàm dùng chung viết đúng — thứ hỏng là nó **có thể quên gọi**. Thêm một hàm tiện ích nữa cũng quên gọi được y hệt.

**Kiểm chứng cả nhóm:** lấy một module danh mục đang có, viết lại trên lớp dùng chung, và số dòng giảm ít nhất một nửa mà không mất chức năng nào.

---

## 5. Bước 2 — Chia giao diện

**Hiện trạng:** một ứng dụng web, một file bố cục `AppLayout.tsx` dài 904 dòng chứa mảng menu cứng khoảng 30 mục, một file `cruds.tsx` dài 765 dòng khai báo toàn bộ màn hình danh sách.

**Bản thiết kế chi tiết của bước này ở [`07` Kiến trúc vỏ ERP](./07-kien-truc-vo-erp.md)** — có hợp đồng dữ liệu của endpoint, bảng chia 28 entity vào phân hệ, cơ chế chạy song song, đường lui. Bảng dưới là danh sách việc; `07` là cách làm.

| Mã | Việc | Xong là thế nào |
|---|---|---|
| FE1 | **Khai báo phân hệ** ở backend `core/modules.py`: mã, tên, biểu tượng, thứ tự, loại, trang chủ, và entity nào thuộc phân hệ nào. Nguồn sự thật duy nhất | Một file khai báo, dùng cho cả lưới, menu, phân quyền, thông báo. **Thêm entity mà quên xếp vào phân hệ thì ứng dụng không khởi động được** |
| FE2 | **Màn hình lưới biểu tượng** làm trang chủ mới | Vào web thấy các ô phân hệ |
| FE3 | **Dashboard hiện tại thành dashboard riêng của Thu mua** | Bấm Thu mua mới thấy |
| FE4 | **Thêm trường `module` vào mảng menu của `AppLayout.tsx`**, lọc theo phân hệ đang đứng, cộng nút quay về lưới. Mảng menu đã có sẵn `entity` và đã tự ẩn theo quyền — **sửa dữ liệu khai báo, không sửa logic** | Menu chỉ hiện màn hình của phân hệ đang mở |
| FE5 | **Tiền tố đường dẫn chỉ cho phân hệ mới**: `/nhan-su/ho-so`, `/nhan-su/hop-dong`. **Thu mua giữ nguyên đường dẫn**, không đổi. Lý do ở [`07` mục 7](./07-kien-truc-vo-erp.md) | Hợp đồng lao động và hợp đồng nhà cung cấp cùng tên `contract` mà không đụng nhau, và không phải đổi bên cũ |
| FE6 | **Kiểm link cũ còn sống.** Lấy một mẫu đường dẫn thật từ cột `notification.link` trong cơ sở dữ liệu, mở thử sau khi bật vỏ | Mọi link trong thông báo đã gửi vẫn vào đúng màn hình |
| ~~FE7~~ | **Tách `cruds.tsx` theo phân hệ — đẩy sang khi thêm phân hệ thứ hai.** Không phải điều kiện của vỏ, và cắt lúc này thì cắt mò | Xem lại ở bước 4 |
| FE8 | **Đăng ký router theo phân hệ ở backend.** `main.py` hiện có 38 dòng import và 38 dòng gắn router viết tay | Thêm phân hệ không phải sửa `main.py` |
| FE9 | **Gắn nhãn phân hệ** vào thông báo, nhật ký thao tác, tìm kiếm | Thông báo nói rõ nó thuộc phân hệ nào |
| FE10 | **Đưa Help Center và Project-M vào lưới** — đã chốt là **có**. Chi tiết ở 5.1 | Hai ô trên lưới, bấm sang được, quay về được |
| FE11 | **Cập nhật Help Center**: menu đổi thì toàn bộ ảnh chụp màn hình trong tài liệu hướng dẫn sai | Ảnh chụp mới, hướng dẫn mới |
| FE12 | **Thông báo và hướng dẫn người dùng hiện tại** trước ngày đổi | Có bản tin gửi trước, có buổi hướng dẫn ngắn |
| **FE13** | **Cờ tính năng `VITE_ERP_SHELL`**, theo đúng khuôn đã dùng cho phiếu hỗ trợ: bản chạy thật tắt, dev bật, cùng một nhánh mã | Tắt cờ là mọi thứ trở lại hệt trước, trong vài phút. Chốt sẵn **hạn bỏ cờ**: một tháng sau ngày bật thật |
| **FE14** | **Có đúng một phân hệ thì vào thẳng, không hiện lưới.** Nhiều phân hệ thì vào cái dùng lần trước, có nút đổi | Người chỉ dùng Thu mua không phải bấm thêm cú nào so với hôm nay |
| **FE15** | **Tệp mô phỏng hợp đồng dữ liệu** của `/api/me/modules`, để người làm giao diện làm trọn lưới trước khi backend xong | Hai người không chặn nhau. Xóa tệp khi endpoint thật lên |

**FE11 và FE12 không phải việc phụ.** Đổi vào lưới biểu tượng là đổi thói quen hằng ngày của toàn bộ người đang dùng Thu mua.

**FE14 cũng không phải việc phụ.** Người chỉ có mỗi Thu mua mà phải bấm thêm một cú mỗi lần vào web, mỗi ngày, mãi mãi — đó là cái giá vỏ ERP bắt người dùng trả mà họ không nhận lại gì.

### 5.1 Help Center và Project-M trên lưới — đã chốt là có

Hai cái này là **ứng dụng riêng, tên miền riêng, dùng chung backend và chung tài khoản**. Không gộp code, chỉ gộp cửa vào.

| Mã | Việc |
|---|---|
| FE10a | Ô trên lưới trỏ sang tên miền riêng của từng ứng dụng, mở cùng tab |
| FE10b | Ẩn ô theo quyền: Help Center hiện với mọi người, Project-M chỉ hiện với người có quyền |
| FE10c | Thêm **nút quay về lưới** trong Help Center và Project-M |
| FE10d | Kiểm tra chuyển tiếp đăng nhập giữa ba ứng dụng, không bắt đăng nhập lại |
| FE10e | Thống nhất biểu tượng và cách đặt tên ô để lưới nhìn không lệch nhau |

Lý do đưa vào: người dùng không cần biết bên trong là ba ứng dụng hay một. Với họ chỉ có một hệ thống.

---

## 6. Bước 3 — Chia quyền

**Hiện trạng, hai điểm quan trọng:**
- `permissions.py` là danh sách **phẳng 28 entity, không có nhóm**. Không có khái niệm phân hệ ở bất kỳ đâu trong code. (Bản 1.2 và [`06`](./06-lo-trinh-nen-tang-va-hrm.md) ghi 29 — đếm lại ngày 12/08/2026 được 28.)
- Phần lọc dữ liệu theo phạm vi (`scoping.py`) **chỉ khai báo 9 trên 28 entity**. Entity nào thiếu thì không lọc chiều đó — im lặng, không báo lỗi.
- **Và ngay cả entity đã khai vẫn hở nếu endpoint quên gọi.** Phạm vi đang áp **bằng tay ở 38 chỗ**. Rà module nhân sự ngày 12/08/2026: `employee` khai đủ, nhưng `GET /api/employees/{id}` và `GET /api/employees/export/csv` **đều không gọi `apply_scope`** — ai có quyền đọc nhân sự là xem được hồ sơ bất kỳ chỉ cần đoán id, và tải về được toàn bộ nhân sự mọi pháp nhân. Cả **11 endpoint xuất/nhập tệp** đều vậy. Hành động `export` **đã có sẵn** trong hệ phân quyền nhưng chỉ **1 trên 11** endpoint kiểm nó. Đây là **PQ11**, làm ngay.

| Mã | Việc | Xong là thế nào |
|---|---|---|
| PQ1 | **API trả về "tài khoản này thấy được phân hệ nào"** — `GET /api/me/modules`, có ít nhất một entity đọc được thì thấy phân hệ đó. Tính ở backend. Dạng trả về chốt sẵn ở [`07` mục 4.3](./07-kien-truc-vo-erp.md) | Giao diện chỉ hỏi, không tự tính. **Không dựng hệ quyền thứ hai** — dùng lại hồ sơ quyền sẵn có |
| PQ2 | **Lưới biểu tượng ẩn phân hệ không có quyền** | Người không làm nhân sự thì không thấy ô Nhân sự |
| PQ3 | **Sửa màn hình phân quyền**: hiện là ma trận phẳng 28 × 8. Thêm HRM và MFM thì thành 60–80 entity, không ai bấm nổi. Gom theo phân hệ, mở đóng từng nhóm, thêm nút cấp cả phân hệ | Cấp quyền cho một người mất dưới một phút |
| PQ4 | **Vá lỗ hổng phạm vi dữ liệu.** Chuyển khai báo phạm vi sang dạng bảng, và **bắt buộc mọi entity phải khai báo — thiếu thì báo lỗi lúc khởi động** | Thiếu khai báo là ứng dụng không lên |
| PQ5 | **Bổ sung khai báo phạm vi cho 19 entity còn thiếu** (đếm lại lúc bắt tay làm, vì danh sách entity có thể đã thêm) | Đủ 28 trên 28 |
| PQ6 | **Bộ kiểm thử phân quyền tự động**, sinh ca kiểm thử từ ma trận | Chạy trong CI, đỏ là không phát hành |
| PQ7 | **Rà lại vai trò hiện có**, gắn vai trò vào phân hệ | Mỗi vai trò nói rõ thuộc phân hệ nào |
| PQ8 | **Rà mọi chỗ sửa vai trò đều xóa bộ đệm quyền** | Không còn chỗ quên |
| PQ9 | **Thu hồi được token.** Thêm mã định danh vào token cộng bảng token đã thu hồi. Hiện token **không có mã định danh riêng** nên khóa một tài khoản xong người đó vẫn dùng tiếp được tới khi token hết hạn; đăng xuất chỉ xóa ở trình duyệt | Khóa một tài khoản thì phiên của người đó chết trong vài giây, có bài kiểm tự động chứng minh |
| PQ10 | **Bộ đệm quyền dùng chung qua Redis** thay cho bộ nhớ từng tiến trình. Hiện đệm nằm trong bộ nhớ tiến trình hạn 60 giây, mà bản chạy thật có **2 tiến trình** — sửa quyền xong tiến trình kia vẫn dùng quyền cũ. Redis đã có sẵn, đang dùng làm hàng đợi | Đổi quyền một người thì mọi tiến trình thấy ngay, có bài kiểm |
| **PQ11** | **Vá bốn chỗ đang hở — làm ngay, không chờ duyệt lộ trình.** (a) Thêm `apply_scope` vào `GET /api/employees/{id}` và cả 11 endpoint xuất/nhập tệp. (b) Bắt buộc kiểm quyền `export` ở cả 11 endpoint đó, thêm hành động `import` vào danh sách hành động — **chỉ bật chặn sau khi HT13 đã chạy và thu thập đủ hai tuần**, xem ghi chú dưới bảng. (c) **Ghi một dòng nhật ký cho mỗi lần xuất**: ai, lúc nào, bảng nào, bao nhiêu dòng, bộ lọc gì. **(d) *(thêm ở bản 1.5)* Sửa hàm dựng điều kiện phạm vi**: hàm này tra khóa `dept_name` và `owner`, còn khai báo phạm vi của bảng nhân sự chỉ có `company`, `dept_id`, `self` — tra không thấy thì **bỏ qua im lặng**. Hệ quả: màn hình cấp quyền cho chọn "chỉ phòng này" hoặc "trừ phòng Nhân sự" trên dữ liệu nhân sự, **lưu được**, mà câu truy vấn **không có mệnh đề nào tương ứng**. Sửa cho tra đúng khóa đã khai, và **tra không thấy thì báo lỗi chứ không bỏ qua**. Chốt Đ9 ở [`04`](./04-danh-muc-cho.md) | Không endpoint nào trả dữ liệu ngoài phạm vi của người gọi; mọi lần xuất dữ liệu tra lại được về sau; **cấu hình loại trừ phòng ban đặt trên dữ liệu nhân sự có tác dụng thật — đếm số dòng trước và sau khi loại trừ phải khác nhau**. **Cỡ khoảng một ngày công cho (a) và (d)** |
| **PQ13** *(thêm ở bản 1.5)* | **Tệp đính kèm phải đi qua kiểm quyền — làm ngay** (chi tiết ở [`06` H17](./06-lo-trinh-nen-tang-va-hrm.md)). Hiện hàm sinh liên kết ký hạn **chỉ dùng ở một chỗ** là tải bản sao lưu; mọi tệp còn lại — hợp đồng, đính kèm chứng từ, ảnh nhân sự, chữ ký, tệp nhập — được lưu và trả về **liên kết công khai vĩnh viễn**, và mount tệp tĩnh `/api/uploads` **không gắn phụ thuộc kiểm quyền nào**. Khóa tệp lại đoán được: `{môi trường}/{loại}/{năm}/{tháng}/{id}-{tên gốc}`. Đưa mọi tệp về **một đường tải duy nhất**: kiểm đăng nhập → kiểm quyền đọc **của chứng từ chủ quản** → áp phạm vi của chứng từ đó → mới chuyển hướng sang liên kết ký hạn ngắn. Bỏ hoặc khóa mount tệp tĩnh; **ngừng lưu liên kết công khai vào cơ sở dữ liệu, lưu khóa tệp và sinh liên kết lúc trả về**; ghi nhật ký mỗi lượt tải | Dán liên kết tệp hợp đồng vào cửa sổ trình duyệt ẩn danh thì **bị chặn**. Người không có quyền đọc chứng từ chủ quản cũng bị chặn dù có liên kết trong tay. **Chặn HR1 và HR3** — hợp đồng lao động và căn cước là **tệp**, không phải cột trong bảng, nên vá phạm vi ở tầng truy vấn không che được đường này |
| **PQ14** *(thêm ở bản 1.5)* | **Nhật ký thao tác phải có quyền và có phạm vi — làm ngay** (chi tiết ở [`06` H18](./06-lo-trinh-nen-tang-va-hrm.md)). Endpoint đọc nhật ký hiện chỉ kiểm **đã đăng nhập**: không kiểm quyền, không áp phạm vi, và **để trống mã bản ghi thì trả nhật ký của mọi bản ghi thuộc loại đó** — chính tài liệu API viết như vậy. Nhật ký chứa giá trị **trước và sau** của từng lần sửa, nên đây là **đường vòng đọc được dữ liệu mà phạm vi đang che**. Thêm kiểm quyền; áp phạm vi **theo chứng từ chủ quản** chứ không theo bản thân dòng nhật ký; che trường nhạy cảm trong nội dung trước/sau bằng đúng bộ lọc của PQ12 | Người không có quyền đọc một chứng từ thì gọi thẳng endpoint nhật ký của chứng từ đó **cũng không ra dòng nào**. Cỡ nhỏ — chặn quyền là việc nửa ngày; phần nhật ký truy cập tách sang **HT13** |
| **PQ12** | **Phân quyền mức trường** (chốt Đ10, chi tiết ở [`06` H15](./06-lo-trinh-nen-tang-va-hrm.md)). Khai danh sách trường nhạy cảm theo entity (lương, căn cước, tài khoản ngân hàng, ngày sinh); cấp quyền đọc và sửa riêng cho từng nhóm trường; **lọc ngay ở lớp schema đầu ra**, không lọc ở giao diện. Xuất tệp và webhook dùng chung bộ lọc đó | Trưởng phòng mở hồ sơ nhân viên phòng mình thì **cột lương không có mặt trong JSON**, không phải trả rỗng — kể cả khi gọi thẳng API bằng công cụ lập trình |

**Tám việc chặn HRM, không được bỏ qua.** Với Thu mua, quên khai báo phạm vi thì hậu quả nhẹ. Với HRM thì đó là lộ lương và hợp đồng lao động.

| Việc | Không làm thì hậu quả gì |
|---|---|
| **PQ11** | **Đang hở, hôm nay.** Hồ sơ nhân sự đọc được bằng cách đoán id; toàn bộ danh sách nhân sự tải về được bằng một cú bấm. HRM sẽ thêm căn cước rồi lương vào đúng bảng đó |
| PQ4 | Thêm một loại dữ liệu mà quên khai phạm vi là mọi người thấy hết, im lặng, không báo lỗi |
| PQ5 | Mười chín loại dữ liệu hiện đang không lọc theo phạm vi |
| PQ9 | Khóa tài khoản một người vừa nghỉ việc nhưng người đó vẫn vào được |
| PQ10 | Rút quyền của một người mà nửa số lượt truy cập vẫn dùng quyền cũ |
| **PQ12** | Không có tầng cột thì "trưởng phòng xem được nhân viên phòng mình" và "kế toán xem được lương" buộc phải tách thành hai entity giả — hoặc để hở. Vá sau khi HR3 đã chạy là sửa lại cả API lẫn giao diện |
| **PQ13** | **Đang hở, hôm nay.** Liên kết tệp là công khai và vĩnh viễn: ai có liên kết là tải được, không cần đăng nhập, không hết hạn, và khóa tệp đoán được theo cấu trúc. HRM sẽ đính kèm **căn cước và hợp đồng lao động** vào đúng đường này. Vá phạm vi ở tầng truy vấn **không che được đường này** vì đây là tệp, không phải cột |
| **PQ14** | **Đang hở, hôm nay.** Nhật ký thao tác đọc tự do và chứa giá trị trước/sau của mọi lần sửa — nghĩa là mọi công sức phân quyền và phạm vi ở trên **bị đi vòng qua bằng một endpoint duy nhất**. Với HRM thì đó là đọc được lịch sử đổi lương |

**Cả tám phải xong trước khi HRM có dữ liệu thật**, riêng **PQ11, PQ13, PQ14 phải xong ngay bây giờ** vì cả ba không chờ HRM mới nguy hiểm. Bản 1.0 chỉ ghi PQ4 và PQ5; PQ9, PQ10 thêm ở bản 1.1; PQ11, PQ12 thêm ở bản 1.4; PQ13, PQ14 thêm ở bản 1.5 sau khi rà riêng tầng middleware và tầng dùng chung ngày 12/08/2026.

> **Ghi chú thứ tự giữa PQ11(b) và HT13.** Hiện chỉ **1/11** endpoint xuất tệp kiểm quyền `export` — tức mười endpoint còn lại đang có người dùng thật, hằng ngày, mà **không ai biết là ai**. Bật chặn trước là cắt việc của những người đó mà không báo trước, và không có cách nào biết trước là cắt vào ai. Thứ tự bắt buộc: **HT13 (nhật ký truy cập) → thu thập hai tuần → đọc danh sách và cấp quyền `export` cho đúng người đang xuất → mới bật chặn ở PQ11(b)**. Ba phần còn lại của PQ11, cùng PQ13 và PQ14, **không chờ gì cả**.

---

## 6b. Bước 3b — Bộ máy duyệt dùng chung

**Việc này ở bản 1.0 là một dòng HR7 nằm trong bước 4.** Bản 1.1 tách ra thành bước riêng, đặt **trước** HRM, vì ba lý do:

1. **Nó không phải việc của HRM.** Thu mua đang dùng nó, HRM sẽ dùng nó, MFM về sau cũng dùng. Để trong HRM thì nó bị tính là chi phí của HRM và dễ bị cắt khi HRM chậm lịch.
2. **Nó chặn phần lớn HRM.** Đơn từ, quyết định điều chuyển, quyết định thôi việc — không cái nào chạy được nếu chưa có bộ máy duyệt khai báo được.
3. **Khối lượng bị đánh giá thấp.** Một dòng trong bảng 13 dòng trông như một phần mười ba của bước 4. Thực tế đây là hạng mục lớn nhất của cả phần nền. Hệ thống HRM thương mại đã khảo sát dùng **một** bộ máy cho **88** loại chứng từ — xem [`tham-khao-hrm/02` mục DT7](./tham-khao-hrm/02-don-tu-va-duyet.md).

**Hiện trạng:** mỗi loại chứng từ tự viết luồng duyệt trong mã nguồn. Thêm loại chứng từ là thêm mã. Đổi người duyệt là sửa mã và triển khai lại.

| Mã | Việc | Xong là thế nào |
|---|---|---|
| DUY1 | **Bảng khai quy trình**: mỗi loại chứng từ khai chuỗi bước, mỗi bước có tên, thứ tự, và điều kiện áp dụng | Khai trên giao diện, không sửa mã |
| DUY2 | **Người duyệt khai bằng vai tương đối** — trưởng phòng của người nộp, giám đốc của pháp nhân của người nộp — chứ không gọi đích danh. Gọi đích danh thì người đó nghỉ phép là cả công ty đứng | Một người đổi phòng ban thì quy trình tự đúng theo, không sửa cấu hình |
| DUY3 | **Rẽ nhánh theo điều kiện**: quá một giá trị thì thêm cấp duyệt; loại chứng từ nào thì bỏ cấp nào | Khai được bằng cấu hình |
| DUY4 | **Nhật ký duyệt dùng chung** cho mọi loại chứng từ, khóa theo loại chứng từ cộng mã phiếu | Một màn hình tra được lịch sử duyệt của mọi loại phiếu |
| DUY5 | **Chuyển một loại chứng từ đang chạy thật của Thu mua sang bộ máy mới**, có đường lui. Đây là phép thử bắt buộc — không chuyển được cái đang chạy thì bộ máy chưa dùng được | Người dùng không nhận ra khác biệt |
| DUY6 | **Màn hình cấu hình quy trình** cho quản trị: thêm, sửa, sao chép quy trình có sẵn | Thêm loại chứng từ mới chỉ cần khai cấu hình, không viết mã |

**Điều kiện vào:** PQ4, PQ5, **PQ11** xong (bộ máy duyệt đọc quyền và phạm vi), DB10 đến DB12 xong, và **DB15** xong (vai tương đối cần biết pháp nhân và phòng ban của người nộp — mà phòng ban phải là `dept_id`, không phải chuỗi tên).

**Phòng ban ở đây là một cấp phẳng**, theo chốt Đ7. DUY2 tìm "trưởng phòng của người nộp" bằng cột `manager_id` của đúng phòng đó, không đi ngược lên phòng cha. Không có phòng nào ở trên để đi ngược lên — đó là ý của quyết định.

**Kiểm chứng cả bước:** DUY5 chạy thật ổn định, và thêm được một loại chứng từ mới bằng cấu hình trong dưới một giờ.

---

## 7. Bước 4 — HRM

Làm theo bản mô tả nghiệp vụ và bảng chốt phạm vi ở bước 0. Danh sách dưới đây là khung; đầu mục nào bị loại ở bảng chốt phạm vi thì bỏ dòng đó.

**Tin tốt:** `tab_employee` đã có sẵn công ty, phòng ban, và đã nối với tài khoản đăng nhập. `tab_department` cũng đã có sẵn cột `parent` và `manager_id` từ trước — nhưng theo chốt Đ7, **`parent` để nguyên không khai thác trong năm nay**.

| Mã | Việc | Xong là thế nào |
|---|---|---|
| HR1 | **Bảng mới cho hồ sơ nhân sự mở rộng** — trường lấy từ biểu mẫu thật thu được ở bước 0. Không sửa `tab_employee`, chỉ thêm bảng con. **Phòng ban giữ một cấp phẳng** (chốt Đ7). Trường nhạy cảm (căn cước, tài khoản ngân hàng, ngày sinh) phải khai vào danh sách của **PQ12** ngay khi tạo bảng, không để sau | Migration chỉ thêm bảng; không trường nhạy cảm nào ra khỏi API mà chưa qua bộ lọc PQ12 |
| HR2 | **Quá trình công tác**: vào công ty, đổi phòng ban, đổi chức danh, nghỉ việc | Xem được lịch sử của một người |
| HR3 | **Hợp đồng lao động**: loại, thời hạn, ngày ký, ngày hết hạn, cảnh báo sắp hết hạn. **Điều kiện vào: PQ12 xong** — bảng này chứa mức lương, thiết kế nó trước khi có phân quyền mức trường là phải làm lại | Có danh sách hợp đồng sắp hết hạn, và mức lương chỉ hiện với người được cấp quyền trường đó |
| HR4 | **Giấy tờ và bằng cấp** — dùng lại phần đính kèm sẵn có, không viết mới | Tải lên xem được, phân quyền được |
| HR5 | **Danh mục HRM**: chức danh, loại hợp đồng, loại nghỉ phép, quan hệ người phụ thuộc | Sửa trên giao diện, không phải sửa code |
| HR6 | **Phân quyền HRM**: nhân viên chỉ thấy hồ sơ mình, trưởng phòng thấy **đúng phòng mình** (một cấp, không lan xuống phòng con — chốt Đ7), HR thấy hết, lương chỉ vài người và đi qua PQ12 | Kiểm thử tự động chứng minh được, gồm cả ca "mở hồ sơ bằng id trực tiếp" và ca "xuất tệp" |
| ~~HR7~~ | **Đã chuyển ra [bước 3b](#6b-bước-3b--bộ-máy-duyệt-dùng-chung), thành DUY1–DUY6.** Không phải việc của HRM, và phải xong trước HRM | Xem bước 3b |
| HR8 | **Nghỉ phép**: đăng ký, duyệt, số ngày còn lại, lịch nghỉ của phòng | Nhân viên tự nộp, trưởng phòng duyệt trên web |
| HR9 | **Tự phục vụ**: nhân viên tự xem và sửa thông tin của mình, tự nộp đơn, tự xem hợp đồng | Phần làm HRM có ích với người dùng cuối, không chỉ với phòng Nhân sự |
| HR10 | **Chấm công** — chỉ làm nếu bảng chốt phạm vi nói là có | Nếu có máy chấm công thì đây là ca dùng thật đầu tiên của webhook đi vào |
| HR11 | **Báo cáo nhân sự**: biến động nhân sự, cơ cấu phòng ban, hợp đồng sắp hết hạn, phép còn lại | |
| HR12 | **Nhập dữ liệu nhân sự hiện có và đối chiếu** | Số trên hệ thống khớp số phòng Nhân sự đang giữ |
| HR13 | **Một vòng quay lại sửa nền.** HRM là phân hệ đầu tiên chạy qua khuôn mới, mọi thiếu sót của bước 1, 2, 3 sẽ lộ ra ở đây | Dự trù sẵn, không phải phát sinh |

**Lưu ý về lương và bảo hiểm:** nếu bảng chốt phạm vi nói là làm, phần này phải bám đúng quy định hiện hành của Việt Nam, và phải có người ngoài đội phần mềm xác nhận cách tính. Đây là loại tính sai thì nhân viên chịu thiệt và công ty chịu trách nhiệm.

---

## 8. Bước 5 — Module quản lý webhook

**Hiện trạng: không có một dòng code nào.** Đã tìm cả backend lẫn frontend — không có webhook, không có khóa API, không có tích hợp ra ngoài. Nhóm này làm từ số 0.

**Nguyên tắc của bước này: viết hạ tầng trước, chưa cần biết nối với ai.** Đối tượng đồng bộ đầu tiên chưa chốt (xem [`04` Danh mục chờ quyết](./04-danh-muc-cho.md), mục C4). Ứng viên gần nhất là đồng bộ đơn hàng. Nhưng phần lõi WH1 đến WH11 không phụ thuộc câu trả lời đó — làm xong rồi nối với ai cũng được.

**Bản 1.1 bỏ ràng buộc "bước 5 làm sau cùng".** Nhóm này **không chặn HRM và không bị HRM chặn** — nó chỉ cần FE1 (danh mục sự kiện sinh từ khai báo phân hệ), HT1 (nhật ký lỗi) và HT4 (hàng đợi). Xếp nó ở cuối là một lựa chọn về lịch chứ không phải ràng buộc kỹ thuật, và lựa chọn đó có giá: việc nào xếp cuối thì việc đó bị cắt đầu tiên khi trượt lịch. Nếu có người rảnh trong lúc chờ khảo sát nghiệp vụ hoặc chờ chốt phạm vi HRM, đây là nhóm nên chen vào — nhất là WH1 đến WH4, không phụ thuộc gì ngoài FE1.

**Nền có sẵn dùng được:** bảng nhật ký thao tác `tab_audit_log` đã tổng quát (entity, id, hành động) nên gắn phát sự kiện vào đó là hợp lý. Celery đã dựng và đang chạy thật (sao lưu R2 hai lần mỗi ngày) nên có sẵn hàng đợi nền.

### 8.1 Phần lõi — làm trong năm nay

| Mã | Việc | Xong là thế nào |
|---|---|---|
| WH1 | **Bảng và màn hình quản lý endpoint**: tên, URL, khóa bí mật, bật tắt, người phụ trách, phân hệ | Thêm sửa xóa trên giao diện |
| WH2 | **Danh mục sự kiện** sinh tự động từ khai báo phân hệ và entity (FE1). Ví dụ `thu_mua.don_mua_hang.duyet`, `nhan_su.nghi_phep.tao` | Không gõ tay danh sách sự kiện |
| WH3 | **Đăng ký: endpoint này nhận sự kiện nào** — chọn theo phân hệ, theo entity, hoặc theo từng sự kiện | Chọn được trên giao diện |
| WH4 | **Phát sự kiện** từ chỗ ghi nhật ký thao tác. Kèm dữ liệu trước và sau khi đổi | Sửa một đơn hàng là có sự kiện |
| WH5 | **Hàng đợi gửi** qua Celery, hàng đợi riêng, không dùng chung với sao lưu | Bên nhận chậm không làm chậm hệ thống |
| WH6 | **Thử lại có giãn cách** khi bên nhận lỗi: 1 phút, 5 phút, 30 phút, 2 giờ, 6 giờ rồi bỏ | Bên nhận sập nửa ngày vẫn không mất dữ liệu |
| WH7 | **Ký chữ ký HMAC** kèm dấu thời gian, chống phát lại | Bên nhận xác minh được gói tin đúng là từ mình |
| WH8 | **Nhật ký gửi**: mỗi lần gửi lưu nội dung, phản hồi, mã lỗi, số lần thử. Màn hình xem, lọc, và **nút gửi lại bằng tay** | Đối tác kêu thiếu dữ liệu là tra ra ngay |
| WH9 | **Hàng chờ chết và cảnh báo**: endpoint hỏng liên tục thì tự tắt và báo người phụ trách | Không có gói tin nào chết im lặng |
| WH10 | **Màn hình thử**: bắn một sự kiện mẫu tới endpoint để đối tác test | Đối tác tự test được, không phải nhờ |
| WH11 | **Phân quyền cho module webhook** — quyền nguy hiểm, vì ai lập được endpoint là đọc được dữ liệu ra ngoài | Chỉ vài tài khoản có quyền |

### 8.2 Phần đi kèm — làm nốt nếu còn thời gian

| Mã | Việc | Ghi chú |
|---|---|---|
| WH12 | **Khóa API cho hệ thống ngoài gọi vào**: tạo, thu hồi, giới hạn phạm vi theo entity và hành động, hạn dùng, nhật ký sử dụng | Dùng lại đúng ma trận quyền hiện có, **không dựng hệ quyền thứ hai** |
| WH13 | **Tách API công khai có đánh số phiên bản** (`/api/v1/...`). API hiện tại là API nội bộ của giao diện, đổi lúc nào cũng được. Một khi bên ngoài đã gọi thì không đổi được nữa | **Làm trước khi đối tác đầu tiên gọi, không phải sau** |
| WH15 | **Tài liệu cho đối tác** và môi trường thử | Không có thì mỗi đối tác tốn một tuần hỗ trợ |

### 8.3 Để sang năm

| Mã | Việc | Vì sao hoãn |
|---|---|---|
| WH14 | Webhook đi vào | Chưa có ca dùng chốt. Nếu HRM làm chấm công thì đây là ca đầu tiên |
| WH16 | Đồng bộ danh mục một chiều | Chưa chốt đồng bộ với hệ thống nào |
| WH17 | Màn hình đối chiếu lệch | Bắt buộc phải có **trước** khi cho ghi hai chiều |
| WH18 | Chốt quy tắc bên nào thắng khi lệch | Quyết định nghiệp vụ, không phải kỹ thuật |

**Đồng bộ hai chiều không làm trong năm nay.** Làm hai chiều mà chưa có WH17 và WH18 là hỏng dữ liệu cả hai bên.

---

## 9. Nhóm chạy song song — tối ưu hạ tầng

Không ai nhìn thấy nhóm này. Thiếu thì mọi phân hệ đều chết.

| Mã | Việc | Vì sao cần |
|---|---|---|
| HT1 | **Nhật ký lỗi tập trung và cảnh báo** | **Bắt buộc có trước bước 5.** Lỗi đồng bộ là loại lỗi không ai thấy cho tới lúc số liệu đã sai một tháng |
| HT2 | **Chạy kiểm thử tự động mỗi lần đẩy code.** Hiện chạy tay bằng lệnh trong Docker | Bộ kiểm thử không tự chạy là bộ kiểm thử sẽ mục |
| HT3 | **Giám sát cơ bản**: CPU, bộ nhớ, dung lượng đĩa, thời gian phản hồi, kèm cảnh báo | Hiện chỉ biết hỏng khi người dùng gọi điện |
| HT4 | **Chuẩn hóa hàng đợi nền.** Celery đang chạy thật nhưng thư mục tác vụ mới chỉ có một tác vụ thử. Cần hàng đợi riêng theo loại việc, số worker rõ ràng, màn hình xem việc lỗi | Nền của WH5 và WH6 |
| HT5 | **Kiểm thử phục hồi sao lưu.** Sao lưu R2 chạy hai lần mỗi ngày nhưng **chưa ai thử phục hồi bao giờ** | Bản sao lưu chưa phục hồi thử là bản sao lưu chưa tồn tại |
| HT6 | **Gói quy trình phát hành thành một lệnh.** Hiện deploy prod phải nhớ chỉ đúng file cấu hình, quên là lỗi 502; và phải nhớ dựng lại worker khi đổi backend | Bỏ được một loại lỗi do người |
| HT7 | **Đưa công cụ đồng bộ dữ liệu giữa môi trường vào repo.** Hiện là script tay chưa commit, nằm trên máy một người | Đang là điểm phụ thuộc vào một người |
| HT8 | **Rà truy vấn chậm, thêm chỉ mục.** Chỉ thêm, hợp quy tắc 1 | Thêm phân hệ là thêm tải |
| HT9 | **Gộp mốc migration.** 75 file cho một sản phẩm chưa tròn năm; năm phân hệ thì thành ba trăm | Làm khi rảnh, không gấp |
| HT10 | **Rà bảo mật đầu vào.** Đã có tiền lệ lỗi ở phần nội dung ngoài của Help Center | Webhook mở thêm cửa vào, phải rà trước |
| HT11 | **Rà biến môi trường và cấu hình theo môi trường** | Dev và prod đang dùng chung một cụm cơ sở dữ liệu, cách ly bằng tiền tố |
| HT12 | **Kiểm thử tải sau khi thêm tầng phân hệ** | Lưới biểu tượng gọi thêm một lượt kiểm tra quyền cho mỗi phân hệ |
| **HT13** *(thêm ở bản 1.5)* | **Middleware vòng đời yêu cầu, và nhật ký truy cập.** Toàn hệ hiện có **đúng một middleware là CORS**. Làm bốn thứ trong một lượt: (a) **mã định danh request** sinh ở đầu mỗi lượt, trả về trong header và trong mọi phản hồi lỗi, ghi vào mọi dòng nhật ký; (b) **bộ xử lý lỗi chưa bắt** — hiện lỗi 500 trả `{"detail": ...}`, **sai vỏ envelope `{success, message, data}` mà giao diện đang dựa vào**, nên người dùng gặp lỗi 500 thì màn hình hỏng chứ không hiện được thông báo; (c) **nhật ký truy cập** — ai gọi endpoint nào, lúc nào, trả bao nhiêu dòng, riêng endpoint xuất tệp ghi thêm bộ lọc; (d) **nạp `SlowAPIMiddleware`** để `default_limits=["300/minute"]` có hiệu lực thật, hoặc **bỏ hẳn dòng khai đó** — hiện nó là **cấu hình chết**, khai rồi mà middleware không nạp nên thực tế chỉ **4/265 route** bị giới hạn, người đọc mã lại tưởng cả hệ được bảo vệ | **(b) là lỗi người dùng đang chịu hôm nay.** **(c) chặn PQ11(b)**: chưa biết ai đang xuất dữ liệu thì bật chặn quyền `export` là cắt việc người ta mà không báo trước. Và **(a)** là điều kiện cần của HT1 — không có mã định danh thì nhật ký lỗi tập trung không nối được các dòng của cùng một lượt gọi |

---

## 10. Lịch từ nay đến 31/12/2026

Bốn tháng rưỡi. Chưa gán người, chưa gán người-ngày.

> **Đọc lịch này thế nào.** Chừng nào [`04` C15](./04-danh-muc-cho.md) chưa được trả lời — ai làm, và có được tách khỏi luồng xử lý yêu cầu thay đổi của Thu mua không — thì bảng dưới là **thứ tự**, không phải **ngày**. Thu mua đang chạy thật ngốn xấp xỉ một yêu cầu thay đổi mỗi ngày, và bốn tháng rưỡi dưới đây chưa trừ phần đó ra.

| Giai đoạn | Việc chính | Người dùng thấy gì |
|---|---|---|
| **Ngay bây giờ** | **PQ11(a)(c)(d), PQ13, PQ14 — vá những chỗ đang hở.** Không chờ duyệt lộ trình, không chờ bước 0, không phụ thuộc gì. Cỡ vài ngày công. **Kèm HT13 khởi động ngay** vì nhật ký truy cập của nó phải chạy đủ hai tuần trước khi bật được PQ11(b) | Không thấy gì — trừ một thứ người dùng đang chịu hôm nay mà sẽ hết: lỗi 500 hiện làm hỏng màn hình vì trả sai vỏ envelope, HT13(b) vá chỗ đó. Còn lại, đây là những chỗ **đang gây hại thật** ở thời điểm viết |
| **Nửa sau T8** | Bước 0: lập danh mục nghiệp vụ toàn công ty, bắt đầu phỏng vấn Nhân sự theo bộ câu hỏi `03`. DB1, DB2, DB3, DB4, DB12. **PQ9, PQ10** (không phụ thuộc gì, làm được ngay). **PQ11(b) — bật chặn quyền `export` sau khi đã đọc hai tuần nhật ký truy cập và cấp quyền cho đúng người đang xuất.** HT1, HT2 | Không thấy gì. Riêng PQ11(b): người đang xuất tệp mà chưa được cấp quyền sẽ bị chặn — nên phải cấp trước, chặn sau |
| **Nửa đầu T9** | Bước 0: xong bản mô tả nghiệp vụ Nhân sự, **chốt phạm vi HRM có duyệt**, **chốt DB13** (một người nhiều pháp nhân). **Chốt hợp đồng dữ liệu và bảng chia entity ở [`07`](./07-kien-truc-vo-erp.md) ngay ngày đầu**, rồi FE15, FE13, FE1, FE2, FE3. DB7, **DB14**. **LC1** (không phụ thuộc gì, và mọi mã viết sau đều hưởng) | Có bản mô tả nghiệp vụ và bảng phạm vi ký duyệt |
| **Nửa sau T9** | FE4, FE5, FE6, FE8, FE9, **FE14**, FE10 (gồm cả FE10a–FE10e). HT3. **WH1–WH4 nếu có người rảnh** | **Lưới biểu tượng chạy**, có đủ ô Help Center và Project-M. Thu mua bên trong vẫn y nguyên |
| **Nửa đầu T10** | FE11, FE12 — đổi giao diện thật cho người dùng. PQ1, PQ2, PQ3 | Người dùng bắt đầu dùng giao diện mới |
| **Nửa sau T10** | PQ4, PQ5, PQ6, PQ7, PQ8, **PQ12**. **DB10 đợt 1, DB11, DB15**. **LC6, LC2, LC3, LC5** — theo đúng thứ tự đó, và LC2 làm sau PQ4, PQ5. DB5, DB9. HT4 | Không thấy gì. Đây là nền cho HRM |
| **Nửa đầu T11** | **Bước 3b: DUY1 đến DUY6** — bộ máy duyệt dùng chung, gồm cả phép thử chuyển một loại chứng từ Thu mua sang | Người dùng Thu mua không nhận ra gì đổi. Đó chính là tiêu chí đạt |
| **Nửa sau T11** | HR1 đến HR6. HT5, HT8 | Hồ sơ nhân sự xem được |
| **Nửa đầu T12** | HR8, HR9, HR11, HR12. WH5 đến WH11. HT10 | **HRM bản 1 dùng được.** Module webhook chạy |
| **Nửa sau T12** | WH12, WH13, WH15. **LC4**. HR13 (vòng sửa nền). HT6, HT7, HT12. DB6 | Hệ thống ngoài nối được vào |
| **Xuyên suốt** | Bảo trì và sửa lỗi Thu mua đang chạy thật — **phần công này chưa được trừ khỏi lịch trên, xem C15**. **Chuyển dần 259 chỗ ném lỗi cũ sang LC1** theo từng module đang sờ vào. **DB10 các đợt sau** (42 bảng, chia theo module). HT9, HT11, DB8 khi có chỗ trống | |

**Lịch này chặt hơn bản 1.0 một nhịp**, vì bước 3b chiếm nửa đầu T11. Nếu trượt thì thứ tự cắt là: WH12, WH13, WH15 cắt trước; rồi **phần mở rộng của LC4** (phần **vá** của LC4 thì không cắt được, xem mục 11); rồi HR11; **không cắt DUY1–DUY6, không cắt PQ4, PQ5, PQ9, PQ10, PQ11, PQ12, PQ13, PQ14, không cắt HT13, và không cắt LC1, LC6, LC2, LC3, LC5** — cắt nhóm sau là HRM chạy trên nền hở, hoặc hơn mười module HRM viết ra rồi phải dọn lại.

**Nửa sau T10 là nhịp nặng nhất của cả lộ trình** — vừa vá quyền, vừa thêm cột pháp nhân, vừa đổi phạm vi phòng ban, vừa dựng lớp dùng chung. Bản 1.2 đã đẩy DB8 sang "xuyên suốt" để bớt tải; bản 1.4 đẩy tiếp **DB10 thành nhiều đợt** vì khối lượng thật là 42 bảng chứ không phải 17. Nếu vẫn quá thì đẩy tiếp HT4 và DB5; **không đẩy PQ4, PQ5, PQ12, LC6, LC2, LC3, LC5**, vì cả bốn nhóm này đều chặn HRM.

**Để sang năm sau, ghi rõ ngay từ bây giờ:** HR10 chấm công (nếu chốt là làm), WH14, WH16 đến WH18, và toàn bộ MFM — xem [`02` Dài hạn](./02-dai-han.md).

**Hai mốc còn thiếu:** ngày đổi giao diện cho người dùng thật trong T10 ([`04` C3](./04-danh-muc-cho.md)), và **nhân lực làm lộ trình này** ([`04` C15](./04-danh-muc-cho.md)). Mốc thứ hai chặn toàn bộ bảng trên.

---

## 11. Thứ tự không đổi được

| Phải xong trước | Mới làm được | Vì sao |
|---|---|---|
| Bảng chốt phạm vi HRM (bước 0) | Toàn bộ bước 4 | Không có mô tả nghiệp vụ thì viết mò |
| FE1 (khai báo phân hệ) | FE2 đến FE10, FE14, PQ1 đến PQ3, WH2 | Mọi thứ đều đọc từ một chỗ này |
| **Hợp đồng dữ liệu `/api/me/modules` + bảng chia entity** ([`07`](./07-kien-truc-vo-erp.md) mục 4.3 và mục 5) | **FE15, rồi toàn bộ phần giao diện của bước 2** | Chốt sau khi đã viết là phải sửa cả lưới, cả menu, cả phân quyền. Đây là việc của một buổi, không phải một tuần |
| **PQ11(a)(c)(d) · PQ13 · PQ14** (vá những chỗ đang hở) | **Không chặn việc nào — chúng chặn chính hôm nay** | Không đợi ai. Hồ sơ nhân sự đang đọc được bằng cách đoán id và xuất được cả bảng; tệp đính kèm tải được không cần đăng nhập; nhật ký thao tác đọc tự do |
| **HT13(c)** (nhật ký truy cập) + hai tuần thu thập | **PQ11(b)** (bật chặn quyền `export`) | Chỉ 1/11 endpoint xuất đang kiểm quyền, nghĩa là **không ai biết mười endpoint kia đang phục vụ ai**. Bật chặn trước là cắt việc người ta mà không biết trước là cắt vào ai |
| **HT13(a)** (mã định danh request) | **HT1** (nhật ký lỗi tập trung), **LC1** (`request_id` trong vỏ lỗi) | Không có mã định danh thì các dòng nhật ký của cùng một lượt gọi không nối lại được, và `request_id` trong phản hồi lỗi không có gì để điền |
| **LC4 phần vá** (bộ sinh router có phạm vi) | **LC4 phần mở rộng, và mọi module kế thừa nó** | Bộ sinh router hiện **không áp phạm vi ở bất kỳ đâu**. Cho module kế thừa trước khi vá là nhân một lỗ hổng ở 1 chỗ thành lỗ hổng ở 36 chỗ |
| **LC1 + LC6** (mã lỗi chuẩn, gói ngữ cảnh) | **LC2, LC3** | LC2 và LC3 đứng lên trên ngữ cảnh yêu cầu — không có ngữ cảnh thì hàm danh sách không tự áp được phạm vi, phải truyền tay, mà truyền tay thì quên được |
| **PQ4 + PQ5** (vá lỗ hổng phạm vi) | **HR6, và HRM có dữ liệu thật** | Không vá thì HRM lộ lương |
| **PQ12** (phân quyền mức trường) | **HR1 thiết kế bảng, và HR3 hợp đồng lao động** | Bảng hợp đồng chứa mức lương. Thiết kế trước khi có tầng cột là phải làm lại cả API lẫn giao diện |
| **DB15** (phòng ban theo `dept_id`) | **DUY2** (vai duyệt tương đối), **HR6** | Vai "trưởng phòng của người nộp" mà phòng ban là chuỗi tên thì đổi tên phòng là quy trình duyệt đứt |
| **PQ9 + PQ10** (thu hồi token, bộ đệm dùng chung) | **HRM có dữ liệu thật** | Khóa tài khoản chưa có hiệu lực thật, và rút quyền chỉ tác dụng ở một trong hai tiến trình |
| **DB13** (một hồ sơ hay nhiều hồ sơ) | **HR1** | Không sửa được sau khi đã nhập dữ liệu nhân sự |
| **DB10 đợt bảng nhân sự + DB12** (pháp nhân, quy tắc dùng chung) | DUY2, HR1 | Vai duyệt tương đối cần biết pháp nhân; hồ sơ nhân sự thuộc pháp nhân nào. **Không cần xong cả 42 bảng** — chỉ cần xong nhóm bảng mà HRM đụng tới |
| **DUY1 đến DUY6** (bộ máy duyệt chung) | HR8 nghỉ phép, và mọi quyết định nhân sự | Không thì sinh luồng duyệt viết tay thứ hai, thứ ba, rồi hàng chục |
| **PQ4 + PQ5** (phạm vi fail-closed) | **LC2** (hàm danh sách chuẩn) | LC2 áp phạm vi làm mặc định — phải có hành vi đúng trước rồi mới gói lại |
| **LC1, LC6, LC2, LC3, LC5** (lớp dùng chung) | **HR1, và mọi module HRM** | Hơn mười module HRM viết trên lớp này. Viết trước rồi mới gom là dọn lại mã đang chạy thật |
| **DB3** (khai enum) | **DB14** (sinh tệp cho giao diện) | Không có tệp nguồn thì không sinh được |
| HT1 (nhật ký lỗi) | Toàn bộ bước 5 | Lỗi tích hợp không cảnh báo là lỗi im lặng |
| HT4 (hàng đợi) | WH5, WH6 | Không hàng đợi thì webhook không thử lại được |
| WH13 (API có phiên bản) | Đối tác đầu tiên gọi API | Đã gọi rồi thì không đổi được nữa |
| DB6 (sản phẩm cha) | BOM của MFM | Sang năm, nhưng bảng phải có trước |

---

## 12. Không làm trong năm nay

| Không làm | Vì sao |
|---|---|
| Khảo sát chi tiết MFM, CRM, Kế toán | Bước 0 chỉ lập danh mục đầu mục cho các phân hệ này |
| MFM chạy thật | Chỉ kịp làm bảng sản phẩm cha (DB6) làm nền |
| CRM, Kế toán đầy đủ | Xem `02` Dài hạn |
| Đồng bộ dữ liệu hai chiều | Phải có WH17 và WH18 trước |
| Sửa trạng thái tiếng Việt trong **bảng cũ** | Quy tắc 1. Bảng **mới** thì bắt buộc dùng số ngay từ đầu (DB3). Kế hoạch sáu bước chuyển 11 cột cũ đã viết sẵn ở [`06` mục 4](./06-lo-trinh-nen-tang-va-hrm.md), làm sang năm — trừ khi [`04` C12](./04-danh-muc-cho.md) chốt khác |
| Đổi tên cột `created_by` | Quy tắc 1 |
| Đa ngôn ngữ, ứng dụng di động riêng, đổi khung công nghệ | Ngoài phạm vi |
| Viết lại toàn bộ giao diện | Chỉ đổi tầng điều hướng, màn hình bên trong giữ nguyên |
| **Tách kho mã Thu mua thành sản phẩm ERP riêng** | Đã cân nhắc và loại ngày 12/08/2026. Bốn lý do ở [`07` mục 1](./07-kien-truc-vo-erp.md). Vỏ ERP là lớp thêm phía trên, không cần thay ruột |
| **Đổi đường dẫn URL của Thu mua** | `notification.link` đang chứa hàng nghìn đường dẫn thật. Xem FE5 |
| **Cây phòng ban nhiều cấp** | Chốt Đ7 ngày 12/08/2026. `tab_department` **đã có sẵn** cột `parent` nên làm cây không tốn mấy — vấn đề không nằm ở công. Có cây thật thì "phạm vi phòng ban" buộc phải đổi nghĩa thành "phòng mình và các phòng con", và **mọi trưởng phòng cấp trên trong Thu mua đột nhiên thấy nhiều chứng từ hơn hôm trước**. Đó là đổi hành vi hệ đang chạy thật, sinh ra từ một việc của HRM — vi phạm tinh thần quy tắc 2. Cột `parent` để nguyên, không khai thác |
| **Sửa cột `department` kiểu chuỗi trên chứng từ cũ** | DB15 **chỉ thêm cột `dept_id`**, giữ cột tên chạy song song. Bỏ cột chuỗi cũ là việc sang năm, cùng đợt với 11 cột trạng thái ở [`06` mục 4](./06-lo-trinh-nen-tang-va-hrm.md) |

---

## 13. Mười rủi ro

| # | Rủi ro | Xử lý thế nào |
|---|---|---|
| R1 | **Khảo sát nghiệp vụ phụ thuộc bộ phận khác trả lời.** File `ke-hoach/01` mục 5 đã ghi: chưa hạn nào chờ bộ phận khác được giữ đúng | Bước 0 phải có tên người và ngày cụ thể cho từng buổi phỏng vấn. Quá hạn thì ghi lại là chặn tiến độ, không im lặng chờ |
| R2 | **Đổi vào lưới biểu tượng là đổi thói quen hằng ngày của toàn bộ người đang dùng Thu mua** | Bản 1.3 rút phần lớn rủi ro này bằng cách **không đổi đường dẫn** và bằng **FE14** — người chỉ dùng Thu mua vào thẳng như cũ, không thấy lưới. Còn lại: FE11 làm lại hướng dẫn, FE12 báo trước, FE6 kiểm link cũ. Ba việc này không được cắt |
| R3 | **HRM là dữ liệu nhạy cảm nhất, lại làm trước, trên nền quyền còn chưa vá.** Bản 1.4 phải sửa cách nói: đây **không còn là rủi ro tương lai**. Kiểu quên gây ra nó **đã xảy ra rồi** trên chính `tab_employee`, ở thời điểm bảng đó mới chỉ chứa họ tên và phòng ban | PQ4, PQ5, **PQ9, PQ10, PQ12** là điều kiện chặn; **PQ11 làm ngay, không đợi lịch**. Nếu trượt lịch thì HRM lùi theo, không chạy song song |
| R5 | **Bước 3b bị coi là "việc kỹ thuật, để sau"** vì người dùng không nhìn thấy nó. Đây là rủi ro thật: ở bản 1.0 nó chỉ là một dòng trong 13 dòng của HRM | Tiêu chí đạt của DUY5 là chuyển được một loại chứng từ **đang chạy thật** sang bộ máy mới. Đó là thứ trình bày được với người ngoài đội phần mềm, nên khó bị cắt |
| R6 | **Cột pháp nhân điền sai cho dòng cũ.** Gán hết vào một pháp nhân mặc định là sai vĩnh viễn | DB10 bắt buộc để rỗng khi không suy được, kèm bảng liệt kê số dòng và cách xử lý từng nhóm. Rỗng thì sửa sau được, gán bừa thì không |
| R7 | **LC1–LC6 bị hoãn sang sau HRM** vì "làm HRM trước cho kịp, gom mã sau cũng được". Đây là rủi ro thật vì nhóm này người dùng không nhìn thấy, và hoãn nó thì tháng sau vẫn chạy bình thường — chỉ là hơn mười module HRM đã viết xong theo cách cũ | LC1, LC6, LC2, LC3, LC5 nằm trong bảng thứ tự không đổi được, chặn HR1. Tiêu chí đạt của LC5 là **viết một module danh mục mới dưới 50 dòng** — đo được, trình bày được, nên khó bị bỏ qua trong lặng lẽ |
| R4 | **Giữ nguyên DB cũ nghĩa là nợ kỹ thuật được dời chứ không mất** | Chấp nhận có ý thức. DB7 phải ghi rõ vào từ điển dữ liệu để người mới không tưởng đó là chuẩn |
| **R8** | **Lịch chưa trừ phần bảo trì Thu mua.** Bốn tháng rưỡi ở mục 10 được xếp như thể đội chỉ làm ERP. Thực tế đo được: CR-034 đến CR-061 rơi gọn trong khoảng năm ngày làm việc — **xấp xỉ một yêu cầu thay đổi mỗi ngày**, và Thu mua không dừng được | [`04` C15](./04-danh-muc-cho.md). Trước khi chốt bất kỳ ngày nào, phải trả lời: ai làm, và người đó có được tách khỏi luồng xử lý yêu cầu thay đổi không. Chưa trả lời thì mục 10 đọc là **thứ tự**, không phải **ngày** |
| **R9** | **Ước lượng dựa trên số đếm sai đơn vị.** Bản 1.1 ghi "17 bảng thiếu cột pháp nhân", thực tế là **42** — vì đếm theo tệp model chứ không theo bảng. Sai một lần thì có thể sai lần nữa ở chỗ khác | Quy tắc từ bản 1.4: **mọi số liệu về bảng, cột, phạm vi phải đếm ở mức bảng**, và ghi rõ lệnh đếm vào tài liệu để người sau kiểm lại được. [`06` bản 2.1](./06-lo-trinh-nen-tang-va-hrm.md) đã đếm lại toàn bộ và ghi cả những chỗ **đếm đúng** để biết phần nào còn tin được. Bản 1.5 sửa thêm một chỗ nữa theo đúng quy tắc này: LC1 ghi `error()` "gọi 2 lần trong 36 module", thật ra là **0** |
| **R10** *(thêm ở bản 1.5)* | **Cấu hình bảo mật có màn hình nhưng không có tác dụng.** Loại lỗi này **không có dấu hiệu sớm nào cả** — người cấp quyền thấy màn hình cho chọn, bấm lưu, hệ báo lưu thành công, và tin là đã chặn. Đã có hai ca thật, tìm ra ngày 12/08/2026: cấu hình loại trừ phòng ban trên dữ liệu nhân sự **lưu được mà không sinh mệnh đề truy vấn nào**; và `default_limits` của bộ giới hạn tần suất **khai rồi mà middleware không được nạp**. Nguy hơn không có tính năng, vì không có thì người ta còn biết là không có | Hai việc. **Một:** mọi cấu hình bảo mật phải có **một bài kiểm chứng minh nó có tác dụng** — không phải chứng minh nó lưu được. Vào PQ6 và HT2. **Hai:** đổi mặc định của mọi chỗ tra bảng cấu hình: **tra khóa không thấy thì báo lỗi, không bỏ qua im lặng**. Chính là fail-closed của PQ4 áp cho cấu hình chứ không chỉ cho dữ liệu |
