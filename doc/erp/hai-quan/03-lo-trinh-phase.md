# PHÂN HỆ TRA CỨU GIÁ HẢI QUAN — LỘ TRÌNH PHASE

> **Mã tài liệu:** ERP-HQ-03 · **Bản:** 1.1 — 23/09/2026 · HQ1…HQ6 đã làm ở LOCAL theo lệnh đại ca cùng ngày, **chưa commit, chưa deploy** — xem dòng *Trạng thái* của từng phase
> KHÔNG đặt mốc lịch (theo lệ chung của bộ tài liệu ERP), có ước lượng **ngày công**. Mỗi phase nghiệm thu riêng được; dừng giữa chừng không để hệ nửa vời.

Mã tính năng (N-xx, T-xx…) tra ở [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md); lược đồ và đường nạp ở [`02-thiet-ke-ky-thuat.md`](./02-thiet-ke-ky-thuat.md); màn hình ở [`04-giao-dien.md`](./04-giao-dien.md).

```
HQ0 chốt câu hỏi ──► HQ1 nền dữ liệu + nạp ──► HQ2 bản cũ + prod ──► HQ3 bản mới ──┬──► HQ4 hoạt chất · nhà nhập khẩu · so sánh ──► HQ6 pháp lý & ngưỡng
                                                                                  └──► HQ5 trợ lý AI
```

**Đợt đầu = HQ1 → HQ3, khoảng 9 ngày công.** Xong HQ3 là thu mua dùng được trên cả hai giao diện. Toàn bộ lộ trình khoảng **20 ngày công**, chưa tính thời gian chờ nghiệp vụ trả lời.

## Hai luật xuyên suốt

1. **Bản cũ trước, bản mới sau** (quy trình đại ca chốt 08/09/2026). Mỗi phase có màn hình chia làm hai đợt: backend + `frontend/` lên `main` và **prod chạy ổn trước**, rồi mới port `frontend-v2/` trên `erp-v2`. Không làm song song hai giao diện trong cùng một đợt.
2. **Mỗi phase một CR**, cấp số và **đặt chỗ ngay lúc bắt đầu phase**, không cấp trước. Deploy prod **theo lệnh đại ca từng lần**.

---

## HQ0 — Chốt câu hỏi — XONG 23/09/2026

**Phạm vi:** trả lời 6 câu hỏi ở §9 của [`01`](./01-danh-sach-tinh-nang.md). Tùy chọn: thử bật nén trang InnoDB trên VPS ([`02`](./02-thiet-ke-ky-thuat.md) §6) để biết hệ thống tệp có hỗ trợ không.

**Kết quả:** Q1 · Q3 · Q5 đã chốt (xem §9 của [`01`](./01-danh-sach-tinh-nang.md)); Q2 · Q4 · Q6 để mở, không chặn.

**Điều kiện đủ để sang HQ1 (bản gốc):**
- **Q3 (dữ liệu có nhạy cảm không)** có câu trả lời — quyết định khóa `customs_price` để công khai hay khoanh theo vai trò.
- **Q1 (ai được nạp)** có câu trả lời — quyết định vai trò nào có `customs_price.write`.
- **Q5 (đứng ở menu nào)** có câu trả lời — cần cho HQ2.

**Không chặn:** Q2 (tần suất nạp), Q4 (dữ liệu năm cũ), Q6 (số tờ khai) — thiết kế chịu được cả ba; riêng Q6 mà có thì nạp dữ liệu đơn giản hẳn.

## HQ1 — Nền dữ liệu và đường nạp (≈ 3 ngày) — backend, nhánh `main`

**Trạng thái: XONG MÃ 23/09/2026 — bao-CR-470, chưa commit, chưa deploy.** Nghiệm thu bằng 5 tệp thật đạt đủ 10/10 điều kiện dưới đây; migration chạy thật trên MySQL 8 (10 phân vùng, khóa chính `(id, reg_date)`, lọc một năm chỉ quét một phân vùng). Khác bản kế hoạch ba chỗ, cố ý:
- **Cửa nạp riêng `/api/customs/imports`**, gác bằng `customs_price` — cửa chung `/api/imports` chỉ nhận `.xlsx`/`.csv` và gác bằng khóa `import`. Bảng lô, nhật ký, chạy thử, hoàn tác thì vẫn dùng lại của `import_tool`.
- **Lô đã thay dữ liệu cũ thì KHÔNG hoàn tác được** (báo "hãy nạp lại tệp đúng") — dòng cũ đã xóa lúc thay, không có bản chụp để dựng lại; hoàn tác là để trống cả khoảng ngày.
- **Luật vá ngày tự nhận diện**: chỉ vá khi cả cột có đúng dấu vân tay "vừa có ô chữ, vừa có ô ngày, mọi ô ngày ≤ 12" — nguồn sửa cách xuất thì tự thôi vá.

**Phạm vi:** N-01 … N-08.
- Migration: `tab_customs_party` + `tab_customs_line` chia phân vùng năm (nhánh `if dialect != "mysql": return` như CR-454).
- `ImportModule.CUSTOMS_DECLARATION = 3` trong `import_tool`; bộ đọc tệp `.xls` bằng `xlrd` (thêm vào `requirements.txt` → **phải dựng lại** `api` + `celery-worker`, không restart suông).
- Luật đọc: khớp tiêu đề theo chữ đã chuẩn hóa; **vá ngày CHỈ ở cột Ngày đăng ký**; bóc dấu `'`; ô trống ra `NULL`; phương tiện vận chuyển ra IntEnum, mã lạ thì từ chối cả lô.
- Ba chế độ lô: `DRY_RUN` · `APPLY` (thay dữ liệu cũ trong khoảng ngày) · `REVERTED` (hoàn tác).
- Khóa quyền `customs_price`: `ENTITIES` + `SCOPE_FIELDS` + seed **cả hai bản**. ⚠️ Phải quyết nó có vào `_SYS_ENTITIES` của `seed.py` không — không vào thì Quản lý thu mua **tự nhiên có quyền ghi**, tức quyền nạp và hoàn tác dữ liệu (luật đã ghi trong CLAUDE.md). Theo câu trả lời Q1.
- Toàn bộ bài kiểm ở §8 của [`02`](./02-thiet-ke-ky-thuat.md).

**Điều kiện cần:** HQ0 xong.

**Điều kiện đủ — kiểm bằng đúng 5 tệp mẫu:**
- Nạp đủ 5 tệp → **đúng 18.243 dòng**, **đúng 7.651 dòng** mang cờ đã vá ngày.
- 5 lô phủ **5 khoảng ngày nối khít**: 02/01–28/02 · 01/03–30/04 · 01/05–30/06 · 01/07–31/08 · 03/09–17/09.
- Nạp lại riêng tệp 2 → lô mới có `deleted_count = 4.772`, tổng vẫn 18.243 (không nhân đôi).
- Hoàn tác lô của tệp 3 → còn **13.777** dòng; các lô khác không suy suyển.
- Ngày hợp đồng của mọi dòng **khớp nguyên văn** tệp gốc (canh cái bẫy vá nhầm cột).
- `test_pham_vi_khai_du_b07.py` xanh với số khóa tăng thêm 1.

**Đường lui:** chưa có màn hình nào dùng tới, gỡ migration là sạch.

## HQ2 — Tra cứu và biểu đồ trên bản cũ (≈ 3,5 ngày) — nhánh `main`, deploy prod

**Trạng thái: XONG MÃ 23/09/2026 (local) — bao-CR-470.** Màn `/customs-prices` năm thẻ (*Danh sách · Biểu đồ · Nhà nhập khẩu · So sánh · Pháp lý & thuế*), hộp nạp, hộp lịch sử + nhật ký lô, hộp chi tiết dòng; mục menu *Mua hàng → Tra cứu giá hải quan*. `tsc` giữ đúng 4 lỗi nền. **Chưa lên prod** — đang tạm dừng deploy prod (19/09), và bản gốc của luật "prod trước" chưa áp được. Số ATRAZINE sau khi gắn hoạt chất: **96 dòng** (92 khớp tên + 4 nhận ra qua hoạt chất), KGM 64 · LTR 30 · TNE 2 — xem đính chính ở §4 của [`04`](./04-giao-dien.md).

**Phạm vi:** T-01 · T-02 · T-03 · B-01 … B-04 trên `frontend/`.
- **API** (dùng chung cho cả hai giao diện về sau): danh sách dòng hàng (lọc + phân trang, đủ 32 cột) · thống kê theo kỳ `period = month | quarter | year` · danh sách cột · dải tháng đã phủ · chạy thử / áp dụng / hoàn tác lô.
- **Màn hình** theo §2 của [`04`](./04-giao-dien.md): màn tra cứu **hai thẻ Danh sách / Biểu đồ** (biểu đồ chỉ hiện khi đã lọc), hộp nạp dữ liệu, hộp *Lịch sử nạp* (bản cũ không có màn Quản lý Import), hộp chi tiết dòng hàng.
- **Biểu đồ vẽ SVG tay** theo khuôn `LineChart` / `BarChart` đang có trong `Reports.tsx` — **không thêm thư viện** vào bản cũ, và **không sửa `Reports.tsx`** (viết thành phần riêng trong trang mới).

**Điều kiện cần:** HQ1 xong trên `main`.

**Điều kiện đủ:**
- Gõ **ATRAZINE** → ra 92 dòng; biểu đồ **tách theo đơn vị** (KGM 60 · LTR 30 · TNE 2), không cộng lẫn.
- Giá bình quân gia quyền theo tháng **khớp tính tay** (bảng số liệu thật ở §4 của [`04`](./04-giao-dien.md)).
- **Tháng 7 hiện là khoảng trống**, không vẽ thành 0 và không nối đường qua.
- Câu độ tin cậy hiện đúng số dòng, số tháng, số năm dữ liệu.
- Người thiếu `customs_price.write` **không thấy** nút Nạp dữ liệu và nút Hoàn tác.
- `tsc` của `frontend/` giữ đúng **4 lỗi nền cũ**, không thêm.

**Đường lui:** ẩn mục menu là tắt được, dữ liệu và API không ảnh hưởng gì phân hệ khác.

## HQ3 — Port sang bản mới (≈ 2,5 ngày) — nhánh `erp-v2`, deploy dev

**Trạng thái: XONG MÃ 23/09/2026 (local)** — xem mục bao-CR-470 trong `change-log-bao.md` cho danh sách tệp và kết quả cổng kiểm.

**Phạm vi:** cùng bộ màn hình của HQ2 trên `frontend-v2/`, theo §3 của [`04`](./04-giao-dien.md).
- Gộp `main` → `erp-v2` trước (backend + migration đi theo).
- Trang trong phân hệ Thu mua; biểu đồ bằng `recharts` có sẵn; bảng 32 cột bằng `DataTable`; chi tiết dòng bằng ngăn kéo bên phải.
- **Lịch sử nạp dùng lại màn `/system/imports`** — chỉ cần thêm nhãn cho `ImportModule.CUSTOMS_DECLARATION` (bộ mã số gõ tay ở TypeScript, `gen_status_ts.py` không sinh cho bộ mã số).

**Điều kiện cần:** HQ2 chạy ổn trên prod.

**Điều kiện đủ:** lặp lại đúng các kịch bản của HQ2 trên `erp`; lô hải quan hiện ở `/system/imports` với đúng nhãn; cổng kiểm `frontend-v2` — typecheck 0 lỗi · lint 0 lỗi · vitest thư mục phân hệ vừa sửa xanh.

## HQ4 — Hoạt chất, nhà nhập khẩu, so sánh, xuất Excel (≈ 4 ngày) — có rủi ro

**Trạng thái: XONG MÃ 23/09/2026 (local).** Lượt đo trước đã chạy: nhận ra hoạt chất **51%** dòng (9.223 / 18.243), hàm lượng / dạng **93%** — đủ để làm tiếp. Ba nguồn theo thứ tự: 99 từ khóa tay → **tên hoạt chất bóc từ danh mục 6.919 thuốc BVTV, khớp nguyên từ** → tên thương mại. Nguồn thứ hai thêm vào sau khi đo: thiếu nó thì ATRAZINE chỉ nhận ra 65/92 dòng; nó cũng **gỡ 14 dòng thuốc kỹ thuật MESOTRIONE bị gắn nhầm ATRAZINE** chỉ vì tên hàng nhắc tới thành phẩm hỗn hợp mà nó dùng để pha. Danh mục BVTV nạp bằng `scripts/load_customs_catalogs.py`; câu hỏi "danh mục đó có được phép dùng và cập nhật định kỳ không" **vẫn mở**.

**Phạm vi:** T-04 · T-05 · T-06 · B-05. Bản cũ trước, bản mới sau, như mọi phase.

**⚠️ Điều kiện cần — một lượt đo trước (≈ 0,5 ngày, nằm trong ước lượng):** nạp danh mục 6.900+ thuốc BVTV (phần mềm ngoài lấy từ `danhmuc.thuocbvtv.com`) rồi **đo tỷ lệ tên hàng trên tờ khai nối được với một hoạt chất**. Số liệu ATRAZINE ([`04`](./04-giao-dien.md) §4) cho thấy cùng một từ khóa đang trộn nhiều dạng bào chế (thuốc kỹ thuật 97% với thành phẩm 80WP) — giá lệch nhau gấp đôi. Nối được hoạt chất **và hàm lượng** thì biểu đồ mới sạch.
- Tỷ lệ nối đủ cao → làm tiếp.
- Tỷ lệ thấp → **dừng T-04 và hỏi đại ca**, không cố ép: phương án thay là cho người dùng tự gắn nhãn hoạt chất cho kết quả tìm kiếm.
- Cũng phải hỏi: danh mục đó có được phép dùng và cập nhật định kỳ không.

**Điều kiện đủ:** tìm theo hoạt chất ra kết quả tách được theo hàm lượng; bảng xếp hạng nhà nhập khẩu gộp đúng theo mã số thuế; so sánh 2–5 từ khóa trên cùng một biểu đồ; xuất Excel theo khuôn xuất sẵn có.

**Cùng lúc xét lại:** bảng tổng hợp theo hoạt chất × tháng ([`02`](./02-thiet-ke-ky-thuat.md) §3.7) — **chỉ** thêm nếu đo được biểu đồ chậm hơn khoảng 1 giây.

## HQ5 — Trợ lý AI (≈ 2 ngày) — làm được ngay sau HQ3

**Trạng thái: A-01…A-03 XONG MÃ 23/09/2026 (local)** — tool `customs_price_stats` + `customs_buy_timing` (`assistant/tools/customs_tool.py`), độ tin cậy chấm theo số năm + số dòng, `recommended_month` chỉ xét tháng đủ `MIN_LINES_FOR_BEST = 5` dòng. **A-04:** bài HDSD dựng bằng `scripts/seed_help_customs_prices.py`, mới chạy ở local.

**Phạm vi:** A-01 … A-04.
- Tool tra giá theo kỳ + tool phân tích thời điểm mua, **đi qua khóa `customs_price`** như mọi tool khác.
- Tool trả về **số liệu kèm độ phủ** (bao nhiêu dòng, bao nhiêu tháng, bao nhiêu năm) để model lập luận trên số, không tự bịa số.
- Bài hướng dẫn sử dụng theo nếp các bài tool trợ lý đã có.

**Được thêm không tốn công:** bot Telegram (Agent Hub) chính là Trợ lý AI của web chạy ở Telegram — tool thêm cho trợ lý thì bot **tự có luôn**.

**Không phụ thuộc HQ4:** tra theo từ khóa đã đủ. Làm HQ4 trước thì trợ lý trả lời theo hoạt chất tốt hơn.

**Điều kiện đủ:**
- Hỏi *"ATRAZINE nên mua tháng nào"* → trả lời có số theo tháng **và** nói rõ chỉ có một năm dữ liệu.
- **Không** được kết luận "tháng 8 rẻ nhất" chỉ dựa trên 3 dòng — số liệu thật cho thấy đúng cái bẫy này ([`04`](./04-giao-dien.md) §4).
- Người không có quyền `customs_price` hỏi → trợ lý từ chối.

## HQ6 — Pháp lý và ngưỡng theo nghị định (≈ 5 ngày + chờ nghiệp vụ)

**Trạng thái: P-01 · P-03 · P-04 XONG MÃ 23/09/2026 (local); P-02 CHƯA.** Đính chính bản 1.0: phần mềm ngoài **CÓ** bảng ngưỡng — NĐ 24/2026 Phụ lục IV, 29 hóa chất kèm ngưỡng kg — nên không phải khai tay từ đầu: đã nạp vào `tab_customs_regulation` cùng PL1–PL3, hoạt chất cấm TT 75/2025 và danh sách phải công bố TT 01/2026, thêm màn sửa (khóa `customs_regulation`). Biểu thuế 2026 nạp vào `tab_customs_tariff` (15.115 mã). Thay cho P-02 là **cảnh báo lúc tra**: từ khóa trùng hóa chất cấm / có ngưỡng / phải công bố thì hiện dải cảnh báo. P-02 thật (so tồn kho với ngưỡng) vẫn chờ cầu nối VTBB ↔ hoạt chất.

**Phạm vi:** P-01 … P-04.

**⚠️ Điều kiện cần — không phải việc lập trình:**
- **Có người chịu trách nhiệm** cung cấp bảng ngưỡng theo từng nghị định và **cập nhật khi nghị định đổi**. Không có người này thì màn khai ngưỡng dựng xong sẽ nằm trống.
- **Đại ca xác nhận lại ranh giới.** P-02 (cảnh báo khi chạm ngưỡng) là chỗ **đầu tiên phải nối với tồn kho** — ngưỡng nói về lượng *đang giữ*. Ranh giới "không nối tồn kho" chốt ngày 23/09 áp cho HQ1–HQ5; tới HQ6 phải mở lại.
- Biểu thuế (P-04) là dữ liệu ngoài, đổi mỗi năm — cần chốt ai cập nhật.

**Điều kiện đủ:** khai được ngưỡng theo hoạt chất kèm căn cứ pháp lý; tồn kho chạm ngưỡng thì có cảnh báo; tra được nghĩa vụ theo tên / số CAS; tra được thuế suất theo mã HS.

---

## Tổng hợp ước lượng

| Phase | Ngày công | Nhánh | Chờ ai |
|---|---|---|---|
| HQ0 | 0,5 | — | Đại ca trả lời Q1 · Q3 · Q5 |
| HQ1 | 3 | `main` | |
| HQ2 | 3,5 | `main` → prod | Đại ca cho deploy prod |
| HQ3 | 2,5 | `erp-v2` → dev | |
| HQ4 | 4 | cả hai | Tỷ lệ nối hoạt chất đủ cao |
| HQ5 | 2 | cả hai | |
| HQ6 | 5 | cả hai | Người cung cấp bảng ngưỡng |
| **Cộng** | **≈ 20,5** | | |
