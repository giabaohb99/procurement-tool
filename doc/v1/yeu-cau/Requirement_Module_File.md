# Requirement — Module Quản lý File / Đính kèm

Chuẩn hóa việc đính kèm & quản lý tệp cho toàn hệ thống (báo giá, hợp đồng, chứng từ, ảnh…), thay cho cách gắn rời rạc hiện tại.

---

## 1. Mục tiêu
- Một cơ chế đính kèm **dùng chung, đa hình** (polymorphic) cho mọi module.
- **Phân quyền theo bản ghi cha** (không phải "cứ đăng nhập là tải/xóa được").
- Giới hạn **loại file & dung lượng**, cấu hình tập trung theo từng entity.
- Lưu trữ trên **Cloudflare R2**, DB chỉ giữ metadata.

## 2. Hiện trạng
- Bảng `tab_attachment`: `entity, entity_id, purchase_order_id, filename, file_key, url, content_type, size` + audit (`created_by`, `created_at`…).
- API: `GET /api/attachments?entity&entity_id` · `POST /api/attachments` (multipart) · `DELETE /api/attachments/{id}`.
- Lưu R2 (`core/storage.py`), key = `{entity}/{entity_id}/{uuid}_{filename}`; fallback thư mục `uploads/` khi chưa cấu hình R2.
- **Điểm yếu cần sửa:** upload/xóa chỉ dùng `get_current_user` (bất kỳ ai đăng nhập) — chưa gắn quyền theo module cha; chưa giới hạn loại/dung lượng file; xóa bản ghi cha chưa dọn file (orphan).

## 3. Phạm vi sử dụng (các entity đang/để đính kèm)
| entity | Nơi dùng | Quyền cha (module) |
|---|---|---|
| `purchase_request` | Yêu cầu mua — chứng từ | purchase_request |
| `purchase_request_quote` | Yêu cầu mua — báo giá | purchase_request |
| `survey` | Khảo sát — chứng từ phiếu | survey |
| `survey_line` | Khảo sát — file theo từng dòng | survey |
| `purchase_order` | Đơn mua hàng — chứng từ | purchase_order |
| `delivery` | PO — file theo lần giao | purchase_order |
| `contract` | Hợp đồng — file HĐ | contract |
| `payment_request` | Yêu cầu thanh toán — UNC… | payment_request |
| `avatar` | Ảnh đại diện user | (chính chủ) |

## 4. Cấu hình tập trung (Entity Registry)
Khai báo 1 bảng cấu hình (code, không phải DB) ánh xạ mỗi `entity` → chính sách file:

| entity | Nhãn | Quyền cha | Loại file cho phép | Dung lượng tối đa | Nhiều file? |
|---|---|---|---|---|:--:|
| purchase_request / _quote | Chứng từ / Báo giá | purchase_request | pdf, jpg, png, xlsx, docx | 20 MB | ✔ |
| survey / survey_line | Chứng từ khảo sát | survey | pdf, jpg, png, xlsx | 20 MB | ✔ |
| purchase_order / delivery | Chứng từ đơn / giao | purchase_order | pdf, jpg, png, xlsx, docx | 20 MB | ✔ |
| contract | Tệp hợp đồng | contract | pdf, jpg, png, docx | 30 MB | ✔ |
| payment_request | Chứng từ thanh toán | payment_request | pdf, jpg, png | 20 MB | ✔ |
| avatar | Ảnh đại diện | (self) | jpg, png, webp | 5 MB | ✖ (thay thế) |

> Entity không khai báo trong registry → **từ chối** upload (tránh entity rác).

## 5. Phân quyền (bắt buộc)
- **Xem/tải (list, download):** theo quyền `read` của module cha + **phạm vi dữ liệu** (không xem được file của bản ghi ngoài scope).
- **Tải lên (upload):** theo quyền `write` của module cha (avatar = chính chủ).
- **Xóa (delete):** theo quyền `write` (hoặc `delete`) của module cha.
- Kiểm tra: từ `(entity → quyền cha)` trong registry, gọi `require(parentEntity, action)`; đồng thời xác thực `entity_id` nằm trong phạm vi người dùng thấy (`apply_scope`).

## 6. Ràng buộc nghiệp vụ
- Chỉ đính kèm khi **bản ghi cha đã lưu** (có `entity_id > 0`).
- **Xóa bản ghi cha → xóa file cha** (DB + R2) để tránh orphan; hoặc dọn định kỳ.
- Tên hiển thị giữ nguyên tên gốc; key lưu có `uuid` chống trùng.
- `avatar`: upload mới thay thế cái cũ (xóa file cũ).

## 7. Giới hạn & kiểm tra khi upload
- Chặn theo **đuôi mở rộng + content-type** trong whitelist của entity.
- Chặn theo **dung lượng tối đa** của entity.
- Làm sạch tên file (bỏ ký tự nguy hiểm, giữ tiếng Việt/space an toàn).
- (Tương lai) quét mã độc trước khi công khai.

## 8. Lưu trữ (R2)
- Key: `{entity}/{entity_id}/{yyyymm}/{uuid}_{filename}` (thêm `yyyymm` để dễ quản lý).
- **Riêng tư mặc định**: chứng từ tài chính/HĐ nên dùng **URL ký tạm (presigned, hết hạn ~15 phút)** thay vì public URL. Ảnh avatar có thể public.
- DB lưu `file_key` (nguồn thật) + `url` (hiển thị); khi private, sinh presigned lúc trả API.

## 9. API (đề xuất chuẩn hóa)
| Method | Path | Quyền |
|---|---|---|
| GET | `/api/attachments?entity&entity_id` | read module cha + scope |
| POST | `/api/attachments` (multipart: entity, entity_id, files[]) | write module cha |
| DELETE | `/api/attachments/{id}` | write/delete module cha |
| GET | `/api/attachments/{id}/download` | read + scope (trả presigned/redirect) |

## 10. Audit & Nhật ký
- Ghi log `upload` / `delete` file vào `audit` gắn với `(parentEntity, entity_id)` (ai, khi nào, tên file).

## 11. Lộ trình
- **P1 (làm ngay):** Entity Registry + gắn quyền theo module cha + giới hạn loại/dung lượng + dọn file khi xóa bản ghi cha.
- **P2:** URL ký tạm cho file riêng tư + endpoint download.
- **P3:** Quét mã độc, xem trước (preview) PDF/ảnh, phiên bản (versioning).

---

### Việc triển khai P1 (nếu duyệt)
1. `core/file_registry.py`: map entity → {parent, actions, exts, max_mb, multiple}.
2. `attachment/controller.py`: thay `get_current_user` bằng kiểm tra registry + `require(parent, action)` + `apply_scope` cho `entity_id`; validate loại & dung lượng.
3. Hook xóa: khi xóa PR/PO/Survey/Contract/Payment → xóa attachment liên quan (DB + `delete_key`).
4. Cấu hình dung lượng/loại đưa vào `.env` hoặc hằng số registry.
