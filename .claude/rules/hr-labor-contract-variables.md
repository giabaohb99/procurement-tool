---
paths:
  - "backend/app/modules/labor_contract/**"
  - "frontend-v2/src/modules/hr/**"
  - "test/backend/*hdld*"
---
# Hợp đồng lao động: danh mục biến mẫu (duoc-CR-630)

- **Danh mục ĐỘNG.** Biến hợp lệ trong mẫu = biến hệ thống (`placeholder_catalog.KNOWN_KEYS`, theo MÃ NGUỒN, thiếu dòng DB không làm mẫu bị từ chối) ∪ biến tùy chỉnh đang dùng
  (`tab_labor_contract_variable`) ∪ `<mã>_bang_chu` của biến tiền. Mọi nơi kiểm mẫu (tải / thay tệp / soạn web) đi qua `template_service.inspect_with_catalog`;
  `docx_engine.inspect_template` giữ THUẦN (nhận `allowed` / `sample` / `inactive`). Thay tệp / soạn web truyền `keep=row.placeholders` để mẫu cũ vẫn sửa được khi chứa biến đã ngừng dùng.
- **`custom_values` (JSON trên `tab_labor_contract`) CHỈ gán dict MỚI** — không có `MutableDict`, sửa tại chỗ SQLAlchemy không thấy. `contract_custom_values.merge_custom_values` luôn trả dict mới;
  đổi giá trị thì bỏ tệp .docx đã sinh (cùng luật lương / ngày).
- **Đếm hợp đồng giữ giá trị một biến: dùng `func.json_extract(col, bindparam('$."mã"'))`**, KHÔNG `col[key]` — trên SQLite SQLAlchemy biên dịch thành `JSON_QUOTE(JSON_EXTRACT())` nên khóa vắng ra chuỗi `'null'`.
- **Mặc định được SAO vào hợp đồng lúc LẬP** (`fill_defaults`), không áp lúc sinh tệp. Bắt buộc chặn Sinh tệp (biến mẫu dùng) và chuyển sang Đã ký (`placeholders_for_signing`: mẫu của HĐ, hoặc mẫu đang dùng của CHÍNH pháp nhân HĐ — không bao giờ quét biến toàn hệ thống); lưu nháp không bao giờ bị chặn. `"0"` là giá trị thật (Số / Tiền), rỗng mới là không có; ký tự điều khiển ASCII bị bỏ khỏi chữ; dòng tùy chỉnh trùng mã hệ thống thì giá trị hệ thống thắng + log.
- **Ghi danh mục đòi phạm vi «tất cả pháp nhân»** (`variable_access.ensure_unrestricted` = `scope_condition(...) is None`), không phải chỉ `has_global_scope` (cái đó bỏ qua giới hạn pháp nhân gán riêng theo người).
- **Giá trị biến nhạy cảm như lương:** `custom_values` nằm trong `_LABOR_CONTRACT_KEYS` (logging_policy) và bộ cột che của change_tracker; 422 chỉ nêu mã / nhãn, không nêu giá trị; `document_archive_sync._title/_summary` không đọc `custom_values`.
- **Seed biến hệ thống insert-only** (`variable_seed.ensure_system_variables`, gọi ở `seed.py` và `seed_prod.py`) — không ghi đè nhãn HR đã sửa (D-018).
- Migration `lbvar01` (down `lbrct02`); migration HĐLĐ kế tiếp phải đặt `down_revision="lbvar01"`.
