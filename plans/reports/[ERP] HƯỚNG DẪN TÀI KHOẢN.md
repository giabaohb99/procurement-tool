# Báo cáo kiểm thử 7 tài khoản + Hướng dẫn phân quyền Văn bản trên giao diện

**Ngày:** 24/08/2026 (vòng 1 + vòng 2 stress) · **Nhánh:** `erp-v2` (đã đồng bộ tới `37ca83d`) · **Môi trường:** local, CSDL vừa
đồng bộ từ dev · **Giao diện:** http://localhost:8083 (frontend-v2)

Báo cáo gồm hai phần: **A. kết quả kiểm thử** (từng ca, từng kết quả) và **B. hướng dẫn thao tác
trên giao diện** — chỉ nói bấm ở màn nào, cụm nào; không nói tới mã nguồn.

---

# PHẦN A — KẾT QUẢ KIỂM THỬ

## A0. Bối cảnh

- Dữ liệu: **53 văn bản** đồng bộ từ dev; bộ máy duyệt nhiều bước **đang BẬT** cho loại chứng từ
  *Văn bản*.
- Bảy tài khoản test **đã có sẵn hồ sơ ở dev**, nhưng **hai vai trò mẫu cho Văn bản chưa có** →
  đã nạp bù và gán lại vai trò + phạm vi dữ liệu cho đúng kịch bản.
- Mật khẩu bảy tài khoản = **đúng mã tài khoản** (VD: `DEMOTP` / `DEMOTP`).

| Tài khoản | Tên trên hệ | Vai trò được gán | Ý đồ kịch bản |
| --- | --- | --- | --- |
| TESTREQ | Nguyễn Văn Yêu Cầu | Nhân sự | Không dính dáng Văn bản |
| **DEMONV** | Nguyễn Nhân Viên | Nhân sự + **Văn bản — chỉ xem** | Chỉ được XEM, không thao tác |
| **DEMOTP** | Trần Trưởng Phòng | Trưởng phòng + **Văn bản — soạn & sửa** | Sửa được, **không** xóa, **không** duyệt |
| DEMOTP2 | Lý Phó Phòng | Trưởng phòng | Không dính dáng Văn bản |
| DEMOTP3 | Hồ Quyền Trưởng Phòng | Trưởng phòng | Không dính dáng Văn bản |
| **DEMOQL** | Lê Quản Lý TM | Quản lý công ty + Văn thư pháp nhân con | Có quyền *Duyệt* trên Văn bản |
| DEMOAD | Phạm Admin TM | Admin thu mua | Không dính dáng Văn bản |

## A1. Ma trận quyền vào phân hệ Văn bản — 7/7 ĐẠT

| # | Ca kiểm | Mong đợi | Kết quả thật | |
| --- | --- | --- | --- | --- |
| 1 | TESTREQ mở danh sách văn bản | Bị chặn | `403 Không có quyền: read document` | ✔ |
| 2 | DEMONV mở danh sách | Xem được, giới hạn pháp nhân | **24 văn bản** (trên tổng 53) | ✔ |
| 3 | DEMOTP mở danh sách | Xem được | 24 văn bản | ✔ |
| 4 | DEMOTP2 mở danh sách | Bị chặn | `403` | ✔ |
| 5 | DEMOTP3 mở danh sách | Bị chặn | `403` | ✔ |
| 6 | DEMOQL mở danh sách | Xem được | 24 văn bản | ✔ |
| 7 | DEMOAD mở danh sách | Bị chặn | `403` | ✔ |

Quyền thật đọc ra từ hệ khi đăng nhập:

- **DEMONV** → `xem`
- **DEMOTP** → `xem · tạo · sửa · in · xuất` (**không** xóa, **không** duyệt, **không** hủy)
- **DEMOQL** → `xem · tạo · sửa · duyệt · in · xuất`

**24/53** là bằng chứng phạm vi dữ liệu chạy đúng: ba tài khoản trên chỉ thấy văn bản của **pháp
nhân mình**, không thấy của 12 pháp nhân con.

## A2. Luồng văn bản đi qua bộ máy phê duyệt — 15/15 ĐẠT

| # | Ca kiểm | Mong đợi | Kết quả thật | |
| --- | --- | --- | --- | --- |
| 1 | DEMOTP tạo văn bản mới | Tạo được | Tạo được (#370) | ✔ |
| 2 | DEMONV **mở xem** văn bản đó | Xem được | `200` | ✔ |
| 3 | DEMONV **sửa tiêu đề** | Chặn | `403 Không có quyền: write document` | ✔ |
| 4 | DEMONV **gửi duyệt** | Chặn | `403 write document` | ✔ |
| 5 | DEMONV **xóa** | Chặn | `403 delete document` | ✔ |
| 6 | DEMOTP gửi duyệt | Sang *Đang duyệt* | *Đang duyệt* · mở phiên #79, luồng «Ban hành văn bản hành chính» | ✔ |
| 7 | **DEMOQL** (CÓ quyền *Duyệt*) bấm trả lại phiếu **không phải việc của mình** | Chặn | `403 Bạn không có việc nào đang chờ ở phiếu này` | ✔ |
| 8 | DEMOQL đi **đường tắt** một bước để ban hành | Chặn | `400 Văn bản này đang chạy trong luồng duyệt nhiều bước` | ✔ |
| 9 | DEMOTP sửa nội dung **lúc đang duyệt** | Đóng băng | `409 Phiên bản 1.0 đang trình duyệt nên khóa nội dung` | ✔ |
| 10 | Đúng người duyệt bấm **Trả lại** kèm lý do | Trả về được | Phiên = *Trả lại* | ✔ |
| 11 | Trạng thái **văn bản** sau khi trả | `9 Trả về` | `9 Trả về` | ✔ |
| 12 | Trạng thái **phiên bản** sau khi trả | `5 Trả về` | `5 Trả về` | ✔ |
| 13 | Lý do trả có lưu lại không | Có | `[Trả về] Thiếu căn cứ mục 2 — bổ sung rồi gửi lại` | ✔ |
| 14 | DEMOTP **sửa nội dung + tiêu đề** lúc đang «Trả về» | Sửa được | `200` cả hai | ✔ |
| 15 | DEMOTP **gửi duyệt lại** | Đang duyệt, **mở phiên mới** | *Đang duyệt* · phiên **#80** (không dùng lại #79) | ✔ |

Duyệt tiếp cho hết luồng:

| # | Ca kiểm | Mong đợi | Kết quả thật | |
| --- | --- | --- | --- | --- |
| 16 | Bước 1 duyệt | Phiếu đi tiếp | *Đang chạy*, chuyển sang người bước 2 | ✔ |
| 17 | Bước cuối duyệt | Phiếu xong | *Đã duyệt* | ✔ |
| 18 | Văn bản sau khi duyệt hết bước | Có hiệu lực + **được cấp số** | *Có hiệu lực* · **07/2026/TB-DEGO** | ✔ |
| 19 | Phiên bản sau ban hành | Đã duyệt + khóa | *Đã duyệt* · khóa = `true` | ✔ |
| 20 | DEMOTP **bãi bỏ** văn bản đã ban hành | Chặn (thiếu quyền *Hủy*) | `403 Không có quyền: cancel document` | ✔ |

## A3. Nhánh TỪ CHỐI và luật xóa — 9/9 ĐẠT

| # | Ca kiểm | Mong đợi | Kết quả thật | |
| --- | --- | --- | --- | --- |
| 1 | Người duyệt bấm **Từ chối** | Được | Phiên = *Từ chối* | ✔ |
| 2 | Trạng thái **văn bản** | `10 Đã từ chối` | `10 Đã từ chối` | ✔ |
| 3 | Trạng thái **phiên bản** | `6 Đã từ chối` | `6 Đã từ chối` | ✔ |
| 4 | Ghi nội dung bản đã từ chối | Khóa | `409 Phiên bản 1.0 đã bị từ chối nên khóa nội dung` | ✔ |
| 5 | Sửa thông tin chung bản đã từ chối | Khóa | `409 Văn bản đã bị từ chối nên khóa` | ✔ |
| 6 | **Gửi duyệt lại** bản đã từ chối | Chặn **và chỉ đường** | `400 … không gửi duyệt lại được. Bấm «Sao chép»` | ✔ |
| 7 | Xóa văn bản **Đã từ chối** (bằng admin) | Chặn | `400 Chỉ xóa được văn bản đang ở trạng thái nháp hoặc bị trả về` | ✔ |
| 8 | Văn bản sau khi **Trả về** | `9 Trả về` | `9 Trả về` | ✔ |
| 9 | Xóa văn bản **Trả về** (bằng admin) | Xóa được | `200` | ✔ |

## A4. Cổng kiểm tự động

| Cổng | Kết quả |
| --- | --- |
| `pytest test/backend` | **1361 xanh** · 1 bỏ qua · **3 đỏ CÓ SẴN** của nhánh B-06, không liên quan |
| `npm run typecheck` | **0 lỗi** |
| `npm run lint` | **0 lỗi** (30 cảnh báo, đều là cảnh báo cũ) |
| `npm run test` (Vitest) | **536 xanh** / 85 tệp |
| `alembic upgrade head` | Một head duy nhất, chạy sạch trong `start.sh` |

**Tổng cộng vòng 1: 37/37 ca nghiệp vụ ĐẠT.**

## A4b. Kiểm PHẠM VI PHÒNG BAN — 5/5 ĐẠT

Vòng 1 mọi tài khoản đều chung một phòng nên phạm vi *Phòng ban* **không diễn được** — đó là kiểm
kiểu happy case. Vòng này đã **đổi phòng ban cho ba trưởng phòng** (DEMOTP → *Kinh doanh*,
DEMOTP2 → *Kế toán*, DEMOTP3 → *Sản xuất*), dựng một vai trò tạm có phạm vi **Phòng ban** và tạo
hai văn bản ở hai phòng khác nhau.

| # | Ca kiểm | Mong đợi | Kết quả thật | |
| --- | --- | --- | --- | --- |
| 1 | Đặt phạm vi **SAI** (`dept_id` — không nằm trong 6 mã hợp lệ) | Không được âm thầm mở toang | **0 văn bản** — chặn sạch, log server ghi `scope chan … pham vi la khong hieu duoc` | ✔ |
| 2 | Đặt đúng `dept` → DEMOTP2 (*Kế toán*) mở danh sách | Chỉ thấy phòng mình | **1 văn bản · Phòng Kế toán** | ✔ |
| 3 | Mở văn bản **của phòng mình** | Xem được | `200` | ✔ |
| 4 | **Gõ thẳng id** văn bản phòng khác vào URL | Chặn | `404 Không tìm thấy văn bản` | ✔ |
| 5 | Lách qua đường **phiên bản** của văn bản phòng khác | Chặn | `404` | ✔ |

⚠️ Ca 1 lộ một chỗ hở nhỏ: **API nhận bừa mã phạm vi sai** (không kiểm với danh sách 6 mã hợp lệ).
Bấm trên giao diện thì không dính vì chỉ chọn được từ danh sách sổ xuống; nhưng ai gọi API hoặc nạp
dữ liệu máy móc thì tạo ra một vai trò **nhìn có quyền mà thực tế không thấy gì**, và chỉ log của máy
chủ mới nói ra được vì sao.

## A5. Ba lỗi phát hiện trong lúc kiểm — đã vá

1. **Bấm *Trả lại* xong nhãn trạng thái không đổi** (vẫn ghi «Đang duyệt») cho tới khi bấm F5 →
   nay đổi ngay tại chỗ.
2. **Văn bản đã từ chối vẫn bày nút *Lưu nội dung*** — bấm vào chỉ nhận lỗi → nay ẩn hẳn, chỉ còn
   nút *Sao chép*.
3. **Đánh số phiên bản** đếm sai gốc nên sau khi bản 2.0 bị từ chối thì hệ tạo lại đúng số 2.0 và
   báo một câu lỗi hoàn toàn không liên quan → nay đếm từ số cao nhất đã dùng.

## A6. KIỂM CHỊU TẢI & CA BIÊN (stress) — 10/14 đạt, **4 lỗi thật · ĐÃ VÁ CẢ BỐN**

Vòng 1 chỉ đi đường đẹp. Vòng này ép các tình huống hai người cùng bấm, nhấp đúp, dữ liệu quá khổ,
phiếu đã đóng, quyền bị gỡ giữa chừng.

### Đạt

| # | Ca kiểm | Kết quả thật | |
| --- | --- | --- | --- |
| S-01 | **Đua cấp số hiệu** — 8 văn bản tạo + gửi duyệt + duyệt 2 bước **song song** | Trọn luồng trong **1,18 giây** · số `08…15/2026/TB-DEGO` liên tục · **KHÔNG trùng số** | ✔ |
| S-02 | Trả về **lần hai** trên phiếu đã đóng | `400 Phiên duyệt này đã kết thúc` | ✔ |
| S-03 | Bấm **Duyệt** trên phiên **đã đóng** (phiếu cũ còn mở trên tab khác) | `400 Phiên duyệt này đã kết thúc` | ✔ |
| S-04 | Trả về với **lý do rỗng** | `400 Phải nêu lý do khi trả lại` | ✔ |
| S-05 | Trả về với lý do **toàn khoảng trắng** | `400` — không lách được bằng dấu cách | ✔ |
| S-06 | Gửi duyệt khi **nội dung trống** | `400 Nội dung văn bản còn trống` | ✔ |
| S-07 | Tạo văn bản **tên 1000 ký tự** | Bị chặn tử tế, không vỡ | ✔ |
| S-08 | **Xóa văn bản đang duyệt** (kể cả bằng admin) | `400 Chỉ xóa được văn bản nháp hoặc bị trả về` | ✔ |
| S-09 | **Gỡ sạch vai trò** của người đang đăng nhập, token cũ vẫn cầm | **403 ngay lập tức**, không có cửa sổ trễ | ✔ |
| S-10 | Dữ liệu sau khi hai người tranh nhau bấm | Trạng thái văn bản vẫn **nhất quán**, không nửa vời | ✔ |

### KHÔNG đạt — bốn lỗi dựng lại được

| # | Lỗi | Cách dựng lại | Hậu quả |
| --- | --- | --- | --- |
| **L-01** | **Nhấp đúp «Gửi duyệt» đẻ ra HAI phiếu duyệt cùng chạy** trên một văn bản | Gọi *Gửi duyệt* hai lần song song → **cả hai đều thành công**; kiểm CSDL thấy **2 phiên trạng thái «Đang chạy»** cho cùng một văn bản | Người duyệt nhận **hai phiếu trùng**; duyệt xong phiếu A là văn bản ban hành, phiếu B **vẫn chạy trên văn bản đã ban hành** — đúng cái tình huống mà chốt `chặn đường cũ` sinh ra để bịt. Chốt hiện tại nằm trong mã (đọc trạng thái rồi mới ghi) nên hai lượt chạy sát nhau lọt cả hai |
| **L-02** | **Hai người duyệt cùng lúc → một người nhận `500`** | Hai người cùng đứng ở một bước, bấm *Duyệt* và *Duyệt* (hoặc *Duyệt* và *Trả lại*) đồng thời | Máy chủ báo `500`, log ghi `Deadlock found when trying to get lock` (MySQL 1213). **Dữ liệu vẫn đúng** (chỉ một cú ăn), nhưng người thua cuộc thấy màn hình lỗi đỏ không hiểu gì — đáng lẽ phải là câu «việc này vừa được người khác xử lý, tải lại trang» |
| **L-03** | **Lý do dài quá 500 ký tự → `500`** | Trả về / từ chối với lý do 5000 ký tự | `500`, log ghi `Data too long for column 'finish_reason'`. Người duyệt dán một đoạn nhận xét dài là gặp ngay. Cần chặn ở giao diện + nới cột hoặc cắt bớt tử tế |
| **L-04** | **Xóa văn bản để lại phiếu duyệt mồ côi** | Tạo → gửi duyệt → bị **trả về** → bấm **Xóa** (đúng luật, nút có trên màn hình) → phiếu duyệt **vẫn còn**, trỏ tới văn bản không còn tồn tại | Rác tích tụ trong bảng phiếu duyệt; báo cáo/thống kê theo phiếu duyệt đếm cả những phiếu không còn chứng từ. Dựng lại được trên đường hoàn toàn hợp lệ (văn bản #390 / phiếu #98) |

**Ba lỗi L-01, L-02, L-04 nằm ở bộ máy duyệt DÙNG CHUNG**, nên khi bật bộ máy cho Thu mua thì
Yêu cầu mua hàng / Đơn mua hàng sẽ dính y hệt.

### ĐÃ VÁ CẢ BỐN — chạy lại đúng kịch bản đã bắt lỗi

| Lỗi | Cách chữa | Chạy lại kịch bản cũ |
| --- | --- | --- |
| **L-01** | Ép ở **tầng dữ liệu**, y cách cột `open_slot` của phiên bản văn bản: cột sinh `running_slot` + `UNIQUE(entity, running_slot)` → mỗi chứng từ nhiều nhất một phiếu **đang mở**. Va chạm dịch thành **409** kèm câu chỉ việc | Nhấp đúp: **1 lượt ăn / 1 lượt nhận `409` «Phiếu duyệt … vừa được mở bởi một lượt bấm khác. Tải lại trang…»** |
| **L-02** | 5 endpoint thao tác phiếu đi qua một chốt chung: kẹt khóa → cuộn lại → **409** «Việc này vừa được người khác xử lý cùng lúc. Tải lại trang…» | Chạy **3 lượt đua**, lượt nào cũng: một cú ăn, một cú `409`, văn bản về **một** trạng thái nhất quán. Hết `500` |
| **L-03** | Chặn ngay ở cửa: trần **1000** ký tự = **đúng** bề rộng cột, kèm bài kiểm chốt hai số này không lệch nhau. Giao diện chặn `maxLength` + hiện bộ đếm khi vượt 80% | Lý do 5000 ký tự → **`422` báo ô nào sai**, không còn `500` |
| **L-04** | Xóa chứng từ thì dọn luôn phiếu duyệt + việc + dấu vết, **trong cùng giao dịch** | Tạo → gửi duyệt → trả về → xóa → hỏi lại phiếu: **`404` — đã dọn** |

⚠️ **Một bài học lấy được trong lúc vá L-02.** Bản chữa đầu tiên có **thử lại một lần** — cách chữa
kẹt khóa thường thấy — và nó **sai ở đúng chỗ nguy hiểm nhất**: A bấm *Duyệt* bước 1, B bấm
*Trả lại* cũng ở bước 1 nhưng kẹt khóa; chạy lại thì phiếu đã sang **bước 2**, nơi B mới là người
duyệt, nên cú *Trả lại* của B **ăn ở bước 2** — một bước B chưa hề mở ra đọc, và **cả hai cú cùng
"thành công"**. Đã bỏ nhịp thử lại: chữ ký phải bám đúng nội dung người ta đọc lúc bấm, nên thà bắt
người thua tải lại trang rồi tự quyết định lần nữa.

**Cổng kiểm sau khi vá:** pytest **1373 xanh** (thêm 12 ca mới cho bốn lỗi này) · `npm run check`
**0 lỗi · 536 test xanh** · `start.sh` migrate + seed chạy sạch, alembic một head.

## A7. Dữ liệu sau khi kiểm — ĐÃ DỌN SẠCH

- Bãi bỏ #370, xóa #371 và **toàn bộ 18 văn bản rác** của các vòng kiểm.
- Xóa **20 phiếu duyệt mồ côi** (kèm việc và dấu vết của chúng).
- Xóa vai trò tạm `test_vanban_phong`, trả DEMOTP2 về vai trò cũ.
- **CSDL về đúng trạng thái sau khi đồng bộ từ dev: 53 văn bản**, phân bố trạng thái y như cũ
  (31 nháp · 19 có hiệu lực · 1 đã thay thế · 2 bãi bỏ), **0 phiếu mồ côi**.
- Vẫn giữ lại (cố ý): **phòng ban mới của ba trưởng phòng** — Kinh doanh / Kế toán / Sản xuất, để
  lần sau còn diễn được phạm vi *Phòng ban*.
- Một dấu vết không xóa được: bộ đếm số hiệu `TB-DEGO` đã nhảy tới **15** (số đã cấp thì không lùi).
  Văn bản thật tiếp theo sẽ mang số 16.

---

# PHẦN B — HƯỚNG DẪN TRÊN GIAO DIỆN

## B0. Quyền của một người được quyết bởi BA tầng

| Tầng | Trả lời câu | Đặt ở màn |
| --- | --- | --- |
| 1. **Vai trò** | Được làm những **hành động** gì (xem/tạo/sửa/xóa/duyệt/hủy/in/xuất) | Nhân sự ▸ **Phân quyền tài khoản** ▸ tab *Vai trò & quyền* |
| 2. **Phạm vi dữ liệu** | Nhìn thấy **bao nhiêu** dữ liệu (của mình / phòng / pháp nhân / tất cả) | Nhân sự ▸ **Phân quyền tài khoản** ▸ tab *Người dùng* → *Sửa phân quyền* → nút **Phạm vi** |
| 3. **Quyền theo từng văn bản** | Riêng văn bản NÀY thì ai đọc được | Ngay trên màn **Tạo văn bản** / chi tiết văn bản — khối *Quyền truy cập* |

Bấm nút *Duyệt* trong luồng là chuyện **thứ tư**, không nằm trong ba tầng trên — xem mục B4.

## B1. Cho một tài khoản vào được phân hệ Văn bản

### Bước 1 — Tạo (hoặc chọn) vai trò

**Vào: phân hệ Nhân sự ▸ nhóm QUẢN TRỊ ▸ «Phân quyền tài khoản» ▸ tab «Vai trò & quyền»**

- Cột trái là danh sách vai trò, mỗi dòng có tên + mã. Bấm **+ Thêm** để tạo vai trò mới, hoặc bấm
  vào một vai trò có sẵn để sửa.
- Bên phải hiện **ma trận quyền**: mỗi dòng là một chức năng, các cột là
  **XEM · TẠO · SỬA · XÓA · DUYỆT · HỦY · IN · XUẤT** và cột cuối là **PHẠM VI**.
- Năm dòng của phân hệ Văn bản (gõ vào ô tìm cho nhanh):
  - **Văn bản (Văn thư)** ← dòng chính
  - **Loại văn bản (Văn thư)**
  - **Sổ văn bản (Văn thư)**
  - **Đơn vị gửi nhận (Văn thư)**
  - **Mức mật / Độ khẩn (Văn thư)**
- Tick xong bấm **Lưu quyền** (góc phải trên).

**Hai vai trò mẫu đã dựng sẵn, dùng luôn được:**

| Vai trò trên màn hình | Tick những gì | Người dùng thấy gì |
| --- | --- | --- |
| **Văn bản — chỉ xem** | *Văn bản*: **XEM** · phạm vi *Công ty*<br>*Loại văn bản*, *Sổ văn bản*: XEM | Mở được danh sách và đọc nội dung. **Không** nút *Tạo văn bản*, **không** *Xuất Excel*, mở chi tiết ra **không có thanh soạn thảo** |
| **Văn bản — soạn & sửa (không xóa, không duyệt)** | *Văn bản*: **XEM · TẠO · SỬA · IN · XUẤT** · phạm vi *Công ty* | Có *Tạo văn bản*, *Lưu nội dung*, *Nhập tệp*, *Gửi duyệt*, *Sao chép*. **Không** nút *Xóa*, **không** *Duyệt / Trả lại*, **không** *Bãi bỏ* |

⚠️ **Bốn dòng danh mục phải tick XEM kèm**, nếu không thì màn *Tạo văn bản* sẽ trống sạch các ô bắt
buộc và không lưu nổi: **Loại văn bản**, **Sổ văn bản**, **Công ty (pháp nhân)**, **Phòng ban**,
**Nhân viên**.

### Bước 2 — Gán vai trò cho người + đặt phạm vi

**Vào: cùng màn đó ▸ tab «Người dùng»**

- Bảng liệt kê: **Người dùng · Phòng ban · Vai trò**. Lọc nhanh bằng ba ô
  *Tất cả phòng ban* / *Tất cả vai trò* / *Tất cả tình trạng*, hoặc gõ tên/mã vào ô tìm.
- Bấm biểu tượng **cây bút — «Sửa phân quyền»** ở cuối dòng (biểu tượng **ổ khóa** bên cạnh là
  *Khóa tài khoản*, đừng bấm nhầm).
- Sang màn **Vai trò & phạm vi**: tick vai trò muốn gán → bấm **Lưu vai trò** (góc phải trên).
- Vai trò **đã lưu** sẽ mọc thêm nút **Phạm vi** ở bên phải dòng đó — bấm vào để giới hạn
  **công ty / phòng ban / nhân sự** riêng cho tài khoản này.

⚠️ Vai trò để phạm vi *Công ty* mà tài khoản **chưa khai dòng phạm vi** thì hệ **chặn sạch** cho
chắc ăn, người dùng sẽ thấy danh sách rỗng. Gán vai trò xong nhớ bấm **Phạm vi** một lần.

⏱️ Đổi quyền xong, người đang đăng nhập cần **đăng xuất/đăng nhập lại** (hoặc chờ khoảng một phút)
thì quyền mới ăn.

## B2. Tạo một văn bản

**Vào: phân hệ Văn bản ▸ nhóm NGHIỆP VỤ ▸ «Văn bản» ▸ nút «Tạo văn bản»** *(nút chỉ hiện với người
có quyền TẠO)*

Màn tạo đi theo **3 bước**:

**Bước 1 — Thông tin chính.** Ô có dấu **\*** đỏ là bắt buộc:
- **Tên văn bản** \*
- **Loại văn bản** \* — quyết định kiểu số hiệu và mức mật mặc định
- **Văn bản mẫu** — chọn mẫu có sẵn, danh sách tự lọc theo loại
- **Pháp nhân ban hành** \* — nơi **ĐỨNG TÊN**, không phải nơi của người đang gõ
- **Phòng chủ trì** \*
- **Vào sổ** — vào sổ thì **mọi thành viên của sổ đó đọc được**
- **Số hiệu** — chỉ **xem trước**; số thật do hệ cấp lúc văn bản được duyệt
- **Người chịu trách nhiệm nội dung** \* · **Người soạn**
- Khối **Quyền truy cập** — mặc định: ai có phạm vi bao trùm văn bản thì đọc được. Cần chia riêng
  cho vài người thì bấm **Phân quyền nâng cao**.

**Bước 2 — Phạm vi áp dụng.** Văn bản áp cho những pháp nhân nào, có **tách bản riêng** cho pháp
nhân con hay không.

**Bước 3 — Thông tin bổ sung.** Mức mật, ngày hiệu lực, từ khóa, tệp đính kèm.

Xong bấm **Tiếp tục** qua từng bước rồi lưu. Văn bản ra đời ở trạng thái **Nháp**.

**Soạn nội dung:** mở văn bản ▸ tab **Soạn thảo** — gõ như Word, hệ *tự lưu trong lúc soạn*, hoặc
bấm **Lưu nội dung**. Có sẵn Word/PDF thì bấm **Nhập tệp** để đưa vào.

**Trình duyệt:** bấm **Gửi duyệt**. Văn bản sang **Đang duyệt** và **khóa nội dung** (băng vàng sẽ
nói rõ vì sao). Muốn sửa lại: tab **Phê duyệt** ▸ **rút phiếu** (về *Nháp*), hoặc chờ người duyệt
**trả về**.

## B3. Phân quyền / cấu hình luồng phê duyệt

**Vào: phân hệ Phê duyệt ▸ nhóm CẤU HÌNH.** Phân hệ này chỉ hiện với người có quyền trên
*Luồng duyệt*, và nó **chỉ để cấu hình** — không phải chỗ đi duyệt hằng ngày.

### B3.1 — Khai luồng: «Luồng duyệt»

Bảng liệt kê: **Tên luồng · Loại chứng từ · Pháp nhân · Áp khi · Số bước**. Bấm **+ Tạo luồng**, hoặc
bấm vào một luồng để mở **sơ đồ**.

Trong sơ đồ:

- Trên cùng là **Người trình duyệt**, dưới cùng là **Hoàn tất / Ban hành**; ở giữa là các bước.
- **+ Thêm bước duyệt** (góc phải) hoặc bấm dấu **+** trên đường nối để chèn bước vào giữa.
- Bấm vào một bước → mở bảng **Thuộc tính** bên phải:
  - **Tên bước** — VD *Trưởng bộ phận duyệt nội dung*
  - **Ai duyệt bước này** — chọn một trong:
    **Người cụ thể · Theo vai trò · Trưởng bộ phận người nộp · Lên N cấp quản lý ·
    Người đại diện pháp nhân · Lấy từ một ô trên phiếu**
  - **Chọn người duyệt** — thêm nhiều người, mỗi người một thẻ
  - **Nhiều người thì** — *Một người duyệt là đủ* hay bắt tất cả phải duyệt
  - **Tùy chỉnh thêm** — hạn duyệt (VD 8h) và xử trí khi không tìm ra người duyệt
  - Bấm **Lưu bước**
- Nút **Cài đặt luồng** (góc phải trên) đặt phần khung của luồng:
  - **Loại chứng từ** (khóa sau khi tạo) · **Tên luồng** \*
  - **Pháp nhân áp dụng** — ⚠️ *Tất cả pháp nhân* **không dùng cho bản clone**; bản riêng của pháp
    nhân con **bắt buộc** có luồng khai đúng pháp nhân đó, thiếu thì gửi duyệt sẽ báo lỗi
  - **Mã luồng** · **Độ ưu tiên** (số lớn xét trước) · điều kiện **áp dụng khi**

### B3.2 — Bật bộ máy: «Bật bộ máy duyệt»

Danh sách các loại chứng từ kèm công tắc:

- Gạt **BẬT** → hiện nhãn xanh **Bộ máy mới**: phiếu tạo từ giờ chạy theo luồng đã khai.
- Để **TẮT** → nhãn **Đường duyệt cũ**.
- Hiện tại **Văn bản đang BẬT** (1/6 loại), năm loại còn lại đi đường cũ.
- Tắt giữa chừng **không cắt ngang** phiếu đang chạy; chỉ phiếu tạo sau đó mới quay về đường cũ.

## B4. Ai bấm được nút *Duyệt / Trả lại*?

Đây là chỗ hay hiểu nhầm nhất, và bài kiểm ở phần A đã xác nhận:

> Bấm được hay không **KHÔNG** do quyền *DUYỆT* trong ma trận vai trò, mà do **có việc đang chờ
> mình trong luồng hay không**.

- DEMOQL **có** tick *DUYỆT* nhưng không nằm trong luồng → bấm vào nhận
  `403 Bạn không có việc nào đang chờ ở phiếu này`.
- Muốn một người duyệt được: **thêm họ vào một bước** ở *Phê duyệt ▸ Luồng duyệt*.
- Quyền *DUYỆT* trong ma trận chỉ mở **đường một bước** (dùng khi bộ máy TẮT), và khi bộ máy đang
  BẬT thì đường đó bị khóa lại (`400 Văn bản này đang chạy trong luồng duyệt nhiều bước`).

**Người duyệt thao tác ở đâu:** phân hệ **Văn bản ▸ «Chờ tôi duyệt»** (có huy hiệu đếm số việc),
hoặc mở thẳng văn bản — băng xanh **«Đang chờ bạn duyệt»** trên đầu trang có nút
**Duyệt / Trả lại**. Hộp thoại cho bốn lựa chọn:

| Lựa chọn | Nghĩa | Văn bản thành |
| --- | --- | --- |
| **Duyệt** | Sang bước kế tiếp | Duyệt hết bước → *Có hiệu lực* + được cấp số |
| **Trả lại** *(bắt buộc nhập lý do)* | Phiếu còn sống — người nộp sửa rồi gửi lại | **Trả về** — sửa được, **Gửi duyệt** lại được |
| **Từ chối** *(bắt buộc nhập lý do)* | Phiếu dừng hẳn | **Đã từ chối** — khóa sửa, muốn làm lại thì **Sao chép** |
| **Ghi ý kiến** | Không đổi trạng thái | giữ nguyên |

Người soạn mở văn bản bị trả sẽ thấy **băng đỏ** ghi *lý do* và câu *«Sửa lại nội dung rồi bấm Gửi
duyệt lần nữa»*; dấu vết đầy đủ nằm ở tab **Phê duyệt**.

## B5. Bảng tra nhanh — muốn thế này thì tick thế kia

| Muốn tài khoản… | Ở tab *Vai trò & quyền*, dòng **Văn bản (Văn thư)** tick | Ghi chú |
| --- | --- | --- |
| Chỉ đọc, không đụng gì | XEM | Không tick IN/XUẤT nếu không muốn họ mang tài liệu ra ngoài |
| Soạn và sửa, không được xóa | XEM · TẠO · SỬA (+ IN · XUẤT nếu cần) | Gửi duyệt tính là **SỬA** |
| Được xóa bản nháp | thêm XÓA | Chỉ xóa được văn bản *Nháp* hoặc *Trả về* và **chưa cấp số** |
| Được bãi bỏ văn bản đã ban hành | thêm HỦY | Đã cấp số thì chỉ bãi bỏ, không xóa |
| Được duyệt | thêm DUYỆT **và** thêm họ vào một bước trong *Luồng duyệt* | Thiếu vế thứ hai thì vẫn không bấm được |
| Chỉ thấy văn bản của pháp nhân mình | cột PHẠM VI = *Công ty* | Rồi bấm **Phạm vi** ở tab *Người dùng* để chỉ đúng pháp nhân |

---

## Việc đã chốt và đã làm ở vòng 2

1. ✔ **Đổi phòng ban ba trưởng phòng** → Kinh doanh / Kế toán / Sản xuất, và kiểm phạm vi
   *Phòng ban* thật (mục A4b). Không còn kiểu kiểm một phòng cho cả bảy người.
2. ✔ **Dọn sạch dữ liệu kiểm thử** (mục A7) — CSDL về đúng 53 văn bản như lúc đồng bộ.
3. ✔ **Thêm vòng kiểm chịu tải và ca biên** (mục A6) — 14 ca, bắt được **4 lỗi thật**.
4. ✔ **Vá cả bốn lỗi** (CR-145) và chạy lại đúng kịch bản đã bắt lỗi để chứng minh — xem cuối mục A6.

## Câu chưa chốt

1. **API nhận bừa mã phạm vi sai** (mục A4b ca 1) — có nên kiểm với danh sách 6 mã hợp lệ và trả
   `400` không? Hiện chỉ log máy chủ mới biết, còn người quản trị thì thấy một vai trò «có quyền mà
   không thấy gì». Chưa sửa vì nằm ngoài bốn lỗi bạn duyệt.
3. **Ba bài kiểm đỏ sẵn** của nhánh B-06 (`test_expected_date_sync`, hai bài `test_luong_duyet_thu_mua`)
   — không thuộc phạm vi đợt này, cần người phụ trách B-06 xử lý.
4. Toàn bộ thay đổi mã **chưa commit**.
