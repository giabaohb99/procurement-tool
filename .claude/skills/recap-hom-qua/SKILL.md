---
name: recap-hom-qua
description: Recap buổi sáng — khi người chủ hỏi "hôm qua có cập nhật gì mới không", "recap hôm qua", "đồng nghiệp làm gì", "tuần này có gì mới". Gom commit của MỌI người trên erp-v2 và main (prod), sổ CR, sổ task, tài liệu / HDSD / kế hoạch, migration, đường API và màn mới; rồi viết bản tóm tắt theo người và theo phân hệ: chức năng THÊM / SỬA / XÓA, tài liệu mới, đã lên prod chưa, việc đang dở, chỗ cần người chủ quyết.
---

# Recap hôm qua

Trả lời từ **dữ liệu git**, không từ trí nhớ của phiên. Chỉ đọc, không sửa gì.

## 1. Gom dữ liệu

```bash
bash .claude/skills/recap-hom-qua/collect.sh                 # mặc định: ngày làm việc trước (thứ Hai lấy từ thứ Bảy) tới nay
bash .claude/skills/recap-hom-qua/collect.sh 2026-11-01      # từ ngày cụ thể
bash .claude/skills/recap-hom-qua/collect.sh 2026-10-27 2026-11-01   # một khoảng
```

Người chủ nói "tuần này", "từ thứ Hai", "3 ngày qua" thì tự quy ra ngày và truyền vào. Script đã `git fetch`; lỗi fetch thì nói rõ số liệu có thể cũ.

## 2. Đọc thêm khi cần (đừng đọc hết)

- Commit có tiêu đề mơ hồ (`fix`, `wip`, `merge`): `git show --stat <sha>` rồi đọc diff phần chính.
- Tài liệu mới hoặc sửa nhiều (mục *TÀI LIỆU / HDSD / KẾ HOẠCH*): đọc phần đầu + mục lục để tóm tắt **nội dung**, không chỉ tên tệp.
- Kế hoạch mới trong `plans/` = việc **sắp làm** của người đó — đọc `plan.md` để nói họ định làm gì tiếp.
- Tệp bị **xóa (D)** ở `backend/app/modules/` hoặc `frontend-v2/src/modules/*/pages/`: xem commit xóa để biết **chức năng nào bị bỏ** — đây là thứ người chủ cần biết nhất, đừng bỏ sót.

## 3. Viết bản recap

Ngắn, tiếng Việt, không emoji, không « » (dùng in đậm / in nghiêng). Xưng hô theo phiên đang chạy (với người chủ: gọi "đại ca", xưng "em"). Bố cục:

```
**Recap <từ ngày> → <tới ngày>** — <N> commit, <số người> người.

**<Tên người 1>** (<số> commit)
- Thêm: <chức năng mới, nói bằng lời người dùng hiểu — màn nào, làm được gì> (<mã CR>)
- Sửa: <chức năng đổi cách chạy / giao diện>
- Bỏ: <chức năng hoặc màn bị gỡ>
- Tài liệu: <tài liệu / HDSD / nghiên cứu mới, một câu nội dung mỗi cái>
- Đang dở / sắp làm: <mục sổ task `dang-lam`, kế hoạch mới trong plans/>

**<Tên người 2>** ...

**Trạng thái môi trường**
- Đã lên prod: <mã CR>
- Mới trên erp-v2, CHƯA lên prod: <mã CR> — có migration: <tên migration nếu có>

**Cần đại ca để ý / quyết**
- <migration chưa lên prod, chức năng bị bỏ, tài liệu lệch mã, bài kiểm đỏ, việc treo lâu>
```

Luật viết:

- **Nói chức năng, không nói tệp.** "Trang Cài đặt nhân sự có công tắc chặn đơn nghỉ lùi ngày" chứ không phải "thêm `leave_policy.py`". Tên tệp chỉ nêu khi người chủ hỏi sâu.
- Gom commit cùng một CR thành **một dòng**. Commit sổ / change-log / đặt chỗ thì không kể riêng.
- Tên người: `giabaohb99` = đại ca và các agent của đại ca (A1–A5, Agent 2/3/4 — đọc tiền tố CR và nội dung commit để phân biệt nếu cần); `minhduoc-tran` = anh Dược; `Agent Hub bot` = bot.
- Trạng thái prod lấy từ mục **ĐỐI CHIẾU THEO MÃ CR** (bảng *ĐÃ LÊN PROD CHƯA* có thể báo nhầm khi cherry-pick có xung đột).
- Không có commit nào trong khoảng thì nói thẳng, kèm commit gần nhất là lúc nào.
- Người chủ hỏi riêng một người hay một phân hệ ("bên Dược có gì", "HRM có gì mới") thì chỉ recap phần đó, nhưng vẫn kèm trạng thái prod của các CR đó.

## 4. Lưu lại (tùy chọn)

Người chủ bảo *lưu* thì ghi bản recap vào `doc/recap/<YYYY-MM-DD>.md` (tạo thư mục nếu chưa có). Không tự commit — chỉ commit khi được bảo.
