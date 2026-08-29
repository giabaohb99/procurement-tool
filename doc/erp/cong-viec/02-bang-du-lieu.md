# PHÂN HỆ CÔNG VIỆC — BẢNG DỮ LIỆU VÀ API

**Bản:** 1.1 — 28/08/2026 · **CR:** CR-216 (bản 1.1: CR-217 — ghi chú mở rộng A-10 lên `tab_work_list`) · Đọc sau [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md)

14 bảng mới, tiền tố `tab_work_*`, module backend `app/modules/work/`. CHƯA viết code —
đây là bản thiết kế để soát trước khi sinh migration.

## 0. Bốn quyết định xuyên suốt (đọc trước khi soát từng bảng)

1. **Người là `employee_id` (ID NHÂN SỰ), không phải ID tài khoản** — nhất quán với
   `assignee_id`/`requester_id` trên các chứng từ hiện có. Hệ quả chấp nhận: tài khoản
   không gắn nhân sự (admin kỹ thuật, `employee_id = 0`) không tham gia list / không được
   giao việc — họ đi cửa quản trị (`04-phan-quyen.md` §4).
2. **Ngày lưu chuỗi `"YYYY-MM-DD"`** (VARCHAR 10), so sánh từ vựng — khớp đúng cách
   chuông cảnh báo và Việc cần làm đang so hạn (`promised_date`, `due_date` của
   delivery/payable). Đổi kiểu DATE là lệch khuôn tích hợp F-02/F-03.
3. **Trạng thái / vai trò / độ ưu tiên là `SMALLINT` + `IntEnum`** (luật R2/QĐ-11), khai ở
   `backend/app/core/status_catalog.py`, đăng qua `app/core/code_sets.py`, FE lấy từ
   `gen_status_ts.py` — không hand-write bộ trạng thái nào ở TypeScript.
4. **Mọi bảng có `company_id`**; model đăng vào `app/core/all_models.py` kẻo
   autogenerate bỏ sót. Nhật ký hoạt động KHÔNG có bảng riêng — dùng `core/audit.py`
   ghi vào `tab_audit` với entity `work_task`, FE hiện bằng `AuditTimeline` sẵn có.

## 1. Bộ IntEnum

| Enum | Giá trị | Ghi chú |
|---|---|---|
| `WorkTaskStatus` | `1 OPEN` · `2 DONE` · `3 CANCELLED` | Trạng thái HỆ THỐNG của task — độc lập với cột kanban (Q2) |
| `WorkPriority` | `0 NONE` · `1 P1` · `2 P2` · `3 P3` · `4 P4` | P1 cao nhất, tô đỏ như Lark |
| `WorkMemberRole` | `1 OWNER` · `2 ADMIN` · `3 MEMBER` · `4 VIEWER` | Số nhỏ = quyền to, tiện lấy `min()` khi gộp vai trò kế thừa (Q9) |
| `WorkAssigneeKind` | `1 PIC` · `2 FOLLOWER` | Một người chỉ một dòng mỗi task |

## 2. Cụm tổ chức: nhóm — list — thành viên

### `tab_work_group` — nhóm (thư mục) chứa task list

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | INT PK | |
| company_id | INT, index | |
| parent_id | INT FK `tab_work_group.id`, NULL | Nhóm con. **Service chặn quá 2 cấp**: cha đã có `parent_id` thì không nhận con |
| name | VARCHAR(200) | |
| description | TEXT | |
| sort_order | INT | Thứ tự trên sidebar |
| is_archived | SMALLINT | 0/1 — lưu trữ, không xóa cứng (A-01) |
| created_at / updated_at | DATETIME | |

### `tab_work_list` — danh sách công việc

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | INT PK | |
| company_id | INT, index | |
| group_id | INT FK `tab_work_group.id`, NULL | NULL = list đứng lẻ ngoài nhóm (hợp lệ, A-08) |
| name | VARCHAR(200) | |
| description | TEXT | |
| color | VARCHAR(20) | Mã màu hiển thị sidebar |
| sort_order | INT | |
| is_archived | SMALLINT | 0/1 |
| created_at / updated_at | DATETIME | |

**Mở rộng A-10 — list kiểu dự án (bản 1.1, QĐ-T2 ở 01 §4b, làm ở W4):** thêm lên chính
bảng này, KHÔNG đẻ bảng `tab_project` riêng: `kind` SMALLINT (`1 thường · 2 dự án`,
mặc định 1) · `start_date` / `end_date` VARCHAR(10) "YYYY-MM-DD" (§0.2) · `proj_status`
SMALLINT — IntEnum mới `WorkProjectStatus`, chỉ có nghĩa khi `kind = 2`, bộ giá trị chốt
lúc làm W4. Tiến độ tổng KHÔNG có cột — tự tính `COUNT(task DONE) / COUNT(task)` lúc đọc.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | INT PK | |
| company_id | INT, index | |
| group_id / list_id | INT FK, index | Mỗi bảng một cột |
| employee_id | INT, index | ID nhân sự (§0.1) |
| role | SMALLINT | `WorkMemberRole`. Mỗi group/list đúng MỘT dòng `OWNER` — service giữ bất biến khi chuyển quyền sở hữu (A-04) |
| created_at | DATETIME | |

Unique `(group_id, employee_id)` và `(list_id, employee_id)`. Tách hai bảng thay vì một
bảng đa hình `target_type/target_id` để giữ được FK thật. **Vai trò hiệu lực trên một
list** = `min(role mời riêng ở list, role kế thừa từ nhóm cha, role kế thừa từ nhóm ông)`
— tính trong service, không lưu (Q9: lấy vai trò cao hơn).

Mời theo phòng ban (A-06, P1): thêm cột `department_id` NULL vào hai bảng này, một dòng
= một phòng; nở ra nhân sự lúc tính quyền — KHÔNG chép từng người vào bảng.

## 3. Cụm việc: cột — task — việc con — người phụ trách

### `tab_work_section` — cột kanban của một list

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | INT PK | |
| company_id | INT | |
| list_id | INT FK, index | |
| name | VARCHAR(100) | "Documentation", "To do"… — người dùng tự đặt, KHÔNG phải trạng thái |
| color | VARCHAR(20) | |
| sort_order | INT | Kéo thả đổi thứ tự cột |
| created_at | DATETIME | |

Tạo list là seed sẵn 3 cột mặc định ("Cần làm", "Đang làm", "Hoàn thành") — sửa/xóa tự do.
Xóa cột đang có task: bắt chọn cột nhận task trước, không xóa mồ côi.

### `tab_work_task` — task và việc con (chung một bảng)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | INT PK | |
| company_id | INT, index | |
| list_id | INT FK, index | Việc con mang `list_id` CỦA CHA (C-05) |
| section_id | INT FK `tab_work_section.id`, NULL | Việc con để NULL — không nằm cột nào nên không bao giờ hiện trên kanban |
| parent_id | INT FK `tab_work_task.id`, NULL | Việc con trỏ cha. **Service chặn cấp 3**: cha đã có `parent_id` thì không nhận con |
| title | VARCHAR(500) | |
| description | TEXT | Bản đầu văn bản thường; rich text tính sau |
| status | SMALLINT | `WorkTaskStatus` |
| priority | SMALLINT | `WorkPriority`, mặc định 0 |
| start_date | VARCHAR(10) | `"YYYY-MM-DD"`, rỗng được |
| due_date | VARCHAR(10) | Nền cho nhắc hạn F-03 và key `job:{id}` |
| sort_order | INT | Thứ tự tay trong cột (B-07); với việc con là thứ tự trong danh sách con |
| created_by | INT | employee_id người tạo |
| completed_at | DATETIME NULL | Đặt khi `status -> DONE`, xóa khi mở lại |
| completed_by | INT NULL | employee_id |
| deleted_at | DATETIME NULL | Xóa mềm — thùng rác B-09; mọi query mặc định lọc `deleted_at IS NULL` |
| created_at / updated_at | DATETIME | |

Đếm việc của list/cột và tiến độ chỉ tính **task cha** (`parent_id IS NULL`); việc con chỉ
đóng góp vào `n/m` của thẻ cha (C-02). Hoàn thành cha KHÔNG tự tick hết con — hiện cảnh
báo "còn n việc con chưa xong" và cho xác nhận.

### `tab_work_task_assignee` — người phụ trách và người theo dõi

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | INT PK | |
| task_id | INT FK, index | |
| employee_id | INT, index | Index phục vụ "Việc của tôi" (G-03) và `job:{id}` trong Việc cần làm |
| kind | SMALLINT | `WorkAssigneeKind` — PIC nhiều người được (Q5, như Lark) |
| created_at | DATETIME | |

Unique `(task_id, employee_id)` — một người một vai trên một task; PIC thắng follower.

## 4. Cụm nhãn tùy biến

⚠️ **`tab_work_tag` và `tab_work_task_tag` KHÔNG CÒN** (migration `c8a1d4f60b72`).
Tag nay là một trường tùy biến kiểu CHỌN NHIỀU tên "Tag", nạp sẵn cho list mới
nhưng `system_key` rỗng — đổi tên, đổi bộ giá trị, xóa hẳn đều được như mọi
trường khác. Xem §4.1 bên dưới.

### `tab_work_label_field` + `tab_work_label_option` + `tab_work_task_label` — nhãn tùy biến (B-08)

| Bảng | Cột | Ghi chú |
|---|---|---|
| `tab_work_label_field` | id · company_id · list_id FK · name VARCHAR(100) · sort_order · created_at | Một TRƯỜNG do list tự đặt ("Phiên bản"). Unique `(list_id, name)` |
| `tab_work_label_option` | id · field_id FK · name VARCHAR(100) · color · sort_order | Bộ giá trị của trường ("Thumua"…). Unique `(field_id, name)` |
| `tab_work_task_label` | id · task_id FK · field_id FK · option_id FK | **Unique `(task_id, field_id)`** = chọn MỘT giá trị mỗi trường (single-select). Sau này B-13 thêm kiểu khác thì thêm cột `value_text/value_number` vào bảng này, không đập lại |

### 4.1 Ba trường từng là "cứng" nay đều là nhãn tùy biến

| Trường | Trước | Nay |
|---|---|---|
| Độ ưu tiên | cột `tab_work_task.priority` | trường `system_key = 'priority'`, kiểu chọn một (migration `b2f7c1d94a30`) |
| Tag | bảng `tab_work_tag` + `tab_work_task_tag` | trường tên "Tag", kiểu CHỌN NHIỀU, `system_key` rỗng (migration `c8a1d4f60b72`) |

Lý do gộp: mọi thứ đụng tới một trường — vẽ trên thẻ, ô nhập ở panel chi tiết, lọc,
sắp xếp, hộp sửa danh mục — phải viết một lần cho tag và một lần cho trường tùy biến,
và hai bản ấy đã bắt đầu lệch nhau. Đổi lại, mỗi dự án tự quyết bộ trường của mình.

`system_key` chỉ là CÁI MÓC để mã nguồn tìm lại trường ưu tiên (tô màu thanh Gantt,
đếm biểu đồ Tổng quan) — nó khóa mỗi việc đổi KIỂU, còn tên · màu · bộ giá trị vẫn
sửa được. Trường "Tag" cố ý KHÔNG mang móc nào.

## 5. Cụm trao đổi: bình luận — đính kèm

### `tab_work_comment` (E-01)

id · company_id · task_id FK index · employee_id · content TEXT · is_edited SMALLINT ·
deleted_at DATETIME NULL · created_at / updated_at. Theo khuôn comment CR-033 (đã tái
dùng ở Diễn đàn); nhắc tên @ (E-02, P1) parse từ content, không bảng riêng.

### `tab_work_attachment` (E-03, P1)

id · company_id · task_id NULL · comment_id NULL (đúng một trong hai) · file_key (đường
R2, có `STORAGE_PREFIX`) · file_name · file_size · content_type · uploaded_by
(employee_id) · created_at. **Tải xuống bắt buộc qua endpoint kiểm quyền thành viên**
(bài học PQ13/H17 — không có URL công khai).

## 6. Phác API (prefix `/api/work` — tránh `/api/tasks` đã bị Việc cần làm chiếm)

| Nhóm | Endpoint | Ghi chú |
|---|---|---|
| Nhóm | `GET/POST /api/work/groups` · `PATCH/DELETE /groups/{id}` · `GET/POST/PATCH/DELETE /groups/{id}/members` | Sidebar trả cây nhóm + list lồng sẵn một lần |
| List | `GET/POST /api/work/lists` · `PATCH/DELETE /lists/{id}` · `/lists/{id}/members` · `/lists/{id}/sections` · `/lists/{id}/label-fields` (+`/options`) | Không còn `/lists/{id}/tags` lẫn `PUT /tasks/{id}/tags` |
| Task | `GET /api/work/lists/{id}/board` (cột + task cha, payload kanban một phát) · `POST /api/work/tasks` · `PATCH /api/work/tasks/{id}` (sửa, kéo cột = `section_id` + `sort_order`, tick xong = `status`) · `DELETE` (xóa mềm) · `/tasks/{id}/subtasks` · `/tasks/{id}/comments` | |
| Cá nhân | `GET /api/work/my-tasks` | Gom task mình là PIC từ mọi list, nhóm theo hạn (G-03) |
| Quản trị | `GET /api/work/admin/lists` · `POST /api/work/admin/lists/{id}/join` | H-03/Q4 — join tự ghi audit |

Tất cả trả phong bì `{success, message, data}` qua `core/response.py` như mọi module.

## 7. Chỉ mục (index) đáng chú ý

- `tab_work_task (list_id, parent_id, deleted_at)` — query kanban/danh sách chính.
- `tab_work_task (due_date, status)` — job nhắc hạn Celery quét (F-03).
- `tab_work_task_assignee (employee_id)` — "Việc của tôi" + đổ vào `build_my_tasks`.
- `tab_work_list_member (employee_id)` / `tab_work_group_member (employee_id)` — dựng
  sidebar và lọc phạm vi thành viên ở MỌI query (xem `04-phan-quyen.md` §2).
