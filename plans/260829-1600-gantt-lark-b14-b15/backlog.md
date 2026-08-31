# Gantt kiểu Lark — cụm B-14 (cột mốc) + B-15 (phụ thuộc)

**Ngày 29/08/2026 · nhánh `erp-v2` · CHƯA COMMIT** — mọi thứ đang nằm ở cây làm việc.
Thứ 2 mở lại đọc file này trước.

---

## 0. Trạng thái một dòng

Chạy được, đã soi tận mắt trên `localhost:8083` (dự án **Dự án ERP v2**, id 22): lưới trái
giàu cột · thang Ngày/Tuần/Tháng · thanh NHÓM gom con · cột mốc hình thoi · mũi tên phụ
thuộc vẽ + kéo tạo + xóa · vạch hôm nay. **Cổng kiểm tra xanh hết**: FE `npm run check`
(typecheck 0 lỗi · lint 0 lỗi · **1718 test**), BE **2090 test** (3 đỏ là lỗi CŨ có sẵn từ
trước — `test_assistant_export_tool.py` ×2, `test_export_xlsx_cr068.py` ×1; đã đối chứng
bằng `git stash`).

**Việc còn lại trước khi coi là xong: mục 3 (viết tài liệu) và mục 4 (commit).**

---

## 1. Đã làm — backend

| Việc | Chỗ |
|---|---|
| `WorkTaskKind` (1 việc · 2 **cột mốc**) + `WorkLinkType` (FS/SS/FF/SF) + nhãn tiếng Việt | `app/modules/work/model.py` |
| Cột `tab_work_task.kind` (SMALLINT, mặc định 1) | `task_model.py` |
| Bảng `tab_work_task_link` — unique `(predecessor, successor)`, FK CASCADE | `link_model.py` **(mới)** |
| Service nối/xóa + **chặn vòng lặp** (`creates_cycle`, hàm thuần) | `link_service.py` **(mới)** |
| `POST /api/work/task-links` · `DELETE /api/work/task-links/{id}` | `task_controller.py` |
| `board` trả thêm khóa **`links`** (đi chung một lượt gọi với `tasks`) | `task_service.py` |
| Đổi việc ↔ cột mốc gộp ngày về **một mốc** (`due_date`), xóa `start_date` | `task_service.update_task` |
| Migration `a9931ac87513` — **ĐÃ chạy trên DB local** | `backend/migrations/versions/` |
| 18 ca test mới | `test/backend/test_cong_viec_phu_thuoc.py` **(mới)** |

⚠️ Bản tự sinh của Alembic kéo theo ~150 dòng `alter_column`/`drop_index` KHÔNG liên quan
(chênh lệch tích tụ từ trước) — đã cắt sạch, migration chỉ còn đúng 2 thay đổi.

## 2. Đã làm — frontend (`frontend-v2/src/modules/work/`)

**Tệp mới:** `utils/gantt-rows.ts` · `utils/gantt-links.ts` · `components/gantt-grid.tsx` ·
`components/gantt-timeline-header.tsx` · `components/gantt-link-layer.tsx` ·
`components/gantt-pane-splitter.tsx` · `hooks/use-task-links.ts` ·
`hooks/use-gantt-link-draft.ts` · `hooks/use-gantt-pane-width.ts` (+ 2 tệp test:
`gantt-rows.test.ts`, `gantt-links.test.ts`).

**Viết lại:** `utils/gantt-scale.ts` (bỏ `groupHeader` → `buildHeader` hai hàng; bo dải về
trọn tuần/trọn tháng; tuần ISO; `milestoneCenter`; `todayLeft`), `utils/gantt-layout.ts`,
`components/gantt-view.tsx`, `components/gantt-row.tsx`.

**Đụng sang khung nhìn khác (cố ý, theo chốt "một nguồn cột cho cả ba khung nhìn"):**

- Bộ «Tùy chỉnh» có thêm **`status` (Trạng thái)** và **`start` (Ngày bắt đầu)** →
  thành cột ở cả Danh sách lẫn Gantt, thành dòng trên thẻ kanban.
- `mergeCardFields` nay chen trường dựng sẵn MỚI vào **trước nhãn tùy biến đầu tiên**
  thay vì nối vào cuối (nối cuối thì ở Gantt chúng bị cắt mất).
- `TaskRowActions` thêm `onSetStart` / `onSetStatus`; `TaskListCell` **được xuất ra** để
  lưới trái Gantt dùng lại đúng ô sửa-tại-chỗ ấy.
- `NewTaskDraft` thêm `startDate`.
- `TaskDueCell` nhận `label` + `tone` (ngày bắt đầu KHÔNG tô màu quá hạn).
- Panel chi tiết có nút bật/tắt **Cột mốc** cạnh viên trạng thái.

**Ba lỗi đã bắt và vá trong lúc soi bằng trình duyệt** (ghi lại kẻo ai đó "dọn" mất):

1. Lưới trái nuốt hết bề ngang → thêm **thanh chia kéo được** + chỉ vẽ các cột LỌT vào ô.
2. `overflow-hidden` để cắt cột **làm hỏng `sticky` của hàng tiêu đề lưới trái** (cuộn
   xuống là tiêu đề trôi mất trong khi tiêu đề trục thời gian vẫn đứng).
3. Thả mũi tên vào thanh NGẮN không ăn: hai mép kéo đổi ngày phủ gần kín thanh một ngày
   → phép dò đích chuyển sang `data-task-id` (mép kéo và chấm nối nay cũng mang id).

---

## 3. CÒN LẠI — tài liệu (làm đầu tiên hôm thứ 2)

- [ ] `doc/tai-lieu-ky-thuat/change-log.md`: thêm dòng **CR mới** (số kế tiếp sau CR-223).
      Nội dung gom từ mục 1–2 ở trên; nhớ ghi 3 lỗi đã vá và quyết định thêm hai trường
      dùng chung vào bộ «Tùy chỉnh».
- [ ] `doc/erp/cong-viec/01-danh-sach-tinh-nang.md`: **B-14, B-15 → Xong**.
- [ ] `doc/erp/cong-viec/03-lo-trinh-phase.md` §W5: bỏ "cụm Gantt mở rộng" khỏi danh sách
      ứng viên còn lại.
- [ ] `doc/erp/cong-viec/05-giao-dien.md` §10: cập nhật — nay đã có mũi tên phụ thuộc,
      cột mốc, thanh nhóm, thang tuần/tháng; ghi cả **luật chặn vòng lặp**.
- [ ] `doc/erp/13-ke-hoach-man-con-lai-v2.md` §3 — cột *Ai làm*: nếu có dòng cho việc này
      thì trả về *Xong (CR-xxx)*.

## 4. CÒN LẠI — commit

Chưa commit gì cả. Gợi ý tách hai commit cho dễ soi:

```bash
git add backend/ test/backend/test_cong_viec_phu_thuoc.py
git commit -m "feat(du-an): cot moc va phu thuoc viec truoc-sau (B-14, B-15)"

git add frontend-v2/ doc/
git commit -m "feat(du-an): dung lai khung nhin Gantt theo Lark (CR-xxx)"
```

`git fetch` trước khi push — nhiều người cùng đẩy lên `erp-v2`.

## 5. CÒN LẠI — nên làm, chưa gấp

- [ ] **Dữ liệu thử còn nằm trên DB local**: dự án 22 đang có 3 mũi tên thật, việc #528 bị
      đặt thành cột mốc, ngày của #503/#507/#513 bị sửa. Chỉ là dữ liệu mẫu local, nhưng
      biết để khỏi tưởng seed sinh ra.
- [ ] **Chưa tái hiện được**: sau loạt thao tác giả lập bằng script, khóa
      `erp.work.ganttpane.22` có lần bị ghi `323` (ô lưới hẹp bất thường). Kéo tay thì
      đúng. Nếu gặp lại thì soi `gantt-pane-splitter.tsx`.
- [ ] `lag_days` mới **lưu và hiện**, chưa có bộ dời lịch dây chuyền (đổi ngày việc trước
      không tự đẩy việc sau). Cố ý — dời lịch dây chuyền là quyết định riêng.
- [ ] Chưa có lối tạo **cột mốc** thẳng từ thanh công cụ (phải tạo việc rồi bật cờ trong
      panel chi tiết).
- [ ] Chưa đổi được **kiểu** một mũi tên đã tạo (phải xóa rồi nối lại).
- [ ] Việc CON không lên Gantt (đúng luật C-05) nên cũng không đặt phụ thuộc được —
      backend chặn thẳng, có test. Nếu khách đòi thì phải bàn lại C-05 trước.
- [ ] Cân nhắc **đường găng (critical path)** — tài liệu QLDA có nhắc, ta chưa làm.
