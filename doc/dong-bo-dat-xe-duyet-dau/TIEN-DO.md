# TIẾN ĐỘ — Đồng bộ app đặt xe cũ ↔ ERP

> Cập nhật trong lúc làm. Chi tiết từng pha ở [danh-sach-phase.md](danh-sach-phase.md).
> Ký hiệu: `[ ]` chưa làm · `[~]` đang làm · `[x]` xong · `[-]` bỏ / hoãn

**Trạng thái chung (16/09/2026): P0 phía ERP XONG · P1 phần phiếu + lịch sử duyệt +
tệp đính kèm + lịch sử thao tác đã CHẠY THẬT DƯỚI LOCAL.** Đã nạp 11 công ty · 22
phòng ban · 134 người · 13 xe · 13 tài xế · **1 313 phiếu** (946 dấu + 321 đặt xe +
46 giao hàng) · **1 313 phiên duyệt** (2 080 việc · 3 745 dấu vết) · **1 488 tệp
đính kèm** · **5 095 dòng nhật ký thao tác**. **Module `sync_log` đã dựng xong** —
một quyển sổ dùng chung cho mọi hệ ngoài, `tab_pos_sync_run` của Điểm cà phê đã gộp
vào đó (migration `e5a1b9c73d04`), 33 bài kiểm xanh. **Byte thật của 1 488 tệp đính
kèm đã thông 17/09** — đọc thẳng bucket app cũ bằng khóa chỉ-đọc, kiểm đủ 1 488/1 488
(xem §P6). Còn: **phần việc bên app cũ chưa động tới**, chưa lên dev, **chưa commit**.

**Bổ sung 21/09/2026 — P4 XONG (bao-CR-449):** quyển sổ nay có màn hình đọc được ở
`/system/sync-logs` (phân hệ Quản trị, khóa `sync_log`), kèm chuông 08:00 gọi người khi
có dòng lỗi quá 24 giờ chưa ai vá. Mới ở **dev**, chưa lên prod. Đây là lần đầu người
không mở được terminal cũng tra được câu *"phiếu bên app cũ sang được chưa, hỏng vì gì"*.

**Bổ sung 21/09/2026 — sổ đồng bộ phía APP CŨ (bao-CR-452):** thêm nhánh `sync_logs` + tab **Đồng bộ
ERP** trong màn Quản trị của app cũ, giữ đúng phần mà sổ ERP không thể biết — những lượt
bắn **không bao giờ tới nơi**. Mã xong và bài kiểm xanh, **chưa commit chưa deploy**;
chặn duy nhất là đại ca dán đoạn Luật Firebase cho nhánh mới. Nhân đây gỡ luôn cái bộ
chạy test app cũ hỏng từ 17/09: thủ phạm là **chữ `đ` trong đường dẫn**, không phải lệch
phiên bản như hai dòng nhật ký trước đã ghi.

**Cách chạy test app cũ cho tới khi ai đó dời thư mục sang đường dẫn không dấu.** Lượt này
em chạy bằng một cấu hình tạm rồi xóa đi (không commit vào repo app cũ, vì nó sẽ hỏng ngay
khi có tệp kiểm nào `import 'cloudflare:test'` — hiện **không tệp nào** dùng). Cần chạy lại
thì dựng lại đúng tệp này rồi `npx vitest run --config vitest.node.config.mts`:

```ts
// my-firebase-api/vitest.node.config.mts — TẠM THỜI, không commit
import { defineConfig } from "vitest/config";
export default defineConfig({
  test: { environment: "node", setupFiles: ["./test/setup.ts"], include: ["test/**/*.test.ts"] },
});
```

Cách chữa dứt điểm là dời cả cây mã sang đường dẫn ASCII (`app dat xe`), không phải dựng
junction — Node tự quy đường dẫn về lối thật nên junction vô hiệu.

---

## Chặn đường — phải gỡ trước khi vào P0

| | Việc | Ai | Ghi chú |
|---|---|---|---|
| [x] | H-01 Người duyệt ký ở đâu | Đại ca | **Xong 15/09 — QĐ-I: ký được ở CẢ HAI, không đụng luồng bên nào.** Đường nối chỉ chuyển kết cục, không chuyển tiến trình. Thiết kế ở `mo-ta-ky-thuat.md` mục 15 |
| [ ] | Rà cho hai danh sách người duyệt trùng nhau | Đại ca + em | **Không chặn đợt nối.** QĐ-J hạ mức việc này xuống: giai đoạn 1 người ta vốn duyệt ở app cũ theo quyền của app cũ, nên chỉ cần rà **một lần ở mốc chuyển giai đoạn** |
| [ ] | Rà xem ERP đã làm được **mọi** thao tác người dùng đang làm trên app cũ chưa | em | Điều kiện số 1 để chuyển giai đoạn 2 (QĐ-J). Chưa rà lượt nào |
| [x] | H-02 Nạp lịch sử có bắn thông báo không | Đại ca | **Đã trả lời 15/09 — KHÔNG thông báo.** Tắt cả chuông lẫn email suốt đợt nạp |
| [x] | H-03 Có nạp môi trường DEV không | Đại ca | **Đã trả lời 15/09 — nạp thử dev trước**, ổn rồi mới lên prod |
| [x] | H-04 Công ty mặc định khi không tra ra | Đại ca | **Đã trả lời 15/09** — phiếu bắt buộc có công ty + phòng ban, cấm `0`, tra không ra thì Dego Holding. Thành QĐ-G |
| [x] | **H-05 Thương hiệu tương ứng cái gì bên ERP** | Đại ca | **Đã đóng 15/09 — thương hiệu CHÍNH LÀ pháp nhân, khớp 11/11** với `tab_company` (9 khớp bằng mã số thuế). Thành **nấc 0**, áp cho cả ba loại phiếu. Xem `doi-chieu-truong` mục 10.5–10.6 |
| [x] | H-06 Dego Holding là `id 1` hay `id 16` | Đại ca | **Đã trả lời 15/09 — `id 1`** (mã `DEGO`) |
| [x] | **H-07 Có điền pháp nhân trước khi nạp không** | Đại ca | **Đã đóng 15/09 — KHÔNG cần.** Có nấc 0 (`brandId`) rồi thì hồ sơ nhân sự thiếu `company_id` không chặn gì. Nấc 1/nấc 2 tụt xuống làm đường lùi |
| [ ] | Kiểm pháp nhân tra ra **có tồn tại thật** trước khi gán | Kỹ thuật | có 1 nhân sự mang `company_id = 15` mà công ty `id 15` không tồn tại |
| [x] | **H-09 Mã số thuế hai dòng Dr.Xanh lệch giữa hai hệ** | Đại ca | **Đã trả lời 16/09 — ERP đúng, app cũ thiếu dữ liệu.** Thành **QĐ-K**. Hai chuỗi số trong tên thương hiệu app cũ là dữ liệu hỏng, cấm dùng để đối chiếu |
| [x] | H-10 Phòng ban lệch (app cũ 22 · ERP 18, khớp ~14) | Đại ca | **Đã trả lời 16/09 — tạo đủ 8 phòng còn thiếu, giữ nguyên tên app cũ** (kể cả `N2AGRO-KT`, `R&D`, `Mua Hàng`). Thành **QĐ-L**, chi tiết ở `doi-chieu-truong` mục 10.7 |
| [x] | H-11 App cũ còn luồng **Mua hàng** đang chạy — có mang sang không | Đại ca | **Đã trả lời 16/09 — KHÔNG mang sang, bỏ khỏi phạm vi.** Phạm vi đồng bộ chốt đúng ba thứ: đặt xe · duyệt dấu · giao hàng. Đổi lại phải **kết xuất bản tổng hợp** phiếu Mua hàng giao đại ca trước ngày tắt app. Thành **QĐ-M** |
| [x] | ~~Đếm tỷ lệ phiếu thật có điền `brandId`~~ **XONG 16/09** | em chạy | **1 313/1 313 = 100%**, 0 tham chiếu chết. Nấc 0 của QĐ-G là đường CHÍNH; nấc 1/nấc 2 vẫn giữ nhưng chỉ còn là lưới an toàn cho phiếu MỚI, không phải đường chạy của đợt nạp lịch sử |
| [ ] | Dựng bảng tra thương hiệu → (`company_id`, `department_id`) | Kỹ thuật P0 | **Đổi cách làm theo QĐ-K:** khóa tra là **`id` thương hiệu**, KHÔNG phải tên và cũng không phải mã số thuế (tên app cũ đã biết là có thể sai; MST nằm chìm trong chuỗi tên; ERP lại có 2 dòng cùng MST `1801722464`). Lập một lần bằng mắt rồi cố định |
| [x] | H-08 Dọn dòng công ty trùng `id 16` | Đại ca | **Đã trả lời 15/09 — tạm dùng `id 1`, dọn sau** trong đợt riêng. Mã đồng bộ coi `1` và `16` là cùng một công ty |
| [x] | Lấy danh sách `brands` thật, so với `tab_company` và `tab_department` | Đại ca cấp ảnh 15/09 | **Xong — 11/11 khớp `tab_company`.** Còn thiếu **id** của từng thương hiệu (ảnh chỉ có tên) để dựng bảng tra |
| [x] | ~~Kết xuất Firebase một lượt~~ **XONG 16/09** | đại ca | Kết xuất **toàn bộ** CSDL `api-degoholding-com` (9,82 MB, 13 nhánh) thay vì hai nhánh lẻ. Bốn số đo đã có: bảng tra 11 thương hiệu · 22 khóa phòng ban · `brandId` **100%** · Mua hàng **0 phiếu**. Ghi ở [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.8 |
| [x] | ~~H-12 Một phiếu thuộc NHIỀU pháp nhân thì ERP lưu thế nào~~ **TỰ ĐÓNG 16/09** | — | **Không chặn gì cả.** ERP đã có bảng nối `tab_seal_request_company` và `core/scoping.py` lọc phạm vi phiếu dấu **theo bảng nối** → 121/123 ca không mất gì; phiếu đặt xe 0/321 ca. Còn đúng **2 phiếu giao hàng**, xử theo cách đã chốt từ trước: lấy phần tử đầu + cờ `multi_brand` vào sổ |
| [ ] | **Suy phòng ban cho 367 phiếu đặt xe + giao hàng** | Kỹ thuật P1 | `departmentId` **chỉ có ở phiếu dấu** (946/946); `CAR_BOOKING` 0/321 và `DELIVERY` 0/46 không mang trường này. Suy qua `createdBy` → `users[uid].departmentId`: phủ **367/367** vì cả 136 người dùng đều có phòng ban hợp lệ |
| [x] | ~~**Script tạo 8 phòng ban bên ERP** (QĐ-L)~~ **XONG 16/09, và con số thành 8 chứ không phải 12** | em viết | `sync_master_data.py` — chỉ THÊM, chạy lại được, khớp theo `legacy_id`, `company_id = 0` như 18 dòng sẵn có. **Đại ca chốt "gần trùng thì dùng của ERP"** nên bốn phòng gần trùng (378/1313 phiếu) GỘP về phòng ban ERP thay vì tạo mới; bốn dòng script đã lỡ tạo ở lượt trước bị xóa sau khi đếm đủ **0 tham chiếu** trên cả 18 cột `department_id` của hệ. Local xong, dev/prod chưa (H-03) |
| [x] | ~~Kết xuất bản tổng hợp phiếu luồng Mua hàng (QĐ-M)~~ **BỎ 16/09** | — | Đo ra **0 phiếu** trên luồng `wf_purchase_01`. Không có gì để tổng hợp; nghĩa vụ của QĐ-M tự tiêu, bước 6 của P8 bỏ theo |
| [ ] | Chốt cách xử `legacy_id` unique | Kỹ thuật | chặn migration P0 |
| [x] | ~~Chốt thêm `notes` vào `StopItem` hay không~~ **CÓ, 16/09** | Kỹ thuật | Đo ra **59 điểm dừng, 25 điểm có ghi chú thật** (*"Rước sale"*). Bỏ trường là mất 25 mẩu tin không tái tạo được. `StopItem` cũng cần `address` · `contactName` · `contactPhone` |
| [x] | ~~Chốt `on_leave` của tài xế đổi thành gì~~ **KHÔNG CÒN LÀ VẤN ĐỀ, 16/09** | Kỹ thuật | `driver.status` trong dữ liệu thật **chỉ có đúng một giá trị `available`** (13/13). Ánh xạ kiểu gì cũng không mất dữ liệu — chọn cách đơn giản nhất, đừng dựng bảng ánh xạ cho tập một phần tử. Lưu ý 2/13 tài xế là người ngoài (`isExternal`) |
| [x] | Chốt trạng thái `sealed` / `delivered_to_staff` | Nghiệp vụ | **Đã chốt 15/09** — QĐ-H: ERP thêm `SEAL_DELIVERED = 8`, ánh xạ kín hai chiều |
| [ ] | Lấy số lượng thật (phiếu, xe, tài xế, tệp, dung lượng R2) | Kỹ thuật | ước lượng P1 và P8 |
| [ ] | Kết xuất dữ liệu thật để soi cấu trúc | Kỹ thuật | định nghĩa kiểu app cũ không đầy đủ |

---

## P0 — Nền móng

| | Việc | Bên |
|---|---|---|
| [x] | Module `sync_log` (model, schema, service, controller) — **một quyển sổ CHUNG cho mọi hệ ngoài**, không phải sổ riêng của app đặt xe. Hai hạt trong cùng một bảng qua cột `grain`: `RUN` (một lượt chạy nền — con trỏ thời gian, số kéo/ghi/bỏ) và `RECORD` (một bản ghi đi qua). Thêm hệ nguồn = thêm một adapter ở `registry.py`, không đụng model/service/controller | ERP |
| [x] | **Gộp `tab_pos_sync_run` của Điểm cà phê vào `tab_sync_log`** — migration `e5a1b9c73d04` dời dữ liệu rồi xóa bảng cũ. Đại ca chốt *"cái gì cũng tách bảng riêng thì quản lý kiểu gì nổi"*. ⚠️ Bộ mã trạng thái **lùi một bậc** vì `SyncStatus` chèn `PENDING = 1` lên đầu: `RUNNING` 1→2, `SUCCESS` 2→3, `FAILED` 3→4, `SKIPPED` 4→5. Ba chỗ phải khớp nhau: enum · bảng dịch trong migration · bảng màu của `coffee-ledger-page.tsx` | ERP |
| [x] | Thêm model vào `all_models.py` | ERP |
| [x] | Cột `legacy_id` cho **7** bảng — `LegacyIdMixin` + migration `b7c2e4a91f30`. Chạy LOCAL 16/09. 4 bảng trong bản vẽ gốc là thiếu: cần thêm `tab_employee` (khớp 136 người dùng), `tab_vehicle`, `tab_driver`. **Index, KHÔNG unique** — MySQL coi mỗi chuỗi rỗng là một giá trị thật nên unique chặn ngay hàng ERP thứ hai | ERP |
| [x] | Bảng tra danh mục + script `scripts/legacy_sync/sync_master_data.py` — chạy LOCAL 16/09, **số chốt sau khi đại ca quyết gộp**: 11 công ty đóng dấu · **14** phòng ban đóng dấu (10 trùng tên tuyệt đối + 4 gộp tay) · **8** phòng ban tạo mới · 4 bản trùng tự tạo ở lượt trước đã xóa · 22/22 khóa app cũ tra ra phòng ban ERP. Chạy lần ba: 0 thay đổi | ERP |
| [x] | Khớp **136 tài khoản app cũ → `tab_employee`** — `sync_users.py`, chạy LOCAL 16/09. Đường tự động DUY NHẤT là **email khớp 1-1**; ra **95 người, gánh 1 137/1 313 phiếu (87%)**. 41 ca còn lại KHÔNG đoán, xếp ra báo cáo chờ đại ca chốt rồi ghi vào `USER_MANUAL_MAP`/`USER_SKIPPED`. Chạy lại: 0 thay đổi | ERP |
| [x] | **Đại ca chốt hai ca người dùng 16/09 → nay khớp 122/136.** (1) Hồ sơ trùng thì **lấy id nhỏ** — 38 (không phải 201); đã rà 64 cột tham chiếu của hệ, **id 201 không dính chứng từ nào** nên chọn xong là xong, không phải cập nhật gì. Ghi vào `USER_MANUAL_MAP`. (2) **26 người không có hồ sơ → tạo mới** bằng `create_missing_employees.py`: 26 hồ sơ `NSU231…NSU256` (id 294…319) + **22 tài khoản** vai trò `employee`. Bốn người app cũ đã khóa (Võ Thị Lan Anh · Trần Thị Kim Ngoan · Huỳnh Thị Đẹp · Huỳnh Thị Ngọc Thoa) tạo hồ sơ TẮT, **không cấp tài khoản** | ERP |
| [x] | Khớp **13 xe + 13 tài xế** — `sync_fleet.py`, chạy LOCAL 16/09, **13/13 và 13/13, không sót bên nào**. Cố ý KHÔNG dò lúc chạy: bảng tra người soát tay, script chỉ thi hành và soi lệch (khóa lạ · hàng ERP không ai trỏ tới · hai khóa trỏ chung một hàng). Chạy lại: 0 thay đổi | ERP |
| [x] | **Đại ca chốt 14 ca "tên trùng mà email khác" 16/09: dùng hồ sơ ERP.** Ghi thẳng vào `USER_MANUAL_MAP` (12 dòng) + `USER_SKIPPED` (2 dòng). Hai UID thừa là của cùng một người — *Phạm Lê Triết Giang* có **ba** tài khoản app cũ trỏ về hồ sơ 221, mà `legacy_id` chỉ có MỘT cột nên không diễn đạt được nhiều-về-một; hai UID kia đánh dấu bỏ và **bộ nạp phiếu phải tra `USER_MANUAL_MAP` TRƯỚC rồi mới tới `legacy_id`**, không thì phiếu của hai UID đó mất người tạo. Kết: **134 đóng dấu + 2 bỏ = 136, không còn ai chờ**. ⚠️ `assistant.n2sbiovn@gmail.com` (→ hồ sơ 75) là **hòm thư dùng chung**, đại ca chốt vẫn gán | ERP |
| [x] | **Luật chung: tài khoản trùng thì luôn giữ id nhỏ nhất** (đại ca chốt 16/09). Script `scripts/dedupe_accounts.py`, chạy LOCAL 16/09 — **3 cụm, xong cả 3**: `ntktrang.idagroup@gmail.com` (giữ tk 47/hồ sơ 38, bỏ 210/201) · `ntnhan.idaglobal@gmail.com` (giữ 185/176, bỏ 205/196) · `hgbao.idagroup@gmail.com` (giữ tk 1, bỏ tk 3/hồ sơ 253). Không xóa gì, chỉ **xóa trống email + tắt hoạt động** hồ sơ thừa qua `employee_service.update_employee` để dây bao-CR-400 chạy đủ (khóa tài khoản · đá phiên · nhật ký). Chạy lại: 0 cụm | ERP |
| [x] | Cột `source`, `external_id` cho `tab_file` — rỗng = byte nằm ở kho R2 của ERP, khác rỗng = `file_key` là khóa của KHO KHÁC. Mọi đường đọc byte phải rẽ theo cột này trước (`core/legacy_files.py`), không thì R2 của ERP trả 404 cho một tệp vẫn còn sống | ERP |
| [x] | Cột `warnings` + bộ cờ cảnh báo trong `tab_sync_log` — cờ chung ở `constants.COMMON_WARNINGS`, cờ riêng của từng nguồn khai trong adapter. Ghi cờ có khử trùng và cắt an toàn theo trần cột | ERP |
| [x] | Hàm tra pháp nhân ba nấc (QĐ-G), cấm trả về `0` — **bản của đợt NẠP LỊCH SỬ** là `_companies_of` trong `import_tickets.py` (chạy thật 1 313/1 313 phiếu); **bản của chiều nhận về** nay là `legacy_datxe/resolver.py` (`PeopleResolver` + `LegacyCatalog`), tra theo `legacy_id` → khóa tự nhiên (đóng dấu `legacy_id` lại) → tạo mới, mà **chỉ xe và tài xế** mới được tạo và còn phải bật `SYNC_DATXE_AUTO_CREATE` | ERP |
| [x] | Khai entity `sync_log` ở `ENTITIES` + `SCOPE_FIELDS` + rà `_SYS_ENTITIES` — **MỘT khóa cho mọi nguồn** (`write` = nút *Chạy lại*). `SCOPE_FIELDS` để `PUBLIC` có chủ ý: một dòng sổ mô tả bản ghi của HỆ BÊN KIA, lúc nó hỏng thì thường ERP chưa có hàng nào để mà lọc phạm vi — lọc là giấu đi đúng những ca hỏng nặng nhất. Đã thêm vào `_SYS_ENTITIES` của `seed.py` để không rơi vào `_PUR_MANAGER_PERMS`, và thêm vào `ENTITIES` bên `frontend-v2` (62 → **63**) | ERP |
| [x] | Migration Alembic, kiểm `alembic heads` ra một head — `b7c2e4a91f30` (cột `legacy_id`) · `c1d4f8a37b62` · **`e5a1b9c73d04`** (dựng `tab_sync_log`, dời dữ liệu POS365 vào, xóa `tab_pos_sync_run`). `upgrade head` chạy sạch trên local; dò lệch bằng `--autogenerate` ra **0 thay đổi** cho bảng mới | ERP |
| [x] | Biến môi trường, công tắc để tắt — `SYNC_DATXE_ENABLED` · `SYNC_SHARED_SECRET` · `SYNC_LEGACY_API_BASE`. ⚠️ Cờ của POS365 là **cầu dao NGẮT** (`POS365_HARD_OFF`, bật = TẮT), ngược chiều — adapter khai `enabled_inverted` thay vì đổi tên biến đang chạy thật ở prod | ERP |
| [x] | Hàm ký / kiểm chữ ký + bài kiểm — `core/sync_signature.py` (phía ERP). Khóa theo TỪNG NGUỒN, lệch giờ quá 5 phút thì từ chối. ⚠️ **Bài kiểm lôi ra một lỗ thật**: `hmac.compare_digest` ném `TypeError` khi chuỗi có ký tự ngoài ASCII, tức một header chữ ký có dấu là đổ **500** thay vì bị từ chối gọn — nay so bằng **bytes** | ERP |
| [x] | Hàm ký / kiểm chữ ký phía app cũ — `signErpBody` ở `src/utils/erp-sync.ts` (HMAC-SHA256 qua WebCrypto). App cũ chỉ **ký để gửi đi**, không kiểm chữ ký của ai vì đường đồng bộ là một chiều. Hai mẫu chữ ký trong bài kiểm tính từ chính `app/core/sync_signature.py` của ERP, một mẫu có dấu tiếng Việt — hai đầu lệch bảng mã thì chỉ phiếu CÓ DẤU bị 401, kiểu hỏng khó lần nhất | App cũ |
| [x] | Ba trường `updatedAt`, `erpId`, `syncStatus` — **cả ba đã ghi thật 21/09**. Khai kiểu ở `src/types/db.types.ts`, đều KHÔNG bắt buộc: phiếu có trước ngày nối ERP không mang ô nào. `syncStatus` cố ý chỉ có **hai** giá trị `synced`/`failed`, không có giá trị thứ ba cho "chưa bắn" — phiếu chưa bắn thì **vắng khóa**, và vắng khóa khác hẳn `failed` về nghĩa. `erpId` và `syncStatus` gom vào **cùng một cú PATCH**: hai lượt ghi liền nhau lên một phiếu là hai lần đánh thức mọi máy đang nghe nhánh `requests` | App cũ |
| [x] | Mọi đường ghi đều cập nhật `updatedAt` — `stampUpdatedAt` ở `src/utils/db.helpers.ts`, cắm vào **cả ba** đường ghi: `createRequestInDb` (PUT) · `updateRequestInDb` (PATCH) · `patchRequest` của `driver.service.ts`. Đường thứ ba là đường **dễ sót nhất** — nó không đi qua tầng `db/`, mà bốn nhịp của tài xế đều chạy qua đó | App cũ |
| [x] | Khai `.indexOn: ["updatedAt"]` trong Rules — **đại ca tự thêm 17/09, cả dev lẫn prod**. Em kiểm lại dự án dev bằng khóa đọc của ERP: `requests` đã có. Hai nhánh `vehicles`/`drivers` **cố ý không khai** — vòng quét chỉ hỏi nhánh `requests` (`NODE_REQUESTS` ở `tasks.py`), xe và tài xế đi bằng đường tra theo id | App cũ |
| [~] | Nhánh `sync_logs` + màn hình xem sổ — **mã xong 21/09, chờ đại ca mở Luật Firebase.** Sổ này KHÔNG chép lại `tab_sync_log` của ERP: sổ bên kia ghi những gì **tới nơi**, còn quyển này giữ đúng chỗ mù của nó — những lượt bắn **không bao giờ tới** (ERP sập, hết giờ chờ, sai khóa), thứ mà trước nay chỉ rơi vào `console.error` của Worker. **Một phiếu một dòng**, khóa là `legacyId` trần: trượt nữa thì đè, sang được thì xóa — nên nhánh tự chặn trên (ERP sập cả ngày thì sổ dày bằng số PHIẾU chứ không phải số LƯỢT) và tự lành theo vòng quét 3 phút. Cửa đọc `GET /v1/administrator/sync-logs`, màn hình là tab **Đồng bộ ERP** trong Quản trị hệ thống, **cố ý không có nút xóa**. ⚠️ Mọi cú ghi sổ đều **nuốt lỗi**, nên chưa mở Luật thì không ai gãy, chỉ là sổ rỗng vĩnh viễn — đoạn Rules phải dán nằm ở cuối `src/db/sync-logs.db.ts` | App cũ |
| [~] | Biến bí mật `SYNC_ENABLED`, `SYNC_SHARED_SECRET` — **khóa ký đã đặt xong 19/09** dạng **Secret** trên worker `my-firebase-api-dev` (đại ca dán tay trên Dashboard; `wrangler secret put` chạy không được vì máy chưa đăng nhập Cloudflare). `SYNC_ENABLED` = `"true"` cho dev nằm trong PR #111, **bật thật khi PR merge**. ⚠️ Hai biến thường phải khai trong `wrangler.jsonc`, khóa ký thì tuyệt đối không — `wrangler deploy` gỡ mọi Variable vắng mặt trong khối `vars`, còn tệp cấu hình thì vào git | App cũ |

**Tiêu chí xong:** migration lên/xuống được trên bản sao DB dev; tạo phiếu bên app cũ thấy `updatedAt` nhảy; bài kiểm chữ ký xanh; hành vi hai hệ **không đổi**.

---

## P1 — Nạp lịch sử một lần

| | Việc |
|---|---|
| [x] | Script nạp phiếu — tên thật `scripts/legacy_sync/import_tickets.py`, mặc định chỉ xem trước, `--apply` mới ghi |
| [x] | Bảng tra người dùng qua email |
| [x] | Nạp xe |
| [x] | Nạp tài xế |
| [x] | Nạp phiếu duyệt dấu (946) |
| [x] | Nạp phiếu đặt xe công tác (321) |
| [x] | Nạp phiếu giao hàng (46) |
| [x] | Nạp **lịch sử duyệt** vào `tab_approval_instance` + `tab_approval_task` + `tab_approval_action` (xem §P1.1) — `scripts/legacy_sync/import_approval_history.py`, chạy thật dưới local 16/09: **1 313 phiên · 2 080 việc · 3 745 dấu vết** |
| [x] | Nạp **5 mốc điều phối chuyến** vào cột của `tab_vehicle_booking` (xem §P1.1) — ba mốc `dispatched`/`trip_started`/`trip_completed` **đã vào** theo phiếu, lịch sử vá nốt **17 ô còn trống** (13 `dispatched_at` · 4 `driver_status`) |
| [x] | Nạp **tệp đính kèm** (946/946 phiếu dấu có `attachedFileIds`) — `scripts/legacy_sync/import_attachments.py`, chạy thật dưới local 16/09: **1 488 dòng `tab_file` · 1 488 dây** vào `seal_request`, nhãn `signed_doc`. 1 519 lượt tệp − 31 lượt trùng **trong cùng một phiếu** = 1 488; 0 tệp dùng chung giữa hai phiếu. Chỉ phiếu dấu có tệp (đếm lại trên bản kết xuất: phiếu xe **0**) — xem §P6 |
| [x] | Nạp **lịch sử thao tác** vào `tab_audit_log` (thẻ *Lịch sử thao tác*) — `scripts/legacy_sync/import_audit_log.py`, chạy thật dưới local 16/09: **5 095 dòng** (2 841 phiếu dấu + 2 254 phiếu xe), phủ **1 313/1 313 phiếu**, 0 mã hành động lạ. Xem §P6.1 |
| [x] | Kiểm lại hai đợt nạp trên qua **đúng đường màn hình** — `scripts/legacy_sync/verify_attachments_and_audit.py`, 16/09: không lỗi |
| [ ] | Xuất CSV các chỗ vướng |
| [x] | Chạy thử dưới local, đọc số đếm, sửa quy tắc dịch |
| [x] | Chạy thật dưới local, soi mắt phiếu |
| [ ] | Chạy thử trên dev, đọc CSV, sửa quy tắc dịch |
| [ ] | Chạy thật trên dev, soi mắt 20 phiếu |
| [ ] | Sao lưu DB prod |
| [ ] | Chạy thử trên prod |
| [ ] | Chạy thật trên prod |

**Mã phiếu nhập về** (đại ca chốt 16/09): `prefix + id đệm 0 sáu chữ số` —
`DD000789` cho phiếu dấu, `DX000789` cho phiếu xe. Không đụng bộ sinh mã của ERP:
hàm `_next_seal_code` / `_next_booking_code` lấy `max+1` trên `re.fullmatch(r"DD(\d+)")`,
mã ba chữ số cũ và mã sáu chữ số mới không bao giờ trùng nhau.

**Loại con dấu.** `tab_seal_type` trống trơn, còn 946 phiếu app cũ đều mang đúng
một chuỗi `sealTypeId = "Phê duyệt dấu"` (app cũ không cho chọn loại). Đại ca chốt
*"chưa có thì tạo trước rồi gắn sau"* → bộ nạp tự tạo **một** loại tên nguyên văn
như vậy rồi gắn cả 946 phiếu vào. Cố ý **không** nhét vào `seed_seal_types.py`:
đó là tên của loại YÊU CẦU, không phải một loại con dấu, trộn vào danh mục mẫu của
ERP là khai sai.

**Tiêu chí xong:** số phiếu khớp theo tháng và theo trạng thái; CSV vướng đã xem hết, mỗi dòng có kết luận.

### P1.1 — Lịch sử duyệt đổ vào đâu

Đại ca chốt 16/09: *"lịch sử duyệt đổ vào cái log á, log mình cũng có phần đó mà,
mà mình có luồng duyệt riêng mà ta, cũng có lịch sử duyệt giống vậy"*. Đúng — ERP
có sẵn `tab_approval_action` (*"Dấu vết duyệt — chỉ ghi thêm, không sửa, không
xóa"*, I20), và cột của nó khớp gần hết với một dòng `history` bên app cũ.

**Nhưng 5 095 dòng `history` KHÔNG phải 5 095 lượt duyệt.** Đo trên bản kết xuất:

| Nhóm | Số dòng | Đổ vào đâu |
|---|---|---|
| Lượt duyệt thật — `created` 1 313 · `approved` 2 112 · `needs_correction` 51 · `admin_canceled` 24 · `rejected` 19 · `canceled` 15 | **3 534** | `tab_approval_action` |
| Mốc điều phối chuyến — `dispatched` 333 · `driver_accepted` 324 · `trip_started` 313 · `trip_completed` 308 · `re-dispatched` 72 | **1 350** | **Cột của `tab_vehicle_booking`** |
| Sửa phiếu — `edited` | **211** | `tab_approval_action`, mã `ACTION_COMMENT` |

Nhóm giữa là chỗ dễ sai nhất: nó nằm chung một mảng với lượt duyệt nên đổ cả mảng
vào là gọn nhất — và là **nói sai một điều vào đúng cái bảng cả hệ dùng để tra
"ai đã ký"**. Tài xế bấm *Bắt đầu chuyến* không phải là người duyệt phiếu. ERP đã
có chỗ đúng cho chúng: `dispatched_by` · `dispatched_at` · `driver_status` ·
`actual_start_time` · `actual_end_time` trên chính `tab_vehicle_booking`.

Nhóm `edited` thì giữ, vì nó giải thích **vì sao có lượt duyệt thứ hai** trên cùng
một phiếu — nhưng ghi bằng `ACTION_COMMENT`, không phải `ACTION_APPROVE`.

**Bảng dịch mã**

| `action` app cũ | `tab_approval_action.action` | | `overallStatus` | `ApprovalInstance.status` |
|---|---|---|---|---|
| `created` | `ACTION_START` (1) | | `pending_approval` (34) | `INSTANCE_RUNNING` (1) |
| `approved` | `ACTION_APPROVE` (2) | | `completed` 1 192 · `fully_approved` 13 · `dispatched` 12 | `INSTANCE_APPROVED` (2) |
| `rejected` | `ACTION_REJECT` (3) | | `rejected` (19) | `INSTANCE_REJECTED` (3) |
| `needs_correction` | `ACTION_RETURN` (4) | | `needs_correction` (4) | `INSTANCE_RETURNED` (4) |
| `canceled` · `admin_canceled` | `ACTION_WITHDRAW` (5) | | `canceled` (39) | `INSTANCE_WITHDRAWN` (5) |
| `edited` | `ACTION_COMMENT` (8) | | | |

**Bốn điều đã đo, không đoán**

1. **Mọi dòng `history` đều có `userId`** (0 dòng thiếu), nên người thao tác tra
   được hết qua bảng `legacy_id` vừa khớp xong. `comment` có ở 3 376/5 095 dòng.
2. **`flow_id = 0`, `flow_version = 0`.** Phiếu cũ KHÔNG chạy theo luồng nào của
   ERP. Gán bừa một `flow_id` đang sống là khai rằng luồng đó đã ký những phiếu
   nó chưa từng thấy, và sửa luồng đó về sau sẽ đọc như thể lịch sử đổi theo.
3. **`flow_snapshot` dựng lại từ `workflowSnapshot` của chính app cũ** — app cũ có
   chụp luồng, đủ cho cả 1 313 phiếu, gọn đúng **ba** luồng: `workflow_seal_v1`
   (946 phiếu, 3 bước) · `wf_car_booking_01` (321 phiếu, 1 bước) · `wf_delivery_01`
   (46 phiếu, 1 bước). Phải **dịch sang khuôn `{"nodes":[...]}` của ERP** chứ không
   nhét nguyên dạng Firebase: `steps_service` đọc `flow_snapshot` để đếm số chặng,
   nhét sai khuôn thì mọi phiếu nhập về hiện một chặng duy nhất. Bản gốc Firebase
   giữ lại trong khóa phụ `legacy` — `doc_snapshot` chỉ đọc `nodes` nên vô hại.
4. **KHÔNG đi qua `instance_service.start`.** Hàm đó chọn luồng ERP đang sống và
   **mở việc chờ thật** cho người duyệt. Chạy nó cho 1 313 phiếu cũ là ném hơn
   nghìn việc đã xử xong vào hàng chờ của người thật.

**Thứ tự bắt buộc:** `ApprovalInstance` có `entity_id` trỏ tới phiếu ERP, nên
**phải nạp phiếu trước rồi mới nạp lịch sử duyệt** — không có đường nào khác.

#### Điều thứ năm, chỉ lòi ra khi chạy thật: PHẢI ghi `tab_approval_task`

Bản thiết kế trên chỉ nói tới hai bảng — *phiên* và *dấu vết* — và lượt `--apply`
đầu tiên làm đúng như vậy: 1 313 phiên, 3 745 dấu vết, mọi con số khớp bảng đếm.
Nhưng đọc lại qua đúng đường màn hình sẽ đọc thì **phiếu duyệt xong hiện cả ba
chặng đều "đã hủy"** — đọc thành phiếu bị rút, trên cả 1 313 phiếu.

Chỗ quyết là `steps_service._one_step`: *chặng không có việc nào + phiên đã kết
thúc = `STEP_CANCELLED`*. Bỏ bảng việc không phải "thiếu thông tin", nó là **vẽ
sai lên màn hình**. Nên bộ nạp ghi thêm bảng việc, theo hai luật:

* **Chỉ trạng thái ĐÃ ĐÓNG** — `TASK_APPROVED` · `TASK_REJECTED` ·
  `TASK_CANCELLED`. Không một dòng `TASK_PENDING`/`TASK_WAITING` nào, nên màn
  *Việc của tôi* không hề nặng thêm. Kiểm được: đếm việc theo trạng thái phải ra
  **0** ở mã 1 và 2.
* **Một chặng một dòng, lấy lượt xử lý CUỐI CÙNG của chặng đó.** Phiếu bị trả về
  ở chặng 3 rồi duyệt lại chính chặng 3 mà ghi cả hai dòng thì `_one_step` thấy
  lẫn «đã hủy» trong nhóm và vẽ chặng đó thành "trả về" trên một phiếu đã duyệt
  xong. Đường đi đầy đủ vẫn còn nguyên trong `tab_approval_action` — đó mới là
  sổ dấu vết. Vì vậy 2 112 lượt `approved` gom lại còn **2 052** dòng việc, và
  51 lượt `needs_correction` còn **9**.

Dấu vết nào là lượt quyết kết cục thì trỏ `task_id` sang dòng việc của chặng;
những lượt trước để trống. Kiểm được: **số dấu vết có `task_id` = số việc = 2 080**.

#### Và một lỗi CÓ SẴN của ERP mà lần nạp này lôi ra

Vá xong bảng việc thì phiếu đã duyệt vẫn còn **990 chặng** mang trạng thái
`cancelled`. Đo ra nguyên nhân, không đoán: luồng dấu khai **3 chặng trên cả 946
phiếu**, mà chặng 2 tên nguyên văn là **"GĐ Quản lý thương hiệu duyệt (Tùy
chọn)"** và **chạy 0/946 lần**; thêm 115 phiếu bật `isSkipApproval` nhảy thẳng
lên chặng 3 nên chặng 1 cũng không chạy.

Tức dữ liệu đúng, chỗ sai nằm ở `steps_service`: nó gộp **chặng không chạy vì
không cần** với **chặng chết vì phiếu bị rút** vào chung một màu. Lỗi này có
trước và không liên quan gì tới app cũ — phiếu ERP đi nhánh rẽ cũng dính y hệt.
Đã thêm trạng thái chặng thứ bảy **`STEP_SKIPPED` ("skipped")**, dùng khi chặng
không có việc nào **và phiên đã DUYỆT XONG**; phiên kết thúc bằng từ chối / trả
về / rút thì chặng trắng vẫn là `cancelled`, vì ở đó nó chết theo phiếu thật.
Khai kèm bên TypeScript ở `hr/types/leave.ts`. Bài kiểm:
`test_nghi_phep_hop_viec_duyet.py::test_chang_KHONG_CHAY_tren_phieu_da_duyet_khong_doc_thanh_da_huy`.

#### Cách kiểm

`scripts/legacy_sync/verify_approval_history.py` — **đọc qua chính
`steps_service` và `serializer`**, không đếm dòng suông, vì đếm dòng chính là
thứ đã cho lượt nạp đầu tiên một bảng điểm toàn đúng.

```
docker compose exec -T -e PYTHONPATH=/app api \
    python /app/scripts/legacy_sync/verify_approval_history.py
```

Ba con số phải đúng: việc ở trạng thái 1 hoặc 2 = **0** · phiên đã duyệt không
còn chặng nào `cancelled` · số dấu vết có `task_id` = số việc.

**ĐÃ QUYẾT — QĐ-N, đại ca chốt 21/09/2026: phương án A, để app cũ ký nốt.**
34 phiếu `pending_approval` (còn `pendingApproverUids`) giữ nguyên như đang nhập:
phiên ở `INSTANCE_RUNNING`, **không mở việc chờ** bên ERP. Người duyệt ký bên app
cũ, kênh P2 đẩy sự kiện sang, ERP tự đóng phiên. Không phải viết thêm bước nào.

Hệ quả phải biết rõ, vì nó có hai mặt và mặt mất không tự nói ra:

- **Được:** phiên còn mở chiếm `running_slot`, nên `block_legacy_path` khóa ba nút
  duyệt thẳng bên ERP. Đúng ý muốn trong lúc chữ ký vẫn đặt ở app cũ — hai nơi
  cùng ký được một phiếu là nguồn của mâu thuẫn không gỡ được.
- **Mất:** **không ai trong ERP duyệt được 34 phiếu đó.** Chúng thấy được, tìm
  được, nhưng đứng im. Ai mở ra mà không biết chuyện này sẽ tưởng hệ thống hỏng.

**Điều kiện lật quyết định:** nếu định **tắt app cũ trước khi 34 phiếu đó ký
xong** thì phải làm phương án B — duyệt qua 34 phiên, đọc `pendingApproverUids`,
quy từng tài khoản app cũ ra người dùng ERP, rồi mở việc chờ **đúng tại chặng
phiếu đang đứng**. Không dùng lại `instance_service.start` được: hàm đó dựng luồng
từ chặng đầu, tức là đẩy phiếu lùi lại và bắt người ta ký lại từ đầu.

Danh sách 34 phiếu in ra ở cuối mỗi lượt chạy `import_approval_history.py` — số
đó tự teo dần mỗi ngày, và đó chính là lý do A rẻ hơn B.

---

## P2 — Chiều app cũ → ERP

| | Việc | Bên |
|---|---|---|
| [x] | Đường nhận `POST /api/sync/datxe/events` | ERP |
| [x] | Kiểm chữ ký, chặn gói cũ gửi lại | ERP |
| [x] | Chặn xử trùng theo `event_id` và `legacy_id` | ERP |
| [x] | Hằng số "trường app cũ làm chủ", dùng một chỗ | ERP |
| [x] | ~~Bài kiểm: nhận cập nhật **không** đụng trạng thái và điều phối~~ → **§9.4 đảo luật ngày 17/09**: ERP đang chỉ là bản sao nên **ghi đè hết, trừ ghi rỗng đè lên đang có**. Bài kiểm nay canh luật mới, kèm ca xóa trắng ô xe của chuyến đã hoàn thành | ERP |
| [ ] | Bài kiểm: khai trần độ dài ở tầng schema | ERP |
| [x] | Bắn chuông sau khi ghi `requests` — `src/utils/erp-sync.ts`, móc ở **cả ba** đường ghi (19/09) | App cũ |
| [x] | Gọi hỏng không làm hỏng việc người dùng | App cũ |
| [x] | Nhận `erpId` ghi ngược | App cũ |
| [ ] | Cờ chặn bắn ngược — làm cùng P3, giờ chưa có chiều ngược nào để chặn | App cũ |
| [x] | Đại ca đặt `SYNC_SHARED_SECRET` cho worker dev — **xong 19/09**, dán tay trên Dashboard dạng Secret. `wrangler secret put --env dev` chạy không được vì máy chưa đăng nhập Cloudflare (`wrangler whoami` báo chưa xác thực); token deploy nằm trong GitHub Actions chứ không nằm dưới máy | Đại ca |
| [x] | Bật `SYNC_ENABLED` = `"true"` cho worker dev — PR #111 đã gộp, CI xanh (172 bài kiểm), worker `my-firebase-api-dev` bản `e5becb27` áp đúng cờ | App cũ |
| [x] | **Chạy thử đầu-cuối XONG 19/09 10:50** — đại ca tạo một phiếu đóng dấu bên app dev, ERP dựng ngay `DD000863` (sổ dòng 4763), rồi worker ghi ngược `erpId = 863` vào Firebase. Chữ ký qua cửa ngay lần đầu, kể cả lý do có dấu tiếng Việt (*"thử nghiệm đồng bộ"*). Không dòng nào bị từ chối chữ ký. ⚠️ `updatedAt` sau cú ghi ngược **vẫn nguyên** `03:50:04.151` — luật "ghi ngược không đóng dấu" đứng vững trên hạ tầng thật | Em |

**Tiêu chí xong:** tạo phiếu bên cũ, 5 giây sau có bên ERP; sửa phiếu thì nội dung đổi mà trạng thái ERP giữ nguyên; tắt ERP thì app cũ vẫn tạo được, sổ có dòng lỗi.

**Khác bản vẽ, cố ý:** §P2 bảo móc ở tầng service. Em móc ở **tầng DB** — `createRequestInDb`, `updateRequestInDb`, và `patchRequest` của tài xế. Tầng service có hơn mười chỗ gọi `updateRequestInDb` rải khắp `admin` / `approval` / `dispatch` / `request`, bỏ sót một chỗ là loại lỗi im lặng đã dính mấy lần: phiếu vẫn ghi, người dùng vẫn thấy bình thường, chỉ ERP là không bao giờ biết. Ba đường ghi kia trùng đúng tập hợp với chỗ đóng dấu `updatedAt`, tức là đã có bài kiểm canh sẵn.

---

## P3 — Chiều ERP → app cũ

| | Việc | Bên |
|---|---|---|
| [ ] | Chỗ phát tín hiệu: duyệt, từ chối, trả về, điều phối, tài xế, km/chi phí | ERP |
| [ ] | Đẩy qua Celery, không gọi thẳng trong lượt người dùng | ERP |
| [ ] | Chỉ phát cho phiếu có `legacy_id` | ERP |
| [ ] | Gói kèm biển số, tên xe, tên tài xế, SĐT dạng chữ | ERP |
| [ ] | Biến ngữ cảnh `sync_in_progress` | ERP |
| [ ] | Van chặn vòng lặp (quá 20 dòng/giờ thì dừng) | ERP |
| [ ] | Đường nhận `POST /api/v1/sync/erp-events` | App cũ |
| [ ] | Cờ "đến từ ERP", không bắn ngược | App cũ |
| [ ] | Màn hình hiện thông tin xe/tài xế nhận về | App cũ |

**Tiêu chí xong:** duyệt bên ERP thì 30 giây sau app cũ đổi theo; gán xe thì hiện đúng biển số và tài xế; mỗi lần đổi chỉ sinh một dòng sổ mỗi bên.

---

## P4 — Màn hình sổ đồng bộ

| | Việc |
|---|---|
| [x] | Màn **`/system/sync-logs`** trong `frontend-v2` — `system/pages/sync-log-list-page.tsx`, menu *Quản trị › Sổ đồng bộ*, khóa `sync_log` (bản vẽ ghi `/system/sync-log` số ít, đường thật là số nhiều cho khớp nếp đặt tên của phân hệ) |
| [x] | Lọc theo trạng thái / hạt / nguồn / đối tượng / ngày / mã bên cũ / lượt chạy — mặc định **7 ngày**, cố ý không có mục "tất cả" (sổ này dày nhất hệ thống) |
| [x] | Xem chi tiết: nguyên cục JSON và nguyên văn lỗi — `sync-log-detail-sheet.tsx`, cục dữ liệu để **chuỗi thô**, không `JSON.parse` |
| [x] | Nút chạy lại (quyền `sync_log.write`) — chỉ nằm trong ngăn chi tiết, chỉ hiện với dòng *lỗi* / *chờ* |
| [x] | Thẻ đếm đầu trang — đếm theo trạng thái, thẻ *lỗi* đổi màu khi khác 0, bấm vào là lọc |
| [x] | Bộ lọc "chưa gắn được người" — nút riêng cho cờ `no_employee`, kèm ô chọn mọi cờ cảnh báo khác |
| [x] | Cảnh báo 08:00 cho dòng lỗi quá 24 giờ — `sync_log/tasks.py::alert_stale_failures`, chuông trong hệ (không email) |

**Tiêu chí xong:** dòng lỗi cố ý tạo hiện đúng trên màn; bấm chạy lại thành công, không đẻ phiếu trùng.

**Đã xong 21/09/2026** (bao-CR-449) — dev, chưa lên prod.

⚠️ **Chuông KHÔNG đếm thẳng theo trạng thái.** `clone_for_retry` cố ý không sửa dòng cũ
(luật §3.2 của `mo-ta-ky-thuat.md`), nên một dòng đã xử xong vẫn mang trạng thái *lỗi*
vĩnh viễn. `find_stale_failures` vì thế hỏi *"sau dòng này, sổ có dòng nào cùng đối tượng
kết thúc êm chưa"* — bản ghi soi theo `(nguồn, đối tượng, mã bên cũ)`, lượt chạy soi theo
`(nguồn, công việc)`. Đếm thẳng là sáng nào chuông cũng réo lại đúng mấy dòng đã xử xong
từ tuần trước, mà chuông kêu sai vài lần thì người ta thôi đọc nó. Cố ý **không có trần
tuổi**: đường duy nhất để một dòng im là đi vá nó.

---

## P5 — Đối soát ban đêm

| | Việc |
|---|---|
| [x] | Quét theo `updatedAt`, so nội dung, vá chỗ lệch — `legacy_datxe/tasks.py::pull_updated`, 17/09 |
| [ ] | Đếm đối chiếu hai bên theo tháng và trạng thái |
| [x] | Gọi lại việc hỏng — `retry_pending`, **trần 3 lần thay vì thang giãn 10 lần** (lý do ở §11.1) |
| [x] | Dòng tổng kết mỗi lượt — dòng `grain = RUN` trong sổ chung, có bộ đếm |
| [x] | Cắm vào Celery beat — **mỗi `SYNC_DATXE_PULL_MINUTES` phút thay vì 01:00** (lưới an toàn của đường chuông, không phải mẻ đêm) |

**Tiêu chí xong:** tắt chuông, tạo ba phiếu, chạy tay đối soát → ba phiếu xuất hiện, sổ ghi rõ "vá bởi đối soát".

**Cần làm trước khi bật thật:** thêm `".indexOn": ["updatedAt"]` vào Rules của **cả hai**
dự án Firebase, nếu không Firebase trả HTTP 400 và vòng quét im lặng báo "kéo được 0 phiếu".
Bốn chỗ bản đã dựng khác bản vẽ ban đầu ghi ở **§11.1 của `mo-ta-ky-thuat.md`**.

---

## P6 — Tệp đính kèm dạng liên kết

| | Việc | Bên |
|---|---|---|
| [x] | Nạp `tab_file` + `tab_file_link` — 1 488 tệp + 1 488 dây, 16/09 dưới local | ERP |
| [x] | Đường tải xuống xử lý `source = "datxe"` — `core/legacy_files.read_file_bytes` | ERP |
| [x] | **Đọc byte thật từ kho app cũ** — `LEGACY_R2_*` + `storage.download_legacy_bytes`, 17/09 | ERP |
| [x] | Kiểm phân quyền của đường tải xuống — 8 bài ở `test_tep_app_cu.py`, cộng `test_pham_vi_dinh_kem_b08.py` | ERP |
| [-] | ~~Đường `GET /api/v1/sync/files/{id}/url`~~ — **không cần nữa**, xem bên dưới | App cũ |

**Tiêu chí xong:** mở tệp cũ trên ERP được; **qua hôm sau mở lại vẫn được**.

**ĐÃ THÔNG 17/09 — và hóa ra không cần app cũ làm gì cả.** 1 488 dòng nạp về hôm
16/09 mới có phần mô tả (tên, kiểu, dung lượng, mã băm, khóa `uploads/...`), byte
nằm trong bucket `degoholding-app-cdn`. Chỗ hiểu sai là ở đây: bucket đó **không
thuộc hệ thống khác** — nó nằm **chung một tài khoản Cloudflare** với kho ERP
(`dego-thumua`), lần thử hôm 16/09 trả 404 / AccessDenied chỉ vì **khóa API của ERP
bị giới hạn đúng bucket của nó**. Nghĩa là đường số 1 của bản thiết kế (bắt app cũ
dựng endpoint ký URL) là **công thừa**: chỉ cần thêm một token *Object Read only*
trỏ đúng bucket cũ, điền bốn biến `LEGACY_R2_*` vào `.env` là xong, bên app cũ không
phải viết dòng mã nào. Đường endpoint vẫn giữ trong mã làm lối thoát cho ngày kho cũ
bị dời chỗ, nhưng **chưa từng chạy thật** — đừng tin nó đúng cho tới khi có người thử.

Vì thế cụm tệp đính kèm **không còn phụ thuộc** `SYNC_DATXE_ENABLED` ·
`SYNC_SHARED_SECRET` · `SYNC_LEGACY_API_BASE` nữa; ba biến đó giờ chỉ còn dành cho
phần đồng bộ phiếu. Chưa điền `LEGACY_R2_*` thì người dùng vẫn nhận câu 503 tiếng
Việt nói rõ lý do chứ không phải trang lỗi trắng.

**Đã kiểm thật, không phải kiểm trên giấy** (`scripts/legacy_sync/verify_legacy_bucket.py`):
`head_object` đủ **1 488/1 488** dòng — 0 thiếu, 0 lệch dung lượng, 0 lỗi khác; rồi
kéo nguyên byte 12 tệp nhắm đúng chỗ dễ gãy nhất (khóa nhiều dấu tiếng Việt, khoảng
trắng, dấu ngoặc) cộng ba tệp nặng nhất, trong đó có tệp **102 MB**. Phép so dung
lượng là cố ý: "khóa có tồn tại" không bắt được ca khóa trúng **nhầm** một tệp khác.

**KHÔNG chép 5.89 GB sang kho ERP** (đảo lại lời khuyên ban đầu). Bucket cũ là của
chính công ty; tắt app cũ là tắt cái Worker, **không hề xóa bucket**. Chép chỉ nhân
đôi dung lượng và đẩy tài khoản từ 7.61 GB qua mức miễn phí 10 GB, đổi lấy số 0 lợi
ích. Xem §P8, dòng "chép tệp thật" đã đóng lại vì lý do đó.

**Cũng cố ý không có `legacy_presigned_url`.** Nghe hợp lý — cho trình duyệt tải
thẳng từ R2 thì byte khỏi đi vòng qua RAM máy chủ. Nhưng chỗ duy nhất muốn gọi nó là
`/attachments/{id}/view`, mà endpoint đó đang gánh ba lớp chắn dựng riêng cho tệp
người ngoài gửi vào (danh sách trắng kiểu tệp · `nosniff` · `sandbox`); chuyển hướng
ra `*.r2.cloudflarestorage.com` là **rụng cả ba**, chưa kể đường dẫn ký sẵn không hỏi
quyền — ai cầm được liên kết là đọc được cho tới lúc hết hạn. Muốn nhẹ RAM thì đi
đường `StreamingResponse`.

**Cố ý KHÔNG xóa tệp bên app cũ.** `attachment/service._delete_storage_of` thoát
sớm khi `source` khác rỗng: xóa dòng trong `tab_file` thì được, đụng vào byte của
hệ khác thì không — ngày nào khóa R2 với sang được, đúng lời gọi đó sẽ xóa bản gốc
mà ERP không sở hữu.

---

## P6.1 — Lịch sử thao tác (`tab_audit_log`)

Không nằm trong bản kế hoạch gốc, thêm 16/09 sau khi phát hiện thẻ **"Lịch sử thao
tác"** trống trơn ở cả 1 313 phiếu nhập về: `import_tickets.py` ghi thẳng xuống
bảng, mà mọi dòng nhật ký bên ERP đều sinh ra từ `core/audit.record(...)` trong
controller.

| | Việc |
|---|---|
| [x] | `scripts/legacy_sync/import_audit_log.py` — 5 095 dòng, phủ 1 313/1 313 phiếu |
| [x] | Bảng dịch 12 mã app cũ → 6 mã đã khai trong `core/action_catalog.py`, 0 mã lạ |
| [x] | Câu chữ lấy nguyên văn của ERP; 211 dòng `edited` dựng lại thành `Chỉnh sửa: <nhãn tiếng Việt>` + điền `changed_fields`/`change_count` |
| [x] | Kiểm qua đúng đường màn hình (`verify_attachments_and_audit.py`) |

**Ba điều ràng buộc cách viết bộ nạp** — ghi lại vì cả ba đều im lặng:

1. **Không gọi được `core/audit.record(...)`**: nó lấy giờ hiện tại và tự
   `db.commit()` từng dòng. Dùng nó là 5 095 dòng cùng mang mốc "hôm nay".
2. **`action` là tập mã ĐÓNG.** Mã lạ vẫn ghi được nhưng hiện ra chữ Anh trần giữa
   câu tiếng Việt và rơi vào nhóm *Không rõ*, biến mất khỏi mọi bộ lọc theo nhóm.
3. **`AuditTimeline` xếp theo `id` giảm dần, KHÔNG theo `created_at`** — nên thứ
   tự `db.add` trong một phiếu chính là thứ tự hiện lên màn hình. Bộ kiểm có hẳn
   một phép soi việc này vì mắt thường không thấy được.

**Hai màn đọc `message` theo hai kiểu khác nhau**, nên câu chữ phải chịu được cả
hai: phiếu dấu dùng `showMessage` (bày *nhãn hành động* rồi mới tới câu), phiếu xe
dùng `messageOnly` — **câu phải đứng một mình đọc được**.

Mọi dòng mang `actor_kind = 3` (*script nhập liệu*) và không có `request_id` — đó
là cách phân biệt "nhập từ app cũ" với thao tác thật bên ERP khi đọc lại sau này.

**Tiêu chí xong:** mở một phiếu dấu và một phiếu xe bất kỳ, thẻ *Lịch sử thao tác*
đọc ra đúng dòng thời gian bên app cũ, đúng tên người, đúng thứ tự.

---

## P7 — Phiếu đóng dấu

| | Việc |
|---|---|
| [ ] | Đếm dữ liệu thật: `isSkipApproval`, `skipApprovalToLevel`, `brandId`, `sealed`, `delivered_to_staff` |
| [ ] | **QĐ-H:** thêm `SEAL_DELIVERED = 8` + nhãn "Đã trả hồ sơ" |
| [ ] | **QĐ-H:** thêm cột `delivered_at`, `delivered_by` + migration |
| [ ] | **QĐ-H:** hành động "Bàn giao hồ sơ" cho văn thư trên màn ERP |
| [ ] | **QĐ-H:** rà hết chỗ coi `SEAL_COMPLETED` là trạng thái cuối |
| [ ] | Nạp danh mục loại dấu, dựng bảng tra |
| [ ] | Nạp lịch sử phiếu dấu |
| [ ] | Chiều cũ → ERP |
| [ ] | Chiều ERP → cũ (nếu chốt làm) |
| [ ] | Kiểm bảng nối công ty — phiếu không được tàng hình với văn thư |

**Tiêu chí xong:** tạo phiếu dấu bên cũ thì sang ERP đủ nội dung kèm tệp mở được; văn thư đóng dấu bên ERP thì app cũ đổi theo.

---

## P8 — Chép tệp thật và tắt app cũ

| | Việc |
|---|---|
| [-] | Chưa mở. Chỉ làm khi có quyết định riêng |
| [-] | ~~Chép tệp thật sang kho R2 của ERP~~ — **bỏ 17/09**: bucket cũ là của chính công ty, tắt app cũ không xóa nó, chép chỉ nhân đôi 5.89 GB. ERP đọc thẳng kho đó (§P6). Việc còn lại ở đây chỉ là **giữ bucket `degoholding-app-cdn` và token chỉ-đọc còn sống** sau ngày tắt app |
| [x] | Đối chiếu số tệp và tổng dung lượng — 1 488/1 488, 5.89 GB, 17/09 |
| [ ] | Chuyển người dùng sang tạo phiếu trên ERP |
| [ ] | Tắt chuông, đóng băng app cũ ở chế độ chỉ đọc |
| [ ] | Kết xuất toàn bộ Realtime Database làm bằng chứng lưu trữ |
| [ ] | Tắt hẳn app cũ |

---

## Nhật ký

| Ngày | Việc | Kết quả |
|---|---|---|
| 15/09/2026 | Soạn bộ tài liệu kế hoạch (README, mô tả kỹ thuật, đối chiếu trường, danh sách pha, tiến độ) | Xong. Chờ đại ca duyệt và trả lời H-01…H-05 |
| 15/09/2026 | Chốt QĐ-G (pháp nhân ba nấc, cấm `company_id = 0`) và QĐ-H (thêm `SEAL_DELIVERED = 8`). Đóng H-04, H-06 (`id 1`), và câu hỏi nấc cuối phiếu dấu | Mở thêm H-07 (237/253 nhân sự chưa gắn pháp nhân) và H-08 (dọn công ty trùng `id 16`) |
| 15/09/2026 | Đóng nốt H-02 (nạp lịch sử không thông báo), H-03 (dev trước prod sau), H-08 (tạm `id 1`). Dò `approval.service.ts` ra bằng chứng **thương hiệu ≈ pháp nhân chứ không phải phòng ban** | Còn treo: **H-01**, **H-05** (chờ danh sách `brands` thật), **H-07** |
| 15/09/2026 | **Đại ca gửi ảnh ba màn quản trị của app cũ** (Phòng ban · Luồng duyệt V2 · "Quản lý Công ty") | **Đóng H-05 và H-07 cùng lúc.** Màn "Quản lý Công ty" của app cũ chính là `brands` (app cũ không có collection `companies` nào khác), tên kèm mã số thuế → **11/11 khớp `tab_company`**. Cả ba loại phiếu đều mang `brandId` → thêm **nấc 0**, không cần điền pháp nhân cho 237 hồ sơ nhân sự nữa. `id 1` và `id 16` **cùng MST `1801722464`** — bằng chứng cứng cho H-08. Mở H-09 (MST Dr.Xanh lệch), H-10 (phòng ban lệch), H-11 (luồng Mua hàng của app cũ) |
| 15/09/2026 | **Đại ca cho biết ĐÍCH ĐẾN: dùng app cũ trước, sau một thời gian chuyển hẳn sang ERP** — tức mỗi lúc chỉ một bên thao tác thật, đụng độ gần như không có, lỡ trùng thì **cú sau ghi đè** | Chốt **QĐ-J**. **Xóa** bộ luật giành quyền 4 điều ở mục 15.3 (canh một chuyện không tới, mỗi nhánh là một chỗ để sai), thay bằng "cú sau ghi đè" + **một** điều kiện kỹ thuật phải giữ: "sau" là theo **giờ bấm**, không phải giờ tín hiệu tới, kẻo webhook chậm 30s đè lên kết quả mới hơn rồi đối soát đêm vẫn báo "đã khớp". Giới hạn 15.4 rút từ 4 xuống 3. **Hệ quả lớn hơn:** đích đến biến P8 (chép tệp thật + tắt app cũ) từ "nếu sau này muốn" thành **việc chắc chắn phải làm**, và nâng mức **H-10** + **H-11** từ "có thể bỏ qua" thành điều kiện chuyển giai đoạn. Sửa luôn mục 2 README — bản đầu viết "ERP là nơi duyệt" là sai từ lúc có QĐ-I |
| 15/09/2026 | **Đại ca bác đề xuất "một nguồn sự thật, hai cửa bấm"** — lý do: app cũ đang chạy thật với người dùng thật, không đổi luồng liền được. Chốt **QĐ-I**: hai bộ máy duyệt giữ nguyên, chỉ nối một đường đồng bộ | Viết mục 15 của mô tả kỹ thuật: đồng bộ **kết cục** chứ không đồng bộ tiến trình · bên nhận đóng phiên bằng một hành động hệ thống ghi rõ nguồn, **cấm ký khống từng chặng** · luật giành quyền "cú bấm sớm hơn thắng", trùng khít thì app cũ thắng · 4 giới hạn phải chấp nhận · ca nguy nhất là `needs_correction` sau khi bên kia đã duyệt → máy **cố ý không tự quyết**, đẩy cho người xử. Sửa mục 5 README: dòng trạng thái duyệt nay **có hai ông chủ**, ngoại lệ cố ý, ghi thẳng ra chứ không giấu |
| 15/09/2026 | **Đo dữ liệu thật trên dev** (262 nhân sự, 18 phòng ban, 14 công ty) thay vì đoán theo mã nguồn | Lật lại một giả định sai của chính tài liệu: **nấc 2 cũng chết** (0/18 phòng ban có pháp nhân, `tab_department_company` rỗng) → hôm nay 100% phiếu rơi xuống mặc định. Đổi đề xuất H-07 sang **điền 18 dòng phòng ban**. Thấy thêm: 1 nhân sự trỏ vào công ty `id 15` không tồn tại; **6 tên vừa là phòng ban vừa là pháp nhân** → đại ca đoán đúng một nửa ở H-05 |
| 16/09/2026 | **Đại ca trả lời nốt ba câu H-09 · H-10 · H-11 trong một lượt** | **Hết câu hỏi treo — cả 11 câu H-01…H-11 đã đóng.** Ra ba quyết định mới: **QĐ-K** (MST lấy theo ERP, app cũ thiếu dữ liệu) · **QĐ-L** (tạo đủ 8 phòng ban, chép nguyên văn tên app cũ) · **QĐ-M** (bỏ luồng Mua hàng khỏi phạm vi, đổi lại phải kết xuất bản tổng hợp). Phạm vi đồng bộ nay chốt cứng ở **ba** thứ: đặt xe · duyệt dấu · giao hàng |
| 16/09/2026 | **Rút hệ quả kỹ thuật từ QĐ-K thay vì chỉ sửa hai ô mã số thuế** | Câu trả lời của đại ca là "ERP đúng", nhưng thứ đáng ghi lại hơn là **tên bên app cũ đã được chứng minh là có thể sai**. Nên bảng tra thương hiệu → pháp nhân đổi khóa sang **`id`**, cấm khớp bằng tên hoặc bằng MST — ai đó sửa tên cho đúng là mọi phép so tên trượt sạch, **im lặng**, phiếu rơi hết xuống công ty mặc định. Viết vào `doi-chieu-truong` mục 10.5 |
| 16/09/2026 | **Chỉ ra cái bẫy QĐ-L giăng sẵn: sau đợt này sẽ có MƯỜI tên vừa là phòng ban vừa là pháp nhân** | 6 tên cũ + 4 tên mới (Agricare · N2AGRO · Dego Agrochem · Dego Holding). Khớp tới 10 chỗ thì rất dễ có người viết hàm "tra pháp nhân theo tên phòng ban". **Cấm** — pháp nhân lấy ở nấc 0 từ `brandId`, trùng tên là trùng tên. Ghi thành cảnh báo ở `doi-chieu-truong` mục 10.7, kèm hai chi tiết tự quyết: `company_id = 0` cho 8 dòng mới, và mỗi dòng mang `legacy_id` |
| 16/09/2026 | **Gộp bốn thứ còn thiếu thành MỘT lượt kết xuất Firebase** | Id thương hiệu · id phòng ban · tỷ lệ phiếu có `brandId` · số phiếu luồng Mua hàng — trước nay nằm rải rác ba chỗ như ba việc khác nhau, thực ra cùng lấy được trong một lần chạy. Ba thứ đầu chặn P0 |
| 16/09/2026 | **Đại ca kết xuất TOÀN BỘ Firebase, em đo trên dữ liệu thật** | Bốn số đo xong trong một buổi. Hai cái xác nhận kế hoạch: `brandId` phủ **100%** và **0 tham chiếu chết** (nấc 0 của QĐ-G là đường chính, ba nấc dự phòng tụt xuống lưới an toàn); **0 phiếu Mua hàng** nên QĐ-M không còn nghĩa vụ nào. Hai cái đổi kế hoạch: `brandId` là **MẢNG** — 123/1 313 phiếu thuộc 2..9 pháp nhân. Em kết luận vội là "chặn P0" rồi dựng ba phương án hỏi đại ca, **sai**: ERP đã có bảng nối `tab_seal_request_company` và phạm vi lọc theo bảng nối, nên 121/123 ca không mất gì, còn đúng 2 phiếu giao hàng. **Số đo mới phải đối chiếu thiết kế cũ trước khi kết luận là nó phá thiết kế.** Và **`departmentId` chỉ có ở phiếu dấu** (946/946), 367 phiếu đặt xe + giao hàng phải suy từ người tạo — suy được **367/367** vì cả 136 người dùng đều có phòng ban hợp lệ |
| 16/09/2026 | **Đại ca bảo "thử đồng bộ dưới local" — bắt đầu P0 thật, xong phần danh mục** | Cột `legacy_id` (7 bảng, migration `b7c2e4a91f30`) + `scripts/legacy_sync/` chạy được hai lần không đẻ thêm gì. **Ba chỗ số đo khác bản vẽ:** (1) không phải 8 phòng ban tạo mới mà **12** — bốn cái chênh là *gần trùng* chứ không mới: "Sản Xuất"~"Sản xuất -Thu mua" **226 phiếu**, "Kế Toán Thuế"~"Kế toán" 134, "Bamboovietnam"~"Bamboo" 12, "Nhà Máy Dego Organic"~"Dego Organic" 6 — tổng **378/1313 phiếu (29%)**, theo H-10 thì tạo mới giữ nguyên tên và ghi vào `DEPARTMENT_NEAR_DUPLICATE` để gộp sau nếu đại ca chốt; (2) suy phòng ban không phải 367/367 mà **1313/1313** — phiếu dấu cũng tra được qua người tạo, không cần hai đường suy; (3) hai dòng Dr.Xanh có **MST lệch hẳn** giữa hai hệ, thêm bằng chứng cho luật cấm khớp theo MST. **Đính chính khảo sát của chính em:** "không có phân hệ delivery" là SAI — `tab_vehicle_booking` đã có `request_type = TYPE_DELIVERY` và đủ trường giao hàng |
| 16/09/2026 | **Hai câu kỹ thuật tự đóng bằng số đo, không phải bằng suy luận** | `StopItem` **phải có `notes`**: 59 điểm dừng, **25 điểm có ghi chú thật**. `driver.status` **chỉ có một giá trị** `available` (13/13) nên ánh xạ kiểu gì cũng không mất dữ liệu — đừng dựng bảng ánh xạ cho tập một phần tử. Thêm một bằng chứng cho `legacy_id`: khóa `dept_kinh_doanh` nay mang tên *"Pháp Lý"*, tức tên phòng ban ĐÃ TỪNG bị đổi thật |
| 16/09/2026 | **Đại ca chốt "gần trùng thì dùng của ERP" — gộp xong, rồi khớp nốt người, xe, tài xế** | Bốn phòng gần trùng gộp về phòng ban ERP; bốn dòng script đã lỡ tạo bị xóa **sau khi đếm đủ 0 tham chiếu trên cả 18 cột `department_id`** của hệ (đếm trước khi xóa, không xóa rồi mới biết). "12 phòng ban tạo mới" thành **8**. Khớp tiếp: **95/136 tài khoản** (email 1-1, gánh **87% số phiếu**) và **13/13 xe + 13/13 tài xế**. Cả ba script chạy lần ba ra 0 thay đổi |
| 16/09/2026 | **Chốt nguyên tắc: chỉ tự động hóa ca 1-1 tuyệt đối, phần còn lại ra BÁO CÁO cho người chốt** | Lý do viết thẳng vào mã: **đoán sai trông y hệt đoán đúng**, nên không ai phát hiện ra. Bốn bằng chứng đo được trong buổi này, đều là ca mà phép khớp "tự nhiên" sẽ sai: (1) `assistant.n2sbiovn@gmail.com` là **hộp thư dùng chung** mang tên một nhân viên thật — khớp theo tên là gán nhầm 12 phiếu; (2) một người có **ba** tài khoản app cũ trỏ về một hồ sơ, mà `legacy_id` là **một cột** nên không diễn đạt được quan hệ nhiều-một; (3) ba xe thuê ngoài mang biển số rác app cũ trong khi ERP lưu **tên loại xe** vào ô biển số — khớp biển số rụng cả ba; (4) hai tài xế **dùng chung số điện thoại** `0971445134` — khớp theo số là hòa, phải người nhìn tên mới tách |
| 16/09/2026 | **Việc khớp người lòi ra HAI lỗ dữ liệu của chính ERP, không phải của app cũ** | (1) `tab_employee` **id 38 và id 201 là cùng một người** — trùng tên, trùng email, cùng `official`, chỉ khác phòng ban 5 với 15; **24 phiếu** treo trên danh tính đó. (2) **26 người app cũ (73 phiếu) không có hồ sơ nhân sự nào bên ERP**, kể cả tra theo tên. Cả hai phải đại ca chốt, script cố ý không tự xử |
| 16/09/2026 | **Đại ca chốt "id trùng thì lấy id nhỏ, nhưng rà xem id lớn có dính gì không"** | Câu hỏi đó trả lời được bằng **số đo, không bằng lời hứa**: quét `information_schema` lấy **64 cột** tên `%employee_id%` · `%assignee_id%` · `%requester_id%` · `manager_id` rồi đếm trên từng cột. Id 201 ra **0 chứng từ** — chỉ có một dòng `tab_employee_department` và một tài khoản. Nên không có gì phải cập nhật lại, và đó là kết luận đo được chứ không phải giả định. Quét này lòi thêm **cặp trùng thứ hai chưa ai biết**: nhân sự **176/196 "Nguyễn Thị Ngọc Hân"** với hai tài khoản **185/205**, cùng cặp **tài khoản 1/3** trên `hgbao.idagroup@gmail.com` — cả hai KHÔNG hiện trong báo cáo đồng bộ vì không tài khoản app cũ nào dùng email đó, tức là **lỗi thuần của ERP** |
| 16/09/2026 | **Tạo hồ sơ + tài khoản cho 26 người — đi qua TẦNG DỊCH VỤ chứ không `db.add` thẳng** | `create_missing_employees.py` gọi `employee_service.create_employee` + `user_service.provision_user`, nên được sinh mã `NSU`, kiểm trùng email, dựng `tab_employee_department` và ghi nhật ký y như người bấm trên giao diện. **Hai chỗ cố ý không đoán:** `status` để `official` cho tất cả (app cũ chỉ có bật/tắt tài khoản, không có khái niệm nghỉ việc — suy ra là bịa), và **người app cũ đã khóa thì không cấp tài khoản** (mở đường đăng nhập cho người bị khóa là việc phải có người quyết). Mật khẩu sinh ngẫu nhiên từng người, ghi ra tệp **ngoài kho mã**; đã thử đăng nhập thật một tài khoản bằng **cả email lẫn mã `NSU`** — vào được, không chỉ "đã tạo". Cả 22 tài khoản mang đúng vai trò `employee` |
| 16/09/2026 | **Nạp thật 1 313 phiếu dưới local** — 946 dấu + 321 đặt xe + 46 giao hàng | Xếp theo `createdAt` rồi mới ghi, nên id ERP (và mã sinh từ id) chạy đúng dòng thời gian app cũ. Ba chỗ **đo ra rồi mới quyết**: (1) `tab_seal_type` rỗng + 946 phiếu cùng một chuỗi loại → tạo **một** loại, tên nguyên văn app cũ; (2) luồng dấu app cũ có 3 cấp mà **cấp 2 chưa từng được duyệt lần nào** và 106 phiếu bỏ qua cấp 1 → lấy cấp 1 làm `approved_*`, **cấp 3 (Pháp lý)** làm `completed_*` — cấp 3 **không phải Văn thư**, lệch nghĩa này ghi thẳng vào mã nguồn để người sau không đọc nhầm; (3) `requester_id`/`approved_by`/`dispatched_by` trên hai bảng này là **id TÀI KHOẢN**, không phải id nhân sự — ngược với luật chung của ERP, đọc mã `create_seal_request` xác nhận trước khi ánh xạ |
| 16/09/2026 | **Bản chạy thử đầu tiên tố giác một lỗi của chính em: 92 phiếu dấu mất phòng ban** | Bộ nạp đọc **bảng tra viết tay** 14 dòng, trong khi `sync_master_data` đã **tạo thêm 8 phòng ban ERP** và đóng dấu `legacy_id` cho chúng — dưới DB có **22** dấu. Mất: Dego Holding 62 phiếu · Mua Hàng 12 · N2AGRO 11 · R&D 7. Sửa bằng cách đổi **nguồn**: danh mục đọc `legacy_id` **từ DB**, bảng tay tụt xuống làm phép đối chiếu và **dừng hẳn** nếu hai bên lệch. Áp cùng luật cho xe và tài xế. Bài học: con số `92` hiện ra trong bảng tổng kết vì có người **đếm cả ca hỏng**, không phải chỉ đếm ca chạy được |
| 16/09/2026 | **Lỗi 1406 lúc ghi thật: cột `String(20)` gặp chuỗi người ta gõ tự do** | Ô "SĐT liên hệ" app cũ có người gõ `"0787936664 - Mỹ Giang"` (21 ký tự). Không vá riêng cột đó — thêm cổng `fit_to_columns` đọc **trần độ dài thẳng từ model** (chép tay là lệch lúc ai đó sửa `String(n)`), cắt cho vừa rồi **chép nguyên văn giá trị gốc xuống `note`** nên không mất chữ nào. Riêng ô điện thoại cắt tại **cụm số ở đầu** — `"0787936664 - Mỹ Gia"` đọc như dữ liệu hỏng và bấm gọi cũng không được. **24 ca**, đúng một cột. Cổng chạy cả ở bản xem trước nên lần sau lỗi lòi ra **trước** khi ghi, không chết ngang mẻ nạp |
| 16/09/2026 | **Hai chỗ dữ liệu gốc đã mất, ghi thành lời chứ không để trống** | (1) Một khóa tài xế trên **7 phiếu** không còn ở bất kỳ nhánh nào của bản kết xuất — hồ sơ đã bị xóa bên app cũ, không có gì tra ra tên; chuyến đã hoàn thành mà ô tài xế trống thì người đọc tưởng bộ nạp hỏng, nên ghi rõ ra ghi chú kèm khóa. (2) `StopItem` chưa có ô `notes` nên **25/59 ghi chú điểm dừng** sẽ rơi im lặng — vá đủ đường: schema · `_dump_stops` · kiểu TS · ô nhập trên form · màn chi tiết |
| 16/09/2026 | **Dựng sổ đồng bộ — MỘT bảng cho mọi hệ ngoài, và gộp luôn `tab_pos_sync_run` vào** | Đại ca đặt ba điều kiện: viết linh động để sau này đồng bộ đơn hàng / POS365 dùng chung được · bỏ bảng riêng của POS365, viết chung một cái · *"mọi thứ phải gọn chứ cái gì cũng tách bảng riêng thì quản lý kiểu gì nổi"*. Kết: một bảng `tab_sync_log`, hai hạt qua cột `grain` (`RUN` = lượt chạy nền, `RECORD` = một bản ghi đi qua), hệ nguồn khai bằng **adapter** ở `registry.py`. Giữ **nguyên khuôn phản hồi cũ** của `/api/coffee/sync/runs` (`kind` vẫn là số cũ, `detail` vẫn là chuỗi JSON) nên `frontend-v2` không phải đổi kiểu — chỉ bảng màu đổi. Và cố ý giữ quyền `pos_order.read` cho đường đó thay vì đòi `sync_log.read`: quản trị quán không nên đột nhiên cần một khóa hệ thống cho màn hằng ngày của họ |
| 16/09/2026 | **Bộ kiểm 33 bài tìm ra một lỗ bảo mật thật trong chính tệp chữ ký** | Tệp `core/sync_signature.py` có hẳn dòng docstring *"đừng bao giờ so bằng `==`"*, và vẫn lủng: `hmac.compare_digest` **ném `TypeError` khi chuỗi có ký tự ngoài ASCII**, nên gửi một header `X-Sync-Signature` có dấu là endpoint đổ **500** thay vì trả câu "Chữ ký không khớp". Sửa bằng cách so **bytes** (vẫn hằng thời gian). Bài kiểm giữ nguyên chuỗi có dấu `"sai-be-bét"` kèm lời dặn đừng sửa thành ASCII. Đây đúng loại lỗ mà bộ kiểm được viết ra để bắt: **không có bài nào đỏ thì không ai biết nó ở đó**. Một bài kiểm khác thì đúng là lỗi của bài kiểm — quên bật cờ nguồn nên chạm chốt "đang tắt đồng bộ" trước khi tới chốt khóa ký |
| 16/09/2026 | **Migration dời dữ liệu: hai chỗ cố ý làm khác thói quen** | (1) Bảng dịch `kind → job` **chép cứng trong migration**, không `import` từ mã nguồn — migration phải chạy đúng như ngày viết ra nó, mã nguồn đổi về sau không được làm đổi ý nghĩa của một lượt dời dữ liệu đã chạy. (2) Câu `INSERT` đi bằng **tham số**, không nối chuỗi: `error` và `detail` là dữ liệu của hệ ngoài. Kèm theo, `event_id` UNIQUE mà mặc định là chuỗi rỗng — MySQL coi mỗi chuỗi rỗng là một giá trị thật nên **mọi dòng bắt buộc phải sinh qua `service.py`**, `db.add` thẳng là hàng thứ hai đụng khóa |
| 17/09/2026 | **Byte của 1 488 tệp đính kèm đã thông — và việc bắt app cũ dựng endpoint là công thừa** | Bản thiết kế chốt hai đường lấy byte, đường chính là *app cũ dựng `GET /api/v1/sync/files/{id}/url` ký hộ URL*. Mở bảng R2 trên Cloudflare ra thì lộ chuyện: bucket `degoholding-app-cdn` của app cũ **nằm chung một tài khoản** với `dego-thumua` của ERP. Lần thử hôm 16/09 trả 404 / AccessDenied **không phải vì kho của người khác**, mà vì khóa API của ERP bị giới hạn đúng bucket của nó. Thêm một token *Object Read only* trỏ bucket cũ, bốn biến `LEGACY_R2_*`, một nhánh rẽ trong `read_file_bytes` — xong, bên app cũ không viết dòng mã nào. Bài học: **đọc lỗi quyền đừng vội kết luận về ranh giới hệ thống**; 404/AccessDenied là câu trả lời của *khóa này không mở được*, không phải của *kho này không phải của bạn* |
| 17/09/2026 | **Đảo lại quyết định "chép một lần" của chính hôm trước** | Hôm 16/09 em khuyên chép 5.89 GB sang kho ERP, lập luận là *ngày tắt app cũ thì 1 488 tệp chết theo*. Lập luận đó dựng trên giả định sai vừa nói ở trên. Bucket cũ là của chính công ty, tắt app cũ là tắt cái **Worker** chứ không xóa bucket; chép chỉ nhân đôi dung lượng và đẩy tài khoản từ 7.61 GB qua mức miễn phí 10 GB. Giữ nguyên tại chỗ, ERP đọc thẳng. Việc duy nhất còn lại ở P8 là **đừng xóa bucket và đừng thu hồi token** vào ngày dọn app cũ |
| 17/09/2026 | **Kiểm đủ 1 488 dòng chứ không kiểm mẫu, và so cả dung lượng** | `verify_legacy_bucket.py` chạy `head_object` cho **toàn bộ** 1 488 khóa (rẻ, không kéo byte): 0 thiếu · 0 lệch cỡ · 0 lỗi. Phép so dung lượng là cố ý — *"khóa có tồn tại"* không bắt được ca khóa trúng **nhầm** một tệp khác. Chặng hai kéo nguyên byte 12 tệp **chọn theo điểm "tên xấu"** (đếm ký tự ngoài ASCII, khoảng trắng, dấu ngoặc, và cờ chuẩn hóa NFD) cộng ba tệp nặng nhất — vì khóa thật trông như `...-Biên bảng điều chỉnh hoá đơn ĐL Trung Liễu (4803-4804).pdf`, đúng loại làm hỏng chữ ký S3. Lấy 10 dòng đầu thì cả hai rủi ro đó đều lọt. Tệp 102 MB đọc về nguyên vẹn |
| 17/09/2026 | **Đại ca đảo luật ghi đè, và luật mới ÍT nhánh hơn luật cũ** | Bản vẽ ban đầu giữ một danh sách "trường app cũ làm chủ", mọi thứ ngoài danh sách thì ERP giữ. Đại ca chốt ngược: *"ghi đè full thông tin phiếu"*, chỉ chừa nhật ký · tệp · dấu vết phê duyệt. Viết thành §9.4 với **đúng một** ngoại lệ: **ghi rỗng không được đè lên ô đang có chữ** — vì app cũ không phân biệt *"người ta xóa trắng ô này"* với *"gói tin này không mang ô đó"*. Hai chỗ phải nói rõ vì trông như rỗng mà không phải: `False` là một giá trị thật, còn `0` trên cột số thì tính là rỗng. Phiếu đã đóng thì đóng băng — cú sửa muộn của app cũ không được lật lại chuyến đã hoàn thành |
| 17/09/2026 | **Bộ tra người / xe / tài xế ba nấc, và nấc ba chỉ mở cho HAI thứ** | Đại ca gợi ý đúng khuôn: *"có 1 hàm kiểm tra tài xế, nếu có thì trả ra còn ngược lại thì tạo xong cũng trả ra"*. `resolver.py` làm vậy — tra `legacy_id`, không thấy thì tra khóa tự nhiên (**và đóng dấu `legacy_id` lại ngay**, nên lần sau chỉ còn một truy vấn), không thấy nữa thì tạo. Nhưng **nấc ba chỉ mở cho xe và tài xế**, lại còn nằm sau công tắc `SYNC_DATXE_AUTO_CREATE` mặc định TẮT: tự đẻ hồ sơ nhân sự là tự cấp danh tính cho người thật, còn một chiếc xe thuê ngoài thì chỉ là một dòng danh mục. Mỗi hàng đẻ ra đóng cờ `auto_created` lên dòng sổ, và bộ lọc *"chỉ dòng có cảnh báo"* của sổ **chính là hàng đợi soát** — `tab_vehicle`/`tab_driver` không có cột `is_active` nên không có chỗ nào khác để treo |
| 17/09/2026 | **Hai vòng chạy nền của P5 — và bốn chỗ cố ý làm khác bản vẽ** | Đường chính vẫn là cái chuông bên app cũ gọi thẳng vào ERP; `legacy_datxe/tasks.py` là **lưới an toàn**. (1) Con trỏ **bao gồm** chính mốc lần trước chứ không cộng 1 mili-giây — cộng vào thì hai phiếu sửa trùng mili-giây mất một, còn đọc lại một phiếu thì `is_unchanged` chặn, không tốn dòng sổ nào. (2) Lượt đầu chỉ nhìn lại **24 giờ**, không thì tick đầu tiên dội cả 1 313 phiếu đã nạp vào sổ. (3) Con trỏ **vẫn tiến dù vài phiếu hỏng** — mỗi phiếu hỏng đã có dòng sổ riêng và vòng chạy lại nhặt nó; ghim con trỏ lại là kéo nguyên mẻ đó mỗi 5 phút, mãi mãi. (4) Chạy lại **TẠI CHỖ** (tăng `attempt_count`, trần 3 lần) thay vì thang giãn 10 nấc, để giữ luật *một sự kiện một dòng*; riêng nút *Chạy lại* của người thì vẫn nhân bản dòng vì đó là một quyết định mới. **Việc hai của P5 — đếm đối chiếu hai bên — chưa dựng.** ⚠️ Thiếu `".indexOn": ["updatedAt"]` trong Rules thì Firebase trả 400 và vòng quét báo "kéo được 0 phiếu" **không kèm lỗi nào** |
| 17/09/2026 | **Gọi tay một phát vào cửa nhận, lòi ra lỗi mà 33 bài kiểm không canh** | Viết `send_test_event.sh` để đại ca tự bắn một phiếu vào ERP (script tự ký, khóa đọc từ `.env`). Gọi lần hai thì ERP trả `erp_id = 0` kèm "Không có gì thay đổi" — mà ô đó chính là thứ app cũ ghi ngược vào `erpId`, tức **một cú bỏ qua sẽ xóa mối nối của chính phiếu vừa nhận xong**, rồi lần sau nhìn vào tưởng chưa đồng bộ bao giờ. Ba nhánh *bỏ qua* (trùng `event_id` · nội dung không đổi ô nào · phiếu đã chốt) nay đều trả id thật; `finish_skipped` nhận thêm `local_id`, và cửa nhận có `find_local_id` cho nhánh không sinh dòng sổ. Bài học: **bộ kiểm canh cái nó được viết ra để canh** — 33 bài đều soi chốt chặn và nội dung ghi xuống, không bài nào soi *câu trả lời gửi ngược về*, vì hồi đó chưa có ai ở đầu kia để mà đọc nó |
| 17/09/2026 | **Viết ra một hàm rồi xóa đi vì chỗ gọi nó sẽ phá lớp chắn** | `legacy_presigned_url` nghe rất hợp lý: tệp 102 MB cho trình duyệt tải thẳng từ R2 thì byte khỏi đi vòng qua RAM máy chủ. Nhưng chỗ duy nhất muốn gọi là `/attachments/{id}/view`, mà endpoint đó gánh ba lớp chắn dựng riêng cho tệp người ngoài gửi vào (**danh sách trắng kiểu tệp · `nosniff` · `sandbox`**) — chuyển hướng ra `*.r2.cloudflarestorage.com` là rụng cả ba, thêm nữa URL ký sẵn **không hỏi quyền**. Xóa hàm, thay bằng một khối chú thích nói rõ vì sao nó cố ý không tồn tại: mã chết thì người sau xóa, còn **lời giải thích thì giữ người sau khỏi viết lại nó** |

| 17/09/2026 | **Đóng dấu `updatedAt` bên app cũ — mảnh cuối để vòng quét thôi chạy không** | Đại ca tự khai `".indexOn": ["updatedAt"]` cho nhánh `requests` ở cả hai dự án Firebase. Đo lại bản kết xuất prod thì `createdAt` có **15 763** chỗ còn `updatedAt` có **0** — chỉ mục đã mở nhưng chưa phiếu nào mang trường đó, nên vòng quét bên ERP dù chạy đúng vẫn kéo về rỗng vĩnh viễn. Vá bằng `stampUpdatedAt` cắm vào **cả ba** đường ghi của nhánh `requests`; đường thứ ba (`patchRequest` trong `driver.service.ts`) không đi qua tầng `db/` nên rất dễ sót, mà bốn nhịp của tài xế đều chạy qua nó. Trước khi gõ có đọc Rules thật bằng khóa đọc của ERP để chắc một điều: `.validate` của `$requestId` dùng `hasChildren([...])`, tức **đòi có mấy khóa bắt buộc chứ không cấm khóa lạ** — nếu nó cấm thì thêm `updatedAt` vào cùng cú ghi sẽ làm hỏng luôn thao tác của người dùng. Hai nhánh `vehicles`/`drivers` **không khai chỉ mục**, đúng ý: vòng quét chỉ hỏi `requests`. ⚠️ Bộ chạy test của app cũ **hỏng sẵn từ trước** (`No such module "cloudflare:test-internal"`, lệch phiên bản `vitest` ↔ `@cloudflare/vitest-pool-workers`) — cất hết thay đổi đi chạy lại vẫn hỏng y hệt; phải chạy vòng qua bằng một cấu hình Node tạm mới kiểm được, **40/40 xanh** trên 6 tệp phủ mọi service ghi vào `requests` |
| 19/09/2026 | **Ba lỗ của vòng quét, và cả ba đều IM LẶNG — vá xong, thêm vòng thứ ba** | (1) **Con trỏ tự đẩy mình vào tương lai.** `_updated_at()` lùi về `createdAt` khi phiếu chưa có dấu thời gian, mà con trỏ lại tiến theo chính hàm đó — một phiếu thử tạo bên ERP ngày 29/08 đã kéo con trỏ lên `1787975823428`, **giấu vĩnh viễn** cả 480 phiếu Firebase dev (`createdAt` 2025-07 → 2025-09). Tách hẳn `cursor_value()`: mốc để TIẾN con trỏ **chỉ nhận `updatedAt` thật**, không có thì trả `0`. Hai hàm nhìn giống nhau nên phải tách tên — trộn chung là lỗi quay lại ngay lần ai đó sửa. (2) **`is_unchanged` chặn luôn phần dựng lại.** Phiếu không đổi nội dung thì `apply_legacy_record` thoát trước khi tới `open_entry`, nên phiên duyệt · nhật ký · tệp đính kèm **không bao giờ được dựng lại** — đúng gốc của 353 phiếu không có luồng duyệt hôm trước. Thêm tham số `force`, nhưng **không mở cho vòng chạy 3 phút**: mở là mỗi nhịp dựng lại cả nhánh. (3) **`read_node` trả `None` cho cả hai nghĩa** *"nhánh rỗng"* và *"hỏng"*, nên nhánh dự phòng "đọc cả nhánh" chạy ở **mọi** nhịp, âm thầm, kể cả lúc mọi thứ bình thường. Nay `{}` = chạy được mà rỗng, `None` = hỏng, và lúc rơi vào dự phòng thì **kêu lên một dòng cảnh báo** — trước đó chỉ mục hỏng trông y hệt "hôm nay không ai sửa phiếu nào". Thêm **vòng thứ ba** `datxe.full_sweep` 02:15 mỗi đêm (bỏ con trỏ + `force`) làm lưới đỡ của lưới đỡ; **cố ý không hạ xuống nhịp phút**. ⚠️ Bẫy lúc viết bài kiểm: ba hàm dựng dữ liệu suy ra chạy **TRƯỚC** câu `return finish_skipped(...)` trong `_write`, nên một lượt quét ép buộc **có dựng lại thật** mà dòng sổ vẫn đóng là `SKIPPED` — bài kiểm phải đếm **lời gọi hàm dựng**, đếm cột `written` là đo nhầm chỗ và ra kết luận ngược. Bộ kiểm 23 → 98 bài xanh trên năm tệp liên quan |
| 19/09/2026 | **Móc đẩy phiếu bên app cũ — đặt ở tầng DB chứ không tầng service, và kiểm chữ ký bằng mẫu của bên kia** | Vòng quét 3 phút chỉ là lưới đỡ; đường chính của P2 là app cũ ghi xong phiếu thì gọi thẳng sang ERP. `src/utils/erp-sync.ts` + móc ở **cả ba** đường ghi. **Khác bản vẽ, cố ý:** §P2 bảo móc ở tầng service, nhưng tầng đó có hơn mười chỗ gọi `updateRequestInDb` rải khắp `admin`/`approval`/`dispatch`/`request` — sót một chỗ là đúng loại lỗi im lặng đã dính mấy lần (phiếu vẫn ghi, người dùng vẫn thấy bình thường, chỉ ERP là không bao giờ biết). Móc ở tầng `db/` thì phủ kín và trùng đúng tập hợp với chỗ đóng dấu `updatedAt`, tức đã có bài kiểm canh sẵn. Ba chỗ nhỏ phải nghĩ kỹ: (1) gói gửi đi **bỏ khóa `id`** — vòng quét đọc thẳng Firebase nên node của nó không có khóa này, gửi kèm là hai đường cùng một phiếu ra hai vân nội dung khác nhau và ERP tưởng phiếu đổi mỗi lần quét; (2) ghi ngược `erpId` **không đóng dấu `updatedAt`**, vì đó là ô do ERP làm chủ và chính ERP vừa cấp xong — đóng dấu là phiếu trông như vừa bị sửa, kéo thêm một lượt xử vô ích, lặp mãi; (3) `event_id` dựng từ `legacy_id` + chính con dấu `updatedAt` chứ không phải mã ngẫu nhiên, gửi lại đúng một lần ghi thì ERP nhận ra trùng. ⚠️ Bẫy trình biên dịch: `const { id, ...than } = node` làm `tsc` **hết bộ nhớ** — `AnyRequest` là kiểu hợp của mấy loại phiếu, tách phần dư trên nó bắt trình biên dịch bung tổ hợp; phải chép nông rồi `delete`. Bộ chạy test của app cũ vẫn hỏng sẵn trên máy này (`cloudflare:test-internal`, **không** phải do đường dẫn có dấu — đã dựng junction ASCII thử, hỏng y hệt), nên ngoài 21 bài kiểm gửi kèm cho CI chạy, em bó `erp-sync.ts` và `requests.db.ts` bằng esbuild rồi chạy thẳng trên Node để kiểm thật: cả chuỗi `syncRequestToErp → fetch ERP → ghi ngược Firebase` xanh. Chữ ký neo bằng **mẫu tính từ `app/core/sync_signature.py` của ERP** chứ không tự ký tự so — kể cả mẫu có dấu tiếng Việt, vì lệch bảng mã thì phiếu có dấu 401 hết còn phiếu không dấu vẫn lọt, kiểu hỏng khó lần nhất |
| 21/09/2026 | **bao-CR-452 — Sổ đồng bộ phía app cũ, và cái bộ chạy test hỏng suốt bốn ngày hóa ra hỏng vì chữ `đ` trong đường dẫn** | Đại ca nhớ là "hình như có màn hình `sync_logs` rồi"; rà lại thì **chưa có bên app cũ** — cái đại ca nhớ là màn `/system/sync-logs` của ERP dựng ở P4. Làm thêm, nhưng cố ý **không chép lại sổ bên kia**: sổ ERP ghi những gì **tới nơi**, chỗ nó mù là những lượt bắn **không bao giờ tới**, và chỉ app cũ mới biết mình đã bắn mà trượt. Chọn **một phiếu một dòng** (khóa `legacyId` trần, trượt nữa thì đè, sang được thì xóa) thay vì một lượt một dòng: sổ theo lượt thì đúng lúc hệ hỏng nặng nhất là lúc nó phình nhanh nhất, còn kiểu này ra **danh sách việc phải làm** và tự lành theo vòng quét 3 phút. Đổi lại mất lịch sử từng lần thử — chấp nhận được, lịch sử đầy đủ của mọi thứ ĐÃ SANG ĐƯỢC nằm bên sổ ERP, hai quyển bù nhau chứ không chồng nhau. Ba chỗ phải nghĩ: (1) `pushRequestToErp` trước đây trả số `0` cho **cả ba** kết cục *tắt cờ* · *ERP nhận mà không cấp số* · *bắn trượt*, gộp vậy nên mới không có chỗ nào ghi lại được — tách thành `ErpPushResult` mang `status`/`httpStatus`/`message`; (2) HTTP 200 mà thiếu `erp_id` vẫn là **ĐÃ NHẬN**, coi là trượt thì sinh ra một dòng kẹt cho phiếu chẳng kẹt; (3) Luật Firebase phải mở `.write` cho **mọi người đã đăng nhập** chứ không siết theo vai trò — phiếu trượt thường là phiếu của nhân viên thường vừa bấm nút, siết vào Administrator thì đúng những ca cần ghi nhất lại không ghi nổi. **Đính chính hai dòng nhật ký 17/09 và 19/09 của chính em:** bộ chạy test app cũ hỏng **không phải** do lệch phiên bản `vitest` ↔ `@cloudflare/vitest-pool-workers` (hai gói khớp dải `peerDependencies`), và **đúng là** do đường dẫn — bật `NODE_DEBUG=vitest-pool-workers:module-fallback` ra nguyên văn `Cannot convert argument to a ByteString because the character at index 32 has a value of 273`, tức chữ **`đ`** trong `app đặt xe`: cầu nạp mô-đun nhét đường dẫn tệp vào một **header HTTP**, mà header chỉ chịu được Latin-1. Lần 19/09 dựng junction ASCII thấy hỏng y hệt nên kết luận vội là "không phải đường dẫn" — **sai, vì Node tự quy đường dẫn về lối thật**, junction không đổi được gì. **Bài học: thấy cách chữa không ăn thì đừng suy ngược ra nguyên nhân, đi hỏi thẳng cái lỗi.** Không tệp kiểm nào của app cũ dùng `cloudflare:test`, nên chạy vòng bằng một cấu hình pool Node là đủ: **188 bài xanh trên 22 tệp**, `tsc --noEmit` sạch cả hai bên | Mã xong, **chưa commit, chưa đẩy, chưa deploy**. Chặn duy nhất: đại ca dán đoạn Rules cho nhánh `sync_logs` (nằm cuối `src/db/sync-logs.db.ts`) |
