# duoc-CR-652 — «Hợp đồng của tôi» (nhân sự tự xem HĐLĐ của mình, chỉ đọc)

Trạng thái: đang làm. Không migration.

## Luật
- Chỉ HĐ của `user.employee_id` (0/rỗng = danh sách rỗng, không bao giờ khớp `employee_id = 0`).
- Chỉ trạng thái LƯU `SIGNED` / `TERMINATED` (Hết hạn = SIGNED + end_date qua, suy ra). Nháp / Đã hủy / xóa mềm = 404.
- Không khóa quyền mới: ngoại lệ «của chính mình» cho mọi tài khoản có hồ sơ nhân sự.

## Backend
1. `core/labor_contract_codes.py`: hằng `SELF_VIEW_STATUSES`.
2. `labor_contract/my_contract_controller.py`: `GET /api/me/labor-contracts`, `/{id}/document`, `/{id}/signed-file` (dùng lại `file_response`, `document_filename`). Lấy nhân sự CHỈ từ token.
3. `document/labor_contract_archive_access.py`: chủ HĐ ĐỌC bản lưu trữ (cùng luật trạng thái); không ghi/chia sẻ; nhật ký vẫn chỉ HR.
4. `core/logging_policy.py`: che lương cho tiền tố `/api/me/labor-contracts`.
5. `main.py`: đăng ký router.

## Frontend
- Mục «Hợp đồng lao động» (nhóm Hồ sơ) ở `/me?tab=labor-contracts`, gác `hasEmployeeProfile`; bảng chỉ đọc + 2 nút tải.
- `queryKeys.hr.myLaborContracts()`.

## Kiểm
- `test/backend/test_hdld_cua_toi_cr652.py` + vitest mục mới; typecheck, lint.
