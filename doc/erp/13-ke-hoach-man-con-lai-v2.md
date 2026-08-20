# 13 — ĐỐI CHIẾU MÀN HÌNH BẢN CŨ ↔ ERP V2 VÀ KẾ HOẠCH DỜI TỪNG ĐỢT

**Bản 2.0 — 19/08/2026.**
*(Bản 1.0 và 1.1 cùng ngày chỉ nói về bảy màn MC-1…MC-7. Bản này mở rộng thành **bảng đối chiếu
toàn bộ màn hình** của bản cũ, và chia phần còn lại thành **15 đợt nhỏ nghiệm thu riêng được**.)*

> **Vì sao viết lại.** Bản 1.1 chỉ đếm bảy màn nên không trả lời được câu "còn bao nhiêu nữa thì tắt
> được bản cũ". Bản này đếm **hết**, kể cả những màn *đã port nhưng còn khuyết một phần* — loại này
> bản 1.1 tính là xong, và đó là chỗ dễ vỡ kế hoạch nhất.

---

## 0. Bốn con số đọc trước

1. **Bản cũ có 48 màn.** Đếm ngày 19/08/2026: **26 xong** · **3 có nhưng khuyết** · **16 chưa có** ·
   **2 đã quyết bỏ** · **1 chờ quyết**. Trong 16 màn chưa có thì **5 màn thuộc ba thứ khách cho
   hoãn** *(Sao lưu CSDL, Quản lý Import, Phiếu hỗ trợ)*, còn lại **11 màn là việc trước mắt**.
2. **Không phải viết backend dòng nào** cho 16 màn còn thiếu. Toàn bộ endpoint đã chạy thật ở bản
   cũ — đây thuần là dựng lại giao diện. (Việc backend của ERP v2 nằm ở `12`, giai đoạn P1/P2/P5…,
   không dính tới tệp này.)
3. **22 – 32 ngày công** cho cả 15 đợt: mười đợt đầu **12,5 – 19**, ba đợt hoãn **7,5 – 10**, hai
   đợt còn lại **2 – 3**.
4. **Ba màn khách hoãn vẫn chặn việc tắt bản cũ** — chúng không có chỗ nào khác để chạy. Hoãn là
   quyền của khách, nhưng hoãn thì `frontend/` phải sống tiếp, đừng hứa ngày tắt.

---

## 1. Đối chiếu toàn bộ màn hình — đo ngày 19/08/2026

Nguồn đo: menu bản cũ (`frontend/src/layouts/AppLayout.tsx`), route bản cũ
(`frontend/src/App.tsx`, kể cả màn không có trong menu), khai báo CRUD
(`frontend/src/config/cruds.tsx`) — đối chiếu với `frontend-v2/src/app/router/` và
`modules/*/routes.tsx`.

Cột **Tình trạng**: `Xong` · `Khuyết` (có màn nhưng thiếu phần) · `Thiếu` · `Bỏ` · `Chờ quyết`.

### 1.1 Đăng nhập và tầng chung

| # | Màn bản cũ | Đường dẫn v2 | Tình trạng |
|---|---|---|---|
| 1 | Đăng nhập | `/login` | Xong |
| 2 | Quên mật khẩu | `/forgot-password` | Xong |
| 3 | Đặt lại mật khẩu | `/reset-password` | Xong *(MC-1)* |
| 4 | Trang chủ *(437 dòng)* | `/procurement` + `/` (màn chọn phân hệ) | **Khuyết** — xem §1.8 |
| 5 | Thông báo | `/notifications` | Xong *(MC-2)* |
| 6 | Trang cá nhân | `/me` | Xong *(MC-3)* |
| 7 | Trung tâm HDSD *(app riêng)* | link ra ngoài, `helpCenterModule` | Xong |

### 1.2 Mua hàng

| # | Màn bản cũ | Đường dẫn v2 | Tình trạng |
|---|---|---|---|
| 8 | Yêu cầu báo giá — danh sách | `/procurement/survey-requests` | Xong |
| 9 | Yêu cầu báo giá — chi tiết | `…/survey-requests/:id` | **Khuyết** — thiếu nút *Xử lý khảo sát*, mà màn đó đã quyết bỏ (§1.9) nên coi như xong khi P6 gộp phiếu |
| 10 | Tiến độ báo giá | — | **Bỏ** (`12` §2.7) |
| 11 | Màn xử lý Yêu cầu báo giá *(798 dòng)* | — | **Bỏ** (`12` §2.7) |
| 12 | Yêu cầu mua hàng — danh sách | `/procurement/purchase-requests` | Xong |
| 13 | Yêu cầu mua hàng — chi tiết | `…/purchase-requests/:id` | Xong |
| 14 | Đơn mua hàng — danh sách | `/procurement/purchase-orders` | Xong |
| 15 | Đơn mua hàng — chi tiết | `…/purchase-orders/:id` | Xong |
| 16 | Tiến độ mua hàng | `/procurement/purchase-progress` | Xong |
| 17 | Báo cáo mua hàng *(8 tab)* | `/procurement/purchase-report` | Xong — còn nợ N-008 *(gom theo TÊN phòng ban)* |

### 1.3 Khảo sát

| # | Màn bản cũ | Đường dẫn v2 | Tình trạng |
|---|---|---|---|
| 18 | Phiếu khảo sát — danh sách | `/procurement/surveys` | Xong |
| 19 | Phiếu khảo sát — chi tiết | `…/surveys/:id` | Xong *(CR-091)* |
| 20 | Báo cáo khảo sát | `/procurement/survey-report` | Xong |

*Bản cũ có thêm hai lối vào `surveys-supplier/:id` và `surveys-product/:id` — cùng một trang chi
tiết, chỉ khác nhãn. v2 gộp làm một, không phải màn thiếu.*

### 1.4 Kho và Công nợ

| # | Màn bản cũ | Đường dẫn v2 | Tình trạng |
|---|---|---|---|
| 21 | Tồn kho | `/inventory/stock` | Xong |
| 22 | Công nợ | `/finance/payables` | **Khuyết** — thiếu cột tick chọn khoản nợ và nút lên phiếu thanh toán *(chờ màn 23)* |
| 23 | Yêu cầu thanh toán — danh sách | *(chưa có)* → `/finance/payment-requests` | **Thiếu** |
| 24 | Yêu cầu thanh toán — chi tiết *(464 dòng)* | *(chưa có)* | **Thiếu** |

### 1.5 Danh mục

| # | Màn bản cũ | Đường dẫn v2 | Tình trạng |
|---|---|---|---|
| 25 | Nhà cung cấp — danh sách | `/production/suppliers` | Xong |
| 26 | Nhà cung cấp — **chi tiết** *(309 dòng, 3 tab)* | `appRoutes.production.supplierDetail` **đã khai, chưa route nào dùng** | **Thiếu** |
| 27 | Sản phẩm | `/production/products` *(+ chi tiết)* | Xong *(Đ-03, CR-100)* |
| 28 | Hợp đồng — danh sách | *(chưa có)* → `/production/contracts` | **Thiếu** *(Đ-04)* |
| 29 | Hợp đồng — chi tiết *(128 dòng)* | *(chưa có)* → `/production/contracts/:id` | **Thiếu** *(Đ-04)* |
| 30 | Kho | `/inventory/warehouses` *(+ chi tiết)* | Xong *(Đ-01, CR-098)* |
| 31 | Đơn vị tính | `/production/units` *(+ chi tiết)* | Xong *(Đ-02, CR-099)* |
| 32 | Phân loại | `/production/item-groups` *(+ chi tiết)* | Xong *(Đ-02, CR-099)* |
| 33 | Phòng ban | `/hr/departments` *(+ chi tiết)* | Xong |
| 34 | Phân công phụ trách *(170 + 187 dòng)* | *(chưa có)* | **Thiếu** |

Chỗ dễ đếm nhầm: **chi tiết Nhà cung cấp mới có một nửa**. v2 có danh sách + hộp thoại sửa
(`modules/production/pages/supplier-list-page.tsx`); bản cũ là **trang riêng** có tab *Hợp đồng*,
*Lịch sử mua hàng*, *KPI giao hàng*. Hằng số đường dẫn đã khai sẵn nên nhìn qua tưởng xong.

### 1.6 Hệ thống

| # | Màn bản cũ | Đường dẫn v2 | Tình trạng |
|---|---|---|---|
| 35 | Công ty *(+ chi tiết)* | `/hr/companies` | Xong |
| 36 | Nhân sự *(+ chi tiết)* | `/hr/employees` | Xong |
| 37 | Phân quyền tài khoản | `/hr/permissions` | Xong |
| 38 | Phân quyền một tài khoản | `/hr/permissions/users/:id` | Xong |
| 39 | Cấu hình hệ thống | `/system/settings` | Xong *(MC-4)* |
| 40 | Quản lý Import — danh sách *(415 dòng)* | *(chưa có)* | **Thiếu** *(MC-6)* |
| 41 | Quản lý Import — chi tiết *(141 dòng)* | *(chưa có)* | **Thiếu** *(MC-6)* |
| 42 | Sao lưu CSDL *(167 dòng)* | *(chưa có)* | **Thiếu** *(MC-5)* |
| 43 | Phiếu hỗ trợ — danh sách *(173 dòng)* | *(chưa có)* | **Thiếu** *(MC-7)* |
| 44 | Phiếu hỗ trợ — chi tiết *(387 dòng)* | *(chưa có)* | **Thiếu** *(MC-7)* |

### 1.7 Phiếu in và màn ngoài menu

| # | Màn bản cũ | Đường dẫn v2 | Tình trạng |
|---|---|---|---|
| 45 | In Yêu cầu mua hàng | `/print/purchase-request/:id` | Xong |
| 46 | In Đơn mua hàng — 2 mẫu *(bản cũ 2 route)* | `/print/purchase-order/:id` — **gộp một trang có công tắc mẫu** | Xong |
| 47 | In Yêu cầu thanh toán *(259 dòng)* | *(chưa có)* | **Thiếu** |
| 48 | Chứng từ *(169 dòng, không có trong menu)* | *(chưa có)* | **Chờ quyết** — xem §6 |

### 1.8 Màn đã có nhưng khuyết — đừng tính là xong

| Màn | Còn thiếu gì |
|---|---|
| **Trang chủ / Tổng quan Thu mua** | Bản cũ có 9 khối, v2 có 5. **Thiếu 4 khối**: *Top nhà cung cấp*, *Chi tiêu theo bộ phận*, *Trạng thái đơn hàng*, *Tuổi nợ*. Thẻ KPI *Công nợ quá hạn* bị thay bằng *Giao hàng trễ*. Danh sách *Yêu cầu mua gần đây* ở bản cũ **duyệt / từ chối ngay tại chỗ**, v2 chỉ xem |
| **Tổng quan Tài chính** và **Tổng quan Kho** | Đang là trang rỗng 11 dòng, chỉ có tiêu đề. Hai khối *Tuổi nợ* và *Công nợ quá hạn* của Trang chủ cũ đúng ra thuộc về đây |
| **Công nợ** | Thiếu cột tick chọn + nút lên phiếu thanh toán từ các dòng đã chọn |
| **Chi tiết Yêu cầu báo giá** | Thiếu nút *Xử lý khảo sát* — nhưng màn đó đã quyết bỏ, việc chọn phương án sẽ nằm ngay trong chi tiết phiếu ở P6 |

### 1.9 Hai màn đã quyết bỏ

*Tiến độ báo giá* và *Màn xử lý Yêu cầu báo giá* — lý do đầy đủ ở `12` §2.7. Cộng lại bỏ được
**1134 dòng** khỏi việc phải port.

---

## 2. Quyết định thiết kế

### 2.1 Bốn quyết định chốt ngày 19/08/2026 *(giữ từ bản 1.1)*

| | Quyết định | Vì sao |
|---|---|---|
| **QĐ-1** | **Thông báo và Trang cá nhân đặt ở tầng chung**, ngoài mọi phân hệ: `/notifications` và `/me` | Khách chốt: *"thông báo chung trên tất cả luôn, khỏi chia ra app"*. Thông báo vốn trộn nhiều phân hệ — chia theo phân hệ là bắt người dùng mở ba chỗ để đọc hết một hộp thư |
| **QĐ-2** | **Cấu hình hệ thống nằm trong phân hệ Quản trị**, đường dẫn `/system/settings` | Đúng ý *"để một cục riêng"*. MC-5 và MC-6 đổ vào cùng chỗ |
| **QĐ-3** | **Màn cấu hình dựng động từ dữ liệu backend trả về**, không viết cứng từng ô | Trả lời cho *"có cách nào flex"* — xem §5 |
| **QĐ-4** | **Trang cá nhân v2 bỏ hai tab của bản cũ**: *Việc cần làm* và *Yêu cầu hỗ trợ của tôi* | *Việc cần làm* đã có nguyên một màn ở v2 (`/approval/my-tasks`) — dựng lại là hai chỗ đếm cùng một tập việc. Tab hỗ trợ chờ MC-7 |

### 2.2 Ba quyết định chốt thêm ngày 19/08/2026 *(mới ở bản 2.0)*

| | Quyết định | Vì sao |
|---|---|---|
| **QĐ-5** | **Yêu cầu thanh toán đặt trong phân hệ Tài chính**: `/finance/payment-requests` *(+ `…/new`, `…/:id`, `/print/payment-request/:id`)* | Khách chốt. Nằm ngay cạnh Công nợ — mà công nợ chính là nơi người dùng bấm để lên phiếu thanh toán, hai màn này dùng chung một mạch việc |
| **QĐ-6** | **Phân công phụ trách port nguyên trạng ngay**, chấp nhận làm lại ở P7 khi nó đổi thành *Định tuyến phân loại về đơn vị xử lý* | Khách chốt. Chờ P7 nghĩa là bản cũ phải sống thêm vài tháng chỉ vì một màn 170 dòng |
| **QĐ-7** | **Làm lớp CRUD khai báo trước, rồi mới đổ danh mục qua nó** *(P4-1 trước P4-2)* | Khách chốt. Viết tay 6 màn danh mục rồi mới dựng lớp nền là làm hai lần. Đầu tư một lần ở đợt 1, năm đợt sau chỉ còn khai báo |

### 2.3 QĐ-8 — danh mục nằm ở phân hệ đúng chức năng, nơi khác cần thì thêm đường dẫn tắt

*(Chỗ này ở bản 2.0 còn để ngỏ; khách chốt ngày 20/08/2026, nay không còn câu hỏi nào treo.)*

| | Quyết định | Vì sao |
|---|---|---|
| **QĐ-8** | **Mỗi danh mục ở đúng phân hệ theo chức năng của nó** — KHÔNG gom cả sáu vào một nhóm *Danh mục* trong Quản trị. Phân hệ nào cần dùng danh mục của phân hệ khác thì **thêm một đường dẫn tắt trong menu phân hệ đó**, trỏ về đúng màn gốc | Khách chốt: *"cứ để đúng chức năng đúng cục đi, nữa ở phần nào cần có đường dẫn thì mình để thêm vào, họ sử dụng trên đúng cục của họ luôn, ví dụ như trong thu mua để thêm đường dẫn sản phẩm nữa"*. Gom hết vào Quản trị thì người mua hàng phải vào phân hệ quản trị mới sửa được sản phẩm — mà quyền quản trị lại không nên phát cho họ. Đường dẫn tắt rẻ hơn nhân bản màn: một dòng `nav`, vẫn một màn duy nhất, một chỗ sửa |

Vị trí chốt của sáu danh mục *(đúng như kế hoạch đang chạy, không phải đổi gì)*:

| Danh mục | Phân hệ gốc | Đường dẫn | Đường dẫn tắt cần thêm |
|---|---|---|---|
| Sản phẩm | Sản xuất | `/production/products` | **Thu mua** *(người lập YCMH/ĐMH tra mã hàng suốt ngày)* |
| Hợp đồng | Sản xuất *(cạnh nhà cung cấp)* | `/production/contracts` | **Thu mua** |
| Đơn vị tính | Sản xuất | `/production/units` | — |
| Phân loại | Sản xuất | `/production/item-groups` | — |
| Kho | Kho | `/inventory/warehouses` | — |
| Nhà cung cấp *(chi tiết)* | Sản xuất | `/production/suppliers/:id` | **Thu mua** |

**Cách làm đường dẫn tắt:** thêm mục vào `nav` của phân hệ cần dùng trong `modules/<phân hệ>/routes.tsx`,
trỏ thẳng vào đường dẫn gốc — **không** đăng ký route thứ hai cho cùng một màn. Hai đường dẫn cùng
mở một màn nghĩa là hai chỗ phải sửa mỗi lần đổi, và người dùng bookmark nhầm cái sắp bị bỏ.
Quyền vẫn tính theo entity gốc *(`product`, `contract`, `supplier`)*, nên ai không có quyền thì
không thấy mục tắt — giống hệt mục gốc.

---

## 3. Mười lăm đợt — chia nhỏ để nghiệm thu từng phần

Nguyên tắc chia: **mỗi đợt là một thứ bấm được và nghiệm thu được riêng**, không đợt nào quá 4 ngày
công, và đợt sau không chặn việc dùng thử đợt trước. Ai làm một mình thì chạy từ trên xuống.

| Đợt | Việc | Ngày công | Chặn tắt bản cũ? | Tình trạng |
|---|---|---|---|---|
| **Đ-01** | Lớp CRUD khai báo + danh mục **Kho** làm màn chứng minh | 2 – 3 | Có | **Xong** |
| **Đ-02** | **Đơn vị tính** + **Phân loại** *(chỉ khai báo, không viết trang)* | 0,5 – 1 | Có | **Xong** |
| **Đ-03** | **Sản phẩm** — danh sách + chi tiết *(có tab Lịch sử mua hàng)* | 2 – 3 | Có | **Xong** |
| **Đ-04** | **Hợp đồng** — danh sách + chi tiết + tệp đính kèm | 1,5 – 2 | Có | Chưa làm |
| **Đ-05** | **Chi tiết Nhà cung cấp** — 3 tab | 1,5 – 2 | Có | Chưa làm |
| **Đ-06** | **Yêu cầu thanh toán — danh sách** ở `/finance/payment-requests` | 1 – 1,5 | Có | Chưa làm |
| **Đ-07** | **Yêu cầu thanh toán — chi tiết** *(gồm cả màn tạo mới từ công nợ)* | 2 – 3 | Có | Chưa làm |
| **Đ-08** | **Phiếu in Yêu cầu thanh toán** | 0,5 – 1 | Có | Chưa làm |
| **Đ-09** | Trả lại **cột tick chọn + nút lên phiếu** ở màn Công nợ | 0,5 – 1 | Có | Chưa làm |
| **Đ-10** | **Phân công phụ trách** — port nguyên trạng *(QĐ-6)* | 1 – 1,5 | Có | Chưa làm |
| **Đ-11** | Vá **4 khối thiếu** ở Trang chủ + dựng Tổng quan Tài chính / Kho | 1,5 – 2 | Không* | Chưa làm |
| **Đ-12** | **Sao lưu CSDL** *(MC-5)* | 1,5 – 2 | Có | **Hoãn** |
| **Đ-13** | **Quản lý Import** *(MC-6)* | 3 – 4 | Có | **Hoãn** |
| **Đ-14** | **Phiếu hỗ trợ** *(MC-7)* | 3 – 4 | Có | **Hoãn** |
| **Đ-15** | Đổi `FRONTEND_URL`, chuyển hướng bản cũ, tắt `frontend/` | 0,5 – 1 | — | Chưa làm |
| | **Cộng** | **22 – 32** | | |

Tách theo nhóm cho dễ hẹn: **Đ-01…Đ-05 danh mục 7,5–11** · **Đ-06…Đ-09 thanh toán 4–6,5** ·
**Đ-10…Đ-11 phần lẻ 2,5–3,5** · **Đ-12…Đ-14 ba màn hoãn 7,5–10** · **Đ-15 tắt bản cũ 0,5–1**.

*\* Đ-11 không chặn về mặt chức năng — người dùng vẫn làm được việc — nhưng đây là màn đầu tiên họ
nhìn thấy mỗi sáng, nên đừng để nó nghèo hơn bản cũ vào đúng ngày chuyển sang v2.*

**Đã xong trước bản này:** MC-1 … MC-4 *(CR-094)* — Đặt lại mật khẩu · Thông báo · Trang cá nhân ·
Cấu hình hệ thống; **Đ-01** *(CR-098)* Kho · **Đ-02** *(CR-099)* ĐVT & Phân loại · **Đ-03** *(CR-100)* Sản phẩm & tab Lịch sử mua hàng · **CR-101** Hợp nhất bảng dòng hàng (YCMH, YCBG, ĐMH).

### Đ-01 — Lớp CRUD khai báo + danh mục Kho · 2–3 ngày

**Đây là đợt duy nhất có phần hạ tầng. Năm đợt sau ăn theo nó.**

**Làm gì.** Dựng `src/shared/crud/`: một kiểu `CrudConfig` khai *entity · đường dẫn API · cột ·
trường của form · bộ lọc · quyền*, cộng ba thứ sinh ra từ nó — tầng gọi API, bộ hook TanStack Query,
và trang danh sách dựng trên `DataTable`. Rồi dùng nó cho **Kho** để chứng minh lớp nền chạy được.

**Vì sao Kho đi đầu.** Ít trường nhất, không có quan hệ với bảng khác, không có tab phụ — nếu lớp
nền sai thì sai lộ ra ngay chứ không lẫn vào độ phức tạp của màn.

**Bám theo cái đã có.** Bản cũ khai **10 danh mục trong 772 dòng** `config/cruds.tsx` — đọc để lấy
danh sách cột và trường, đừng đọc để chép kiến trúc (bản cũ dựng trên `<table>` tự ghép). Khuôn
trang của v2 là `modules/hr/pages/company-list-page.tsx`; luật bảng ở `frontend-v2/docs/ui/table.md`
là **bắt buộc**, không phải gợi ý.

**Điều kiện đủ.** Mở `/inventory/warehouses` thấy danh sách có phân trang, tìm kiếm, bộ lọc phụ ·
thêm / sửa / xóa chạy thật · tài khoản thiếu `warehouse.write` không thấy nút thêm và không thấy
nút sửa · đổi bộ lọc thì trang nhảy về 1 · **khai một danh mục thứ hai chỉ tốn một khối khai báo,
không tạo tệp trang mới** — chứng minh bằng chính Đ-02.

### Đ-02 — Đơn vị tính + Phân loại · 0,5–1 ngày

**Làm gì.** Hai khối khai báo, không viết trang. Đây là **bài kiểm cho Đ-01**: nếu đợt này còn phải
mở tệp trang ra sửa thì lớp nền chưa đạt, quay lại Đ-01 chứ đừng vá tạm.

**Bẫy.** Cả hai là **danh mục dùng chung toàn tập đoàn** (Q3 ở `12`) — **không** gắn đơn vị sở hữu,
sau này chỉ ẩn/hiện theo đơn vị. Đừng thêm ô "thuộc công ty nào" vào form cho giống mấy màn kia.

**Điều kiện đủ.** Hai màn chạy đầy đủ như Kho · số dòng viết thêm ngoài khai báo bằng **không**.

### Đ-03 — Sản phẩm · 2–3 ngày

**Làm gì.** Danh sách khai bằng lớp CRUD, cộng **trang chi tiết** có tab *Thông tin* và tab ***Lịch
sử mua hàng*** (bản cũ dùng `components/PurchaseHistoryTable.tsx`, 124 dòng).

**Bẫy — đọc trước khi gõ dòng nào.** `tab_product` **là bảng biến thể (SKU)**, không phải sản phẩm
cha, và bảy bảng khác nối vào nó **bằng chuỗi `product_code`** chứ không bằng khóa ngoại. Cấm đổi
hoặc dùng lại `product_code`, cấm đặt cột giá lên sản phẩm. Đầy đủ ở
`doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md` và D-025 trong change-log.

**Điều kiện đủ.** Danh sách lọc được theo phân loại và trạng thái · chi tiết mở tab lịch sử ra đúng
các lần mua của đúng mã hàng đó · đối chiếu một mã bất kỳ với bản cũ ra cùng số dòng và cùng đơn giá.

### Đ-04 — Hợp đồng · 1,5–2 ngày

**Làm gì.** Danh sách khai bằng lớp CRUD + trang chi tiết *(bản cũ 128 dòng)* có khối tệp đính kèm.

**Bẫy.** Entity `contract` **hiện không có trong `SCOPE_FIELDS`** — nghĩa là ai có quyền đọc là đọc
hợp đồng của **mọi** công ty. Đây là việc P4-3 ở `12`, không sửa trong đợt này, nhưng **phải ghi vào
biên bản nghiệm thu** để khỏi tưởng màn mới làm lộ dữ liệu.

**Điều kiện đủ.** Tải lên và tải về tệp đính kèm chạy · hạn hợp đồng sắp hết hiện cảnh báo như bản
cũ · lọc theo nhà cung cấp ra đúng.

### Đ-05 — Chi tiết Nhà cung cấp · 1,5–2 ngày

**Làm gì.** Trang `/production/suppliers/:id` với ba tab: *Hợp đồng*, *Lịch sử mua hàng*, *KPI giao
hàng* — đúng ba tab bản cũ *(309 dòng)*. Nối `appRoutes.production.supplierDetail` **đã khai sẵn
nhưng chưa route nào dùng** vào router, và cho dòng trong danh sách bấm được sang đây.

**Điều kiện đủ.** Ba tab ra số khớp bản cũ trên cùng nhà cung cấp · từ tab hợp đồng bấm sang chi
tiết hợp đồng của Đ-04 · hộp thoại sửa nhanh ở danh sách vẫn chạy, không bị trang mới nuốt mất.

### Đ-06 — Yêu cầu thanh toán, danh sách · 1–1,5 ngày

**Làm gì.** `/finance/payment-requests` theo QĐ-5: danh sách phân trang, lọc theo trạng thái / nhà
cung cấp / khoảng ngày, thêm `finance.paymentRequests*` vào `app-routes.ts`, thêm một dòng `nav`
vào `modules/finance/routes.tsx`.

**Điều kiện đủ.** Số phiếu và tổng tiền khớp bản cũ trên cùng bộ dữ liệu dev · người không có
`payment_request.read` không thấy mục menu.

### Đ-07 — Yêu cầu thanh toán, chi tiết · 2–3 ngày

**Làm gì.** Trang chi tiết *(bản cũ 464 dòng)*: khối thông tin phiếu, bảng dòng công nợ được gom
vào phiếu, luồng gửi duyệt / duyệt / từ chối, và **màn tạo mới nhận danh sách khoản nợ từ màn Công
nợ đẩy sang**.

**Bẫy.** Chuyện phân bổ tiền của phiếu thanh toán **đã từng dồn tiền vào khoản nợ đã tất toán**, đẻ
ra công nợ âm và dòng đơn mua hàng kẹt không sang được *Hoàn thành* — đã vá ở backend (commit
`82ce6ad`). Màn mới **không được** tự tính lại phân bổ ở giao diện; hiển thị đúng cái backend trả về.

**Điều kiện đủ.** Lên một phiếu từ 3 khoản nợ, duyệt, rồi kiểm công nợ trừ đúng và **không** có số
âm · từ chối phiếu thì các khoản nợ được nhả ra chọn lại được · phiếu có tiền bằng 0 xử lý theo đúng
cách bản cũ đang làm.

### Đ-08 — Phiếu in Yêu cầu thanh toán · 0,5–1 ngày

**Làm gì.** `/print/payment-request/:id` *(bản cũ 259 dòng)*, route đặt **ngoài** `ModuleLayout` để
trang in không mang theo menu — giống hai phiếu in đã có.

**Bẫy.** Phần đọc số tiền thành chữ ở bản cũ là hàm viết tay `docTien`. **Chép nguyên hàm đó sang**,
đừng viết lại: viết lại là đẻ ra hai cách đọc "một trăm lẻ năm nghìn" khác nhau giữa hai phiếu in.

**Điều kiện đủ.** In ra khớp từng dòng với bản cũ trên cùng một phiếu · chữ ký lấy từ Trang cá nhân
hiện đúng · số tiền bằng chữ khớp bản cũ ở các ca lẻ (số tròn nghìn, số có "lẻ", số hàng tỷ).

### Đ-09 — Trả cột chọn ở màn Công nợ · 0,5–1 ngày

**Làm gì.** Thêm lại cột tick *(chỉ bật ở dòng còn nợ)* và nút lên phiếu thanh toán, đẩy các dòng đã
chọn sang màn tạo mới của Đ-07. Bản cũ: `Payables.tsx` dòng 138 và 165.

**Điều kiện đủ.** Chọn nhiều dòng khác nhà cung cấp thì chặn hoặc tách phiếu đúng như bản cũ · dòng
đã tất toán không tick được · gỡ được đoạn ghi chú "chỗ này khuyết chờ màn YCTT" trong
`payable-list-page.tsx` và `finance/routes.tsx`.

### Đ-10 — Phân công phụ trách · 1–1,5 ngày

**Làm gì.** Port **nguyên trạng** theo QĐ-6: màn danh sách *(170 dòng)* + màn thêm mới *(187 dòng)*.
Không thiết kế lại, không đón đầu P7.

**Ghi rõ trong biên bản nghiệm thu:** màn này **sẽ được làm lại** ở P7 thành *Định tuyến phân loại
về đơn vị xử lý*. Port bây giờ là để tắt được bản cũ sớm, không phải vì thiết kế này đúng lâu dài.

**Điều kiện đủ.** Gán và gỡ người phụ trách chạy · phiếu mới sinh ra vẫn về đúng người như bản cũ.

### Đ-11 — Vá Trang chủ và hai trang tổng quan · 1,5–2 ngày

**Làm gì.** Thêm 4 khối còn thiếu vào Tổng quan Thu mua *(Top nhà cung cấp · Chi tiêu theo bộ phận ·
Trạng thái đơn hàng · Tuổi nợ)*, trả lại nút duyệt / từ chối nhanh ở danh sách *Yêu cầu mua gần
đây*, và dựng nội dung cho **Tổng quan Tài chính** và **Tổng quan Kho** *(đang là trang rỗng 11
dòng)*.

**Chỗ cần quyết khi làm.** *Tuổi nợ* và *Công nợ quá hạn* thuộc về Tài chính hơn là Thu mua — đưa
sang Tổng quan Tài chính thì đúng phân hệ, nhưng người mua hàng mất một thứ họ quen nhìn. Đề xuất:
**để ở cả hai**, cùng đọc một endpoint.

**Điều kiện đủ.** Bốn khối ra số khớp bản cũ · duyệt nhanh từ trang chủ chạy và cập nhật ngay số ở
thẻ KPI · hai trang tổng quan còn lại không còn là trang trắng.

### Đ-12 — Sao lưu CSDL *(MC-5)* · 1,5–2 ngày — **khách cho hoãn**

**Làm gì.** `/system/backups`: danh sách bản sao lưu *(thời điểm, dung lượng, ai tạo, trạng thái)*,
nút tạo bản mới, tải về, xóa. Lịch chạy tự động do Celery lo, màn này chỉ xem và bấm tay.

**Bẫy.** Bảng `tab_db_backup` ghi lại cả những bản **đã bị xóa khỏi ổ đĩa** — trạng thái phải hiện
rõ, không thì người dùng bấm tải về một tệp không còn tồn tại. Nút tạo phải chặn bấm hai lần: chạy
song song hai lần kết xuất là chuyện đã gặp ở bản cũ.

**Điều kiện đủ.** Tạo được bản sao lưu và tải về mở ra đúng tệp · thao tác xóa có hỏi lại · người
không có quyền không thấy mục này trên menu.

### Đ-13 — Quản lý Import *(MC-6)* · 3–4 ngày — **khách cho hoãn**

**Làm gì.** `/system/import-batches` + trang chi tiết một đợt nhập: chọn tệp, xem trước, đối chiếu
dòng lỗi, xác nhận nạp, xem lịch sử thay đổi từng dòng.

**Vì sao đắt.** Bản cũ 556 dòng và là màn nhiều bước nhất: tải tệp lên → máy chủ đọc thử → bày bảng
lỗi → người dùng sửa hoặc bỏ dòng → xác nhận. Mỗi bước một trạng thái, và trạng thái đó phải sống
sót qua F5.

**Điều kiện đủ.** Nạp một tệp có dòng lỗi thì lỗi hiện đúng số dòng và đúng lý do · bỏ ngang giữa
chừng không để lại đợt nhập treo · nạp lại đúng tệp đó lần hai không nhân đôi dữ liệu.

### Đ-14 — Phiếu hỗ trợ *(MC-7)* · 3–4 ngày — **khách cho hoãn**

**Làm gì.** Danh sách phiếu + chi tiết có trao đổi qua lại, đổi trạng thái, gán người phụ trách,
đính kèm ảnh. Bản cũ có **cờ tắt/bật** riêng (`config/features.ts`) — v2 dùng cờ `enabled` của phân
hệ cho việc đó, không cần cờ riêng.

**Kèm theo.** Xong thì thêm lại tab *Yêu cầu hỗ trợ của tôi* vào Trang cá nhân (QĐ-4), và **gán vai
trò `support`** cho người phụ trách — việc này đang nợ từ trước, không phải việc mới.

**Điều kiện đủ.** Người gửi chỉ thấy phiếu của mình, người có vai trò `support` thấy tất cả · trả
lời một phiếu thì người kia nhận được thông báo · đổi trạng thái có ghi vào nhật ký thao tác.

### Đ-15 — Tắt bản cũ · 0,5–1 ngày

**Làm gì.** Đổi `FRONTEND_URL` ở `.env` của **cả prod lẫn dev** sang v2 *(nếu không, thư đặt lại mật
khẩu vẫn dẫn về giao diện cũ)*, trỏ tên miền sang v2, để bản cũ chạy thêm một thời gian ở đường dẫn
phụ rồi mới dừng hẳn.

**Điều kiện cần.** Đ-01 … Đ-14 xong hết. Nếu khách vẫn hoãn Đ-12/13/14 thì bản cũ **chưa tắt được** —
ba màn đó không có chỗ nào khác để làm.

---

## 4. Ba chỗ MC-1…MC-4 đã làm khác kế hoạch

Ghi lại để lần rà sau khỏi tưởng là làm hụt:

1. **MC-3 bỏ ô bật thông báo đẩy.** `frontend-v2` chưa có PWA, chưa có service worker, chưa có
   VAPID — cả hạ tầng đẩy chỉ tồn tại ở bản cũ. Dựng một ô bật cho thứ chưa tồn tại là thêm nút bấm
   không làm gì. Khi nào v2 có đẩy thật thì thêm ô đó vào Trang cá nhân.
2. **Menu phân hệ Quản trị khai HAI mục, không phải ba.** Mục menu trỏ vào màn MC-5/MC-6 chưa tồn
   tại thì bấm ra 404 — tệ hơn là không có mục. Làm Đ-12/Đ-13 thì thêm một dòng vào `nav`.
3. **Trang tổng quan Quản trị nói thẳng hai màn đang nợ** để người dùng khỏi lục menu tìm.

---

## 5. Cấu hình hệ thống — viết chỗ nào cho hợp lý *(trả lời QĐ-3)*

Câu hỏi đặt ra là: mai mốt thêm một cấu hình nữa thì phải sửa mấy chỗ?

**Câu trả lời: một chỗ, và nằm ở backend** — `backend/app/modules/setting/service.py` khai hai bảng
dữ liệu:

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

`GET /api/settings` trả về **nguyên hai bảng này kèm giá trị hiện tại**. Giao diện không cần biết
trước có bao nhiêu ô — nó **duyệt danh sách và vẽ theo `type`**: `bool` → công tắc · `int` → ô số ·
`str` → ô chữ; gom theo `group`, nhãn nhóm tra từ một bảng nhỏ ở giao diện, thiếu thì lấy luôn
`group` làm nhãn.

**Thêm một cấu hình = thêm một dòng vào `FIELDS`, không đụng `frontend-v2`.** Chỉ khi cần kiểu ô mới
mới phải thêm một nhánh vào `setting-field.tsx` — chỗ duy nhất được phép biết đến `type`.

**Luật cứng với khóa bí mật.** Backend **không bao giờ trả về giá trị** của `SECRET_FIELDS`, chỉ trả
`configured: true/false`. Giao diện phải giữ đúng vậy:

- hiện *"Đã cấu hình"* / *"Chưa cấu hình"*, **không** hiện giá trị, **không** hiện dạng chấm tròn
  gợi ý độ dài, **không** có nút *hiện mật khẩu*;
- ô nhập để trống nghĩa là **giữ nguyên**, chỉ gửi lên khi người dùng thực sự gõ cái mới;
- không ghi giá trị vào nhật ký, không đưa vào thông báo lỗi.

Đây là chỗ chứa mật khẩu SMTP và khóa lưu trữ đám mây — làm hụt một gạch đầu dòng là lộ khóa cho bất
kỳ ai mở được màn cấu hình.

**Đã làm ở MC-4 (CR-094):** luật khóa bí mật nằm ở `modules/system/utils/build-setting-values.ts`,
có tệp test riêng cạnh nó, và có thêm một điều kiện mục này chưa nói tới: **ô bí mật chỉ có khoảng
trắng cũng tính là để trống** — lỡ chạm phím cách không được biến thành một lần đổi khóa. Ngược lại,
giá trị người dùng thật sự gõ thì gửi **nguyên vẹn**, không cắt khoảng trắng: mật khẩu ứng dụng của
Google có dạng bốn cụm cách nhau.

---

## 6. Hợp nhất Logic Bảng dòng hàng & Quy chuẩn UX chung *(CR-101, CR-102)*

Khách yêu cầu: *"trên yêu cầu mua hàng, yêu cầu báo giá, đơn mua hàng thì cái bảng cũng có dạng cột cố định, đổi vị trí, rút gọn/đầy đủ như phần sản phẩm... gom chung 1 logic hết"*. 

**CR-101** kết nối bộ đồ nghề của `DataTable` vào ba bảng dòng hàng; **CR-102** rút phần lặp lại ra
thành **một component dùng chung `LinesTable`** (`src/shared/data-table/lines-table.tsx`) và phủ nốt
bảng thứ tư.

### 6.1 Bốn bảng dòng hàng áp dụng
1. **Yêu cầu mua hàng (PYC)** — `purchase-request-items-table.tsx` *(`erp.table.purchase-request-items`)*
2. **Yêu cầu báo giá (SR)** — `survey-request-lines-table.tsx` *(`erp.table.survey-request-lines`)*
3. **Đơn mua hàng (PO)** — `purchase-order-items-table.tsx` *(`erp.table.purchase-order-items`)*
4. **Giao hàng nhiều lần** trong popup Chi tiết dòng của ĐMH — `purchase-order-deliveries-table.tsx`
   *(`erp.table.purchase-order-deliveries`, thêm ở CR-102)*

**`LinesTable` là bảng SỬA ĐƯỢC**, khác `DataTable` ở chỗ ô chứa input/select và nội dung vẽ theo chỉ
số dòng: bảng khai `columns: LinesTableColumn[]` *(chỉ mô tả cột, không kèm `cell`)* rồi vẽ ô bằng
một hàm `renderCell(columnKey, row, index)`. Bảng dòng hàng **mới phải dùng `LinesTable`**, đừng chép
lại phần khung — chép là mỗi bảng lại lệch một kiểu như trước CR-102.

### 6.2 Bộ tính năng bảng thống nhất
* **Ghim cột (Sticky Pin):** Mặc định ghim 3 cột đầu (`No`, `Mã hàng`, `Tên hàng/thông số`) và cột `Thao tác` bên phải. Tự động tính `pinnedOffsets` qua DOM offset thực tế (`usePinnedOffsets`), không bị lệch khi co giãn cột.
* **Kéo thả đổi vị trí cột trực tiếp (Direct Header Drag & Drop):** Người dùng có thể nhấn giữ chuột trái trên bất kỳ tiêu đề cột nào trên bảng để kéo sang trái/phải (`useColumnDrag` + `ColumnHeaderCell`), có vạch xanh chỉ vị trí chèn và thẻ tên cột nổi bay theo con trỏ chuột; hoặc sắp xếp trong Menu *Cột*.
* **Co giãn độ rộng cột (Column Resizing):** Kéo mép phải cột để co nhỏ hoặc nới rộng tùy ý (minWidth hạ về 40–60px), nháy đúp để tự vừa nội dung (Auto-fit).
  ⚠️ **KHÔNG đặt bề rộng cứng cho thẻ `<table>`.** Bản CR-101 gắn `style={{ width: totalWidth }}`;
  ẩn bớt cột là tổng bề rộng tụt xuống dưới bề ngang khung, để lại **một khoảng trắng bên phải trong
  khung viền** — đúng lỗi khách báo *"nó lủng 1 lỗ ở bảng luôn rồi nè"*. CR-102 bỏ hẳn dòng đó:
  `table-fixed` + `w-full` cho bề rộng bằng `max(khung chứa, tổng cột)`, ẩn cột thì bảng vẫn phủ kín,
  mở nhiều cột thì tự cuộn ngang — giống hệt màn *Sản phẩm & Vật tư*.
* **Chuyển đổi Bảng rút gọn / Bảng đầy đủ:**
  - Cột nào thuộc nhóm phụ thì khai `compactHidden: true` ngay trong định nghĩa cột; nút *Bảng rút gọn / Bảng đầy đủ* ẩn/hiện cả nhóm.
  - *Bảng rút gọn:* Chỉ giữ các cột nghiệp vụ cốt lõi (No, Mã, Tên hàng, ĐVT, SL, Đơn giá, Thành tiền, Thao tác), ẩn toàn bộ các cột phụ.
  - *Bảng đầy đủ:* Mở rộng xem toàn bộ cột (Kho nhận, Phân loại, VAT%, Tiến độ, TG dự kiến, NSTM phụ trách).
  - Dùng hàm `setHiddenColumns` để ẩn/hiện hàng loạt an toàn, không bị lỗi stale closure state.
  - Cờ **`defaultCompact`** cho bảng quá nhiều cột *(bảng giao hàng có 22 cột)* mở lần đầu ở dạng rút gọn — chỉ là **mặc định**, bố cục người dùng đã chỉnh vẫn được nhớ như thường.
* **Tự động lưu cấu hình:** Mọi tùy biến (thứ tự, ghim, ẩn/hiện, độ rộng, màu sắc) tự động lưu vào `localStorage` độc lập cho từng bảng theo `storageKey` *(xem §6.1)*.

### 6.3 Quy chuẩn UX dùng chung bổ sung
* **Tự động xuống dòng (No Truncate):** Các cột chữ dài (Tên sản phẩm, Nhà cung cấp, Công ty, Kho nhận, Phân loại, Chi tiết thông số, Ghi chú) và thẻ Huy hiệu Trạng thái (`ProgressStatusBadge`) bật `wrap: true` (`break-words whitespace-normal leading-snug`), chiều cao hàng tự co giãn `min-h-10 py-1.5`, cấm dùng `truncate` làm mất thông tin người dùng.
* **Chặn Enter tự submit Form:** Mọi form chi tiết và popup (`CrudDetailPage`, `CrudFormDialog`, `PurchaseHistoryTable`) đều chặn sự kiện phím `Enter` kích hoạt submit tự động khi đang gõ text/number/date, bắt buộc người dùng bấm nút "Lưu" hoặc "Tạo mới" thủ công (riêng `textarea` vẫn cho Enter xuống dòng).
* **Đồng bộ HTTP Method:** Cập nhật `useCrudSave` dùng `apiPatch` thay vì `apiPut` để khớp 100% với endpoint chuẩn FastAPI backend (`PATCH /{id}`).

### 6.4 Đính kèm được ngay trên dòng chưa lưu *(CR-102)*

Bảng giao hàng trước đây hiện chữ **"Lưu đơn để đính kèm"** ở lần giao vừa thêm, vì tệp phải gắn vào
một `delivery_id` mà dòng chưa lưu thì chưa có id. Khách bác: *"sao có dụ lưu đơn để đính kèm nữa nè,
cho đính kèm luôn chứ bạn"*.

Cách làm — **giữ tạm rồi đẩy sau khi lưu**, đúng lối đã dùng cho dòng phiếu khảo sát
(`helpers/pending-line-files.ts`):

1. Chọn tệp trên dòng chưa lưu thì tệp nằm trong bộ nhớ trang, khóa theo `"<chỉ số dòng>:<chỉ số lần giao>"` (`helpers/pending-delivery-files.ts`), có xem trước tên tệp và bỏ được từng tệp.
2. Bấm **Lưu đơn** → `savePurchaseOrder` trả về đơn đầy đủ kèm `id` của mọi lần giao → `flushPendingDeliveryFiles` dò ra id thật rồi tải tệp lên qua `useUploadDeliveryFiles`.
3. **Dò id theo danh tính nghiệp vụ, không theo vị trí mảng**: khớp dòng theo `id` → `product_code` → chỉ số, rồi trong các lần giao *chưa từng có id* thì khớp theo `delivery_no`. Backend sắp lần giao theo `id.asc()` nên dòng mới thêm không chắc nằm đúng chỗ cũ — lấy theo chỉ số là gắn tệp nhầm lần giao.
4. Xóa lần giao / xóa dòng / nhân bản dòng đều làm lệch chỉ số, nên ba thao tác đó báo ngược lên trang để dời giỏ tệp theo (`shiftPendingAfter*`).

Giỏ tệp được **dọn trước** khi gọi tải lên: lỡ có lần giao nào không dò ra id thì cũng đừng để tệp cũ
treo lại rồi tải nhầm sang lượt lưu sau.

### 6.5 Nợ kỹ thuật của lớp CRUD — trả trước khi mở rộng thêm

Rà lại `shared/crud/` (dựng ở CR-098) thấy các chỗ sau; chưa cái nào chặn chạy, nhưng **đợt Đ-04 và
Đ-05 sẽ nhân bản chúng lên gấp đôi** nên trả sớm rẻ hơn:

| Chỗ | Vấn đề | Vì sao phải sửa |
|---|---|---|
| `crud-detail-page.tsx`, `crud-form-dialog.tsx`, `crud-list-page.tsx`, `use-crud.ts` | **25 cảnh báo `no-explicit-any` mới** *(lint từ 6 lên 31 cảnh báo)*, trong đó `any` lọt vào chữ ký export `CrudListPage<T extends Record<string, any>>` | `typescript.md`: *"Never let `any` leak into a public/exported signature"*. Dùng `unknown` + thu hẹp, hoặc ràng generic vào kiểu bản ghi thật |
| `crud-form-dialog.tsx` | Ghép class bằng **template string** | `styling.md` **CẤM** — bỏ qua `tailwind-merge` nên class đè nhau im lặng. Đổi sang `cn()` |
| `use-crud.ts` | Khóa query viết thẳng tại chỗ `['crud', apiPath, …]` | `naming.md`: khóa phải khai ở `shared/constants/query-keys.ts`, không thì `invalidate` trượt âm thầm |
| `shared/crud/types.ts` | Một câu `import` nằm **giữa tệp** (dòng 40) | Khó thấy phụ thuộc, và là chỗ dễ đẻ vòng lặp import |
| `crud-detail-page.tsx` | Khối form + `renderExtra` + `AuditTimeline` bị **chép nguyên hai lần** cho nhánh có tab và nhánh không tab | Sửa một chỗ quên chỗ kia là hai màn lệch nhau |
| `crud-detail-page.tsx` vs `crud-form-dialog.tsx` | `FormFieldItem`/`SelectField` và `DetailFormFieldItem`/`DetailSelectField` **trùng nhau ~85 dòng** | Cùng một ô nhập mà hai bản, sửa quy tắc hiển thị phải nhớ cả hai |
| `CrudConfig` | `config.exportXlsx` khai ra nhưng **không chỗ nào dùng** | Đọc khai báo tưởng có xuất Excel, thật ra không |
| `crud-detail-page.tsx:83`, `crud-form-dialog.tsx:77` | `useEffect` thiếu phụ thuộc `buildDefaultValues`, `reset` | Mở lại form với bản ghi khác có thể còn giữ giá trị cũ |

---

## 7. Kiểm trước khi báo xong

Áp cho **mọi** đợt, không có ngoại lệ:

- `docker compose exec erp npm run check` xanh cả ba cổng — typecheck **0 lỗi**, lint **0 lỗi**,
  test xanh hết. Cảnh báo lint: mốc cũ là **6**, hiện **31** vì lớp CRUD *(xem §6.5)* — **đừng thêm
  mới**, và trả về 6 khi dọn xong §6.5.
- Mỗi đợt có **ít nhất một tệp test đặt cạnh tệp nó kiểm**, tên `it(...)` bằng tiếng Việt, mô tả
  hành vi. Ưu tiên phần dễ sai âm thầm: kiểm tra dữ liệu nhập, dịch bộ lọc, tính tiền.
- Màn nào có phân quyền thì phải có bài kiểm **thiếu quyền không thấy mục menu** — ẩn nút ở giao
  diện chỉ cho gọn mắt, chặn thật vẫn nằm ở backend.
- Màn nào port từ bản cũ thì nghiệm thu bằng **đối chiếu số liệu trên cùng bộ dữ liệu dev**, không
  nghiệm thu bằng "nhìn thấy giống".
- Không chạy `npm run format` trên cả cây trong lúc còn người đang sửa dở.

---

## 8. Không nằm trong kế hoạch này

- **Màn "Chứng từ"** (`frontend/src/pages/Documents.tsx`, 169 dòng — kho tệp đính kèm gom theo đơn
  mua hàng, không có trong menu). **Chờ quyết port hay bỏ.** Ở v2 tệp đính kèm đã hiện ngay trong
  từng chứng từ nên khả năng cao là bỏ, nhưng bản cũ gom tệp theo đơn nên ai quen dùng sẽ hỏi. Hỏi
  người dùng trước khi xóa khỏi danh sách.
- **Toàn bộ việc backend của ERP v2** — vá lỗ hổng phạm vi (P1), nền đa pháp nhân (P2), danh mục
  theo đơn vị (P5), gộp Yêu cầu báo giá với Yêu cầu mua hàng (P6), định tuyến đơn vị xử lý (P7),
  công nợ theo pháp nhân (P8), báo cáo tổng (P9). Xem `12` §3.
- **Khai phạm vi cho `contract` / nhận hàng / lịch sử mua hàng** (P4-3 ở `12`) — liên quan tới Đ-04
  nhưng là việc backend, không gộp vào đợt.
- **N-008** — báo cáo mua hàng gom theo TÊN phòng ban thay vì ID. Xem change-log.

---

## 9. Liên quan

- [`12` Kế hoạch chuyển Thu mua sang ERP v2](./12-ke-hoach-erp-v2-da-phap-nhan.md) — §2.7 hai màn đã
  quyết bỏ, §3 mười giai đoạn của phần backend.
- [`11` Đa pháp nhân và chuyển chức năng sang ERP v2](./11-da-phap-nhan-va-erp-v2.md).
- `frontend-v2/docs/ui/table.md` — hợp đồng bắt buộc cho mọi màn danh sách, đọc trước Đ-01.
- `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md` — đọc trước Đ-03.
- `doc/tai-lieu-chuc-nang/09-thong-bao-va-trang-ca-nhan.md` · `10-ho-tro-ticket.md`.
- `doc/tai-lieu-ky-thuat/change-log.md` — **CR-093** (kế hoạch bảy màn), **CR-094** (MC-1…MC-4),
  **CR-097** (bản 2.0 này).

*Tên tệp giữ nguyên `13-ke-hoach-man-con-lai-v2.md` dù nội dung đã rộng hơn cái tên — đổi tên là
gãy đường dẫn ở `CLAUDE.md`, `12`, `README.md` và bốn dòng CR.*
