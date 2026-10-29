# NGHIỆP VỤ MUA HÀNG

| | |
|---|---|
| Phiên bản | **1.1** — 29/10/2026 (thêm mục 10: trả trước, nhập khẩu, cách cân bằng) |
| Người viết | A5 Nghiên cứu nghiệp vụ |
| Trạng thái | Tài liệu nghiên cứu nghiệp vụ chuẩn, chưa phải tài liệu yêu cầu |
| Căn cứ | Cách SAP, Oracle, Odoo, Microsoft Dynamics dựng phân hệ Mua hàng · Chuẩn mực kế toán số 02 · Thông tư 99/2025 (số hiệu tài khoản giữ như Thông tư 200) |
| Cùng cụm | [`10` Nghiệp vụ Kho](./10-nghiep-vu-kho.md) · [`san-xuat/00` Nghiệp vụ Sản xuất](../san-xuat/00-tong-quan-nghiep-vu.md) · [`01` Luồng nối Mua hàng, Kho, Sản xuất](./01-luong-chuan-mua-hang-kho-san-xuat.md) |

Số tiền trong ví dụ là giả định. Thuế suất GTGT lấy 10% cho dễ tính. Chỗ dính quy định thuế cần kế toán xác nhận.

---

## 1. Phân hệ Mua hàng làm gì

Mua hàng lo **toàn bộ việc mua của công ty**, từ lúc có người cần hàng đến lúc trả xong tiền cho nhà cung cấp (NCC). Phân hệ này phục vụ mọi phòng, không riêng Sản xuất.

| Phân hệ | Quan hệ với Mua hàng |
|---|---|
| Sản xuất | Sinh nhu cầu vật tư, đẩy đề xuất mua sang |
| Kho | Nhận hàng theo đơn mua, báo số thực nhận |
| Bán hàng | Sinh nhu cầu mua hàng về bán, hoặc giao thẳng cho khách |
| Kế toán | Nhận hóa đơn, ghi công nợ, chi tiền |

**Ba nguyên tắc:**
1. **Ba người khác nhau:** người mua đặt hàng, thủ kho nhận hàng, kế toán nhập hóa đơn.
2. **Đơn đã duyệt thì khóa.** Muốn đổi thì làm bản sửa đổi có số phiên bản và duyệt lại.
3. **Trả tiền theo hóa đơn đã đối chiếu**, không trả theo đơn mua.

---

## 2. Vai trò

| Vai trò | Làm gì |
|---|---|
| Người cần hàng | Lập yêu cầu mua |
| Trưởng phòng của người cần hàng | Duyệt yêu cầu mua |
| Trưởng Thu mua | Chia việc cho người mua, duyệt phương án chọn NCC |
| Người mua | Hỏi giá, so sánh, lập đơn mua, theo dõi giao hàng, xử lý với NCC |
| Cấp duyệt đơn mua | Duyệt theo hạn mức giá trị |
| Thủ kho, QC | Nhận và kiểm hàng (xem tài liệu Kho) |
| Kế toán phải trả | Nhập hóa đơn, đối chiếu, ghi công nợ |
| Kế toán thanh toán, thủ quỹ | Lập lệnh chi, chi tiền |

---

## 3. Chứng từ và trạng thái

| Chứng từ | Trạng thái |
|---|---|
| **Yêu cầu mua (PR)** | Nháp → Chờ duyệt → Đã duyệt → Đã chuyển báo giá hoặc đơn mua → Đóng · Từ chối · Hủy |
| **Yêu cầu báo giá (RFQ)** | Nháp → Đã gửi → Đã nhận báo giá → Đã chọn → Đóng |
| **Đơn mua (PO)** | Nháp → Chờ duyệt → Đã duyệt → Đã gửi NCC → Nhận một phần → Nhận đủ → Đã có hóa đơn → Đóng · Hủy · Đóng sớm |
| **Hóa đơn NCC** | Nháp → Đang đối chiếu → Treo (lệch) hoặc Đã ghi sổ → Trả một phần → Đã trả |
| **Đề nghị thanh toán** | Nháp → Chờ duyệt → Đã duyệt → Đã chi |

Chứng từ sau luôn **trỏ về** chứng từ trước, để từ một khoản chi lần ngược được về yêu cầu mua ban đầu.

---

## 4. Nhu cầu mua phát sinh từ đâu

| Nguồn | Ví dụ | Loại hàng, tài khoản |
|---|---|---|
| Sản xuất (MRP) | Kế hoạch cần 30,6 tấn, tồn 8, đang về 10, tồn an toàn 5 → mua 17,6 tấn | Nguyên vật liệu, 152 |
| Tồn dưới mức đặt hàng lại | Dùng 2 tấn mỗi ngày × NCC giao 15 ngày + tồn an toàn 10 = đặt khi tồn dưới 40 tấn | 152 hoặc 156 |
| Đơn bán của khách | Mua về bán lại | Hàng hóa, 156 |
| Phòng ban dùng | Văn phòng phẩm, sửa máy, thuê xe | Chi phí 627, 641, 642 |
| Đầu tư | Máy trộn, xe nâng | Tài sản cố định, 211 |
| Hợp đồng khung | Mua lặp lại theo giá đã ký | Theo loại hàng |
| Sự cố, mua gấp | Máy hỏng, thiếu bao bì | Đi đường duyệt nhanh, lập phiếu bổ sung sau |

Loại hàng phải xác định **ngay từ yêu cầu mua**, vì nó quyết định tài khoản ghi sổ về sau.

---

## 5. Luồng chính

### Chặng 1. Yêu cầu mua
- **Người dùng:** chọn mã hàng, số lượng, ngày cần, kho nhận, đối tượng chi phí (phòng ban, dự án, lệnh sản xuất). Gửi duyệt.
- **Hệ thống:** tự chọn luồng duyệt theo phòng ban và giá trị. Nếu có ngân sách thì kiểm còn tiền và tạm giữ.
- Đề xuất do MRP sinh ra ở dạng *Đề xuất*. Người mua xem lại, gộp, rồi mới chuyển thành yêu cầu mua.

### Chặng 2. Hỏi giá và chọn NCC
- **Người dùng:** từ yêu cầu mua, tạo yêu cầu báo giá gửi 2–3 NCC. Nhận về thì nhập giá, thời gian giao, điều kiện thanh toán, cước vận chuyển.
- **Hệ thống:** dựng bảng so sánh gồm tổng tiền thật (cộng cước), có kịp ngày cần không, điểm NCC từ các lần trước (giao trễ, tỷ lệ lỗi).
- **Chọn:** đánh dấu phương án, ghi lý do, trình duyệt. Giá chốt được lưu vào **bảng giá NCC** để lần sau tự điền.

### Chặng 3. Đơn mua
- **Người dùng:** tạo đơn mua từ phương án đã chọn. Bổ sung ngày giao, kho nhận, công ty đứng tên mua, dung sai nhận (ví dụ ±2%), mức đối chiếu (2, 3 hay 4 chiều).
- **Duyệt theo hạn mức** (ví dụ):

| Giá trị đơn | Duyệt |
|---|---|
| Dưới 50 triệu | Trưởng phòng |
| 50 đến 500 triệu | Thêm Giám đốc tài chính |
| Trên 500 triệu | Thêm CEO |

- **Duyệt xong, hệ thống tự làm:**
  1. Khóa giá, số lượng, NCC, điều kiện thanh toán.
  2. Sinh **lệnh chờ nhận hàng** bên Kho. Màn của thủ kho không thấy giá.
  3. Sinh **lịch thanh toán dự kiến** để dự báo dòng tiền.
  4. Gửi đơn cho NCC. NCC xác nhận.
- **Sửa đơn đã duyệt:** tạo phiên bản mới, giữ phiên bản cũ, ghi lý do. Giá trị tăng thì duyệt lại.

### Chặng 4. Theo dõi giao hàng
- Ghi ngày hẹn giao. Hệ thống nhắc đơn sắp đến hạn và đơn đã trễ.
- Nhận hàng, kiểm hàng, trả hàng lỗi: xem tài liệu Kho. Mua hàng nhận lại kết quả để xử lý với NCC.

### Chặng 5. Hóa đơn NCC
- **Hóa đơn sinh ra khi nào:** NCC lập vào **ngày giao hàng** (lúc chuyển quyền sở hữu). Với dịch vụ thì lập khi làm xong. Hóa đơn điện tử gửi về email.
- **Kế toán:** tạo hóa đơn NCC, chọn đơn mua. Hệ thống kéo các dòng đã nhận mà chưa có hóa đơn.
- **Kiểm khi nhận hóa đơn:**
  - Tên, mã số thuế bên mua đúng công ty đứng tên đơn. Thương hiệu khác pháp nhân thì phải xuất cho đúng pháp nhân.
  - Hàng, số lượng, đơn giá khớp đơn mua và số thực nhận.
  - Đúng thuế suất, có mã của cơ quan thuế.
- **Đối chiếu:**

| Mức | So | Dùng cho |
|---|---|---|
| 2 chiều | Đơn mua, hóa đơn | Dịch vụ |
| 3 chiều | Thêm phiếu nhập kho | Hàng hóa |
| 4 chiều | Thêm số đã qua kiểm | Nguyên liệu bắt buộc kiểm |

- Trong dung sai thì ghi sổ, **công nợ tự sinh**, hạn trả = ngày hóa đơn + số ngày công nợ. Vượt dung sai thì **treo** hóa đơn chờ xử lý.

### Chặng 6. Thanh toán
- **Kế toán:** chạy **đề xuất thanh toán**, lọc khoản nợ đến hạn, bỏ khoản đang tranh chấp. Gửi duyệt.
- **Duyệt xong:** xuất lệnh chi gửi ngân hàng. Công nợ giảm, đơn mua đóng.
- Hóa đơn **từ 5 triệu đồng trở lên** phải chuyển khoản mới được khấu trừ thuế GTGT (Luật Thuế GTGT 2024, từ 01/07/2025).

### Chặng 7. Cuối tháng
1. Soát **hàng về chưa có hóa đơn** và **hóa đơn về chưa có hàng**.
2. Đóng sớm các đơn treo lâu ở *Nhận một phần*.
3. Đối chiếu công nợ với từng NCC, ký biên bản.
4. Tính lại chênh lệch tỷ giá cho nợ ngoại tệ.

---

## 6. Hóa đơn và thời điểm ghi nợ

| Tình huống | Cách ghi |
|---|---|
| Hàng và hóa đơn về cùng lúc | Ghi nhập kho và nợ NCC theo hóa đơn |
| Hàng về trước, hóa đơn về sau | Trong tháng thì chờ. Hết tháng chưa có thì ghi theo **giá tạm tính**, có hóa đơn thì điều chỉnh |
| Hóa đơn về trước, hàng chưa về | Ghi **151 hàng mua đang đi đường**. Hàng về thì chuyển sang kho |
| Hóa đơn sai | Không tự sửa. Yêu cầu NCC lập hóa đơn điều chỉnh hoặc thay thế |
| NCC giảm giá sau khi bán | Hóa đơn điều chỉnh giảm, công nợ và giá vốn cùng giảm |

| Loại giấy tờ đầu vào | Khấu trừ thuế GTGT? |
|---|---|
| Hóa đơn GTGT | Có |
| Hóa đơn bán hàng (NCC nộp thuế trực tiếp, hộ kinh doanh) | Không, toàn bộ vào giá vốn hoặc chi phí |
| Tờ khai hải quan và chứng từ nộp thuế (nhập khẩu) | Có, phần thuế GTGT hàng nhập khẩu |

---

## 7. Các khoản chi phí khi mua

Nguyên tắc: **giá vốn gồm mọi chi phí để đưa hàng về tới kho, ở trạng thái dùng được.**

| Khoản | Vào giá vốn? | Tài khoản |
|---|---|---|
| Giá mua chưa thuế | Có | 152, 153, 156, 211 |
| Chiết khấu thương mại, giảm giá trên hóa đơn | Có, làm giảm | Giảm 152, 156 |
| Cước, bốc xếp, bảo hiểm hàng đi đường | Có | 152, 156 (hàng hóa có thể tách 1562) |
| Thuế nhập khẩu, tiêu thụ đặc biệt, bảo vệ môi trường | Có | Có 3333, 3332, 33381 |
| Phí hải quan, nâng hạ, lưu bãi ở cảng | Có | 152, 156 |
| Thuế GTGT được khấu trừ | Không | 1331 (nhập khẩu: Có 33312) |
| Thuế GTGT không được khấu trừ | Có | Cộng vào giá vốn hoặc chi phí |
| Hao hụt trên đường trong mức cho phép | Có | Không ghi riêng |
| Thiếu ngoài mức cho phép | Không | 1381 chờ xử lý |
| Chiết khấu trả sớm | Không | Có 515 |
| Lãi trả chậm | Không | Nợ 635 |
| Chênh lệch tỷ giá khi trả | Không | 515 (lãi), 635 (lỗ) |
| Tiền phạt NCC giao trễ | Không | Có 711 |
| Phí lưu kho sau khi đã nhập kho | Không | 641 hoặc 642 |
| Chi phí của phòng Thu mua | Không | 642 |

**Chi phí mua hàng chung cho nhiều mặt hàng** (ví dụ cước một container): lập phiếu chi phí mua hàng, chia cho từng mã theo một trong năm cách: chia đều, theo số lượng, theo giá trị, theo khối lượng, theo thể tích. Chi phí về muộn khi hàng đã xuất bớt: phần của hàng còn trong kho cộng vào giá tồn, phần đã xuất ghi vào giá vốn của kỳ đó.

---

## 8. Ví dụ có số

**Mua trong nước:** 17 tấn × 15.000.000 đ, VAT 10%.

| Bước | Bút toán | Số tiền |
|---|---|---|
| Ứng trước 30% | Nợ 331 / Có 112 | 84.150.000 |
| Hàng về 16,8 tấn, hóa đơn 17 tấn | Nợ 152: 252.000.000 · Nợ 1381: 3.000.000 · Nợ 1331: 25.500.000 / Có 331: 280.500.000 | |
| Cước xe | Nợ 152: 3.000.000 · Nợ 1331: 300.000 / Có 331 nhà xe: 3.300.000 | |
| NCC giao bù 0,2 tấn | Nợ 152 / Có 1381 | 3.000.000 |
| Trả 0,5 tấn lỗi | Nợ 331: 8.250.000 / Có 152: 7.500.000 · Có 1331: 750.000 | |
| Trả nốt sớm, chiết khấu 1% | Nợ 331: 188.100.000 / Có 515: 1.881.000 · Có 112: 186.219.000 | |

Kết quả: kho có 16,5 tấn, giá trị 250,5 triệu, khoảng **15.181.800 đ/tấn**.

**Nhập khẩu:** 12.000 USD, tỷ giá 25.000.

| Bước | Bút toán | Số tiền |
|---|---|---|
| Hàng về | Nợ 152 / Có 331 | 300.000.000 |
| Thuế nhập khẩu 3% | Nợ 152 / Có 3333 | 9.000.000 |
| Thuế GTGT nhập khẩu 10% × 309 triệu | Nợ 1331 / Có 33312 | 30.900.000 |
| Phí hải quan, nâng hạ, kéo về | Nợ 152: 6.000.000 · Nợ 1331: 600.000 / Có 331 | |
| Trả NCC khi tỷ giá 25.200 | Nợ 331: 300.000.000 · Nợ 635: 2.400.000 / Có 1122: 302.400.000 | |

Kết quả: giá vốn 315 triệu, **15.750.000 đ/tấn**. Lỗ tỷ giá là chi phí tài chính, không vào giá vốn.

---

## 9. Các luồng đặc biệt

| Luồng | Cách làm |
|---|---|
| **Mua dịch vụ** | Đơn mua loại dịch vụ, không qua kho. Bên yêu cầu xác nhận *đã làm xong*. Đối chiếu 2 chiều. Ghi vào chi phí 627, 641, 642 |
| **Hợp đồng khung** | Ký giá và tổng lượng một lần. Mỗi lần cần thì *gọi hàng* sinh đơn mua con. Hệ thống theo dõi phần trăm đã dùng |
| **Gia công ngoài** | Đơn mua dịch vụ gia công, kèm định mức vật tư gửi đi. Vật tư chuyển sang kho tại nhà gia công. Nhận thành phẩm thì tự trừ vật tư theo định mức. Giá thành = vật tư + phí gia công + vận chuyển |
| **Nhập khẩu** | Đơn ngoại tệ, theo dõi lô hàng (vận đơn, ngày tàu). Hàng trên biển ghi 151. Về cảng thì gom cước, thuế, phí vào chi phí mua hàng |
| **Giao thẳng cho khách** | Đơn bán sinh đơn mua, NCC giao thẳng khách. Không qua tồn kho, ghi thẳng giá vốn |
| **Hàng ký gửi** | Hàng của NCC để ở kho mình. Dùng bao nhiêu ghi nợ bấy nhiêu, NCC xuất hóa đơn theo số đã dùng |
| **Tài sản cố định** | Nhận hàng xong tự tạo thẻ tài sản và lịch khấu hao. Nợ 211 / Có 331, hằng tháng Nợ 627 hoặc 642 / Có 214 |
| **Mua lặt vặt** | Tạm ứng (Nợ 141 / Có 111), mua xong nộp hóa đơn quyết toán (Nợ 642 hoặc 152, 1331 / Có 141) |
| **Trả trước, đặt cọc** | Khoản ứng gắn với đơn mua (Nợ 331 / Có 112). Có hóa đơn thì tự trừ vào nợ |
| **Hủy đơn** | Chưa nhận gì thì hủy. Đã nhận một phần thì chỉ đóng sớm. Đã ứng trước thì đòi hoàn hoặc trừ vào đơn sau |

---

## 10. Trả trước và nhập khẩu: các trường hợp và cách cân bằng

### 10.1. Trên app, cân bằng được làm thế nào
1. **Mỗi khoản trả trước là một dòng *Ứng trước*** gắn với đơn mua, có ba cột: đã ứng, đã đối trừ, còn lại.
2. **Khi ghi sổ hóa đơn**, hệ thống tự hiện các khoản ứng trước còn lại của NCC đó và gợi ý trừ.
3. **Màn công nợ NCC** luôn hiện: tổng hóa đơn, tổng ứng trước, tổng đã trả, số dư.
4. **Tài khoản trung gian** (151, tài khoản tạm chờ hóa đơn, 3333, 33312) chỉ là chỗ tiền đi ngang qua. Xong một vòng thì phải về 0. Còn dư là có chỗ sai.

### 10.2. Trả trước 100%, NCC giao thiếu
Đơn 5.000.000 + VAT 500.000 = 5.500.000 đ, trả trước toàn bộ.

| Bước | Trên app | Bút toán | Nợ NCC |
|---|---|---|---|
| Ứng trước | *Đề nghị ứng trước* từ đơn mua, duyệt, chi | Nợ 331 / Có 112: 5.500.000 | Dư Nợ 5.500.000 |
| NCC giao 90%, có hóa đơn | Nhập kho 90%, nhập hóa đơn, hệ thống trừ ứng trước | Nợ 152 4.500.000, Nợ 1331 450.000 / Có 331 4.950.000 | Dư Nợ 550.000 |
| NCC không giao tiếp | *Đóng sớm* đơn. Dòng ứng trước còn 550.000 hiện cảnh báo | | Dư Nợ 550.000 |
| NCC hoàn tiền | *Nhận hoàn tiền ứng trước* | Nợ 112 / Có 331: 550.000 | **0** |

Không hoàn mà muốn giữ lại thì bấm *Chuyển sang đơn* khác. NCC không hoàn, không giao thì chuyển sang phải thu khác để đòi, có quyết định xóa thì ghi 811.

### 10.3. Đặt cọc 30%, giao hai đợt
Đơn 110.000.000 đ có VAT, cọc 33.000.000 đ. Đợt 1 hóa đơn 66 triệu, đợt 2 hóa đơn 44 triệu. Trên đơn mua chọn **cách trừ cọc**:

| | Cách A: trừ hết vào hóa đơn đầu | Cách B: trừ 30% mỗi hóa đơn |
|---|---|---|
| Hóa đơn đợt 1 | Trừ 33 triệu, trả 33 triệu | Trừ 19,8 triệu, trả 46,2 triệu |
| Hóa đơn đợt 2 | Trả 44 triệu | Trừ 13,2 triệu, trả 30,8 triệu |
| Tổng chi | 110 triệu | 110 triệu |

Hai cách đều cân, chỉ khác dòng tiền từng đợt.

### 10.4. Hủy đơn sau khi đã trả trước

| Tình huống | Cách làm |
|---|---|
| Chưa nhận hàng, NCC hoàn đủ | Hủy đơn, nhận hoàn: Nợ 112 / Có 331 |
| Chuyển tiền sang đơn khác | *Chuyển sang đơn* trên dòng ứng trước |
| NCC giữ một phần làm phí hủy | Nợ 112 (phần hoàn), Nợ 811 (phí hủy) / Có 331 |
| Đã nhận một phần | Không hủy được, chỉ đóng sớm, xử lý như 10.2 |

### 10.5. Nhập khẩu trọn vòng
Đơn từ NCC nước ngoài, giá đã gồm cước tàu: K₂SO₄ 15 tấn × 600 USD = 9.000 USD, KNO₃ 5 tấn × 1.000 USD = 5.000 USD, **tổng 14.000 USD**. Trả trước 30% (4.200 USD), 70% (9.800 USD) trả sau khi nhận hàng 30 ngày.

**Quy tắc tỷ giá:** phần đã trả trước ghi giá hàng theo tỷ giá ngày trả trước, phần còn lại theo tỷ giá ngày nhận hàng. Kế toán xác nhận theo hướng dẫn hiện hành.

| # | Việc | Trên app | Bút toán |
|---|---|---|---|
| 1 | Trả trước 4.200 USD, tỷ giá 25.000 | *Đề nghị ứng trước*, chi từ tài khoản ngoại tệ | Nợ 331 / Có 1122: 105.000.000 |
| 2 | Tàu chạy, có bộ chứng từ, tỷ giá 25.100 | Mở **lô hàng nhập khẩu**, nhập vận đơn, *Ghi nhận hàng đi đường*. Giá hàng = 105.000.000 (phần đã ứng) + 9.800 × 25.100 = 245.980.000. Tổng 350.980.000, chia theo giá trị: K₂SO₄ 225.630.000, KNO₃ 125.350.000 | Nợ 151 / Có 331: 350.980.000. Nợ NCC còn dư Có 245.980.000 |
| 3 | Thông quan, tỷ giá hải quan 25.150 | Nhập tờ khai. Thuế nhập khẩu K₂SO₄ 3%: 9.000 × 25.150 × 3% = 6.790.500. Thuế GTGT nhập khẩu: (352.100.000 + 6.790.500) × 10% = 35.889.050 | Nợ 151 / Có 3333: 6.790.500 · Nợ 1331 / Có 33312: 35.889.050 |
| 4 | Nộp thuế | Lệnh chi nộp ngân sách | Nợ 3333, 33312 / Có 112: 42.679.550 |
| 5 | Phí hải quan, nâng hạ, kéo về | **Phiếu chi phí mua hàng** gắn lô hàng, 8.000.000 + VAT, chia theo khối lượng: K₂SO₄ 6.000.000, KNO₃ 2.000.000 | Nợ 151 8.000.000, Nợ 1331 800.000 / Có 331 đại lý 8.800.000 |
| 6 | Hàng về kho đủ | Thủ kho nhận theo lô hàng | Nợ 152 / Có 151: 365.770.500 |
| 7 | Phí lưu container về muộn 3.000.000 + VAT, đã xuất 10/15 tấn K₂SO₄ | Phiếu chi phí mua hàng gắn cùng lô. Hệ thống chia: K₂SO₄ 2.250.000 (1.500.000 phần đã xuất, 750.000 phần còn tồn), KNO₃ 750.000 | Nợ 152 1.500.000, Nợ 621 1.500.000, Nợ 1331 300.000 / Có 331 3.300.000 |
| 8 | Trả 9.800 USD, tỷ giá 25.300 | Đề xuất thanh toán, duyệt, chi | Nợ 331 245.980.000, Nợ 635 1.960.000 / Có 1122 247.940.000 |
| 9 | Trả đại lý và phí cảng | Đề xuất thanh toán | Nợ 331 / Có 112: 8.800.000 và 3.300.000 |

**Giá vốn khi về kho:**

| Mặt hàng | Giá hàng | Thuế nhập khẩu | Phí | Giá vốn | Mỗi tấn |
|---|---:|---:|---:|---:|---:|
| K₂SO₄ | 225.630.000 | 6.790.500 | 6.000.000 | 238.420.500 | 15.894.700 |
| KNO₃ | 125.350.000 | 0 | 2.000.000 | 127.350.000 | 25.470.000 |

**Kiểm cân bằng cuối vòng:**

| Tài khoản | Số dư | Nghĩa |
|---|---:|---|
| 331 NCC nước ngoài | 0 | Đã trả hết |
| 151 Hàng đi đường | 0 | Hàng đã về kho đủ |
| 3333, 33312 | 0 | Đã nộp thuế |
| 331 đại lý, phí cảng | 0 | Đã trả |
| 1331 | 36.989.050 | Đúng, chờ kê khai khấu trừ |
| 635 | 1.960.000 | Lỗ tỷ giá, chi phí tài chính, không vào giá vốn |
| 621 | 1.500.000 | Phần chi phí về muộn đã vào giá thành kỳ này |

### 10.6. Màn soát cân bằng cho kế toán
1. **Ứng trước chưa đối trừ:** khoản đã chi chưa có hóa đơn trừ vào, kèm số ngày treo.
2. **Hàng đi đường:** số dư 151 theo từng lô hàng, treo quá 60 ngày thì cảnh báo.
3. **Hàng về chưa có hóa đơn:** số dư tài khoản tạm theo từng phiếu nhập.
4. **Công nợ ngoại tệ:** số dư theo USD và VNĐ. Cuối kỳ tính lại chênh lệch tỷ giá theo tỷ giá cuối kỳ.

---

## 11. Ranh giới với Kho và Kế toán

- **Mua hàng** sở hữu: yêu cầu mua, yêu cầu báo giá, đơn mua, bảng giá NCC, đánh giá NCC.
- **Kho** sở hữu: phiếu nhập, kết quả kiểm, phiếu trả hàng NCC, tồn kho, giá vốn tồn. Xem [`10`](./10-nghiep-vu-kho.md).
- **Kế toán** sở hữu: hóa đơn NCC, công nợ phải trả, thanh toán, sổ cái.
- Mỗi phân hệ chỉ **đọc** chứng từ của phân hệ khác, không sửa.
