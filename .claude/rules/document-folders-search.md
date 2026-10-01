---
paths:
  - "backend/app/modules/document/**"
  - "backend/app/modules/doc_catalog/**"
  - "backend/migrations/**"
  - "backend/scripts/reindex_documents.py"
  - "frontend-v2/src/modules/document/**"
---
# Thư mục + tìm toàn văn của phân hệ Văn bản

> Chuyển nguyên văn từ CLAUDE.md gốc ngày 01/10/2026 — chỉ nạp khi làm việc với các đường dẫn ở trên.

⚠️ **THƯ MỤC + TÌM TOÀN VĂN của phân hệ Văn bản** (23/09/2026 — kế hoạch
`frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/`, HDSD §22–28 của
`doc/huong-dan-su-dung/van-ban/mo-ta-luong-nghiep-vu-van-ban.pdf`):

- Khóa quyền mới **`doc_folder`** (ENTITIES **+1**; `origin/erp-v2` đã lên 68 nên gộp xong là 69).
  Hệ đang chạy **không tự có** (D-018): tick ở màn Phân quyền, hoặc `SEED_FORCE_SYNC=true` một
  lần. `doc_folder.write` = mức Quản lý **đè cả dòng Cấm** trên mọi pháp nhân nó với tới — seed
  cố ý để scope `company` và đưa vào `_SYS_ENTITIES`; đừng nới thành `all`.
- `tab_doc_folder.path` chỉ do `folder_service` / `folder_move_service` / `folder_root_service`
  ghi; bảng nối `tab_document_folder_link` chỉ ghi qua `folder_link_service` (ngoại lệ duy nhất:
  `document/service.py` dọn dòng nối khi xóa văn bản). Lưu thư mục của văn bản phải **giữ** liên
  kết tới thư mục người gọi không thấy (`stage_folders`) — cùng bài học `pickWritableProfile`.
- ⚠️ **Quyền thư mục KHÔNG mở quyền đọc văn bản.** Số đếm, bảng, kết quả tìm luôn lọc thêm bằng
  `document/access_service.visible_condition`. Mức thư mục tính ở MỘT chỗ:
  `folder_access_service.effective_levels`.
- Văn bản **`company_id = 0` không có thư mục nào** — cố ý (`resolve_default_for` trả `None`).
- `tab_document_search` là **dữ liệu dẫn xuất**: thêm đường tạo/sửa văn bản mới thì gọi
  `queue_reindex`; dựng lại bằng `docker compose exec -T api python scripts/reindex_documents.py`.
- ⚠️ **Bẫy từ dừng FULLTEXT `ngram`**: MySQL bỏ các ngram trùng từ dừng tiếng Anh → «văn»,
  «bản», «toàn», «là» tìm ra **0 dòng**. Mọi lần dựng lại chỉ mục (migration mới, khôi phục sao
  lưu, `OPTIMIZE TABLE`, `ALTER` kiểu COPY) phải `SET SESSION innodb_ft_enable_stopword = 0` trong
  cùng kết nối (mẫu: migration `83679db84fd1`). Kiểm: `--check-stopwords`, vá: `--fix-stopwords`
  của cùng script. Pytest chạy SQLite nên **không bắt được**.
- `pypdf` mới trong `backend/requirements.txt` → deploy phải **dựng lại image `api`**.
