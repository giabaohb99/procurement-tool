# NGHIỆP VỤ KHO

| | |
|---|---|
| Phiên bản | **1.0** — 29/10/2026 |
| Người viết | A5 Nghiên cứu nghiệp vụ |
| Trạng thái | Tài liệu nghiên cứu nghiệp vụ chuẩn, chưa phải tài liệu yêu cầu |
| Căn cứ | Cách SAP, Oracle, Odoo, Microsoft Dynamics dựng phân hệ Kho · Chuẩn mực kế toán số 02 *Hàng tồn kho* · Thông tư 99/2025 |
| Cùng cụm | [`09` Nghiệp vụ Mua hàng](./09-nghiep-vu-mua-hang.md) · [`san-xuat/00` Nghiệp vụ Sản xuất](../san-xuat/00-tong-quan-nghiep-vu.md) · [`01` Luồng nối Mua hàng, Kho, Sản xuất](./01-luong-chuan-mua-hang-kho-san-xuat.md) |

---

## 1. Phân hệ Kho làm gì

Kho trả lời ba câu: **có bao nhiêu, ở đâu, trị giá bao nhiêu**. Mọi hàng ra vào đều phải qua một phiếu kho.

| Phân hệ | Quan hệ với Kho |
|---|---|
| Mua hàng | Đơn mua sinh lệnh chờ nhận. Kho nhận, kiểm, trả hàng lỗi |
| Sản xuất | Kho cấp vật tư theo lệnh, nhận thành phẩm và vật tư thừa trả lại |
| Bán hàng | Kho xuất hàng giao khách, nhận hàng khách trả |
| Kế toán | Mỗi phiếu kho tự sinh bút toán. Kế toán khóa kỳ, tính giá |

**Ba nguyên tắc:**
1. **Sổ kho chỉ ghi thêm.** Không sửa, không xóa phiếu đã ghi sổ. Sai thì lập phiếu đảo.
2. **Thủ kho xác nhận số thực**, không lấy số trên đơn mua hay đơn bán.
3. **Hàng chưa kiểm hoặc hàng lỗi không được dùng**, dù đang nằm trong kho.

---

## 2. Vai trò

| Vai trò | Làm gì |
|---|---|
| Thủ kho | Nhận, xuất, chuyển, đếm hàng, lập phiếu kho |
| QC | Kiểm hàng nhập, chuyển trạng thái tồn |
| Trưởng kho | Duyệt xuất ngoài định mức, duyệt điều chỉnh kiểm kê |
| Người có nhu cầu | Lập đề nghị xuất (sản xuất, phòng ban) |
| Kế toán kho | Theo dõi giá trị, đối chiếu sổ kho với sổ cái, khóa kỳ |

Thủ kho **không thấy giá** trên màn nhận và xuất hàng. Giá chỉ kế toán và quản lý thấy.

---

## 3. Dữ liệu gốc

| Dữ liệu | Nội dung |
|---|---|
| **Kho** | Mỗi kho thuộc một công ty. Có các kho đặc biệt: chờ kiểm, cách ly, đang chuyển, kho tại nhà gia công, kho hàng ký gửi |
| **Vị trí** | Kho → Khu → Dãy → Kệ → Ô. Doanh nghiệp vừa thường chỉ cần tới Khu |
| **Mã hàng** | Đơn vị tính và quy đổi (bao 50 kg = 50 kg), theo dõi lô hay không, có hạn dùng không |
| **Lô và hạn dùng** | Gắn ngay từ lúc nhập. Dùng để truy xuất và để xuất hàng gần hết hạn trước |
| **Tồn tối thiểu, tối đa** | Mức đặt hàng lại cho từng mã, từng kho |
| **Cách tính giá** | Bình quân, nhập trước xuất trước, hoặc đích danh. Chọn một lần, giữ ổn định |

---

## 4. Trạng thái tồn

| Trạng thái | Nghĩa | Được dùng? |
|---|---|---|
| **Chờ kiểm** | Đã nhận, chưa có kết quả kiểm | Không |
| **Dùng được** | Đã đạt | Có |
| **Cách ly** | Không đạt, chờ xử lý | Không |
| **Đã giữ chỗ** | Đã dành cho một lệnh sản xuất hoặc đơn bán | Chỉ cho lệnh hoặc đơn đó |
| **Đang chuyển** | Đã xuất khỏi kho đi, chưa tới kho đến | Không |

**Tồn khả dụng** = dùng được − đã giữ chỗ. **Tồn dự báo** = khả dụng + hàng đang về − nhu cầu đã biết. Mua hàng nhìn tồn dự báo để quyết đặt thêm.

---

## 5. Các loại phiếu kho

| Phiếu | Tăng / giảm | Trỏ về | Bút toán (đơn giản) |
|---|---|---|---|
| Nhập mua | + | Đơn mua | Nợ 152, 156 / Có 331 hoặc TK tạm chờ hóa đơn |
| Nhập thành phẩm | + | Lệnh sản xuất | Nợ 155 / Có 154 |
| Nhập vật tư thừa từ sản xuất | + | Lệnh sản xuất | Nợ 152 / Có 621 |
| Nhập hàng khách trả | + | Đơn bán | Nợ 155, 156 / Có 632 |
| Xuất cho sản xuất | − | Lệnh sản xuất | Nợ 621 / Có 152 |
| Xuất bán | − | Đơn bán | Nợ 632 / Có 155, 156 |
| Xuất dùng nội bộ | − | Đề nghị xuất | Nợ 627, 641, 642 / Có 152, 153 |
| Xuất trả NCC | − | Phiếu nhập gốc | Nợ 331 / Có 152, 1331 |
| Xuất hủy | − | Biên bản hủy | Nợ 632 hoặc 811 / Có 152, 155 |
| Chuyển kho | − kho đi, + kho đến | Phiếu chuyển | Không có bút toán nếu cùng công ty |
| Chuyển trạng thái | Không đổi tổng | Kết quả kiểm | Không có bút toán |
| Kiểm kê thừa / thiếu | + / − | Biên bản kiểm kê | Nợ 152 / Có 3381 · Nợ 1381 / Có 152 |

Mỗi phiếu có **ngày ghi sổ**. Kỳ đã khóa thì không ghi lùi ngày vào được.

---

## 6. Nhập kho

### Nhập mua
1. Đơn mua duyệt xong thì kho có **lệnh chờ nhận**.
2. Hàng tới: thủ kho chọn đơn, gõ **số thực đếm được**, số lô, hạn dùng, vị trí. Xác nhận thì sinh **phiếu nhập**.
3. Hàng cần kiểm vào trạng thái **chờ kiểm**, miễn kiểm vào thẳng **dùng được**.
4. QC kiểm: phần đạt sang dùng được, phần lỗi sang cách ly.

| Trường hợp | Cách làm |
|---|---|
| Giao nhiều lần | Mỗi chuyến một phiếu nhập. Phần còn thiếu thành đơn dở dang |
| NCC không giao tiếp | Bên Mua hàng đóng sớm đơn, kho bỏ lệnh chờ nhận còn lại |
| Giao vượt trong dung sai | Cho nhận |
| Giao vượt quá dung sai | Chặn, cần người duyệt hoặc trả lại phần dư |
| Giao sai mã | Không nhận vào đơn, lập biên bản |
| Đơn mua chưa duyệt | Chặn, không cho nhập |
| Nhập sai số | Lập phiếu đảo rồi lập phiếu đúng |

### Nhập thành phẩm
- Sản xuất báo hoàn thành. Hàng qua kiểm thành phẩm, đạt thì nhập kho thành phẩm, mang số lô thành phẩm.
- Giá nhập tạm theo giá chuẩn hoặc giá ước tính. Khóa kỳ, tính xong giá thành thì điều chỉnh.

---

## 7. Xuất kho

| Xuất cho | Ai đề nghị | Ai duyệt | Lưu ý |
|---|---|---|---|
| Sản xuất | Kế hoạch sản xuất, theo lệnh | Lệnh đã phát hành là đủ | Số gợi ý theo định mức. Xuất vượt định mức phải có lý do và người duyệt |
| Bán | Bán hàng, theo đơn | Đơn bán đã duyệt | Gợi ý lô gần hết hạn xuất trước |
| Dùng nội bộ | Phòng có nhu cầu | Trưởng phòng | Bắt buộc chọn mục đích chi phí |
| Trả NCC | Mua hàng hoặc QC | Trưởng kho | Trỏ về phiếu nhập gốc để lấy đúng giá |
| Hủy | Kho hoặc QC | Hội đồng | Kèm biên bản |

**Cấp vật tư cho sản xuất có hai cách:**
- **Phiếu xuất theo lệnh** trước khi làm: thấy ngay xuất vượt định mức.
- **Trừ tự động sau khi báo hoàn thành** (backflush): nhanh, nhưng che mất tiêu hao thật. Hao hụt cao hơn định mức thì phải tới kiểm kê mới lộ.

---

## 8. Chuyển kho

| Cách | Khi nào dùng | Hệ thống làm gì |
|---|---|---|
| **Một bước** | Hai kho gần nhau | Trừ kho đi, cộng kho đến cùng lúc |
| **Hai bước** | Chuyển xa, xe chạy nhiều ngày | Kho đi xuất, hàng nằm ở **kho đang chuyển**. Kho đến xác nhận mới cộng. Lệch số thì lộ ngay |
| **Gửi nhà gia công** | Gửi vật tư cho nhà máy khác làm | Chuyển sang **kho tại nhà gia công**. Hàng vẫn của mình. Nhận thành phẩm về thì tự trừ vật tư theo định mức |

Chuyển giữa **hai công ty khác nhau** không phải chuyển kho. Đó là mua bán nội bộ, phải có hóa đơn.

---

## 9. Kiểm kê

1. Lập phiếu kiểm kê: chọn kho, khu, nhóm hàng.
2. Hệ thống **chụp số sổ sách** tại lúc bắt đầu.
3. Khóa xuất nhập khu đang đếm, hoặc ghi lại phát sinh trong lúc đếm.
4. **Đếm mù:** người đếm không thấy số sổ sách.
5. Hệ thống tính chênh lệch. Lệch lớn thì đếm lại.
6. Trưởng kho duyệt biên bản. Hệ thống sinh phiếu điều chỉnh thừa hoặc thiếu.

- **Kiểm kê toàn bộ:** cuối năm, bắt buộc.
- **Kiểm kê xoay vòng:** hàng giá trị cao đếm hằng tháng, hàng vừa hằng quý, hàng thấp nửa năm. Không phải đóng kho cả ngày.
- Thiếu chưa rõ nguyên nhân thì ghi **1381 chờ xử lý**, không ghi thẳng vào chi phí.

---

## 10. Tính giá xuất kho

| Cách | Làm thế nào | Hợp khi |
|---|---|---|
| **Bình quân di động** | Mỗi lần nhập tính lại giá bình quân. Xuất theo giá bình quân lúc xuất | Hàng đồng nhất, nhập nhiều lần. Phổ biến nhất |
| **Bình quân cuối kỳ** | Cuối kỳ mới tính một giá cho cả kỳ | Ít nghiệp vụ, chấp nhận chờ khóa kỳ mới biết giá vốn |
| **Nhập trước xuất trước** | Xuất theo giá lô nhập sớm nhất còn lại | Hàng có hạn dùng, giá biến động mạnh |
| **Đích danh** | Xuất đúng giá của lô cụ thể | Hàng giá trị lớn, theo dõi từng lô |

**Ví dụ bình quân di động:**

| Ngày | Việc | Số lượng | Đơn giá | Tồn | Giá trị tồn | Bình quân |
|---|---|---:|---:|---:|---:|---:|
| 01/10 | Nhập | 1.000 | 50.000 | 1.000 | 50.000.000 | 50.000 |
| 05/10 | Xuất | −400 | 50.000 | 600 | 30.000.000 | 50.000 |
| 10/10 | Nhập | 1.000 | 54.000 | 1.600 | 84.000.000 | 52.500 |
| 15/10 | Xuất | −800 | 52.500 | 800 | 42.000.000 | 52.500 |

Lần xuất đã chốt giá thì không đổi theo khi về sau có điều chỉnh. Chi phí mua hàng về muộn: phần của hàng còn tồn cộng vào giá tồn, phần đã xuất ghi vào giá vốn của kỳ đó.

---

## 11. Bổ sung hàng

```
Mức đặt hàng lại = Dùng mỗi ngày × Số ngày NCC giao + Tồn an toàn
```

- Ví dụ: dùng 2 tấn mỗi ngày, NCC giao sau 15 ngày, tồn an toàn 10 tấn. Đặt khi **tồn dự báo** dưới 40 tấn.
- Hệ thống tự sinh **đề xuất mua** (hoặc đề xuất sản xuất) để kéo tồn lên mức tối đa. Đề xuất chuyển sang Mua hàng.
- Luôn so với tồn dự báo, không so với tồn sổ sách, để không đặt trùng hàng đang về.

---

## 12. Cuối tháng

1. Đối chiếu **giá trị tồn trên sổ kho** với số dư 152, 153, 155, 156 trên sổ cái.
2. Soát hàng **chờ kiểm** và **cách ly** treo lâu, đẩy xử lý.
3. Soát **kho đang chuyển** và **kho tại nhà gia công**, đối chiếu với nhà gia công.
4. Báo cáo **hàng sắp hết hạn** trước 30, 60, 90 ngày, và hàng chậm luân chuyển.
5. Khóa kỳ kho trước khi kế toán khóa sổ.

---

## 13. Ranh giới với các phân hệ khác

- **Kho** sở hữu: phiếu kho, kết quả kiểm, tồn, giá vốn tồn, kiểm kê.
- **Mua hàng** sở hữu đơn mua. Kho chỉ đọc đơn mua để nhận hàng. Xem [`09`](./09-nghiep-vu-mua-hang.md).
- **Sản xuất** sở hữu lệnh sản xuất, định mức. Kho cấp và nhận theo lệnh. Xem [`san-xuat/00`](../san-xuat/00-tong-quan-nghiep-vu.md).
- **Kế toán** sở hữu sổ cái. Phiếu kho tự sinh bút toán, kế toán không gõ tay lại.
