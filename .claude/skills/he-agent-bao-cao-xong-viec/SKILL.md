---
name: he-agent-bao-cao-xong-viec
description: Chạy khi xong một nghiệp vụ / một việc trong kế hoạch. Báo người chủ 3–4 dòng theo mẫu, đồng thời cập nhật Dự án ERP, kế hoạch doc/erp/00 và sổ task để người chủ theo dõi tiến độ ở một chỗ mà không phải hỏi.
---

# Báo cáo khi xong việc

Người chủ không muốn bản tin định kỳ; họ muốn **xong phần nào biết phần đó**, gọn, và nhìn tiến độ ở một chỗ.

## Mẫu báo (không dài hơn)

> **Xong:** <nghiệp vụ, mã việc / CR>. **Kiểm:** <bài kiểm, rà mã, soát dev — kết quả bằng con số>. **Còn:** <bước sau / việc dở / chờ ai>. **Cần đại ca:** <câu cần quyết kèm đề nghị> hoặc *không*.

Có việc **tự làm theo hạn mức hoặc tiền lệ** thì thêm một dòng: *Đã tự làm: ... (M3 / theo tiền lệ <ngày>)* — để người chủ biết và hoàn tác được.

## Các bước

1. **Kiểm thật trước khi báo xong.** Bài kiểm chạy rồi (con số pass / fail), rà mã có biên bản, việc có giao diện thì đã soát trên dev. Chưa kiểm thì báo *xong mã, chưa kiểm*, không báo *xong*.
2. **Sổ task** `doc/tai-lieu-ky-thuat/nhat-ky-task.md`: sửa mục của việc — `status: xong`, mô tả theo luật 7 (Bối cảnh / Đã làm / Kết quả / Còn lại, dòng cuối Mã nguồn / Commit / Deploy).
3. **Đồng bộ lên Dự án** bằng `backend/scripts/sync_task_journal.py` với tệp cấu hình của người chủ (`--env-file`), chạy `--dry-run` trước, chỉ chạy thật khi danh sách thay đổi đúng ý. Đây là việc M3 — không cần hỏi.
4. **Kế hoạch** `doc/erp/00-ke-hoach-theo-module.md`: dòng của việc ghi **XONG — <CR>, <ngày>** (chờ deploy thì ghi rõ), hoặc chuyển nội dung vào dòng *Đã có* của module.
5. **Gửi mẫu báo** cho người chủ. Không kèm nhật ký lệnh, không kèm giải thích dài — chi tiết đã nằm ở sổ task.
6. Có câu ở **Cần đại ca** thì đi qua skill `he-agent-truoc-khi-hoi` trước (có thể tiền lệ đã trả lời rồi).

## Kiểm đã làm đúng

- Người chủ mở Dự án hoặc kế hoạch `00` là thấy việc đã xong mà không cần đọc tin nhắn.
- Báo cáo không quá 4 dòng (cộng 1 dòng *Đã tự làm* nếu có).

## Bẫy đã gặp

- **Báo xong khi chưa kiểm:** duoc-CR-656 qua bài kiểm vitest nhưng hỏng bản dựng vì vitest không kiểm kiểu — *xong* phải gồm cả bước dựng (`npm run build` / `tsc`).
- **Sổ task sai dòng kết thúc** (CRLF / LF) làm commit đổi cả tệp: ghi sổ bằng Python mở `newline=""`, kiểm `git diff --stat` chỉ thêm dòng.
- **Máy không phân giải được tên miền prod** (sự cố DNS .vn 22/10): đồng bộ lỗi kết nối không phải lỗi sổ — xem lại DNS trước khi sửa sổ.
