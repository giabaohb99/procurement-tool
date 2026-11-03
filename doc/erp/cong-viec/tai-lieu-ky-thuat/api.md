# TÀI LIỆU API — DỰ ÁN VÀ CÔNG VIỆC

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `work`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `work`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/work/groups` | Cây điều hướng bên trái: nhóm → nhóm con → list, kèm list đứng lẻ (A-05). | `work_task.read` |  | |
| POST | `/api/work/groups` | create group | `work_task.create` |  | |
| DELETE | `/api/work/groups/{group_id}` | LƯU TRỮ nhóm — không xóa cứng (A-01). | `work_task.delete` |  | |
| PATCH | `/api/work/groups/{group_id}` | update group | `work_task.write` |  | |
| GET | `/api/work/groups/{group_id}/members` | get group members | `work_task.read` |  | |
| POST | `/api/work/groups/{group_id}/members` | Mời vào nhóm — vai trò kế thừa xuống mọi list bên trong (A-09). | `work_task.write` |  | |
| DELETE | `/api/work/groups/{group_id}/members/{member_id}` | remove group member | `work_task.write` |  | |
| DELETE | `/api/work/label-fields/{field_id}` | delete label field | `work_task.delete` |  | |
| PATCH | `/api/work/label-fields/{field_id}` | update label field | `work_task.write` |  | |
| POST | `/api/work/label-fields/{field_id}/options` | create label option | `work_task.write` |  | |
| DELETE | `/api/work/label-options/{option_id}` | delete label option | `work_task.delete` |  | |
| PATCH | `/api/work/label-options/{option_id}` | update label option | `work_task.write` |  | |
| GET | `/api/work/lists` | Mọi dự án mình thấy. `with_people=1` nạp thêm chủ sở hữu + thành viên — | `work_task.read` |  | |
| POST | `/api/work/lists` | create list | `work_task.create` |  | |
| DELETE | `/api/work/lists/{list_id}` | archive list | `work_task.delete` |  | |
| GET | `/api/work/lists/{list_id}` | get list | `work_task.read` |  | |
| PATCH | `/api/work/lists/{list_id}` | update list | `work_task.write` |  | |
| GET | `/api/work/lists/{list_id}/activities` | Nhật ký gộp của cả dự án — việc + thành viên + cột, mới nhất trước (§8). | `work_task.read` |  | |
| GET | `/api/work/lists/{list_id}/activity-actors` | Những người từng thao tác trên dự án — nguồn cho ô lọc "theo người". | `work_task.read` |  | |
| GET | `/api/work/lists/{list_id}/board` | Cột + task cha + mọi thứ vẽ trên thẻ, trong MỘT lượt gọi (D-01). | `work_task.read` |  | |
| GET | `/api/work/lists/{list_id}/label-fields` | get label fields | `work_task.read` |  | |
| POST | `/api/work/lists/{list_id}/label-fields` | create label field | `work_task.write` |  | |
| POST | `/api/work/lists/{list_id}/leave` | Tự rời danh sách (A-03) — chỉ cần quyền đọc: rời khỏi chỗ của mình | `work_task.read` |  | |
| GET | `/api/work/lists/{list_id}/members` | get list members | `work_task.read` |  | |
| POST | `/api/work/lists/{list_id}/members` | add list member | `work_task.write` |  | |
| DELETE | `/api/work/lists/{list_id}/members/{member_id}` | remove list member | `work_task.write` |  | |
| GET | `/api/work/lists/{list_id}/sections` | get sections | `work_task.read` |  | |
| POST | `/api/work/lists/{list_id}/sections` | create section | `work_task.write` |  | |
| GET | `/api/work/lists/{list_id}/sections/{section_id}/tasks` | Trang kế của một cột — bao-CR-483. `section_id = 0` = "Chưa phân cột". | `work_task.read` |  | |
| POST | `/api/work/lists/{list_id}/transfer` | Chuyển quyền sở hữu (A-04) — nguyên tử, giữ bất biến đúng một chủ. | `work_task.write` |  | |
| GET | `/api/work/lists/{list_id}/trash` | Thùng rác của dự án (B-09): việc đã xóa mềm, kèm cờ `can_restore` theo quyền người xem. | `work_task.read` |  | |
| GET | `/api/work/overview` | Số liệu màn Tổng quan — chỉ đếm trong những dự án mình tham gia. | `work_task.read` |  | |
| DELETE | `/api/work/sections/{section_id}` | Xóa cột. Cột còn việc thì phải kèm `?move_to=` cột nhận. | `work_task.delete` |  | |
| PATCH | `/api/work/sections/{section_id}` | update section | `work_task.write` |  | |
| POST | `/api/work/sections/{section_id}/move` | Kéo cột sang chỗ khác — trả CẢ danh sách cột đã xếp lại. | `work_task.write` |  | |
| GET | `/api/work/summary` | work summary | `báo cáo 13`, `work_task.read` |  | |
| GET | `/api/work/summary/export` | work summary export | `báo cáo 13`, `work_task.export` |  | |
| POST | `/api/work/task-links` | Nối việc trước → việc sau trên Gantt (B-15). Service chặn vòng lặp, chặn | `work_task.write` |  | |
| DELETE | `/api/work/task-links/{link_id}` | Xóa CỨNG: mũi tên là quan hệ hiển thị, không có gì để tra lại về sau. | `work_task.write` |  | |
| PATCH | `/api/work/task-links/{link_id}` | Đổi KIỂU (FS/SS/FF/SF) hoặc độ trễ. Đổi hai đầu thì xóa rồi nối lại. | `work_task.write` |  | |
| GET | `/api/work/task-types` | `{total, items}`. Không truyền `is_active` = cả loại đã ngừng (màn quản trị); ô chọn của task truyền `is_active=true`. | `work_task.read` |  | |
| POST | `/api/work/task-types` | create task type | `setting.write` |  | |
| DELETE | `/api/work/task-types/{type_id}` | Chưa ai dùng thì xóa hẳn; đã có task dùng thì chỉ ngừng dùng. | `setting.write` |  | |
| PATCH | `/api/work/task-types/{type_id}` | update task type | `setting.write` |  | |
| POST | `/api/work/tasks` | create task | `work_task.create` |  | |
| DELETE | `/api/work/tasks/{task_id}` | Xóa MỀM — vào thùng rác của list (B-09), khôi phục được. | `work_task.delete` |  | |
| GET | `/api/work/tasks/{task_id}` | Chi tiết + việc con. Không phải thành viên của list là 403, kể cả khi | `work_task.read` |  | |
| PATCH | `/api/work/tasks/{task_id}` | Sửa, kéo cột (`section_id` + `sort_order`), tick hoàn thành (`status`). | `work_task.write` |  | |
| PUT | `/api/work/tasks/{task_id}/assignees` | Đặt LẠI cả bộ người phụ trách + theo dõi (B-02). Nhiều PIC được. | `work_task.write` |  | |
| PATCH | `/api/work/tasks/{task_id}/comments/{comment_id}` | Sửa bình luận CỦA CHÍNH MÌNH (E-05) — người khác sửa là 403. Tạo/xóa đi cửa chung `/api/comments`. | `work_task.write` |  | |
| PUT | `/api/work/tasks/{task_id}/label` | Đặt giá trị cho một trường tùy biến. Sáu kiểu, xem `LabelIn` (B-13). | `work_task.write` |  | |
| POST | `/api/work/tasks/{task_id}/move` | Kéo thả kanban — đổi cột và/hoặc thứ tự trong cột, đánh số lại cả cột đích. | `work_task.write` |  | |
| POST | `/api/work/tasks/{task_id}/outcome` | Đánh giá kết quả task đã xong: 1 = Đạt · 2 = Phải làm lại (tự mở lại task). duoc-CR-656. | `work_task.write` |  | |
| POST | `/api/work/tasks/{task_id}/restore` | Khôi phục việc khỏi thùng rác — cùng luật với xóa (cả RBAC `work_task.delete` lẫn | `work_task.delete` |  | |
| POST | `/api/work/tasks/{task_id}/subtasks` | Thêm việc con. `parent_id` lấy từ đường dẫn nên client không đặt nhầm cha. | `work_task.create` |  | |

## 2. Dữ liệu vào / ra chính

Chưa có — người phụ trách điền các trường mang luật nghiệp vụ.

## 3. Lỗi riêng của phân hệ

Chưa có.

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
