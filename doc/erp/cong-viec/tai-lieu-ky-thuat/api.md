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

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `work`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/work/groups` | Cây điều hướng bên trái: nhóm → nhóm con → list, kèm list đứng lẻ (A-05). | `work_task.read` |  | tự dò: v2 `work` |
| POST | `/api/work/groups` | create group | `work_task.create` |  | tự dò: v2 `work` |
| PATCH | `/api/work/groups/{group_id}` | update group | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/groups/{group_id}` | LƯU TRỮ nhóm — không xóa cứng (A-01). | `work_task.delete` |  | tự dò: v2 `work` |
| GET | `/api/work/groups/{group_id}/members` | get group members | `work_task.read` |  | tự dò: v2 `work` |
| POST | `/api/work/groups/{group_id}/members` | Mời vào nhóm — vai trò kế thừa xuống mọi list bên trong (A-09). | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/groups/{group_id}/members/{member_id}` | remove group member | `work_task.write` |  | tự dò: v2 `work` |
| PATCH | `/api/work/label-fields/{field_id}` | update label field | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/label-fields/{field_id}` | delete label field | `work_task.delete` |  | tự dò: v2 `work` |
| POST | `/api/work/label-fields/{field_id}/options` | create label option | `work_task.write` |  | tự dò: v2 `work` |
| PATCH | `/api/work/label-options/{option_id}` | update label option | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/label-options/{option_id}` | delete label option | `work_task.delete` |  | tự dò: v2 `work` |
| GET | `/api/work/lists` | Mọi dự án mình thấy. | `work_task.read` |  | tự dò: v2 `work` |
| POST | `/api/work/lists` | create list | `work_task.create` |  | tự dò: v2 `work` |
| GET | `/api/work/lists/{list_id}` | get list | `work_task.read` |  | tự dò: v2 `work` |
| PATCH | `/api/work/lists/{list_id}` | update list | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/lists/{list_id}` | archive list | `work_task.delete` |  | tự dò: v2 `work` |
| GET | `/api/work/lists/{list_id}/activities` | Nhật ký gộp của cả dự án — việc + thành viên + cột, mới nhất trước (§8). | `work_task.read` |  | tự dò: v2 `work` |
| GET | `/api/work/lists/{list_id}/activity-actors` | Những người từng thao tác trên dự án — nguồn cho ô lọc "theo người". | `work_task.read` |  | tự dò: v2 `work` |
| GET | `/api/work/lists/{list_id}/board` | Cột + task cha + mọi thứ vẽ trên thẻ, trong MỘT lượt gọi (D-01). | `work_task.read` |  | tự dò: v2 `work` |
| GET | `/api/work/lists/{list_id}/label-fields` | get label fields | `work_task.read` |  | tự dò: v2 `work` |
| POST | `/api/work/lists/{list_id}/label-fields` | create label field | `work_task.write` |  | tự dò: v2 `work` |
| POST | `/api/work/lists/{list_id}/leave` | Tự rời danh sách (A-03) — chỉ cần quyền đọc: rời khỏi chỗ của mình không phải hành động ghi lên dữ liệu người khác. | `work_task.read` |  | tự dò: v2 `work` |
| GET | `/api/work/lists/{list_id}/members` | get list members | `work_task.read` |  | tự dò: v2 `work` |
| POST | `/api/work/lists/{list_id}/members` | add list member | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/lists/{list_id}/members/{member_id}` | remove list member | `work_task.write` |  | tự dò: v2 `work` |
| GET | `/api/work/lists/{list_id}/sections` | get sections | `work_task.read` |  | tự dò: v2 `work` |
| POST | `/api/work/lists/{list_id}/sections` | create section | `work_task.write` |  | tự dò: v2 `work` |
| GET | `/api/work/lists/{list_id}/sections/{section_id}/tasks` | Trang kế của một cột — bao-CR-483. | `work_task.read` |  | tự dò: v2 `work` |
| POST | `/api/work/lists/{list_id}/transfer` | Chuyển quyền sở hữu (A-04) — nguyên tử, giữ bất biến đúng một chủ. | `work_task.write` |  |  |
| GET | `/api/work/lists/{list_id}/trash` | Thùng rác của dự án (B-09): việc đã xóa mềm, kèm cờ `can_restore` theo quyền người xem. | `work_task.read` |  | tự dò: v2 `work` |
| GET | `/api/work/overview` | Số liệu màn Tổng quan — chỉ đếm trong những dự án mình tham gia. | `work_task.read` |  | tự dò: v2 `work` |
| PATCH | `/api/work/sections/{section_id}` | update section | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/sections/{section_id}` | Xóa cột. | `work_task.delete` |  | tự dò: v2 `work` |
| POST | `/api/work/sections/{section_id}/move` | Kéo cột sang chỗ khác — trả CẢ danh sách cột đã xếp lại. | `work_task.write` |  | tự dò: v2 `work` |
| GET | `/api/work/summary` | work summary | `báo cáo 13`, `work_task.read` |  | tự dò: v2 `report` |
| GET | `/api/work/summary/export` | work summary export | `báo cáo 13`, `work_task.export` |  | tự dò: v2 `report` |
| POST | `/api/work/task-links` | Nối việc trước → việc sau trên Gantt (B-15). | `work_task.write` |  | tự dò: v2 `work` |
| PATCH | `/api/work/task-links/{link_id}` | Đổi KIỂU (FS/SS/FF/SF) hoặc độ trễ. | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/task-links/{link_id}` | Xóa CỨNG: mũi tên là quan hệ hiển thị, không có gì để tra lại về sau. | `work_task.write` |  | tự dò: v2 `work` |
| GET | `/api/work/task-types` | `{total, items}`. | `work_task.read` |  | tự dò: v2 `work` |
| POST | `/api/work/task-types` | create task type | `setting.write` |  | tự dò: v2 `work` |
| PATCH | `/api/work/task-types/{type_id}` | update task type | `setting.write` |  |  |
| DELETE | `/api/work/task-types/{type_id}` | Chưa ai dùng thì xóa hẳn; đã có task dùng thì chỉ ngừng dùng. | `setting.write` |  |  |
| POST | `/api/work/tasks` | create task | `work_task.create` |  | tự dò: v2 `work` |
| GET | `/api/work/tasks/{task_id}` | Chi tiết + việc con. | `work_task.read` |  | tự dò: v2 `work` |
| PATCH | `/api/work/tasks/{task_id}` | Sửa, kéo cột (`section_id` + `sort_order`), tick hoàn thành (`status`). | `work_task.write` |  | tự dò: v2 `work` |
| DELETE | `/api/work/tasks/{task_id}` | Xóa MỀM — vào thùng rác của list (B-09), khôi phục được. | `work_task.delete` |  | tự dò: v2 `work` |
| PUT | `/api/work/tasks/{task_id}/assignees` | Đặt LẠI cả bộ người phụ trách + theo dõi (B-02). | `work_task.write` |  | tự dò: v2 `work` |
| PATCH | `/api/work/tasks/{task_id}/comments/{comment_id}` | Sửa bình luận CỦA CHÍNH MÌNH (E-05) — người khác sửa là 403. | `work_task.write` |  | tự dò: v2 `work` |
| PUT | `/api/work/tasks/{task_id}/label` | Đặt giá trị cho một trường tùy biến. | `work_task.write` |  | tự dò: v2 `work` |
| POST | `/api/work/tasks/{task_id}/move` | Kéo thả kanban — đổi cột và/hoặc thứ tự trong cột, đánh số lại cả cột đích. | `work_task.write` |  | tự dò: v2 `work` |
| POST | `/api/work/tasks/{task_id}/outcome` | Đánh giá kết quả task đã xong: 1 = Đạt · 2 = Phải làm lại (tự mở lại task). duoc-CR-656. | `work_task.write` |  | tự dò: v2 `work` |
| POST | `/api/work/tasks/{task_id}/restore` | Khôi phục việc khỏi thùng rác — cùng luật với xóa (cả RBAC `work_task.delete` lẫn vai trò dự án): MEMBER chỉ khôi phục việc mình tạo. | `work_task.delete` |  | tự dò: v2 `work` |
| POST | `/api/work/tasks/{task_id}/subtasks` | Thêm việc con. | `work_task.create` |  | tự dò: v2 `work` |

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
