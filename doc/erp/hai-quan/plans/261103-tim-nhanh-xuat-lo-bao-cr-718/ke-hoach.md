# KẾ HOẠCH — TRA CỨU THỊ TRƯỜNG: TÌM NHANH + XUẤT TOÀN BỘ CHẠY NỀN (bao-CR-718)

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 03/11/2026 |
| Người phụ trách | Agent 4 (A1 Điều phối giao, người chủ chốt) |
| Trạng thái | Xong trên erp-v2 / dev — chờ soát trên dev và người chủ gật lên prod |
| CR liên quan | bao-CR-718 |

## 1. Việc

1. Tìm kiếm chậm: đo trước, tìm câu chậm thật, sửa theo bằng chứng, ghi số trước / sau.
2. Xuất toàn bộ (hoặc theo bộ lọc) chạy NỀN, chia nhiều tệp, đọc theo khối, nghỉ giữa khối; báo dự kiến số tệp +
   tiến độ; xong thì chuông, bấm chuông ra màn tải từng tệp; mỗi người một lô; tệp giữ N ngày rồi dọn.
3. Giữ quyền `customs_price.export` và nhật ký xuất `tab_export_log`. Giao diện v2 trước.

## 2. Cách đo

Không đọc prod. Dựng MySQL 8.4 riêng (cùng bản prod), nạp bảng hải quan của máy local (18.243 dòng) rồi nhân 18 lần trải
2020–2026 → **328.374 dòng, 166 MB dữ liệu + 134 MB chỉ mục** (prod 03/11: 328.495 dòng, 182 + 123 MB). Bộ đệm InnoDB
512 MB. Script đo: [`do-toc-do.py`](do-toc-do.py) — gọi thẳng hàm service, trung vị 3 lần sau 1 lần làm nóng, trang 50 dòng.

## 3. Số đo TRƯỚC (erp-v2 ec34d668)

## truoc — 328374 dòng
| Kịch bản | đếm total (ms) | trang 1 (ms) | trang 100 (ms) | list_lines (ms) |
|---|---|---|---|---|
| mo-man (khong loc) | 32 | 352 | 525 | 387 |
| q=abamectin | 687 | 856 | 1004 | 1533 |
| q=abamectin 3.6 -TC | 714 | 880 | 908 | 1573 |
| q=glyphosate + 2025 | 118 | 144 | 147 | 250 |
| hs=3808 | 64 | 394 | 793 | 450 |
| importer top | 2 | 4 | 17 | 9 |
| nam 2025 | 21 | 64 | 85 | 89 |
| kind=2 | 10 | 180 | 243 | 188 |
| q=xyzkhongco | 659 | 841 | 823 | 1471 |

| Đường mở màn | ms |
|---|---|
| /coverage | 114 |
| /options | 1149 |
| /parties q=cong | 6 |
| /alerts q=abamectin | 10 |
| /stats q=abamectin | 765 |
| /importers q=abamectin | 772 |

`EXPLAIN ANALYZE` cho thấy:
- trang 1 không lọc = *covering index scan* cả bảng rồi *Sort* 328 nghìn dòng (không có chỉ mục `reg_date`);
- có từ khóa = *Table scan* (95 ms) + *Filter* `lower(product_name) like lower('%…%')` (thêm ~580 ms), và chạy HAI lần
  (đếm + lấy trang).

## 4. Nguyên nhân và cách sửa

| # | Nguyên nhân | Sửa | Vì sao không làm cách khác |
|---|---|---|---|
| 1 | Sắp `reg_date DESC, id DESC` không có chỉ mục → quét + sắp cả bảng mỗi trang | Chỉ mục `ix_customs_line_date (reg_date)` (InnoDB tự kèm khóa chính `(id, reg_date)`) — đi ngược chỉ mục, dừng khi đủ trang. Thêm ~10 MB, dựng 1,3 giây | — |
| 2 | Từ khóa = `LIKE '%…%'` trên tên hàng dài trung bình 187 ký tự (~61 MB chữ); B-tree không giúp được | (a) bỏ `LOWER()` trên MySQL — collation `utf8mb4_unicode_ci` đã không phân biệt hoa thường (−20%); (b) trang 1 dùng chỉ mục #1 nên chỉ dò tới khi đủ 50 dòng; (c) số đếm qua đệm Redis theo bộ lọc → lật trang không đếm lại; (d) tổng = 0 thì không dò trang | **FULLTEXT không đặt được**: bảng chia phân vùng theo năm, MySQL báo *The used table type doesn't support FULLTEXT indexes*. Bỏ phân vùng hoặc dựng bảng tìm kiếm phụ đồng bộ ở mọi đường ghi (nạp, sửa, xóa, gộp, hoàn tác, gắn nhãn) là rủi ro lớn hơn lợi ích lúc này. So nhị phân (`utf8mb4_bin`) vẫn 330 ms — chỗ chậm là lượng chữ phải dò, không phải cách so |
| 3 | `/options` bảy câu GROUP BY cả bảng mỗi lần mở màn (1,1 giây) | Đệm Redis | Thêm chỉ mục cho bảy cột là phình dung lượng cho một ô chọn |

Đệm: khóa = `MAX(id)` + bộ lọc (lô nạp mới tự đổi khóa), hạn 5 phút; xóa hẳn sau gộp dòng trùng, sửa / xóa tay, hoàn tác
lô (các thao tác bớt dòng mà `MAX(id)` không đổi). Chỉ bật trên MySQL; Redis chết thì tính thẳng.

## 5. Số đo SAU

## sau — 328374 dòng
| Kịch bản | đếm total (ms) | trang 1 (ms) | trang 100 (ms) | list_lines lần đầu (ms) | list_lines lật trang (ms) |
|---|---|---|---|---|---|
| mo-man (khong loc) | 26 | 4 | 11 | 40 | 9 |
| q=abamectin | 479 | 15 | 781 | 512 | 31 |
| q=abamectin 3.6 -TC | 506 | 54 | 920 | 558 | 83 |
| q=glyphosate + 2025 | 80 | 149 | 151 | 234 | 153 |
| hs=3808 | 55 | 3 | 13 | 71 | 7 |
| importer top | 1 | 3 | 12 | 9 | 7 |
| nam 2025 | 18 | 3 | 12 | 26 | 7 |
| kind=2 | 9 | 3 | 39 | 17 | 8 |
| q=xyzkhongco | 434 | 856 | 854 | 1263 | 827 |

| Đường mở màn | ms |
|---|---|
| /coverage | 98 |
| /options lần đầu | 1025 |
| /options lần sau | 3 |
| /parties q=cong | 4 |
| /alerts q=abamectin | 8 |
| /stats q=abamectin | 530 |
| /importers q=abamectin | 525 |

*lần đầu* = đệm trống (người đầu tiên gõ từ khóa đó); *lật trang* = đệm đã có. Từ khóa không có dòng nào: lần đầu ~0,45 giây
(chỉ còn câu đếm). Biểu đồ / Doanh nghiệp vẫn dò cả tập lọc (~0,5 giây) — chấp nhận, chỉ chạy khi người dùng mở thẻ đó.

## 6. Xuất toàn bộ chạy nền — thiết kế

- Bảng `tab_customs_export_batch`: người xuất, bộ lọc, trạng thái (SMALLINT + `CustomsExportStatus`), tổng dòng lúc tạo,
  số tệp dự kiến, tệp xong, dòng xong, con trỏ `last_id`, trần `max_id` (ảnh chụp lúc tạo), danh sách tệp, hạn giữ,
  khóa `active_user_id` UNIQUE (mỗi người một lô đang chạy).
- Mỗi tệp `.xlsx` 50.000 dòng (cùng cột với nút xuất cũ — nạp lại được), ghi `write_only` ra đĩa; đọc khối 2.000 dòng
  theo `id` tăng, nghỉ 0,3 giây giữa khối.
- **Mỗi tệp một task Celery**, xong tự hẹn tệp kế sau vài giây → không chiếm worker lâu, việc khác chen được; không cần
  hàng đợi / worker mới.
- Mỗi tệp: lưu kho (R2) + một dòng `tab_export_log`. Xong: chuông trỏ trang chi tiết lô (tải từng tệp).
- Dọn: `customs.cleanup_export_batches` hằng đêm, giữ `customs_export_keep_days` ngày (mặc định 7); lô kẹt quá 2 giờ
  không chạy tiếp thì đánh hỏng, nhả khóa người dùng.

Chạy thử trên bảng 328.374 dòng (`bench_export`): tạo lô 0,2 giây (đếm đã đệm); 7 tệp, mỗi tệp 50.000 dòng ~22 giây
(gồm 7,5 giây nghỉ giữa khối), ~12,8 MB; bộ nhớ tiến trình đứng ~300 MB suốt lô; cả lô ~2,5 phút (+5 giây nghỉ giữa tệp
khi chạy qua Celery). Lọc *abamectin* 5.724 dòng: 1 tệp, 2,8 giây.

## 6b. Giao diện v2

- Nút *Xuất dữ liệu* thẻ Danh sách thành menu: *Xuất ngay (tối đa 50.000 dòng)* (cũ; tắt khi bộ lọc quá trần) · *Xuất toàn
  bộ theo bộ lọc (chạy nền)* (hộp xác nhận nêu bộ lọc, số dòng, số tệp dự kiến, giữ 7 ngày → tạo lô → sang màn lô; 409 thì
  chỉ đường sang *Lô xuất của tôi*) · *Lô xuất của tôi*.
- Màn `/procurement/customs-prices/exports` (lô của mình) và `/exports/:id` (tiến độ, tải từng tệp, dừng lô; hỏi lại 3 giây
  khi lô còn chạy). Gác `customs_price.export`; menu trái không thêm mục (mục ẩn, sáng *Giá thị trường*).
- v1 (`frontend/`) không đổi — A1 chốt 03/11: xuất lô chỉ ở v2; phần tìm nhanh có hiệu lực cả v1 vì chung backend.

## 7. Lên môi trường

Có migration `hqx718` (chỉ mục) và `hqx718b` (bảng lô xuất) → **chỉ lên dev**; prod chờ người chủ gật.
