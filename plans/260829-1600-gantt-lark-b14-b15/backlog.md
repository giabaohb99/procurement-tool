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

Commit: `06ee95c` (backend) · `63788e0` (frontend + tài liệu) · một commit nữa cho hai
việc thêm ngày 31/08. **Chưa push** — `git fetch` trước khi push, nhiều người cùng đẩy lên
`erp-v2`.

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

## 3. CÒN LẠI — cần khách/anh chốt trước khi làm

- [ ] **Dời lịch dây chuyền theo `lag_days`.** Cột đã có, mới LƯU và hiện. Câu hỏi phải
      chốt: kéo việc TRƯỚC thì có tự đẩy mọi việc SAU không? Nếu có thì đẩy **cứng**
      (luôn giữ đúng khoảng cách) hay chỉ đẩy khi vi phạm ràng buộc? Có hỏi xác nhận
      trước khi dời hàng loạt không? Làm sai hướng là ghi đè ngày của cả một dây việc.
- [ ] **Đường găng (critical path)** — tài liệu QLDA có nhắc. Cần `lag_days` tham gia
      tính toán nên phụ thuộc mục trên.
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
