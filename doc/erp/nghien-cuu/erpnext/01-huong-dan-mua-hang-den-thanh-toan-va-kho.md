# ERPNext học nghiệp vụ: từ Yêu cầu mua hàng tới Thanh toán, và nghiệp vụ Kho

Bản 1.0, 31/10/2026. Trang học: https://erpnext.degoholding.vn (dữ liệu thật của ERP DEGO từ 01/08/2026, chỉ để học, thao tác ở đây **không ảnh hưởng ERP thật**).

Tài liệu gồm ba phần:
- **Phần A**: bức tranh chung, ai làm bước nào, mỗi bước ảnh hưởng **kho** và **sổ kế toán** ra sao.
- **Phần B**: bài thực hành một vòng đầy đủ: Yêu cầu vật tư, hỏi giá, đơn mua, duyệt, nhập kho, hóa đơn, yêu cầu thanh toán, chi tiền.
- **Phần C**: nghiệp vụ kho: xuất kho, chuyển kho, kiểm kê, trả hàng nhà cung cấp, nhận thiếu nhiều lần, kiểm chất lượng.

Cuối tài liệu có bảng đối chiếu với ERP DEGO và các lỗi hay gặp.

---

## 0. Chuẩn bị

### 0.1 Tài khoản tập theo vai

Mật khẩu các tài khoản tập: **admin**. Đăng nhập bằng email hoặc tên đăng nhập đều được.

| Tài khoản | Vai | Dùng ở bước |
|---|---|---|
| `nguoi.de.nghi@erpnext.local` | Người đề nghị mua | Lập Yêu cầu vật tư |
| `thu.mua@erpnext.local` | Nhân viên thu mua (Purchase User) | Hỏi giá, nhập báo giá, lập Đơn mua hàng, gửi duyệt |
| `truong.phong@erpnext.local` | Trưởng phòng thu mua (Purchase Manager) | Duyệt / từ chối đơn trên 50 triệu |
| `thu.kho@erpnext.local` | Thủ kho (Stock User + Stock Manager + Quality Manager) | Nhập kho, kiểm chất lượng, xuất / chuyển kho, kiểm kê |
| `ke.toan@erpnext.local` | Kế toán (Accounts User + Accounts Manager) | Hóa đơn mua hàng, Yêu cầu thanh toán, Bút toán thanh toán |
| `Administrator` | Quản trị | Làm được mọi bước, bật tắt cấu hình |

Nhân sự thật cũng đăng nhập được bằng **mã nhân viên** (ví dụ NSU209), mật khẩu ban đầu là chính mã nhân viên, quyền theo vai trò bên ERP.

Mẹo: muốn xem hai vai cùng lúc thì mở thêm một **cửa sổ ẩn danh** (Ctrl+Shift+N) đăng nhập vai thứ hai.

### 0.2 Công ty, kho, hàng, nhà cung cấp dùng trong bài

| Mục | Giá trị dùng trong bài |
|---|---|
| Công ty | **CÔNG TY TNHH DEGO HOLDING** (viết tắt DGH, đang là công ty mặc định) |
| Kho nhận hàng | **Stores - DGH** |
| Kho thứ hai (chuyển kho, kiểm kê) | **KHO B18 - DGH** |
| Mặt hàng | **CPT0234** Chai PET tròn cổ 44 500ml (45g) Trắng, đơn vị Nos (cái) |
| Nhà cung cấp 1 | **CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI BAO BÌ CẨM HÙNG** |
| Nhà cung cấp 2 | **CÔNG TY TNHH BAO BÌ NHỰA PHƯƠNG NAM** |
| Thuế | Mẫu **GTGT đầu vào 10% - DGH** |
| Tiền chi ra | Tài khoản **Tiền gửi ngân hàng - DGH**, hình thức **Chuyển khoản** |

### 0.3 Mẹo giao diện

- Ô **Tìm kiếm** trên cùng (Ctrl+G): gõ tên màn (tiếng Việt hoặc tiếng Anh) rồi Enter.
- Trên mỗi chứng từ đã gửi có nút **Tạo** (Create) để sinh chứng từ kế tiếp, dữ liệu tự chép sang.
- Vòng đời chứng từ: **Nháp** (sửa được) → **Gửi** (Submit: khóa lại, lúc này mới ghi sổ kho và sổ kế toán) → **Hủy** (Cancel: đảo ngược bút toán) → **Sửa đổi** (Amend: tạo bản mới từ bản đã hủy).
- Trên chứng từ đã gửi có nút **Sổ cái** (View → Accounting Ledger) để xem bút toán, và **Sổ kho** (Stock Ledger) để xem biến động kho.
- Nút **Kết nối** (Connections) ở đầu chứng từ cho thấy các chứng từ trước và sau nó.
- Đổi dữ liệu mà màn không đổi: bấm **Ctrl+Shift+R**.

### 0.4 Bộ chứng từ mẫu đã làm sẵn (31/10/2026)

Một vòng đã làm xong đúng như Phần B và C, để mở ra xem từng bước và bút toán (bấm **Sổ cái** trên chứng từ). Ghi chú trên chứng từ có chữ *MẪU HƯỚNG DẪN*. Người học tự làm lại một vòng mới theo tài liệu để tập.

| Bước | Chứng từ mẫu | Bút toán thật trên máy |
|---|---|---|
| B1 Yêu cầu vật tư | **MAT-MR-2026-00323** | Không có |
| B2 Yêu cầu báo giá | **PUR-RFQ-2026-00002** | Không có |
| B3 Báo giá Cẩm Hùng / Phương Nam | **PUR-SQTN-2026-00003** (3.500) / **PUR-SQTN-2026-00004** (3.650) | Không có |
| B4–B5 Đơn mua hàng, thu mua gửi duyệt, trưởng phòng duyệt | **PUR-ORD-2026-00403** (77.000.000) | Không có |
| B6 Biên nhận (nhập kho) | **MAT-PRE-2026-00369** | Nợ Stock In Hand 70.000.000 / Có Stock Received But Not Billed 70.000.000 |
| B7 Hóa đơn mua hàng | **ACC-PINV-2026-00570** (hạn 30/11) | Nợ SRBNB 70.000.000, Nợ Thuế GTGT đầu vào 7.000.000 / Có Creditors 77.000.000 |
| B8 Yêu cầu thanh toán | **ACC-PRQ-2026-00001** | Không có |
| B9 Bút toán thanh toán | **ACC-PAY-2026-00006** (UNC-0001) | Nợ Creditors 77.000.000 / Có Tiền gửi ngân hàng 77.000.000 |
| C2 Xuất kho sản xuất 5.000 chai | **MAT-STE-2026-00005** | Nợ Stock Adjustment 17.500.000 / Có Stock In Hand 17.500.000 |
| C3 Chuyển 2.000 chai sang KHO B18 | **MAT-STE-2026-00006** | Không có (cùng tài khoản kho) |
| C4 Kiểm kê KHO B18 thiếu 10 | **MAT-RECO-2026-00002** | Nợ Stock Adjustment 35.000 / Có Stock In Hand 35.000 |
| C5 Trả 100 chai lỗi | **MAT-PRE-2026-00370** (biên nhận trả) | Nợ SRBNB 350.000 / Có Stock In Hand 350.000 |
| C5 Giấy báo nợ | **ACC-PINV-2026-00571** | Nợ Creditors 385.000 / Có SRBNB 350.000, Có Thuế GTGT đầu vào 35.000 |
| C6 Đơn nhỏ thu mua tự duyệt, nhận đợt 1 | **PUR-ORD-2026-00404** + **MAT-PRE-2026-00371** | Đơn đã nhận 60%; **còn 2.000 chai để người học tự nhận đợt 2** |

Sau giấy báo nợ, vì hóa đơn đã trả đủ, Cẩm Hùng đang **nợ ngược lại** công ty 385.000 (xem Tóm tắt Phải trả).

Chứng từ **thật** đồng bộ từ ERP DEGO để tra đối chiếu (ô tìm theo cột **Mã ERP** dùng được):

| Loại | Mã ERPNext | Mã bên ERP DEGO |
|---|---|---|
| Yêu cầu vật tư | MAT-MR-2026-00322 | PYC29072701 (phiếu gõ nhầm năm 2027, ngày đã kẹp về 30/10) |
| Đơn mua hàng | PUR-ORD-2026-00402 | PO00839 |
| Biên nhận mua hàng | MAT-PRE-2026-00368 | PO00807, nhận 30/10 |
| Hóa đơn mua hàng (công nợ) | ACC-PINV-2026-00536 | Công nợ SVC Chemical khoảng 108 triệu, hạn 27/10 (đã quá hạn) |

Tài khoản tập kế toán `ke.toan@erpnext.local` và quyền Stock Manager của `thu.kho` được thêm ngày 31/10/2026 để đi trọn vòng.

---

## Phần A. Bức tranh chung

### A.1 Chuỗi chứng từ và người làm

```
Người đề nghị     Thu mua                          Trưởng phòng     Thủ kho                  Kế toán
-------------     -------------------------------  ---------------  -----------------------  ------------------------------------------
Yêu cầu vật tư -> Yêu cầu báo giá -> Báo giá NCC -> Duyệt đơn mua ->  Biên nhận mua hàng   ->  Hóa đơn mua hàng -> Yêu cầu thanh toán
                  (so sánh báo giá) -> Đơn mua hàng                   (nhập kho, kiểm CL)       -> Bút toán thanh toán (chi tiền)
```

### A.2 Mỗi bước ảnh hưởng gì

| Bước | Chứng từ ERPNext (tiếng Anh) | Ghi sổ kho? | Ghi sổ kế toán? | Ý nghĩa nghiệp vụ |
|---|---|---|---|---|
| 1 | Yêu cầu vật tư (Material Request) | Không | Không | Bộ phận nói "cần mua gì, bao nhiêu, khi nào" |
| 2 | Yêu cầu báo giá (Request for Quotation) | Không | Không | Thu mua hỏi giá nhiều NCC |
| 3 | Báo giá từ NCC (Supplier Quotation) | Không | Không | Ghi lại giá NCC trả lời, để so sánh |
| 4 | Đơn mua hàng (Purchase Order) | Không | Không | Cam kết mua với NCC, sau khi duyệt mới gửi được |
| 5 | Biên nhận mua hàng (Purchase Receipt) | **Có, tăng tồn** | **Có** | Hàng thực tế về kho, thủ kho xác nhận số nhận |
| 6 | Hóa đơn mua hàng (Purchase Invoice) | Không | **Có** | Ghi nhận khoản phải trả NCC theo hóa đơn, có thuế GTGT |
| 7 | Yêu cầu thanh toán (Payment Request) | Không | Không | Đề nghị chi tiền, chờ duyệt (giống YCTT bên mình) |
| 8 | Bút toán thanh toán (Payment Entry) | Không | **Có** | Tiền thật đi ra, công nợ giảm |

Điểm quan trọng: **chỉ ba chứng từ ghi sổ kế toán** trong chuỗi mua là Biên nhận, Hóa đơn, Thanh toán. Các bước trước chỉ là kế hoạch và cam kết.

### A.3 Tài khoản ERPNext dùng và tài khoản tương ứng theo chế độ kế toán Việt Nam

Hệ thống tài khoản trên site là **chuẩn quốc tế của ERPNext**, chưa phải Thông tư 200. Bảng dưới để đọc bút toán theo thói quen số hiệu Việt Nam.

| Tài khoản ERPNext (công ty DGH) | Tương ứng VAS (TT200) | Ghi chú |
|---|---|---|
| Stock In Hand - DGH | **152** Nguyên vật liệu / **153** Công cụ / **156** Hàng hóa | Giá trị hàng tồn kho (ERPNext gộp một tài khoản, có thể tách theo kho) |
| Stock Received But Not Billed - DGH | Không có tài khoản riêng; gần với **331** ghi theo giá tạm tính | Tài khoản **trung gian**: hàng đã về nhưng chưa có hóa đơn |
| Creditors - DGH | **331** Phải trả người bán | Công nợ nhà cung cấp |
| Thuế GTGT đầu vào được khấu trừ - DGH | **1331** Thuế GTGT được khấu trừ của hàng hóa, dịch vụ | Thuế đầu vào trên hóa đơn |
| Tiền gửi ngân hàng - DGH | **1121** Tiền gửi ngân hàng VND | Tiền chi ra |
| Stock Adjustment - DGH | **621 / 627 / 632 / 1381 / 811** tùy lý do | Chênh lệch kho, xuất dùng, hao hụt |
| Expenses Included In Valuation - DGH | **1562** Chi phí thu mua hàng hóa (hoặc cộng thẳng vào 152) | Cước, thuế nhập khẩu cộng vào giá vốn |
| Cost of Goods Sold - DGH | **632** Giá vốn hàng bán | Khi xuất bán |

Vì sao có tài khoản trung gian *Stock Received But Not Billed*: ERPNext ghi kho **ngay lúc hàng về** (theo biên nhận), nhưng công nợ chỉ chắc chắn **khi có hóa đơn**. Tài khoản trung gian giữ giá trị hàng đã về mà chưa có hóa đơn. Khi hóa đơn vào thì tài khoản này về 0. Số dư còn lại cuối tháng = **hàng về chưa có hóa đơn**, kế toán dùng để đòi hóa đơn NCC.

---

## Phần B. Bài thực hành: một vòng mua đầy đủ

Tình huống: Xưởng cần **20.000 chai PET 500ml** cho đợt chiết rót tháng 11. Giá dự kiến 3.500 đ/chai. Tổng 70 triệu, **trên 50 triệu nên phải qua trưởng phòng duyệt**.

### Bước 1. Lập Yêu cầu vật tư (người đề nghị)

**Nghiệp vụ:** bộ phận sử dụng nói rõ cần mua gì, bao nhiêu, cần lúc nào, nhận ở kho nào. Đây là căn cứ để thu mua bắt đầu, chưa có giá, chưa có NCC.

**Thao tác** (đăng nhập `nguoi.de.nghi`):
1. Tìm **Yêu cầu vật tư** (Material Request) → **+ Thêm**.
2. **Mục đích**: *Mua hàng* (Purchase). **Công ty**: DEGO HOLDING.
3. **Ngày cần**: chọn một ngày tuần sau.
4. Bảng mặt hàng: **Mã hàng** CPT0234, **Số lượng** 20.000, **Kho** Stores - DGH.
5. **Lưu** → **Gửi**.

**Kết quả cần thấy:** trạng thái *Đang chờ* (Pending). Thu mua sẽ thấy phiếu này.

**Sổ kế toán:** không có bút toán.

### Bước 2. Hỏi giá nhà cung cấp (thu mua)

**Nghiệp vụ:** gửi cùng một yêu cầu hỏi giá cho nhiều NCC để so sánh công bằng.

**Thao tác** (đăng nhập `thu.mua`):
1. Mở Yêu cầu vật tư ở bước 1 → **Tạo** → **Yêu cầu báo giá** (Request for Quotation).
2. Bảng **Nhà cung cấp**: thêm hai dòng: *Bao bì Cẩm Hùng* và *Bao bì nhựa Phương Nam*.
3. **Lưu** → **Gửi**. (Site chưa có hộp thư nên không gửi email thật; bước này chỉ lưu phiếu.)

### Bước 3. Nhập báo giá và so sánh (thu mua)

**Nghiệp vụ:** NCC trả lời giá, thu mua nhập lại để so sánh theo giá, thời gian giao, điều kiện.

**Thao tác:**
1. Mở Yêu cầu báo giá → **Tạo** → **Báo giá từ nhà cung cấp** (Supplier Quotation) → chọn *Cẩm Hùng*. Nhập **Đơn giá** 3.500. Thêm thuế **GTGT đầu vào 10% - DGH**. **Lưu** → **Gửi**.
2. Làm lại cho *Phương Nam* với đơn giá 3.650. **Lưu** → **Gửi**.
3. Mở báo cáo **So sánh báo giá từ nhà cung cấp** (Supplier Quotation Comparison), lọc theo mặt hàng CPT0234: thấy hai giá đặt cạnh nhau.

**Chọn:** Cẩm Hùng rẻ hơn, chọn Cẩm Hùng.

### Bước 4. Lập Đơn mua hàng và gửi duyệt (thu mua)

**Nghiệp vụ:** đơn mua là cam kết với NCC: số lượng, giá, thuế, ngày giao, kho nhận. Đơn lớn phải có người duyệt trước khi gửi NCC.

**Thao tác:**
1. Mở Báo giá của Cẩm Hùng → **Tạo** → **Đơn mua hàng**.
2. Kiểm tra: **Ngày giao** (Required By), **Kho** Stores - DGH, **Mẫu thuế** GTGT đầu vào 10% - DGH.
3. Tổng phải là **77.000.000** (70.000.000 + thuế 7.000.000).
4. **Lưu**. Góc trên có nút **Hành động** (Actions) → **Gửi duyệt** (vì trên 50 triệu, không có nút *Duyệt luôn*).

**Kết quả:** trạng thái *Chờ duyệt*.

### Bước 5. Duyệt đơn (trưởng phòng)

**Thao tác** (đăng nhập `truong.phong`):
1. Tìm **Đơn mua hàng**, lọc **Trạng thái quy trình** = *Chờ duyệt*.
2. Mở đơn → **Hành động** → **Duyệt** (hoặc **Từ chối**, khi đó thu mua sửa rồi *Gửi lại*).

**Kết quả:** trạng thái *Đã duyệt*, đơn được gửi, trạng thái giao nhận *Chờ nhận hàng*.

**Sổ kế toán:** vẫn chưa có bút toán. Đơn mua chỉ là cam kết.

Thử thêm: lập một đơn nhỏ (ví dụ 5.000 chai = 17,5 triệu), sẽ thấy nút **Duyệt luôn** cho thu mua tự duyệt.

### Bước 6. Nhận hàng, nhập kho (thủ kho)

**Nghiệp vụ:** hàng về, thủ kho đếm và xác nhận số thực nhận vào kho nào. Từ lúc này hàng mới thuộc tồn kho.

**Thao tác** (đăng nhập `thu.kho`):
1. Mở Đơn mua hàng đã duyệt → **Tạo** → **Biên nhận mua hàng** (Purchase Receipt).
2. Kiểm tra cột **Số lượng chấp nhận** (Accepted Qty) = 20.000, **Kho chấp nhận** = Stores - DGH.
3. **Lưu** → **Gửi**.

**Kết quả:** tồn kho CPT0234 tại Stores - DGH tăng 20.000. Đơn mua chuyển *Chờ lập hóa đơn*.

**Bút toán** (bấm **Sổ cái** trên biên nhận):

| | Tài khoản | Nợ | Có | VAS tương ứng |
|---|---|---|---|---|
| | Stock In Hand - DGH | 70.000.000 | | Nợ 152 |
| | Stock Received But Not Billed - DGH | | 70.000.000 | Có 331 (tạm tính) |

Thuế GTGT **chưa** ghi ở bước này, vì thuế chỉ được khấu trừ khi có hóa đơn.

### Bước 7. Nhập hóa đơn NCC (kế toán)

**Nghiệp vụ:** NCC gửi hóa đơn GTGT. Kế toán nhập hóa đơn, đối chiếu ba chiều: **đơn mua** (giá, số lượng đặt) với **biên nhận** (số thực nhận) với **hóa đơn** (số tiền NCC đòi). Lệch thì không được ghi.

**Thao tác** (đăng nhập `ke.toan`):
1. Mở Biên nhận mua hàng → **Tạo** → **Hóa đơn mua hàng** (Purchase Invoice).
2. Ô **Số hóa đơn NCC** (Supplier Invoice No): ví dụ *0001234*; **Ngày hóa đơn NCC**: hôm nay.
3. **Ngày đến hạn** (Due Date): ví dụ 30 ngày sau. Ngày này quyết định **tuổi nợ**.
4. Kiểm tra tổng **77.000.000**. **Lưu** → **Gửi**.

**Kết quả:** khoản nợ Cẩm Hùng 77 triệu xuất hiện ở báo cáo **Phải trả Tài khoản**.

**Bút toán:**

| | Tài khoản | Nợ | Có | VAS tương ứng |
|---|---|---|---|---|
| | Stock Received But Not Billed - DGH | 70.000.000 | | (xóa số tạm tính) |
| | Thuế GTGT đầu vào được khấu trừ - DGH | 7.000.000 | | Nợ 1331 |
| | Creditors - DGH | | 77.000.000 | Có 331 |

Gộp bước 6 và 7 lại thì đúng bút toán quen thuộc theo VAS: **Nợ 152: 70tr, Nợ 1331: 7tr / Có 331: 77tr.**

### Bước 8. Lập Yêu cầu thanh toán (kế toán hoặc thu mua)

**Nghiệp vụ:** đến hạn, lập đề nghị chi tiền gửi người có thẩm quyền duyệt. Chưa có tiền đi ra.

**Thao tác** (đăng nhập `ke.toan`):
1. Mở Hóa đơn mua hàng → **Tạo** → **Yêu cầu thanh toán** (Payment Request).
2. Số tiền tự điền 77.000.000 (có thể sửa để trả một phần).
3. **Lưu** → **Gửi**.

**Sổ kế toán:** không có bút toán.

### Bước 9. Chi tiền (kế toán)

**Nghiệp vụ:** chuyển khoản cho NCC, ghi giảm công nợ và giảm tiền ngân hàng.

**Cách 1, từ Yêu cầu thanh toán:**
1. Mở Yêu cầu thanh toán → **Tạo** → **Bút toán thanh toán** (Payment Entry).
2. **Tài khoản thanh toán từ**: Tiền gửi ngân hàng - DGH. Điền **Số Séc/Tham chiếu** (số UNC, ví dụ UNC-0001) và **Ngày tham chiếu**.
3. **Lưu** → **Gửi**.

**Cách 2, trả gộp nhiều hóa đơn của một NCC:**
1. Tìm **Bút toán thanh toán** → **+ Thêm**. **Loại thanh toán** *Trả* (Pay), **Công ty** DGH, **Loại đối tác** *Nhà cung cấp*, chọn NCC.
2. Nhập **Số tiền đã thanh toán** (gõ số lớn hơn 0 trước, mục **Tham khảo** mới hiện ra).
3. Mục **Tham khảo** → **Lấy hóa đơn chưa thanh toán** → **Lấy**. Giữ các hóa đơn muốn trả, sửa cột **Đã phân bổ** nếu trả một phần.
4. Sửa **Số tiền đã thanh toán** bằng tổng cột Đã phân bổ, điền số UNC, ngày tham chiếu. **Lưu** → **Gửi**.

**Bút toán:**

| | Tài khoản | Nợ | Có | VAS tương ứng |
|---|---|---|---|---|
| | Creditors - DGH | 77.000.000 | | Nợ 331 |
| | Tiền gửi ngân hàng - DGH | | 77.000.000 | Có 1121 |

**Kết quả cần thấy:** hóa đơn chuyển *Đã thanh toán*; nợ Cẩm Hùng trên **Tóm tắt Phải trả** giảm 77 triệu; đơn mua chuyển *Hoàn thành*.

### Bước 10. Kiểm lại cả vòng

- Mở Đơn mua hàng → khung **Kết nối**: thấy Yêu cầu vật tư, Báo giá, Biên nhận, Hóa đơn, Thanh toán nối với nhau.
- Báo cáo **Sổ cái** (General Ledger), lọc **Đối tác** = Cẩm Hùng: thấy đủ bút toán của bước 7 và 9, số dư bằng 0.
- Báo cáo **Bảng cân đối phát sinh** (Trial Balance): tài khoản *Stock Received But Not Billed - DGH* không còn số dư của vòng này.

---

## Phần C. Nghiệp vụ kho

Các phiếu kho nằm ở màn **Bút toán kho** (Stock Entry), chọn **Loại** ở đầu phiếu. Đăng nhập `thu.kho`.

### C.1 Xem tồn kho

- **Số dư kho** (Stock Balance): tồn theo mặt hàng và kho, có số lượng và giá trị.
- **Sổ kho** (Stock Ledger): từng lần nhập, xuất, kèm giá trị và tồn sau mỗi lần.
- **Số lượng tồn dự kiến** (Stock Projected Qty): tồn thực + đang đặt mua − đã giữ cho đơn khác. Thu mua nhìn số này để biết có cần mua nữa không.

Giá trị xuất kho tính theo phương pháp đã cài ở **Cài đặt kho** (Stock Settings) → **Phương pháp định giá** (mặc định ERPNext là FIFO; doanh nghiệp Việt Nam hay dùng **bình quân gia quyền** = *Moving Average*).

### C.2 Xuất kho cho sản xuất (Material Issue)

**Nghiệp vụ:** xưởng lĩnh 5.000 chai để chiết rót. Hàng rời kho, giá trị chuyển thành chi phí.

**Thao tác:**
1. **Bút toán kho** → **+ Thêm** → **Loại**: *Xuất vật tư* (Material Issue).
2. Dòng: CPT0234, số lượng 5.000, **Kho nguồn** Stores - DGH.
3. Ô **Tài khoản chênh lệch** (Difference Account): để mặc định *Stock Adjustment - DGH*, hoặc chọn tài khoản chi phí sản xuất nếu đã tạo.
4. **Lưu** → **Gửi**.

**Bút toán** (giá 3.500 đ/chai):

| Tài khoản | Nợ | Có | VAS tương ứng |
|---|---|---|---|
| Stock Adjustment - DGH | 17.500.000 | | Nợ 621 (chi phí NVL trực tiếp) |
| Stock In Hand - DGH | | 17.500.000 | Có 152 |

### C.3 Chuyển kho (Material Transfer)

**Nghiệp vụ:** đưa 2.000 chai từ kho tổng sang KHO B18.

**Thao tác:**
1. **Bút toán kho** → **Loại**: *Chuyển vật tư* (Material Transfer).
2. Dòng: CPT0234, 2.000, **Kho nguồn** Stores - DGH, **Kho đích** KHO B18 - DGH.
3. **Lưu** → **Gửi**.

**Bút toán:** hai kho cùng dùng tài khoản *Stock In Hand - DGH* nên **không có bút toán sổ cái**, chỉ **sổ kho** đổi (Stores giảm 2.000, B18 tăng 2.000). Nếu muốn mỗi kho một tài khoản (ví dụ kho nhà máy riêng), đặt **Tài khoản** trên màn Kho; khi đó chuyển kho sẽ sinh bút toán Nợ kho đích / Có kho nguồn.

### C.4 Kiểm kê (Stock Reconciliation)

**Nghiệp vụ:** cuối tháng đếm thực tế KHO B18 được 1.990 chai, sổ ghi 2.000, thiếu 10.

**Thao tác:**
1. Tìm **Đối chiếu tồn kho** (Stock Reconciliation) → **+ Thêm**. **Mục đích**: *Đối chiếu tồn kho* (Stock Reconciliation).
2. Dòng: CPT0234, **Kho** KHO B18 - DGH, **Số lượng** 1.990 (số đếm thực tế). Để trống **Đơn giá định giá** để giữ giá hiện tại.
3. **Lưu** → **Gửi**.

**Bút toán:**

| Tài khoản | Nợ | Có | VAS tương ứng |
|---|---|---|---|
| Stock Adjustment - DGH | 35.000 | | Nợ 1381 (tài sản thiếu chờ xử lý) hoặc 632 |
| Stock In Hand - DGH | | 35.000 | Có 152 |

Kiểm kê thừa thì bút toán ngược lại (Nợ kho / Có Stock Adjustment, VAS: Có 3381).

### C.5 Trả hàng cho nhà cung cấp

**Nghiệp vụ:** phát hiện 100 chai lỗi, trả lại Cẩm Hùng. Gồm hai việc: **trả hàng** (giảm kho) và **giảm công nợ** (NCC xuất hóa đơn điều chỉnh giảm hoặc mình lập giấy báo nợ).

**Thao tác:**
1. (Thủ kho) Mở **Biên nhận mua hàng** ở bước 6 → **Tạo** → **Trả hàng** (Return). Số lượng tự hiện số âm, sửa thành **−100**. **Lưu** → **Gửi**.
2. (Kế toán) Mở **Hóa đơn mua hàng** ở bước 7 → **Tạo** → **Trả hàng / Giấy báo nợ** (Return / Debit Note). Sửa số lượng **−100**. **Lưu** → **Gửi**.

**Bút toán:**

| Chứng từ | Tài khoản | Nợ | Có | VAS |
|---|---|---|---|---|
| Biên nhận trả hàng | Stock Received But Not Billed - DGH | 350.000 | | |
| | Stock In Hand - DGH | | 350.000 | Có 152 |
| Giấy báo nợ | Creditors - DGH | 385.000 | | Nợ 331 |
| | Stock Received But Not Billed - DGH | | 350.000 | |
| | Thuế GTGT đầu vào được khấu trừ - DGH | | 35.000 | Có 1331 |

Gộp lại theo VAS: **Nợ 331: 385.000 / Có 152: 350.000 / Có 1331: 35.000.**

Nếu hóa đơn đã trả đủ tiền thì giấy báo nợ làm NCC **nợ ngược lại mình** 385.000. Lần trả tiếp theo cho NCC đó, khoản này được trừ khi bấm *Lấy hóa đơn chưa thanh toán*.

### C.6 Nhận thiếu, nhận nhiều lần

**Nghiệp vụ:** đặt 20.000, đợt 1 về 12.000, đợt 2 về 8.000.

**Thao tác:** từ Đơn mua hàng → **Tạo** → **Biên nhận mua hàng**, sửa số lượng thành 12.000 → Gửi. Đơn mua hiển thị *Đã nhận 60%*. Lần sau lại **Tạo** → **Biên nhận**: ERPNext tự điền phần còn lại 8.000.

Nhận **dư** hơn số đặt bị chặn, trừ khi mặt hàng có **Dung sai nhận dư** (Over Delivery/Receipt Allowance) ở màn Mặt hàng hoặc ở Cài đặt kho. Với dữ liệu thật đồng bộ từ ERP, 128 mặt hàng đã được nới dung sai này vì bên ERP từng nhận dư.

### C.7 Kiểm chất lượng trước khi nhập

**Nghiệp vụ:** nguyên liệu phải đạt kiểm tra mới được nhập kho. Hàng không đạt ghi vào cột *từ chối* và để ở kho riêng.

**Bật cho một mặt hàng:** mở **Mặt hàng** → tab **Chất lượng** (Quality) → tick **Yêu cầu kiểm tra trước khi mua** (Inspection Required before Purchase) → Lưu.

**Thao tác:**
1. Trên Biên nhận mua hàng (nháp), mỗi dòng có ô **Kiểm tra chất lượng** → **Tạo mới**.
2. Phiếu Kiểm tra: kết quả **Chấp nhận** (Accepted) hoặc **Từ chối** (Rejected) → Gửi.
3. Quay lại biên nhận: nhập **Số lượng chấp nhận** và **Số lượng từ chối**, chọn **Kho từ chối** (Rejected Warehouse). Biên nhận chỉ gửi được khi đã có phiếu kiểm tra.

**Bút toán:** chỉ phần **chấp nhận** vào *Stock In Hand*. Phần từ chối nằm ở kho từ chối với giá trị 0 và không tính vào công nợ; sau đó trả NCC theo mục C.5.

### C.8 Tự đề nghị mua khi tồn thấp

**Bật:** **Mặt hàng** → tab **Tồn kho** → bảng **Mức đặt hàng lại** (Reorder Levels): kho, **mức tồn tối thiểu**, **số lượng đặt**. Và **Cài đặt kho** → tick **Tự tạo yêu cầu vật tư** (Auto Material Request).

Mỗi ngày một lần, mặt hàng nào tồn dưới mức sẽ tự sinh **Yêu cầu vật tư** nháp cho thu mua.

---

## D. Báo cáo nên mở sau khi làm

| Báo cáo | Để xem gì |
|---|---|
| Phải trả Tài khoản (Accounts Payable) | Từng hóa đơn còn nợ, chia tuổi nợ 0–30 / 31–60 / 61–90 / trên 90 ngày |
| Tóm tắt Phải trả Tài khoản (Accounts Payable Summary) | Còn nợ theo từng NCC |
| Sổ cái (General Ledger) | Bút toán, lọc theo chứng từ, tài khoản hoặc đối tác |
| Bảng cân đối phát sinh (Trial Balance) | Số dư mọi tài khoản trong kỳ |
| Số dư kho (Stock Balance) | Tồn theo mặt hàng, kho, giá trị |
| Sổ kho (Stock Ledger) | Từng lần nhập, xuất |
| Phân tích mua hàng (Purchase Analytics) / Sổ mua hàng (Purchase Register) | Mua theo NCC, mặt hàng, tháng |
| Đơn mua hàng cần nhận (Purchase Order Items To Be Received) | Đơn đã duyệt chưa nhận đủ hàng |
| Đã nhận chưa có hóa đơn (Received Items To Be Billed) | Hàng đã về mà NCC chưa gửi hóa đơn |

Ở mọi báo cáo, ô **Công ty** ở đầu báo cáo quyết định xem công ty nào. Mặc định là DEGO HOLDING.

---

## E. Đối chiếu với ERP DEGO

| ERPNext | ERP DEGO | Ghi chú |
|---|---|---|
| Yêu cầu vật tư | **Yêu cầu mua hàng (YCMH)** | Bên mình có thêm duyệt trưởng phòng và điều phối |
| Yêu cầu báo giá + Báo giá NCC | **Yêu cầu báo giá (YCBG)**, khảo sát NCC | Bên mình mạnh hơn: phương án, khảo sát thành chứng từ |
| Đơn mua hàng + quy trình duyệt | **Đơn mua hàng (ĐMH)** + luồng duyệt | Tương đương |
| Biên nhận mua hàng | **Dòng giao hàng** trên ĐMH, phiếu nhập sinh ngầm | Bên mình chưa có phiếu nhập do thủ kho lập (TM-GN-3) |
| Kiểm tra chất lượng, số lượng từ chối | Chưa có | TM-GN-1 |
| Hóa đơn mua hàng | **Công nợ** sinh theo giá đơn | Bên mình chưa đối chiếu ba chiều với hóa đơn NCC |
| Yêu cầu thanh toán | **Yêu cầu thanh toán (YCTT)** | Tương đương |
| Bút toán thanh toán | YCTT bước *Đã chi* | Trên prod chưa có YCTT nào tới *Đã chi* nên công nợ chưa giảm |
| Trả hàng + Giấy báo nợ | Chưa có | TM-GN-2 |
| Xuất kho, chuyển kho, kiểm kê | Chỉ có nhập và điều chỉnh tay | TM-GN-4 |
| Sổ cái, bút toán tự động | Không có (ERP mình không làm kế toán) | Phần kế toán nằm ở phần mềm kế toán riêng |

Chi tiết chấm điểm độ phủ: `procurement-tool/doc/erp/nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md` (ERP DEGO đạt khoảng 59%).

---

## F. Lỗi hay gặp

| Thông báo / hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Không thấy mục **Tham khảo** trên Bút toán thanh toán | Số tiền đã thanh toán đang là 0 | Gõ số tiền lớn hơn 0 trước |
| Không có nút **Duyệt luôn** trên đơn | Đơn trên 50 triệu | Bấm **Gửi duyệt**, trưởng phòng duyệt |
| Không thấy nút **Duyệt** | Đang đăng nhập người lập đơn, hoặc không có vai trò Purchase Manager | Đăng nhập `truong.phong` |
| *Over limit* / *vượt quá giới hạn* khi nhận hàng hoặc lập hóa đơn | Nhận hoặc lập hóa đơn nhiều hơn số đặt | Sửa số lượng, hoặc nới dung sai ở màn Mặt hàng |
| Biên nhận không gửi được, đòi Kiểm tra chất lượng | Mặt hàng bật *Yêu cầu kiểm tra trước khi mua* | Tạo phiếu Kiểm tra chất lượng ở từng dòng |
| *Số lượng âm* khi xuất kho | Tồn không đủ ở kho nguồn | Kiểm **Số dư kho**, chọn đúng kho |
| Báo cáo trống | Ô **Công ty** đang chọn công ty khác, hoặc trình duyệt giữ bản cũ | Đổi ô Công ty; bấm Ctrl+Shift+R |
| Bấm **Hủy** chứng từ bị chặn | Có chứng từ sau đang nối vào | Hủy chứng từ sau trước (ví dụ hủy Thanh toán rồi mới hủy Hóa đơn) |
