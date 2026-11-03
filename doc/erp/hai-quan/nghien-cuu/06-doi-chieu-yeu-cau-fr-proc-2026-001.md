# Đối chiếu yêu cầu FR-PROC-2026-001 — Tra cứu thị trường

> Nguồn: tệp «YÊU CẦU TÍNH NĂNG TRA CỨU GIÁ HS CODE-NOTE 250926.xlsx» (chị Mi, Trưởng phòng Thu mua,
> lập 22/09/2026, ghi chú 25/09/2026). Đối chiếu với bản đang chạy trên **dev** ngày 28/09/2026
> (`erp-v2` từ bdf164a3 trở đi). Màn hình đã đổi tên từ «Tra cứu giá hải quan» thành **«Tra cứu
> thị trường»** (bao-CR-500). Mọi mục dưới đây có ở **cả bản cũ (v1) lẫn bản mới (v2)**, trừ khi ghi
> rõ khác. Prod chưa có cụm này.
>
> Ký hiệu cột «Kết quả»: **[x] Đạt** · **[~] Một phần** · **[ ] Chưa**.

## 1. Tóm tắt

| Nhóm yêu cầu | Tổng | Đạt | Một phần | Chưa |
|---|---|---|---|---|
| Chức năng F01–F11 (sheet 2) | 11 | 6 | 5 | 0 |
| Trường lọc (sheet 4) | 13 | 13 | 0 | 0 |
| Tiêu chí nghiệm thu (sheet 6) | 7 | 5 | 0 | 2 |
| Phi chức năng (sheet 6) | 5 | 3 | 2 | 0 |
| Đề xuất thêm của đại ca (chat 25–26/09) | 6 | 6 | 0 | 0 |

**Đọc nhanh:** phần lõi (nạp tệp, tìm kiếm, lọc, phân loại, tỷ giá, biểu đồ, phân quyền, lưu bộ
lọc) đã chạy. Phần còn thiếu chủ yếu **chờ mẫu của chị Mi** (Excel theo mẫu công ty, in báo giá /
PDF). Ba chỗ còn thiếu trên thanh lọc đã bù ở bao-CR-503 (28/09). Danh sách việc còn lại ở mục 7.

## 2. Chức năng (sheet 2)

| Mã | Tên | Chị Mi ghi 25/09 | Bản hiện tại | Kết quả |
|---|---|---|---|---|
| F01 | Tải tệp dữ liệu | Log từng dòng (Thêm mới / update / lỗi…); thêm tải về tệp đã nạp | Nạp nhiều tệp .xls/.xlsx một lần, kiểm đủ 32 cột và báo lỗi cụ thể, chạy thử trước khi ghi. Thẻ **Lịch sử nạp**: từng lô có ai nạp, lúc nào, số dòng; mở lô xem **kết quả từng dòng** (Thêm mới / Lỗi / Trùng trong lô); **tải lại tệp gốc**; hoàn tác lô. Không có trạng thái «Cập nhật» vì tệp không có số tờ khai (đại ca chốt 25/09). Loại trùng làm theo cách khác yêu cầu, xem rủi ro R1 ở mục 6 | [x] |
| F02 | Tìm theo tên hàng | Thêm từ đồng nghĩa, người dùng tự khai từ gốc + từ gần giống | Không phân biệt hoa/thường; gõ nhiều từ = phải có ĐỦ (AND); `-từ` = loại trừ (NOT); tự quy đổi nồng độ (3,6% ≡ 3.6EC ≡ 36 G/L ≡ 3.6% W/W); dòng gợi ý dưới ô tìm cho biết đang khớp những gì. Danh mục **Từ đồng nghĩa** ở thẻ Cấu hình | [x] |
| F03 | Lọc theo trường | Done | Lọc kết hợp nhiều trường, hiện tổng số dòng khớp. Chi tiết từng trường ở mục 3 — đủ cả 13 trường từ bao-CR-503 | [x] |
| F04 | Phân loại Thành phẩm / Nguyên liệu | Nút lọc theo nhóm, sửa được nhóm từ khóa | Tự gắn nhãn khi nạp; cột + ô lọc «Phân loại»; danh mục **Từ khóa** ở thẻ Cấu hình, sửa xong bấm «Gắn lại nhãn». Dev: 13.425 thành phẩm / 4.818 nguyên liệu trên 18.243 dòng | [x] |
| F05 | Tỷ giá theo dòng | Done | Cột «Tỷ giá USD» lấy thẳng từ tệp gốc, thêm hai cột **Giá VND**: × 1,07 (thuế NK 7% tạm tính) và × (1 + thuế suất XNK của dòng) | [x] |
| F06 | Xuất Excel theo mẫu | Done (cần xác nhận lại mẫu form) | Xuất đúng các dòng đang lọc (tối đa 50.000), 36 cột. **Chưa** có định dạng mẫu công ty: dòng tiêu đề + số dòng, header tô màu, wrap tên hàng, ngày dd/mm/yyyy, phân cách hàng nghìn, tách sheet theo nhóm hàng — **chờ tệp mẫu chị Mi** | [~] |
| F07 | Lưu bộ lọc | Gợi ý từ khóa đã nhập; hoặc chế độ xem dùng chung, tìm được | Lưu / chọn lại / cập nhật / xóa bộ lọc **riêng từng người** (tối đa 50), v1 và v2 dùng chung kho. **Chưa** có bộ lọc dùng chung (bảng đã có sẵn cờ, chưa có giao diện) và **chưa** có gợi ý từ khóa | [~] |
| F08 | Biểu đồ xu hướng giá | Done | Giá trung bình gia quyền / thấp nhất / cao nhất / khoảng phổ biến theo **tháng, quý, năm**; so sánh nhiều mặt hàng. **Chưa** có kỳ **tuần** (yêu cầu ghi «theo tuần hoặc theo tháng») | [~] |
| F09 | Trang tra cứu giá | Pending (cần xác nhận lại mẫu) | Bảng đủ 32 cột như tệp GTT02, ẩn/hiện cột, lọc như F02–F04, xuất Excel. **Chưa** có in báo giá và xuất PDF — **chờ mẫu in chị Mi** | [~] |
| F10 | Phân quyền | Done | Quyền riêng «Tra cứu thị trường» (xem / nạp / hoàn tác / xuất Excel) và «Danh mục hóa chất»; thiếu quyền thì không vào được màn, không xuất được | [x] |
| F11 | Lịch sử tải tệp & nhật ký | Thêm block lịch sử thao tác cho trang | Lịch sử **nạp tệp** đầy đủ (xem F01). **Chưa** có khối «lịch sử thao tác» trên trang cho các việc khác: xuất Excel, sửa từ khóa / từ đồng nghĩa / hóa chất, gắn lại nhãn. Hệ thống có ghi nhật ký sửa danh mục ở tầng dưới nhưng trang chưa bày ra | [~] |

## 3. Trường lọc (sheet 4)

| # | Trường | Yêu cầu | Bản hiện tại | Kết quả |
|---|---|---|---|---|
| 1 | Tên hàng | Từ khóa AND / NOT, quy đổi nồng độ | Như F02 | [x] |
| 2 | Phân loại | Chọn 1 hoặc nhiều | Ô chọn Thành phẩm / Nguyên liệu (bỏ trống = cả hai) | [x] |
| 3 | Ngày đăng ký | Khoảng ngày | Ô chọn khoảng ngày, có nút nhanh (v1 đổi từ tháng sang ngày ở bao-CR-502) | [x] |
| 4 | Tên doanh nghiệp XNK | Chọn nhiều, **gõ có gợi ý** | Ô «Thêm doanh nghiệp nhập khẩu…» trong hàng Lọc thêm: gõ tên hoặc mã số thuế, chọn là thêm một chip (chọn nhiều bằng cộng dồn); vẫn thêm được từ thẻ «Nhà nhập khẩu» / chi tiết dòng (bao-CR-503) | [x] |
| 5 | Đơn vị đối tác | Chọn nhiều, **gõ có gợi ý** | Ô «Thêm đối tác nước ngoài…», cùng cách như mục 4 (bao-CR-503) | [x] |
| 6 | Đơn giá khai báo (USD) | Khoảng số | Khoảng số, so trên giá hiệu lực (điều chỉnh nếu có) | [x] |
| 7 | Nguyên tệ | Dropdown | Có | [x] |
| 8 | Lượng | Khoảng số | Có | [x] |
| 9 | Đơn vị tính | Dropdown | Có | [x] |
| 10 | Nước xuất xứ | Dropdown | Có | [x] |
| 11 | Điều kiện giao hàng | Dropdown | Có | [x] |
| 12 | Tỷ giá USD | Khoảng số | Có | [x] |
| 13 | Tệp nguồn | **Chọn nhiều** | Ô chọn nhiều lô nạp (bao-CR-503) | [x] |

## 4. Tiêu chí nghiệm thu (sheet 6)

| Mã | Tiêu chí | Chị Mi đánh giá | Hiện trạng | Kết quả |
|---|---|---|---|---|
| F01 | Nạp ≥ 2 tệp mẫu, gộp đúng số dòng, không trùng, báo lỗi thiếu cột | Đạt | Giữ nguyên | [x] |
| F02 | «Abamectin» AND «3.6» NOT «TC» ra đúng nhóm 3.6EC, không lẫn TC/TECH | (trống) | Có bài kiểm tự động cho đúng câu này; cần chị Mi thử lại trên dev: gõ `abamectin 3.6 -TC` | [x] |
| F03 | ≥ 3 điều kiện lọc cùng lúc cho kết quả đúng AND | Đạt | Giữ nguyên | [x] |
| F04 | Gắn nhãn đúng ≥ 95% (đối chiếu tay 50 dòng) | (trống) | **Chưa đo.** Cần chị Mi lấy 50 dòng đối chiếu tay; sai chỗ nào thì thêm từ khóa ở thẻ Cấu hình rồi «Gắn lại nhãn» | [ ] |
| F05 | 100% dòng xuất ra có Tỷ giá USD khớp tệp gốc | Đạt | Giữ nguyên | [x] |
| F06 | Excel đúng mẫu (header màu, dd/mm/yyyy, phân cách nghìn) | (trống) | **Chưa** — chờ tệp mẫu (xem F06) | [ ] |
| F10 | Không có quyền thì không vào được, không tải được | Đạt | Giữ nguyên | [x] |

## 5. Phi chức năng (sheet 6)

| Hạng mục | Yêu cầu | Hiện trạng | Kết quả |
|---|---|---|---|
| Hiệu năng | ~50MB / hàng chục nghìn dòng, phản hồi < 30 giây | Dev đang chạy 18.243 dòng, lọc và phân trang phản hồi tức thì; nạp chạy nền. Chưa thử tệp 50MB | [x] |
| Độ chính xác | Không mất / không nhân đôi dòng khi nạp nhiều tệp trùng phần dữ liệu | Nạp lại cùng tệp không nhân đôi. **Có rủi ro mất dòng** trong một tình huống, xem R1 | [~] |
| Mở rộng | Thêm cột mới mà không viết lại | Bộ đọc tệp theo tên cột; thêm cột là thêm khai báo + migration | [x] |
| Bảo mật & phân quyền | Chỉ tài khoản được cấp quyền mới xem / tải | Như F10 | [x] |
| Bảo trì | Từ khóa F04 và quy tắc nồng độ F02 để admin sửa, không cứng trong mã | Từ khóa phân loại + từ đồng nghĩa: admin sửa ở thẻ Cấu hình. **Quy tắc quy đổi nồng độ vẫn nằm trong mã** (luật mặc định; đại ca chốt 25/09 làm mặc định trước, ngoại lệ bổ sung sau) | [~] |

## 6. Rủi ro cần xác nhận

**R1 — Cách loại trùng khác yêu cầu.** Yêu cầu F01 loại trùng theo **Số hợp đồng + Số thứ tự hàng +
Tên doanh nghiệp**. Bản hiện tại **thay theo khoảng ngày**: nạp một lô mới thì mọi dòng của lô khác
nằm trong khoảng ngày của lô đó bị xóa rồi mới ghi dòng mới. Lý do: tệp GTT02 không có số tờ khai, so
đủ 32 cột vẫn còn 806 dòng trùng khít, nên không dựng được khóa duy nhất.

- **Đúng** khi mỗi tệp là trọn một khoảng thời gian (tệp tháng 1, tệp tháng 2…) — đó là cách chị Mi
  nạp khi nghiệm thu F01 (đã «Đạt»).
- **Mất dữ liệu** nếu hai tệp **cùng khoảng ngày nhưng khác nhóm hàng** (ví dụ tệp tháng 3 mã HS 3808
  và tệp tháng 3 mã HS 2903): nạp tệp sau sẽ xóa dòng của tệp trước. Lượt chạy thử có báo trước «sẽ
  thay n dòng cũ», nhưng dễ bị bỏ qua.
- **Cần hỏi chị Mi:** phòng Thu mua kết xuất GTT02 theo thời gian hay theo nhóm mã HS?

## 7. Việc còn lại

| # | Việc | Thuộc | Chặn bởi | Cỡ việc |
|---|---|---|---|---|
| N1 | Excel theo mẫu công ty (tiêu đề, header màu, wrap, dd/mm/yyyy, phân cách nghìn, tách sheet theo nhóm) | F06 | Tệp mẫu của chị Mi | Vừa |
| N2 | In báo giá + xuất PDF | F09 | Mẫu in của chị Mi | Vừa |
| N3 | ~~Ô gõ có gợi ý, chọn nhiều doanh nghiệp / đối tác ngay trên thanh lọc~~ — **xong bao-CR-503** | Sheet 4 #4–5 | — | — |
| N4 | ~~Tệp nguồn chọn nhiều~~ — **xong bao-CR-503** | Sheet 4 #13 | — | — |
| N5 | Khối «lịch sử thao tác» trên trang (xuất Excel, sửa cấu hình, gắn lại nhãn) | F11 | Không | Vừa |
| N6 | Biểu đồ kỳ tuần | F08 | Đại ca chốt có cần không | Nhỏ |
| N7 | Bộ lọc dùng chung + gợi ý từ khóa đã nhập | F07 | Đại ca chốt (26/09 chốt làm riêng từng người trước) | Vừa |
| N8 | Quy tắc quy đổi nồng độ cho admin sửa | Phi chức năng | Chị Mi có ngoại lệ cần thêm không | Vừa |
| N9 | Đo tỷ lệ gắn nhãn đúng trên 50 dòng mẫu | Nghiệm thu F04 | Chị Mi đối chiếu tay | Không phải mã |
| N10 | Làm rõ R1 (tệp chia theo thời gian hay theo mã HS) | F01 | Chị Mi trả lời | Không phải mã |

## 8. Đề xuất thêm của đại ca (chat 25–26/09) — đã xong hết

| Đề xuất | CR | Kết quả |
|---|---|---|
| Tải lại tệp đã nạp | bao-CR-493 | [x] |
| Bỏ hẳn nút «Giá ưu tiên» trên biểu đồ (luôn vẽ giá điều chỉnh) | bao-CR-493 | [x] |
| Gom Kỳ (tháng / quý / năm) và Đơn vị vào một thẻ | bao-CR-493 | [x] |
| Đổi tên thành «Tra cứu thị trường» | bao-CR-500 | [x] |
| Cấu hình nằm trong một thẻ, không đẻ màn riêng (từ khóa, từ đồng nghĩa, hóa chất) | bao-CR-501 | [x] |
| v1 và v2 cùng chức năng | bao-CR-502 | [x] |

## 9. CR liên quan

bao-CR-470 (nền phân hệ) · 477 · 481 · 493 (đợt 1: VND, lọc thêm, lịch sử nạp) · 494 (nhãn Thành phẩm /
Nguyên liệu) · 495 (AND/NOT, nồng độ, đồng nghĩa) · 496 (lưu bộ lọc, log từng dòng) · 500 (đổi tên) ·
501 (thẻ Cấu hình v2) · 502 (v1 theo kịp v2, lọc theo ngày, vá lỗi lưu hóa chất) · 503 (ô gợi ý doanh
nghiệp / đối tác, tệp nguồn chọn nhiều). Chi tiết từng CR ở
`doc/tai-lieu-ky-thuat/change-log-bao.md`; đối chiếu gốc theo nhóm Y ở `01-danh-sach-tinh-nang.md` §11.
