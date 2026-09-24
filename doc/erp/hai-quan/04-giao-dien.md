# PHÂN HỆ TRA CỨU GIÁ HẢI QUAN — GIAO DIỆN

> **Mã tài liệu:** ERP-HQ-04 · **Bản:** 1.2 — 23/09/2026 · **Loại:** THIẾT KẾ + ĐÃ DỰNG (bao-CR-470, local, chưa commit) — chỗ nào bản dựng khác đề xuất thì ghi ở §7
> Màn hình cho **cả bản cũ (`frontend/`, thumua) lẫn bản mới (`frontend-v2/`, erp)** — theo quy trình đại ca chốt 08/09/2026: bản cũ làm và chạy ổn trên prod trước, rồi mới port sang bản mới. Thứ tự làm ở [`03-lo-trinh-phase.md`](./03-lo-trinh-phase.md).

Hai bản dùng **chung một bộ API và chung một bố cục**. Khác nhau chỉ ở cách dựng (§5).

---

## 1. Danh sách màn hình

| Mã | Màn | Đợt | Bản cũ | Bản mới |
|---|---|---|---|---|
| M1 | **Trang tra cứu giá hải quan** — thẻ *Danh sách* + thẻ *Biểu đồ* (biểu đồ chỉ hiện khi đã lọc) | 1 | `/customs-prices` | `/procurement/customs-prices` |
| M2 | Chi tiết một **dòng hàng** — đủ 32 trường | 1 | Hộp thoại | Popup (đổi từ ngăn kéo, 23/09) |
| M3 | Nạp dữ liệu — 3 bước: chọn tệp · xem trước · áp dụng | 1 | Hộp thoại | Hộp thoại |
| M4 | Lịch sử nạp + hoàn tác | 1 | **Hộp thoại mở từ nút trên M1** (bản cũ không có màn Quản lý Import) | **Dùng lại `/system/imports`** sẵn có, lọc theo phân hệ |
| M5 | Thẻ *Nhà nhập khẩu* trong M1 | 2 | Có | Có |
| M6 | Thẻ *So sánh* 2–5 từ khóa trong M1 | 2 | Có | Có |
| M7 | Lọc theo hoạt chất + hàm lượng trong M1 | 2 | Có | Có |
| M8 | Ngưỡng theo nghị định — danh mục khai tay | 3 | Có | Có |
| M9 | Tra cứu nghĩa vụ theo tên / số CAS · Tra biểu thuế | 3 | Có | Có |

**Chỉ một màn chính (M1), phần báo cáo là thẻ Biểu đồ nằm trong đó** — không tách màn báo cáo riêng (đại ca chốt 23/09/2026).

**Vị trí menu:** một mục **"Tra cứu giá hải quan"** trong menu Thu mua, gác bằng khóa `customs_price` — ai không được tick quyền xem thì không thấy mục này. Chỗ đứng cụ thể trong menu đổi được bất cứ lúc nào, không ảnh hưởng gì khác.

---

## 2. M1 — Trang tra cứu giá hải quan

**Bố cục đại ca chốt 23/09/2026:** một màn, **hai thẻ** — *Danh sách* và *Biểu đồ*. Phần báo cáo nằm ngay trong thẻ Biểu đồ, không tách thành màn báo cáo riêng. **Biểu đồ chỉ hiện khi đã có bộ lọc.**

Bản 1.0 của tài liệu này có một trang tổng quan hiện lúc chưa tìm (top mã HS, top doanh nghiệp…). **Bỏ** — không ai cần nó để trả lời câu hỏi "mua lúc nào", và bỏ nó thì **không còn gì phải tính sẵn** (xem §2.3).

```
┌ Tra cứu giá hải quan ──────────────────────────── [ Lịch sử nạp ] [ Nạp dữ liệu ] ┐
│ Dữ liệu: 02/01/2026 → 17/09/2026 · 18.243 dòng hàng · lần nạp gần nhất 18/09/2026   │
│ Tháng đã phủ:  01 02 03 04 05 06 07 08 09 │ 10 11 12                                 │
│                ██ ██ ██ ██ ██ ██ ██ ██ ██ │ ░░ ░░ ░░   ← tháng trống hiện rõ         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ [ Tìm tên hàng hoặc hoạt chất ........................................ ] [ Tìm ]   │
│ Mã HS [Tất cả ▾]  Xuất xứ [Tất cả ▾]  Doanh nghiệp [Tất cả ▾]  Từ [01/2026] Đến [09/2026] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ [ Danh sách ]  [ Biểu đồ ]                                                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

- **Thanh lọc dùng chung cho cả hai thẻ.** Lọc xong bấm qua lại giữa hai thẻ không mất bộ lọc.
- **Dải tháng đã phủ** giữ lại ở đầu trang — nó chặn lỗi "quên nạp một tệp": mỗi lần kết xuất GTT02 bị cắt thành nhiều tệp hai tháng, sót một tệp là thấy ngay hai ô trống giữa dải. Số này tính thẳng lúc mở trang (đếm dòng theo tháng trên ~26.000 dòng/năm), không cần lưu sẵn.
- Nút **Nạp dữ liệu** và **Lịch sử nạp** chỉ hiện với người có `customs_price.write`.

### 2.1 Thẻ *Danh sách* — mặc định

Bảng dòng hàng, **hiện ngay cả khi chưa lọc** (phân trang, mới nhất lên đầu). Đủ 32 cột theo đúng thứ tự và tiêu đề Excel; mặc định bật 10 cột — *ngày đăng ký · tên hàng · mã HS · doanh nghiệp nhập · đối tác · đơn giá USD · lượng · đơn vị · xuất xứ · điều kiện giao hàng*; 22 cột còn lại bật trong nút **Cột**. Tên hàng dài (trung bình 187 ký tự) → cắt một dòng, rê chuột xem đủ, bấm dòng mở M2.

### 2.2 Thẻ *Biểu đồ* — chỉ hiện khi đã lọc

**Chưa lọc** → không vẽ gì, chỉ hiện một câu: *"Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ."*

Lý do chặn đúng như đại ca muốn: biểu đồ của **toàn bộ** dữ liệu là trộn hàng nghìn mặt hàng khác nhau, kg lẫn lít — con số ra vô nghĩa. **Bộ lọc đủ để vẽ = có từ khóa hoặc có mã HS.** Các ô lọc khác (xuất xứ, doanh nghiệp, khoảng ngày) chỉ thu hẹp thêm, một mình chúng chưa đủ.

**Đã lọc** →

```
│ Kỳ:  (•) Tháng  ( ) Quý  ( ) Năm          Giá:  (•) Ưu tiên giá điều chỉnh  ( ) Chỉ khai báo │
│ Đơn vị:  [ KGM · 60 dòng ]  [ LTR · 30 dòng ]  [ TNE · 2 dòng ]   ← vẽ từng đơn vị một       │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  Thấp nhất       Bình quân gia quyền     Cao nhất        Tổng lượng       Số dòng hàng       │
│  2,740 USD/kg    3,358 USD/kg            6,000 USD/kg    877 tấn          60                 │
│  Dựa trên 60 dòng hàng trong 8 tháng (không có dữ liệu tháng 7). Mới có dữ liệu năm 2026 —   │
│  một năm chưa đủ để kết luận theo mùa vụ.                                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  Biểu đồ giá: đường bình quân gia quyền + dải thấp–cao; điểm rỗng = kỳ dưới 5 dòng;          │
│  kỳ trống để trống; kỳ giá tốt nhất (đủ dữ liệu) tô màu                                      │
│  Biểu đồ lượng: cột lượng nhập theo kỳ                                                        │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  Bảng theo kỳ: kỳ · số dòng · tổng lượng · thấp nhất · bình quân gia quyền · cao nhất        │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

Bảng theo kỳ nằm **dưới biểu đồ trong cùng thẻ** — biểu đồ để nhìn, bảng để đọc số chính xác và chép đi.

### 2.3 Không còn gì phải tính sẵn

Bỏ trang tổng quan thì **mọi con số trên màn hình đều tính lúc mở**: danh sách đọc thẳng bảng, biểu đồ gom theo kỳ bằng SQL trên tập đã lọc, dải tháng đã phủ đếm thẳng. **Không có bảng tổng hợp, không có bản tính sẵn trong `tab_report_snapshot`, không có task định kỳ.** Chỉ xét lưu sẵn khi dữ liệu lên cỡ triệu dòng và đo được chậm thật ([`02`](./02-thiet-ke-ky-thuat.md) §3.7).

### 2.4 Trạng thái rỗng — phải nói đúng lý do

| Tình huống | Câu hiện ra |
|---|---|
| Chưa nạp lô nào | "Chưa có dữ liệu hải quan." + nút **Nạp dữ liệu** (nếu có quyền), hoặc "Liên hệ người phụ trách nạp dữ liệu" (nếu không) |
| Có dữ liệu nhưng từ khóa không khớp | "Không có dòng nào khớp «…»." + gợi ý bỏ bớt ô lọc |
| Khớp nhưng bộ lọc loại hết | "Có N dòng khớp từ khóa nhưng bộ lọc hiện tại loại hết." + nút **Bỏ lọc** |

Một câu chung cho cả ba là người gõ nhầm một chữ đọc ra "chưa có dữ liệu" và tin là vậy (luật chung của các màn danh sách).

---

## 3. M2 · M3 · M4

### M2 — Chi tiết một dòng hàng

Một dòng Excel là **một dòng hàng** của một tờ khai, không phải cả tờ khai — định nghĩa ở [`02`](./02-thiet-ke-ky-thuat.md) §2.2. Ngăn này hiện đủ 32 trường của dòng đó; phần đầu tờ khai (ngày, chi cục, doanh nghiệp, hợp đồng…) là thông tin lặp lại ở mọi dòng của cùng tờ khai. **Không có màn "xem cả tờ khai"** vì dữ liệu không có số tờ khai và đã bị lọc bớt dòng.

32 trường chia **6 nhóm**, mỗi giá trị bôi đen và sao chép được (không dùng ô nhập bị khóa):

| Nhóm | Trường |
|---|---|
| Tờ khai | Ngày đăng ký (kèm dấu **"đã vá ngày"** nếu dòng đó được vá) · Nơi mở tờ khai · Số thứ tự hàng |
| Các bên | Doanh nghiệp nhập + mã số thuế · Đối tác nước ngoài · Nước xuất xứ · Nước nhập khẩu |
| Hàng | Tên hàng đầy đủ · Mã HS · Lượng · Đơn vị tính |
| Giá | Đơn giá khai báo (USD / nguyên tệ) · Đơn giá điều chỉnh (USD / nguyên tệ) · Nguyên tệ · Tỷ giá nguyên tệ · Tỷ giá USD |
| Hợp đồng & vận chuyển | Số hợp đồng · Ngày hợp đồng · Điều kiện giao hàng · Phương tiện vận chuyển |
| Thuế | 5 thuế suất · 5 số tiền thuế |

Chân ngăn: hai liên kết **"Các lần nhập khác của doanh nghiệp này"** và **"… của đối tác này"** — đổ ngược bộ lọc vào M1.

### M3 — Nạp dữ liệu

```
Bước 1  Chọn tệp          [ Chọn tệp .xls ]  (chọn được nhiều tệp một lần)
Bước 2  Xem trước         ← chạy DRY_RUN, chưa ghi gì
        ┌──────────┬───────┬─────────────────────────┬──────────┬───────────┬──────────┐
        │ Tệp      │ Dòng  │ Khoảng ngày             │ Vá ngày  │ Sẽ thay   │ Cảnh báo │
        ├──────────┼───────┼─────────────────────────┼──────────┼───────────┼──────────┤
        │ 1.xls    │ 3.370 │ 02/01/2026 → 28/02/2026 │  1.482   │       0   │    —     │
        │ 2.xls    │ 4.772 │ 01/03/2026 → 30/04/2026 │  1.703   │   4.772   │    —     │  ← đã có dữ liệu khoảng này
        └──────────┴───────┴─────────────────────────┴──────────┴───────────┴──────────┘
Bước 3  [ Áp dụng ]       ← chạy nền, hiện tiến độ; xong thì M1 tự làm mới
```

- Cột **Sẽ thay** là cột quan trọng nhất: nó cho người nạp biết trước lần này sẽ **xóa bao nhiêu dòng cũ** trong khoảng ngày trùng.
- Tệp thiếu cột tiêu đề hay có mã phương tiện lạ → dòng đó **đỏ, không áp dụng được**, nói đúng cột nào thiếu.
- Nút **Áp dụng chặn bấm đúp ngay trong lượt bấm** — khóa nút bằng trạng thái hiển thị là không đủ, bấm liền tay vẫn gửi hai lần (luật chung của biểu mẫu).

### M4 — Lịch sử nạp

- **Bản cũ:** nút **Lịch sử nạp** trên M1 mở một hộp thoại. Bảng: lô · tệp · người nạp · lúc nạp · số dòng · khoảng ngày · trạng thái · nút **Hoàn tác** (chỉ người có `customs_price.delete`, hỏi xác nhận nói rõ sẽ xóa bao nhiêu dòng).
- **Bản mới:** không dựng lại — **màn `/system/imports` đã có** danh sách lô, chi tiết lô, nhật ký dòng. Nút **Lịch sử nạp** của M1 dẫn sang đó, lọc sẵn theo phân hệ hải quan.

---

## 4. Số liệu thật: ATRAZINE — và bốn điều nó buộc màn hình phải làm

Gõ *ATRAZINE* vào 5 tệp mẫu ra **92 dòng**: KGM 60 · LTR 30 · TNE 2. Riêng KGM, gom theo tháng (giá điều chỉnh USD nếu có, không thì giá khai báo):

| Tháng | Số dòng | Lượng (kg) | Bình quân gia quyền | Thấp nhất | Cao nhất |
|---|---|---|---|---|---|
| 01/2026 | 8 | 125.000 | 3,477 | 2,800 | 6,000 |
| 02/2026 | **3** | 42.000 | 4,580 | 2,880 | 6,000 |
| 03/2026 | 10 | 143.800 | 3,055 | 2,760 | 4,250 |
| 04/2026 | 12 | 178.000 | 3,488 | 2,740 | 6,000 |
| 05/2026 | **16** | 209.250 | **3,053** | 2,800 | 3,700 |
| 06/2026 | 7 | 146.000 | 3,586 | 2,850 | 6,000 |
| 07/2026 | **0** | — | — | — | — |
| 08/2026 | **3** | 23.000 | **2,817** | 2,770 | 2,950 |
| 09/2026 | **1** | 10.000 | 3,100 | 3,100 | 3,100 |

*(USD/kg. Đây là số đo thật, dùng làm số đối chiếu tính tay ở nghiệm thu HQ2.)*

> **Đính chính sau HQ4 (23/09/2026).** Bảng trên đo bằng **khớp tên hàng**. Bản dựng khớp **tên hàng HOẶC hoạt chất đã nhận ra**, nên cùng từ khóa ATRAZINE nay ra **96 dòng**: KGM **64** · LTR 30 · TNE 2 (thêm 4 dòng thành phẩm hỗn hợp có ATRAZINE mà tên hàng chỉ ghi tên thương mại). Số tháng đổi theo: 01/2026 10 dòng · 02/2026 4 · 03/2026 11 · 04/2026 12 · **05/2026 16 dòng, 3,053** · 07/2026 trống · 08/2026 3 dòng, 2,817 · 09/2026 1. Bốn kết luận bên dưới **giữ nguyên** — tháng 8 vẫn rẻ nhất mà chỉ có 3 dòng, tháng 5 vẫn là kỳ tốt nhất đủ dữ liệu.
> Có một lượt trung gian ra **78 dòng KGM** — đó là số SAI: 14 dòng thuốc kỹ thuật MESOTRIONE bị gắn nhầm ATRAZINE vì tên hàng nhắc tới thành phẩm hỗn hợp mà nó dùng để pha. Đã sửa ở bộ nhận hoạt chất (xem [`03`](./03-lo-trinh-phase.md) HQ4). Lọc thêm *Hàm lượng / dạng = 97%* thì còn 39 dòng thuốc kỹ thuật, bình quân **2,91**, trần **4,00** thay vì 6,00 — đúng như điều 4 dự đoán.

**1. Phải tách theo đơn vị.** Một phần ba số dòng ATRAZINE tính bằng **lít**. Cộng chung với kg là ra một con số vô nghĩa. → Hàng nút chọn đơn vị trên biểu đồ, mặc định đơn vị nhiều dòng nhất.

**2. Tháng không có dữ liệu phải hiện là trống.** Tháng 7 không có dòng nào. Vẽ thành 0 là nói dối "tháng 7 giá bằng 0"; nối đường qua là nói dối "tháng 7 giá khoảng 3,2". → Đứt đường ở tháng trống.

**3. Tháng ít dữ liệu không được "thắng".** Nhìn cột bình quân, **tháng 8 rẻ nhất (2,817)** — nhưng chỉ dựa trên **3 dòng**. Tháng 5 gần ngang (3,053) mà dựa trên **16 dòng**, đáng tin hơn nhiều. Ai chỉ nhìn biểu đồ sẽ chọn tháng 8. → **Điểm của kỳ ít hơn 5 dòng vẽ rỗng**, rê chuột thấy số dòng; nhãn **"tháng giá tốt nhất" chỉ xét các kỳ có từ 5 dòng trở lên**. *(Ngưỡng 5 là đề xuất, chỉnh được.)* Trợ lý AI ở HQ5 phải theo đúng luật này.

**4. Một từ khóa đang trộn nhiều dạng hàng.** Giá sàn đứng yên quanh **2,74–2,88** suốt 9 tháng, nhưng giá trần nhảy lên **6,000** ở 4 tháng — gần như chắc chắn là **thuốc kỹ thuật 97%** lẫn với **thành phẩm dạng bột 80WP** cùng mang chữ ATRAZINE. Dải thấp–cao vì vậy rộng gấp đôi và kéo bình quân lên. → Đợt 1: vẫn vẽ dải nhưng tô nhạt, và bảng *Dòng hàng* cho người dùng tự nhìn tên hàng. Đợt 2: **tách theo hoạt chất và hàm lượng** (T-04, M7) — đây là lý do T-04 đáng làm.

---

## 5. Bản cũ và bản mới khác nhau ở đâu

| Thành phần | Bản cũ `frontend/` | Bản mới `frontend-v2/` |
|---|---|---|
| Đường dẫn | Route riêng trong `App.tsx` | `routes.tsx` của phân hệ Thu mua |
| Menu | `layouts/AppLayout.tsx`, nhóm Báo cáo | `modules/procurement/routes.tsx`, nhóm Báo cáo |
| Ô lọc | `components/FilterBar.tsx` sẵn có | Thanh lọc + ô chọn sẵn có; chọn nhiều giá trị dùng `useUrlMultiParam` (CR-423) |
| Biểu đồ | **SVG tự vẽ** theo khuôn `LineChart` / `BarChart` trong `pages/Reports.tsx`. Viết thành phần **riêng trong trang mới** — không sửa `Reports.tsx`, **không thêm thư viện** vào bản cũ | `recharts` có sẵn: một khung ghép vùng (dải thấp–cao) + đường (bình quân) + cột (lượng) |
| Bảng 32 cột | Bảng thường + `components/TableToolbar.tsx` (nút **Cột**, ẩn/hiện) | `DataTable`, bố cục cột nhớ theo người dùng |
| Chi tiết dòng (M2) | Hộp thoại | **Popup giữa màn** (đại ca chốt 23/09/2026 — bản đầu là ngăn kéo bên phải), chân popup có hai nút lọc nhanh cùng doanh nghiệp / cùng đối tác |
| Lịch sử nạp (M4) | Hộp thoại — **bản cũ không có màn Quản lý Import** | Liên kết sang `/system/imports` |
| Định dạng giá | `fmtPrice` (giữ 4 số lẻ) + chữ **"USD/kg"** viết riêng. ⚠️ **Không dùng `fmtVND`** — hàm đó làm tròn về đồng, cắt mất phần lẻ của giá USD | Hàm định dạng số sẵn có, 4 số lẻ |
| Trạng thái lọc | Giữ trong trang | **Nằm trên đường dẫn** — gửi link cho người khác là họ thấy đúng kết quả đang xem |

---

## 6. Luật chung phải theo (đều đã từng gây lỗi ở màn khác)

- **Rỗng vì lọc ≠ chưa có dữ liệu** — §2.3.
- **Đổi bộ lọc phải kéo trang về 1** — bản mới dùng `usePageResetOnFilterChange`, theo dõi từ khóa **đã hoãn** chứ không theo từng phím gõ.
- **Cột ẩn mặc định chỉ áp cho người chưa từng đụng nút Cột** — sửa danh sách cột mặc định xong mà màn hình không đổi thì không phải mã sai.
- **Ô chỉ xem ở M2 không dùng ô nhập bị khóa** — khóa là mất khả năng bôi đen và sao chép.
- **Nút Áp dụng ở M3 chặn bấm đúp ngay trong lượt bấm** — §3.
- **Giá USD giữ đủ 4 số lẻ**, dấu thập phân kiểu Việt: `2,817 USD/kg`.

---

## 7. Bản dựng 23/09/2026 khác đề xuất ở đâu

| Chỗ | Đề xuất | Bản dựng | Vì sao |
|---|---|---|---|
| Số thẻ của M1 | Hai thẻ (+ M5–M9 gắn vào sau) | **Năm thẻ ngay từ đầu:** *Danh sách · Biểu đồ · Nhà nhập khẩu · So sánh · Pháp lý & thuế* | Đại ca bảo làm đủ mọi phase một lượt. *Biểu đồ* và *Nhà nhập khẩu* theo đúng luật "chưa lọc thì không vẽ"; *So sánh* có ô từ khóa riêng; *Pháp lý & thuế* tra độc lập được |
| Menu bản cũ | Nhóm Báo cáo | Nhóm **Mua hàng**, ngay sau *Tiến độ mua hàng* | Người dùng là thu mua, đứng cạnh các màn họ mở hằng ngày |
| Nút *Lịch sử nạp* | Chỉ người có `customs_price.write` | **Mọi người có quyền đọc** đều thấy; nút *Hoàn tác* trong đó mới cần `customs_price.delete` | Người xem cần biết dữ liệu nạp khi nào, từ tệp nào — để tin hay không tin con số |
| M4 bản mới | Dẫn sang `/system/imports` | **Hộp thoại riêng như bản cũ** | `/system/imports` gác bằng khóa `import` (quản trị); người thu mua được tick `customs_price` thường không có khóa đó. Lô hải quan vẫn nằm trong bảng lô chung nên quản trị vẫn thấy ở `/system/imports` |
| Lọc doanh nghiệp | Ô chọn *Doanh nghiệp* trên thanh lọc | **Bấm một dòng ở thẻ Nhà nhập khẩu** → lọc cả trang, hiện thẻ nhỏ kèm nút bỏ | 3.503 doanh nghiệp — ô chọn thả xuống vô dụng; xếp hạng theo lượng đã là cách tìm doanh nghiệp tự nhiên |
| Cảnh báo pháp lý | Chỉ trong M9 | Thêm **dải cảnh báo ngay dưới thanh lọc** khi từ khóa trùng hóa chất cấm / có ngưỡng / phải công bố | Thay tạm cho P-02 (so tồn kho) chưa làm được; cảnh báo đúng lúc người ta đang tính mua |
| M8 | "Ngưỡng khai tay" | **Danh mục hóa chất theo văn bản** (`/customs-regulations`, khóa `customs_regulation`) nạp sẵn từ phần mềm ngoài, sửa tay khi văn bản đổi | Ngưỡng có sẵn trong NĐ 24/2026 Phụ lục IV — xem đính chính P-01 ở [`01`](./01-danh-sach-tinh-nang.md) |
| Dải tô nhạt trên biểu đồ giá | Thấp – cao | **Khoảng giá phổ biến = phân vị 25–75%** (nửa số dòng ở giữa); thấp / cao / số dòng / lượng hiện ở **ô rê chuột** và bảng; đếm và nói ra số «dòng giá bất thường» (luật hộp râu 1,5 × IQR) | Đại ca bắt lỗi 23/09: vài dòng 250 USD/lít (gói nhỏ, khai khác đơn vị) giữa đám 2–4 USD/lít kéo trục lên trần, đường bình quân dẹp sát đáy, không đọc được. Thêm: SVG vẽ đúng bề rộng đo được (không co giãn chữ), hai biểu đồ giá / lượng chung trục ngang, trục chia số tròn, trục lượng viết gọn «2 tr» |
| Cột mặc định bảng dòng hàng | 10 cột, 22 cột ẩn trong nút **Cột** | **Hiện HẾT 32 cột đúng thứ tự và tiêu đề Excel**, rồi hai cột suy ra *Hoạt chất* · *Hàm lượng / dạng* ở cuối; không có cột giá gộp riêng | Đại ca chốt 23/09/2026: *"về thứ tự và số lượng cột thì mặc định là show full cột"*. Muốn gọn thì người dùng tự ẩn ở nút **Cột** |
