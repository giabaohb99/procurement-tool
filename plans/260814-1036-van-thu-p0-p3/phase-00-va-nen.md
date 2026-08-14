# PHASE 0 · VÁ NỀN

> [← plan.md](./plan.md) · Nguồn: `van-thu/00` mục 3, `01` nhóm N, `02` mục 4, `04` mục 3
> **Phase duy nhất chạm vào hệ Thu mua đang chạy thật. Không sinh ra tính năng nào người dùng thấy.**

⚠️ **Số tài khoản prod chưa chốt.** `van-thu/00` mục 2.1 ghi "gần 300 tài khoản", `CLAUDE.md` ghi "~20–100 users", DB local chỉ có 7 (dữ liệu seed). Con số **không đổi thiết kế nào** ở phase này — lý do chuyển cache quyền sang Redis (P0-T05) là **tính đúng đắn giữa nhiều tiến trình** (thu hồi quyền phải có hiệu lực ngay và đều trên mọi worker), không phải chịu tải. Nhưng vẫn phải chốt để ước lượng đúng mức rủi ro khi deploy: đếm `tab_user WHERE is_active = 1` trên prod trước khi bắt đầu.

## Tổng quan

| | |
|---|---|
| Ưu tiên | Cao nhất — chặn mọi phase sau |
| Trạng thái | ☐ Chưa bắt đầu |
| Mã `01` | N01–N09, M01, H03 |
| Migration | M1 (+`tab_file_access_log` kéo sớm từ M10) |

Đưa văn bản mật vào một hệ mà tệp đính kèm tải được không cần quyền là tạo ra **sự cố**, không phải sản phẩm. Ba lỗ hổng + hai chỗ hở phải vá xong trước khi mở tài khoản văn thư trên prod.

## Điểm cần biết trước

1. **Không dồn deploy.** Mỗi task một lần lên dev, theo dõi vài ngày, rồi lên prod. Task nào cũng phải có cờ tắt.
2. `tab_file.url` đang lưu **link công khai vĩnh viễn**. Xử lý 3 bước: (1) ngừng ghi giá trị mới — phase này · (2) xóa trắng giá trị cũ sau khi chuyển hết · (3) bỏ cột ở M11, **sau khi chạy thật ổn**. Không xóa cột ngay, còn mã cũ đang đọc.
3. `_PERM_CACHE` trong `core/auth.py` sống 60s **trong tiến trình** — chạy nhiều worker thì mỗi worker một bản. Thu hồi quyền trễ và lệch nhau.
4. Phạm vi phòng ban đang khớp bằng **chuỗi tên** (`SCOPE_FIELDS[...]["dept_name"] = "department"`). Đổi tên phòng ban = mất quyền hàng loạt, im lặng.
5. **Chỗ dễ sai số 6** (`04` mục 13): bảng mới quên khai `SCOPE_FIELDS` thì **không lọc gì cả** — hiện 9/28 entity có khai.

## Danh sách task

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P0-T01** | BE | **Kiểm thử 5 luồng duyệt hiện tại** | Bắt buộc làm **đầu tiên**, không chờ ai. `test/backend/test_approval_purchase_request.py`, `..._survey.py`, `..._survey_request.py`, `..._purchase_order.py`, `..._payment_request.py`. Mỗi tệp phủ: nộp → duyệt → từ chối → hủy → kiểm quyền `require()` → kiểm `apply_scope`. Đây là **lưới an toàn duy nhất** cho mọi phase sau |
| **P0-T02** | DB | **Migration M1** | `tab_file` thêm `sha256 CHAR(64)`, `is_private BOOLEAN DEFAULT TRUE`, `scan_status TINYINT DEFAULT 0`. `tab_notification` thêm `app VARCHAR(30) DEFAULT 'thumua'`. Tạo `tab_file_access_log` (`file_id, document_id NULL, user_id, action TINYINT, ip, user_agent, created_at`) + index `(file_id, created_at)`, `(user_id, created_at)`. **Kéo sớm từ M10** vì H03 thuộc phase này. Khai model vào `app/core/all_models.py` |
| **P0-T03** | BE | **Kho R2 riêng tư hoàn toàn** | Tắt public access trên bucket. `modules/attachment/service.py`: ngừng ghi `url`, đặt `is_private = True` cho mọi tệp mới, tính `sha256` lúc upload. Script chuyển tệp cũ (Python/SQLAlchemy, **không chạy SQL tiếng Việt qua dòng lệnh mysql**) |
| **P0-T04** | BE | **Link tạm có kiểm quyền** | `GET /api/attachments/{id}/link` → `require(entity, "read")` + `apply_scope` trên bản ghi chủ → sinh presigned URL **sống 60–120s** → ghi `tab_file_access_log` (action 4). `GET .../view` và `.../download` ghi action 1 và 2. Trả lỗi 403 chứ không 404 khi đủ quyền đọc nhưng cấm tải |
| **P0-T05** | BE | **Bộ nhớ đệm quyền sang Redis** | `core/auth.py`: `_PERM_CACHE` → Redis key `perm:{user_id}` TTL 60s. `perm_cache_clear(user_id)` **publish** lên kênh `perm:invalidate` để mọi tiến trình xóa ngay. Rà lại toàn bộ chỗ mutate role/permission/user_role đã gọi `perm_cache_clear` chưa |
| **P0-T06** | ∞ | **Phạm vi phòng ban khớp bằng ID** | Thêm cột `department_id` vào các bảng đang dùng chuỗi `department` (`tab_purchase_request`, `tab_survey_request`, `tab_purchase_order`), backfill theo tên, đổi `SCOPE_FIELDS` từ `dept_name` sang `dept_id`. Giữ cột chuỗi để hiển thị. FE: nơi nào gửi `department` chuỗi thì gửi kèm id |
| **P0-T07** | BE | **Vá loại trừ phòng ban** | Cấu hình lưu một tên trường, mã nguồn tra một tên khác → tick "loại trừ phòng X" không có tác dụng. Sửa `core/scoping.py`, thêm test: đặt loại trừ → người phòng đó **thật sự không thấy** dữ liệu |
| **P0-T08** | BE | **Vá nhật ký thao tác** | `modules/audit/controller.py`: thêm `require("setting", "read")` (hoặc entity riêng `audit_log`) + `apply_scope`. **Bỏ trống `entity_id` không được trả nhật ký của mọi bản ghi** — bắt buộc truyền, hoặc chỉ cho phép với scope `all` |
| **P0-T09** | DB | **Nhật ký chỉ ghi thêm** | Tài khoản ứng dụng MySQL chỉ được `INSERT`, `SELECT` trên `tab_audit_log` (và sau này `tab_approval_action`). Làm ở tầng grant của MySQL, **không làm trong mã ứng dụng** |
| **P0-T10** | ∞ | **Gom nhóm đối tượng phân quyền theo phân hệ** | `core/permissions.py`: thêm `ENTITY_GROUPS = {"thumua": [...], "vanthu": [...], "nen": [...]}` + entity mới `document`, `document_request`, `doc_type`, `approval_flow`, `document_acl`. FE `hr/components/role-permission-matrix.tsx` render theo nhóm có thể thu gọn. 28 → ~40 đối tượng mà không rối |
| **P0-T11** | ∞ | **Thông báo tách theo app** | BE: `modules/notification` nhận + lọc `app`; mọi chỗ `create_notification` truyền `app`. FE: `shared/notifications/use-notifications.ts` gửi `app` theo module đang mở; chuông chỉ đếm chưa đọc của app đó. **Không tạo bảng thông báo thứ hai** |
| **P0-T12** | FE | **Tệp đính kèm đi qua link tạm** | `modules/document/components/document-attachment-list.tsx` và `procurement/components/document-attachments-card.tsx`: bỏ dùng `file.url`, gọi `/api/attachments/{id}/link` ngay lúc bấm, không prefetch (link chỉ sống 60–120s). Nút tải ẩn khi API trả `can_download = false` |
| **P0-T13** | BE | **Guard `SCOPE_FIELDS` lúc khởi động — có danh sách miễn trừ** | Quét model trong `all_models.py`: bảng có `company_id` mà entity chưa khai `SCOPE_FIELDS` thì báo. ⚠️ **Không được raise thẳng**: đối chiếu ngày 14/08/2026 có **14 model mang `company_id`** mà `SCOPE_FIELDS` chỉ khai **9** — thiếu `contract`, `department`, `goods_receipt`, `purchase_history`, `report`, `user`. Bật guard kiểu "thiếu là raise" thì **prod chết ngay lần deploy đầu**. Cách làm: hằng số `SCOPE_EXEMPT = {...}` liệt kê đúng 6 entity cũ kèm ghi chú vì sao · entity **nào không nằm trong danh sách đó mà thiếu khai thì raise** · entity cũ chỉ log cảnh báo lúc startup. Mọi entity văn thư mới **cấm** cho vào `SCOPE_EXEMPT`. Rút dần danh sách miễn trừ ở các phase sau, mỗi lần rút một entity kèm test |

## Tệp đụng tới

**Sửa:** `backend/app/core/auth.py` · `core/scoping.py` · `core/permissions.py` · `core/all_models.py` · `modules/attachment/{model,service,controller}.py` · `modules/audit/controller.py` · `modules/notification/{model,service,controller}.py` · `frontend-v2/src/shared/notifications/*` · `frontend-v2/src/modules/hr/components/role-permission-matrix.tsx` · `frontend-v2/src/modules/document/components/document-attachment-list.tsx`
**Tạo:** `backend/migrations/versions/<M1>.py` · `backend/app/modules/attachment/access_log_model.py` · `test/backend/test_approval_*.py` (5 tệp) · `test/backend/test_scope_fields_guard.py`

## Todo

- [ ] P0-T01 · 5 tệp kiểm thử luồng duyệt, tất cả xanh
- [ ] P0-T02 · Migration M1 + khai model vào `all_models.py`
- [ ] P0-T03 · Bucket R2 riêng tư, ngừng ghi `url`, tính `sha256`
- [ ] P0-T04 · Endpoint link tạm + ghi `tab_file_access_log`
- [ ] P0-T05 · Perm cache sang Redis + kênh xóa đệm
- [ ] P0-T06 · Scope phòng ban khớp bằng `department_id`
- [ ] P0-T07 · Loại trừ phòng ban có tác dụng thật
- [ ] P0-T08 · Nhật ký thao tác có quyền + theo phạm vi
- [ ] P0-T09 · Grant MySQL append-only cho bảng nhật ký
- [ ] P0-T10 · Entity mới + gom nhóm màn phân quyền
- [ ] P0-T11 · Chuông lọc theo app
- [ ] P0-T12 · FE tệp đính kèm dùng link tạm
- [ ] P0-T13 · Guard `SCOPE_FIELDS` lúc khởi động
- [ ] Deploy dev ≥1 tuần, người dùng thật xác nhận, rồi mới lên prod

## Nghiệm thu

| Bài kiểm | Kết quả phải là |
|---|---|
| Chạy 5 kiểm thử luồng duyệt Thu mua | Tất cả xanh |
| Lấy một `tab_file.url` bất kỳ trong DB, dán vào tab ẩn danh | **Không xem được** |
| Đổi tên một phòng ban | Quyền của người trong phòng **không đổi** |
| Đặt loại trừ một phòng ban | Người phòng đó **thật sự không thấy** dữ liệu |
| Đăng nhập tài khoản không quyền, gọi API nhật ký | Bị từ chối |
| Gọi API nhật ký không truyền `entity_id` | Bị từ chối (hoặc chỉ trả về trong phạm vi) |
| Thu hồi một vai trò | Mất quyền **trong vài giây**, không chờ 60s, đều trên mọi worker |
| Tải tệp qua endpoint mới | Có dòng trong `tab_file_access_log` |
| Khởi động app với một entity **mới** có `company_id` chưa khai `SCOPE_FIELDS` | App **không khởi động được** |
| Khởi động app với 6 entity cũ đang thiếu khai (`contract`, `department`, `goods_receipt`, `purchase_history`, `report`, `user`) | App **vẫn khởi động**, log 6 dòng cảnh báo |

## Rủi ro

| Rủi ro | Mức | Giảm bằng |
|---|---|---|
| Đổi đường tải tệp làm hỏng màn hình Thu mua đang dùng | Cao | P0-T04 giữ cả đường cũ sau cờ `LEGACY_FILE_URL=true`, tắt cờ sau khi FE xong P0-T12 |
| Backfill `department_id` không khớp (tên phòng đã đổi, có khoảng trắng thừa) | Trung bình | Báo cáo đối chiếu trước khi chạy; dòng nào không khớp thì để `NULL` và liệt kê ra, không đoán |
| Redis chết → không ai có quyền | Trung bình | Fallback về cache trong tiến trình khi Redis không kết nối được, log cảnh báo |
| Grant MySQL append-only chặn nhầm migration | Thấp | Migration chạy bằng tài khoản riêng, không phải tài khoản ứng dụng |

## Bảo mật

- Link tạm **vẫn sao chép được trong 60–120s** và **không chống được chụp màn hình**. Nói rõ với người dùng, đừng để hiểu nhầm là đã chống rò rỉ triệt để (`00` mục 4.6).
- Quét virus (N10) để bản 2, nhưng cột `scan_status` tạo ngay ở M1; tệp `scan_status = 0` **vẫn cho tải** ở phase này (chưa có bộ quét), siết lại khi có.
- `tab_file_access_log` sinh nhiều dòng → **lên kế hoạch dọn ngay từ đầu**: giữ chi tiết 24 tháng, cũ hơn gộp thành số liệu tổng.

## Tiếp theo

[Phase 1 · Danh mục và số hiệu](./phase-01-danh-muc-va-so-hieu.md) — chỉ bắt đầu khi 9 bài kiểm ở trên đạt và bản vá đã chạy prod ổn định.
