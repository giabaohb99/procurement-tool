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

⚠️ **BẢN LƯU TRỮ HỢP ĐỒNG LAO ĐỘNG** (duoc-CR-629, 19/10/2026 — kế hoạch `plans/261019-0935-hdld-sinh-van-ban-luu-tru-cr629/`):

- Văn bản là bản lưu trữ HĐLĐ ⇔ có dòng `tab_labor_contract.document_id` trỏ tới nó (kể cả HĐ xóa mềm). Nhận diện bằng
  **liên kết**, KHÔNG bằng mã loại `HDLD` — đổi mã/tên loại trên giao diện không mở khóa. Quyền ĐỌC chỉ theo
  `labor_contract.read` trong phạm vi (`document/labor_contract_archive_access.py`); phạm vi `document` (kể cả *tất cả*),
  chia đích danh, CẤM, sổ, duyệt, phạm vi áp dụng, clone, chủ/người tạo đều KHÔNG tính. Ghi/xóa luôn `False`; sao chép,
  clone, trích, ký, duyệt, trả về, bỏ nháp → 409; tạo/đổi sang loại `HDLD` ở Văn bản → 400.
- `visible_condition()` **không còn trả `None`** (luôn có vế loại bản lưu trữ). Chỗ nào gọi nó phải xử lý như điều kiện thật;
  đừng dùng `is None` làm tín hiệu «thấy tất cả».
- Loại `HDLD` bị loại khỏi `tab_document_search` (`search_index_service.reindex`). Đường đọc văn bản mới KHÔNG đi qua
  `visible_condition`/`can()` (như `link_service.allowed_targets`) thì phải tự trừ `archive_ids()`.
- Mọi đường GHI HĐLĐ mới (lập, sửa, sinh tệp, tải bản ký, chuyển trạng thái, xóa) phải gọi
  `labor_contract/document_archive_sync.archive_sync(db, contract_id, actor_id)` sau commit (best-effort, idempotent).
  Bù HĐ cũ: `scripts/backfill_hdld_van_ban_luu_tru.py` (`--dry-run`, `--soft-delete-all` để rollback).
- Triển khai: vai trò đang chạy **không tự có** `document.read` phạm vi «Của tôi» (D-018) — tick ở màn Phân quyền cho vai
  trò giữ `labor_contract`, hoặc `SEED_FORCE_SYNC=true` một lần (đè mọi vai trò, cân nhắc).

