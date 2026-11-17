# Giải thích từng quy trình của Phòng Sản xuất

*Em viết để đại ca hiểu **logic**: mỗi quy trình sinh ra để làm gì, chạy thế nào, nối với quy trình khác ra sao. Không dùng chữ viết tắt. Hai nguồn (khảo sát MIC và tệp bàn giao) nói khác nhau thì em theo khảo sát MIC. Muốn tra nguồn từng ý thì xem [tai-lieu-gop-phong-san-xuat.md](tai-lieu-gop-phong-san-xuat.md).*

## Mục lục

- [Phần A. Bức tranh chung](#phần-a-bức-tranh-chung)
  - [A1. Phòng làm gì, trong một câu](#a1-phòng-làm-gì-trong-một-câu)
  - [A2. Mấy chữ phải hiểu trước](#a2-mấy-chữ-phải-hiểu-trước)
  - [A3. Các quy trình nối với nhau thế nào](#a3-các-quy-trình-nối-với-nhau-thế-nào)
  - [A4. Ai giữ việc gì](#a4-ai-giữ-việc-gì)
- [Phần B. Giải thích từng quy trình](#phần-b-giải-thích-từng-quy-trình)
  - [1. Làm việc với nhà máy mới](#1-làm-việc-với-nhà-máy-mới)
  - [2. Khai báo mã](#2-khai-báo-mã)
  - [3. Tính giá vốn](#3-tính-giá-vốn)
  - [4. Quản lý đơn hàng gia công (quan trọng nhất)](#4-quản-lý-đơn-hàng-gia-công-quan-trọng-nhất)
  - [5. Kiểm pháp lý](#5-kiểm-pháp-lý)
  - [6. Quản lý nhà máy: giấy tờ, công nợ, trả tiền](#6-quản-lý-nhà-máy-giấy-tờ-công-nợ-trả-tiền)
  - [7. Công thức cho thuế](#7-công-thức-cho-thuế)
  - [8. Nguyên liệu và hàng pha sẵn](#8-nguyên-liệu-và-hàng-pha-sẵn)
  - [9. Bao bì](#9-bao-bì)
  - [10. Gọi xe Grab](#10-gọi-xe-grab)
  - [11 và 12. Xử lý sự cố](#11-và-12-xử-lý-sự-cố)
  - [13. Ngưng hợp tác với nhà máy (chưa viết)](#13-ngưng-hợp-tác-với-nhà-máy-chưa-viết)
  - [Ai được ký giấy gì (chưa viết)](#ai-được-ký-giấy-gì-chưa-viết)
- [Phần C. Em đánh giá chung](#phần-c-em-đánh-giá-chung)

---

## Phần A. Bức tranh chung

### A1. Phòng làm gì, trong một câu

**Phòng Sản xuất là "tổng thầu":** bên bán đặt hàng; phòng thuê khoảng 12 nhà máy ngoài làm hộ, gửi nguyên liệu và bao bì sang, theo dõi tới khi hàng về kho, kiểm chất lượng, tính giá vốn, rồi làm giấy tờ để Kế toán trả tiền nhà máy.

Khoảng **42 đơn mỗi tháng**, mỗi đơn **10–20 ngày**. Mọi thứ chạy trên Google Drive và Zalo.

### A2. Mấy chữ phải hiểu trước

| Chữ | Nghĩa |
|---|---|
| **Gia công** | Thuê nhà máy ngoài làm hộ. DEGO không có nhà máy riêng |
| **Nguyên liệu** | Hóa chất gốc, hoạt chất, phụ gia |
| **Hàng pha sẵn** (tài liệu gốc gọi *bán thành phẩm*) | Thuốc hoặc phân đã pha xong nhưng **chưa đóng chai, đóng túi** |
| **Thành phẩm** | Hàng đã đóng gói, dán nhãn, bán được |
| **Bao bì** | Chai, nắp, nhãn, túi, thùng carton |
| **Công thức** (tài liệu gốc gọi *bảng định mức*) | Một sản phẩm cần bao nhiêu nguyên liệu, bao nhiêu bao bì. Có 3 tầng: công thức hàng pha → công thức bao bì → ghép thành công thức thành phẩm |
| **Bên bán** | Các thương hiệu nội bộ đặt hàng: IDA, ABA, BamBoo, Dr Xanh, N2SBIO |
| **Hình mẫu bao bì** (mockup) | Ảnh thiết kế nhãn, chai, thùng do phòng Thiết kế làm |
| **Đơn đặt hàng gửi nhà máy** | Phiếu gửi nhà máy, không ghi giá |
| **Lệnh sản xuất** | Giấy chính thức ra lệnh làm, gắn với hóa đơn |
| **Lab** | Phòng kiểm nghiệm, nói đạt hay không đạt |
| **Giá vốn** | Chi phí thật để làm ra một sản phẩm |
| **Công ty sở hữu sản phẩm** | Công ty nội bộ đứng tên giấy phép sản phẩm. Hóa đơn phải xuất cho công ty này, không phải công ty đặt hàng |

### A3. Các quy trình nối với nhau thế nào

```
                 [1. Nhà máy mới]                 [2. Khai báo mã]
                        │                                │
                        ▼                                ▼
   [3. Tính giá vốn] ──► [4. ĐƠN HÀNG GIA CÔNG] ◄── [7. Công thức cho thuế]
                        ▲     │      │
   [8. Nguyên liệu] ────┘     │      └────► [11-12. Sự cố] (khi có lỗi)
   [9. Bao bì] ───────────────┤
   [5. Kiểm pháp lý] ─────────┘
                              │
                              ▼
                 [6. Giấy tờ, công nợ, trả tiền nhà máy]

   Chạy riêng: [10. Gọi xe Grab]      Chưa viết: [13. Ngưng hợp tác]
```

> **Logic:** quy trình **4 (đơn hàng)** là xương sống. Các quy trình 3, 5, 8, 9 là **bảy cửa kiểm** trước khi đơn được đi. Quy trình 1 và 2 tạo **dữ liệu nền** (nhà máy, mã hàng). Quy trình 6 **khép sổ** (trả tiền). Quy trình 11–12 là **lối thoát khi có lỗi**.

### A4. Ai giữ việc gì

| Người | Giữ quy trình |
|---|---|
| Chị Ngân (Trưởng phòng) | Duyệt mọi thứ; đang kiêm Trưởng nhóm Điều phối |
| Thảo, Ngọc, Oanh (điều phối thành phẩm) | 4. Đơn hàng; 10. Grab (Oanh) |
| Oanh (điều phối nguyên liệu) | 8. Nguyên liệu và hàng pha |
| Ly, Tiên, An (điều phối bao bì) | 9. Bao bì |
| Hương (giá vốn) | 3. Tính giá vốn |
| Anh Huỳnh (trưởng nhóm Hồ sơ, kiêm Pháp lý) | 5. Pháp lý; ký giá vốn thật; duyệt hợp đồng, sự cố |
| Thơ, Liên, Khang (hồ sơ nhà máy) | 1. Nhà máy mới; 6. Công nợ, trả tiền; 7. Công thức cho thuế |
| Bảo Thi (xử lý sự cố) | 11–12. Sự cố |

---

## Phần B. Giải thích từng quy trình

### 1. Làm việc với nhà máy mới

**Để làm gì:** tìm và ký với một nhà máy gia công mới.
**Khi nào:** có sản phẩm mới mà nhà máy cũ không làm được; nhà máy cũ làm không tốt; hoặc muốn so giá. Năm nay có khoảng 4 nhà mới.

**Chạy thế nào:**
1. Chị Ngân nhận yêu cầu, tìm vài nhà máy (nhờ người quen, Thu mua, tìm trên mạng).
2. Người hồ sơ **kiểm giấy phép** của nhà máy: có được phép sản xuất không. Không đạt thì bỏ, tìm nhà khác.
3. Bên bán chốt **danh sách sản phẩm** sẽ làm ở nhà máy này; Giám đốc duyệt.
4. **Thử mẫu**: gửi công thức cho nhà máy pha thử, Lab kiểm. Mất 10–14 ngày; thử 2 lần không đạt thì bỏ.
5. Làm **bảng giá** gia công (chị Ngân ký).
6. Làm **hợp đồng**: người hồ sơ soạn → anh Huỳnh duyệt → Pháp lý → Kế toán → Giám đốc ký. Có khoảng 25 điều phải chốt (giá, cọc nhãn, công nợ, lưu kho, số lượng tối thiểu, kiểm hàng, xử lý hàng lỗi...).
7. **Biên bản bàn giao nội bộ** (Mẫu 05): những gì thỏa thuận miệng mà không ghi vào hợp đồng phải ghi ra đây, giao cho Hương để báo giá cho bên bán.

> **Logic:** đi theo thứ tự *giấy phép → sản phẩm → mẫu → giá → hợp đồng*. Lọc rẻ trước (giấy phép), tốn công sau (thử mẫu). Mẫu 05 có để **không mất thỏa thuận miệng** khi người đàm phán không phải người trong phòng.

**Còn vướng:** bước so sánh, chọn nhà máy chưa giao cho ai. Tệp ghi chị Ngân duyệt hợp đồng, nhưng khảo sát nói anh Huỳnh duyệt; em theo khảo sát.

---

### 2. Khai báo mã

**Để làm gì:** mỗi nguyên liệu, bao bì, hàng pha, thành phẩm, nhà máy... phải có **một mã duy nhất**, để Drive của phòng và phần mềm Kế toán gọi cùng một tên.
**Khi nào:** có thứ gì mới.

**Chạy thế nào:**
1. Người phụ trách loại hàng đó khai trên Drive *Dữ liệu đầu vào sản xuất*. Ví dụ: bao bì do Ly khai, nguyên liệu do Thu mua khai, nhà máy do người hồ sơ khai.
2. Tự kiểm có bị trùng không.
3. Gửi nhóm Zalo chung với Kế toán; **chị Ngân duyệt ngay trên Zalo**.
4. Kế toán nhập vào phần mềm MISA, báo lại.
5. Người khai cập nhật Drive.

**Quy tắc mã:** mỗi loại có đầu mã riêng. Ví dụ NLNK là nguyên liệu nhập khẩu, N là túi / nhãn, TH là thùng carton.

> **Logic:** đây là **gốc của mọi số liệu**. Mã sai hoặc trùng thì tồn kho và giá vốn sai theo. Vì vậy người khai **tự chịu trách nhiệm**, chị Ngân chỉ duyệt nhanh qua Zalo.

**Còn vướng:**
- **Chưa có quy tắc đặt mã cho đơn hàng, sự cố, công thức.** ERP cần cái này đầu tiên.
- Mã hàng pha "ruột" do Thu mua hay Oanh khai: tệp tự ghi hai kiểu.
- Bảng danh mục gốc (*Data 1*) chưa chốt. Bảng này mà đổi là mọi Drive phải chạy lại.

---

### 3. Tính giá vốn

**Để làm gì:** biết làm một sản phẩm tốn bao nhiêu, để bên bán định giá và biết lời lỗ.

**Có 3 lúc tính:**

| Lúc | Chuyện gì | Ai |
|---|---|---|
| **Trước khi có đơn** | Bên bán hỏi *làm cái này hết bao nhiêu*. Hương kiểm giấy phép, kiểm công thức, hỏi giá nguyên liệu, bao bì, phí gia công rồi lập bảng giá. Kết quả ghi vào Drive *Dự trù kinh doanh*. Không có hạn trả lời | Hương |
| **Lúc duyệt đơn** | Hương kiểm lại giá, lập *Phiếu duyệt giá* với 3 mức (giá nội bộ, giá cho thuế, giá bán). Chị Ngân ký. **Quy định mới:** phòng không cảnh báo lời lỗ nữa, bên bán tự xem | Hương, chị Ngân |
| **Sau khi hàng về kho** | Tính **giá thật** từ chi phí thực tế, chụp gửi Kế toán qua Signal, anh Huỳnh ký | Hương, anh Huỳnh |

> **Logic:** giá đi từ **ước** (lúc hỏi) → **duyệt** (lúc đặt) → **thật** (lúc xong). Lệch giữa các lần là chỗ lời lỗ thay đổi.

**Còn vướng:** đang có **3 con số giá vốn khác nhau** (của bên bán, của Sản xuất, của Kế toán), nên hay vênh. Tệp ghi chị Ngân ký giá thật và tính khi có lệnh sản xuất; khảo sát nói anh Huỳnh ký và tính khi hàng về kho. Em theo khảo sát.

---

### 4. Quản lý đơn hàng gia công (quan trọng nhất)

**Để làm gì:** đưa một đơn từ lúc bên bán đặt tới lúc hàng về kho và đạt chất lượng.
**Có 3 loại đơn:** đơn thành phẩm, đơn hàng pha, đơn làm lại (khi có lỗi).

**Chạy thế nào:**

| Bước | Chuyện gì xảy ra | Vì sao |
|---|---|---|
| 1. Nhận đơn | Bên bán ghi đơn lên Drive, nhắn Zalo. Điều phối thành phẩm kiểm đủ thông tin; **thiếu hình mẫu bao bì thì dừng** | Không có hình bao bì thì không biết đóng gói thế nào |
| 2. Bảy người kiểm | Oanh (đủ nguyên liệu?), Ly (đủ bao bì?), Hương (giá ổn?), anh Huỳnh (giấy phép? hóa đơn xuất cho công ty nào?), Bảo Thi (đơn có dính sự cố cũ?), người hồ sơ (công thức thành phẩm), chị Ngân. Trơn tru thì khoảng 1 buổi | Mỗi người chặn một loại rủi ro, để không gửi một đơn sẽ hỏng |
| 3. Trưởng phòng duyệt | Chị Ngân tick cột duyệt. Có lúc **duyệt trước, giấy tờ bổ sung sau** | Để không trễ hàng; nhưng việc này chỉ dựa vào kinh nghiệm của chị |
| 4. Gửi đơn nhà máy | Gửi qua Zalo kèm hình bao bì. **Không ghi giá** | Giữ bí mật giá |
| 5. Theo dõi | Hỏi lại sau 2 ngày, và 2 ngày trước ngày có hàng; báo cáo hằng ngày | Nhà máy hay trễ, phải đôn đốc |
| 5a. Có hàng | Nhà máy báo xong. Lập đề nghị nhập kho; người hồ sơ đi lấy hóa đơn | Hóa đơn phải xuất cùng ngày hoặc sau lệnh sản xuất |
| 5b. Nhận hàng | Kho Dr Xanh nhận, kiểm số thùng, kiểm bề ngoài | |
| 6. Kiểm chất lượng | **Đơn nào cũng gửi mẫu Lab.** Kiểm bề ngoài 1–2 ngày, kiểm hàm lượng khoảng 14 ngày. Không đạt thì chuyển sang quy trình sự cố | Lab là người quyết đạt hay không |
| 7. Chốt xong | Đủ 3 thứ: Lab đạt, kho nhận đủ, có hóa đơn. Khóa đơn. Số lượng lệch thì hỏi bên bán: thiếu thì làm thêm hay hủy, dư thì nhận hay không | Khóa để không ai sửa số sau khi xong |
| 8. Trả tiền | Chuyển sang quy trình 6 | |

**Hủy đơn** (chỉ có trong tệp):
- Chưa gửi nhà máy: dừng mua, dừng pha, bên yêu cầu hủy chịu chi phí.
- Đã gửi mà nhà máy không chịu hủy: hỏi bên bán có nhận hàng không. Không nhận thì chuyển sang quy trình sự cố.

> **Logic:** *kiểm kỹ trước khi gửi* (bước 2–3), *đôn đốc trong lúc làm* (bước 5), *kiểm kỹ sau khi xong* (bước 6–7). Chỗ chậm nhất là bước 2: bảy người, không ai có hạn chót.

**Còn vướng:**
- **Chưa có danh sách trạng thái đơn chuẩn** (đang chờ duyệt, đã gửi nhà máy, chờ hóa đơn, đã nhận hàng, Lab không đạt, hoàn thành...). ERP cần cái này.
- Chốt đơn khi Lab báo đạt **bề ngoài**, hay phải chờ đạt **hàm lượng** (14 ngày): chưa rõ.
- Chưa có luật *được cho nợ giấy tờ tới đâu*.

---

### 5. Kiểm pháp lý

**Để làm gì:** chắc chắn đơn hàng **hợp pháp** trước khi làm, và hóa đơn xuất **đúng công ty**.
**Ai:** anh Huỳnh. Đây là một trong bảy cửa kiểm của quy trình 4.

**Kiểm 5 thứ trên mỗi đơn:**
1. Đơn có đang dính sự cố cũ không.
2. **Nguồn gốc sản phẩm**: giấy đăng ký thuốc / phân còn hạn không, công ty nào đứng tên.
3. **Điều kiện sản xuất**: nhà máy có giấy phép sản xuất loại này không.
4. **Điều kiện mua bán**: có hợp đồng, giấy phép mua bán không.
5. **Dòng hóa đơn**: hóa đơn xuất cho công ty nào. Ví dụ IDA đặt nhưng sản phẩm đứng tên BamBoo thì hóa đơn xuất cho BamBoo.

Ngoài ra anh Huỳnh theo dõi **hạn giấy tờ** (giấy đăng ký, ủy quyền, thuê tên) để báo gia hạn.

> **Logic:** thuốc bảo vệ thực vật bị quản rất chặt. Làm hàng khi giấy hết hạn, hoặc xuất hóa đơn sai công ty, là rủi ro phạt và rủi ro thuế. Vì vậy pháp lý là một cửa riêng.

**Còn vướng:**
- Khảo sát MIC **không hỏi** quy trình này.
- Không bước nào ghi ai duyệt lại.
- Chưa rõ có kiểm cho cả đơn hàng pha và việc mua nguyên liệu không.
- Chưa rõ ai báo hạn giấy tờ: Pháp lý sản xuất hay Pháp lý chung của công ty.

---

### 6. Quản lý nhà máy: giấy tờ, công nợ, trả tiền

**Để làm gì:** giữ hồ sơ với từng nhà máy và **khép sổ tiền**.
**Ai:** Thơ, Liên, Khang, mỗi người giữ vài nhà máy; anh Huỳnh kiểm.

**Theo từng đơn:**
- Ghép **công thức thành phẩm** (từ công thức hàng pha + bao bì), gửi Kế toán.
- Lấy **hóa đơn** của nhà máy.
- Lập **lệnh sản xuất**, phiếu nhập kho, xuất kho, chuyển kho gửi Kế toán.
- Nếu bán hàng pha giữa các công ty nội bộ: làm phiếu xuất bán, phụ lục; gửi Kế toán trước ngày 5 tháng sau.

**Theo tháng:**
- **Đối chiếu tồn kho** với nhà máy. Lệch thì chứng minh cho nhà máy, theo tới khi khớp; chị Ngân ký biên bản.
- **Đối chiếu công nợ** (số nội bộ và số thuế): trình ký **trước ngày 20**.
- **Trả tiền** khi tới hạn. Bộ hồ sơ có 14 loại giấy (đề nghị thanh toán, hóa đơn, hợp đồng, đơn đặt hàng, phiếu kho, biên bản đối chiếu, ủy nhiệm chi...).
- Theo dõi phí phạt, chiết khấu, phí lưu kho, chia theo thương hiệu.
- **Dự chi** cho tháng sau: làm ngày 25–28.

**Theo hợp đồng:** báo gia hạn hợp đồng và giấy tờ pháp lý **trước 3 tháng** (6 tháng nếu công ty đứng tên sản phẩm).

> **Logic:** đây là nơi **tiền và giấy gặp nhau**. Quy trình 4 lo hàng chạy; quy trình 6 lo giấy tờ đủ để Kế toán trả tiền và khai thuế được.

**Còn vướng:**
- Nhiều nhà máy **không chịu ký** đơn đặt hàng, giấy đề nghị thanh toán, xác nhận công nợ (Thái Nông, An Nông, Hà Long...).
- Biên bản giao nhận hay ghi sai công ty.
- Chưa có Drive theo dõi phí phạt.

---

### 7. Công thức cho thuế

**Để làm gì:** làm **công thức bản cho thuế**, vì cơ quan thuế xem công thức để chấp nhận chi phí nguyên liệu, bao bì.
**Ai:** Oanh (hàng pha), Ly (bao bì), người hồ sơ (thành phẩm); chị Ngân ký bản in.

**Chạy thế nào:**
- Công thức hàng pha tính trên 1.000 lít hoặc kg. Chỉ lập mới khi đổi dạng (lỏng / rắn), đổi hàm lượng hoặc đổi tỷ trọng.
- Công thức bao bì và thành phẩm tính trên 1 đơn vị sản phẩm.
- Bản gốc gửi Kế toán; bản điện tử gửi nhóm Zalo thuế theo từng công ty (IDA Global, Dego Holding, ABA).

> **Logic:** công thức **nội bộ** để làm hàng; công thức **thuế** để hợp lệ chi phí. Hai bản có thể khác nhau, ví dụ thuế tính chai và nắp là một bộ, nội bộ tính riêng. Đây là một nguồn của chuyện *hai bộ số liệu*.

**Còn vướng:** khảo sát MIC không hỏi quy trình này. Phần thuế cho hao hụt chưa thống nhất với Kế toán.

---

### 8. Nguyên liệu và hàng pha sẵn

**Để làm gì:** lúc nào cũng có đủ nguyên liệu và hàng pha đúng chỗ, đúng lúc, cho các đơn.
**Ai:** Oanh.

**Chạy thế nào:**
1. **Khảo sát**: Hương nhờ Oanh hỏi giá, thử công thức với nhà máy (10–14 ngày).
2. **Kiểm tồn khi có đơn**: đủ hàng pha thì cho làm luôn; đủ nguyên liệu thì đề nghị pha; tồn ở kho khác thì hỏi bên bán; không có thì mua.
3. **Lập công thức hàng pha** (lấy công thức kỹ thuật từ Lab, chị Ngân ký).
4. **Dự trù mua**: bên bán gửi dự trù **ngày 15 hằng tháng**; Oanh trả lời trong **5 ngày làm việc**, lập phiếu mua gửi Thu mua.
5. **Đề nghị pha**: gửi nhà máy pha từ nguyên liệu có sẵn.
6. **Theo dõi pha**; hao hụt vượt mức cho phép thì báo chị Ngân.
7. **Chuyển kho** giữa các nhà máy: chọn xe, báo nhà máy trước 1 ngày, gửi giấy cho Kế toán trong ngày.
8. **Nhập kho, xuất kho, hao hụt**: hao hụt vượt mức thì nhà máy đền; trong mức thì tính vào chi phí.
9. **Đối chiếu tồn hằng tháng** (Drive, MISA thuế, MISA nội bộ), chia phí lưu kho theo thương hiệu.
10. **Tính giá hàng pha** từ giá nguyên liệu + phí pha (ví dụ dạng lỏng SL 12 nghìn, dạng EC 40–55 nghìn).

> **Logic:** cùng một mục đích *không để thiếu hàng khi tới ngày làm*, nhưng phải **cân với tiền tồn kho và phí lưu kho**. Vì vậy mua theo dự trù của bên bán, không mua dư.

**Còn vướng:**
- **Chưa có bảng** ghi rõ với từng sản phẩm, từng nhà máy: ai chuẩn bị nguyên liệu, công ty hay nhà máy.
- Hàng dư sau sản xuất chưa ai ghi nhận ("sẽ xây dựng sau").
- Tỷ lệ hao hụt cho phép chưa thống nhất với Kế toán.

---

### 9. Bao bì

**Để làm gì:** đủ chai, nhãn, túi, thùng đúng mẫu tại nhà máy trước ngày đóng gói.
**Ai:** Ly (việc chung), Tiên (Hà Long), An (các nhà khác).

**Chạy thế nào:**
1. Mỗi sản phẩm có **công thức bao bì** (lấy từ hình mẫu bao bì của Thiết kế).
2. Có đơn: kiểm tồn bao bì; thiếu thì chuyển từ chỗ khác, mua, hoặc thay loại khác.
3. **Mua**: phản hồi bên bán trong 4 ngày. Thời gian làm bao bì: nhãn thường 7 ngày, túi in 21 ngày, thùng khoảng 15–18 ngày, nên phải đặt sớm.
4. **Cọc nhãn**: một số nhà máy giữ tiền cọc nhãn; hoàn cọc theo sản lượng.
5. Nhập, xuất kho; hao hụt ngoài mức thì nhà máy trả.
6. Đối chiếu tồn hằng tháng, báo cáo bên bán (giá cao nhất / thấp nhất 5 lần mua gần nhất, hao hụt, cọc nhãn).

> **Logic:** bao bì là thứ **chậm nhất** để có (tới 21 ngày) và **dễ sai nhất** (đóng nhầm nhãn, nhầm chai), nên cần người riêng.

**Còn vướng:**
- **Mã bao bì của mình lệch mã nhà máy**, nên hay đóng nhầm.
- Hà Long hao hụt túi tới 23%.
- Bao bì mang sang nhà máy **trên 5 tỷ** chưa vào được sổ thuế.
- Cọc nhãn ở 6 nhà mà phần lớn chưa có giấy xác nhận.
- 4 điểm trong quy trình ghi *cần thống nhất trước khi ban hành*.

---

### 10. Gọi xe Grab

**Để làm gì:** gửi mẫu, vật tư nhỏ giữa kho, nhà máy, Lab.
**Ai:** Oanh giữ tài khoản Grab chung.

**Chạy thế nào:** tạm ứng khoảng 1 triệu mỗi tháng (chị Ngân duyệt) → nhận yêu cầu qua Zalo → nếu lấy mẫu từ kho thì làm phiếu xuất kho → đặt xe trên app → **cuối tháng** gom hóa đơn, làm 2 bộ đề nghị thanh toán (một bộ chia theo thương hiệu, một bộ cho thuế về Dego) → chị Ngân ký → hoàn ứng trong **7 ngày làm việc**.

> **Logic:** báo giá Grab đã duyệt từ đầu, nên **không duyệt từng chuyến**, chỉ quyết toán cuối tháng.

---

### 11 và 12. Xử lý sự cố

**Để làm gì:** khi có lỗi thì xử lý, chia trách nhiệm, đòi tiền đúng người.
**Hai loại:** **trong sản xuất** (thiếu nguyên liệu, bao bì sai, pha không đạt, nhà máy trục trặc) và **sau sản xuất** (hàng lỗi ở kho, ở khách, khi vận chuyển). Khảo sát coi đây là **một quy trình, hai nhánh**.

**Chạy thế nào:**
1. **Nhận tin**: ai thấy thì báo Zalo kèm ảnh, video, mã, số lượng, date.
2. **Phân loại**:
   - Lỗi nhỏ, **không ảnh hưởng giá và công nợ** → điều phối tự xử lý luôn.
   - Còn lại → **Bảo Thi** nhận, ghi sổ sự cố.
3. **Kiểm** tồn kho, tiến độ, hợp đồng để xem phương án nào khả thi.
4. **Lập phương án** (dùng hàng thay thế, làm lại, thu hồi, đổi nhà máy...). Anh Huỳnh duyệt, vướng thì lên chị Ngân.
5. **Giấy tờ**: hủy hoặc điều chỉnh hóa đơn, phiếu kho, công thức mới nếu đổi.
6. **Chia tiền**: **ai gây lỗi người đó chịu**. Biên bản cấn trừ công nợ hoặc thu hồi tiền.
7. **Làm lại hàng** thì mở *đơn làm lại*, đi qua bảy người kiểm như đơn mới.
8. Lưu lại để đơn sau tránh.

> **Logic:** tách *lỗi nhỏ, xử lý tại chỗ* với *lỗi có tiền dính vào*. Hễ dính tới giá hay công nợ là phải có người chuyên trách và có giấy tờ, vì sau này phải đòi tiền nhà máy hoặc trừ chi phí bên bán.

**Còn vướng:**
- Không có hạn chót (phòng cho là đúng, vì mỗi vụ một khác).
- Chưa có mức tiền bắt buộc phải lên chị Ngân.
- Chưa đếm mỗi tháng bao nhiêu vụ.
- Tệp ghi điều phối làm hết, khảo sát nói Bảo Thi làm chính; em theo khảo sát.

---

### 13. Ngưng hợp tác với nhà máy (chưa viết)

Mục lục có tên, nhưng **chưa có nội dung**. Những gì đang biết:
- Chấm điểm nhà máy **dưới 60 / 100 thì ngưng**. Chưa chấm lần nào vì chưa có biểu mẫu.
- Nhà máy không ký đơn, pha 2 lần không đạt, hoặc bên bán muốn đổi thì đổi nhà máy.
- Trước khi chuyển sang nhà khác: kiểm giấy phép, năng lực, nhãn, giá của nhà mới.

**Cần viết thêm:**
- Thu hồi nguyên liệu, bao bì, khuôn in từ nhà cũ.
- Đòi lại tiền cọc nhãn.
- Đối chiếu tồn và công nợ lần cuối.
- Thanh lý hợp đồng.
- Xử lý nhãn cũ còn tồn.
- Ai quyết ngưng.

Ca thật để học: Basel hết giấy phép từ 01/2024.

---

### Ai được ký giấy gì (chưa viết)

Mục lục ghi *chưa có*. Em gom tạm từ hai nguồn:

| Giấy tờ | Ai lập | Ai ký |
|---|---|---|
| Hợp đồng với nhà máy | Người hồ sơ | Anh Huỳnh duyệt → Pháp lý → Kế toán → Giám đốc ký (chỉ ký, không quyết) |
| Danh sách sản phẩm với nhà máy mới | Bên bán | Giám đốc |
| Bảng giá nhà máy | Người hồ sơ | Chị Ngân |
| Phiếu duyệt giá từng đơn | Hương | Chị Ngân |
| Giá vốn thật gửi Kế toán | Hương | Anh Huỳnh |
| Công thức hàng pha, bao bì, thành phẩm | Oanh / Ly / người hồ sơ | Chị Ngân |
| Mã hàng mới | Người khai | Chị Ngân duyệt qua Zalo |
| Phiếu kho | Các điều phối | Chị Ngân (sau này Trưởng nhóm Điều phối) |
| Biên bản đối chiếu tồn, công nợ | Người hồ sơ | Chị Ngân |
| Phương án, chi phí sự cố | Bảo Thi | Anh Huỳnh, vướng thì chị Ngân |
| Quyết toán Grab | Oanh | Chị Ngân |
| **Biên bản giao nhận, biên bản hàng lỗi** | **chưa rõ** | **chưa rõ** (đây là loại hay sai công ty) |

> **Nhận xét của em:** chị Ngân đang ký **gần hết**. Khi có Trưởng nhóm Điều phối, nên chuyển bớt phiếu kho và công thức sang người đó.

---

## Phần C. Em đánh giá chung

1. **Logic của phòng hợp lý:** kiểm kỹ trước khi gửi, đôn đốc trong lúc làm, kiểm kỹ sau khi xong, khép sổ tiền cuối tháng. Vấn đề không nằm ở cách nghĩ.
2. **Vấn đề nằm ở 3 chỗ:**
   - **Không có hạn chót**: bảy người kiểm đơn, giá vốn, sự cố, Thiết kế, Kế toán đều không có.
   - **Dồn vào một người**: chị Ngân duyệt và ký gần hết; mỗi việc chỉ một người biết.
   - **Giấy tờ với nhà máy**: nhiều công ty nội bộ, hai bộ số liệu, nhà máy không chịu ký.
3. **Tệp bàn giao:** viết khá kỹ, nhưng thiếu thời gian, thiếu người duyệt ở vài chỗ, còn 3 mục chưa viết (ngưng hợp tác, sơ đồ và mô tả công việc, ai ký gì). Người mới theo tệp **làm được khoảng 60–70%**.
4. **Thứ tự em đề xuất cho ERP:**
   1. Mã hàng + hồ sơ nhà máy (nền).
   2. Đơn gia công có bảy người kiểm song song, có hạn và tự nhắc.
   3. Sổ sự cố.
   4. Tồn kho nguyên liệu, bao bì tại từng nhà máy.
   5. Tiền, thuế, sau khi đã có chính sách riêng với từng nhà máy.
