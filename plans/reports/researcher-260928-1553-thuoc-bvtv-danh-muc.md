# Cào danh mục thuốc BVTV — danhmuc.thuocbvtv.com (28/09/2026)

## Nguồn & cách lấy
- Trang PHP render sẵn HTML (LiteSpeed), không cần đăng nhập, không có điều khoản cấm cào. Nguồn gốc dữ liệu (theo chân trang): EcoFarm của Cục BVTV, Thông tư 75/2025/TT-BNNMT.
- robots.txt: `Allow: /`, chỉ cấm `/api/`, `/thuoc/search`, `/crawler/` → **không dùng** mấy đường này. Không có nút xuất Excel.
- Danh sách: trang chủ `/?trang=1..139` (50 dòng/trang). Sitemap `sitemap-thuoc.xml?page=1..7` = tập URL thứ hai để đối chiếu.
- Chi tiết: `/thuoc/detail/<id>/<slug>` — parse HTML + JSON-LD.
- Tốc độ: 3 req/s, 3 luồng, retry + backoff (429/5xx/rớt kết nối), checkpoint JSONL. Hết ~40 phút; vài lần server ngắt kết nối, retry đều qua.

## Đối chiếu số lượng
| Nguồn | Số |
|---|---|
| Trang báo ("6,919 Sản Phẩm") | 6919 |
| Dòng danh sách (139 trang) | 6919 (id không trùng) |
| URL trong sitemap | 6919 |
| Đã lấy chi tiết | **6919**, lỗi **0** |
| Dòng phạm vi sử dụng (cây trồng–dịch hại) | 15 309 |

Kiểm lại ngẫu nhiên 3 bản ghi với trang thật (id 1484 Sunner 40WP, 4490 Padnia 60WG, 3222 Fenapyr 150WP): khớp 100% mọi trường.

## Trường (thuoc-bvtv.json)
`id, slug, url, ten_thuoc, phan_nhom, linh_vuc, tinh_trang, cong_ty_dang_ky, cong_ty_url, hoat_chat, ham_luong, hoat_chat_danh_sach, quan_ly_tinh_khang{nhom[{ma[], loai}], hoat_chat[{ten, ma (FRAC/IRAC/HRAC), nhom, phuong_thuc, cung_nhom[]}]}, so_dang_ky, thoi_han_dang_ky (thô), ngay_cap, ngay_het_han (ISO), nhom_doc[{he: GHS/WHO, nhom, mo_ta}], tom_tat_su_dung, pham_vi_su_dung[{cay_trong, dich_hai, lieu_luong, thoi_gian_cach_ly, cach_dung}], nguon_ecofarm, thong_tin_khac{}`
- `thong_tin_khac` = hốt mọi nhãn lạ nếu có; thực tế rỗng ở cả 6919 → trang không còn trường nào ngoài bộ trên.
- Không lấy: khối "Sản phẩm cùng công ty / cùng hoạt chất" (dẫn xuất được), widget shop affiliate.
- Trang chi tiết **không có** "dạng thuốc" riêng — hậu tố tên (EC, WP, SC…) chính là dạng thuốc.

## Tệp xuất
Thư mục `/Users/tmduoc/working/comapy/dego-holding/procurement-tool/plans/260928-1553-thuoc-bvtv-danh-muc/`
- `scrape-thuoc-bvtv.py` — script (`--rps`, `--workers`, `--export-only`)
- `thuoc-bvtv.json` (18 MB, lồng nhau)
- `thuoc-bvtv.csv` (utf-8-sig, 6919 dòng; trường lồng gộp chuỗi, phạm vi nối bằng ` || `)
- `thuoc-bvtv.xlsx` — sheet `Danh sach thuoc` (6919) + `Pham vi su dung` (15 309 dòng phẳng, kèm id/tên/số ĐK)
- `checkpoint/` (list.json, sitemap.json, details.jsonl, errors.json = `{}`), `run.log`

## Thống kê nhanh
- Tình trạng: Còn hiệu lực 4860 · Hết hiệu lực 1877 · Đang sử dụng 182.
- Phân nhóm: trừ sâu 2794 · trừ bệnh 2383 · trừ cỏ 1093 · điều hòa sinh trưởng 288 · trừ ốc 201 · trừ chuột 82 · trừ mối 30 · xử lý hạt giống 12 · bảo quản lâm sản 11 · dẫn dụ côn trùng 10 · khử trùng kho 10 · chất hỗ trợ 5.

## Bản ghi thiếu dữ liệu (do NGUỒN, không phải lỗi cào)
- 84 thuốc (đều "Đang sử dụng") trang chi tiết chỉ có tên + nhóm + công ty: không hoạt chất, không số ĐK, không phạm vi (vd id 440 Abatimec 3.6EC). Đã mở trang thật xác nhận.
- 182 thuốc không có thời hạn đăng ký (đúng bằng số "Đang sử dụng"); 1 bản có thời hạn nhưng không tách được ngày (`ngay_cap` trống 183).
- 107 thiếu hàm lượng, 110 thiếu nhóm độc.
- 42 dòng: hoạt chất ở danh sách bị cắt "…", bản chi tiết đầy đủ → dùng bản chi tiết.
- Nguồn tự viết hoa lỗi: `loai` nhóm kháng ra "THUốC TRừ SâU" — giữ nguyên thô.

## Câu hỏi còn treo
- Có cần gộp/lọc chỉ thuốc "Còn hiệu lực" không, hay giữ cả thuốc hết hiệu lực (1877)?
- 84 thuốc "Đang sử dụng" thiếu dữ liệu: có cần bù từ EcoFarm (link `nguon_ecofarm` là redirect sang site khác, chưa đi theo) hoặc từ PDF Thông tư 75/2025 không?
- `__pycache__/` còn sót trong thư mục xuất (hook chặn xóa) — xóa tay nếu muốn.
