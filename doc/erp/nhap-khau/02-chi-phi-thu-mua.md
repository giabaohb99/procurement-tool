# 02 · CHI PHÍ THU MUA — THIẾT KẾ bao-CR-453

| | |
|---|---|
| **Phiên bản** | **v1.1** · 22/09/2026 (v1.0 sáng cùng ngày = bản thiết kế) |
| **Loại tài liệu** | Thiết kế (PRD + TDD gộp) — chốt trước khi code |
| **Nguồn yêu cầu** | Đại ca nêu 21/09/2026 khi bàn giá đơn nhập khẩu (*"tách ra riêng thành 1 chức năng giá trị khác... 1 dòng có thể có 3 cột giá"*). Bản đánh giá + bảy điểm chờ quyết ở `doc/erp/19-viec-con-lai-tong-hop.md` §5 |
| **Xây trên** | Thẻ *Chi phí lô hàng nhập khẩu* của ĐMH (bao-CR-319 P3..P5, bao-CR-347) — `tab_po_import_cost`, công nợ `source_type = import_cost`, phân bổ 5 cách, báo cáo giá vốn `report/import_landed_cost.py`. Đặc tả hiện hành: `doc/tai-lieu-chuc-nang/04-don-mua-hang.md` mục K |
| **CR** | `bao-CR-453-chi-phi-thu-mua` (đặt chỗ 21/09/2026, dòng đầu `change-log-bao.md`) |
| **Trạng thái** | **ĐÃ CODE ĐỦ NĂM ĐỢT GĐ1..GĐ5 ngày 22/09/2026** theo lệnh khách *"làm xong 1 lần rồi commit luôn... làm đủ giai đoạn rồi đẩy lên 1 lượt"* — một commit, lên **dev**. Prod tạm dừng deploy (19/09), chưa lên. Đặc tả hiện hành sau khi code: `doc/tai-lieu-chuc-nang/04-don-mua-hang.md` mục K (K.0 → K.7); tài liệu này giữ làm bản thiết kế + lý do |

---

## 0. Bảy điểm đã chốt

Đại ca chốt điểm (1) sau khi duyệt bản phác màn hình ngày 22/09/2026; sáu điểm còn lại chốt cùng ngày theo đúng phương án đề xuất (*"theo em đề xuất, viết thiết kế CR-453 đi"*).

| # | Câu hỏi | Đáp án đã chốt | Hệ quả thiết kế |
|---|---|---|---|
| 1 | Tên + nhãn cột + bố cục | **«Chi phí thu mua»** (khớp TK 1562 *Chi phí thu mua hàng hóa*, Thông tư 200). Ba cột **Dự toán / Tạm tính / Quyết toán**. Khối nằm trong chi tiết ĐMH, cho **mọi loại đơn** | Mục 4, 5 |
| 2 | Nới bảng cũ hay bảng mới; gom phí vận chuyển không | **Nới tại chỗ, đổi tên bảng** `tab_po_import_cost` thành `tab_po_cost`. Phí vận chuyển **giữ nguyên chỗ** trên lần giao, khối mới chỉ **hiện thêm như một dòng chỉ xem** | Mục 6.1, 6.4 |
| 3 | Ai quản danh mục loại chi phí, loại nào sinh công nợ | 15 mã sẵn có thành **dòng seed** của bảng danh mục mới; **quản trị thêm bớt**; **mọi loại đều sinh công nợ trừ loại đánh dấu «không sinh»** | Mục 6.2, 7 |
| 4 | Công nợ sinh ở giai đoạn nào | **Chỉ ở Quyết toán** | Mục 5.4 |
| 5 | Ai bấm Chốt, có mở lại được không | `purchase_order.write` **chốt**; **mở lại** chỉ vai trò có `purchase_order.approve`, **bắt ghi lý do** | Mục 5.3, 7 |
| 6 | Giá hàng ba giai đoạn làm chung hay tách | **Tách CR sau.** bao-CR-453 chỉ làm chi phí, không đụng đơn giá dòng hàng | Mục 3 (KHÔNG làm) |
| 7 | Tỷ giá mỗi giai đoạn một số hay chung | **Mỗi giai đoạn một tỷ giá** | Mục 6.1 |

---

## 1. Vì sao cần

Thẻ chi phí hiện tại (bao-CR-319) chỉ có ở **đơn nhập khẩu**, và mỗi dòng chi phí chỉ giữ **một con số**. Cờ *Dự kiến / Thực tế* của bao-CR-347 đã bị bỏ khỏi màn hình ngày 10/09/2026 vì hai số mà nằm ở **hai dòng khác nhau** thì không so được với nhau, và thu mua phải xóa dòng dự kiến rồi gõ lại dòng thực tế.

Thực tế mua hàng đi qua ba bước: **dự toán** lúc lập đơn để chốt giá bán, **tạm tính** khi có báo giá dịch vụ hoặc tờ khai, **quyết toán** khi hóa đơn về. Ba bước này cần nằm **cạnh nhau trên cùng một dòng** để:

1. Thấy ngay khoản nào **lệch** so với dự toán và lệch bao nhiêu.
2. **Công nợ chỉ hiện ra khi đã quyết toán**, không đòi trả khoản chưa có hóa đơn.
3. Đơn **trong nước** cũng có chi phí (vận chuyển nội địa, bốc xếp, lưu kho, kiểm định) mà hiện không có chỗ ghi ngoài ô Ghi chú.

Chi phí thu mua **chỉ ảnh hưởng giá vốn sản phẩm, không đổi giá đơn hàng** — giữ đúng ranh giới của bao-CR-319.

---

## 2. Mục tiêu — bốn câu hỏi màn hình phải trả lời được

1. **Đơn này dự toán bao nhiêu, thực chi bao nhiêu, lệch bao nhiêu?** — ba cột và cột Lệch trên từng dòng, bốn ô tổng dưới bảng.
2. **Đơn đang ở giai đoạn nào, ai chốt, khi nào?** — dải giai đoạn trên đầu khối, nhật ký lấy từ audit.
3. **Khoản nào đã thành công nợ, còn phải chi bao nhiêu?** — như hôm nay, nhưng chỉ tính trên cột Quyết toán.
4. **Mỗi dòng hàng gánh bao nhiêu chi phí, theo giai đoạn nào?** — khối *Chi phí theo dòng hàng* có nút chọn giai đoạn.

---

## 3. Phạm vi

### Làm

- Đổi tên và nới bảng chi phí cho **mọi loại đơn** (trong nước + nhập khẩu).
- Một dòng chi phí ba bộ số (tiền nguyên tệ, tỷ giá, quy đổi) cho ba giai đoạn.
- Giai đoạn hiện hành ở **cấp đơn**, cột hiện hành gõ được, cột đã qua khóa; hai nút **Chốt tạm tính** / **Chốt quyết toán**; **Mở lại** có lý do.
- **Quyết toán riêng một dòng** khi hóa đơn về sớm.
- Công nợ, chặn Hoàn thành, phân bổ, bản in, báo cáo giá vốn đọc theo giai đoạn.
- Danh mục **Loại chi phí thu mua** người dùng quản, seed từ 15 mã sẵn có.
- Migration đưa dữ liệu cũ về đúng cột, đơn cũ coi như đã quyết toán.
- Giao diện v1 trước, port v2 sau; bài HDSD; bộ test.

### KHÔNG làm (cố ý)

- **Giá hàng ba giai đoạn** (đơn giá dòng ĐMH nhập khẩu) — CR riêng sau, theo điểm (6).
- **Gộp phí vận chuyển của lần giao vào bảng chi phí.** Phí đó là công nợ `source_type = shipping` theo từng lần giao, có luồng YCTT riêng; gom vào là phá khớp nợ với YCTT đã chi. Khối mới chỉ hiện nó như dòng chỉ xem (mục 6.4).
- **Tính giá vốn / giá nhập kho, ghi kết quả phân bổ xuống cột.** Vẫn ranh giới của bao-CR-319: hệ chưa có phân hệ hóa đơn.
- **Đổi tên mã nguồn lịch sử** ở ba chỗ: `source_type = import_cost` trên `tab_payable` (đang nằm trong dữ liệu prod), khóa `import_costs` / `import_cost_summary` / `import_cost_allocation` của API chi tiết ĐMH (hai giao diện cùng đọc, đổi là gãy v2 trước khi port). Chỉ đổi **nhãn** người dùng thấy. Ghi rõ ở mã là "tên lịch sử".
- **Lịch sử ba cột theo từng lần sửa** — lấy từ `tab_change_log` (bao-CR-402) sẵn có, không dựng bảng lịch sử riêng.
- Custom-field engine, gõ tay tỷ lệ phân bổ, nhiều mã chỉ định: giữ nguyên như K.2.

---

## 4. Khái niệm

| Khái niệm | Định nghĩa |
|---|---|
| **Chi phí thu mua** | Mọi khoản chi ngoài giá hàng để đưa hàng về kho: cước, phí cảng, thuế nhập, kiểm định, bảo hiểm, vận chuyển nội địa, lưu kho, khoản khác do người dùng khai. |
| **Giai đoạn** (`CostStage`) | `1` Dự toán · `2` Tạm tính · `3` Quyết toán. Đơn có **giai đoạn hiện hành** (`PurchaseOrder.cost_stage`). |
| **Cột hiện hành** | Cột của giai đoạn hiện hành: tô nền, gõ được. Cột trước đó **khóa**. Cột sau đó **mờ**, chưa gõ. |
| **Chốt** | Chuyển đơn sang giai đoạn kế: Dự toán → Tạm tính (*Chốt tạm tính*), Tạm tính → Quyết toán (*Chốt quyết toán*). Ô trống ở cột mới được **chép số cột trước sang**. |
| **Mở lại** | Lùi đơn về giai đoạn trước, cần `purchase_order.approve` và lý do. Dòng đã có tiền chi **không lùi** (mục 5.3). |
| **Quyết toán riêng dòng** | Một dòng được đưa lên Quyết toán trước cả đơn (`line_stage = 3`) khi hóa đơn về sớm. Giai đoạn **hiệu lực** của dòng = max(giai đoạn đơn, giai đoạn dòng). |
| **Số hiệu lực** | Số của giai đoạn hiệu lực cao nhất **đã có số** trên dòng. Dùng cho bản in, cột Lệch và báo cáo khi người dùng không chỉ định giai đoạn. |
| **Lệch** | Số hiệu lực (quy đổi) trừ Dự toán (quy đổi). Dòng chưa có Dự toán thì Lệch để trống, không coi là lệch 100 %. |
| **Loại chi phí** | Dòng danh mục `tab_po_cost_type`, mã số SMALLINT, người dùng thêm bớt. Mỗi loại khai: nhóm (thuế / dịch vụ), có sinh công nợ không, NCC mặc định, cách phân bổ mặc định, VAT mặc định. |

---

## 5. Danh sách chức năng

Mã chức năng: **A** khối trên chi tiết ĐMH · **B** giai đoạn · **C** công nợ và hoàn thành · **D** phân bổ, bản in, báo cáo · **E** danh mục · **F** dữ liệu cũ.

### 5.1 A — Khối «Chi phí thu mua» trên chi tiết ĐMH

| Mã | Chức năng | Luật |
|---|---|---|
| A01 | Khối hiện cho **mọi loại đơn**, ngay dưới bảng Dòng hàng, thay thẻ *Chi phí lô hàng nhập khẩu* | Đơn trong nước chưa có dòng nào thì khối thu gọn còn một dòng tiêu đề + nút *Thêm chi phí*, không chiếm chỗ. |
| A02 | Dải giai đoạn trên đầu khối: ba bước, bước hiện hành tô đậm, kèm ngày và người chốt của bước đã qua | Ngày / người đọc từ audit (mã hành động mục 6.5). Đơn cũ migration ghi "chốt tự động khi nâng cấp". |
| A03 | Bảng chi phí, mỗi dòng một khoản của một NCC | Cột: **#** · Loại chi phí · Diễn giải · NCC · Tiền tệ · **Dự toán** · **Tạm tính** · **Quyết toán** · **Lệch** · VAT % · Đã chi · Còn lại · Số HĐ · Ngày HĐ · Hạn TT · Cách phân bổ · Mã chỉ định · Ghi chú · Hành động. Cột *Cách phân bổ* vẫn nằm gần đầu như K.1 để khỏi khuất; ba cột tiền đặt trước VAT vì đó là thứ người ta nhìn đầu tiên. |
| A04 | Mỗi ô giai đoạn hiện **số nguyên tệ**, dòng phụ nhỏ bên dưới hiện **tỷ giá** và **số quy đổi** | Cùng tiền tệ VNĐ thì dòng phụ ẩn. Tỷ giá gõ ở popup chi tiết (A07) hoặc bấm vào dòng phụ. |
| A05 | Ô của **cột hiện hành** gõ được và tô nền; cột đã qua khóa (chỉ xem); cột chưa tới mờ | Dòng đã *Quyết toán riêng* thì cột Quyết toán của dòng đó gõ được dù đơn mới ở Tạm tính, hai cột kia khóa. |
| A06 | Cột **Lệch** = số hiệu lực quy đổi trừ Dự toán quy đổi, kèm % | Tô đỏ khi vượt dự toán, xanh khi thấp hơn, trống khi chưa có Dự toán. |
| A07 | Popup *Chi tiết chi phí #n* (cây bút) bày đủ trường theo form hai cột, ba khối giai đoạn mỗi khối: số tiền nguyên tệ · tỷ giá · quy đổi · trạng thái (đã chốt / hiện hành / chưa tới) | Dùng chung state với bảng như K.2. Vẫn phải bấm **Lưu của đơn**. |
| A08 | Bốn ô tổng dưới bảng: **Dự toán** · **Tạm tính** · **Quyết toán** · **Lệch** (quyết toán hoặc số hiệu lực trừ dự toán, kèm %) | Thay dải năm thẻ của K.3. *Tiền hàng quy đổi*, *Đã chi*, *Còn phải chi*, *Tổng giá trị lô hàng* dồn xuống một dòng nhỏ dưới bốn ô; *Đã chi / Còn phải chi* chỉ hiện khi đã có công nợ (như K.3). |
| A09 | Dòng chỉ xem **Phí vận chuyển (theo lần giao)** cuối bảng, nền xám | Cộng `shipping_amount` của các lần giao; chỉ điền cột Quyết toán, hai cột kia hiện "—". **Không cộng vào bốn ô tổng** (nó đã có công nợ và YCTT riêng), có chú thích một dòng. |
| A10 | Nút **Tạo YCTT**, tick dòng, khối *Thanh toán chi phí theo NCC* giữ nguyên cách làm K.4 | Chỉ dòng đã quyết toán và đã thành công nợ mới tick được. |
| A11 | Bảng **mở cả khi đơn đã duyệt** như K.1 | Khóa `import_costs` vẫn nằm ngoài `block_edit_approved_order`. Đơn *Hoàn thành* / *Hủy* thì chỉ xem. |
| A12 | Nhãn người dùng thấy đổi hết sang *Chi phí thu mua*: thẻ, tab YCTT, màn Công nợ, dashboard NCC, xuất Excel | `frontend/src/utils/payable.ts`, `payable/export.py`, `PAY_TABS`. Mã `import_cost` giữ (mục 3). |

### 5.2 B — Giai đoạn và chốt

| Mã | Chức năng | Luật |
|---|---|---|
| B01 | Đơn mới tạo ở **Dự toán** (`cost_stage = 1`) bất kể loại đơn | Không ép đơn trong nước phải qua đủ ba bước: đơn không có dòng chi phí thì giai đoạn vô hại. |
| B02 | Nút **Chốt tạm tính** (Dự toán → Tạm tính) | Cần `purchase_order.write`. Với mỗi dòng: ô Tạm tính trống thì chép **số tiền + tỷ giá** Dự toán sang; đã có số thì giữ. Lưu bảng trước rồi chốt (một request, mục 6.6). |
| B03 | Nút **Chốt quyết toán** (Tạm tính → Quyết toán) | Cần `purchase_order.write`. Chép Tạm tính sang ô Quyết toán trống. Ngay sau đó chạy đồng bộ công nợ (C01). Hộp xác nhận liệt kê **số dòng sẽ thành công nợ** và **số dòng chưa có NCC** (sẽ không thành nợ). |
| B04 | Chốt thẳng từ Dự toán lên Quyết toán | **Cho phép** bằng hai lần bấm liên tiếp hoặc một request `target = 3`: hệ chép Dự toán → Tạm tính → Quyết toán theo đúng thứ tự, ghi hai dòng audit. Đơn nhỏ trong nước không cần đi qua Tạm tính bằng tay. |
| B05 | **Quyết toán riêng dòng** (menu Hành động → *Quyết toán dòng này*) | Cần `purchase_order.write`, chỉ khi đơn chưa ở Quyết toán. Đặt `line_stage = 3`, chép số hiệu lực sang ô Quyết toán nếu trống, đồng bộ công nợ cho riêng dòng đó. |
| B06 | **Mở lại** (Quyết toán → Tạm tính, hoặc Tạm tính → Dự toán) | Cần `purchase_order.approve`. Bắt **lý do ≥ 10 ký tự**, ghi vào audit. Dòng có công nợ **đã chi một phần** thì **giữ nguyên `line_stage = 3`** và nợ; các dòng khác gỡ nợ chưa chi (như luật hủy đơn K.4 mục 6). Số ở cột đã mở không xóa, chỉ mở khóa. |
| B07 | Mở lại một dòng đã quyết toán riêng | Cùng quyền và lý do như B06, chặn nếu dòng đã chi. |
| B08 | Mọi thao tác B ghi **audit** với mã hành động mục 6.5 và **thông báo chuông** cho người tạo đơn + người xử lý đơn | Dùng kênh thông báo sẵn có của ĐMH, không thêm loại thông báo mới. |

### 5.3 C — Công nợ, Yêu cầu thanh toán, Hoàn thành đơn

| Mã | Chức năng | Luật |
|---|---|---|
| C01 | Công nợ chỉ sinh từ **cột Quyết toán** của dòng có giai đoạn hiệu lực = 3 | Thay `is_actual_cost` bằng `is_final_cost(row, po)`. Điều kiện còn lại giữ nguyên K.4: đơn ở `IMPORT_COST_PAYABLE_STATUSES`, có NCC, quy đổi > 0. `amount` nợ = `final_amount × final_rate`, `vat` = phần thuế, `total` = `final_base`. |
| C02 | Sửa số Quyết toán của dòng đã có nợ | Cập nhật cùng khoản nợ (khóa `ref_id`), như K.4 mục 4. Dòng đã chi nhiều hơn số mới → **400** "đã chi X, không hạ dưới số đã chi". |
| C03 | Xóa dòng | Như K.4 mục 5: đã chi thì cấm. Dòng chưa chi nhưng đã quyết toán: xóa được, gỡ nợ. |
| C04 | **Hoàn thành đơn** | Đơn **có ít nhất một dòng chi phí** thì phải ở **Quyết toán** mới Hoàn thành được (400 "Chốt quyết toán chi phí trước khi Hoàn thành"). Đơn không có dòng nào: không chặn, và khi Hoàn thành hệ **tự đặt `cost_stage = 3`** cho gọn. Đơn **nhập khẩu** giữ thêm luật chặt K.4 mục 8 (trả đủ mới Hoàn thành), xét trên cột Quyết toán. Đơn trong nước **không** thêm luật trả đủ. |
| C05 | Hộp xác nhận Hoàn thành nhắc trước: giai đoạn hiện hành, số dòng chưa quyết toán, còn phải chi | Từ `import_cost_summary` (giữ tên khóa). |
| C06 | YCTT | Không đổi: tab *Chi phí thu mua* (đổi nhãn), ba đường tạo YCTT của K.4. Khớp nợ theo `payable_id` như cũ. |

### 5.4 D — Phân bổ, bản in, báo cáo

| Mã | Chức năng | Luật |
|---|---|---|
| D01 | `allocate_import_costs(items, costs, stage)` nhận thêm **giai đoạn**, chia theo `<stage>_base` của từng dòng | Dòng không có số ở giai đoạn đó thì không tham gia. Cách chia và luật lùi giữ nguyên K.2. Cách 5 *Nhập tay*: `manual_allocation` là **một bộ số dùng chung** cho ba giai đoạn (tổng phải khớp `final_base` nếu đã quyết toán, nếu chưa thì khớp số hiệu lực); không đẻ ba bộ nhập tay. |
| D02 | Khối **Chi phí theo dòng hàng** có nút chọn giai đoạn (ba nút một hàng), mặc định = giai đoạn hiện hành của đơn | API trả `import_cost_allocation` cho **cả ba** giai đoạn (`{"1": ..., "2": ..., "3": ...}`) để đổi nút không gọi lại server. Giai đoạn chưa có số nào thì nút mờ. |
| D03 | Bản in **In Đơn nhập khẩu** khối B, C, D đọc **số hiệu lực**, tiêu đề khối ghi rõ "(Quyết toán)" / "(Tạm tính)" / "(Dự toán)" | Không in ba cột trên bản in này; bản in là chứng từ một giai đoạn. |
| D04 | Báo cáo **Giá vốn nhập khẩu** (`report/import_landed_cost.py`, tab ở Báo cáo mua hàng) nhận ô lọc **Giai đoạn** (mặc định Quyết toán, có lựa *Số hiệu lực*) | Bảng theo đơn và theo dòng hàng tính bằng cột giai đoạn đã chọn. Excel hai sheet thêm dòng ghi giai đoạn. |
| D05 | Tab mới **So sánh ba giai đoạn** trong cùng báo cáo: mỗi đơn một dòng, mỗi loại chi phí ba cột + Lệch, tổng cuối | Chỉ dòng có Dự toán mới tính %. Xuất Excel. |
| D06 | Báo cáo mở cho **cả đơn trong nước có dòng chi phí** | `_pick_orders` bỏ điều kiện `order_type = IMPORT` khi người dùng tick *Gồm đơn trong nước*; mặc định vẫn nhập khẩu để số cũ không đổi. Tên tab giữ *Giá vốn nhập khẩu* đợt này; đổi tên tab là việc của HDSD sau. |

### 5.5 E — Danh mục Loại chi phí thu mua

| Mã | Chức năng | Luật |
|---|---|---|
| E01 | Màn danh mục **Loại chi phí thu mua** trong nhóm Danh mục | Quyền mới `purchase_cost_type` (read/write), seed cho `admin` và `pur_manager`. Một khóa = một màn hình (CR-157). |
| E02 | Trường: mã số (tự cấp, chỉ xem) · tên · nhóm (`1` Thuế nộp ngân sách · `2` Dịch vụ) · **sinh công nợ** (mặc định bật) · NCC mặc định · cách phân bổ mặc định · VAT % mặc định · thứ tự · đang dùng | Nhóm Thuế thì NCC mặc định gợi `NSNN` như K.1. |
| E03 | 15 mã sẵn có (1..14, 99) là dòng seed, **giữ nguyên số** vì đã nằm trong dữ liệu prod | Migration chèn. `99 Chi phí khác` không xóa, không tắt được. |
| E04 | Loại đã dùng trên dòng chi phí nào thì **không xóa**, chỉ **tắt** | Dòng cũ vẫn hiện tên; ô chọn trên bảng chi phí chỉ liệt kê loại đang dùng, dòng đang mang loại đã tắt vẫn hiện tên kèm "(đã tắt)". |
| E05 | Loại **không sinh công nợ** | Dòng mang loại này không thành `tab_payable`, không chặn Hoàn thành, nhưng vẫn vào tổng chi phí và phân bổ. Dùng cho khoản đã trả ngoài hệ thống (ứng tiền mặt, khoản nội bộ). |
| E06 | Chọn loại trên bảng chi phí tự điền NCC mặc định, cách phân bổ, VAT nếu ô đang trống | Không ghi đè ô đã gõ. |
| E07 | Trợ lý AI: tool `search_docs` / tra cứu sẵn có tự thấy vì đọc HDSD; **không thêm tool** đợt này | Ghi để khỏi hỏi lại. |

### 5.6 F — Dữ liệu cũ

| Mã | Luật |
|---|---|
| F01 | Dòng `cost_status = 2` (Thực tế) hoặc trống: `amount / exchange_rate / base_amount` chép sang **ba cột Quyết toán**, hai cột kia trống, `line_stage = 3`. |
| F02 | Dòng `cost_status = 1` (Dự kiến, sót từ đợt thử nghiệm): chép sang **cột Dự toán**, hai cột kia trống, `line_stage = 1`. |
| F03 | Đơn có ít nhất một dòng chi phí, hoặc đang ở `completed` / `cancelled` / `rejected`: `cost_stage = 3`. Đơn còn lại: `cost_stage = 1`. |
| F04 | Công nợ `import_cost` hiện có **không đụng**: dòng F01 vẫn là dòng đã quyết toán nên `sync` chạy lại cho ra đúng khoản nợ cũ. Kiểm bằng test đếm số khoản nợ trước và sau. |
| F05 | Không có dòng audit chốt cho đơn cũ; dải giai đoạn A02 hiện "Chốt khi nâng cấp 453" thay cho ngày và người. |

---

## 6. Thiết kế kỹ thuật

### 6.1 Bảng `tab_po_cost` (đổi tên từ `tab_po_import_cost`, ORM `POCost`)

Migration `op.rename_table` (revision `05a62d38a47a`); ORM đổi tên lớp `POImportCost` → `POCost`. Alias `POImportCost = POCost` chỉ sống trong lúc code GĐ1, **đã gỡ ở GĐ4** cùng đợt.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `po_id`, `cost_type`, `description`, `supplier_code`, `supplier_name`, `currency`, `vat`, `allocation_method`, `allocation_target`, `manual_allocation`, `invoice_no`, `invoice_date`, `payment_due_date`, `note` | như cũ | `cost_type` nay là **mã trong `tab_po_cost_type`**, không còn là IntEnum cứng; enum `ImportCostType` giữ để nhãn dự phòng khi thiếu danh mục. `vat` và `currency` là **một số cho cả ba giai đoạn**. |
| `estimate_amount` · `provisional_amount` · `final_amount` | Numeric(18,2), NULL = chưa có số | Tiền **nguyên tệ trước thuế** từng giai đoạn. Phân biệt NULL (chưa gõ) với 0 (gõ 0 thật) vì luật chép sang chỉ chép vào ô NULL. |
| `estimate_rate` · `provisional_rate` · `final_rate` | Numeric(18,6), default 1 | Điểm (7): mỗi giai đoạn một tỷ giá. `rate_of(row)` sẵn có đọc `exchange_rate` → thêm `cost_rate_of(row, stage)`. |
| `estimate_base` · `provisional_base` · `final_base` | Numeric(18,2), NULL | = `amount × (1 + vat/100) × rate`, tính server (`cost_base_of(row, stage)`), lưu để báo cáo cộng bằng IN như hôm nay. **Không** đặt tên có hậu tố tiền tệ (B.32). |
| `line_stage` | SMALLINT `CostStage`, default 1 | Giai đoạn riêng của dòng; hiệu lực = max(đơn, dòng). Chỉ nhận 3 (quyết toán riêng) hoặc 1. |
| **Bỏ** `amount`, `exchange_rate`, `base_amount`, `cost_status` | | Bỏ hẳn sau khi chép (F01, F02) để không còn hai nguồn sự thật. `downgrade` tạo lại và chép ngược từ cột hiệu lực; `cost_status` = 2 nếu `final_amount` có số, 1 nếu chỉ có Dự toán. |

Index thêm: `(po_id, line_stage)`.

### 6.2 Bảng mới `tab_po_cost_type`

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `code` | SMALLINT, unique | 1..14, 99 seed; mã mới cấp từ 15 trở lên, bỏ qua 99. |
| `name` | String(100) | |
| `group_kind` | SMALLINT `CostTypeGroup`: `1` Thuế nộp ngân sách · `2` Dịch vụ | Seed: 4, 5, 6, 7 = 1, còn lại = 2 (khớp `TAX_COST_TYPES`). |
| `creates_payable` | Boolean, default true | E05. |
| `default_supplier_code` | String(50), default "" | Seed `NSNN` cho nhóm thuế. |
| `default_allocation_method` | SMALLINT, default 1 | |
| `default_vat` | Numeric(5,2), default 0 | |
| `sort_order` | Integer | Seed = code, 99 cuối. |
| `is_active` | Boolean, default true | |

Module đặt ở `modules/purchase_order/cost_type.py` (model + service + router `/api/po-cost-types`) thay vì `modules/catalog`, vì nó lệ thuộc hoàn toàn vào ĐMH. Quyền `purchase_cost_type` khai ở `core/permissions.ENTITIES` + `ENTITY_LABELS`, `core/scoping.py` = `PUBLIC` (danh mục, không lọc theo dòng); test đếm ENTITIES == SCOPE_FIELDS tự nhắc nếu thiếu.

### 6.3 `PurchaseOrder`

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `cost_stage` | SMALLINT `CostStage`, default 1 | Giai đoạn hiện hành của đơn. Ngày, người, lý do lấy từ audit (6.5), **không thêm cột**. |

`CostStage` và `CostTypeGroup` khai ở `purchase_order/model.py` cạnh `AllocationMethod`, kèm `COST_STAGE_LABELS`.

### 6.4 Phí vận chuyển

Không đụng `PODelivery.shipping_unit_price / shipping_amount`, không đụng công nợ `shipping`. Controller `_out` trả thêm `import_cost_summary.shipping_total` (tổng `shipping_amount` các lần giao) để giao diện vẽ dòng A09.

### 6.5 Mã hành động (audit) — khai ở `core/action_catalog.py`

| Mã | Nhãn | Nhóm |
|---|---|---|
| `cost_stage_prov` | Chốt tạm tính chi phí thu mua | EDIT — mã ≤ 20 ký tự nên viết tắt |
| `cost_stage_final` | Chốt quyết toán chi phí thu mua | APPROVE |
| `cost_stage_reopen` | Mở lại giai đoạn chi phí thu mua | APPROVE — `note` = lý do |
| `cost_line_final` | Quyết toán riêng một dòng chi phí | EDIT — `doc_code` = mã đơn, `note` = "#id dòng" |
| `cost_line_reopen` | Mở lại một dòng chi phí đã quyết toán | APPROVE |

`tab_change_log` (bao-CR-402) tự ghi trước/sau cho `POCost` vì đi qua ORM; không cần cấu hình thêm.

### 6.6 API

Giữ nguyên các khóa lịch sử trong `GET /api/purchase-orders/{id}` và payload `PATCH`:

- `import_costs[]` mỗi phần tử thêm: `estimate_amount / estimate_rate / estimate_base`, `provisional_*`, `final_*`, `line_stage`, `effective_stage`, `effective_base`, `variance_base`, `variance_pct`, `cost_type_name`, `creates_payable`. Bỏ `cost_status`, `cost_status_label`, `amount`, `exchange_rate`, `base_amount`.
- `import_cost_summary` thêm: `estimate_total`, `provisional_total`, `final_total`, `effective_total`, `variance_total`, `variance_pct`, `shipping_total`, `stage`, `stage_label`, `lines_not_final`, `lines_without_supplier`. `cost_total` = `effective_total` (giữ tên để bản in và YCTT không gãy).
- `import_cost_allocation` đổi từ một bộ thành `{"1": ..., "2": ..., "3": ...}`; giao diện v1 và v2 sửa cùng lượt (v2 chỉ đọc khóa này ở `purchase-order-import-costs-card.tsx`, sửa nhỏ ngay GĐ2 để dev không gãy, port đầy đủ ở GĐ4).
- `PATCH` với `import_costs[]`: server chỉ nhận số ở **cột hiệu lực** của từng dòng; số gửi lên cho cột đã khóa bị **bỏ qua và ghi warning** (không 400, để lưu tự động của bảng không kẹt).

Mới:

| Method | Đường dẫn | Body | Quyền |
|---|---|---|---|
| `POST` | `/api/purchase-orders/{id}/cost-stage/advance` | `{ "target": 2 \| 3, "import_costs": [...] }` (bảng gửi kèm để lưu rồi chốt trong một transaction) | `purchase_order.write` |
| `POST` | `/api/purchase-orders/{id}/cost-stage/reopen` | `{ "target": 1 \| 2, "reason": "..." }` | `purchase_order.approve` |
| `POST` | `/api/purchase-orders/{id}/costs/{cost_id}/finalize` | rỗng | `purchase_order.write` |
| `POST` | `/api/purchase-orders/{id}/costs/{cost_id}/reopen` | `{ "reason": "..." }` | `purchase_order.approve` |
| `GET/POST/PATCH` | `/api/po-cost-types`, `/api/po-cost-types/{id}` | danh mục | `purchase_cost_type.read/write` |
| `GET` | `/api/reports/import-landed-cost?stage=1\|2\|3\|effective&include_domestic=1` | | `report.read` (như cũ) |

### 6.7 Service (`purchase_order/service.py`)

- `cost_rate_of(row, stage)`, `cost_base_of(row, stage)`, `effective_stage_of(row, po)`, `effective_base_of(row, po)`.
- `is_final_cost(row, po)` thay `is_actual_cost`; `final_costs(rows, po)` thay `actual_costs`.
- `advance_cost_stage(db, po, target, user_id)`: kiểm target > hiện hành; với từng bước chép ô NULL; ghi audit từng bước; gọi `sync_import_cost_payables`.
- `reopen_cost_stage(db, po, target, reason, user_id)`: kiểm quyền và lý do; dòng có `paid_amount > 0` giữ `line_stage = 3`; gỡ nợ chưa chi của dòng khác; audit.
- `finalize_cost_line` / `reopen_cost_line`.
- `block_complete_not_final_costs(db, po)` (C04) gọi trước `block_complete_unpaid_import_costs`; hàm sau đổi sang đọc cột Quyết toán.
- `sync_import_cost_payables`: đọc `final_*`, thêm điều kiện `creates_payable` của loại.
- `_save_import_costs`: kiểm loại còn `is_active` (hoặc là loại dòng đang mang), chỉ ghi cột hiệu lực, tính lại ba `_base`, kiểm `manual_allocation` khớp số hiệu lực.
- `allocate_import_costs(items, costs, stage)`.

### 6.8 Migration (một tệp, revision mới, `down_revision` = head hiện hành lúc code — kiểm bằng `alembic heads`)

1. Tạo `tab_po_cost_type`, seed 15 dòng.
2. `rename_table tab_po_import_cost → tab_po_cost`.
3. Thêm 9 cột giai đoạn + `line_stage`; `tab_purchase_order.cost_stage`.
4. Chép dữ liệu bằng SQL: F01, F02 (theo `cost_status`), F03 cho đơn.
5. Bỏ `amount`, `exchange_rate`, `base_amount`, `cost_status`.
6. `downgrade` làm ngược, chép từ cột hiệu lực về; **không** xóa `tab_po_cost_type` nếu có mã ≥ 15 đang được dùng (in cảnh báo và giữ bảng).

Ghi mô tả trường vào data dictionary theo luật "mỗi migration một ghi chú" (hẹn 06-07/09).

### 6.9 Giao diện v1 (`frontend/src/pages/PurchaseOrderDetail.tsx`)

- Thẻ đổi tên, bỏ điều kiện `isImport`; thêm dải giai đoạn + hai nút; bảng thêm ba cột giai đoạn + Lệch, bỏ cột Số tiền / Tỷ giá / Quy đổi cũ; popup chi tiết ba khối giai đoạn; bốn ô tổng; dòng phí vận chuyển chỉ xem; nút chọn giai đoạn ở *Chi phí theo dòng hàng*; hộp xác nhận Hoàn thành thêm dòng giai đoạn.
- `COST_ACTUAL = 2` và mọi nhánh `cost_status` gỡ.
- Màn danh mục mới `frontend/src/pages/POCostTypes.tsx` (bảng + popup, theo mẫu màn Đơn vị tính), menu Danh mục, route, quyền `purchase_cost_type`.
- Nhãn: `utils/payable.ts` "Chi phí nhập khẩu" → "Chi phí thu mua"; `PAY_TABS`.
- `ImportLandedCostReport.tsx`: ô lọc giai đoạn, tick đơn trong nước, tab so sánh.
- Đây là **ngoại lệ có chủ đích** của D-026 (frontend/ đóng băng) theo luật *v1 trước rồi mới port v2* (08/09).

### 6.10 Port v2 (GĐ4)

17 tệp đang nhắc `import_cost` trong `frontend-v2/src/modules/procurement` và `finance` (đã liệt kê bằng grep 22/09): `purchase-order-import-costs-card.tsx`, `purchase-order-detail-page.tsx`, `purchase-order-import-print-page.tsx`, `utils/purchase-order-import-cost.ts` (+ test), `purchase-order-api.ts`, `purchase-order-payment-api.ts`, `purchase-order-payment-dialog.tsx`, `types/purchase-order-detail.ts`, `finance/types/payable.ts`... Thêm màn danh mục và ô lọc báo cáo tương ứng. Test vitest chạy **theo thư mục** `src/modules/procurement`.

---

## 7. Phân quyền

| Việc | Quyền | Vai trò seed có sẵn |
|---|---|---|
| Xem khối, xem danh mục trong ô chọn | `purchase_order.read` | như ĐMH |
| Gõ chi phí, Chốt tạm tính, Chốt quyết toán, Quyết toán riêng dòng | `purchase_order.write` | `proc`, `dept_proc`, `pur_manager`, `pur_dept_manager` |
| Mở lại giai đoạn / dòng | `purchase_order.approve` + lý do | `pur_manager`, `pur_dept_manager` (theo phạm vi phòng của bao-CR-414) |
| Danh mục Loại chi phí | `purchase_cost_type.read/write` (khóa mới) | `admin`, `pur_manager` |
| Tạo YCTT từ chi phí | `payment_request.create` | như K.4 |
| Báo cáo giá vốn | `report.read` | như cũ |

Phạm vi dữ liệu của `tab_po_cost` đi theo đơn cha (`purchase_order` trong `scoping.py`), không khai riêng. Seed **không ghi đè** vai trò người dùng đã sửa (D-018); quyền mới đưa vào `seed_prod.py` như một dòng **thêm**, không đụng dòng cũ.

---

## 8. Test (chỉ phần đổi)

`test/backend/test_po_chi_phi_thu_mua_cr453.py`:

1. Migration mapping qua ORM: dòng Thực tế → cột Quyết toán, dòng Dự kiến → Dự toán, số khoản nợ `import_cost` trước = sau.
2. Chốt tạm tính chép ô NULL, không chép đè ô đã có; chốt từ 1 lên 3 ghi hai dòng audit.
3. Công nợ chỉ sinh khi giai đoạn hiệu lực = 3; loại `creates_payable = false` không sinh.
4. Quyết toán riêng dòng sinh nợ cho một dòng, các dòng khác vẫn chưa.
5. Mở lại: thiếu quyền → 403, thiếu lý do → 400, dòng đã chi giữ nguyên nợ.
6. Hoàn thành: đơn trong nước có dòng chi phí chưa quyết toán → 400; không dòng nào → qua và tự đặt 3; đơn nhập khẩu vẫn chặn khi chưa trả đủ.
7. `PATCH` gửi số cho cột đã khóa → bị bỏ qua, có warning.
8. Danh mục: tắt loại đang dùng được, xóa không được; ô chọn không liệt kê loại đã tắt.
9. Phân bổ theo giai đoạn: `manual_allocation` khớp số hiệu lực.

Bốn tệp `test_po_*_cr319.py` và `test_po_gia_von_cr347.py` sửa tên cột, **không** mở rộng. Ma trận `dept_proc` (bao-CR-440) thêm hai đường mới `cost-stage/advance` và `reopen`.

---

## 9. Chia đợt

| Đợt | Nội dung | Cổng kiểm | Deploy |
|---|---|---|---|
| **GĐ1** | Backend: model, migration, danh mục, service, API, audit, test mục 8 | pytest hai tệp CR-453 + bốn tệp CR-319/347 + ma trận dept_proc; `alembic heads` một head | dev |
| **GĐ2** | Giao diện v1: khối ĐMH, popup, ô tổng, bản in, nhãn công nợ / YCTT, hộp Hoàn thành; vá nhỏ v2 để đọc `import_cost_allocation` dạng mới | typecheck + lint 0 lỗi; thử tay trên dev với đơn demo `seed_demo_import_po.py` | dev |
| **GĐ3** | Màn danh mục v1, báo cáo giá vốn (ô lọc giai đoạn, đơn trong nước, tab so sánh, Excel) | như GĐ2 | dev |
| **GĐ4** | Port v2 (17 tệp + danh mục + báo cáo), gỡ alias `POImportCost` | vitest `src/modules/procurement`; typecheck | dev |
| **GĐ5** | Bài HDSD «Chi phí thu mua» (seed dev), cập nhật `04-don-mua-hang.md` mục K thành mục mới, `08-he-thong-bao-cao.md` mục 10, data dictionary, nhật ký task | | dev |

Kế hoạch ban đầu là mỗi đợt một commit; khách đổi ý 22/09/2026 (*"làm đủ giai đoạn rồi đẩy lên 1 lượt"*) nên **cả năm đợt gộp một commit**, lên dev cùng lúc. Prod: **không** đụng cho tới khi có lệnh mở lại (19/09).

**Tình trạng 22/09/2026:** GĐ1 backend (migration `05a62d38a47a`, 127 bài kiểm xanh) · GĐ2+GĐ3 giao diện v1 · GĐ4 port v2 + gỡ alias · GĐ5 tài liệu (mục K của `04-don-mua-hang.md`, tab Giá vốn của `08-he-thong-bao-cao.md`, từ điển dữ liệu `05a`, bài HDSD «Chi phí thu mua» seed dev bằng `backend/scripts/seed_help_chi_phi_thu_mua.py`) — **xong hết, đã deploy dev**.

---

## 10. Rủi ro và cách né

| Rủi ro | Cách né |
|---|---|
| Đổi tên bảng + bỏ bốn cột trong một migration, prod có dữ liệu thật | Test mapping (mục 8.1) + chạy migration trên bản sao DB dev đổ từ prod trước khi lên dev; `downgrade` được kiểm bằng `alembic downgrade -1` rồi `upgrade` lại trên local. |
| 48 chỗ trong `service.py` và 32 chỗ trong `PurchaseOrderDetail.tsx` đang đọc `amount / base_amount / cost_status` | Bỏ hẳn cột cũ để **lỗi nổ ngay** lúc import / typecheck chứ không lặng lẽ đọc 0. |
| Hai giao diện cùng một backend | Giữ khóa API lịch sử; điểm đổi hình dạng duy nhất là `import_cost_allocation`, vá v2 nhỏ ngay GĐ2. |
| Người dùng gõ số vào cột đã khóa qua request cũ (v2 chưa port) | Server bỏ qua + warning (6.6), không 400. |
| Loại chi phí bị xóa mất khi còn dòng dùng | E04: chỉ tắt; FK mềm bằng mã số, không FK cứng (giống cách NCC). |
| Tên tệp `.ts` viết qua trình soạn nhị phân sinh byte NUL (bẫy 19/09) | Ghi tệp giao diện bằng Write / python `io.open(newline="")`. |

---

## 11. Câu hỏi còn mở cho khách (không chặn code)

| # | Câu hỏi | Mặc định đang làm |
|---|---|---|
| H1 | Có cần khóa cột Dự toán ngay khi đơn được **duyệt** (dự toán là con số đã trình duyệt) không? | Chưa khóa theo duyệt; chỉ khóa theo giai đoạn. Thêm sau nếu khách cần, một điều kiện trong A05. |
| H2 | Lệch vượt bao nhiêu % thì cần cảnh báo lên chuông quản lý? | Chưa cảnh báo; chỉ tô màu. Ngưỡng nếu có sẽ để ở `tab_setting`. |
| H3 | Báo cáo so sánh có cần theo NCC dịch vụ (cước hãng nào hay vượt dự toán) không? | Đợt này theo đơn và loại chi phí. |
