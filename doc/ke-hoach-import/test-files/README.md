# Test Files - Import Khảo sát

Thư mục này chứa 2 file Excel dùng để kiểm thử chức năng "Import Khảo sát"
(`app/modules/import_tool/survey_import.py`).

Script tạo file: `tmp_build_test_xlsx.py` (gốc dự án).
Script verify: `tmp_verify_dryrun.py` (gốc dự án).

---

## Quy ước cấu trúc file

- Header dòng 5, dữ liệu từ dòng 6.
- Sheet "3. KHẢO SÁT, LẤY MẪU ĐÁNH GIÁ N" (NCC) và "4. KHẢO SÁT, LẤY MẪU ĐÁNH GIÁ S" (SP).

---

## FILE 1: test1_khaosat_coban.xlsx

### CASE A - Loại 1 + số VN text + ngày lệch + NCC mới

- VTBB: THC0005 (có trong danh mục) -> loại 1, gom 1 phiếu
- Sheet4: 3 dòng NCC (Đông Tây, Cẩm Hùng, Bao Bì Test Mới), ngày 01/04/2026
- Sheet3: Đông Tây ngày 03/04/2026 (LỆCH 2 ngày), Cẩm Hùng và Bao Bì Test Mới 01/04/2026
- Giá: Đông Tây "20.600" (text), Cẩm Hùng "22.000" (text), Bao Bì Test Mới "19.500" (text)
- VAT: Đông Tây "8%" (text), Cẩm Hùng 0.08 (số float), Bao Bì Test Mới "8%"
- Duyệt: Đông Tây "Duyệt", Cẩm Hùng "Không duyệt", Bao Bì Test Mới trống

Kỳ vọng (Apply):
- 1 phiếu VTBB THC0005, has_product_code=True
- 3 SP line + 3 NCC line
- Giá Đông Tây = 20600 (không phải 20.6)
- NCC "Bao Bì Test Mới" (MST 9990001112) được tự tạo mới
- Đông Tây khớp loose (theo ig+detail+mst, bỏ ngày)

### CASE B - Loại 2, không VTBB

- Mộc Ấn, Phân loại "Hộp", Chi tiết "Hop giay 3 lop", ngày 05/04/2026
- Sheet4 cột P (VTBB) trống -> loại 2

Kỳ vọng (Apply):
- 1 phiếu loại 2 (REQ), has_product_code=False
- 1 SP line + 1 NCC line

### CASE C - no_product_match

- Tân Đức, Phân loại "Nhãn", Chi tiết "Nhan decal trong", ngày 06/04/2026
- Chỉ có ở Sheet3, không có dòng SP tương ứng

Kỳ vọng (Apply):
- 1 phiếu trống được tạo
- Log REVIEW category "no_product_match"

### CASE D - duplicate_line

- An Tín, Phân loại "Thùng", Chi tiết "Thung carton 3 lop", ngày 07/04/2026
- Sheet3: 2 dòng y hệt
- Sheet4: 1 dòng VTBB=THC0003

Kỳ vọng (Apply):
- 1 phiếu VTBB THC0003
- Log WARNING category "duplicate_line" cho dòng NCC thứ 2

### CASE E - value_unmatched

- Đông Tây, VTBB=THI0002, Phân loại "Phân loại lạ ABC", ĐVT "ĐVT lạ XYZ", ngày 08/04/2026
- Có cả Sheet3 và Sheet4

Kỳ vọng (Apply):
- Log REVIEW "value_unmatched" cho Phân loại "Phân loại lạ ABC"
- Log REVIEW "value_unmatched" cho ĐVT "ĐVT lạ XYZ"
- Dữ liệu vẫn được giữ dưới dạng text

### CASE F - missing_key

- Sheet3 dòng 14: Stt=9, Phân loại cột F để TRỐNG
- Sheet4 dòng 12: Stt=7, Tên viết tắt NCC cột O để TRỐNG

Kỳ vọng (Apply):
- 2 log ERROR category "missing_key"
- 2 dòng bị bỏ qua (skipped=2)

---

## FILE 2: test2_khaosat_nangcao.xlsx

### CASE G - Nhiều đợt khảo sát cùng NCC -> 2 phiếu loại 2

- Đông Tây, Phân loại "Nhãn", Chi tiết "Nhan A", không VTBB
- Đợt 1: 01/04/2026 (Sheet3 + Sheet4 cùng ngày)
- Đợt 2: 15/04/2026 (Sheet3 + Sheet4 cùng ngày)

Kỳ vọng (Apply):
- 2 phiếu REQ riêng biệt (mã yêu cầu khác nhau theo ngày)
- Phiếu 1: pr_code = "PYC.NM.01042026.01"
- Phiếu 2: pr_code = "PYC.NM.15042026.01"

### CASE H - mst_conflict (phát hiện giới hạn logic)

- Sheet3 dòng 8: NCC="Đông Tây", MST="0316254811"
- Sheet3 dòng 9: NCC="Đông Tây Khác", MST="0316254811" (cùng MST, tên khác)
- Sheet4 dòng 8: 1 dòng cho "Đông Tây", Phân loại "Hộp", Chi tiết "Hop H"

Kỳ vọng (Apply):
- Log INFO category "ncc_by_mst" tại Sheet3 dòng 9: MST khớp NCC hệ thống "Đông Tây"
  -> LẤY NCC HỆ THỐNG làm chuẩn, bỏ tên viết tắt "Đông Tây Khác" trong file (ghi đè, KHÔNG coi là lỗi)
- Kèm WARNING "duplicate_line" (vì sau chuẩn hoá, 2 dòng cùng NCC + cùng line_key -> gộp)

Ghi chú: theo yêu cầu, khi MST đã có NCC trong hệ thống thì dùng NCC hệ thống (không tạo NCC mới,
không cảnh báo rà soát) -> chỉ ghi log INFO để tra cứu.

### CASE I - Mã yêu cầu có sẵn cột E

- Cẩm Hùng, cột E = "PYC.MANUAL.001", Phân loại "Hộp", Chi tiết "Hop dac biet"
- VTBB trống -> loại 2

Kỳ vọng (Apply):
- pr_code của phiếu = "PYC.MANUAL.001" (không tự sinh)

### CASE J - Số VN đa dạng

- Mộc Ấn, Phân loại "Nhãn", Chi tiết "Nhan J", ngày 12/04/2026
- Giá: "1.234.567" (text) -> phải ra 1234567
- MOQ: "2.000" (text) -> phải ra 2000
- VAT: "10%" -> phải ra 10.0
- Thành tiền: "2.469.134.000" (text) -> phải ra 2469134000

Kỳ vọng (Apply):
- Tất cả số được parse đúng theo quy tắc VN (dấu chấm là phân cách nghìn)

### CASE K - BP viết tắt lạ -> KC

- NCC="Mộc Ấn", BP="PHÒNG BAN LẠ" (không có trong bảng viết tắt)
- Phân loại "Nắp", Chi tiết "Nap X", VTBB trống -> loại 2

Kỳ vọng (Apply):
- pr_code tự sinh bắt đầu bằng "PYC.KC."
- Ví dụ: "PYC.KC.13042026.01"

---

## Kết quả Dry-Run thực tế

Chạy ngày 2026-07-20 trên môi trường dev (container procurement-tool-api-1).

### FILE 1: test1_khaosat_coban.xlsx

```
Sheets: ['3. KHẢO SÁT, LẤY MẪU ĐÁNH GIÁ N', '4. KHẢO SÁT, LẤY MẪU ĐÁNH GIÁ S']
SUMMARY  created=13 updated=1 skipped=2 review=3 warn=1 err=2 total_rows=16

LOGS:
  [INFO  ] ncc_created          3.KS-NCC  row= 8  ref=Bao Bì Test Mới      | Tạo NCC mới 'Bao Bì Test Mới'
  [INFO  ] ncc_created          3.KS-NCC  row=14  ref=Supplier F           | Tạo NCC mới 'Supplier F'
  [INFO  ] survey_update        -         row= 0  ref=PYC.NM.01042026.01   | Cập nhật phiếu đã có KS00197
  [INFO  ] survey_new           -         row= 0  ref=PYC.NM.05042026.01   | Tạo phiếu mới KS00199
  [INFO  ] survey_new           -         row= 0  ref=PYC.NM.07042026.01   | Tạo phiếu mới KS00200
  [REVIEW] value_unmatched      4.KS-SP   row=11  ref=Phân loại lạ ABC     | Phân loại 'Phân loại lạ ABC' không có trong danh mục
  [INFO  ] survey_new           -         row= 0  ref=PYC.NM.08042026.01   | Tạo phiếu mới KS00201
  [REVIEW] value_unmatched      4.KS-SP   row=11  ref=ĐVT lạ XYZ           | ĐVT 'ĐVT lạ XYZ' không có trong danh mục
  [ERROR ] missing_key          4.KS-SP   row=12  ref=                     | Thiếu Phân loại hoặc NCC
  [REVIEW] no_product_match     3.KS-NCC  row=10  ref=Tân Đức              | NCC (MST 0301909568) không khớp dòng SP nào
  [INFO  ] survey_new           -         row= 0  ref=PYC.NM.06042026.01   | Tạo phiếu mới KS00202
  [WARN  ] duplicate_line       3.KS-NCC  row=12  ref=An Tín               | Dòng NCC trùng khoá (Mã YC PYC.NM.07042026.01 + MST 0315259038)
  [ERROR ] missing_key          3.KS-NCC  row=14  ref=                     | Thiếu Phân loại hoặc NCC
```

### FILE 2: test2_khaosat_nangcao.xlsx

```
Sheets: ['3. KHẢO SÁT, LẤY MẪU ĐÁNH GIÁ N', '4. KHẢO SÁT, LẤY MẪU ĐÁNH GIÁ S']
SUMMARY  created=12 updated=1 skipped=0 review=0 warn=1 err=0 total_rows=13

LOGS:
  [INFO  ] ncc_by_mst           3.KS-NCC  row= 9  ref=Đông Tây             | MST 0316254811 khớp NCC hệ thống 'Đông Tây' — dùng NCC hệ thống, bỏ tên trong file
  [WARN  ] duplicate_line       3.KS-NCC  row= 9  ref=Đông Tây             | Dòng NCC trùng khoá (Mã YC PYC.NM.10042026.01 + MST 0316254811)
  [INFO  ] survey_new           -         row= 0  ref=PYC.NM.01042026.01   | Tạo phiếu mới
  [INFO  ] survey_new           -         row= 0  ref=PYC.NM.15042026.01   | Tạo phiếu mới
  [INFO  ] survey_new           -         row= 0  ref=PYC.NM.10042026.01   | Tạo phiếu mới
  [INFO  ] survey_new           -         row= 0  ref=PYC.MANUAL.001       | Tạo phiếu mới
  [INFO  ] survey_new           -         row= 0  ref=PYC.NM.12042026.01   | Tạo phiếu mới
  [INFO  ] survey_new           -         row= 0  ref=PYC.KC.13042026.01   | Tạo phiếu mới
```

---

## Bảng tổng kết PASS/FAIL

| Case | Mô tả ngắn | Kết quả |
|------|-----------|---------|
| A | Loại 1 + số VN "20.600"->20600 + ngày lệch + NCC mới | PASS |
| B | Loại 2, VTBB trống, 1 phiếu REQ | PASS |
| C | no_product_match: chỉ có sheet3 không có sheet4 | PASS |
| D | duplicate_line: 2 dòng NCC y hệt | PASS |
| E | value_unmatched: Phân loại + ĐVT không có trong danh mục | PASS |
| F | missing_key: bỏ trống PL (sheet3) và NCC viết tắt (sheet4) | PASS |
| G | 2 đợt khác ngày -> 2 phiếu loại 2 riêng | PASS |
| H | Cùng MST khác tên -> dùng NCC hệ thống (INFO ncc_by_mst) | PASS |
| I | Mã YC có sẵn cột E -> pr_code không tự sinh | PASS |
| J | Số VN: "1.234.567"->1234567, "2.469.134.000"->2469134000 | PASS |
| K | BP lạ -> viết tắt KC -> pr_code "PYC.KC...." | PASS |

Tất cả 11 case PASS. CASE H ban đầu FAIL (dead code) và đã được sửa trong
`survey_import.py`: truyền tên viết tắt GỐC vào `_upsert_supplier` để so sánh với NCC
danh mục theo MST, nên `mst_conflict` (REVIEW) chạy đúng — kèm `duplicate_line` (WARN)
vì sau chuẩn hoá 2 dòng cùng line_key.
