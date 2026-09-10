# PHÂN HỆ ĐIỂM CÀ PHÊ — PHÂN QUYỀN

**Bản:** 1.0 — 08/09/2026 · Đọc sau [`02-bang-du-lieu.md`](./02-bang-du-lieu.md) ·
Chạy trên hệ phân quyền hai trục sẵn có (`core/permissions.py` + `core/auth.py` + `core/scoping.py`)
— **không viết cơ chế mới**, chỉ khai báo.

## 1. Entity mới — 4 cái, khai đủ cả hai chỗ

Luật B-07: entity vào `ENTITIES` mà thiếu `SCOPE_FIELDS` là chặn tất (`false()`) và test
`test_pham_vi_khai_du_b07.py` đỏ (44/44 hiện tại → **48/48** sau phase CP1 — nhớ sửa số
đếm trong test).

| Entity | Bảng | SCOPE_FIELDS | Vì sao |
|---|---|---|---|
| `coffee_policy` | `tab_coffee_policy` | company (`company_id`) | Chính sách không có dữ liệu cá nhân; lọc theo pháp nhân là đủ |
| `coffee_member` | `tab_coffee_member` | employee (`employee_id`) + company (`company_id`) | Scope `own` = thấy dòng của mình; quản trị scope rộng thấy cả |
| `coffee_ledger` | `tab_coffee_ledger` | employee (`employee_id`) + company (`company_id`) | **Cột sống của cả phân hệ**: "nhân viên chỉ thấy sổ của mình" là một phép áp scope, không phải một câu hứa. Đọc lẻ theo id bắt buộc qua `get_scoped` |
| `pos_order` | `tab_pos_order` | company (`company_id`) — cân nhắc thêm employee | Dữ liệu vận hành/đối soát, người thường không cần; nếu sau này màn Ví muốn hiện tên món từng đơn thì thêm chiều employee lúc đó |

`tab_pos_sync_run` **không thành entity riêng** — nhật ký đồng bộ đọc/ghi qua quyền của
`pos_order` (cùng một mối quan tâm vận hành, thêm entity thứ 5 chỉ tăng ô ma trận phải seed).

## 2. Ma trận hành động (dùng bộ ACTIONS sẵn có, không thêm action mới)

| Entity | read | create | write | delete | Ghi chú |
|---|---|---|---|---|---|
| `coffee_policy` | xem chính sách | thêm dòng mức mới | sửa dòng CHƯA dùng | — | Dòng đã qua reset: service chặn sửa (02 §2), delete không cấp cho ai |
| `coffee_member` | xem thành viên / **tra cứu quầy** | gán cấp người mới | ghép POS365, đổi cấp, đổi trạng thái | — | |
| `coffee_ledger` | xem sổ (scope quyết của ai) | — | **điều chỉnh tay A-07 + xử lý đơn chưa khớp** | — | `create` không mở: dòng sổ chỉ sinh từ service/task; delete không tồn tại theo thiết kế |
| `pos_order` | xem đơn kéo về + nhật ký đồng bộ | — | **bấm chạy đồng bộ tay** | — | |

Ba quyền tách của PS12 nằm ở ba ô khác nhau: xem sổ người khác = `coffee_ledger.read` +
scope rộng · điều chỉnh = `coffee_ledger.write` · chạy đồng bộ = `pos_order.write`. **Một
vai trò không được ôm cả ba** trừ quản trị hệ thống.

## 3. Vai trò seed (STD_ROLES)

| Vai trò | Cấp gì | Scope mặc định |
|---|---|---|
| *(mọi nhân viên — vai trò chung hiện có)* | — không cấp entity nào — | Ví của tôi đi qua `GET /api/coffee/my-wallet`: chỉ cần đăng nhập, service tự lấy `employee_id` của người gọi. **Không cấp `coffee_ledger.read` đại trà** — đường `own` đã có endpoint riêng, khỏi phát quyền rộng rồi bóp bằng scope |
| `coffee_admin` | `coffee_policy` read/create/write · `coffee_member` read/create/write · `coffee_ledger` read/write · `pos_order` read/write | company (quán một pháp nhân) hoặc all |
| `coffee_counter` (quầy) | `coffee_member` read | company. Endpoint `lookup` **tự cắt dữ liệu trả về** còn `{name, balance}` — quyền read của quầy không kéo theo xem lịch sử, vì API không trả |
| `coffee_finance` (tùy chọn, bản 2) | `coffee_ledger` read + export | company — phục vụ E-01/E-02, khai khi làm |

Seed ở cả `seed.py` lẫn `seed_prod.py`; đổi trên prod sau này nhớ luật `SEED_FORCE_SYNC`.

## 4. Chỗ dễ hở — soát lúc review CP1/CP2

1. **`my-wallet` với tài khoản không gắn nhân sự** (`employee_id = 0`): trả ví rỗng + câu
   giải thích, **không** trả sổ của employee_id 0 gộp chung (mọi dòng task tự động
   `created_by=0` không phải là ví của ai).
2. **`lookup` là chỗ rò thông tin nếu viết ẩu**: không nhận wildcard, không phân trang danh
   sách toàn bộ thành viên, chỉ trả khi khớp đúng mã NV hoặc SĐT đủ; đáp án tối đa 1 người.
3. **Đường ghi sổ duy nhất** là service (`ledger_service.append(...)`) — controller `adjust`
   và các task đều gọi nó; hàm này là chỗ duy nhất biết luật `uniq_key`, `reason` bắt buộc.
   Không import model Ledger ở chỗ khác để `db.add` tay.
4. **Audit**: mọi mutation (policy, member, adjust, resolve, chạy tay) qua `core/audit.py
   record(...)` như mọi module — màn chi tiết hiện `AuditTimeline` miễn phí.
5. Mutation quyền/vai trò lúc seed hay trên UI xong phải `perm_cache_clear` — cache profile
   60s là đủ để "vừa cấp quyền xong sao chưa thấy" thành ticket ma.

**Tiếp theo:** [`05-giao-dien.md`](./05-giao-dien.md).
