# PHÂN HỆ ĐIỂM CÀ PHÊ — LỘ TRÌNH PHASE

**Bản:** 1.0 — 08/09/2026 · KHÔNG đặt mốc lịch (theo lệ chung của bộ tài liệu ERP), có ước
lượng **ngày công**. Mỗi phase nghiệm thu riêng được; dừng giữa chừng không để hệ nửa vời.

Mã tính năng (N-xx, A-xx…) tra ở [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md);
bảng dữ liệu ở [`02`](./02-bang-du-lieu.md); thuật toán đồng bộ ở [`03`](./03-tich-hop-pos365.md);
phân quyền ở [`04`](./04-phan-quyen.md); giao diện ở [`05`](./05-giao-dien.md).

```
CP0 (POC, 2 ngày) ──► CP1 (nền DB+quyền) ──► CP2 (client+task+sổ cái) ──► CP3 (5 màn) ──► CP4 (thí điểm 1 tháng) ──► CP5
                 └─ song song: trình nghiệp vụ chốt 4 câu treo (bộ cấp · mức điểm · âm điểm · thuế)
```

---

## CP0 — POC & thủ tục (≈ 2 ngày công) — ✅ XONG 08/09/2026 (làm SAU code, trên cửa hàng thật `degocode`)

**Kết quả:** toàn bộ K1 + P1…P7 đã trả lời — bảng đáp án + bằng chứng ở Phụ lục A của
[`../17`](../17-ke-hoach-trien-khai-pos365-diem-ca-phe.md). Điểm chốt: danh sách đơn
MANG `AccountId` + `MoreAttributes` (P1 đóng, không N+1); UI không cho thêm tài khoản
nhưng **API `AccountCreateOrUpdate` thì được** → đã tạo `TRU DIEM CAFE` **Id 46714**
(điền `.env`); đơn void `Status=3`; server không lọc thời gian (kéo cắt ở client);
Partner không lộ `Password`. Đã chạy trọn đường ống dev bằng dữ liệu thật: kéo 42 đơn
→ nhặt đúng 1 đơn 46714 → hàng chờ → gán tay → ví 200.000−30.000. Còn treo: P5 (ghi
`Point` — chỉ cần cho D-07/CP5) và 4 câu nghiệp vụ (chặn CP4 như cũ).

**Phạm vi:** 7 câu P1–P7 ([`03`](./03-tich-hop-pos365.md) §5) gọi thật và lưu bằng chứng;
lập **tài khoản API riêng** trên POS365; dựng **tài khoản thanh toán "Trừ điểm"** + đọc
`AccountId` (N-04); hỏi POS365 về **cửa hàng thử** (K7). Song song (không phải việc dev):
trình nghiệp vụ 4 câu treo — bộ cấp `CoffeeLevel` (A-02), bảng mức điểm, luật âm điểm
(C-05), thuế TNCN (E-02/N10).

**Điều kiện cần:** có tài khoản admin của cửa hàng POS365 để tạo tài khoản API + tài khoản
thanh toán.
**Điều kiện đủ:** Phụ lục A của [`../17`](../17-ke-hoach-trien-khai-pos365-diem-ca-phe.md)
điền đủ 7 dòng, mỗi dòng kèm curl + response; `AccountId` ghi vào tài liệu vận hành.
**Đường lui:** P1 xấu (không đọc được phương thức thanh toán bằng bất kỳ cách nào) → toàn
bộ phương án đổ, quay về ngã rẽ 3 của `09` §3.3 — dừng ở đây, chưa mất dòng code nào.

## CP1 — Nền dữ liệu & phân quyền (≈ 2 ngày công) — ✅ XONG 08/09/2026

**Phạm vi:** N-05 + G-01/G-02/G-03 — 5 bảng + migration; 6 IntEnum vào `status_catalog.py`
+ `code_sets.py` + chạy `gen_status_ts.py`; 4 entity vào `ENTITIES` + `SCOPE_FIELDS` +
seed cả hai bản (sửa số đếm test B-07 từ 44 lên 48); khung module `app/modules/coffee_point/`
+ đăng `all_models.py`; biến cấu hình N-01/N-02 vào `core/config.py` (`POS365_HARD_OFF`
mặc định `true`).

**Điều kiện cần:** CP0 xong (P1 không đổ phương án); tài liệu 01/02/04 đã soát.
**Điều kiện đủ:** `alembic upgrade head` chạy sạch cả hai chiều trên DB local;
`test_pham_vi_khai_du_b07.py` xanh với 48 entity; seed không đổi hành vi vai trò cũ.
Bộ cấp `CoffeeLevel` chưa chốt cũng không chặn — seed bộ tạm, đổi enum trước CP4.

**Đã làm (08/09/2026):** module `app/modules/coffee_point/` (model 5 bảng + 6
IntEnum + `ENUM_LABELS` theo khuôn `work`) · 4 entity vào `ENTITIES` +
`SCOPE_FIELDS` (+ đăng ký `scope_factory`, bảng phân loại `db.get` — con số test
B-07 nay là **57**, không phải 48 như dự tính vì nhánh khác thêm Nghỉ phép + Đặt
phòng) · seed `coffee_admin`/`coffee_counter` + 4 khóa vào `_SYS_ENTITIES` ·
config `POS365_*` (`HARD_OFF` mặc định bật) · migration **viết tay**
`coffee1cp1a01` (autogenerate không chạy được vì DB dev đang lệch một migration
của nhánh khác — xem Ghi chú môi trường cuối tệp), đã kiểm cả hai chiều trên DB
nháp. `CoffeeLevel` đang là BỘ TẠM 4 cấp — chốt với nghiệp vụ trước CP4.

## CP2 — Client POS365, sổ cái, task đồng bộ (≈ 5–6 ngày công) — ✅ XONG 08/09/2026

**Phạm vi:** N-03 (`pos365_client.py`: phiên, retry, HARD_OFF, `strip_sensitive`) ·
C-01 (`ledger_service.append` — đường ghi sổ duy nhất, luật `uniq_key`) · A-03/A-04/A-05
(reset tháng, chống trùng, thu hồi nghỉ việc) · A-07 (adjust) · D-01…D-06 (4 task + hàng
chờ chưa khớp + cảnh báo) · toàn bộ API `/api/coffee/...` ở `02` §8.

**Điều kiện cần:** CP1 xong.
**Điều kiện đủ:** bộ test backend của module xanh, tối thiểu phủ 6 bài:
1. `pull_orders` chạy 2 lần trên cùng dữ liệu giả — lần hai `written = 0`, số dư không đổi;
2. `monthly_reset` chạy 2 lần cùng kỳ — không nhân đôi (nghiệm thu 2 của `09` §11);
3. đơn void → đúng một dòng `refund`;
4. nhân sự nghỉ việc → số dư về 0, có dòng `revoke` (nghiệm thu 3);
5. `SUM(sổ)` = số dư hiển thị với chuỗi giao dịch trộn đủ 6 loại (nghiệm thu 5);
6. bật `POS365_HARD_OFF`, chạy đủ 5 task — **0 HTTP call** (nghiệm thu 9).
Test theo khuôn SQLite in-memory sẵn có, POS365 mock ở tầng client.

**Đã làm (08/09/2026):** `pos365_client.py` (guard trước MỌI request, re-login 401
đúng một lần, retry chỉ cho request ĐỌC, `strip_sensitive` bỏ `Password`) ·
`service.py` (`append_ledger` là đường ghi sổ duy nhất; 5 vòng nghiệp vụ) ·
`tasks.py` (5 task + khung `_run_logged` ghi `tab_pos_sync_run`, `Pos365Disabled`
→ SKIPPED, cảnh báo D-06 sau 3 FAILED liên tiếp) · 13 endpoint `/api/coffee/...`
· beat: kéo 5' / void mỗi giờ / reset 00:05 ngày 1 / đối chiếu 06:00 (mirror
CHƯA có lịch, chờ P5). **11 test** ở `test/backend/test_diem_ca_phe.py` phủ đủ 6
bài bắt buộc — trong đó bài reset-2-lần bắt được một bug thật lúc viết (lần chạy
lại expire luôn số vừa cấp; đã sửa: có GRANT của kỳ là bỏ qua trọn bộ). Toàn
suite backend xanh trừ MỘT test có sẵn của Thu mua (xem Ghi chú môi trường).
**Lệch thiết kế cố ý:** đối chiếu D-04 bản 1 so SỔ ↔ BẢN SAO ĐƠN trong DB (không
gọi lại POS365 như `03` §4.4) — đủ bắt lệch ghi sổ; so trực tiếp POS365 thêm ở
CP4 khi có kết nối thật. Nút chạy tay chạy INLINE trong request, không cần worker.

## CP3 — Giao diện (≈ 5 ngày công) — ✅ XONG 08/09/2026 (chưa đi trọn vòng dùng thử)

**Phạm vi:** phân hệ "Bán lẻ & quán" vào `module-registry.ts`; 5 màn của [`05`](./05-giao-dien.md)
(Ví của tôi · Chính sách · Thành viên & ghép · Sổ & đối soát 4 tab · Tra cứu quầy);
C-02/C-03/C-04, B-02/B-03 phía UI.

**Điều kiện cần:** CP2 xong (API có thật để gọi).
**Điều kiện đủ:** `docker compose exec erp npm run check` xanh (typecheck + lint + test);
đi trọn vòng trên dev với dữ liệu giả: gán cấp → ghép (mock) → reset tay → thấy ví →
adjust → thấy dòng trên sổ; nhân viên thường gõ URL sổ của người khác bị chặn.
**Đây là mốc nghiệm thu NỘI BỘ** — chưa đụng quán thật.

**Đã làm (08/09/2026):** dựng vào phân hệ **`dego-coffee` có sẵn** (đã có ô "Dego
Coffee" chờ ở registry — bật `enabled`, KHÔNG tạo phân hệ `ban_le` mới như `05`
§0 dự tính; route là `/dego-coffee/...` thay vì `/retail/...`, các tài liệu khác
đọc theo đây). 5 màn: Ví của tôi (root) · Tra cứu quầy (chữ to, auto-clear 30s)
· Chính sách · Thành viên & ghép (dialog tra POS365 + xác nhận từng cặp + tạo
khách B-03) · Sổ & đối soát 4 tab. Dialog theo case C-01 qua vỏ chung
`coffee-dialog-shell.tsx`. 4 khóa vào `permission-types.ts`; hai test hàng rào
router thêm `dego-coffee` vào danh sách mở-công-khai CÓ CHỦ Ý (Ví là của mọi
người). `npm run check` xanh (0 lỗi type/lint, 2538 test pass). CÒN THIẾU của
chính CP3: chưa có ai đi trọn vòng trên dev bằng tay — làm lúc bắt đầu CP4.

## CP4 — Thí điểm trên quán thật (≈ 1 tháng lịch, ~3 ngày công vận hành)

**Phạm vi:** bật kết nối thật ở prod (`POS365_HARD_OFF=false` **chỉ ở prod**); ghép toàn bộ
nhân sự tham gia (B-02, người xác nhận từng cặp); huấn luyện quầy (chọn khách + phương thức
"Trừ điểm", thanh toán hỗn hợp); **chạy song song với cấp tay** — phương án 0 của `09` §9
giữ nguyên giá trị: bảng tính tay là chuẩn đối chứng của tháng đầu.

**Điều kiện cần:** CP3 xong; 4 câu nghiệp vụ treo đã chốt **bằng văn bản** (bộ cấp + mức
điểm + âm điểm + thuế) — thiếu là hoãn, đây là chốt chặn cứng; P3 (thu ngân bấm được) đã
nghiệm ở CP0.
**Điều kiện đủ — 8 tiêu chí kiểm được:**
1. Tuần đầu: 100% đơn "Trừ điểm" khớp người hoặc nằm hàng chờ có người xử lý trong ngày;
2. Quầy trừ một người → dòng tiêu xuất hiện trong sổ ≤ 10 phút (nghiệm thu 7 của `09`);
3. Cuối tháng: số máy ↔ số tay lệch 0 sau khi giải thích hết các dòng đối soát;
4. Reset đầu tháng kế chạy tự động đúng lịch, không ai bấm gì;
5. Cố ý làm lệch một bên → sáng hôm sau có trên màn đối soát, hệ không tự sửa (nghiệm thu 8);
6. Một đơn void ở quầy → điểm hoàn trong ≤ 1 giờ;
7. Tra một lần đồng bộ bất kỳ trong nhật ký: biết ai/lúc nào/kéo gì/lỗi gì (nghiệm thu 10);
8. Nhân viên tự trả lời "tôi còn bao nhiêu điểm" bằng Ví, Nhân sự không phải trả lời hộ.
**Đường lui:** tắt `POS365_HARD_OFF` về `true` — quầy quay lại cấp tay, không mất dữ liệu
(sổ giữ nguyên, chỉ ngừng kéo).

## CP5 — Mở rộng (làm dần sau khi CP4 đóng)

**Phạm vi:** D-07 soi gương số dư (nếu P5 cho) · D-08 menu + E-03 báo cáo món · E-01 báo
cáo kỳ · E-02 bàn giao kế toán (theo đáp án thuế) · B-05 gán cấp CSV · nối A-02 vào danh mục
chức danh khi HR5 của lộ trình HRM có thật.
**Điều kiện cần:** CP4 nghiệm thu đóng. Không có điều kiện đủ chung — từng mục nghiệm riêng.

---

## Tổng ước lượng & nhân lực

| Phase | Ngày công dev | Ghi chú |
|---|---|---|
| CP0 | 2 | + thời gian chờ POS365 trả lời (cửa hàng thử, rate limit) |
| CP1 | 2 | |
| CP2 | 5–6 | Nặng nhất — toàn bộ logic tiền |
| CP3 | 5 | |
| CP4 | ~3 (rải trong 1 tháng lịch) | + công Nhân sự ghép người, huấn luyện quầy |
| **Tổng bản 1** | **17–18 ngày công** | 1 dev full-stack; CP0 làm ngay được, không chờ ai |

Hai chỗ dễ trượt nhất: (1) **4 câu nghiệp vụ treo** — không tốn công dev nhưng chặn cứng
CP4, trình sớm từ CP0; (2) **phụ thuộc POS365 trả lời** (cửa hàng thử, giới hạn gọi) — nằm
ngoài tay mình, hỏi ngay ngày đầu CP0.

---

## Bổ sung chiều 08/09/2026 — sếp chốt nghiệp vụ + 3 tính năng mới

**Nghiệp vụ chốt (qua chat):**
- **Bộ cấp (A-02) CHỐT 5 cấp:** Thực tập sinh · Thử việc · Nhân viên chính thức ·
  Trưởng bộ phận · **Chúa tể Hội đồng quản trị (VÔ HẠN điểm)**. Vô hạn = không
  cấp/không thu kỳ nào, quầy không chặn, ví hiện "Không giới hạn" — dòng TIÊU vẫn
  ghi sổ đủ. Còn thiếu: **mức điểm/tháng của 4 cấp thường** (khai ở màn Chính sách).
- **A-06 CHỐT: cấp phát từng kỳ PHẢI CÓ NGƯỜI DUYỆT.** Beat ngày 1 chỉ chạy dự
  kiến + chuông nhắc; đường ghi thật là nút **Cấp phát kỳ** (xem trước → Chốt,
  quyền `coffee_ledger.approve` — seed cho `coffee_admin`).
- Còn treo: âm điểm (C-05) và thuế TNCN (E-02).

**Ba màn/tính năng mới (ngoài kế hoạch CP3 gốc, làm cùng ngày):**
1. **Quản lý POS** (`/dego-coffee/pos`, quyền `pos_order.read`) — chỉ-ĐỌC từ
   POS365 đúng doc 09 §12: thẻ số hôm nay (đơn/doanh thu/tiền mặt/trừ điểm),
   doanh thu 7 ngày (`ColumnChart`), đơn gần đây kèm phương thức, nút mở POS365.
   Backend `GET /api/coffee/pos-dashboard` + hàm thuần `build_pos_dashboard` có test.
2. **Tự đặt nước** (`/dego-coffee/order`, mọi người đăng nhập) — menu + ẢNH đọc
   thẳng POS365 (`ProductImages[].ImageURL`, 25/25 món có ảnh), giỏ hàng, đặt →
   `POST /api/coffee/self-order` tạo đơn trên POS365 (spec §5.3 OrderSave: trả
   trọn tài khoản 46714, `PartnerId` = khách đã ghép, `SoldById` = UserId tài
   khoản API, `Description` "DEGO tự đặt — <tên>") → quầy thấy đơn → kéo về trừ
   ví (endpoint kéo ngay một vòng best-effort cho ví cập nhật liền). Giá tra lại
   từ POS365 lúc đặt, chặn đặt quá số dư (trừ cấp vô hạn). **Đã chạy thật:**
   đơn `HD080926-0007` (08/09 16:43).
3. **Dev = môi trường thí điểm:** `.env` dev đặt `POS365_HARD_OFF=false` (đảo
   khuyến cáo cũ — cửa hàng `degocode` đang là bản trial/thử, compose local
   không chạy beat/worker nên không có gì tự động; ghi thật chỉ sau nút có quyền).

**Dữ liệu thật đã nạp (qua API):** 6 đơn thử HD080926-* đã void sạch; dữ liệu thử
local xóa trắng; 5 thành viên thật tạo + ghép (TESTREQ=Thử việc, DEMONV=NV chính
thức, DEMOTP + DEMO_MANAGER_PURCHASE=Trưởng bộ phận, degoadmin=Chúa tể HĐQT) —
khách POS365 Id 24196660…24196664. `policy_points` thêm luật `company_id=0` = áp
mọi pháp nhân.

**Việc kế tiếp:** khai mức điểm 4 cấp ở màn Chính sách rồi bấm Cấp phát kỳ ·
import/export thành viên & sổ điểm từ xlsx (B-05 mở rộng — file mẫu Products/
Customers.xlsx đã đọc cấu trúc) · trước khi chạy chính thức: bấm "Xóa dữ liệu
mẫu" trên POS365 ⚠️ nút này có thể xóa luôn 25 MÓN MẪU (menu tự đặt sẽ trống —
phải nhập thực đơn thật) và cần kiểm tài khoản 46714 còn sống không.

## Ghi chú môi trường (08/09/2026 — lúc code CP1–CP3)

Hai vấn đề CÓ SẴN của nhánh/DB dev, KHÔNG do phân hệ này, ghi lại để ai gặp khỏi đổ nhầm:

1. **DB dev lệch migration:** DB đang ở `b3f4a1c2d5e6` nhưng chuỗi `erp-v2`
   (`6835fb9cfecd`…) chưa áp, mà cột `tab_work_task.kind` thì ĐÃ có sẵn trong DB —
   `alembic upgrade head` chết ở `Duplicate column name 'kind'`. Vì vậy bảng
   `tab_coffee_*` CHƯA có trên DB dev local; migration `coffee1cp1a01` đã kiểm cả
   hai chiều trên DB nháp sạch. Người giữ nhánh `erp-v2` xử lý drift (stamp hoặc
   sửa migration đó thành idempotent) rồi `alembic upgrade head` là bảng tự vào.
2. **Một test Thu mua đỏ sẵn:** `test_pr_line_no_po_cr074.py::test_moi_lap_don_nhap_thi_phieu_van_o_da_dieu_phoi`
   (sync trạng thái YCMH) — đỏ từ trước khi thêm phân hệ này, không liên quan.
