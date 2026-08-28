# PHÂN HỆ CÔNG VIỆC — PHÂN QUYỀN

**Bản:** 1.0 — 28/08/2026 · **CR:** CR-216 · Bản chi tiết của §5 trong
[`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md). Các quyết định Q1/Q4/Q9 đã
chốt 28/08/2026.

Nguyên tắc gốc: **hai tầng, tầng nào việc nấy.**
- Tầng 1 — RBAC hệ thống: gác CỬA phân hệ (ai vào được, ai tạo được).
- Tầng 2 — thành viên (membership): gác DỮ LIỆU (ai thấy list nào, sửa được gì trong đó).
Tầng 1 không bao giờ thay tầng 2: có `work_task.read` toàn hệ vẫn KHÔNG đọc được list
mình không phải thành viên.

---

## 1. Tầng 1 — RBAC hệ thống

- Thêm entity **`work_task`** vào `ENTITIES` (`core/permissions.py`). MỘT entity cho cả
  phân hệ — không tách `work_list` riêng, vì mọi quyền thật nằm ở tầng thành viên; tách
  hai entity chỉ đẻ thêm ô ma trận không ai hiểu.
- Ý nghĩa từng action:

| Action | Nghĩa trong phân hệ này |
|---|---|
| `read` | Thấy thẻ phân hệ "Công việc", vào được các list mình là thành viên |
| `create` | Tạo được nhóm/list mới (Q1: toàn dân) và tạo task trong list mình có quyền |
| `write` | Sửa task/list theo vai trò thành viên |
| `delete` | Xóa (mềm) theo vai trò thành viên |
| `approve` / `cancel` / `print` / `export` | KHÔNG dùng ở bản đầu (`export` để dành H-04) |

- **Seed:** mọi vai trò chuẩn trong `STD_ROLES` được `read + create + write + delete`
  (công cụ toàn dân, như Diễn đàn). Sửa seed phải sửa CẢ `seed.py` và `seed_prod.py`;
  trên prod/dev phân quyền cũ không tự đổi theo — cần thì `SEED_FORCE_SYNC=true` một lần
  (lệ `seed-prod-khong-ghi-de`).
- **`SCOPE_FIELDS` (luật B-07 — bắt buộc khai):** `work_task` khai bằng **sentinel
  `PUBLIC`**, kèm chú thích trỏ về tài liệu này. Lý do: phạm vi thật của phân hệ là "theo
  tư cách thành viên", không diễn đạt được bằng cột phòng ban/công ty của khuôn
  `apply_scope`. Đổi lại, **MỌI query trong service PHẢI tự lọc thành viên** (§2) — khai
  `PUBLIC` mà quên lọc là lộ toàn bộ, nên có test khóa riêng (§5).
- `company_id` vẫn lọc cứng ở service theo pháp nhân của người dùng, như mọi module.

## 2. Tầng 2 — thành viên: luật lọc BẮT BUỘC

Mọi đường đọc/ghi dữ liệu của phân hệ đi qua đúng một hàm service (đề xuất
`visible_list_ids(db, employee_id, company_id)`), trả về tập `list_id` người đó thấy:

```
list mình có dòng tab_work_list_member
UNION list thuộc nhóm (hoặc nhóm cha của nhóm) mình có dòng tab_work_group_member
```

- **Vai trò hiệu lực** trên một list = `min(role các nguồn)` — mời riêng ở list, kế thừa
  từ nhóm, kế thừa từ nhóm ông (Q9: số nhỏ = quyền to, lấy cao nhất).
- **Đọc một bản ghi theo id** (task, comment, attachment…) phải kiểm `list_id` của nó nằm
  trong `visible_list_ids` — chống gõ id thẳng vào URL, đúng bài học `get_scoped`.
- List `is_archived` vẫn đọc được (tra cứu), khóa mọi thao tác ghi.

## 3. Ma trận vai trò trong list/nhóm (`WorkMemberRole`)

| Việc | 1 OWNER | 2 ADMIN | 3 MEMBER | 4 VIEWER |
|---|---|---|---|---|
| Xem list + task + bình luận | x | x | x | x |
| Tạo/sửa task, kéo thả, tick việc con, bình luận | x | x | x | — |
| Xóa task bất kỳ / khôi phục từ thùng rác | x | x | chỉ task mình tạo | — |
| Sửa cột (section), tag, nhãn tùy biến của list | x | x | — | — |
| Mời / gỡ thành viên, đổi vai trò (≤ vai trò của mình) | x | x | — | — |
| Sửa tên/mô tả list, lưu trữ list | x | — | — | — |
| Chuyển quyền sở hữu | x | — | — | — |

- Mỗi list/nhóm đúng **một OWNER** (bất biến service; chuyển quyền là thao tác nguyên tử:
  hạ owner cũ xuống ADMIN + nâng người mới).
- Vai trò gán ở NHÓM áp cho mọi list bên trong theo đúng ma trận trên; riêng quyền
  "sửa tên/lưu trữ/chuyển sở hữu NHÓM" chỉ thuộc OWNER của nhóm.
- Vai trò là DỮ LIỆU của phân hệ (cột `role` trên bảng thành viên) — KHÔNG đẻ role hệ
  thống mới, không đụng `STD_ROLES`.

## 4. Quản trị hệ thống (Q4 đã chốt)

- Màn quản trị (`GET /api/work/admin/lists`, gác thêm điều kiện có role hệ thống
  `admin`/`hr_admin` tùy seed) chỉ trả **siêu dữ liệu**: tên nhóm/list, chủ sở hữu, số
  thành viên, số task, ngày hoạt động cuối. KHÔNG trả nội dung task.
- Cần vào nội dung (nhân sự nghỉ ngang, thanh tra…): bấm **"Tự thêm mình vào list"**
  (`POST /api/work/admin/lists/{id}/join`) — vào với vai trò ADMIN, **ghi audit** ai
  join lúc nào, và mọi thành viên list thấy dòng "X (quản trị) đã tham gia" trong nhật
  ký. Minh bạch là cái giữ niềm tin để người ta dám dùng.
- Tài khoản kỹ thuật không gắn nhân sự (`employee_id = 0`) chỉ đi được cửa quản trị này,
  không tham gia list như người thường (hệ quả `02` §0.1).

## 5. Kiểm thử bắt buộc đi kèm (khóa các lỗ đã từng dính nơi khác)

1. **Người ngoài bị chặn cả hai đường:** không thấy list ở danh sách VÀ 403 khi
   `GET /api/work/tasks/{id}` theo id — chống lỗ `get_scoped` kinh điển.
2. **Kế thừa nhóm:** gán MEMBER ở nhóm → thấy list mới tạo trong nhóm; mời riêng VIEWER
   ở list nhưng ADMIN ở nhóm → hiệu lực ADMIN (`min()`).
3. **Bất biến một OWNER** và chuyển quyền nguyên tử.
4. **Đính kèm phải qua kiểm quyền thành viên** — tải file bằng URL trần phải 401/403
   (bài học PQ13/H17).
5. **Audit join của quản trị** có ghi và có hiện.
6. **Entity khai đủ:** `test_pham_vi_khai_du_b07.py` xanh sau khi thêm `work_task`.
7. **Tập cha CR-215** mở rộng: key `job:{id}` phát ở chuông thì phải có trong
   `build_my_tasks` (khi làm W3).
