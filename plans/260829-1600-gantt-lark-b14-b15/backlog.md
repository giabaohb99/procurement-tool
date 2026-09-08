# Gantt kiểu Lark — cụm B-14 (cột mốc) + B-15 (phụ thuộc)

**Bắt đầu 29/08/2026 · nhánh `erp-v2` · ĐÃ COMMIT ngày 31/08/2026.**
Ghi ở [`change-log.md`](../../doc/tai-lieu-ky-thuat/change-log.md) là **CR-226**.

---

## 0. Trạng thái

**XONG phần chính.** Chạy thật trên `localhost:8083` (dự án *Dự án ERP v2*, id 22): lưới
trái giàu cột · thang Ngày/Tuần/Tháng · thanh NHÓM gom con · cột mốc hình thoi · mũi tên
phụ thuộc vẽ + kéo tạo + đổi kiểu + xóa · vạch hôm nay.

Cổng kiểm tra: FE `npm run check` xanh (typecheck 0 · lint 0 lỗi, 24 cảnh báo nền · **1718
test**) · BE **2090 test** — 3 đỏ (`test_assistant_export_tool.py` ×2,
`test_export_xlsx_cr068.py` ×1) là lỗi **có sẵn từ trước**, đã đối chứng bằng `git stash`.

**ĐÃ PUSH lên `erp-v2`** (31/08/2026, tới `ff48587`): `06ee95c` backend · `63788e0`
frontend + tài liệu · `44129e9` cột mốc từ thanh công cụ + đổi kiểu mũi tên · `f1bc056`
test bảng tra kiểu · `c6ae169` chốt không dời lịch dây chuyền · `ff48587` merge remote.

⚠️ **Merge kéo theo hai thứ phải biết:**

1. **Hai đầu Alembic** (nhánh Đặt xe của người khác + nhánh Gantt) — đã hợp nhất bằng
   revision rỗng `7e93b1977593`, DB local đã `upgrade head`. Ai kéo về sau nhớ chạy lại.
2. ⚠️ **6 test ĐỎ không phải của cụm này**: `test_search_product_cr069.py` (tìm kiếm YCBG)
   gãy từ commit `f6e5e61` của người khác — họ đổi `apply_scope(...)` thành
   `scope_condition(...)` + tự `filter` trong `survey_request/controller.py`, và giờ
   `_list_query` trả **rỗng** cho mọi tìm kiếm trong test. Đã đối chứng: thư mục
   `survey_request/` trong cây này giống HỆT `origin/erp-v2`. Đáng ngờ là lỗi thật chứ
   không phải test lệch — theo luật ở `core/scoping.py`, scope không dịch được thành điều
   kiện thì nay **chặn sạch** (`false()`), tức người dùng có thể mở màn YCBG ra thấy trống
   trơn. **Người đẩy `f6e5e61` cần xem.** Ngoài ra 3 test đỏ cũ từ trước
   (`test_assistant_export_tool.py` ×2, `test_export_xlsx_cr068.py` ×1).

---

## 1. Đã làm — backend

| Việc | Chỗ |
|---|---|
| `WorkTaskKind` (1 việc · 2 **cột mốc**) + `WorkLinkType` (FS/SS/FF/SF) + nhãn tiếng Việt | `app/modules/work/model.py` |
| Cột `tab_work_task.kind` (SMALLINT, mặc định 1) | `task_model.py` |
| Bảng `tab_work_task_link` — unique `(predecessor, successor)`, FK CASCADE | `link_model.py` **(mới)** |
| Service nối / **đổi kiểu** / xóa + **chặn vòng lặp** (`creates_cycle`, hàm thuần) | `link_service.py` **(mới)** |
| `POST` · `PATCH` · `DELETE /api/work/task-links` | `task_controller.py` |
| `board` trả thêm khóa **`links`** (đi chung một lượt gọi với `tasks`) | `task_service.py` |
| Đổi việc ↔ cột mốc gộp ngày về **một mốc** (`due_date`), xóa `start_date` | `task_service.update_task` |
| Migration `a9931ac87513` — đã chạy trên DB local | `backend/migrations/versions/` |
| **22 ca test** | `test/backend/test_cong_viec_phu_thuoc.py` **(mới)** |

⚠️ Bản tự sinh của Alembic kéo theo ~150 dòng `alter_column`/`drop_index` KHÔNG liên quan
(chênh lệch tích tụ từ trước) — đã cắt sạch, migration chỉ còn đúng 2 thay đổi.

## 2. Đã làm — frontend (`frontend-v2/src/modules/work/`)

**Tệp mới:** `utils/{gantt-rows,gantt-links}.ts` (+2 tệp test) ·
`components/{gantt-grid,gantt-timeline-header,gantt-link-layer,gantt-pane-splitter}.tsx` ·
`hooks/{use-task-links,use-gantt-link-draft,use-gantt-pane-width}.ts`.

**Viết lại:** `utils/gantt-scale.ts` (`groupHeader` → `buildHeader` hai hàng; bo dải về
trọn tuần/trọn tháng; tuần ISO; `milestoneCenter`; `todayLeft`), `utils/gantt-layout.ts`,
`components/{gantt-view,gantt-row}.tsx`.

**Đụng sang khung nhìn khác (cố ý, theo chốt "một nguồn cột cho cả ba khung nhìn"):**

- Bộ «Tùy chỉnh» có thêm **`status` (Trạng thái)** và **`start` (Ngày bắt đầu)**.
- `mergeCardFields` chen trường dựng sẵn MỚI vào **trước nhãn tùy biến đầu tiên**.
- `TaskRowActions` thêm `onSetStart` / `onSetStatus`; `TaskListCell` **được xuất ra**.
- `NewTaskDraft` thêm `startDate`; `TaskDueCell` nhận `label` + `tone`.
- Panel chi tiết có nút bật/tắt **Cột mốc**; thanh công cụ có mục **«Cột mốc mới»**.

**Ba lỗi đã bắt khi soi bằng trình duyệt** (ghi lại kẻo ai đó "dọn" mất):

1. Lưới trái nuốt hết bề ngang → thêm **thanh chia kéo được** + chỉ vẽ các cột LỌT vào ô.
2. `overflow-hidden` để cắt cột **làm hỏng `sticky` của hàng tiêu đề lưới trái**.
3. Thả mũi tên vào thanh NGẮN không ăn: hai mép kéo đổi ngày phủ gần kín thanh một ngày
   → phép dò đích chuyển sang `data-task-id`.

---

## 3. Đã chốt — KHÔNG dời lịch dây chuyền

**Khách chốt 31/08/2026:** *"cập nhật bth nha, ko cần phụ thuộc gì hết"* → kéo một việc
thì **chỉ đổi ngày của chính việc ấy**. Mũi tên phụ thuộc là thứ để ĐỌC quan hệ trước–sau,
không phải bộ máy tự nắn lịch.

Hệ quả, và là chủ ý: đồ thị phụ thuộc **có thể mâu thuẫn với ngày thật** (việc sau bắt đầu
trước khi việc trước xong) mà hệ **không cảnh báo gì**. Ghi ở `05-giao-dien.md` §10.5 —
ai định "sửa" chỗ này về sau thì đọc dòng đó trước, nó không phải lỗ hổng bỏ quên.

Kéo theo: **đường găng (critical path) hoãn** vì cần lịch dây chuyền mới tính được.

## 3b. CÒN LẠI — cần chốt trước khi làm

- [ ] **Baseline** (chụp mốc kế hoạch để đối chiếu về sau) — chưa ai đòi.
- [ ] **Phụ thuộc cho VIỆC CON.** Backend chặn thẳng, có test — vì việc con không bao giờ
      lên Gantt (luật C-05). Muốn có thì phải bàn lại C-05 trước.

## 4. CÒN LẠI — vặt

- [ ] **Dữ liệu thử còn nằm trên DB local**: dự án 22 có 3 mũi tên, việc #528 là cột mốc,
      thêm việc «Cột mốc mới», ngày của #503/#507/#513 đã sửa. Dữ liệu mẫu local, biết để
      khỏi tưởng seed sinh ra.
- [ ] **Chưa tái hiện được**: sau loạt thao tác giả lập bằng script, khóa
      `erp.work.ganttpane.22` có lần bị ghi `323` (ô lưới hẹp bất thường). Kéo tay thì
      đúng. Nếu gặp lại thì soi `gantt-pane-splitter.tsx`.
- [ ] Nhóm rỗng vẫn chiếm một dòng trên Gantt — đúng như Danh sách, nhưng dự án nhiều cột
      rỗng thì biểu đồ loãng. Chờ xem người dùng có kêu không.
