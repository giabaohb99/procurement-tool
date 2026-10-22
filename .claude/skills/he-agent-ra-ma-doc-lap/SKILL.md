---
name: he-agent-ra-ma-doc-lap
description: Dành cho agent rà mã (không phải người viết). Rà mọi thay đổi trước khi gộp vào erp-v2: đúng sai, bảo mật và phạm vi dữ liệu, bài kiểm thiếu, hiệu năng, mã rườm. Xếp lỗi chặn / nên sửa / gợi ý, kết luận được gộp hay trả lại. Không sửa mã mình đang rà.
---

# Rà mã độc lập

Nghiên cứu và thực tế đều cho thấy: agent tự chấm bài mình thì tự khen; người rà **không dùng chung ngữ cảnh** với người viết bắt được lỗi người viết bỏ sót. Vì vậy:

- **Mở ngữ cảnh mới** cho mỗi lần rà; chỉ đọc mã việc, điều kiện xong, diff — không đọc lời giải thích của người viết trước khi tự kết luận.
- **Không sửa mã mình đang rà.** Lỗi thì ghi vào biên bản và trả lại người viết.

## Đầu vào

Mã việc / CR, điều kiện xong (trong kế hoạch hoặc sổ task), diff (`git diff <gốc>..<nhánh>`).

## Các bước

1. Đọc điều kiện xong. Diff có làm đúng **và chỉ** điều đó không? Phần thừa ngoài phạm vi ghi *nên sửa*.
2. **Chạy kiểm phần vừa sửa** (luật repo: chỉ chạy kiểm khu vừa đụng):
   - Backend: `python -m pytest -q --timeout=120 test/backend/<tệp liên quan>` trong container có stack sống.
   - Giao diện v2: `npx tsc --noEmit` cả cây + `npx vitest run src/modules/<phân hệ>`; đụng giao diện là phải dựng được (`npm run build`) — vitest không kiểm kiểu.
3. **Danh mục rà** (mỗi mục: đạt / lỗi):
   - **Phạm vi dữ liệu:** truy vấn danh sách đi qua `apply_scope`; lấy một bản ghi theo id đi qua `get_scoped`, không `db.get`; entity mới khai `SCOPE_FIELDS`; controller mới không lọc phạm vi thì có dòng miễn trừ kèm lý do thật (bài kiểm BB4).
   - **Quyền:** route gác `require(entity, action)` đúng hành động (xuất dữ liệu dùng `export`, không dùng `read`); đổi vai trò / quyền gọi `perm_cache_clear`.
   - **Dữ liệu nhạy cảm:** không lộ qua xuất CSV / API cho người thiếu `employee_sensitive.read`; không in khóa, mật khẩu, token ra log.
   - **Đầu vào:** cột `String(n)` có `max_length` ở schema (thiếu là lỗi 500); JSON có trần kích thước; ngày có dải năm.
   - **Migration:** một đầu alembic; không sửa dữ liệu bằng SQL tay có tiếng Việt.
   - **Bài kiểm:** có bài kiểm cho hành vi mới và cho ca lỗi; bài kiểm không xanh giả (SQLite không ép độ dài VARCHAR — kiểm ở tầng schema).
   - **Hiệu năng:** không truy vấn trong vòng lặp; danh sách có phân trang.
   - **Mã rườm:** lớp trừu tượng không ai dùng, cấu hình thừa, mã chết.
   - **Dấu xung đột:** `git grep -nE '^(<<<<<<<|>>>>>>>) '` phải rỗng.
4. **Viết biên bản** (ghi vào mục việc trong sổ task, phần *Rà mã*):

   | Mức | Nghĩa |
   |---|---|
   | **Chặn** | Sai hành vi, lỗ bảo mật / phạm vi, kiểm đỏ, dựng hỏng — **không được gộp** |
   | **Nên sửa** | Đúng nhưng dễ vỡ, thiếu bài kiểm ca biên, lệch luật repo |
   | **Gợi ý** | Gọn hơn, đặt tên rõ hơn |

   Mỗi lỗi: tệp:dòng · mô tả một câu · vì sao sai · cách sửa đề xuất.
5. **Kết luận:** *được gộp* (không có lỗi chặn) hoặc *trả lại* (có lỗi chặn). Trả lại quá **3 vòng** cho cùng một việc → dừng, báo điều phối để báo người chủ.
6. Lỗi đáng ra phải bị bắt tự động → đề xuất bài kiểm canh hoặc luật mới (`he-agent-cai-tien` sẽ gom).

## Bẫy đã gặp

- duoc-CR-656: thêm 5 trường mới vào kiểu dữ liệu mà không sửa 9 tệp kiểm — vitest xanh, `npm run build` đỏ.
- 19/10: commit dính dấu xung đột do agent khác rebase dở trên cây chung.
- Màn mới không lọc phạm vi (position_role, feature_usage, task_type) làm bài kiểm BB4 đỏ — chỉ thiếu dòng khai, nhưng phải soi mã để chắc không hở quyền thật trước khi khai.
- Quyền đọc dữ liệu nhạy cảm chỉ xét **khóa**, không xét phạm vi (phát hiện 21/10 khi lập bộ AGC): vai trò HR thu hẹp theo công ty vẫn đọc được nhạy cảm của cả tập đoàn qua vai trò khác nếu không thu hẹp mọi vai trò.
