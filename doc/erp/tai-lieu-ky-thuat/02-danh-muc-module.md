# DANH MỤC MODULE — BACKEND VÀ FRONTEND-V2

Bản 1.0 — 28/08/2026. Đếm tại chỗ: **46 module backend** (`backend/app/modules/`),
**20 phân hệ frontend-v2** (`frontend-v2/src/modules/`). Mỗi cái một dòng để tra nhanh
"cái này nằm đâu, thuộc cụm nào" — mô tả sâu thì đọc mã nguồn của chính module đó.

## 1. Backend — 46 module, gom theo cụm

### Cụm Thu mua lõi (từ v1, đang chạy prod)

| Module | Vai trò |
|---|---|
| `survey_request` | Yêu cầu báo giá (YCBG) + phương án khảo sát |
| `survey`, `survey_progress` | Phiếu khảo sát NCC/SP + tiến độ khảo sát |
| `purchase_request` | Yêu cầu mua hàng (YCMH) |
| `purchase_order`, `purchase_progress` | Đơn mua hàng (ĐMH) + tiến độ nhận hàng |
| `goods_receipt` | Nhận hàng |
| `payable`, `payment_request` | Công nợ + Yêu cầu thanh toán (YCTT) |
| `purchase_history` | Lịch sử mua hàng theo mã sản phẩm |
| `supplier`, `contract` | Nhà cung cấp + hợp đồng NCC |
| `product`, `catalog`, `category_assignee` | Sản phẩm/vật tư (bảng SKU), danh mục ĐVT/phân loại, phân công phụ trách phân loại |
| `inventory` | Tồn kho + luân chuyển kho + danh mục kho |
| `report`, `dashboard` | Báo cáo mua hàng/khảo sát + tổng quan trang chủ |

### Cụm tổ chức và tài khoản

| Module | Vai trò |
|---|---|
| `auth`, `user`, `role` | Đăng nhập JWT, tài khoản, vai trò + ma trận quyền |
| `employee`, `department`, `company` | Nhân sự, phòng ban, pháp nhân (cây cha–con) |
| `user_preference` | Tùy chọn hiển thị của từng người (bảng màu, chế độ nền) |

### Cụm Văn thư và phê duyệt (mới ở v2)

| Module | Vai trò |
|---|---|
| `document` | Văn bản: soạn → gửi duyệt → ký → ban hành; phiên bản; clone xuống pháp nhân con |
| `doc_catalog` | Danh mục văn thư: loại văn bản, sổ, cấp bảo mật, đơn vị gửi nhận, mẫu |
| `approval` | Bộ máy duyệt dùng chung: luồng, bước, cách chọn người duyệt |
| `seal_request` | Trình duyệt dấu (phân hệ FE chưa bật) |

### Cụm cộng tác và hỗ trợ

| Module | Vai trò |
|---|---|
| `forum` | Diễn đàn nội bộ: bài, bình luận, like, mention, đối tượng xem |
| `comment` | Bình luận trên chứng từ (CR-033), diễn đàn dùng lại |
| `ticket` | Phiếu hỗ trợ (khách báo lỗi/yêu cầu) |
| `help_center`, `faq` | Nội dung Trung tâm HDSD (app FE riêng cổng 8082) |
| `assistant` | Trợ lý AI: hội thoại + ~29 tool nghiệp vụ đọc dữ liệu theo quyền người hỏi |
| `notification`, `alert`, `push` | Thông báo chuông + email (mailbox danh nghĩa CR-184), nhắc hạn, Web Push |

### Cụm hạ tầng vận hành

| Module | Vai trò |
|---|---|
| `attachment` | File đính kèm (R2) + thumbnail (CR-193); chính sách ô đính kèm ở `core/file_registry.py` |
| `audit` | Nhật ký thao tác trên chứng từ |
| `import_tool`, `export_log` | Nhập liệu batch (thử → ghi thật → hoàn tác) + nhật ký xuất dữ liệu |
| `setting` | Cấu hình hệ thống (SMTP, công tắc email...) — màn `/system/settings` |
| `backup` | Backup DB lên R2 qua Celery beat |
| `meta` | Endpoint meta/enum dùng chung cho FE |
| `vehicle_booking` | Đặt xe (backend có, phân hệ FE chưa bật) |
| `meeting_room` | Đặt phòng họp: danh mục phòng + phiếu đặt chạy qua bộ máy duyệt, chặn trùng khung giờ (nằm trong phân hệ FE Nhân sự) |

## 2. Frontend-v2 — 20 phân hệ

Trạng thái lấy từ `module-registry.ts` + cờ `enabled`; "Sắp có" = có thẻ mờ, không có route.

| Phân hệ (id) | Thẻ trên màn chọn | Trạng thái | Ghi chú |
|---|---|---|---|
| `hr` | Nhân sự | Đang chạy | Nhân sự, phòng ban, công ty, vai trò + phân quyền |
| `procurement` | Thu mua | Đang chạy | YCBG, YCMH, ĐMH, khảo sát, tiến độ, báo cáo, phân công |
| `production` | Sản xuất | Đang chạy | Danh mục: NCC (kèm 5 tab), sản phẩm, ĐVT, phân loại, hợp đồng |
| `inventory` | Kho | Đang chạy | Tồn kho, danh mục kho |
| `finance` | Tài chính | Đang chạy | Công nợ, Yêu cầu thanh toán (QĐ-5) |
| `document` | Văn bản | Đang chạy | Văn thư đầy đủ + «Chờ tôi duyệt» mở cho người duyệt ngoài phân hệ |
| `approval` | Phê duyệt | Đang chạy | Khai luồng duyệt dùng chung |
| `forum` | Diễn đàn | Đang chạy | Khung riêng (`customLayout`), kiểu bảng tin |
| `support` | Hỗ trợ | Đang chạy | Phiếu hỗ trợ |
| `assistant` | Trợ lý AI | Đang chạy | Trang hội thoại + bong bóng chat nổi mọi trang |
| `system` | Quản trị | Đang chạy | Cấu hình, hộp thư gửi, nhập/xuất dữ liệu |
| `appearance` | Giao diện | Đang chạy | Tùy chọn của chính người đăng nhập — mở công khai |
| `help` | Hướng dẫn sử dụng | Đang chạy | `externalUrl` → app Help Center, mở tab mới |
| `sales` | Bán hàng | Sắp có | |
| `customer` | Khách hàng | Sắp có | |
| `project` | Dự án | Sắp có | Công cụ QLDA hiện là app Project-M riêng (`PM/`) |
| `approval-seal` | Duyệt dấu | Sắp có | Backend `seal_request` đã có |
| `vehicle-booking` | Đặt xe | Sắp có | Backend `vehicle_booking` đã có |
| `dego-coffee` | Dego Coffee | Sắp có | Phúc lợi điểm + POS, xem `doc/erp/09` |
| `report` | Báo cáo | Sắp có | Báo cáo hiện nằm trong từng phân hệ |

## 3. Cách giữ tài liệu này đúng

Thêm module backend hay phân hệ FE mới thì thêm **một dòng** vào đúng bảng trên, cùng đợt với dòng CR
ở change-log. Tài liệu này cố ý không ghi số bảng, số route, số test — mấy con số đó đổi hằng tuần
và đã có nguồn khác (mã nguồn, change-log) nói chính xác hơn.
