# KẾ HOẠCH TRIỂN KHAI — POS365 QUẢN LÝ ĐIỂM CÀ PHÊ

| | |
|---|---|
| Bản | **1.0 — 07/09/2026** |
| Đối tượng đọc | Người chủ trì · Đội phần mềm · Phòng Nhân sự · Quầy cà phê |
| Trả lời câu hỏi | Đưa POS365 lên quản lý quầy cà phê, nhân viên order và **thanh toán bằng phương thức trừ điểm** trên tài khoản cá nhân, điểm **reset theo cấp nhân sự vào mốc định kỳ hằng tháng** — làm bằng cách nào, theo thứ tự nào |
| Quan hệ với bản 09 | [`09-phuc-loi-diem-va-pos.md`](./09-phuc-loi-diem-va-pos.md) là bản **định hướng** (12/08). Bản này là bản **thực thi**: đã đọc được tài liệu API chính thức, và đề bài mới chốt thêm 2 quyết định nghiệp vụ làm thay đổi phương án được chọn (xem mục 1) |
| Bộ tài liệu kỹ thuật | **[`diem-ca-phe/`](./diem-ca-phe/README.md)** (08/09/2026) — bản thiết kế thực thi chi tiết: tính năng có mã, bảng dữ liệu, thuật toán đồng bộ, phân quyền, giao diện, phase CP0→CP5. **Chỗ nào lệch bản này thì lấy bộ đó** |

**Ba câu tóm tắt.** POS365 vẫn là màn hình duy nhất của quầy: thu ngân chọn khách hàng (là nhân viên đã ghép) và bấm phương thức thanh toán **"Trừ điểm"** — một *tài khoản thanh toán* dựng sẵn trong POS365, không cần POS365 biết gì về điểm. ERP là **sổ cái duy nhất**: kéo đơn hàng về theo lịch, đơn nào thanh toán bằng tài khoản "Trừ điểm" thì ghi một dòng **tiêu** vào sổ điểm của đúng nhân viên; đầu mỗi tháng một tác vụ hẹn giờ **reset và cấp lại điểm theo cấp nhân sự**. Vì chỉ còn MỘT nơi giữ số (ERP), bài toán "hai hệ cùng giữ một con số tiền" của bản 09 biến mất — đổi lại phải xử lý một điểm yếu duy nhất: POS365 không tự chặn người đã hết điểm (mục 5).

---

## 1. Khác gì bản 09 — và vì sao

Bản 09 khuyến nghị **P2** (ERP giữ sổ, POS365 giữ số dư quầy, phải **đẩy điểm** sang POS365). Bản này chuyển sang một biến thể của **P3**: **ERP giữ tất, POS365 chỉ ghi nhận giao dịch qua phương thức thanh toán**. Ba lý do:

| # | Lý do | Chi tiết |
|---|---|---|
| 1 | **Đề bài mới chốt N2 = reset hằng tháng, theo cấp** | Bản 09 mặc định "có cộng dồn" chính vì số dư một-con-số của POS365 không diễn tả được lô/hạn. Nay nghiệp vụ chốt **reset định kỳ** → mô hình lô không cần nữa, nhưng "đẩy điểm + reset" nghĩa là mỗi tháng phải ghi đè số dư hàng loạt bên POS365 — đúng thao tác mà quy tắc cứng số 2 của bản 09 cấm. Bỏ hẳn việc POS365 giữ số dư thì mâu thuẫn này biến mất |
| 2 | **Cơ chế "phương thức thanh toán" đã có bằng chứng trong spec chính thức**, còn "API ghi điểm" thì chưa | Spec `OrderSave` mô tả rõ `MoreAttributes.PaymentMethods[{AccountId, Value}]` — `AccountId: null` là tiền mặt, khác null là **tài khoản chỉ định**; và metadata có `AccountList` để lấy danh sách tài khoản đó. Ngược lại K2 của bản 09 (ghi được `Point` không) vẫn chưa ai kiểm chứng. Chọn đường đã có bằng chứng |
| 3 | **Không đổi thói quen quầy** | Thu ngân vẫn bán trên POS365 như hôm nay, chỉ thêm động tác chọn khách + chọn phương thức "Trừ điểm" — nhẹ hơn cả P3 nguyên bản của 09 (bắt quầy mở thêm màn hình ERP để trừ) |

Những gì bản 09 viết mà bản này **giữ nguyên, không nhắc lại**: sổ cái chỉ ghi thêm (mục 4 của 09) · 4 chỗ hỏng mất tiền thật A1–A4 (mục 8) · phương án 0 chạy tay tháng đầu (mục 9) · không tự viết POS (mục 12) · danh sách "không làm" (mục 13). Đọc bản này phải đọc kèm bản 09.

---

## 2. Những gì ĐÃ kiểm chứng được từ tài liệu API (07/09/2026)

Nguồn: bản *API Specification Doc 1.0* chính thức của POS365 (14/06/2021) + trang metadata `https://api.pos365.vn/api/metadata`. Trả lời được một phần chín câu K1–K9 của bản 09 §3.2:

| Câu 09 | Trả lời | Bằng chứng |
|---|---|---|
| K1 — xác thực máy | **Nửa có.** Không có token máy; đăng nhập `GET /api/auth/credentials?Username=&Password=` → `SessionId`, gửi bằng cookie `ss-id`. Phiên **có hạn**, spec dặn: gặp 401 thì đăng nhập lại. → Dùng được cho máy nếu lập **một tài khoản riêng cho API** (không dùng tài khoản của người) + tự động re-login khi 401 | Spec §1 |
| K5 — kéo giao dịch | **Có.** `GET /api/orders` (phân trang `$top/$skip`, tổng `__count`, `Includes=Partner`); chi tiết dòng `GET /api/orders/detail?OrderId=`. Đơn có `Status`, `Total`, `PurchaseDate`, `SoldById` | Spec §2, §5.1, §5.2 |
| K6 — webhook | **Không thấy** webhook ra ngoài trong metadata (chỉ có FireBase nội bộ của họ) → chạy **kéo theo lịch**, chấp nhận trễ vài phút | metadata |
| K9 — sản phẩm | **Có, hai chiều**: `GET/POST/DELETE /api/products`. Bản 1 chỉ dùng chiều đọc (menu phục vụ báo cáo) | Spec §3 |
| Khách hàng | `GET/POST/DELETE /api/partners`; Partner có `Code`, `Phone`, `Point`, `Loyalty`, `Debt`, `PartnerGroupMembers` → tạo/ghép nhân viên làm được | Spec §4 |
| **Phương thức thanh toán** | `OrderSave` nhận `MoreAttributes.PaymentMethods[{AccountId, Value}]` — nhiều phương thức trên một đơn, `AccountId` trỏ vào *tài khoản thanh toán*; metadata có **`AccountList` / `AccountCreateOrUpdate`** để đọc/dựng tài khoản đó | Spec §5.3 + metadata |
| Điểm | metadata có **`PointUseSave` / `PointUseList` / `PointUseDelete`** — ứng viên cho K2, nhưng chưa gọi thử | metadata |

### 2.1 Còn PHẢI kiểm chứng bằng lời gọi thật (POC ~2 ngày — GĐ 0, chặn mọi việc code)

| # | Câu hỏi | Quyết định gì |
|---|---|---|
| P1 | Đơn kéo về từ `GET /api/orders` có mang **phương thức thanh toán** không (trường `MoreAttributes` hay `Includes` nào)? Hay phải gọi thêm từng đơn? | Quyết cách lọc "đơn trừ điểm" — lọc ngay ở danh sách hay phải đọc chi tiết N+1 |
| P2 | `AccountList` trả những gì; tạo tay một tài khoản "Trừ điểm cà phê" trên giao diện POS365 rồi đọc ra `AccountId` cố định | `AccountId` này là hằng số cấu hình của toàn bộ tích hợp |
| P3 | Thu ngân **có bấm được** phương thức đó trên màn hình bán hàng không, và đơn in bill hiện tên gì | Nghiệm thu thao tác quầy |
| P4 | `GET /api/orders` lọc được theo thời gian không (tham số ngày, hay chỉ `$skip` theo `CreatedDate` giảm dần)? Đơn **void** thể hiện ra sao (`Status` nào)? | Quyết thuật toán kéo tăng dần + hoàn điểm khi hủy đơn |
| P5 | `PartnerSave` có ghi được `Point`/`Description` không (K2 cũ) | Chỉ phục vụ tiện ích "thu ngân nhìn thấy số dư" (mục 5) — **không** chặn kiến trúc |
| P6 | Giới hạn tần suất gọi, cỡ trang tối đa (K8 cũ) | Quyết chu kỳ kéo 1' hay 5' |
| P7 | Trường `Password` trong Partner có bao giờ trả giá trị thật không (cảnh báo an toàn của 09 §3.2) | Nếu có → lọc bỏ ngay tầng nhận, không lưu, không log |

Kết quả POC ghi thành phụ lục của chính tài liệu này (bảng P1–P7 điền đáp án + curl mẫu), đúng tinh thần "không viết code phần B trước khi bảng được điền" của 09 §3.3.

---

## 3. Thiết kế nghiệp vụ

### 3.1 Luồng tại quầy (không đổi thói quen POS365)

1. Nhân viên ra quầy đọc **mã nhân viên / số điện thoại**.
2. Thu ngân chọn đúng **khách hàng** trên POS365 (đã ghép sẵn 1-1 với nhân sự — mục 4), lên đơn như bình thường.
3. Thanh toán: chọn phương thức **"Trừ điểm"** (tài khoản thanh toán `AccountId` cố định). Cho phép **thanh toán hỗn hợp**: phần vượt số dư thu tiền mặt/chuyển khoản (spec hỗ trợ nhiều `PaymentMethods` trên một đơn).
4. ERP kéo đơn về theo lịch (mục 6), ghi dòng **tiêu** vào sổ điểm của nhân viên = phần `Value` trả bằng tài khoản "Trừ điểm".

### 3.2 Reset điểm hằng tháng theo cấp nhân sự

- **Mốc:** 00:05 ngày **1 hằng tháng**, giờ VN (Celery beat đã chạy `Asia/Ho_Chi_Minh` sẵn — xem `backend/app/core/celery_app.py`).
- **Cách reset:** ghi **hai dòng sổ** cho mỗi nhân sự đang hưởng: dòng `expire` (thu hồi toàn bộ số dư còn lại của kỳ cũ, có thể = 0) rồi dòng `grant` (cấp mức của cấp nhân sự tại thời điểm cấp). Tuyệt đối **không** UPDATE số dư — số dư là tổng sổ, đúng luật PL2/PL5 của bản 09.
- **Chống cấp trùng:** ràng buộc UNIQUE `(employee_id, period, type='grant')` ở tầng DB — chạy lại task của cùng kỳ không nhân đôi điểm (nghiệm thu số 2 của 09 §11).
- **"Cấp nhân sự" hiện CHƯA có trong hệ thống** — `tab_employee.position` chỉ là chữ tự do (xem `backend/app/modules/employee/model.py`). Bản 1 giải quyết bằng **bảng chính sách tự khai**: danh mục *Cấp phúc lợi cà phê* (mã cấp SMALLINT theo luật R2 + tên + mức điểm/tháng + hiệu lực), và **gán cấp cho từng nhân sự** trên màn quản trị. Khi nào HR5 (danh mục chức danh) của lộ trình HRM có thật thì nối chính sách vào chức danh, bỏ gán tay — thiết kế bảng để dành sẵn cột `title_id` nhưng chưa dùng.

### 3.3 Quy đổi và các câu đã chốt / còn treo

| Câu (từ 09 §7) | Trạng thái |
|---|---|
| N2 cộng dồn? | **ĐÃ CHỐT theo đề bài 07/09: KHÔNG cộng dồn — reset theo mốc hằng tháng.** |
| N1 tỷ lệ | Đề nghị giữ mặc định **1 điểm = 1 đồng** (menu POS365 tính bằng đồng, khỏi quy đổi trên bill). Chờ xác nhận |
| N5 nghỉ việc | Giữ mặc định 09: thu hồi về 0 ngày nghỉ việc (dòng `revoke`) + **gỡ ghép/khóa** khách hàng tương ứng trên POS365 |
| N9 ai duyệt | Bản 1 đề nghị: bảng cấp phát tháng sinh tự động, **không cần duyệt từng kỳ** vì mức đã duyệt một lần ở *chính sách*; chỉ **điều chỉnh tay** mới cần quyền riêng + lý do. Nếu nghiệp vụ vẫn đòi duyệt từng kỳ thì thêm bước xem-trước-rồi-chốt (PL3/PL4 của 09) — quyết trước GĐ 2 |
| N10 thuế TNCN | Vẫn treo — hỏi kế toán, như 09 |
| **Mới — âm điểm** | Thanh toán hỗn hợp (3.1) đã chặn phần lớn ca âm. Ca lọt lưới (thu ngân trừ quá vì không thấy số dư): về **âm trong sổ**, lên màn đối soát; xử lý âm là quyết định nghiệp vụ (trừ kỳ sau / thu tiền), KHÔNG tự sửa. Giảm ca này bằng mục 5 |

---

## 4. Dữ liệu và chỗ đứng trong mã nguồn

Module backend mới `app/modules/coffee_point/` (model · schema · service · controller · `pos365_client.py` · `tasks.py`), theo đúng khuôn `vehicle_booking`/`seal_request`. So với 7 entity của 09 §4, bản 1 rút còn **5 bảng** (bỏ `point_grant` — cấp phát tự động không cần chứng từ đợt riêng, bỏ `pos_outlet` — một quầy, để thành cấu hình):

| Bảng | Nội dung | Ghi chú |
|---|---|---|
| `tab_coffee_policy` | Cấp phúc lợi: `level_code` SMALLINT (IntEnum, luật R2) · tên cấp · `monthly_points` · hiệu lực từ/đến | Sửa mức = thêm dòng hiệu lực mới, không sửa dòng cũ → tra được "mức của tháng trước" |
| `tab_coffee_member` | Gán cấp cho nhân sự: `employee_id` (unique) · `level_code` · `pos_partner_id` (khóa ghép POS365, theo luật A3: ghép một lần có người xác nhận, không tự ghép lại) · trạng thái SMALLINT | Gộp vai `pos_partner_map` của 09 vào đây |
| `tab_coffee_ledger` | **Sổ cái — chỉ INSERT.** `employee_id` · `period` (YYYYMM) · `type` SMALLINT (`grant/expire/spend/refund/adjust/revoke`) · `points` · `pos_order_id` · `reason` · người ghi | UNIQUE `(employee_id, period, type)` cho `grant`; UNIQUE `pos_order_id` cho `spend` → kéo trùng vô hại |
| `tab_pos_order` | Bản sao đơn kéo về: `pos_order_id` unique · code · ngày · partner · tổng tiền · phần trả bằng điểm · `status` SMALLINT · JSON thô | Nguồn đối soát + hoàn điểm khi void |
| `tab_pos_sync_run` | Nhật ký mỗi lần đồng bộ: lúc nào · kéo bao nhiêu · lỗi gì · ai bấm (PS7 của 09) | |

Ràng buộc hệ thống bắt buộc (đều là luật đã có, liệt kê để khỏi sót):

1. Model mới phải vào `app/core/all_models.py` rồi mới autogenerate migration.
2. Entity mới (`coffee_policy`, `coffee_member`, `coffee_ledger`, `pos_order`) phải khai vào `ENTITIES` (`core/permissions.py`) **và** `SCOPE_FIELDS` (`core/scoping.py`) ngay — test `test_pham_vi_khai_du_b07.py` đang khóa 44/44, thiếu là đỏ suite. Sổ điểm khai scope theo `employee_id` để "nhân viên chỉ thấy sổ của mình" có hiệu lực thật (nghiệm thu số 4 của 09 §11).
3. Quyền + vai trò khai trong `seed.py`/`seed_prod.py`, nhớ luật `SEED_FORCE_SYNC` của prod.
4. Mọi cột trạng thái/loại/cấp là SMALLINT + IntEnum, khai ở `status_catalog.py`, sinh TS bằng `gen_status_ts.py` — không hand-write bên frontend.
5. Cấu hình kết nối (`POS365_BASE_URL` = `https://<cửa-hàng>.pos365.vn`, `POS365_USERNAME/PASSWORD` của **tài khoản API riêng**, `POS365_PAYMENT_ACCOUNT_ID`, `POS365_HARD_OFF`) nằm ở biến môi trường — **`POS365_HARD_OFF` mặc định bật ở mọi môi trường không phải prod** (luật A1 của 09; client từ chối gọi ra ngoài khi cờ bật, có test).

---

## 5. Điểm yếu duy nhất của phương án — và ba lớp vá

POS365 không biết số dư → **không tự chặn** người hết điểm tại quầy. Ba lớp, làm từ rẻ tới đắt:

| Lớp | Làm gì | Khi nào |
|---|---|---|
| 1 — Quy trình | Thanh toán hỗn hợp là mặc định: thu ngân hỏi "trừ bao nhiêu điểm?", phần còn lại thu tiền. Số âm hiếm và nhỏ | GĐ 1, chỉ là hướng dẫn quầy |
| 2 — Màn tra cứu quầy | Trang nhỏ của ERP (đăng nhập tài khoản quầy, quyền chỉ-đọc số dư): gõ mã NV/SĐT → thấy số dư hiện tại. Tablet/điện thoại đặt cạnh máy POS | GĐ 2 |
| 3 — Soi gương số dư lên POS365 | Nếu P5 (POC) xác nhận `PartnerSave` ghi được `Point`/`Description`: job đêm ghi số dư ERP vào hồ sơ khách để thu ngân thấy ngay trên màn POS365. **Chỉ là hiển thị** — nguồn đúng vẫn là sổ ERP, lệch không gây hại | GĐ 3, tùy kết quả POC |

---

## 6. Đồng bộ — thuật toán và lịch

Chạy bằng **Celery + Redis đang có sẵn** (beat timezone VN, khuôn xem `notification/tasks.py`, `import_tool/tasks.py`) — đúng chủ trương PS9 của 09 "mượn hạ tầng bước 5, không viết lại".

| Task | Lịch | Nội dung |
|---|---|---|
| `coffee.pull_orders` | mỗi **5 phút** (siết còn 1–2' sau khi biết P6) | Đăng nhập (cache SessionId, re-login khi 401) → kéo `/api/orders` **tăng dần** từ mốc `last_synced` (trừ lùi 10' đè mép) → lọc đơn có `PaymentMethods` chứa `POS365_PAYMENT_ACCOUNT_ID` → upsert `tab_pos_order` → INSERT dòng `spend` (idempotent nhờ UNIQUE `pos_order_id`). Partner không ghép được → dòng chờ trên màn đối soát, **không đoán** |
| `coffee.check_voids` | mỗi giờ | Đọc lại `Status` các đơn đã ghi `spend` trong 7 ngày; đơn void → INSERT dòng `refund` (unique theo đơn) |
| `coffee.monthly_reset` | **ngày 1, 00:05** | Theo 3.2: `expire` + `grant` từng người theo chính sách hiệu lực. Bỏ qua người `inactive`/nghỉ việc |
| `coffee.reconcile` | 06:00 hằng ngày | Đối chiếu tổng `spend` trong sổ ↔ tổng đơn "Trừ điểm" bên POS365 theo ngày; lệch → cảnh báo màn đối soát, **không tự sửa** (luật số 3 của 09 §2) |
| `coffee.mirror_balance` | đêm, tùy chọn | Lớp 3 của mục 5, chỉ khi POC xác nhận |

---

## 7. Giao diện (frontend-v2)

Phân hệ mới trong `src/app/router/module-registry.ts` (một dòng), thư mục `src/modules/coffee-point/`. Trạng thái/loại đọc từ file TS sinh tự động. Màn hình bám khuôn CRUD khai báo sẵn có:

| Màn | Ai dùng | Nội dung |
|---|---|---|
| **Ví điểm của tôi** | Mọi nhân viên | Số dư kỳ này · được cấp bao nhiêu · lịch sử tiêu (món gì nếu đã đồng bộ menu) — PL7 của 09 |
| **Chính sách cấp điểm** | Quản trị/Nhân sự | CRUD `tab_coffee_policy` (khung CrudListPage) |
| **Thành viên & ghép POS365** | Quản trị/Nhân sự | Gán cấp; ghép nhân sự ↔ khách POS365 (tra theo SĐT, người bấm xác nhận từng cặp — A3); nút tạo khách mới trên POS365 cho người chưa có (PS3) |
| **Sổ điểm & đối soát** | Quản trị/Kế toán | Sổ cái lọc theo người/kỳ/loại; tab đơn không ghép được; tab lệch đối soát + nút xử lý sinh dòng `adjust` có lý do |
| **Tra cứu số dư (quầy)** | Tài khoản quầy | Lớp 2 của mục 5 — một ô tìm, một con số to |

Phân quyền: quyền xem sổ người khác · quyền điều chỉnh tay · quyền chạy đồng bộ tay là **ba quyền riêng** (PS12 của 09).

---

## 8. Lộ trình và ước lượng

| GĐ | Việc | Ước lượng | Điều kiện ra |
|---|---|---|---|
| **0 — POC** | 7 câu P1–P7 (mục 2.1), lập tài khoản API riêng, dựng tài khoản thanh toán "Trừ điểm" trên POS365, ghi phụ lục kết quả | **2 ngày** | Bảng P1–P7 điền xong, có curl bằng chứng |
| **1 — Backend lõi** | 5 bảng + migration + ENTITIES/SCOPE_FIELDS + seed quyền · `pos365_client` (login/retry/paging/HARD_OFF) · 4 task Celery · API cho các màn | **~1 tuần** | pytest xanh, kể cả test idempotent (chạy `monthly_reset` 2 lần, kéo đơn 2 lần — số dư không đổi) |
| **2 — Giao diện** | 5 màn ở mục 7 + `npm run check` sạch | **~1 tuần** | Nhân viên tự tra được ví; quầy tra được số dư |
| **3 — Thí điểm** | Chạy **song song với cấp tay** (phương án 0 của 09 vẫn giữ cho tháng đầu): tháng thí điểm đối chiếu số tay ↔ số máy hằng tuần; bật `mirror_balance` nếu POC cho | **1 tháng lịch** | 10 tiêu chí nghiệm thu của 09 §11 (bỏ các mục về "đẩy điểm" — thay bằng: *kéo trùng không nhân đôi*, *void có hoàn*, *reset chạy 2 lần vô hại*) |
| **4 — Mở rộng** | Báo cáo tiêu theo món (đồng bộ menu PS8) · nối chính sách vào danh mục chức danh khi HR5 có · cân nhắc `PointUse*` nếu muốn POS365 hiển thị điểm chính thức | sau | |

Nhân lực: 1 dev full-stack là đủ cho GĐ 0–2; GĐ 0 không chờ ai, làm ngay được.

---

## 9. Rủi ro còn lại

| # | Rủi ro | Đỡ bằng |
|---|---|---|
| 1 | Danh sách đơn không trả kèm phương thức thanh toán (P1 xấu) → phải gọi chi tiết từng đơn | Chu kỳ kéo giữ 5', kéo theo lô, cache; quầy nội bộ vài chục đơn/ngày nên N+1 chịu được |
| 2 | Thu ngân quên chọn khách hoặc chọn phương thức khác → đơn "vô danh" | Đơn trả bằng tài khoản "Trừ điểm" mà không có Partner → nổi lên màn đối soát trong ngày; huấn luyện quầy + kiểm tuần đầu |
| 3 | Phiên API bị POS365 đổi chính sách/khóa | Tài khoản API riêng, giám sát: 3 lần đồng bộ hỏng liên tiếp → bắn cảnh báo (mượn khuôn alert sẵn có — PS10) |
| 4 | Dev bắn nhầm vào cửa hàng thật | `POS365_HARD_OFF` mặc định bật + test khẳng định không có HTTP call khi cờ bật (A1) |
| 5 | Mức điểm/cấp chưa được nghiệp vụ chốt bằng văn bản | Không chặn GĐ 0–1 (bảng chính sách là dữ liệu), nhưng **chặn GĐ 3** — trình N1/N9/N10 + bảng mức theo cấp trước khi thí điểm |

---

## Phụ lục A — Kết quả POC (bắt đầu điền 08/09/2026, cửa hàng thật `degocode.pos365.vn`, tài khoản API riêng, chỉ lời gọi ĐỌC)

| # | Câu | Đáp án | Bằng chứng (response rút gọn) |
|---|---|---|---|
| K1 | Xác thực máy | **ĐẠT** — `GET /api/auth/credentials` trả `SessionId`, cookie `ss-id` dùng được cho mọi request sau | Login trả `{"SessionId": "jTGXSQ…"}` |
| P1 | Đơn kéo về có mang phương thức thanh toán? | **ĐẠT (08/09, 3 đơn thử bán từ màn POS):** dòng DANH SÁCH mang cả `AccountId` top-level lẫn `MoreAttributes` = chuỗi JSON `{"PaymentMethods":[{"AccountId":…,"Value":…}]}` — đúng hình dạng spec §5.3, `extract_points_paid` chạy nguyên. Không cần đọc chi tiết từng đơn (không N+1). ⚠️ Hai điều kèm: (a) 36 đơn **dữ liệu mẫu** seed sẵn KHÔNG có hai trường này — đừng lấy làm chuẩn; (b) đơn qua cổng tích hợp còn treo (chưa xác nhận tiền) vẫn ghi đủ phương thức, chỉ `AmountReceived=0` | `HD080926-0003`: `AccountId=2014`, `MoreAttributes={"PaymentMethods":[{"AccountId":2014,"Value":30000}]…}`; `HD080926-0001` (tiền mặt): `PaymentMethods:[{"AccountId":null,"Value":30000}]` |
| P2 | `AccountList` + AccountId "Trừ điểm" | **ĐẠT** — `GET /api/accounts` chạy, trả **MẢNG THÔ** (không bọc `results`); 8 tài khoản hệ thống (`RetailerId=0`). UI KHÔNG cho thêm tài khoản (cả Cài đặt lẫn nút ➕ ở màn thanh toán), nhưng **`AccountCreateOrUpdate` qua API thì ĐƯỢC**: `POST /api/accounts` body `{"Account":{"Id":0,"Name":"TRU DIEM CAFE"}}` → tạo thành công tài khoản riêng của cửa hàng. **`POS365_PAYMENT_ACCOUNT_ID = 46714`** — đã điền `.env` | `POST /api/accounts` → `{"Id":46714,"Name":"TRU DIEM CAFE","RetailerId":236910,...}` |
| P3 | Thu ngân bấm được phương thức? | **ĐẠT** — sau khi tạo tài khoản qua API, ô TÀI KHOẢN ▾ trên màn thanh toán có "TRU DIEM CAFE"; bán đơn thử **ghi nhận ngay, KHÔNG treo dialog** (khác hẳn tài khoản cổng tích hợp PAYOO-POS/VNPAY-POS — mấy cái đó bật "Chờ thanh toán" đợi máy cà thẻ, không dùng làm nút trừ điểm được). Nút ➕ trên màn thanh toán và Cài đặt đều KHÔNG cho tự thêm tài khoản — cửa duy nhất là API | Đơn `HD080926-0006`: `AccountId=46714`, `Status=2` |
| P3b | Gói POS365 có cho thêm tài khoản thanh toán tùy chỉnh ở phần Cài đặt? | **KHÔNG** — menu bánh răng không có mục tài khoản ngân hàng; "Thiết lập thanh toán QR-PAY" chỉ 4 mục cố định. Cửa duy nhất còn lại là nút ➕ trên màn thanh toán | Ảnh menu Cài đặt + màn QR-PAY 08/09 |
| P4 | Lọc thời gian · đọc lẻ đơn · Status void | **ĐẠT:** `GET /api/orders/{id}` đọc lẻ được (trả thẳng object); tham số lọc `Id` trên danh sách bị BỎ QUA; `FromDate/ToDate` cũng bị BỎ QUA → mốc kéo tăng dần cắt ở client (đúng như code đang làm). `DELETE /api/orders/{id}/void` chạy được; **đơn void mang `Status = 3`** (đơn thường = 2) — khớp hằng `POS_STATUS_ACTIVE=2` trong service, không phải sửa | Void `HD080926-0002` → `{"Message":"Xóa dữ liệu thành công"}`; đọc lại: `Status=3` |
| P5 | `PartnerSave` ghi được `Point`? | *(chưa — là lời gọi GHI, để sau khi P1 chốt)* | |
| P6 | Giới hạn gọi / cỡ trang | *(chưa đo — các lời gọi `$top=5` đều <1s, không thấy chặn; đo kỹ khi kéo trang lớn)* | |
| P7 | Trường `Password` của Partner | **AN TOÀN** — response `/api/partners` thô KHÔNG chứa khóa `Password` (khác ảnh Postman 2026 của cửa hàng khác); `strip_sensitive` vẫn giữ như lưới dự phòng | RAW check: `"Password" in text == False` |

Ghi chú thêm ngoài bộ câu hỏi:

- Dữ liệu cửa hàng đang là **dữ liệu mẫu** (36 đơn, khách `KH000001…5` tạo cùng một giây) + 6 đơn thử `HD080926-*` — trước CP4 bấm **"Xóa dữ liệu mẫu"** (menu bánh răng) và void nốt đơn thử để sổ sạch từ đầu. ⚠️ Kiểm xem xóa dữ liệu mẫu có xóa mất tài khoản `TRU DIEM CAFE` (46714) không — mất thì tạo lại qua API và cập nhật `.env`.
- Màn bán hàng có sẵn ô **"CHIẾT KHẤU ĐIỂM THƯỞNG"** và `MoreAttributes` có trường `PointDiscount` — POS365 có cơ chế điểm thưởng NATIVE gắn `Partner.Point`. Bản 1 cố ý không dùng (đi đường tài khoản thanh toán như đã chốt), ghi lại làm ứng viên cho D-07/CP5.
- **Chạy trọn đường ống 08/09/2026 trên dev với dữ liệu THẬT:** cấp kỳ 200.000 → `pull_orders` kéo 42 đơn, nhặt đúng 1 đơn `HD080926-0006` (AccountId 46714, bỏ qua tiền mặt/PAYOO/VNPAY/36 đơn mẫu) → vào hàng chờ (quầy không chọn khách) → gán tay → ví còn 170.000 với 2 dòng sổ. **GĐ 0 (POC) ĐÓNG — toàn bộ K1 + P1…P7 trả lời xong, trừ P5 (ghi `Point` — dời sang CP5 vì bản 1 không cần) và P6 (chưa thấy rate-limit ở tải thử).**

## Phụ lục B — Tra cứu nhanh API đã đọc được từ spec

```
Đăng nhập : GET  https://<shop>.pos365.vn/api/auth/credentials?Username=..&Password=..&format=json
             → {UserId, SessionId}; gửi kèm mọi request: Cookie: ss-id=<SessionId>; 401 → login lại
Phân trang: $top=a&$skip=(n-1)*a — response luôn có __count
Khách hàng: GET/POST /api/partners  (Partner: Code, Name, Phone, Type=1, Point, Loyalty, Debt)
            DELETE   /api/partners/{id}
Đơn hàng  : GET  /api/orders?Includes=Partner            — danh sách
            GET  /api/orders/detail?OrderId=..&Includes=Product — dòng hàng
            POST /api/orders                              — tạo đơn; nhiều phương thức thanh toán qua
                 MoreAttributes = "{\"PaymentMethods\":[{\"AccountId\":null,\"Value\":50000},
                                                        {\"AccountId\":7815,\"Value\":15000}], ...}"
                 (AccountId null = tiền mặt; khác null = tài khoản thanh toán chỉ định)
            DELETE /api/orders/{id}/void                  — hủy đơn
Sản phẩm  : GET/POST /api/products · DELETE /api/products/{id}
Metadata  : AccountList/AccountCreateOrUpdate (tài khoản thanh toán) · PointUseSave/List/Delete ·
            PartnerGroupList · toàn bộ: https://api.pos365.vn/api/metadata
```
