# 13 — KẾ HOẠCH BẢY MÀN CÒN LẠI CỦA ERP V2

**Bản 1.1 — 19/08/2026.** *(Bản 1.0 cùng ngày; bản này ghi tình trạng sau khi làm xong MC-1 … MC-4.)*

> **Tình trạng — 19/08/2026.** **MC-1, MC-2, MC-3, MC-4 đã xong** (CR-094), làm gộp một đợt theo
> yêu cầu của khách. **MC-5, MC-6, MC-7 khách cho hoãn**, chưa hẹn ngày. Ba chỗ lệch so với kế
> hoạch ghi ở mục 4 — đọc trước khi rà lại.

Tệp [`12`](./12-ke-hoach-erp-v2-da-phap-nhan.md) mục 2.6 gạt sáu màn sang **"chưa xếp lịch"** rồi
để đó. Tệp này xếp lịch cho chúng, và bổ sung **một màn thứ bảy mà `12` bỏ sót: Đặt lại mật khẩu** —
không phải màn thiếu cho đủ bộ, mà là **một luồng đang gãy**: `frontend-v2` có màn *Quên mật khẩu*,
người dùng bấm gửi, nhận được thư, bấm vào đường dẫn trong thư và rơi vào trang 404.

Đây là **bản thực thi**, chia nhỏ để nhiều người làm song song. Mã hạng mục **MC-1** đến **MC-7**
(MC = màn còn lại). Ước lượng ghi theo **ngày công cho một người**.

---

## 0. Ba kết luận đọc trước

1. **Không phải viết backend dòng nào.** Cả bảy màn đều đã có endpoint chạy thật ở bản cũ — đây
   thuần là việc dựng lại giao diện. Xem bảng đối chiếu ở mục 3.
2. **13,5 – 18,5 ngày công** cho cả bảy, chia được cho tối đa ba người làm song song vì các màn
   không đụng nhau (chỉ MC-4 và MC-5, MC-6 chạm chung một tệp: `modules/system/routes.tsx`).
3. **Làm hết bảy màn này vẫn CHƯA tắt được `frontend/`.** Phần chặn nằm ở chỗ khác: Yêu cầu thanh
   toán (P3) và bộ danh mục (P4). Bảy màn này là điều kiện **cần**, không phải điều kiện đủ.

---

## 1. Đo hiện trạng — 19/08/2026

Đối chiếu menu bản cũ (`frontend/src/layouts/AppLayout.tsx`, 24 mục) và các route trực tiếp
(`frontend/src/App.tsx`) với bảng đăng ký phân hệ của v2 (`src/app/router/module-registry.ts`).
**Còn 17 màn chưa có ở v2**, chia về bốn nơi:

| Nhóm | Màn | Xử lý ở đâu |
|---|---|---|
| **Tệp này** | Đặt lại mật khẩu · Thông báo · Trang cá nhân · Cấu hình hệ thống · Sao lưu CSDL · Quản lý Import · Phiếu hỗ trợ | **MC-1 … MC-7** |
| Đã có lịch ở `12` | Yêu cầu thanh toán + phiếu in | P3 |
| Đã có lịch ở `12` | Sản phẩm · Hợp đồng *(+ chi tiết)* · Kho · Đơn vị tính · Phân loại · **chi tiết** Nhà cung cấp | P4 |
| Đã có lịch ở `12` | Phân công phụ trách → *Định tuyến phân loại về đơn vị xử lý* | P7 |
| **Đã quyết bỏ** | Tiến độ báo giá · Màn xử lý Yêu cầu báo giá | `12` mục 2.7 |

Hai ghi chú để khỏi đếm nhầm:

- **Chi tiết Nhà cung cấp mới có một nửa.** v2 có danh sách + hộp thoại sửa
  (`modules/production/pages/supplier-list-page.tsx`); bản cũ là trang riêng có tab *Hợp đồng*,
  *Lịch sử mua hàng*, *KPI giao hàng*. Hằng số `appRoutes.production.supplierDetail` đã khai
  nhưng **chưa route nào dùng** — dễ tưởng là đã xong.
- **Màn "Chứng từ"** (`frontend/src/pages/Documents.tsx`, kho tệp đính kèm gom theo đơn mua hàng)
  không nằm trong menu và **chưa có ai quyết** port hay bỏ. Ở v2 tệp đính kèm đã hiện ngay trong
  từng chứng từ, nên nhiều khả năng là bỏ. Ghi ở mục 7.

---

## 2. Bốn quyết định thiết kế — chốt ngày 19/08/2026

| | Quyết định | Vì sao |
|---|---|---|
| **QĐ-1** | **Thông báo và Trang cá nhân đặt ở tầng chung**, ngoài mọi phân hệ: `/notifications` và `/me`, nằm trong `LauncherLayout` của `app-router.tsx` | Khách chốt: *"thông báo chung trên tất cả luôn, khỏi chia ra app"*. Thông báo vốn đã trộn nhiều phân hệ (thu mua, văn thư, duyệt) — chia theo phân hệ là bắt người dùng mở ba chỗ để đọc hết một hộp thư |
| **QĐ-2** | **Cấu hình hệ thống nằm trong phân hệ Quản trị** (`modules/system`, đang `enabled: false`, `entity: 'setting'`), đường dẫn `/system/settings`. Bật phân hệ này ở MC-4 | Đúng ý *"để một cục riêng"*. Phân hệ đã có sẵn khung, chỉ chờ có màn thật. MC-5 và MC-6 đổ vào cùng chỗ, nên bật một lần dùng cho ba màn |
| **QĐ-3** | **Màn cấu hình dựng động từ dữ liệu backend trả về**, không viết cứng từng ô | Đây là câu trả lời cho *"có cách nào flex"* — xem mục 4, MC-4 |
| **QĐ-4** | **Trang cá nhân v2 bỏ hai tab của bản cũ**: *Việc cần làm* và *Yêu cầu hỗ trợ của tôi* | *Việc cần làm* đã có nguyên một màn ở v2 (`/approval/my-tasks`, I17) — dựng lại là hai chỗ đếm cùng một tập việc, lệch nhau lúc nào không biết. Tab hỗ trợ chờ MC-7; khi có thì thêm lại |

---

## 3. Bảy màn — endpoint đã có sẵn

Không hạng mục nào trong bảng này cần thêm route backend, thêm bảng, hay migration.

| Mã | Màn | Endpoint đã chạy | Bản cũ (dòng) |
|---|---|---|---|
| MC-1 | Đặt lại mật khẩu | `POST /api/auth/reset-password` | 103 |
| MC-2 | Thông báo | `GET /api/notifications` · `POST /{id}/read` · `POST /read-all` · `DELETE /read` · `DELETE /{id}` | 127 |
| MC-3 | Trang cá nhân | `GET /api/auth/me` · `POST /change-password` · `POST /avatar` · `POST` + `DELETE /signature` | 790 *(9 tệp)* |
| MC-4 | Cấu hình hệ thống | `GET` + `PUT /api/settings` · `POST /test-email` · `POST /test-storage` | 139 |
| MC-5 | Sao lưu CSDL | 4 route ở `modules/backup/controller.py` | 167 |
| MC-6 | Quản lý Import | 7 route ở `modules/import_tool/controller.py` | 556 *(2 tệp)* |
| MC-7 | Phiếu hỗ trợ | 7 route ở `modules/ticket/controller.py` | 560 *(2 tệp)* |

---

## 4. Thứ tự làm

Sắp theo **rẻ trước, và trong nhóm rẻ thì cái đang gãy đi trước**. Ai làm một mình thì chạy từ
trên xuống; chia ba người thì cột "Chạy song song được với" cho biết ghép thế nào.

| Mã | Màn | Ngày công | Chạy song song được với | Tình trạng |
|---|---|---|---|---|
| **MC-1** | Đặt lại mật khẩu | 0,5 – 1 | tất cả | **Xong** (CR-094) |
| **MC-2** | Thông báo | 1 – 1,5 | tất cả | **Xong** (CR-094) |
| **MC-3** | Trang cá nhân | 2 – 3 | tất cả | **Xong** (CR-094) |
| **MC-4** | Cấu hình hệ thống *(+ bật phân hệ Quản trị)* | 2 – 3 | MC-1, MC-2, MC-3 | **Xong** (CR-094) |
| **MC-5** | Sao lưu CSDL | 1,5 – 2 | mọi thứ **trừ** MC-4 *(cùng sửa `system/routes.tsx`)* | Hoãn |
| **MC-6** | Quản lý Import | 3 – 4 | mọi thứ **trừ** MC-4 | Hoãn |
| **MC-7** | Phiếu hỗ trợ | 3 – 4 | tất cả | Hoãn |
| | **Cộng** | **13,5 – 18,5** | | còn **7,5 – 10** |

### Ba chỗ đã làm khác kế hoạch — 19/08/2026

Ghi lại để lần rà sau khỏi tưởng là làm hụt:

1. **MC-3 bỏ ô bật thông báo đẩy.** `frontend-v2` chưa có PWA, chưa có service worker, chưa có
   VAPID — cả hạ tầng đẩy chỉ tồn tại ở bản cũ. Dựng một ô bật cho thứ chưa tồn tại là thêm nút
   bấm không làm gì. Khi nào v2 có đẩy thật thì thêm ô đó vào Trang cá nhân, không phải làm lại
   trang.
2. **Menu phân hệ Quản trị khai HAI mục, không phải ba** như §5 dự tính. Mục menu trỏ vào màn
   MC-5/MC-6 chưa tồn tại thì bấm ra 404 — tệ hơn là không có mục. Làm MC-5/MC-6 thì thêm mục vào
   `nav`, một dòng mỗi màn.
3. **Trang tổng quan Quản trị nói thẳng hai màn đang nợ** (Sao lưu CSDL, Quản lý Import) để người
   dùng khỏi lục menu tìm.

### MC-1 — Đặt lại mật khẩu · 0,5–1 ngày

**Làm gì.** Thêm route công khai `/reset-password` vào `AuthLayout` (cạnh `login` và
`forgot-password`); trang đọc `?token=`, nhập mật khẩu mới hai lần, gọi
`POST /api/auth/reset-password`, xong thì chuyển về màn đăng nhập.

**Tệp.** `core/auth/pages/reset-password-page.tsx` · `core/auth/reset-password-schema.ts` (theo
đúng khuôn `forgot-password-schema.ts` đã có) · thêm `resetPassword` vào `shared/constants/app-routes.ts`
· thêm 1 route vào `app/router/app-router.tsx`.

**Bẫy.** Thư gửi cho người dùng dựng đường dẫn từ biến `FRONTEND_URL`
(`backend/app/core/config.py`, mặc định trỏ **bản cũ**). Ngày nào v2 thay bản cũ thì phải đổi biến
này ở `.env` của cả prod lẫn dev, nếu không thư vẫn dẫn về giao diện cũ. Ghi vào việc deploy, đừng
để lúc đó mới tìm.

**Điều kiện đủ.** Token hợp lệ đổi được mật khẩu và đăng nhập lại được bằng mật khẩu mới · token
rỗng/sai/hết hạn hiện lỗi rõ ràng chứ không trắng màn · hai ô mật khẩu không khớp thì chặn ngay ở
giao diện · test khẳng định trang **không** gọi API khi thiếu token.

### MC-2 — Thông báo · 1–1,5 ngày

**Làm gì.** Trang `/notifications` ở tầng chung (QĐ-1): danh sách phân trang, hai tab
*Tất cả* / *Chưa đọc*, ô tìm kiếm, đánh dấu đã đọc từng cái và tất cả, xóa cái đã đọc. Bấm vào một
thông báo thì đi tới chứng từ tương ứng.

**Đỡ được nhiều.** Tầng gọi API đã viết sẵn cho cái chuông ở `shared/notifications/`
(`notification-api.ts`, `use-notifications.ts`, `notification-link.ts`, `notification-types.ts`) —
trang này chỉ là một khung hiển thị khác trên cùng bộ dữ liệu đó. Tab và ô tìm kiếm lưu trên URL
bằng `shared/hooks/use-url-param-state.ts`.

**Tệp.** `app/pages/notification-page.tsx` · 1 route trong `LauncherLayout` · thêm `notifications`
vào `app-routes.ts` · cái chuông trỏ *"Xem tất cả"* sang trang này.

**Điều kiện đủ.** Đọc một thông báo thì số chưa đọc trên chuông giảm ngay, không phải tải lại trang
· bấm vào thông báo của phiếu đã bị xóa không làm vỡ trang · danh sách rỗng có màn trống tử tế ·
lọc *Chưa đọc* rồi F5 vẫn giữ đúng bộ lọc.

### MC-3 — Trang cá nhân · 2–3 ngày

**Làm gì.** Trang `/me` ở tầng chung: thẻ danh tính (ảnh đại diện, họ tên, chức danh, phòng ban,
vai trò), thông tin cá nhân, **đổi mật khẩu**, **chữ ký** (tải lên / xem / xóa), và ô bật **thông
báo đẩy**. Theo QĐ-4, **không** dựng lại tab *Việc cần làm* — thay bằng một đường dẫn sang
`/approval/my-tasks`.

> **Đã làm khác:** ô bật **thông báo đẩy bị bỏ** — `frontend-v2` chưa có PWA/service worker nào để
> mà bật. Xem mục 4, chỗ lệch số 1.

**Tệp.** `app/pages/profile-page.tsx` + `app/components/profile/` (thẻ danh tính, đổi mật khẩu,
chữ ký, thông báo đẩy) · 1 route trong `LauncherLayout` · `me` trong `app-routes.ts`.

**Bẫy.** Đổi mật khẩu thành công thì backend **không** thu hồi phiên hiện tại — đừng tự đăng xuất
người dùng, và cũng đừng quên báo cho họ biết là các thiết bị khác vẫn đang đăng nhập. Ảnh đại diện
và chữ ký là tải tệp thật: kiểm kiểu tệp và dung lượng ở giao diện trước khi gửi, và sau khi đổi
phải làm mới bộ nhớ đệm của `auth-store` chứ không thì ảnh cũ còn nguyên tới lần đăng nhập sau.

**Điều kiện đủ.** Đổi mật khẩu sai mật khẩu cũ báo lỗi đúng chỗ · tải chữ ký lên rồi vào phiếu in
thấy đúng chữ ký mới · xóa chữ ký xong phiếu in không còn ảnh hỏng · ảnh đại diện đổi xong hiện
ngay trên thanh tiêu đề.

### MC-4 — Cấu hình hệ thống · 2–3 ngày

**Đây là hạng mục có phần thiết kế đáng bàn nhất — mục 5 viết riêng.**

**Làm gì.** Bật phân hệ **Quản trị** (`modules/system/routes.tsx`: `enabled: true`, thêm `nav` và
`routes`, viết trang tổng quan), rồi dựng `/system/settings`: ba nhóm *Quy trình duyệt*,
*Email (SMTP)*, *Lưu trữ (R2/S3)*, hai nút gửi thử email và kiểm tra lưu trữ.

**Tệp.** `modules/system/routes.tsx` · `modules/system/pages/system-dashboard-page.tsx` ·
`modules/system/pages/setting-page.tsx` · `modules/system/api/setting-api.ts` ·
`modules/system/components/setting-field.tsx` · `system.settings` trong `app-routes.ts`.

**Điều kiện đủ.** Tài khoản không có quyền `setting.read` **không thấy** phân hệ Quản trị trên màn
chọn phân hệ · có `read` mà không có `write` thì xem được, mọi ô khóa · **không ô nào hiện giá trị
thật của khóa bí mật** (xem mục 5) · lưu xong tải lại trang thấy đúng giá trị vừa lưu · nút gửi thử
email báo được cả trường hợp thành công lẫn thất bại kèm lý do.

### MC-5 — Sao lưu CSDL · 1,5–2 ngày

**Làm gì.** `/system/backups`: danh sách bản sao lưu (thời điểm, dung lượng, ai tạo, trạng thái),
nút tạo bản mới, tải về, xóa. Lịch chạy tự động do Celery lo, màn này chỉ xem và bấm tay.

**Bẫy.** Bảng `tab_db_backup` ghi lại cả những bản đã bị xóa khỏi ổ đĩa — trạng thái phải hiện rõ,
không thì người dùng bấm tải về một tệp không còn tồn tại. Nút tạo bản sao lưu phải chặn bấm hai
lần: chạy song song hai lần kết xuất là chuyện đã gặp ở bản cũ.

**Điều kiện đủ.** Tạo được bản sao lưu và tải về mở ra đúng tệp · thao tác xóa có hỏi lại · người
không có quyền không thấy mục này trên menu.

### MC-6 — Quản lý Import · 3–4 ngày

**Làm gì.** `/system/import-batches` + trang chi tiết một đợt nhập: chọn tệp, xem trước, đối chiếu
dòng lỗi, xác nhận nạp, xem lịch sử thay đổi từng dòng.

**Vì sao đắt.** Bản cũ 556 dòng và là màn nhiều bước nhất trong nhóm này: tải tệp lên → máy chủ
đọc thử → bày bảng lỗi → người dùng sửa hoặc bỏ dòng → xác nhận. Mỗi bước một trạng thái, và trạng
thái đó phải sống sót qua F5.

**Điều kiện đủ.** Nạp một tệp có dòng lỗi thì lỗi hiện đúng số dòng và đúng lý do · bỏ ngang giữa
chừng không để lại đợt nhập treo · nạp lại đúng tệp đó lần hai không nhân đôi dữ liệu.

### MC-7 — Phiếu hỗ trợ · 3–4 ngày

**Làm gì.** Danh sách phiếu + chi tiết có trao đổi qua lại, đổi trạng thái, gán người phụ trách,
đính kèm ảnh. Phiếu này ở bản cũ có **cờ tắt/bật** (`config/features.ts`, prod đang bật) — v2 dùng
cờ `enabled` của phân hệ cho việc đó, không cần cờ riêng.

**Kèm theo.** Xong MC-7 thì thêm lại tab *Yêu cầu hỗ trợ của tôi* vào MC-3 (QĐ-4), và gán vai trò
`support` cho người phụ trách — việc này đang nợ từ trước, không phải việc mới.

**Điều kiện đủ.** Người gửi chỉ thấy phiếu của mình, người có vai trò `support` thấy tất cả · trả
lời một phiếu thì người kia nhận được thông báo · đổi trạng thái có ghi vào nhật ký thao tác.

---

## 5. Cấu hình hệ thống — viết chỗ nào cho hợp lý *(trả lời QĐ-3)*

Câu hỏi đặt ra là: mai mốt thêm một cấu hình nữa thì phải sửa mấy chỗ?

**Câu trả lời: một chỗ, và nằm ở backend.** Chỗ đó đã có sẵn từ lâu —
`backend/app/modules/setting/service.py` khai hai bảng dữ liệu:

```python
FIELDS = [
    {"key": "email_enabled", "group": "email", "label": "Bật gửi email", "type": "bool"},
    {"key": "smtp_port",     "group": "email", "label": "SMTP Port",     "type": "int"},
    ...
]
SECRET_FIELDS = [
    {"key": "smtp_password", "group": "email", "label": "SMTP App Password"},
    ...
]
```

`GET /api/settings` trả về **nguyên hai bảng này kèm giá trị hiện tại**. Nghĩa là giao diện không
cần biết trước có bao nhiêu ô, tên là gì, thuộc nhóm nào — nó chỉ cần **duyệt danh sách và vẽ theo
`type`**:

- `bool` → công tắc · `int` → ô số · `str` → ô chữ
- gom theo `group`, mỗi nhóm một thẻ; nhãn nhóm tra từ một bảng nhỏ ở giao diện, thiếu thì lấy luôn
  `group` làm nhãn (thêm nhóm mới không làm vỡ màn hình)
- `SECRET_FIELDS` vẽ khác hẳn: xem mục dưới

**Kết quả: thêm một cấu hình = thêm một dòng vào `FIELDS`, không đụng `frontend-v2`.** Chỉ khi cần
một kiểu ô mới (ví dụ `select` có danh sách chọn, hay `json`) mới phải sửa giao diện — và lúc đó
cũng chỉ thêm một nhánh vào `setting-field.tsx`. Đó là chỗ duy nhất được phép biết đến `type`.

**Luật cứng với khóa bí mật.** Backend **không bao giờ trả về giá trị** của `SECRET_FIELDS`, chỉ
trả `configured: true/false`. Giao diện phải giữ đúng như vậy:

- hiện *"Đã cấu hình"* hoặc *"Chưa cấu hình"*, **không** hiện giá trị, **không** hiện dạng chấm tròn
  gợi ý độ dài, **không** có nút *hiện mật khẩu*;
- ô nhập để trống nghĩa là **giữ nguyên**, chỉ gửi lên khi người dùng thực sự gõ cái mới;
- không ghi giá trị vào nhật ký, không đưa vào thông báo lỗi.

Đây là chỗ chứa mật khẩu SMTP và khóa lưu trữ đám mây — làm hụt một trong ba gạch đầu dòng trên là
lộ khóa cho bất kỳ ai mở được màn cấu hình.

**Còn hai màn nữa vào chung phân hệ Quản trị** (MC-5, MC-6). Dự tính ban đầu là khai luôn menu trái
ba mục cho xong một lần — **khi làm thì bỏ**, vì mục menu trỏ vào màn chưa tồn tại thì bấm ra 404.
Menu hiện có hai mục (*Tổng quan*, *Cấu hình hệ thống*); MC-5 và MC-6 mỗi màn thêm một dòng vào
`nav` của `modules/system/routes.tsx`.

**Đã làm ở MC-4 (CR-094):** luật khóa bí mật nằm ở `modules/system/utils/build-setting-values.ts`
và có tệp test riêng cạnh nó. Có thêm một điều kiện mà mục này chưa nói tới: **ô bí mật chỉ có
khoảng trắng cũng tính là để trống**, không gửi lên — lỡ chạm phím cách trong ô mật khẩu không được
biến thành một lần đổi khóa. Ngược lại, giá trị người dùng thật sự gõ thì gửi **nguyên vẹn**, không
cắt khoảng trắng: mật khẩu ứng dụng của Google có dạng bốn cụm cách nhau.

---

## 6. Kiểm trước khi báo xong

Áp cho **mọi** hạng mục MC, không có ngoại lệ:

- `docker compose exec erp npm run check` xanh cả ba cổng — typecheck **0 lỗi**, lint **0 lỗi**
  (cảnh báo giữ nguyên **6**, đừng thêm), test xanh hết.
- Mỗi hạng mục có **ít nhất một tệp test đặt cạnh tệp nó kiểm**, tên `it(...)` bằng tiếng Việt, mô
  tả hành vi. Ưu tiên phần dễ sai âm thầm: kiểm tra dữ liệu nhập, dịch bộ lọc, và **luật che khóa
  bí mật** ở MC-4.
- Màn nào có phân quyền thì phải có bài kiểm **thiếu quyền không thấy mục menu** — ẩn nút ở giao
  diện chỉ là cho gọn mắt, chặn thật vẫn nằm ở backend.
- Không chạy `npm run format` trên cả cây trong lúc còn người đang sửa dở.

---

## 7. Không nằm trong kế hoạch này

- **Yêu cầu thanh toán, bộ danh mục, chi tiết Nhà cung cấp** — đã có lịch ở `12` (P3, P4).
- **Màn "Chứng từ"** (`pages/Documents.tsx`) — **chờ quyết port hay bỏ**. Ở v2 tệp đính kèm đã hiện
  ngay trong từng chứng từ, nên khả năng cao là bỏ; nhưng bản cũ gom tệp theo đơn mua hàng nên ai
  quen dùng sẽ hỏi. Hỏi người dùng trước khi xóa khỏi danh sách.
- **Tắt `frontend/`** — chỉ bàn khi bảy hạng mục này cộng P3 và P4 xong hết.
- **Đổi `FRONTEND_URL`** ở prod và dev — việc lúc deploy, không phải việc lúc viết mã (xem MC-1).

---

## 8. Liên quan

- [`12` Kế hoạch chuyển Thu mua sang ERP v2](./12-ke-hoach-erp-v2-da-phap-nhan.md) — mục 2.6 là chỗ
  bảy màn này bị gạt sang một bên, mục 2.7 là hai màn đã quyết bỏ.
- [`11` Đa pháp nhân và chuyển chức năng sang ERP v2](./11-da-phap-nhan-va-erp-v2.md).
- `doc/tai-lieu-chuc-nang/09-thong-bao-va-trang-ca-nhan.md` — mô tả nghiệp vụ của MC-2 và MC-3.
- `doc/tai-lieu-chuc-nang/10-ho-tro-ticket.md` — mô tả nghiệp vụ của MC-7.
- `doc/tai-lieu-ky-thuat/change-log.md` — dòng **CR-093**.
