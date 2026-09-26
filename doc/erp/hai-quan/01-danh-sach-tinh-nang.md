# PHÂN HỆ TRA CỨU GIÁ HẢI QUAN — DANH SÁCH TÍNH NĂNG

> **Mã tài liệu:** ERP-HQ-01 · **Bản:** 1.1 — 23/09/2026 · **Loại:** KẾ HOẠCH + TÌNH TRẠNG (bao-CR-470 đã có mã nguồn ở LOCAL, chưa commit — xem §0)
> **Nguồn quyết định:** đại ca chốt miệng 23/09/2026, xem §7. **Nguồn dữ liệu tham chiếu:** thư mục ngoài repo `thongtinhaiquan/` (5 tệp `.xls` kết xuất GTT02 ngày 18/09/2026 + một phần mềm HTML chạy offline của IDA Group). Thư mục đó **không** đưa vào repo.

## 0. Tình trạng (23/09/2026, bao-CR-470)

Đại ca bảo *"làm full xong hết tất cả phase + đưa data vào local"* — đã làm đủ HQ1…HQ6 ở **LOCAL**, **chưa commit, chưa deploy**, chờ đại ca review.

| Nhóm | Đã có | Còn thiếu / để sau |
|---|---|---|
| N — nền + nạp | N-01…N-08 đủ. 5 tệp mẫu đã nạp: **18.243 dòng**, 7.651 dòng vá ngày, 3.503 đối tượng (nhà nhập khẩu + đối tác) | Q2, Q6 vẫn mở |
| T — tra cứu | T-01…T-06 đủ, cả bản cũ lẫn bản mới | — |
| B — biểu đồ | B-01…B-05 đủ | Q4 (dữ liệu các năm trước) vẫn mở — B-03 vẫn phải cảnh báo "một năm" |
| A — trợ lý AI | A-01…A-03: hai tool `customs_price_stats` + `customs_buy_timing` (ToolSpec, gác `customs_price.read`); **A-05…A-08 (bao-CR-481):** so sánh, `customs_market`, `customs_legal_check`, đánh giá «có nên mua lúc này» | A-04: bài «Tra cứu giá hải quan» dưới nhóm *Dành cho Nhân viên Mua hàng*, dựng bằng `scripts/seed_help_customs_prices.py` — **mới chạy ở local**, CẤM tự chạy ở prod |
| P — pháp lý | P-01 (dạng danh mục có sẵn ngưỡng — xem đính chính ở §7), P-03, P-04, cảnh báo theo từ khóa đang tra | **P-02 (so tồn kho với ngưỡng) chưa làm** — cần cầu nối vật tư ↔ hoạt chất, đại ca để sau |

Nhận ra hoạt chất: **9.223 / 18.243 dòng (51%)**, hàm lượng / dạng **93%**. Phần không nhận ra phần lớn là hóa chất khử trùng / tẩy rửa, không có hoạt chất BVTV để nối.

## 1. Việc này là gì

Thu mua cần biết **mặt hàng mình sắp mua đang được nhập về Việt Nam với giá nào, lượng bao nhiêu, và tháng nào giá tốt nhất** — để quyết định mua lúc nào và có ôm hàng trước hay không. Dữ liệu là tờ khai hải quan nhập khẩu do bên ngoài kết xuất, mình nạp vào bằng Excel.

**Ranh giới đã chốt — đọc trước khi thiết kế:**

- **KHÔNG nối với VTBB của mình.** Đây là màn **tra cứu độc lập**. Chưa chắc mặt hàng trong dữ liệu hải quan có tương ứng trong danh mục của mình, và cầu nối (nếu làm) sẽ là một việc riêng, chốt sau.
- **KHÔNG nối với tồn kho, KHÔNG nối lịch sử mua hàng.** Câu hỏi *"có nên tồn hàng không"* trả lời bằng **biểu đồ giá + trợ lý AI**, không bằng số liệu kho. Ví dụ đại ca đưa: biết vụ đông xuân sẽ bán nhiều một loại chai, cần lượng lớn hoạt chất A, nhưng giá A ổn định nhất lại rơi vào tháng sau → mua trước và ôm tới tháng 10 mới sản xuất.
- **Lấy KHUNG CHỨC NĂNG của phần mềm ngoài, không bê mã.** Phần mềm kia chạy trong trình duyệt, dữ liệu nằm trong máy người dùng (IndexedDB), không máy chủ, không tài khoản, không phân quyền — không dùng lại được ở ERP.

## 2. Cách đọc bảng

| Cột | Nghĩa |
|---|---|
| Mã | Mã tính năng ổn định — cấp một lần, không đổi số |
| Nội dung | Làm gì · luật/ranh giới (bôi đậm) · vì sao |
| Bản | `1` = đợt đầu · `2` = đợt sau · `3` = đợt cuối · `?` = chờ trả lời câu hỏi còn mở |
| Có sẵn | `[x]` tận dụng nguyên · `[~]` có khuôn phải sửa · `[ ]` làm mới |

Tổng: **24 tính năng**, trong đó **13 thuộc đợt đầu**.

---

## 3. Nhóm N — Nền dữ liệu và đường nạp

> Nhóm này quyết định mọi thứ phía sau. Ba tính năng N-03, N-04, N-05 là **ba cái bẫy đã đo được trên dữ liệu thật**, không phải lo xa: bỏ qua chúng thì mọi biểu đồ phía sau đều sai, và **sai im lặng**.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| N-01 | Bảng tờ khai | Một dòng = một dòng hàng trên tờ khai. 32 cột nguồn, giữ **cả giá khai báo lẫn giá điều chỉnh**, cả nguyên tệ lẫn tỷ giá. Khối lượng dự kiến ~18.000 dòng mỗi lần kết xuất, nạp định kỳ → phải có chỉ mục theo **mã HS · tháng · tên hàng** ngay từ đầu | 1 | [ ] |
| N-02 | Nạp bằng Excel | Màn nạp đọc đúng khuôn tệp GTT02 trong `thongtinhaiquan/data/`. **Đọc được `.xls` đời cũ (OLE2/BIFF)** — 5 tệp mẫu đều là định dạng này, `openpyxl` KHÔNG đọc được, phải thêm `xlrd` vào `requirements.txt` | 1 | [~] khuôn `import_tool` |
| N-03 | **Vá ngày tháng bị đảo** | ⚠️ Cột *Ngày đăng ký* trong tệp mẫu **lẫn hai kiểu và 42% số dòng SAI**: 10.592 dòng là chữ `DD-MM-YYYY` (đúng), 7.651 dòng là số ngày Excel với **ngày và tháng bị hoán đổi**. Bằng chứng khớp tuyệt đối: ô kiểu chữ chỉ chứa ngày 13–31, ô kiểu số suy ra "ngày" chỉ 1–9 — hễ ngày ≤ 12 thì Excel đọc nhầm thành tháng. Hệ quả nhìn thấy được: tệp kết xuất ngày 18/09/2026 mà dữ liệu thô hiện tới **09/12/2026**, ba tháng trong tương lai. **Luật nạp: ô kiểu số thì phải đảo lại ngày/tháng; ô kiểu chữ thì đọc thẳng `DD-MM-YYYY`.** Không vá thì biểu đồ giá theo tháng sai 42% mà không một dòng lỗi nào hiện ra. ⚠️ **Chỉ vá cột Ngày đăng ký** — cột *Ngày hợp đồng* là ô ngày thật, KHÔNG bị đảo (10.855 ô có ngày > 12); vá nhầm cột đó là làm hỏng 39% số ngày hợp đồng đang đúng. Chi tiết ở [`02`](./02-thiet-ke-ky-thuat.md) §4.2 | 1 | [ ] |
| N-04 | **Không có khóa duy nhất — nạp theo LÔ** | ⚠️ Dữ liệu **không có số tờ khai**, nên không dựng được khóa duy nhất: so đủ cả 32 cột vẫn còn **806 dòng trùng khít**, và khóa tốt nhất thử được (`ngày + mã DN + tên hàng + số thứ tự + lượng + giá`) vẫn còn 1.297 dòng đụng nhau. Nghĩa là **không dùng được kiểu «có rồi thì cập nhật, chưa có thì tạo»** — nạp chồng hai tệp giao nhau là nhân đôi dữ liệu. Chốt: mỗi lần nạp là **một LÔ** có mã riêng, ghi rõ khoảng ngày lô đó phủ; nạp lô mới trùng khoảng ngày thì **xóa sạch khoảng đó rồi nạp lại**, không trộn. **Một lô = một tệp**, chọn được cả bộ tệp một lần — GTT02 cắt mỗi lần xuất thành từng khối hai tháng (bộ mẫu: 5 tệp nối khít nhau, không chồng ngày). Nguy cơ sót một tệp thì xử bằng **dải tháng đã phủ** trên màn hình, tháng trống hiện rõ ([`04`](./04-giao-dien.md)) | 1 | [ ] |
| N-05 | **Quy về một đơn vị và một đồng tiền** | ⚠️ 29 loại đơn vị tính (KGM 10.962 · LTR 2.891 · PCE 1.616 · UNK 909 · …) và 5 đồng tiền (USD 85% · VND · EUR · JPY · GBP). So giá giữa các dòng mà không quy đổi là so táo với cam. **Tiền: dùng thẳng cột giá USD có sẵn** — hải quan đã quy đổi hộ theo tỷ giá tại ngày khai, không phải tự nhân lại. **Đơn vị: KHÔNG quy đổi**, tách riêng theo từng đơn vị (kg và lít chiếm 76%); chỉ `TNE → KGM` là đổi chắc chắn, còn cái/bộ/đơn vị thì không đổi sang kg được | 1 | [ ] |
| N-06 | Chọn giá nào là "giá" | **58% số dòng có đơn giá ĐIỀU CHỈNH** khác giá khai báo — đó là giá hải quan áp lại. Bản đầu: **ưu tiên giá điều chỉnh, không có thì lấy giá khai báo**, và màn hình nói rõ đang xem giá nào | 1 | [ ] |
| N-07 | Khóa phân quyền `customs_price` | Một khóa mới (kèm `customs_regulation` cho danh mục pháp lý ở P-01 — tổng **hai khóa**, `test_pham_vi_khai_du_b07.py` 66 → 68), khai `PUBLIC` trong `SCOPE_FIELDS` — đây là dữ liệu thị trường bên ngoài, **không thuộc phòng ban hay pháp nhân nào** nên không lọc phạm vi. **Thiếu khai scope là suite đỏ** (`test_pham_vi_khai_du_b07.py`). Quyền `write` chỉ cho người được nạp dữ liệu | 1 | [~] |
| N-08 | Nhật ký lô đã nạp | Ai nạp · lúc nào · tệp gì · bao nhiêu dòng · bao nhiêu dòng bị vá ngày · khoảng ngày phủ. **Dùng lại nguyên `tab_import_batch` + `tab_import_log` + chế độ chạy thử `DRY_RUN`** của mô-đun `import_tool` (thêm `ImportModule.CUSTOMS_DECLARATION = 3`), bản mới hiện luôn ở màn `/system/imports` sẵn có. Xem [`02`](./02-thiet-ke-ky-thuat.md) §3.1 | 1 | [x] `import_tool` |

## 4. Nhóm T — Tra cứu

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| T-01 | Màn tra cứu | Ô tìm theo **tên hàng** (dữ liệu là chữ tự do, trung bình 165 ký tự) + lọc **mã HS · xuất xứ · năm · tháng · đơn vị tính · doanh nghiệp nhập**. Bảng kết quả dùng `DataTable` | 1 | [~] |
| T-02 | Gom theo kết quả tìm kiếm | Gom **tập dòng khớp lần tìm** (thường gõ tên hoạt chất: *ATRAZINE*, *MANCOZEB*): **giá thấp nhất · cao nhất · bình quân gia quyền theo lượng · lượng cộng dồn · **số dòng hàng** (không phải số tờ khai) · lần nhập gần nhất**. ⚠️ **Không gom theo tên hàng từng chữ** — đo được 83% tên hàng chỉ xuất hiện đúng một lần (chữ tự do nhét cả hàm lượng, quy cách), gom theo tên là gần như không gom được gì. Xem [`02`](./02-thiet-ke-ky-thuat.md) §2.1 | 1 | [ ] |
| T-03 | Chi tiết một dòng hàng | Mở ra thấy đủ 32 trường của dòng hàng, đối tác nước ngoài, nước xuất xứ, điều kiện giao hàng, thuế suất | 1 | [ ] |
| T-04 | Tra theo hoạt chất | Nối tên thương mại với **hoạt chất** — phần mềm ngoài có sẵn danh mục 6.900+ thuốc BVTV kèm hoạt chất. **Đây là thứ thu mua thật sự cần**: họ mua theo hoạt chất chứ không theo tên thương mại. Cần nạp danh mục đó thành một bảng riêng | 2 | [ ] |
| T-05 | Bảng xếp hạng nhà nhập khẩu | Ai đang nhập mặt hàng này, lượng bao nhiêu — biết được thị trường ai đang gom | 2 | [ ] |
| T-06 | Xuất Excel kết quả tra cứu | Theo khuôn xuất sẵn có của hệ | 2 | [~] |

## 5. Nhóm B — Biểu đồ và bảng điều khiển

> Đây là phần trả lời câu hỏi *"tháng nào giá tốt nhất"* và *"có nên ôm hàng không"*.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| B-01 | Biểu đồ giá theo kỳ | Đường giá bình quân gia quyền theo **kỳ chọn được — tháng · quý · năm** — của tập kết quả tìm kiếm, kèm dải cao–thấp. Kỳ gom là **tham số của truy vấn, không phải bảng lưu sẵn** ([`02`](./02-thiet-ke-ky-thuat.md) §3.5). Dùng `recharts` đã có trong `frontend-v2` | 1 | [~] |
| B-02 | Biểu đồ lượng theo tháng | Cột lượng nhập theo tháng — **giá rẻ mà cả thị trường không ai nhập thì rẻ đó đáng ngờ** | 1 | [~] |
| B-03 | ⚠️ Cảnh báo độ tin cậy của mùa vụ | Dữ liệu hiện **chỉ có một năm (2026)**. Một năm nói được xu hướng trong năm, **không nói được mùa vụ** — muốn khẳng định "tháng 10 luôn rẻ" thì cần ít nhất 3 năm. Màn hình **phải nói rõ đang dựa trên bao nhiêu năm và bao nhiêu lần nhập**, đừng vẽ một đường rồi để người đọc tự tin quá mức | 1 | [ ] |
| B-04 | Dải tháng đã phủ | Đầu màn tra cứu: khoảng ngày của dữ liệu · tổng số dòng hàng · lần nạp gần nhất · **dải 12 tháng tô ô đã có dữ liệu** — chặn lỗi quên nạp một tệp. Tính thẳng lúc mở, **không lưu sẵn**. *(Bản trước là "bảng điều khiển tổng quan" dùng `tab_report_snapshot` — bỏ theo bố cục hai thẻ đại ca chốt 23/09/2026)* | 1 | [ ] |
| B-05 | So sánh nhiều mặt hàng | Xếp 2–5 mặt hàng cạnh nhau trên cùng một biểu đồ | 2 | [ ] |

## 6. Nhóm A — Trợ lý AI

> Đại ca chốt: *"có 1 phase là cho AI đọc được luôn thì tốt"*. Trợ lý AI của hệ đã có sẵn kiến trúc công cụ (hiện ~34 tool), thêm vào đó chứ không dựng riêng.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| A-01 | Tool tra giá cho trợ lý | Trợ lý tra được giá / lượng / khoảng thời gian của một mặt hàng hay hoạt chất. **Phải đi qua đúng khóa `customs_price`** như mọi tool khác — người không có quyền hỏi thì trợ lý không trả lời | 2 | [~] khuôn tool sẵn có |
| A-02 | Tool phân tích thời điểm mua | Trả lời *"nên mua vào lúc nào thì giá thấp nhất"*: trả về giá theo tháng + biên độ + số lần nhập, **để model lập luận trên số, không để model tự bịa số** | 2 | [ ] |
| A-03 | ⚠️ Trợ lý phải nói ra độ tin cậy | Cùng lẽ với B-03: chỉ có một năm dữ liệu thì câu trả lời **bắt buộc kèm cảnh báo**. Một câu khẳng định chắc nịch dựa trên 3 lần nhập là thứ nguy hiểm nhất của cả tính năng này — người đọc sẽ đặt hàng thật theo nó | 2 | [ ] |
| A-04 | Bài hướng dẫn sử dụng | Một bài trong Trung tâm HDSD, theo nếp các bài tool trợ lý đã có | 2 | [~] |
| A-05 | So sánh qua trợ lý | `customs_price_stats` nhận thêm `compare_keywords` (1–4 mặt hàng) → so trên CÙNG một đơn vị với mặt hàng chính (bao-CR-481) | 2 | [x] |
| A-06 | Tool thị trường `customs_market` | Ai nhập (gộp theo MST, thị phần), mua của đối tác nào, từ nước nào, 5 lô gần nhất — chỉ trong một đơn vị tính (bao-CR-481) | 2 | [x] |
| A-07 | Tool pháp lý `customs_legal_check` | Tra danh mục hóa chất theo tên / CAS / công thức (nặng nhất lên đầu) + biểu thuế theo mã HS. **Không có mức phạt trong dữ liệu — trợ lý cấm tự nêu**; không thấy trong danh mục thì không được kết luận là được phép (bao-CR-481) | 2 | [x] |
| A-08 | ⚠️ «Có nên mua lúc này không» | `customs_buy_timing` trả thêm phần `now`: giá tháng gần nhất thấp / trung bình / cao so với tứ phân vị các tháng ĐỦ dữ liệu, xu hướng 3 tháng (chỉ tháng đủ dữ liệu), dữ liệu cũ quá 45 ngày thì gắn cờ; tháng gần nhất ít lô thì kèm `reference_month`. Trợ lý kết luận dạng «dữ liệu giá nghiêng về …» và **bắt buộc** nói không biết tồn kho / nhu cầu / hạn dùng / dòng tiền (bao-CR-481) | 2 | [x] |

## 7. Nhóm P — Pháp lý và ngưỡng theo nghị định (đợt cuối)

> Đại ca chốt: *"cái này để cho phase cuối đi"*. Ghi lại ngay để không rơi.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| P-01 | Danh mục hóa chất theo văn bản (có ngưỡng) | ⚠️ **ĐÍNH CHÍNH bản 1.0:** bản trước ghi "phần mềm ngoài KHÔNG có bảng ngưỡng khối lượng" — **SAI**. Mã nguồn của nó có đủ bốn phụ lục NĐ 24/2026/NĐ-CP, trong đó **Phụ lục IV = 29 hóa chất kèm NGƯỠNG KHỐI LƯỢNG** (vd Ammonia 500 kg, Clo 25 kg); bản 1.0 chỉ rà thẻ giao diện mà sót dữ liệu phía dưới. Đã nạp thành `tab_customs_regulation` (PL1 39 · PL2 787 · PL3 164 (nguồn có 2 dòng trùng tên + CAS) · PL4 29 · hoạt chất cấm TT 75/2025 31 · phải công bố TT 01/2026 10) + màn sửa **Danh mục hóa chất theo văn bản** (khóa `customs_regulation`) để khi văn bản đổi thì sửa tay. Vẫn cần **người chịu trách nhiệm cập nhật** khi nghị định đổi | 3 | [x] nạp từ phần mềm ngoài |
| P-02 | Cảnh báo khi chạm ngưỡng | Dựa trên P-01. **Lúc này mới cần nối với tồn kho** — ngưỡng nói về lượng đang giữ, không nói về lượng nhập của thị trường. **CHƯA LÀM** — tồn kho tính theo VTBB, mà VTBB chưa có cầu nối sang hoạt chất (ranh giới "không nối VTBB" chốt 23/09). Đã làm thay bằng **cảnh báo lúc tra**: gõ từ khóa trùng hóa chất cấm / có ngưỡng / phải công bố thì màn tra cứu hiện dải cảnh báo ngay | 3 | [ ] |
| P-03 | Tra cứu nghĩa vụ theo hoạt chất / CAS | Bê khung tra cứu nghĩa vụ của phần mềm ngoài: nhập tên hóa chất / số CAS / công thức → ra nghĩa vụ phải làm | 3 | [ ] |
| P-04 | Biểu thuế XNK | Phần mềm ngoài có sẵn biểu thuế 2026 đầy đủ kèm thuế suất 12 hiệp định FTA và ghi chú chính sách từng mã HS. Nạp thành danh mục tra cứu | 3 | [ ] |

---

## 8. Lộ trình

| Đợt | Gồm | Ra được gì |
|---|---|---|
| **Đ-1** | N-01…N-08 · T-01…T-03 · B-01…B-04 | Nạp được Excel, tra được giá và lượng, xem được biểu đồ giá theo kỳ. **Đây là phần trả lời trực tiếp câu hỏi của thu mua**. Lộ trình chi tiết theo phase: [`03-lo-trinh-phase.md`](./03-lo-trinh-phase.md) |
| **Đ-2** | T-04…T-06 · B-05 · A-01…A-04 | Tra theo hoạt chất, so sánh nhiều mặt hàng, trợ lý AI đọc được và phân tích thời điểm mua |
| **Đ-3** | P-01…P-04 | Ngưỡng theo nghị định, cảnh báo, tra cứu nghĩa vụ, biểu thuế |

## 9. Câu hỏi còn mở — cần đại ca trả lời trước khi gõ mã

| # | Câu hỏi | Vì sao chặn |
|---|---|---|
| Q1 | ~~Ai được nạp dữ liệu?~~ **Đã chốt 23/09/2026:** tạo khóa quyền mới, **đại ca tự tick trên màn Phân quyền** cho vai trò nào được xem / được nạp. Hệ thống không tự cấp cho vai trò nào | — |
| Q2 | **Nạp bao lâu một lần, và mỗi lần phủ khoảng nào?** Cả năm chạy lại từ đầu, hay chỉ tháng mới? | Quyết định N-04: xóa-rồi-nạp theo khoảng ngày cần biết khoảng đó do người nạp khai hay hệ tự suy từ dữ liệu |
| Q3 | ~~Dữ liệu có nhạy cảm không?~~ **Đã chốt 23/09/2026:** ai được tick quyền xem thì thấy **toàn bộ** dữ liệu, không lọc theo phòng ban / công ty. Đại ca sẽ tick cho Quản lý thu mua, Admin thu mua, Nhân sự thu mua | — |
| Q4 | **Có lấy được dữ liệu các năm trước không?** | B-03 và A-03: một năm thì không kết luận được mùa vụ, mà mùa vụ lại đúng là thứ đại ca muốn |
| Q5 | ~~Đứng ở menu nào?~~ **Đã chốt 23/09/2026:** một màn tra cứu trong menu Thu mua, **hai thẻ Danh sách / Biểu đồ**, biểu đồ chỉ hiện khi đã lọc — không có màn báo cáo riêng. Bản làm ra thêm ba thẻ cạnh đó (*Nhà nhập khẩu* · *So sánh* · *Pháp lý & thuế*) cho T-05, B-05, P-03/P-04, cùng một luật: chưa lọc thì không vẽ. Xem [`04`](./04-giao-dien.md) §2 | — |
| Q6 | **GTT02 có xuất kèm SỐ TỜ KHAI được không?** | Dữ liệu hiện tại không có. Có số tờ khai thì *số tờ khai + số thứ tự hàng* là khóa duy nhất tự nhiên — hết phải nạp kiểu xóa theo khoảng ngày (N-04), và đếm được số tờ khai chính xác. Xem [`02`](./02-thiet-ke-ky-thuat.md) §2.2 |

## 10. Ghi chú kỹ thuật đã đo được

Đo trên 5 tệp trong `thongtinhaiquan/data/` ngày 23/09/2026:

- **18.243 dòng**, 100% thuộc chương HS **3808** (thuốc trừ sâu/bệnh/nấm, chất khử trùng). Không có mặt hàng nào khác.
- Khoảng thời gian thật: **02/01/2026 → 17/09/2026** (sau khi vá ngày theo N-03).
- Thiết kế lưu trữ, lược đồ bảng, đường nạp và ước lượng dung lượng: xem [`02-thiet-ke-ky-thuat.md`](./02-thiet-ke-ky-thuat.md).
- **1.461 doanh nghiệp nhập khẩu** — Syngenta 407 dòng, Ecolab 250, Bayer 212 dẫn đầu.
- Tên hàng **không bị cắt cụt**: dài 16–200 ký tự, trung bình 165.
- Tệp `.xls` đời cũ, **cần `xlrd`** (`openpyxl` không đọc được).

## 11. Nhóm Y — Yêu cầu phòng Thu mua 25/09/2026 (FR-PROC-2026-001, chị Mi)

> Tệp «YÊU CẦU TÍNH NĂNG TRA CỨU GIÁ HS CODE-NOTE 250926.xlsx» (22/09, ghi chú 25/09) đối chiếu với bản
> đang chạy trên dev 25/09/2026. Đại ca chốt cùng ngày: hai cột VND (7% tạm tính + theo thuế suất dòng);
> bỏ hẳn nút Giá trên biểu đồ; không cần số tờ khai (log từng dòng có Thêm mới / Lỗi / Bỏ qua); lưu bộ lọc
> riêng từng người nhưng có sẵn cờ dùng chung; Excel định dạng và in báo giá chờ mẫu chị Mi.
> Đại ca chốt thêm 25/09: **bê cả sang bản cũ (v1)** — Y-01…Y-07 đã có ở cả hai bản. 26/09 đại ca chốt luật chung: **v1 và v2 phải cùng chức năng, cái nào thiếu thì ERP Agent 2 bù**; phần giao diện v1 của Y-08…Y-13 làm sau khi Erp Agent 1 cắm xong v2.

| Mã | Yêu cầu gốc | Nội dung làm | CR | Ai làm | Có sẵn |
|---|---|---|---|---|---|
| Y-01 | Sheet 3 cột 15 | Hai cột «Đơn giá quy đổi VND»: giá hiệu lực × tỷ giá USD × 1,07 (thuế NK 7% tạm tính) và × (1 + thuế suất XNK của dòng); có ở bảng, chi tiết dòng, Excel | bao-CR-493 | ERP Agent 2 | [x] |
| Y-02 | Đề xuất đại ca 2.1 | Bỏ hẳn nút «Giá: điều chỉnh / khai báo» trên biểu đồ — luôn vẽ giá điều chỉnh | bao-CR-493 | ERP Agent 2 | [x] |
| Y-03 | Đề xuất đại ca 2.2 | Kỳ (tháng / quý / năm) và Đơn vị gom vào MỘT thẻ | bao-CR-493 | ERP Agent 2 | [x] |
| Y-04 | Đề xuất đại ca 1 | Tải lại tệp GTT02 đã nạp (chỉ lô nạp qua màn hình có tệp gốc; lô nạp bằng script không có) | bao-CR-493 | ERP Agent 2 | [x] |
| Y-05 | F11 | Lịch sử nạp thành THẺ trên trang thay hộp thoại | bao-CR-493 | ERP Agent 2 | [x] |
| Y-06 | Sheet 4 mục 4–5 | Doanh nghiệp nhập / đối tác chọn NHIỀU (chip cộng dồn, id nối dấu phẩy) | bao-CR-493 | ERP Agent 2 | [x] |
| Y-07 | Sheet 4 mục 6–13 | Hàng «Lọc thêm»: nguyên tệ, điều kiện giao hàng, tệp nguồn (lô nạp), khoảng đơn giá (giá hiệu lực), khoảng lượng, khoảng tỷ giá USD | bao-CR-493 | ERP Agent 2 | [x] |
| Y-08 | F04 | Nhãn tự động Thành phẩm / Nguyên liệu (TC, TECH, TG, «kỹ thuật», «nguyên liệu»; không khớp = Thành phẩm), cột + lọc theo nhãn, bảng từ khóa admin sửa được | bao-CR-494 | Erp Agent 1 | [~] |
| Y-09 | F02 | Tìm «Có các từ» / «Không có từ» (AND / NOT) trên tên hàng | bao-CR-495 | Erp Agent 1 | [~] |
| Y-10 | F02 | Quy đổi cách viết nồng độ theo luật mặc định (3,6% ≡ 3.6EC ≡ 36 G/L); ngoại lệ chị Mi bổ sung sau | bao-CR-495 | Erp Agent 1 | [~] |
| Y-11 | F02 ghi chú 25/09 | Màn từ đồng nghĩa người dùng tự thêm cặp, nạp mồi từ bảng bí danh sẵn có | bao-CR-495 | Erp Agent 1 | [~] |
| Y-12 | F07 | Lưu bộ lọc RIÊNG từng người (đặt tên, chọn lại một phát); bảng có sẵn cột dùng chung, mặc định tắt | bao-CR-496 | ERP Agent 2 | [ ] |
| Y-13 | F01 ghi chú 25/09 | Log từng dòng khi nạp: Thêm mới / Lỗi / Bỏ qua vì trùng trong lô (không có «Cập nhật» vì dữ liệu không có số tờ khai) | bao-CR-496 | ERP Agent 2 | [ ] |
| Y-14 | F06 | Excel theo mẫu công ty: tiêu đề, header màu, wrap, dd/mm/yyyy, phân cách hàng nghìn, tách sheet theo nhóm | NỢ — chờ tệp mẫu chị Mi | — | [ ] |
| Y-15 | F09 | Trang tra cứu giá: in báo giá, xuất PDF | NỢ — chờ mẫu in chị Mi | — | [ ] |
| Y-16 | F08 | Biểu đồ theo TUẦN (yêu cầu ghi «tuần hoặc tháng») | chưa cấp số — hỏi lại có cần không | — | [ ] |

**Đã có sẵn từ trước, không làm lại:** F03 lọc nhiều trường · F05 tỷ giá theo dòng · F08 biểu đồ (tháng / quý / năm,
so sánh nhiều mặt hàng) · F10 phân quyền (`customs_price`) · F01 nạp nhiều tệp, kiểm cột, hoàn tác lô.

