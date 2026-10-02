---
paths:
  - "backend/app/**"
  - "test/backend/**"
---
# Trần độ dài / kích thước dữ liệu đầu vào ở backend

> Chuyển nguyên văn từ CLAUDE.md gốc ngày 01/10/2026 — chỉ nạp khi làm việc với các đường dẫn ở trên.

⚠️ **CỘT `String(n)` MÀ SCHEMA KHÔNG KHAI `max_length` = LỖI 500, KHÔNG PHẢI
422** (duoc-CR-316 — luật này áp cho MỌI module, không riêng nhân sự). Chuỗi dài
đi thẳng xuống MySQL, và MySQL là chỗ đầu tiên phản đối: người dùng dán nhầm một
đoạn văn bản vào ô là nhận «mã sự cố», quản trị đi tra một lỗi vốn đáng ra là câu
«tối đa n ký tự». Rà 22 trường của hồ sơ nhân sự thì **12 ca trả 500**, trong đó
4 trường có lỗ từ lâu.

- Khai bằng bí danh ở `modules/employee/field_limits.py` (`Str20`, `Str255`…),
  số phải khớp ĐÚNG `String(n)` ở `model.py`.
- ⚠️ **`test/backend` chạy SQLite, và SQLite KHÔNG ép độ dài `VARCHAR`.** Bài
  kiểm nào ghi xuống DB rồi khẳng định là **xanh giả** — đúng lý do lỗ hổng này
  sống lâu vậy. Phải kiểm ở tầng SCHEMA (`pytest.raises(ValidationError)`).
- Cùng họ với nó: cột JSON cần trần **kích thước** chứ không chỉ trần số khóa
  (20 khóa × 2MB = 40MB một bản ghi, MySQL nhận hết); cột ngày cần **dải năm**
  hợp lý (MySQL nhận tới năm 9999, mà `hire_date` năm 0001 là hai nghìn năm
  thâm niên); danh sách con cần **trần số dòng** (`sort_order` SMALLINT tràn ở
  dòng 32768).
- ⚠️ Vòng dò có TRẦN ĐỘ SÂU thì chạm trần phải **chặn**, đừng trả về im lặng —
  "dò không thấy" không phải "không có". `block_manager_cycle` từng bỏ lọt đúng
  kiểu đó, và cái lọt là vòng lặp vô hạn trong bộ máy duyệt.
