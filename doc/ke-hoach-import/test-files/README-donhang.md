# Test Files - Import Don mua hang

Thu muc nay chua file Excel de kiem thu chuc nang "Import Don mua hang"
(`app/modules/import_tool/po_import.py`).

Script tao file: `tmp_build_po_xlsx.py` (goc du an).
Script verify: `tmp_verify_po_dryrun.py` (goc du an).

---

## Quy uoc cau truc file

- Sheet: "6. TIEN DO MUA HANG"
- Header dong 4, du lieu tu dong 5.
- Dung khi ca cot A (Stt) va J (Ma Misa) deu trong.
- Importer doc theo chu cai cot (openpyxl.utils.column_index_from_string).

## Mapping cot chinh

| Cot | Y nghia |
|-----|---------|
| A   | Stt |
| C   | Ngay yeu cau co hang |
| D   | Ngay du kien nhan |
| E   | Ngay nhan thuc te |
| F   | Bo phan dat |
| G   | Phap ly lay hoa don (Cong ty) |
| H   | NSPT |
| I   | NCC |
| J   | Ma Misa (khoa gom PO) |
| K   | Phan loai |
| L   | Ma VTBB/SP |
| M   | Ten SP |
| O   | Ten tren hoa don |
| P   | Trang thai |
| Q   | NCC co san hang |
| R   | Kho nhan |
| V   | SL yeu cau |
| W   | DVT |
| X   | SL dat NCC |
| Y   | SL da nhan |
| Z   | Don gia |
| AA  | VAT |
| AD  | Ngay dat hang |
| AE  | So hoa don (khoa gom POItem cung Misa+SP) |

---

## FILE: test_donhang.xlsx

1 sheet "6. TIEN DO MUA HANG", 13 dong du lieu (dong 5-17).
Du lieu thu: 9 case A..I, dong 16 la missing_key (J trong).

---

## CASE A - 1 Misa nhieu SP (2 dong hang)

**Misa:** TDMH001 | **NCC:** Cam Hung | **Cty:** DEGO | **Kho:** Agama

| Dong | SP | HD | X | Y | Gia | Trang thai |
|------|----|----|---|---|-----|------------|
| 5 | THC0005 | 5001 | 100 | 100 | "20.600" (text) | Hoan thanh |
| 6 | THC0003 | 5002 | 50 | 48 | "15.000" (text) | Hoan thanh |

**Ky vong:**
- 1 PO, 2 dong hang (THC0005+5001 va THC0003+5002)
- Gia 20.600 parse ra 20600.0 (khong phai 20.6)
- 2 payable, autopay_preview cho 2 khoan no
- Log INFO: po_new TDMH001 + autopay_preview

---

## CASE B - Cung SP khac so HD -> 2 dong hang

**Misa:** TDMH002 | **NCC:** Dong Tay | **SP:** THC0004

| Dong | HD | X | Y | Trang thai |
|------|----|---|---|------------|
| 7 | 6001 | 100 | 100 | Hoan thanh |
| 8 | 6002 | 100 | 108 | Hoan thanh |

**Ky vong:**
- 1 PO, 2 dong hang rieng (cung THC0004 nhung khac so HD)
- autopay_preview cho 2 khoan no

---

## CASE C - Cung SP+HD nhieu lan giao (khac ngay nhan)

**Misa:** TDMH003 | **NCC:** Cam Hung | **SP:** THC0005 | **HD:** 7001

| Dong | E (ngay nhan) | X | Y | Trang thai |
|------|--------------|---|---|------------|
| 9 | 2026-04-05 | 100 | 50 | Hoan thanh |
| 10 | 2026-04-10 | 100 | 60 | Hoan thanh |

**Ky vong:**
- 1 PO, 1 dong hang + 2 lan giao (khac ngay)
- SL nhan tong = 110
- KHONG co log duplicate_line (vi khac ngay nhan)
- autopay_preview cho 2 khoan no (moi lan giao 1 cong no)

---

## CASE D - SL dat (X) lech -> log REVIEW qty_order_mismatch

**Misa:** TDMH004 | **NCC:** Tan Duc | **SP:** THC0003 | **HD:** 8001

| Dong | X | Y | Trang thai |
|------|---|---|------------|
| 11 | 100 | 60 | Dang giao |
| 12 | 120 | 40 | Dang giao |

**Ky vong:**
- Log REVIEW "qty_order_mismatch" row=11, ref=THC0003
- Lay X=100 (dong dau), bo X=120

---

## CASE E - Dang giao, khong auto-pay

**Misa:** TDMH005 | **NCC:** Dong Tay | **SP:** THC0004 | **HD:** 9001 | X=200 Y=150

**Ky vong:**
- PO tao duoc
- Payable sinh tu Y*Z*(1+VAT) nhung KHONG co autopay_preview
- Log INFO po_new TDMH005, khong co autopay_preview

---

## CASE F - SP moi -> log INFO product_created

**Misa:** TDMH006 | **SP:** SPMOI001 (khong co trong danh muc) | **HD:** 9101 | X=10 Y=10 | Hoan thanh

**Ky vong:**
- Log INFO "product_created" ref=SPMOI001
- SP duoc tao toi thieu tu don (ma L, ten M, DVT W, PL K)
- autopay_preview vi Hoan thanh

---

## CASE G - value_unmatched (gia tri khong co trong danh muc)

**Misa:** TDMH007 | **SP:** THC0005 | **HD:** 9201

| Truong | Gia tri trong file | Ky vong |
|--------|-------------------|---------|
| G (Phap ly) | "Phap ly la" | REVIEW: Phap ly khong khop Cong ty -> de trong |
| K (Phan loai) | "Phan loai la" | REVIEW: value_unmatched -> giu text |
| W (DVT) | "DVT la" | REVIEW: value_unmatched -> giu text |
| R (Kho) | "Kho la ZZZ" | REVIEW: value_unmatched -> giu text |

**Ky vong:**
- 4 log REVIEW "value_unmatched" tai dong 15

---

## CASE H - missing_key (co Stt nhung Misa trong)

**Dong 16:** A=12, J=trong (khong co Ma Misa)

**Ky vong:**
- Log ERROR "missing_key" row=16
- Dong bi bo qua (skipped += 1)

---

## CASE I - So VN lon: "1.000.000" -> 1000000

**Misa:** TDMH008 | **NCC:** Cam Hung | **SP:** THC0003 | **HD:** 9301

| Truong | Gia tri text | Ky vong parse |
|--------|-------------|--------------|
| Z (don gia) | "1.000.000" | 1000000.0 |
| X (SL dat) | "2.000" | 2000.0 |
| Y (SL nhan) | "1.800" | 1800.0 |

**Ky vong:**
- Gia parse dung -> payable sinh duoc
- autopay_preview (Hoan thanh)

---

## Ket qua Dry-Run thuc te

Chay ngay 2026-07-20 tren moi truong dev (container procurement-tool-api-1).

```
Sheets: ['6. TIEN DO MUA HANG']
SUMMARY  created=12 updated=0 skipped=1 review=5 warn=0 err=1 total_rows=12

LOGS (21 entries):
  [REVIEW] value_unmatched           6.PO       row= 15  ref=Phan loai la           | Phan loai 'Phan loai la' khong co trong danh muc -- giu text
  [REVIEW] value_unmatched           6.PO       row= 15  ref=DVT la                  | DVT 'DVT la' khong co trong danh muc -- giu text
  [REVIEW] value_unmatched           6.PO       row= 15  ref=Kho la ZZZ              | Kho 'Kho la ZZZ' khong co trong danh muc -- giu text
  [REVIEW] value_unmatched           6.PO       row= 15  ref=Phap ly la              | Phap ly 'Phap ly la' khong khop Cong ty -- de trong
  [ERROR ] missing_key               6.PO       row= 16  ref=                        | Thieu Ma Misa
  [INFO  ] po_new                    6.PO       row=  0  ref=TDMH001  target=PO#####  | Tao don moi PO##### (Misa TDMH001)
  [INFO  ] autopay_preview           6.PO       row=  0  ref=         target=PO#####  | [Chay thu] Se tao YCTT + ghi DA CHI cho 2 khoan no (don PO#####)
  [INFO  ] po_new                    6.PO       row=  0  ref=TDMH002  target=PO#####  | Tao don moi PO##### (Misa TDMH002)
  [INFO  ] autopay_preview           6.PO       row=  0  ref=         target=PO#####  | [Chay thu] Se tao YCTT + ghi DA CHI cho 2 khoan no (don PO#####)
  [INFO  ] po_new                    6.PO       row=  0  ref=TDMH003  target=PO#####  | Tao don moi PO##### (Misa TDMH003)
  [INFO  ] autopay_preview           6.PO       row=  0  ref=         target=PO#####  | [Chay thu] Se tao YCTT + ghi DA CHI cho 2 khoan no (don PO#####)
  [INFO  ] po_new                    6.PO       row=  0  ref=TDMH004  target=PO#####  | Tao don moi PO##### (Misa TDMH004)
  [REVIEW] qty_order_mismatch        6.PO       row= 11  ref=THC0003  target=PO#####  | SL dat lech giua cac lan giao ([100.0, 120.0]) -- lay dong dau, can ra
  [INFO  ] po_new                    6.PO       row=  0  ref=TDMH005  target=PO#####  | Tao don moi PO##### (Misa TDMH005)
  [INFO  ] po_new                    6.PO       row=  0  ref=TDMH006  target=PO#####  | Tao don moi PO##### (Misa TDMH006)
  [INFO  ] product_created           6.PO       row= 14  ref=SPMOI001               | Tao SP toi thieu 'SPMOI001' tu don
  [INFO  ] autopay_preview           6.PO       row=  0  ref=         target=PO#####  | [Chay thu] Se tao YCTT + ghi DA CHI cho 1 khoan no (don PO#####)
  [INFO  ] po_new                    6.PO       row=  0  ref=TDMH007  target=PO#####  | Tao don moi PO##### (Misa TDMH007)
  [INFO  ] autopay_preview           6.PO       row=  0  ref=         target=PO#####  | [Chay thu] Se tao YCTT + ghi DA CHI cho 1 khoan no (don PO#####)
  [INFO  ] po_new                    6.PO       row=  0  ref=TDMH008  target=PO#####  | Tao don moi PO##### (Misa TDMH008)
  [INFO  ] autopay_preview           6.PO       row=  0  ref=         target=PO#####  | [Chay thu] Se tao YCTT + ghi DA CHI cho 1 khoan no (don PO#####)
```

Dry-run rollback: PO trong DB sau khi chay = 0 (khong ghi that).

---

## Bang tong ket PASS/FAIL

| Case | Mo ta ngan | Ket qua |
|------|-----------|---------|
| A | 1 Misa nhieu SP, gia "20.600"->20600, 2 dong hang, autopay 2 khoan | PASS |
| B | Cung SP khac so HD -> 2 dong hang rieng, autopay 2 khoan | PASS |
| C | Cung SP+HD 2 lan giao khac ngay -> 1 dong hang + 2 lan giao | PASS |
| D | SL dat X lech (100 vs 120) -> log REVIEW qty_order_mismatch | PASS |
| E | Trang thai "Dang giao" -> payable nhung KHONG autopay_preview | PASS |
| F | SP moi SPMOI001 -> log INFO product_created | PASS |
| G | Phan loai la + DVT la + Kho la + Phap ly la -> 4x REVIEW value_unmatched | PASS |
| H | Stt co nhung Misa trong -> ERROR missing_key + skip | PASS |
| I | So VN "1.000.000"->1000000, "2.000"->2000, "1.800"->1800 -> parse dung | PASS |

**Tat ca 9 case PASS.**
