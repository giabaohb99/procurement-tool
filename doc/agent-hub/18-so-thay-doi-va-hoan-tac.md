# 18 — Sổ thay đổi do bot ghi + hoàn tác 24 giờ (phase 15.1, ai-CR-182)

> Viết 13/10/2026. Đại ca chốt cùng ngày: hạn hoàn tác **24 giờ** · từng người xem **của mình**, người có `agent_group.read`
> (quản lý bot AI) xem **hết** · **KHÔNG** hoàn tác khi phiếu đã gửi duyệt hoặc đã bị người khác sửa. Phần LÕI phía ERP đã
> xong (`assistant/change_service.py`, `change_model.py`, `change_controller.py`); hai phần kế dựa vào tài liệu này:
> **(a)** bot Telegram (lệnh «bot vừa làm gì» + nút Hoàn tác), **(b)** màn web ERP v2.

## 1. Bảng `tab_assistant_change` (DB **ERP**, migration `grp14`)

| Cột | Ý nghĩa |
|---|---|
| `user_id` | người bấm xác nhận — cũng là người được hoàn tác |
| `entity` · `entity_id` · `doc_code` | `purchase_request` · `survey_request` · `leave_request` · `payment_request` · `work_task` · `ticket` · `account_setup` |
| `action` (`ChangeAction`) | 1 CREATE · 2 UPDATE · 3 DELETE · 4 SUBMIT · 5 REUSE (dùng lại nháp / sửa đè đơn nghỉ trùng ngày) · 6 ACCOUNT |
| `summary` | câu tiếng Việt: «Sửa Đơn nghỉ phép NP001: Đến ngày», «Tạo yêu cầu mua hàng (YCMH) YCMH00123» |
| `before` · `after` (JSON ≤ 64 KB) | `{fields, lines, leave, status}` — chỉ trường đã đổi (+ dòng nếu sửa dòng); tạo → `before = null`; xóa → `after = null`; quá trần: cắt dòng, `truncated: true` |
| `after_sig` | dấu trạng thái phiếu NGAY SAU khi ghi (`change_service.state_sig`) — lệch dấu hiện tại = có người sửa chen |
| `source` (`ChangeSource`) | 0 không rõ · 1 Telegram (mọi lượt qua cổng B) · 2 web · 3 Zalo (chưa dùng) |
| `undo_status` · `undone_at` · `undone_by` · `undo_of` | 0 chưa · 1 đã hoàn tác · 2 bị chặn; dòng ghi việc hoàn tác trỏ `undo_of` về dòng gốc và **không** hoàn tác lại được |

## 2. Luật hoàn tác (kiểm lại TỪ ĐẦU lúc bấm — `change_service._check_undo`)

1. Trong 24 giờ kể từ `created_at`; chưa hoàn tác; không phải dòng `undo_of`. SUBMIT → «rút / trả về bằng tay»;
   ACCOUNT → «sửa tay ở màn Phân quyền» — hai loại này **chỉ ghi sổ**.
2. Chính người đó hoặc quản lý bot AI, dùng **quyền + phạm vi hiện tại của mình**: `write` cho UPDATE / REUSE, `delete`
   cho CREATE / DELETE (phiếu hỗ trợ: `write`, vì không xóa — đóng + ghi chú).
3. Phiếu còn (DELETE: còn đang xóa mềm), còn **Nháp / Bị trả lại** (đơn nghỉ: Nháp / Trả về; việc Dự án: đang mở), và
   `state_sig` hiện tại == `after_sig`. Chặn vì phiếu → `undo_status = 2`.
4. Làm ngược qua **đúng service của form**: UPDATE / REUSE → `update_tool.write_doc` ghi lại `before` (đơn nghỉ: đủ
   `before.leave` qua `request_service.update`); CREATE → xóa mềm (`delete_pr` / `delete_sr` / `soft_delete` /
   `delete_task`; ticket: đóng); DELETE → `restore_soft_deleted` (bỏ `is_deleted` + `deleted_at` + `deleted_by`, hoặc
   `deleted_at` của việc Dự án kèm việc con). Xong: dòng gốc `undo_status = 1`, thêm **một dòng ngược** (`undo_of`),
   nhật ký ERP `undo` (+ `restore` khi khôi phục).

## 3. Hợp đồng API

**DÒNG** = `{id, when (ISO), user_id, entity, entity_label, entity_id, doc_code, action, action_label, summary, source,
source_label, undo_status, undo_status_label, undo_of, can_undo, undo_reason, url}` — `url` là đường chi tiết v2
(`/procurement/purchase-requests/{id}`, `/hr/leave-requests/{id}`, `/project/tasks/{id}`, `/system/permissions/users/{id}`…).
Nút «Hoàn tác» chỉ bật khi `can_undo`; tắt thì hiện `undo_reason`.

| Đường | Tham số | Kết quả `data` |
|---|---|---|
| Web `GET /api/assistant/changes` (gác `assistant.read` + cờ AI) | `limit` 1–200 (mặc định 30) · `all=1` chỉ khi có `agent_group.read` (không thì 403) | `{items: [DÒNG]}` mới nhất trước |
| Web `GET /api/assistant/changes/{id}` | — | DÒNG + `before`, `after`, `undone_at`, `undone_by`; của người khác → 404 |
| Web `POST /api/assistant/changes/{id}/undo` | không thân | `{id (dòng ngược), undo_of, entity, entity_label, doc_code, action, action_label, summary, url}`; chặn → 400 (hạn / loại) · 403 (quyền / người khác) · 404 · 409 (đã hoàn tác / phiếu đổi / đã gửi duyệt) |
| Cổng B `GET /api/agent-gw/changes/mine` (`gateway_user`) | `limit` 1–100 (mặc định 20) | `[DÒNG]` của chính người gọi |
| Cổng B `POST /api/agent-gw/changes/undo` | `{id}` | như web; lỗi nghiệp vụ trả `{error, status}` (không 4xx) |

Phía bot gọi qua `agent_hub/erp.py`: `erp.my_changes(db, user, limit)` → `[DÒNG]`; `erp.undo_change(db, user, change_id)`
→ dict kết quả, lỗi ném `HTTPException(status, detail)` (cùng khuôn `erp.confirm_proposal`). Gợi ý phần (a): lệnh «bot vừa
làm gì» / «hoàn tác» → thẻ liệt kê DÒNG có `can_undo`, nút callback `undo:<id>` → `erp.undo_change` → trả `summary`.

## 4. Giả định / còn để lại

- Cổng B ghi `source = 1` cho mọi lượt (dịch vụ AI hiện chỉ nhận Telegram); mở Zalo thì thêm header kênh ở
  `erp._Remote._call` rồi đọc ở `GATEWAY_SOURCE`. Chạy chung tiến trình (embedded) ghi 0.
- ACCOUNT chỉ ghi khi có gì đổi; YCTT sửa câu in khi đã gửi duyệt vẫn ghi sổ nhưng không hoàn tác (luật «đã gửi duyệt»).
- Hoàn tác xóa YCMH không nối lại dây YCBG → YCMH đã gỡ lúc xóa (`unlink_deleted_pr`). Việc Dự án chỉ có đường tạo / xóa
  qua bot nên hoàn tác cũng chỉ hai đường đó.
