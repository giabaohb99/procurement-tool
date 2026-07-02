# Thiết kế giao diện — Mini Tool Thu Mua (DEGO)

> Tài liệu này mô tả **giao diện nên trông như thế nào**, viết cho người không chuyên FE.
> Đọc theo thứ tự: (0) Tinh thần → (1) Màu → (2) Chữ → (3) Khung màn hình → (4) Khối chuẩn → (5) **Trang chủ** → (6) Các màn khác → (7) Checklist "đẹp".

---

## 0. Tinh thần chung (đọc cái này trước)

Phong cách tham chiếu (Horizon UI) **không phải** là nhiều màu sặc sỡ hay dải gradient lớn. Ngược lại, nó **rất tĩnh và sạch**:

- Nền tổng thể là **xanh-xám rất nhạt**, gần như trắng.
- Nội dung nằm trong các **thẻ trắng bo góc tròn**, cách nhau bằng khoảng trắng rộng, có **bóng đổ mềm** (không viền đậm).
- Chỉ dùng **1 màu nhấn duy nhất** cho nút/biểu đồ/menu đang chọn. Mọi thứ còn lại là trắng – xám – navy.
- Con số quan trọng thì **to và đậm**, nhãn mô tả thì **nhỏ và xám**.

**Lỗi của bản hiện tại (cần sửa):**
1. Dải "Thao tác nhanh" là **gradient tím lớn, chói** → Horizon chỉ dùng gradient cho **1 ô nhỏ**, phần lớn là thẻ trắng. Cần thu nhỏ hoặc bỏ gradient.
2. Màu nhấn đang là **tím**, trong khi **logo DEGO là xanh biển + xanh lá**. Màu nhấn nên theo logo.
3. Trang chủ **còn trống**, hiển thị ít thông tin → cần **dày thêm** bằng các khối báo cáo tóm tắt.

---

## 1. Bảng màu (theo logo DEGO)

Logo DEGO gồm 2 màu: **xanh biển `#00AEEF`** và **xanh lá chanh `#92C83E`**. Đây là gốc thương hiệu, giao diện nên dùng đúng 2 màu này thay vì tím.

| Vai trò | Mã màu | Dùng ở đâu |
|---|---|---|
| **Nhấn chính (Primary)** | `#00AEEF` xanh biển | Nút chính, link, menu đang chọn, đường biểu đồ chính, viền ô đang focus |
| Nhấn chính (đậm hơn) | `#0096CC` | Trạng thái hover của nút chính |
| **Tích cực / thành công** | `#92C83E` xanh lá | Badge "hoàn thành", số liệu tăng trưởng, thanh tiến độ tốt |
| **Chữ tiêu đề (navy)** | `#1B2559` | Tên trang, con số KPI, tiêu đề thẻ |
| **Chữ phụ / nhãn (muted)** | `#A3AED0` | Nhãn nhỏ dưới con số, mô tả, tiêu đề cột |
| **Nền canvas** | `#F4F7FE` | Nền toàn trang (xanh-xám rất nhạt) |
| **Nền thẻ** | `#FFFFFF` | Mọi thẻ nội dung |
| **Viền mảnh** | `#EEF1F8` | Viền thẻ, kẻ dòng bảng |
| Cảnh báo (vàng) | `#D97706` nền `#FFF6E5` | Sắp đến hạn, chờ duyệt |
| Nguy hiểm (đỏ) | `#B91C1C` nền `#FEE2E2` | Quá hạn, hết hạn, giao trễ |

> **Quy tắc 1 màu nhấn:** trên 1 màn hình chỉ nên có **1 nút màu xanh biển đậm** (hành động chính). Các nút khác để trắng viền mảnh. Nhiều nút cùng tô đậm sẽ rối.

---

## 2. Chữ (Typography)

- **Font:** một font sans hiện đại, đều nét. Gợi ý **Inter** (đang dùng, ổn) hoặc **DM Sans** (giống Horizon nhất). Chỉ dùng **1 font** cho cả app.
- **Cỡ chữ chuẩn:**
  - Con số KPI lớn: **26px, đậm**, màu navy.
  - Tên trang / tiêu đề thẻ: **18px, đậm**, navy.
  - Nội dung bảng/form: **14px**.
  - Nhãn nhỏ, mô tả: **12–13px**, màu xám muted.
- **Chỉ 2 độ đậm:** thường (400) và đậm (600–700). Đừng dùng quá nhiều mức.
- Viết **thường** (sentence case), không VIẾT HOA cả cụm, **không icon cảm xúc (emoji)**.

---

## 3. Khung màn hình (Layout)

```
┌───────────┬────────────────────────────────────────────────┐
│           │  Thanh trên: breadcrumb   ·   🔔  ·  Avatar tên  │
│  SIDEBAR  ├────────────────────────────────────────────────┤
│  (menu)   │                                                  │
│  [logo]   │        VÙNG NỘI DUNG (nền #F4F7FE)               │
│  Trang chủ│        gồm các thẻ trắng bo góc                  │
│  Mua hàng │                                                  │
│  Kho...   │                                                  │
│  Danh mục │                                                  │
└───────────┴────────────────────────────────────────────────┘
```

### 3.1 Sidebar (menu trái)
- **Nên đổi sang nền TRẮNG** (Horizon dùng sidebar trắng, nhìn nhẹ hơn nền tối hiện tại). Nếu muốn giữ tối cũng được, nhưng trắng đúng chất Horizon hơn.
- **Trên cùng: logo DEGO** (file `Dego Holding Logo.svg`) — đặt logo thật thay cho icon + chữ "Thu Mua Tool".
- Nhóm menu có tiêu đề nhỏ màu xám (MUA HÀNG, KHO & CÔNG NỢ, DANH MỤC…).
- Mục đang chọn: **chữ + icon màu xanh biển**, nền là **viên bo tròn xanh rất nhạt** (`#E5F7FF`), không cần thanh accent bên trái.

### 3.2 Thanh trên (Topbar)
- Trái: breadcrumb (Mua hàng / Trang chủ).
- Phải: chuông thông báo (có chấm đỏ nếu có cảnh báo) + avatar tròn (chữ cái đầu tên) + tên + nút Đăng xuất.
- Nền trắng, viền dưới mảnh.

---

## 4. Các khối chuẩn (dùng lại khắp nơi)

### 4.1 Thẻ (Card)
- Nền trắng, **bo góc 20px**, **bóng mềm** `0 18px 40px rgba(112,144,176,.12)`, viền mảnh `#EEF1F8`, padding ~20px.

### 4.2 Thẻ KPI (con số tóm tắt)
```
┌──────────────────────────┐
│  (◔ icon tròn màu)  Nhãn nhỏ xám      │
│                      1,250   ← số to, navy │
└──────────────────────────┘
```
- Icon nằm trong **hình tròn nền nhạt** cùng tông màu ý nghĩa.
- Nhãn nhỏ (12–13px, xám) ở trên, **con số to (26px, đậm, navy)** ở dưới.
- Cả thẻ bấm được → nhảy tới màn liên quan; hover nhấc nhẹ lên.

### 4.3 Nhãn trạng thái (Badge)
- Viên bo tròn nhỏ, chữ 12px: xanh lá = tốt/hoàn thành, vàng = chờ/sắp hạn, đỏ = quá hạn/lỗi, xám = nháp.

### 4.4 Bảng
- Tiêu đề cột nền xám rất nhạt, chữ navy.
- Dòng chẵn nền hơi khác để dễ đọc; hover đổi nền nhạt.
- Dòng cảnh báo (vd HĐ sắp hết hạn) **tô cả dòng** vàng/đỏ nhạt.

### 4.5 Nút
- Nút chính: nền xanh biển, chữ trắng, bo 10–12px. **Chỉ 1 nút chính/màn.**
- Nút phụ: nền trắng, viền mảnh, chữ đen.

---

## 5. TRANG CHỦ (Dashboard) — "trung tâm điều hành" (đã triển khai)

Mục tiêu: admin **mở 1 màn là nắm toàn cảnh** — việc cần làm, dòng tiền, mua sắm, kho, cảnh báo. Bí quyết để **dày mà không rối**: gom theo tầng, **các thẻ cùng chiều cao**, xếp lưới **2 cột đều** (biểu đồ chính 1.7:1). Toàn bộ lấy từ 1 endpoint `GET /api/dashboard/overview`.

```
Hàng 1 — Lời chào + "Số liệu năm N" + số cảnh báo
Hàng 2 — 8 THẺ KPI (2 hàng × 4):
   [Đơn chờ duyệt] [PO đang chạy] [Giao trễ] [Khảo sát chờ]
   [Nợ đến hạn 7n] [Nợ quá hạn] [HĐ sắp hết hạn] [Giá trị tồn kho]
Hàng 3 — [ Chi phí mua theo tháng (cột, có nhãn số) ]  [ Cơ cấu phân loại (donut) ]
Hàng 4 — [ Trạng thái đơn hàng (thanh) ]               [ Tuổi nợ còn phải trả (thanh) ]
Hàng 5 — [ Top NCC theo giá trị (thanh) ]              [ Chi tiêu theo bộ phận (thanh) ]
Hàng 6 — [ Cảnh báo cần xử lý (danh sách) ]            [ Tồn kho thấp / sắp hết (bảng) ]
Hàng 7 — [ Đơn hàng gần đây (bảng đầy đủ chiều ngang) ]
```

### Từng khối & nguồn dữ liệu

| Khối | Hiển thị | Nguồn |
|---|---|---|
| KPI Đơn chờ duyệt | PYC `submitted` | PurchaseRequest |
| KPI PO đang chạy | PO approved/partial/received | PurchaseOrder |
| KPI Giao trễ | Lần giao chưa nhận đã quá hạn | PODelivery |
| KPI Khảo sát chờ | Survey `submitted` | Survey |
| KPI Nợ đến hạn (7n) | Tiền phải trả trong 7 ngày | Payable |
| KPI Nợ quá hạn | Tiền đã quá hạn | Payable |
| KPI HĐ sắp hết hạn | Hợp đồng ≤30 ngày | Contract |
| KPI Giá trị tồn kho | Tổng giá trị tồn (BQ gia quyền) | Inventory |
| Chi phí theo tháng | Cột giá trị nhận hàng, **nhãn số trên đầu cột**, hover xem đủ tiền | PODelivery×POItem |
| Cơ cấu phân loại | Donut tỷ trọng chi tiêu theo nhóm | POItem.item_group |
| Trạng thái đơn hàng | Thanh số đơn theo trạng thái | PurchaseOrder |
| Tuổi nợ | Thanh tiền theo Chưa đến hạn / 1–30 / 31–60 / >60 ngày | Payable |
| Top NCC | 5 NCC giá trị cao nhất | POItem×PO |
| Chi tiêu bộ phận | Giá trị mua theo phòng ban | POItem×PO |
| Cảnh báo cần xử lý | Nợ/HĐ/giao trễ — chấm màu + bấm nhảy tới | `/api/alerts` |
| Tồn kho thấp | SP tồn thấp nhất, dòng hết hàng tô đỏ | Inventory |
| Đơn hàng gần đây | 8 đơn mới nhất: mã · NCC · ngày · trạng thái · giá trị | PurchaseOrder×POItem |

> Con số **tô màu theo ý nghĩa**: xanh lá = tốt/đúng hạn, vàng/cam = chờ/sắp, đỏ = quá hạn/thiếu. Thẻ và dòng bảng **bấm được** để đi thẳng tới màn chi tiết.

### Đã bỏ
- **Dải gradient tím lớn** (chói, lệch thương hiệu) — thay bằng nền thẻ trắng thuần.
- Màu nhấn tím → về **xanh biển logo `#00AEEF`**; logo DEGO gắn ở đầu sidebar.

---

## 6. Các màn khác (áp dụng cùng khối chuẩn)

- **Danh sách (NCC, SP, PO…):** thanh lọc gọn trên cùng → bảng nằm trong 1 thẻ trắng bo góc. Nút "Thêm" là nút chính duy nhất.
- **Chi tiết (NCC, PO, HĐ):** chia **tab** (Thông tin / … / Lịch sử) trong các thẻ; lịch sử thao tác để **cuối trang**. Form 2 cột trên máy tính, 1 cột trên điện thoại.
- **Báo cáo:** giữ dạng nhiều tab + biểu đồ có trục, mỗi thẻ 1 báo cáo.

---

## 7. Checklist "đẹp" — Nên / Tránh

**Nên**
- Nền xanh-xám nhạt + thẻ trắng bo góc lớn + bóng mềm.
- Đúng 1 màu nhấn (xanh biển logo), xanh lá cho tích cực.
- Con số to đậm navy, nhãn nhỏ xám. Nhiều khoảng trắng.
- Icon dạng nét mảnh, đặt trong hình tròn nền nhạt.

**Tránh**
- Gradient lớn/chói, nhiều màu sặc sỡ.
- Viền đậm, bo góc vuông cứng.
- Nhồi nhiều nút tô đậm cạnh nhau.
- Chữ đen tuyền trên nền màu (dùng tông đậm cùng màu).
- VIẾT HOA cả cụm, emoji.

---

## 8. Lộ trình áp dụng (đề xuất)

1. **Đổi màu nhấn về xanh biển logo** + gắn **logo DEGO** vào sidebar. *(nhanh)*
2. **Bỏ/thu nhỏ dải gradient**, làm gọn thao tác nhanh. *(nhanh)*
3. **Dày trang chủ**: thêm các khối KPI + biểu đồ 12 tháng + donut + Top NCC + Cảnh báo + Tồn sắp hết. *(chính)*
4. (Tùy chọn) **Sidebar nền trắng** kiểu Horizon.
5. Rà lại các màn để đồng bộ thẻ/khoảng cách.

> Anh chỉ cần duyệt lộ trình này, em sẽ triển khai từng bước và cho xem lại.
