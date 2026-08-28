# PHÂN QUYỀN VÀ TẦNG HIỂN THỊ — ERP V2

Bản 1.0 — 28/08/2026. Phần 1–2 là lõi backend (không đổi so với v1, tóm để đứng một mình được);
phần 3–5 là tầng v2 xây thêm phía trên. Thiết kế gốc đầy đủ:
[`doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`](../../phan-quyen/Thiet_Ke_Phan_Quyen.md).

## 1. Hai trục — luật gốc của cả hệ

1. **Hành động thuộc VAI TRÒ**: ma trận `(entity × action)`, action gồm
   `read · create · write · delete · approve · cancel · print · export` (+ `import` từ CR-186).
   Danh sách entity chuẩn ở `core/permissions.py`. Endpoint gác bằng dependency `require(entity, action)`.
2. **Phạm vi dữ liệu thuộc NGƯỜI DÙNG**: mỗi cặp (người × vai trò) mang phạm vi riêng
   (`own · assigned · proc · dept · company · all`) cộng include/exclude đích danh.
   `apply_scope(...)` lọc truy vấn theo **hợp (OR)** của mọi grant có action đó trên entity.

Hai chốt an toàn phải nhớ:

- **Mọi entity phải khai trong `SCOPE_FIELDS`** (`core/scoping.py`) — hoặc cột thật, hoặc sentinel
  `PUBLIC` khi cố ý không lọc. Thiếu khai = **chặn hết** (`false()`) chứ không rơi về "thấy tất"
  (B-07/CR-131); test `test_pham_vi_khai_du_b07.py` bắt đủ số entity.
- Lấy một dòng theo id phải qua `get_scoped(...)`, không `db.get(...)` — không thì gõ id vào URL là
  vượt được bộ lọc danh sách.
- Cache hồ sơ quyền 60 giây (`_PERM_CACHE`): sửa vai trò/quyền xong phải `perm_cache_clear(user_id)`.

## 2. Hai bản seed — quyền trên DB thật là nguồn sự thật

| | `app/seed.py` (LOCAL) | `app/seed_prod.py` (prod + dev VPS) |
|---|---|---|
| Dữ liệu mẫu, tài khoản demo | Có (VT\<mã pháp nhân\>, DEMO\*...) | **Không** |
| Phân quyền đã sửa trên UI | Ghi đè theo `STD_ROLES` | **Không ghi đè** — DB là nguồn sự thật |
| Ép áp lại `STD_ROLES` | — | `SEED_FORCE_SYNC=true`, restart api một lần, trả về `false` |

Hệ quả: đổi `STD_ROLES` trong mã KHÔNG tự đổi quyền trên prod/dev — phải chủ động ép, và biết
rằng ép là đè cả phần admin đã chỉnh tay.

## 3. Tầng hiển thị frontend-v2 — từ quyền tới thẻ phân hệ

`can(entity, action)` phía FE đọc từ bản đồ quyền trả lúc đăng nhập — **chỉ để ẩn/hiện giao diện**,
chốt thật luôn nằm ở backend. Trên nó, v2 có một tầng suy luận khai báo, toàn bộ ở
`src/app/router/module-visibility.ts`:

- Mục menu khai khóa trong `routes.tsx`: `entity` (một khóa) / `entities` (nhiều khóa, hiện khi có
  **bất kỳ** khóa nào — sinh ra cho «Thiết lập văn bản» CR-157) / `action` / `manage`
  (= `create|write|delete`). Mục **không khai gì = luôn hiện** — dành cho mục cố ý công khai.
- **Thẻ phân hệ mở khi còn ít nhất một mục menu hiện được** (`canOpenModule`). Phân hệ
  `externalUrl` (HDSD) luôn mở — app đích tự gác quyền của nó.
- Thẻ khóa hiện chú thích "Bạn chưa được cấp quyền vào phân hệ này"; phân hệ `enabled: false`
  hiện "Sắp có".

### Bài học CR-196 (28/08/2026) — mục menu quên khai khóa là thẻ mở cho cả người ngoài

Mục «Tổng quan» của 5 phân hệ nghiệp vụ không khai `entity`/`entities`, nên nó luôn hiện →
thẻ Thu mua/Sản xuất/Kho/Tài chính mở với **mọi** tài khoản, kể cả văn thư không có quyền nào bên đó
(vào trong gặp dashboard toàn số 0, vì `/api/dashboard/overview` gác từng khối bằng `can(entity)`
và bỏ hẳn khóa khi thiếu quyền). Sửa: Tổng quan khai `entities` = đúng các khóa dashboard vẽ.

Luật rút ra, có test canh ở `module-registry.test.ts`: **mục menu của phân hệ nghiệp vụ phải khai
khóa quyền**; phân hệ muốn mở công khai thật phải nằm trong danh sách chủ-ý-mở của test kèm lý do.
Danh sách hiện tại: `document` («Chờ tôi duyệt» cho người duyệt ngoài phân hệ) · `forum` (bảng tin
toàn công ty) · `appearance` (tùy chọn của chính mình).

### Vì sao KHÔNG gác thẻ bằng `module.entity`

Đã thử và hỏng (22/08/2026, ghi trong chú thích `module-visibility.ts`): gác cả phân hệ bằng một
entity đại diện thì tài khoản có quyền lệch bộ (vd chỉ có `purchase_order` mà không có
`purchase_request`) bị khóa oan cả phân hệ. Suy từ menu là đúng bản chất: thấy được mục nào thì
mới có lý do mở phân hệ đó.

## 4. Phạm vi theo vai trò thu mua — mấy quy ước dễ quên

- Bậc `proc`: chỉ thấy chứng từ **đã duyệt** (kèm fix `_see_all_items`).
- `pur_admin`: ĐMH phạm vi `all` nhưng **chỉ đọc, không duyệt**; `pur_manager`: đủ + duyệt.
- Sửa phạm vi mặc định phải sửa trong seed (`STD_ROLES`) chứ không sửa tay DB local — local seed đè lại.
- YCBG che NCC theo quyền `supplier.read` — NCC lưu 2 cụm JSON req/pur trên chứng từ.

## 5. Tài khoản demo để thử quyền (chỉ LOCAL)

`seed.py` tạo sẵn: `TESTREQ / DEMONV / DEMOTP / DEMO_MANAGER_PURCHASE` (mật khẩu = mã) cho luồng
thu mua, và mỗi pháp nhân một văn thư `VT<mã pháp nhân>` (vd `VTDEGOHOLDING`, mật khẩu = mã nhân sự)
từ `seed_van_thu_phap_nhan_con.py` — đúng bộ tài khoản dùng để kiểm CR-196.
