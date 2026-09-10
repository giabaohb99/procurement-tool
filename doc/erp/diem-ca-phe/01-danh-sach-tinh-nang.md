# PHÂN HỆ ĐIỂM CÀ PHÊ (POS365) — DANH SÁCH TÍNH NĂNG

> **Mã tài liệu:** ERP-CF-01 · **Bản:** 1.0 — 08/09/2026 · **Loại:** KẾ HOẠCH (chế độ A — công cụ chưa có, liệt kê tính năng cần có)
> **Nguồn quyết định:** [`../17-ke-hoach-trien-khai-pos365-diem-ca-phe.md`](../17-ke-hoach-trien-khai-pos365-diem-ca-phe.md) (bản thực thi 07/09/2026) và [`../09-phuc-loi-diem-va-pos.md`](../09-phuc-loi-diem-va-pos.md) (bản định hướng 12/08/2026). Chỗ nào hai bản lệch nhau thì lấy `17`.
> **Phương án đã chốt:** ERP là **sổ cái duy nhất**; quầy tiêu điểm bằng **phương thức thanh toán "Trừ điểm"** trên POS365; điểm **reset đầu mỗi tháng theo cấp nhân sự**, không cộng dồn.

## Cách đọc bảng

| Cột | Nghĩa |
|---|---|
| Mã | Mã tính năng ổn định — cấp một lần, không đổi số, dùng để nhắc trong lộ trình ([`06-lo-trinh-phase.md`](./06-lo-trinh-phase.md)) |
| Nội dung | Làm gì · luật/ranh giới (bôi đậm) · vì sao |
| Bản | `1` = bản đầu phải có · `2` = làm sau · `?` = chờ trả lời câu hỏi còn mở (ghi rõ chờ gì) |
| Có sẵn | `[x]` tận dụng nguyên · `[~]` có khuôn phải sửa · `[ ]` làm mới |

Tổng: **31 tính năng**, trong đó **22 thuộc bản đầu**.

---

## Nhóm N — Việc nền & kết nối

> Không có nhóm này thì mọi nhóm sau chỉ chạy trên giấy: chưa có phiên API và cầu dao an toàn thì một lần chạy thử ở dev là một lần bắn dữ liệu vào quán thật.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| N-01 | Cấu hình kết nối POS365 | Biến môi trường: `POS365_BASE_URL` (dạng `https://<cửa-hàng>.pos365.vn`), `POS365_USERNAME/PASSWORD` của **tài khoản API riêng** (không dùng tài khoản của người — người đổi mật khẩu là tác vụ nền chết im lặng), `POS365_PAYMENT_ACCOUNT_ID`. **Mật khẩu không vào mã nguồn, không vào tệp cấu hình chung** (luật A4 của `09` §8) | 1 | [~] khuôn `core/config.py` |
| N-02 | Cầu dao `POS365_HARD_OFF` | Cờ tắt cứng, **mặc định BẬT ở mọi môi trường không phải prod**; khi bật, client từ chối MỌI lời gọi HTTP ra POS365 và có test khẳng định điều đó. Vì hệ đang có hai môi trường chung một máy chủ DB — đã từng phải cách ly email đúng kiểu này (A1 của `09` §8) | 1 | [~] khuôn cờ email |
| N-03 | Phiên làm việc POS365 | Đăng nhập `GET /api/auth/credentials` lấy `SessionId`, cache trong tiến trình, gửi bằng cookie `ss-id`; **gặp 401 thì đăng nhập lại đúng MỘT lần rồi mới lỗi** — không login bão làm khóa tài khoản. Chi tiết ở [`03-tich-hop-pos365.md`](./03-tich-hop-pos365.md) §2 | 1 | [ ] |
| N-04 | Tài khoản thanh toán "Trừ điểm" | Dựng tay một *tài khoản thanh toán* trên giao diện POS365, đọc `AccountId` bằng `AccountList`, ghi vào N-01. **`AccountId` này là hằng số nhận diện của TOÀN BỘ tích hợp** — đổi nó là mọi đơn cũ hết lọc được. Thao tác một lần, có ghi vào tài liệu vận hành | 1 | [ ] |
| N-05 | Nền dữ liệu & khai báo hệ thống | 5 bảng `tab_coffee_*`/`tab_pos_*` + migration; IntEnum vào `status_catalog.py` + `code_sets.py` + chạy `gen_status_ts.py`; 4 entity vào `ENTITIES` + `SCOPE_FIELDS` + seed cả hai bản. **Thiếu khai scope là test `test_pham_vi_khai_du_b07.py` đỏ suite** — luật B-07 sẵn có, không phải luật mới | 1 | [~] khuôn W0 của `cong-viec` |

## Nhóm A — Chính sách & cấp phát điểm

> Trái tim nghiệp vụ: ai được bao nhiêu điểm, cấp lúc nào, thu lúc nào. Toàn bộ đi qua sổ cái C-01 — **không có đường nào đổi số dư mà không thành một dòng sổ**.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| A-01 | Danh mục chính sách theo cấp | Mỗi dòng: cấp (A-02) · mức điểm/tháng · hiệu lực từ ngày. **Đổi mức = thêm dòng hiệu lực mới, không sửa dòng cũ** — để tra được "mức của tháng trước" khi đối chiếu hay khi kế toán hỏi | 1 | [~] khung CRUD khai báo |
| A-02 | Bộ cấp phúc lợi (`CoffeeLevel`) | `SMALLINT` + IntEnum theo luật R2. "Cấp nhân sự" **chưa tồn tại trong hệ** (`tab_employee.position` là chữ tự do) nên bản 1 gán cấp tay ở B-01; khi HR5 (danh mục chức danh) có thật thì nối vào, cột `title_id` để dành sẵn. **Bộ giá trị cấp do nghiệp vụ chốt trước khi seed** | ? — chờ nghiệp vụ chốt bộ cấp | [ ] |
| A-03 | Reset hằng tháng | Celery beat **ngày 1, 00:05 giờ VN**: với từng người đang hưởng, ghi cặp dòng `expire` (thu hết số dư kỳ cũ) + `grant` (mức của cấp tại thời điểm cấp). **Không UPDATE số dư — số dư là tổng sổ.** Người `SUSPENDED`/nghỉ việc bị bỏ qua | 1 | [~] Celery beat sẵn múi giờ VN |
| A-04 | Chống cấp trùng | Khóa duy nhất **ở tầng DB** (cột `uniq_key`, xem [`02`](./02-bang-du-lieu.md) §3): một người một kỳ đúng một dòng `grant`. **Chạy lại task của cùng kỳ không nhân đôi điểm** — mạng lỗi giữa chừng rồi bấm lại là ca chắc chắn xảy ra, không phải ca hiếm | 1 | [ ] |
| A-05 | Thu hồi khi nghỉ việc | Nhân sự chuyển trạng thái nghỉ → dòng `revoke` đưa số dư về 0 + khóa thành viên (B-04). **Không thu hồi là người đã nghỉ vẫn quẹt được — lỗ tiền thật** (N5 của `09` §7) | 1 | [ ] |
| A-06 | Duyệt bảng cấp phát từng kỳ | Bản 1 đề nghị **không cần**: mức đã duyệt một lần ở chính sách A-01, cấp phát tháng chỉ là thi hành. Nếu nghiệp vụ vẫn đòi duyệt từng kỳ thì thêm bước sinh bảng dự kiến → xem trước → chốt (PL3/PL4 của `09`) | ? — chờ N9 | [ ] |
| A-07 | Điều chỉnh tay | Cộng bù / trừ nhầm, **lý do bắt buộc**, quyền riêng (G-02), thành dòng `adjust` có người ghi. **Không có đường sửa số dư nào không để lại dấu vết** | 1 | [ ] |

## Nhóm B — Thành viên & ghép POS365

> Ghép sai một người là trừ điểm của người khác. Vì thế luật xuyên suốt là luật A3 của `09` §8: **ghép một lần có người xác nhận, về sau chỉ đi theo `pos_partner_id`, không bao giờ tự ghép lại theo tên hay số điện thoại**.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| B-01 | Gán cấp cho nhân sự | Mỗi nhân sự một dòng thành viên: cấp + trạng thái hưởng. Nguồn danh sách người là `tab_employee` sẵn có, **không chép hồ sơ nhân sự sang** | 1 | [ ] |
| B-02 | Ghép nhân sự ↔ khách POS365 | Tra khách bên POS365 theo SĐT/tên, **người bấm xác nhận TỪNG cặp**, lưu `pos_partner_id` làm khóa. SĐT trùng/rỗng thì để người quyết, hệ không đoán | 1 | [ ] |
| B-03 | Tạo khách mới trên POS365 | Nhân sự chưa có bên kia → `POST /api/partners` (mã = mã nhân viên, nhóm khách riêng để tách khách vãng lai). Nhân viên mới vào là quẹt được ngay, không nhờ quầy tạo tay | 1 | [ ] |
| B-04 | Gỡ ghép / khóa thành viên | Đi cùng A-05: khóa dòng thành viên (hết hiện ở tra cứu quầy C-04), giữ nguyên lịch sử sổ. **Không xóa cứng** — sổ tiền phải tra ngược được | 1 | [ ] |
| B-05 | Gán cấp hàng loạt | Nhập CSV gán cấp cho cả danh sách khi khởi động phân hệ (~vài chục người thì làm tay được, để bản 2 trừ khi số người lớn) | 2 | [~] khung import sẵn |

## Nhóm C — Sổ điểm & tự phục vụ

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| C-01 | Sổ cái điểm chỉ-INSERT | 6 loại dòng (`grant/expire/spend/refund/adjust/revoke`), điểm **có dấu**, số dư = `SUM(points)`. **Không UPDATE, không DELETE — sửa sai bằng dòng đảo ngược.** Sổ tiền mà sửa được thì không còn là sổ (`09` §4) | 1 | [ ] |
| C-02 | Ví điểm của tôi | Nhân viên tự xem: số dư kỳ này · được cấp bao nhiêu · lịch sử tiêu. Nhờ scope `own` (G-01), **gõ thẳng id người khác vào URL cũng không mở được** (nghiệm thu 4 của `09` §11) | 1 | [~] khuôn trang `/me` |
| C-03 | Sổ điểm quản trị | Danh sách sổ cái lọc theo người/kỳ/loại trên `DataTable`; xuất CSV để bản 2 (đợi khung export log của `16`) | 1 | [~] DataTable |
| C-04 | Tra cứu số dư cho quầy | Màn tối giản: gõ mã NV/SĐT → tên + số dư chữ to. Tài khoản quầy có vai trò riêng **chỉ đọc được (tên, số dư)** — không thấy lịch sử, không thấy sổ. Đây là lớp vá số 2 cho việc POS365 không tự chặn người hết điểm (`17` §5) | 1 | [ ] |
| C-05 | Xử lý âm điểm | Thanh toán hỗn hợp tại quầy đã chặn phần lớn ca âm; ca lọt lưới về **âm trong sổ**, nổi lên màn đối soát D-04. Trừ kỳ sau hay thu tiền là quyết định nghiệp vụ, **hệ không tự xử lý** | ? — chờ nghiệp vụ | [ ] |

## Nhóm D — Đồng bộ POS365

> Toàn bộ nhóm này chạy bằng Celery + Redis đang có sẵn (chủ trương PS9 của `09`: mượn hạ tầng, không viết lại). Thuật toán chi tiết ở [`03-tich-hop-pos365.md`](./03-tich-hop-pos365.md).

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| D-01 | Kéo đơn hàng định kỳ | 5 phút/lần (siết sau POC P6): kéo `/api/orders` **tăng dần** từ mốc đã kéo (trừ lùi 10 phút đè mép), lọc đơn có phương thức "Trừ điểm", ghi `tab_pos_order` + dòng `spend`. **Idempotent nhờ UNIQUE `pos_order_id` — kéo trùng vô hại** | 1 | [~] khuôn task Celery |
| D-02 | Hàng chờ đơn không khớp | Đơn trả bằng "Trừ điểm" mà không có khách / khách chưa ghép → nằm hàng chờ trên màn đối soát, **hệ không đoán người**. Đây là lưới bắt lỗi thao tác quầy (quên chọn khách) | 1 | [ ] |
| D-03 | Soát đơn hủy (void) | Mỗi giờ đọc lại `Status` các đơn đã ghi `spend` trong 7 ngày; đơn void → dòng `refund` (duy nhất theo đơn). Quầy hủy bill mà điểm không hoàn là mất lòng tin ngay tuần đầu | 1 | [ ] |
| D-04 | Đối chiếu hằng ngày | 06:00 so tổng `spend` trong sổ ↔ tổng đơn "Trừ điểm" bên POS365 theo ngày; **lệch thì lên màn hình, KHÔNG tự sửa** (luật số 3 của `09` §2). Nút xử lý từng dòng sinh dòng `adjust` có lý do | 1 | [ ] |
| D-05 | Nhật ký đồng bộ + chạy tay | Mỗi lần chạy một dòng `tab_pos_sync_run`: lúc nào, kéo bao nhiêu, lỗi gì, ai bấm. Nút chạy tay có quyền riêng (G-02). "Quán kêu thiếu điểm là tra ra trong một phút" (PS7) | 1 | [ ] |
| D-06 | Cảnh báo đồng bộ chết | 3 lần chạy hỏng liên tiếp → báo người phụ trách qua khuôn thông báo sẵn có. **Không có lần đồng bộ nào chết im lặng** (PS10) | 1 | [~] module alert/notification |
| D-07 | Soi gương số dư lên POS365 | Job đêm ghi số dư vào hồ sơ khách POS365 (`Point`/`Description`) để thu ngân thấy ngay trên màn POS — lớp vá số 3 của `17` §5. **Chỉ là hiển thị, nguồn đúng vẫn là sổ ERP** — lệch không gây hại | ? — chờ POC P5 xác nhận ghi được | [ ] |
| D-08 | Đồng bộ menu quán | Kéo `/api/products` một chiều về bảng chỉ-đọc, phục vụ báo cáo "điểm tiêu vào món gì". **Cấm đụng `tab_product` và cấm thêm cột giá vào bảng sản phẩm** (luật D-025) | 2 | [ ] |

## Nhóm E — Báo cáo & bàn giao

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| E-01 | Báo cáo cấp/tiêu theo kỳ | Tổng cấp, tổng tiêu, tỷ lệ dùng, theo phòng ban / pháp nhân / cấp. Kế toán nhận một con số mỗi tháng, không tự cộng (PL9) | 2 | [~] khuôn báo cáo |
| E-02 | Bàn giao kế toán | Chốt số cuối kỳ, xuất theo mẫu kế toán. **Nếu N10 (thuế TNCN) trả lời "có" thì phải xuất theo TỪNG NGƯỜI theo tháng**, không gộp — đó là lý do E-02 chưa khóa thiết kế | ? — chờ N10 | [ ] |
| E-03 | Báo cáo tiêu theo món | Cần D-08. Trả lời "quán nên nhập gì, món nào được chuộng" — giá trị phụ, không chặn gì | 2 | [ ] |

## Nhóm G — Phân quyền

> Chi tiết khai báo ở [`04-phan-quyen.md`](./04-phan-quyen.md). Luật gốc là PS12 của `09`: **quyền xem, quyền điều chỉnh, quyền chạy đồng bộ là ba quyền riêng, không gộp**.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| G-01 | 4 entity + phạm vi dữ liệu | `coffee_policy` · `coffee_member` · `coffee_ledger` · `pos_order` vào `ENTITIES` + `SCOPE_FIELDS`. Sổ và thành viên lọc theo `employee_id` để scope `own` chạy thật; **đọc lẻ theo id phải qua `get_scoped`**, không `db.get` | 1 | [~] hệ 2 trục sẵn |
| G-02 | Ba quyền tách | Xem sổ người khác (`coffee_ledger.read` + scope rộng) · điều chỉnh tay (`coffee_ledger.write`) · chạy đồng bộ tay (`pos_order.write`). Gộp lại là một tài khoản lộ có thể vừa tự cộng điểm vừa xóa dấu | 1 | [x] ma trận role×action |
| G-03 | Vai trò seed | `coffee_admin` (Nhân sự/quản trị quán) · `coffee_counter` (tài khoản quầy — chỉ C-04). Khai ở `seed.py`/`seed_prod.py`, nhớ luật `SEED_FORCE_SYNC` khi đổi trên prod | 1 | [x] khuôn STD_ROLES |

---

## Bảng tổng hợp

| Nhóm | Số tính năng | Thuộc bản đầu |
|---|---|---|
| N · Việc nền & kết nối | 5 | 5 |
| A · Chính sách & cấp phát | 7 | 5 |
| B · Thành viên & ghép | 5 | 4 |
| C · Sổ điểm & tự phục vụ | 5 | 4 |
| D · Đồng bộ POS365 | 8 | 6 |
| E · Báo cáo & bàn giao | 3 | 0 |
| G · Phân quyền | 3 | 3 |
| **Tổng** | **31** | **22** |

**Nhận định.** Nhóm nặng nhất là **D — đồng bộ** (6/8 dòng bản đầu, và là nơi duy nhất nói chuyện với hệ bên ngoài — mọi ca lỗi mạng, trùng, hủy đơn dồn về đây); nhưng nhóm quyết định *đúng/sai tiền* lại là **A + C** — sổ cái chỉ-INSERT và khóa chống cấp trùng, hai thứ phải có test riêng trước khi chạm quán thật. Phần tái dùng được nhiều nhất là hạ tầng: Celery beat, khung CRUD, DataTable, hệ phân quyền 2 trục, khuôn thông báo — nên khối lượng viết mới thật sự nằm ở `pos365_client` + 4 task đồng bộ + sổ cái, không nằm ở màn hình. Ba dấu `?` treo trên A-02 (bộ cấp), A-06/C-05 (luật duyệt & âm điểm) và E-02 (thuế) — đều là câu **nghiệp vụ**, không chặn CP0–CP1 nhưng **chặn thí điểm CP4**.

**Tiếp theo:** [`06-lo-trinh-phase.md`](./06-lo-trinh-phase.md) — các mã trên được xếp vào phase CP0…CP5.
