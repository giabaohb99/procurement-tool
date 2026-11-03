# NỀN TẢNG DÙNG CHUNG (NT)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · CR-170..172 (nhập / xuất) · bao-CR-312 (nhật ký và phiên đăng nhập) · bao-CR-703 (việc chạy ngầm) |

## Phân hệ này là gì

Phần dùng chung mà mọi phân hệ nghiệp vụ (Thu mua, Văn thư, Nhân sự, Đặt xe...) cùng dựa vào: luồng duyệt, chuông
thông báo, phiếu hỗ trợ, khối Trao đổi trên chứng từ, tệp đính kèm, nhập / xuất dữ liệu, báo cáo, cấu hình, việc chạy
ngầm, nhật ký và phiên đăng nhập. Không phải một màn riêng: nó hiện ở chuông trên thanh tiêu đề và Trang cá nhân `/me`,
phân hệ **Hỗ trợ** (`/tickets`), khối **Trao đổi** cuối trang chi tiết chứng từ, phân hệ **Phê duyệt** (Luồng duyệt, Bật
bộ máy duyệt), phân hệ **Báo cáo**, phân hệ **Quản trị** `/system` (Cấu hình hệ thống, Mẫu email thông báo, Sao lưu
CSDL, Hộp thư gửi, Nhật ký nghiệp vụ, Nhật ký hệ thống, Phiên đăng nhập, Sổ đồng bộ, Việc chạy ngầm, Phân quyền tài
khoản, Nhập dữ liệu, Xuất dữ liệu) và Trung tâm trợ giúp ở tên miền riêng.

## Tới đâu rồi

Chỉ ghi trạng thái khi tài liệu nguồn nói rõ; còn lại ghi *chưa ghi*.

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Chuông thông báo, Web Push, email luồng duyệt, nhật ký email (`/system/email-logs`, bao-CR-721) | chưa ghi | Mô tả ở [`10`](chuc-nang/10-thong-bao-va-trang-ca-nhan.md); bao-CR-349 công tắc email theo người |
| Phiếu hỗ trợ | Trên dev | Tài liệu [`11`](chuc-nang/11-ho-tro-ticket.md) ghi bật ở dev, tắt ở prod bằng cờ build `VITE_FEATURE_TICKET` (ghi cho bản v1) |
| Bình luận trên chứng từ | chưa ghi | [`12`](chuc-nang/12-binh-luan-tren-chung-tu.md); CR-030, CR-031, CR-033 |
| Trung tâm trợ giúp (HDSD) | Đã lên prod | `help.degoholding.vn` theo [`13`](chuc-nang/13-trung-tam-hdsd.md); CR-019, CR-052..054 |
| Nhập dữ liệu theo lô | Đang làm | Đ-13a và Đ-13d phần 1 xong; Đ-13c, Đ-13e chưa ([`16`](tai-lieu-ky-thuat/16-quan-ly-import-export-v2.md) §9; kế hoạch NT1-1, NT2-1) |
| Xuất dữ liệu tập trung | Đang làm | Lõi xong (CR-171 → CR-172), còn thêm bảng vào registry và vá ba export viết tay ([`16`](tai-lieu-ky-thuat/16-quan-ly-import-export-v2.md) §9.2) |
| Nhật ký hệ thống, phiên đăng nhập | Đã lên prod | [Kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §1; sổ bảo mật BM-002, BM-005 |
| Sao lưu CSDL lên R2, Celery | Đã lên prod | [Kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §1 |
| Bộ lọc và sắp xếp màn danh sách | Đang làm | NT2-2 xong mã, chờ rà ([`14`](tai-lieu-ky-thuat/14-filter-sort-man-danh-sach-v2.md)) |
| Luồng duyệt dùng chung, báo cáo và quyền xem từng báo cáo, việc chạy ngầm, xóa mềm | chưa ghi | Đường API đã có trong [`api.md`](tai-lieu-ky-thuat/api.md); tài liệu chưa ghi trạng thái lên môi trường |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) · nhóm `approval`, `notification`, `ticket`, `comment`, `attachment`, `import`, `export`, `report`, `setting`, `system-jobs`, `system-log`, `audit`, `auth`, `user`, `role` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [`tai-lieu-ky-thuat/`](tai-lieu-ky-thuat/) · nhật ký và phiên: [`nhat-ky-va-phien-dang-nhap.md`](../../tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md) · luồng duyệt: [Văn thư nhóm I](../van-thu/chuc-nang/12-danh-sach-tinh-nang.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | [`nghien-cuu/`](nghien-cuu/) · câu chờ quyết ở [kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §1 |
| Kế hoạch đang làm / đã xong | chưa có thư mục `plans/`; việc còn lại ở [kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §1 (NT1-x, NT2-x, NT3-x) |
| Kịch bản kiểm thử tay | chưa có |
| Hướng dẫn người dùng | Trung tâm trợ giúp, bài hệ thống ([`seed_help_he_thong_cap_nhat.py`](../../../backend/scripts/seed_help_he_thong_cap_nhat.py)) và bài bước duyệt theo phân quyền ([`seed_help_phe_duyet_theo_quyen.py`](../../../backend/scripts/seed_help_phe_duyet_theo_quyen.py)) |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng CN-NT-NN, tóm tắt và liên kết tới tài liệu chi tiết | Nháp |
| [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-NT-01..12 | Nháp |
| [`chuc-nang/10-thong-bao-va-trang-ca-nhan.md`](chuc-nang/10-thong-bao-va-trang-ca-nhan.md) | Chuông thông báo, `/notifications`, Web Push, email luồng duyệt, khối tài khoản, Trang cá nhân `/me`, PWA | chưa ghi |
| [`chuc-nang/11-ho-tro-ticket.md`](chuc-nang/11-ho-tro-ticket.md) | Phiếu hỗ trợ: vai trò, ba màn, trạng thái, thông báo, API, phân quyền | chưa ghi |
| [`chuc-nang/12-binh-luan-tren-chung-tu.md`](chuc-nang/12-binh-luan-tren-chung-tu.md) | Khối Trao đổi trên chứng từ: trả lời hai cấp, nhắc `@`, thích, đính kèm, quyền xem / xóa | chưa ghi |
| [`chuc-nang/13-trung-tam-hdsd.md`](chuc-nang/13-trung-tam-hdsd.md) | Trung tâm trợ giúp: hai khu, vai trò, cây bài, FAQ, nhập bài, lọc HTML, mang nội dung giữa môi trường | chưa ghi (cập nhật 11/08/2026) |
| [`nghien-cuu/erpnext-02-bai-tap-vai-tro-luong-duyet-va-bat-tat.md`](nghien-cuu/erpnext-02-bai-tap-vai-tro-luong-duyet-va-bat-tat.md) | Bài tập ERPNext: tài khoản theo vai, luồng duyệt đơn mua, tồn tối thiểu, kiểm chất lượng | chưa ghi |
| [`tai-lieu-ky-thuat/07-kien-truc-vo-erp.md`](tai-lieu-ky-thuat/07-kien-truc-vo-erp.md) | Kiến trúc vỏ ERP bọc Thu mua thành phân hệ | chưa ghi (bản 1.0, 12/08/2026) |
| [`tai-lieu-ky-thuat/14-filter-sort-man-danh-sach-v2.md`](tai-lieu-ky-thuat/14-filter-sort-man-danh-sach-v2.md) | Thiết kế bộ lọc và sắp xếp màn danh sách Thu mua, Sản xuất | Bản thiết kế (chờ duyệt) |
| [`tai-lieu-ky-thuat/15-do-be-tong-nen-v2.md`](tai-lieu-ky-thuat/15-do-be-tong-nen-v2.md) | Đổ bê tông nền ERP v2: chín đợt B-01..B-09, QĐ-9, QĐ-10, QĐ-12 | chưa ghi (bản 1.1, 22/08/2026) |
| [`tai-lieu-ky-thuat/16-quan-ly-import-export-v2.md`](tai-lieu-ky-thuat/16-quan-ly-import-export-v2.md) | Quản lý nhập / xuất ở `/system`: quyết định, danh mục được nhập, đợt Đ-13a..e | chưa ghi (bản 1.0, 25/08/2026) |
| [`tai-lieu-ky-thuat/20-ra-soat-xoa-cung.md`](tai-lieu-ky-thuat/20-ra-soat-xoa-cung.md) | Rà soát xóa cứng, chuyển sang xóa mềm theo đợt | chưa ghi |
| [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) | Bảng đường API nền tảng (dựng tự động từ mã) | Nháp |
| [`tai-lieu-ky-thuat/thiet-ke-luu-va-trang-thai-dong.md`](tai-lieu-ky-thuat/thiet-ke-luu-va-trang-thai-dong.md) | Quyết định nút Lưu hay tự lưu; trạng thái dòng YCKS, YCMH, ĐMH | chưa ghi |
| [`plans/261019-1450-tracking-ho-so-lam-viec-cr641/`](plans/261019-1450-tracking-ho-so-lam-viec-cr641/plan.md) | duoc-CR-641 — Hồ sơ cách làm việc (pha 1, 2, 3 của duoc-CR-626) (dời từ `plans/` gốc, bao-CR-712) | chưa ghi |
| [`plans/261020-1600-d0-d1-ghi-nhan-thao-tac-nang-luc/`](plans/261020-1600-d0-d1-ghi-nhan-thao-tac-nang-luc/plan.md) | D0 + D1 — ghi nhận thao tác & năng lực theo loại việc (dời từ `plans/` gốc, bao-CR-712) | chưa ghi |
| [`plans/261002-0836-phan-quyen-tung-bao-cao/`](plans/261002-0836-phan-quyen-tung-bao-cao/plan.md) | Phân quyền xem từng báo cáo (dời từ `plans/` gốc, bao-CR-712) | chưa ghi |
| [`plans/reports/`](plans/reports/) | Báo cáo của agent khi làm kế hoạch (dời từ `plans/` gốc, bao-CR-712) | chưa ghi |

## Mã nguồn

- Backend: `backend/app/modules/` các module `approval`, `notification`, `push`, `comment`, `ticket`, `attachment`,
  `import_tool`, `export_log`, `report`, `report_access`, `dashboard`, `alert`, `setting`, `job_run`, `system_log`,
  `request_log`, `audit`, `change_log`, `login_session`, `auth`, `user`, `role`, `company`, `department`, `sync_log`,
  `backup`, `help_center`, `faq`, `meta`, `user_preference`, `feature_usage`, `usage_profile`, `capability`; lõi dùng
  chung ở `backend/app/core/` (`scoping.py`, `permissions.py`, `file_registry.py`, `celery_app.py`).
- Giao diện v2: `frontend-v2/src/modules/system/`, `approval/`, `support/`, `report/`, `help/`.
- Trung tâm trợ giúp: [`help-center/README.md`](../../../help-center/README.md).
- Luật cho người viết mã: [`backend-input-limits.md`](../../../.claude/rules/backend-input-limits.md), phân quyền hai
  trục ở [`CLAUDE.md`](../../../CLAUDE.md).
