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
  chia đích danh, CẤM, sổ, duyệt, phạm vi áp dụng, clone, chủ/người tạo đều KHÔNG tính. **SỬA (duoc-CR-640)** ⇔ đọc được HĐ
  VÀ có `labor_contract.write` phủ HĐ VÀ `document.write` (`can_write`; HĐ xóa mềm thì chỉ đọc; `/permissions` khớp route): sửa ghi chú /
  nơi lưu / nội dung / tải-gỡ tệp «mềm» / thư mục. Trường **do đồng bộ sở hữu** (`SYNC_OWNED_FIELDS`: title, summary, keywords,
  effective_date, expire_date, doc_type_id, book_id, company_id, department_id, owner_employee_id) đổi qua PATCH → 409
  (gửi lại đúng giá trị cũ thì qua); `company_id`/`doc_type_id` = null → 422. XÓA luôn `False`. Vẫn CHẶN 409 (`_load(..., derived=True)` / `ensure_not_archive`): sao chép, clone
  (+kế hoạch/trạng thái), trích, ký, gửi duyệt / duyệt / trả về / ban hành / cấp số / bãi bỏ / xác nhận rà soát, chia sẻ và
  thu hồi chia sẻ, quan hệ, phạm vi áp dụng, đổi loại, vào sổ; tạo/đổi sang loại `HDLD` → 400. Lớp 1 của sửa/tải tệp đòi
  `document.write` — vai trò `hr_profile` seed `document: read+write` phạm vi `own` (không mở thêm văn bản thường nào).
  `/permissions` trả thêm `is_archive` để giao diện ẩn các nút bị chặn.
  **CHỦ HỢP ĐỒNG ĐỌC được (duoc-CR-652)** bản lưu trữ của chính mình khi HĐ ở trạng thái Đã ký / Đã chấm dứt và chưa xóa
  (`SELF_VIEW_STATUSES`, `core/labor_contract_codes.py`) — chỉ đọc: `can_write`, xóa, chia sẻ, nhật ký `blocked_*` vẫn theo
  luật chỉ-Nhân-sự. Đường `/api/me/labor-contracts*` lấy nhân sự TỪ TOKEN (`employee_id = 0` → rỗng), HĐ nháp/hủy/của người khác → 404.
  `keywords = 'hdld:{id HĐ}'` chỉ là dấu nhận lại văn bản MỒ CÔI: `document_archive_sync._unlinked_marked` chỉ xét văn bản loại HDLD
  chưa HĐ nào trỏ tới — danh tính văn bản↔HĐ luôn là `tab_labor_contract.document_id`, không bao giờ là `keywords`.
  `role_level_cap`: chỉ `document.write` (không `document.create`/`doc_folder.*`) ⇒ trần ĐÓNG GÓP (gắn văn bản vào thư mục,
  không hiện «+ Mới» / «Thêm thư mục con»).
- **Tệp trên bản lưu trữ**: `document_archive_files.mirror` chỉ quản lý các bản sao do CHÍNH NÓ tạo (đánh dấu
  `tab_file_link.doc_type = 'hdld_sync'`; bản sao trước CR-640 nhận ra qua thư mục lưu `labor-contract-archive`). Tệp người
  dùng tải lên KHÔNG bao giờ bị đụng. Tạo phiên bản mới chép LIÊN KẾT (dùng chung file_id) — đồng bộ chỉ chỉnh phiên bản
  hiện hành, bản cũ giữ nguyên bộ tệp, tệp chỉ bị xóa khi không còn liên kết nào. Người dùng xóa một bản sao đồng bộ ⇒ lần
  đồng bộ sau có thể thêm lại. Bản lưu trữ chỉ có bản nháp 1.0 sửa được (không ai duyệt được nó) nên thực tế mọi sửa nội dung
  đi vào bản nháp đó.
- `visible_condition()` **không còn trả `None`** (luôn có vế loại bản lưu trữ). Chỗ nào gọi nó phải xử lý như điều kiện thật;
  đừng dùng `is None` làm tín hiệu «thấy tất cả».
- Loại `HDLD` bị loại khỏi `tab_document_search` (`search_index_service.reindex`). Đường đọc văn bản mới KHÔNG đi qua
  `visible_condition`/`can()` (như `link_service.allowed_targets`) thì phải tự trừ `archive_ids()`.
- Mọi đường GHI HĐLĐ mới (lập, sửa, sinh tệp, tải bản ký, chuyển trạng thái, xóa) phải gọi
  `labor_contract/document_archive_sync.archive_sync(db, contract_id, actor_id)` sau commit (best-effort, idempotent).
  Bù HĐ cũ: `scripts/backfill_hdld_van_ban_luu_tru.py` (`--dry-run`, `--soft-delete-all` để rollback).
- Triển khai: vai trò đang chạy **không tự có** `document.read` phạm vi «Của tôi» (D-018) — tick ở màn Phân quyền cho vai
  trò giữ `labor_contract`, hoặc `SEED_FORCE_SYNC=true` một lần (đè mọi vai trò, cân nhắc).
- **Bảng mẫu dùng chung** (duoc-CR-629b bước B): `tab_document_template` chứa 2 loại mẫu bằng STI (`template_kind`: 1 `DocumentTemplate`, 2 `LaborContractTemplate`). **CẤM `query(TemplateRecord)`** / `TemplateRecord.__table__` / bulk `update()` không lọc loại ngoài migration — test `test_hdld_gop_bang_mau_cach_ly_cr629b.py::test_khong_ma_ung_dung_nao_truy_van_lop_goc` chặn; đó là lưới giữ mẫu HĐLĐ khỏi người chỉ có `doc_template`. Thêm loại mẫu mới = thêm lớp con STI + mã `DocumentTemplateKind` (số mới) + chạy `gen_status_ts.py`. Chuỗi `tab_document_template` / `.__table__` của lớp mẫu cũng CẤM ngoài `template_model.py` (test AST chặn). Lớp con STI chung bảng muốn lịch sử `tab_change_log` riêng thì khai `__change_log_table__` (mẫu HĐLĐ giữ tên cũ `tab_labor_contract_template`).
