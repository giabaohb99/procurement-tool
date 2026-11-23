# 21 — Giá bao bì: tác động giá, bảng giá VTBB, báo giá, lịch sử mua, định mức bao bì

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 21/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Hiệu lực (chỉ trên dev) |
| CR liên quan | duoc-CR-784 |
| Giao diện | ERP v2: phân hệ Thu mua, nhóm menu **Giá nguyên vật liệu sản xuất** (tên chốt 21/11/2026, trước là Giá bao bì) (`/procurement/packaging-cost/...`, `frontend-v2/src/modules/procurement/pages/packaging-*.tsx`) · giao diện cũ Thu mua: **cụm menu riêng Giá nguyên vật liệu sản xuất** (`/packaging-cost/...`, `/packaging-boms`, `/product-price-quotes`; `frontend/src/pages/packaging/*`) |
| Bài Help Center | Thẻ **Hướng dẫn sử dụng Giá bao bì** + 8 bài, `backend/scripts/seed_help_gia_bao_bi_cr784.py` |
| Hợp đồng kỹ thuật | [api.md](../tai-lieu-ky-thuat/api.md) (nhóm `packaging-cost`, các dòng `/api/packaging-cost/*`, `/api/packaging-boms`, `/api/product-price-quotes`) · [kế hoạch 261120](../plans/261120-tac-dong-gia-bao-bi/plan.md) (phase 04 = hợp đồng API và số đo hiệu năng) |
| Nguồn | Bản mẫu `Bao cao gia NVL san xuat - 11.2026.html` của Thu mua; mã màn và mã backend `packaging_cost/`, `product_price/`, `core/packaging_price_codes.py` (đọc 21/11/2026) |

Nội dung ở đây và ở seed `seed_help_gia_bao_bi_cr784.py` phải khớp nhau; cẩm nang trợ lý
`backend/app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md` (mục *Giá bao bì*) tóm tắt cùng luật. Sửa luật hay
nhãn nút thì sửa cả ba nơi.

**Hai giao diện.** Cụm có ở cả ERP v2 lẫn giao diện cũ Thu mua. Bản cũ là **ngoại lệ của D-026** (`frontend/` đóng băng,
chỉ vá lỗi): người chủ duyệt 21/11/2026 vì người dùng Thu mua còn làm chính trên bản cũ. Cùng API, cùng dữ liệu, cùng
quyền; chỗ khác nhau ghi ở từng mục. **Chỉ trên dev** (`deverp`, `devthumua`), chưa lên prod.

## 1. Mục đích, công thức, nguồn giá

**Mục đích.** Nhà cung cấp đổi giá một mã vật tư bao bì (VTBB: chai, nắp, nhãn, nhãn thùng, thùng) thì chi phí bao bì của
sản phẩm (mã HH) nào đổi theo, đổi bao nhiêu — để quyết nhận giá, thương lượng, đổi NCC hay báo xem lại giá bán.

**Công thức** (đúng `productRow()` của bản mẫu, `packaging_cost/cost_service.py`):

- CP bao bì / chai = Chai + Nắp + Nhãn + (Nhãn thùng + Thùng) / Quy cách thùng.
- CP bao bì / thùng = CP bao bì / chai x Quy cách thùng.
- Giá VNĐ chưa VAT theo ĐVT danh mục; dòng ĐMH ngoại tệ nhân tỷ giá trên đơn.

**Sổ giá** (`tab_product_price_ledger`, tự gom, không nhập tay):

| Nguồn (`PriceSourceType`) | Vào sổ khi nào | Đổi thế nào |
|---|---|---|
| 1 — Lịch sử mua hàng | mỗi dòng `tab_purchase_history` (hệ thống và dữ liệu cũ nạp vào) | chỉ chèn, không sửa (dòng lịch sử bị xóa khi nạp lại dữ liệu cũ thì dòng sổ xóa theo) |
| 2 — Dòng đơn mua hàng (màn ghi *ĐMH đang mở*) | ĐMH đã duyệt trở đi, chưa xóa mềm; dòng chưa hủy, có mã hàng, chưa sang lịch sử | sửa giá / SL / VAT / NCC / ngày / tỷ giá thì cập nhật đúng dòng; dòng sang lịch sử, bị hủy, đơn bị hủy duyệt thì xóa |
| 3 — Sổ Misa (nạp TẠM) | `scripts/import_misa_price_ledger.py` nạp từ báo cáo HTML của chủ dự án (sổ chi tiết mua hàng Misa 2025 – 06/2026), mỗi dòng Misa một dòng sổ (`source_id` = id dòng Misa), kèm tên NCC chép theo dòng (`supplier_name`) vì mã NCC Misa không nằm trong danh mục nhà cung cấp | chạy lại thì cập nhật đúng dòng (idempotent); `--purge` xóa hết dòng nguồn 3 và mốc → trả hành vi cũ |

Dòng đơn giá 0 vẫn ghi (đếm số lần mua), tầng tính giá bỏ qua. Báo giá **không** vào sổ giá.

**Mốc cắt sổ Misa** (chủ dự án chốt tạm: *coi báo cáo HTML là dữ liệu đúng, chạy giá theo đó*). Nạp xong, ngày lớn nhất của dòng
Misa (hiện là 30/06/2026) được ghi vào `tab_setting` khóa `misa_price_cutoff`. Từ đó MỌI phép tính giá — giá cũ / mới, hai lần
mua gần nhất, số lần mua, ngày cuối, min / max, Tổng hợp theo sản phẩm, Giá mua gần nhất, Lịch sử mua hàng, ba công cụ AI —
chỉ xét **dòng Misa có ngày <= mốc** và, sau mốc, **chỉ lần mua của ĐMH thật trên ERP** (dòng ĐMH đã duyệt và lịch sử mua có gắn ĐMH); lịch sử cũ nạp từ Excel khảo sát (`source='legacy'`, nhiều dòng sai ngày / sai giá) bị bỏ hẳn khi có mốc. Đối chiếu 23/11/2026 trên dữ liệu máy local: Tổng hợp 1.000 sản phẩm ra Tăng 239 · Giảm 251 · Không đổi 510 · Chưa có giá 0, khớp tuyệt đối báo cáo HTML. Chưa có mốc (chưa nạp hoặc đã
gỡ) thì hành vi y hệt trước đây. Điều kiện là một biểu thức SQL dùng chung (`product_price/misa_cutoff.py`, áp bên trong
`latest_priced_by_code` và `build_history`), nên không thêm truy vấn nào. Nhãn nguồn hiện **Sổ Misa**.

Chủ dự án chốt **phương án A** ngày 23/11/2026: giữ cả hai nguồn như trên (sổ Misa tới mốc, ĐMH thật trên ERP sau mốc),
không chuyển sang chỉ dùng sổ Misa. Vì vậy trên máy dev, nơi đã có ĐMH thật sau 30/06/2026, Tổng hợp ra Tăng 316 · Giảm 270 ·
Không đổi 414, lệch báo cáo HTML (239 · 251 · 510) là đúng ý: phần lệch đến từ 97 dòng ĐMH đã duyệt và 12 dòng lịch sử mua
có gắn ĐMH sau mốc.

**Giá cũ / giá mới** (`product_price/price_state_service.py`):

| Mã đang có | Giá mới | Giá cũ |
|---|---|---|
| Có báo giá | báo giá mới nhất theo ngày hiệu lực (kể cả ngày ở tương lai — Q2 chốt 20/11), hòa ngày thì báo giá nhập sau | lần mua có giá gần nhất; chưa mua thì = giá mới |
| Không báo giá, từ hai lần mua có giá | lần mua có giá gần nhất | lần mua có giá ngay trước |
| Không báo giá, một lần mua có giá | lần đó | = giá mới |
| Không lần mua có giá, không báo giá | rỗng (*chưa có giá*) | rỗng |

"Gần nhất" = ngày mua giảm, rồi id ĐMH giảm, rồi id dòng sổ giảm. Màu chênh lệch: **tăng xanh, giảm đỏ** (người chủ chốt
20/11, ngược bản mẫu).

## 2. Tác động giá bao bì

Màn `/procurement/packaging-cost` (tiêu đề *Tác động tăng giá bao bì*; menu v2 *Tác động giá bao bì*, menu cũ *Tác động giá*,
đường cũ `/packaging-cost/impact`). Bài HDSD: *Giá bao bì — Xem tác động khi nhà cung cấp đổi giá chai, nắp, nhãn, thùng*.

- Ô chọn nhiều mã (*Chọn mã chai / nắp / nhãn / nhãn thùng / thùng*): mã dùng trong định mức, gõ không dấu; gõ tên nhóm
  (nhiều nhóm cách dấu phẩy) rồi **Chọn tất cả** để chọn cả nhóm; nhãn mã có nút **x**, nút **x** cuối ô bỏ hết; tối đa 500 mã.
- Bảng mã đã chọn: Mã, Tên vật tư, Nhóm, Giá cũ, Giá mới, **Giá giả định** (ô *Nhập giá*, trễ 400 ms rồi tính lại, xóa
  trắng = bỏ), Chênh lệch, %, Số SP, Min, Max, Ghi chú, nút bỏ mã. Dòng tóm tắt **Mã đã chọn · Sản phẩm bị ảnh hưởng**.
- *Khoảng ngày tính min – max* chỉ áp cho Min / Max.
- Bảng sản phẩm bị ảnh hưởng (phân trang, tìm, xếp tại máy chủ): STT, Mã HH, Tên hàng hóa, Quy cách thùng, Chai, Nắp,
  Nhãn, Nhãn thùng (giá /thùng), Thùng (giá /thùng) — ô thành phần ghi *giá cũ → giá đang dùng*, mã đang chọn tô vàng —,
  CP bao bì/chai cũ, CP bao bì/chai mới, Tăng/giảm /chai, Tăng/giảm /thùng, Ghi chú.
- **Xuất Excel** (quyền `export`): hai sheet *Mã đã chọn*, *Sản phẩm bị ảnh hưởng*, theo giá giả định đang gõ, `q` và thứ tự.
- Bản cũ: cùng bước, nút, cột.

**Ghi chú cảnh báo** (`CostWarning`, nhãn ở `core/packaging_price_codes.py`):

| Mã | Nhãn | Khi nào | Ảnh hưởng số |
|---|---|---|---|
| 1 | Thiếu giá chai | mã chai chưa có giá | CP rỗng, xu hướng *Chưa có giá* |
| 2 | Chưa khai mã thành phần (kèm Nắp / Nhãn) | định mức bỏ trống nắp hoặc nhãn | không (nhãn thùng / thùng trống thì im) |
| 3 | Thiếu giá thành phần (kèm vai trò) | có mã nhưng chưa có giá | phần đó tính 0 |
| 4 | Thiếu quy cách thùng | có nhãn thùng / thùng mà quy cách 0 | phần thùng tính 0 |
| 5 | ĐVT mua khác ĐVT danh mục | ĐVT lần mua gần nhất khác ĐVT danh mục (so sau bỏ dấu, chữ thường) | không, chỉ báo |
| 6, 7 | Dưới ngưỡng sàn / Vượt ngưỡng trần | — | **đang tắt**, xem mục 8 |

## 3. Tổng hợp theo sản phẩm

Màn `/procurement/packaging-cost/products` (cũ `/packaging-cost/products`). Bài HDSD: *Giá bao bì — Rà chi phí bao bì của
mọi sản phẩm*. Mọi mã HH có định mức, giá cũ so với giá mới hiện hành, không có giá giả định.

- Chip **Tất cả / Tăng / Giảm / Không đổi / Chưa có giá** kèm số đếm (đếm sau lọc từ khóa, chưa lọc xu hướng).
- Cột: Mã HH (bấm → Lịch sử mua hàng theo mã sản phẩm), Tên hàng hóa, Quy cách, CP cũ /chai, CP mới /chai, Chênh /chai,
  Chênh /thùng, % chênh, Xu hướng, năm ô thành phần (mã bấm được), Ghi chú.
- Ô tìm *Tìm mã HH, tên, mã thành phần…*; xếp + phân trang tại máy chủ; **Xuất Excel** tối đa 5.000 dòng.

## 4. Bảng giá VTBB và báo giá

Màn `/procurement/packaging-cost/prices` (cũ `/packaging-cost/price-list`). Bài HDSD: *Giá bao bì — Tra Bảng giá VTBB và
nhập báo giá của nhà cung cấp*.

- Cột: Mã VTBB, Tên vật tư, Nhóm, ĐVT, Số lần mua, Mua gần nhất, Giá mua gần nhất, Giá mua lần trước, Báo giá mới (kèm ngày
  hiệu lực), Giá cũ, Giá mới, Chênh lệch, %, Min, Max, Số SP đang dùng, Ghi chú, Thao tác (nút **Báo giá**).
- v2 ẩn sẵn Min, Max, Ghi chú (mở ở nút **Cột**); bản cũ hiện sẵn Min, Max, ẩn Ghi chú.
- Lọc: ô *Tìm mã, tên vật tư…*, chip nhóm, phạm vi **Mã trong định mức** (mã trong định mức ∪ mã có báo giá, mặc định) /
  **Mọi mã có giá** (thêm mọi mã trong sổ giá), *Khoảng ngày tính min – max*. Xếp + phân trang tại máy chủ, Xuất Excel theo
  đúng bộ lọc và thứ tự.
- **Báo giá mới** (đầu trang) / **Báo giá** (từng dòng, mã khóa sẵn) mở hộp: Mã VTBB *, Mã NCC, Đơn giá (VNĐ, chưa VAT) *,
  VAT (%), Ngày hiệu lực *, Ghi chú; nút **Lưu báo giá**. Lỗi: *Nhập mã vật tư bao bì.*, *Nhập đơn giá báo giá (lớn hơn
  0).*, *Chọn ngày hiệu lực.* Cần quyền `packaging_cost.create`.
- Màn danh sách **Báo giá VTBB** (`/procurement/packaging-cost/quotes`, cũ `/product-price-quotes`) **ẩn khỏi menu**
  (người chủ chốt 21/11: bản mẫu không có tab này) nhưng vẫn gác quyền `packaging_cost`. v2 sửa trong hộp (**Lưu thay
  đổi**), bản cũ sửa ở trang chi tiết chung (**Lưu**, **Xóa**).

## 5. Giá mua gần nhất

Màn `/procurement/packaging-cost/last-prices` (cũ `/packaging-cost/last-prices`). Bài HDSD: *Giá bao bì — So đơn giá các lần
mua gần nhất*.

- Mỗi mã VTBB một dòng; nhóm cột *Thông tin VTBB* (Mã VTBB, Tên vật tư, Nhóm, ĐVT, Số lần có giá); mỗi lần mua một nhóm cột
  gộp *Lần 1 (gần nhất)*, *Lần 2*… (Ngày mua, Nhà cung cấp, [Số lượng], Đơn giá; xanh đắt hơn lần trước, đỏ rẻ hơn); *Biến
  động* (Lần 1 so lần 2, Lần 1 so lần n); *Giá TB* (Giá TB n lần). Chỉ lần mua có giá.
- Lọc: ô tìm, chip nhóm kèm số, *Số lần hiển thị* 3 / 5 (mặc định) / 10, *Phạm vi mã* **Định mức + báo giá** / **Mọi mã**,
  *Nhà cung cấp* (giữ mã có NCC đó trong n lần đang hiện), *Khoảng ngày mua*, *Biến động lần 1 so lần 2* (Tất cả / Tăng /
  Giảm / Không đổi), *Biến động từ (%)*, công tắc *Chỉ mã đã có giá* (bật sẵn), *Chỉ mã đang dùng trong định mức*, *Hiện số
  lượng*. Xuất Excel theo đúng bộ lọc, n và thứ tự.

## 6. Lịch sử mua hàng (của cụm Giá bao bì)

Màn `/procurement/packaging-cost/history` (cũ `/packaging-cost/history`), đường dẫn sâu `?codes=` / `?hh=`. Bấm mã ở mọi bảng
của cụm là mở màn này. Bài HDSD: *Giá NVL sản xuất — Xem lịch sử mua và biểu đồ giá của một mã*. Khác tab Lịch sử mua hàng ở chi
tiết sản phẩm ([18](18-lich-su-mua-hang.md)): đọc sổ giá nên có cả dòng ĐMH đang mở.

- Chế độ **Theo mã VTBB** (rỗng = mọi mã) / **Theo mã sản phẩm** (mọi thành phần của định mức, thêm cột Vai trò); tối đa 200
  mã; lọc Nhà cung cấp, Khoảng ngày mua, ô tìm.
- Thẻ số liệu (trên toàn bộ tập lọc), trình bày y bản mẫu HTML (thẻ trắng, viền trên xanh lá, số to, một dòng phụ; chốt
  23/11/2026), ở cả màn hình lẫn bản in:
  - Đúng một mã: *Tổng số lần mua* (dòng phụ: khoảng ngày) · *Tổng số lượng mua* (ĐVT) · *Tổng giá trị mua* (giá x SL của
    các lần có giá; dòng phụ: số lần có giá / số lần mua) · *Giá thấp nhất – cao nhất* (BQ gia quyền) · *Gần nhất so với lần
    đầu* (phần trăm giá lần có giá gần nhất so với lần có giá đầu tiên, tăng xanh giảm đỏ; dòng phụ: giá đầu → giá gần
    nhất) · *Số nhà cung cấp*; kèm biểu đồ *Diễn biến đơn giá*.
  - Nhiều mã / mọi mã: *Số mã đã chọn* (số mã có lịch sử mua) hoặc *Số mã hàng* · *Tổng số lần mua* · *Tổng giá trị mua* ·
    *Số nhà cung cấp*.
  - Theo mã sản phẩm: *Số sản phẩm* · *Mã vật tư liên quan* · *Số dòng lịch sử* · *Số nhà cung cấp*.
- Cột: Lần, Ngày mua, Mã VTBB, Tên vật tư, [Vai trò], Nhà cung cấp, **Kho**, Số lượng, Đơn giá, Thành tiền, So lần trước, Nguồn
  (mã ĐMH bấm được, nhãn *ĐMH đang mở*). Dòng giá 0 hiện nhưng không tính KPI / biểu đồ. Xuất Excel tối đa 5.000 dòng.
- **Kho** (bổ sung 23/11/2026 theo ý kiến chủ dự án: *thiếu cột kho so với file của Ms.Mi*): tên kho nhập hàng của lần mua. Dòng
  Misa lấy từ cột kho của sổ chi tiết mua hàng (vd *KHO NCC_HÀ LONG*, *Kho VTBB DEGO Cần Thơ*); dòng của ERP lấy từ kho trên dòng
  ĐMH (tên trong danh mục kho theo mã kho; mã không có trong danh mục thì hiện chính mã); không biết kho thì để trống. Ô tìm tìm
  được cả theo tên kho, bấm tiêu đề cột để xếp (ô trống luôn xuống cuối), có trong bản in và trong Excel (cột *Kho* ngay sau
  *Nhà cung cấp*). Chưa có bộ lọc theo kho.

## 7. Định mức bao bì và nhập từ Excel

Màn `/procurement/packaging-cost/boms` (cũ `/packaging-boms`). Bài HDSD: *Giá bao bì — Khai và nhập định mức bao bì từ Excel*.
Bảng `tab_packaging_bom`, mỗi mã HH một dòng; Thu mua tự khai.

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| Mã HH (`hh_code`) | Có | không sửa sau khi tạo |
| Quy cách thùng (chai / thùng) | Không (0) | 0 = chưa có, phần nhãn thùng / thùng không tính |
| Tên hàng hóa, Tên pháp lý | Không | |
| Mã chai | Có | |
| Mã nắp, Mã nhãn | Không | trống thì cảnh báo 2 |
| Mã nhãn thùng, Mã thùng | Không | giá cho cả thùng, chia quy cách |

- Mã thành phần chưa có trong danh mục sản phẩm tô đỏ (*chưa có trong danh mục*).
- v2: **Thêm định mức** / bấm dòng mở hộp, nút **Tạo mới** / **Lưu thay đổi**, xóa trong hộp. Bản cũ: danh sách chung, **Thêm**
  hoặc bấm dòng mở trang chi tiết, **Tạo** / **Lưu** / **Xóa**.
- **Nhập từ Excel** (cần `packaging_cost.create` + `import.create` + `import.read`): hộp *Nhập định mức bao bì*, tệp
  `DATA_CHAI.xlsx` (sheet `MAP_SP`, hoặc `data` + `DATA CHUNG`), nút **Chạy thử** → trang lô Quản lý Import (`module=4`) xem
  nhật ký từng dòng → **Ghi thật** (hộp hỏi lại). Bản cũ: trang lô `/import-batches/:id` có nút **Ghi thật** riêng cho lô
  định mức bao bì đã chạy thử xong. Có rồi thì cập nhật, chưa có thì tạo, dòng không có trong tệp giữ nguyên; khớp mã HH bỏ
  số 0 đầu; trần 20.000 dòng; **chưa hoàn tác được**.

## 8. Quyền, giới hạn, phạm vi chưa làm

- Khóa quyền **`packaging_cost`** (*Giá bao bì*, nhóm Thu mua ở màn Vai trò & quyền): `read` mở mọi màn, `export` nút Xuất
  Excel, `create` báo giá / định mức / nhập Excel, `write` sửa, `delete` xóa. Nằm trong `SENSITIVE_PROCUREMENT_ENTITIES`
  (giá vốn): tick Xem / Xuất cho vai trò mặc định hiện dòng nhắc vàng. Seed không giao sẵn cho vai trò nào ngoài admin.
- Phạm vi: `SCOPE_FIELDS["packaging_cost"] = {"company": "company_id"}` đo trên sổ giá — giá tính theo pháp nhân người xem
  được thấy. Định mức, báo giá là danh mục dùng chung (`scoped=False`).
- Giới hạn: một chai một bộ chai / nắp / nhãn (chưa có số lượng thành phần); mỗi mã HH một định mức, chưa có phiên bản (Q7
  treo); đơn giá hiểu là giá một cái theo ĐVT danh mục (Q3 treo); giá từ lịch sử mua của ERP; riêng giai đoạn tới mốc cắt (30/06/2026) lấy TẠM từ sổ Misa nạp bằng script (xem mục 1, Q1).
- **Phạm vi chưa làm / cố ý ẩn:** ngưỡng giá sàn / trần (`/api/product-price-limits`, cảnh báo 6 / 7) có backend nhưng giao diện
  tắt bằng công tắc `PACKAGING_LIMITS_ENABLED = false` ở cả hai bản (người chủ chốt 21/11 "tạm thời chưa xài") — bài HDSD
  không nhắc; bật lại thì bổ sung mục 4 và bài Bảng giá. Ba công cụ AI cho Trợ lý / bot / cổng MCP
  (`packaging_price_impact`, `packaging_price_lookup`, `packaging_product_cost`, `assistant/tools/packaging_cost_tool.py`,
  bài kiểm `test_cong_cu_gia_bao_bi_cr784.py`) đang trong cùng đợt mã của duoc-CR-784: cẩm nang dặn trợ lý dùng công cụ nếu
  có trong danh sách, không thì chỉ màn Tác động giá bao bì. Bài HDSD chưa có mục hỏi Trợ lý về giá bao bì.
