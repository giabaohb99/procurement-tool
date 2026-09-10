# PHÂN HỆ ĐIỂM CÀ PHÊ — ĐẶC TẢ TÍCH HỢP POS365

**Bản:** 1.0 — 08/09/2026 · Đọc sau [`02-bang-du-lieu.md`](./02-bang-du-lieu.md) ·
Nguồn sự thật về API bên kia: *API Specification Doc 1.0* của POS365 (14/06/2021) + metadata
`https://api.pos365.vn/api/metadata` — trích lục ở Phụ lục B của [`../17-...md`](../17-ke-hoach-trien-khai-pos365-diem-ca-phe.md).

Toàn bộ phần nói chuyện với POS365 nằm trong MỘT tệp `app/modules/coffee_point/pos365_client.py`
— service và task **không tự gọi HTTP**, chỉ gọi client. Lý do: cầu dao HARD_OFF, phiên, retry,
lọc `Password` phải nằm một chỗ; rải ra là sót một chỗ.

## 1. Cầu dao an toàn (N-02) — điều kiện của mọi thứ bên dưới

```
def _guard(self):
    if settings.POS365_HARD_OFF or not settings.POS365_BASE_URL:
        raise Pos365Disabled(...)   # task bắt lỗi này -> ghi sync_run SKIPPED, không phải FAILED
```

- Kiểm **trước mọi request**, kể cả login.
- Test bắt buộc ở CP2: bật cờ, chạy đủ 5 loại task, khẳng định **không một HTTP call nào**
  phát ra (mock ở tầng transport, đếm 0 lần gọi).
- Dev/UAT không bao giờ đặt `false`. Muốn thử thật thì thử trên **chi nhánh/cửa hàng thử**
  (câu K7 — hỏi POS365 trong POC).

## 2. Phiên làm việc (N-03)

| Việc | Cách làm |
|---|---|
| Đăng nhập | `GET {base}/api/auth/credentials?Username=..&Password=..&format=json` → `{SessionId}` |
| Gửi kèm | Header `Cookie: ss-id={SessionId}` cho mọi request sau |
| Cache | SessionId giữ trong tiến trình (biến của client instance). **Không lưu DB** — lộ DB backup không lộ phiên |
| Hết hạn | Response 401 → đăng nhập lại **đúng MỘT lần** rồi phát lại request; 401 lần hai → lỗi thật, ghi sync_run FAILED. Không loop login — sai mật khẩu mà loop là bị khóa tài khoản bên kia |
| Tài khoản | **Tài khoản API riêng** tạo trên POS365, không phải tài khoản của người nào (người đổi mật khẩu là tác vụ nền chết im lặng — bài học ghi sẵn ở `09` §3.1) |

## 3. Quy ước gọi chung

- Phân trang: `$top=a&$skip=(n-1)*a`, response luôn có `__count`. Cỡ trang mặc định 50,
  chỉnh theo POC P6.
- Timeout 15s/request; lỗi mạng retry 3 lần giãn cách (2s · 8s · 30s) — **chỉ retry request
  ĐỌC**; request GHI (tạo partner) không tự retry mù, vì chưa biết POS365 có idempotent không
  (K4) — lỗi thì dừng, người bấm lại sau khi client **đọc kiểm tra** đã tạo chưa.
- Mọi response chứa Partner phải qua `strip_sensitive()` **bỏ trường `Password`** trước khi
  trả ra khỏi client — không lưu, không log (cảnh báo `09` §3.2).
- Lỗi `400 POSException` đọc `ResponseStatus.Message` (tiếng Việt) ghi thẳng vào `error` của
  sync_run — đó là câu người vận hành cần thấy.

## 4. Thuật toán từng task (Celery — đăng ở `celery_app.py`, hàng đợi riêng `coffee`)

### 4.1 `coffee.pull_orders` — kéo đơn, ghi dòng tiêu (D-01, D-02) — mỗi 5 phút

```
mốc = max(cursor_to của lần SUCCESS gần nhất, đầu ngày hôm qua) - 10 phút   # đè mép
1. Kéo /api/orders (Includes=Partner) trang một, lọc PurchaseDate >= mốc
   (nếu POC P4 cho lọc server-side thì lọc từ query; không thì đọc tới khi gặp đơn cũ hơn mốc)
2. Với từng đơn:
   a. Đọc phần thanh toán (MoreAttributes.PaymentMethods — theo POC P1 có thể phải gọi chi tiết)
   b. Không chứa POS365_PAYMENT_ACCOUNT_ID -> bỏ qua (đơn khách vãng lai)
   c. Upsert tab_pos_order theo pos_order_id (UNIQUE — kéo trùng vô hại)
   d. Khớp người: pos_partner_id -> tab_coffee_member.pos_partner_id
      - khớp: match_status=MATCHED, INSERT ledger SPEND (uniq_key S-{pos_order_id},
        points = -points_paid, period = kỳ của PurchaseDate) — trùng khóa thì bỏ qua im lặng
      - không khớp: match_status=UNMATCHED, KHÔNG ghi sổ, chờ người xử lý (resolve)
3. Ghi sync_run: fetched/written/skipped, cursor_to = thời điểm bắt đầu chạy
```

Bất biến phải test: chạy hai lần liên tiếp trên cùng dữ liệu → lần hai `written = 0`.

### 4.2 `coffee.check_voids` — hoàn điểm đơn hủy (D-03) — mỗi giờ

```
Lấy các tab_pos_order có dòng SPEND, is_voided=0, purchase_date trong 7 ngày
Đọc lại từng đơn bên POS365; Status là "void" (giá trị chốt ở POC P4)
  -> is_voided=1, INSERT ledger REFUND (uniq_key R-{pos_order_id}, points = +points_paid)
```

### 4.3 `coffee.monthly_reset` — reset & cấp kỳ mới (A-03, A-04) — ngày 1, 00:05

```
period_cu = kỳ vừa hết, period_moi = kỳ mới
Với từng tab_coffee_member status=ACTIVE:
  1. du = SUM(ledger.points) của người đó
     du != 0 -> INSERT EXPIRE (uniq_key E-{emp}-{period_cu}, points = -du)
     (du âm — người bị âm điểm — thì EXPIRE ghi +|du|: kỳ mới bắt đầu từ 0,
      còn khoản âm đã nằm trên màn đối soát từ lúc phát sinh, xử lý theo C-05)
  2. mức = tab_coffee_policy: dòng (company, level_code) có effective_from lớn nhất <= ngày 1
     không có dòng nào -> bỏ qua + đếm vào cảnh báo (cấp chưa khai mức là lỗi cấu hình, phải nổi lên)
  3. INSERT GRANT (uniq_key G-{emp}-{period_moi}, points = +mức)
Chạy trong MỘT transaction cho từng người (không phải cả đợt) — đứt giữa chừng thì
người đã xong không lặp (uniq_key đỡ), người chưa xong chạy lại là tiếp.
```

Hai đường vào: beat tự động + nút chạy tay (quyền `pos_order.write`) truyền `period` tường
minh — chạy bù khi beat chết, và **cũng chỉ idempotent nhờ uniq_key, không nhờ ai nhớ**.

### 4.4 `coffee.reconcile` — đối chiếu (D-04) — 06:00 hằng ngày

```
Theo từng ngày trong 3 ngày gần nhất:
  A = SUM(points_paid) các đơn "Trừ điểm" đọc TRỰC TIẾP từ POS365 của ngày đó
  B = -SUM(ledger SPEND) + SUM(ledger REFUND) của các dòng có pos_order thuộc ngày đó
  A != B -> ghi nhận lệch (hiện ở tab Đối soát), bắn thông báo D-06 nếu lệch 2 ngày liên tiếp
KHÔNG tự sửa — luật số 3 của 09 §2. Người xử lý bấm từng dòng, sinh ADJUST có lý do.
```

### 4.5 `coffee.mirror_balance` — soi gương số dư (D-07, tùy chọn) — 02:00

Chỉ bật khi POC P5 xác nhận `PartnerSave` ghi được `Point`/`Description`. Ghi số dư ERP vào
hồ sơ khách để thu ngân thấy trên màn POS365. **Chỉ hiển thị** — không bao giờ đọc ngược
`Point` từ POS365 về sổ; lệch chiều đó là vô hại và tự hết ở lần soi sau.

### 4.6 Cảnh báo (D-06)

Bọc chung ở tầng task: một `kind` FAILED **3 lần liên tiếp** (đếm từ `tab_pos_sync_run`) →
thông báo người phụ trách qua module notification sẵn có. `Pos365Disabled` không tính —
HARD_OFF là chủ ý, không phải sự cố.

## 5. POC — bảy câu phải trả lời bằng lời gọi thật (GĐ CP0, chặn mọi việc code)

Chép từ `17` §2.1 để bộ tài liệu này tự đứng được; kết quả điền vào Phụ lục A của `17`.

| # | Câu hỏi | Quyết định gì trong tài liệu này |
|---|---|---|
| P1 | `GET /api/orders` có trả phương thức thanh toán không, hay phải gọi chi tiết từng đơn? | Bước 2a của 4.1 |
| P2 | `AccountList` trả gì; tạo tài khoản "Trừ điểm" rồi đọc `AccountId` | Hằng số N-04 |
| P3 | Thu ngân bấm được phương thức đó trên màn bán hàng? Bill in tên gì? | Nghiệm thu thao tác quầy (CP4) |
| P4 | Lọc đơn theo thời gian được không; đơn void mang `Status` nào? | Mốc kéo 4.1 + điều kiện void 4.2 |
| P5 | `PartnerSave` ghi được `Point`/`Description`? | Bật/tắt 4.5 |
| P6 | Giới hạn tần suất, cỡ trang tối đa? | `POS365_PULL_MINUTES`, cỡ trang §3 |
| P7 | Trường `Password` của Partner có khi nào mang giá trị thật? | Mức nghiêm của `strip_sensitive()` §3 |

Kèm hai việc hành chính của CP0: lập **tài khoản API riêng** và hỏi POS365 về **cửa hàng /
chi nhánh thử** (K7) — có nó thì mọi phép thử về sau không chạy trên quán thật.

## 6. Kịch bản hỏng & đáp án (soát lại lúc code review CP2)

| Kịch bản | Hệ phải làm gì | Cơ chế đỡ |
|---|---|---|
| Kéo đơn đứt giữa chừng, chạy lại | Không trừ ai hai lần | UNIQUE `pos_order_id` + `uniq_key S-...` |
| Beat chết qua ngày 1 | Chạy tay reset với `period` chỉ định, không nhân đôi | `uniq_key G-/E-` |
| POS365 sập nửa ngày | Task FAILED có nhật ký, tự lành ở chu kỳ sau (mốc kéo không nhích khi FAILED) | cursor chỉ tiến khi SUCCESS |
| Thu ngân quên chọn khách | Đơn nằm UNMATCHED, nổi trên màn đối soát trong ngày | D-02 |
| Quầy hủy bill sau khi đã trừ | Hoàn đúng một lần trong ≤1 giờ | 4.2 + `uniq_key R-` |
| Nhân sự nghỉ việc còn dư điểm | `revoke` về 0 + member LEFT + (nếu P5 cho) số dư soi gương về 0 | A-05/B-04 |
| Dev chạy cả bộ task ở local | Không một call nào ra ngoài | §1 + test đếm 0 |
| Đổi `POS365_PAYMENT_ACCOUNT_ID` giữa chừng | Cấm — đơn cũ hết lọc được. Muốn đổi phải chốt sổ, ghi vận hành | Tài liệu vận hành N-04 |

**Tiếp theo:** [`04-phan-quyen.md`](./04-phan-quyen.md).
