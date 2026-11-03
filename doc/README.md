# Tài liệu dự án ERP DEGO — bản đồ

| | |
|---|---|
| Bản | 2.0 — tổ chức lại theo khuôn phân hệ (bao-CR-712, đề xuất [`de-xuat-to-chuc-lai-tai-lieu.md`](tai-lieu-ky-thuat/de-xuat-to-chuc-lai-tai-lieu.md)) |
| Ngày | 03/11/2026 |
| Người phụ trách | A1 Điều phối (chạy bài kiểm tài liệu, nhắc) |
| Trạng thái | Hiệu lực |

Cấp `doc/` chỉ giữ cái **chung**; cái **riêng** của phân hệ nào nằm trọn trong `doc/erp/<phan-he>/`. Luật viết và xếp tài
liệu: [`.claude/rules/chung-tai-lieu.md`](../.claude/rules/chung-tai-lieu.md). Kiểm: `python backend/scripts/kiem_tai_lieu.py`.

## Vào lần đầu thì đọc

| Muốn biết | Đọc |
|---|---|
| Một phân hệ làm được gì, gọi API nào, tới đâu rồi | `README.md` của phân hệ đó (bảng dưới) — mỗi phân hệ có `chuc-nang/01-yeu-cau-chuc-nang.md`, `02-yeu-cau-phi-chuc-nang.md`, `tai-lieu-ky-thuat/api.md` |
| Ai đổi gì, khi nào (+ nhật ký deploy, quyết định đã chốt) | [change-log.md](tai-lieu-ky-thuat/change-log.md) **+** [change-log-bao.md](tai-lieu-ky-thuat/change-log-bao.md) — **đọc cả hai**; mảng AI có sổ riêng [change-log-ai.md](tai-lieu-ky-thuat/change-log-ai.md); nhật ký việc [nhat-ky-task.md](tai-lieu-ky-thuat/nhat-ky-task.md) |
| Kiến trúc, từ điển dữ liệu, danh sách màn | [tai-lieu-ky-thuat/kien-truc/](tai-lieu-ky-thuat/kien-truc/README.md) |
| Phân quyền hai trục, phạm vi dữ liệu | [tai-lieu-ky-thuat/phan-quyen/thiet-ke-phan-quyen.md](tai-lieu-ky-thuat/phan-quyen/thiet-ke-phan-quyen.md) |
| Nhánh, deploy, Docker, bảo mật, rà hiệu năng | [tai-lieu-ky-thuat/van-hanh/](tai-lieu-ky-thuat/van-hanh/quy-trinh-nhanh-va-deploy.md) |
| Luật viết mã, luật tài liệu, skill và agent | [tai-lieu-ky-thuat/quy-dinh/README.md](tai-lieu-ky-thuat/quy-dinh/README.md) (khuôn tài liệu ở `quy-dinh/mau/`) |
| Kế hoạch tổng, lộ trình theo module | [plans/](plans/00-ke-hoach-theo-module.md) |

## Phân hệ (`doc/erp/`)

| Phân hệ | Thư mục | Ghi chú |
|---|---|---|
| Thu mua (YCBG, YCMH, ĐMH, công nợ, YCTT, báo cáo thu mua) | [erp/thu-mua/](erp/thu-mua/README.md) | dùng chung backend với bản V1 |
| Nhập khẩu (chi phí ba giai đoạn) | [erp/nhap-khau/](erp/nhap-khau/README.md) | |
| Kho · Mặt hàng · Nhận hàng · Xuất hàng · Lô / serial | [kho](erp/kho/README.md) · [mat-hang](erp/mat-hang/README.md) · [nhan-hang](erp/nhan-hang/README.md) · [xuat-hang](erp/xuat-hang/README.md) · [lo-serial](erp/lo-serial/README.md) | phần lớn đang ở mức nghiên cứu |
| Hải quan (tra cứu thị trường) | [erp/hai-quan/](erp/hai-quan/README.md) | |
| Sản xuất | [erp/san-xuat/](erp/san-xuat/README.md) | khảo sát hiện trạng |
| Nhân sự (HRM) | [erp/hrm/](erp/hrm/README.md) | người phụ trách HRM tự chuẩn hóa |
| Văn thư | [erp/van-thu/](erp/van-thu/README.md) | |
| Duyệt dấu · Đặt xe | [duyet-dau](erp/duyet-dau/README.md) · [dat-xe](erp/dat-xe/README.md) | đồng bộ app cũ ở `dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/` |
| Dự án và công việc | [erp/cong-viec/](erp/cong-viec/README.md) | |
| Diễn đàn · Điểm cà phê | [dien-dan](erp/dien-dan/README.md) · [diem-ca-phe](erp/diem-ca-phe/README.md) | |
| Trợ lý AI (Trợ lý web, cổng MCP, Kho skill) | [erp/tro-ly-ai/](erp/tro-ly-ai/README.md) | bộ máy bot làm ra phần mềm ở [agent-hub/](agent-hub/README.md) |
| CRM | [erp/crm/](erp/crm/README.md) | kế hoạch |
| Nền tảng dùng chung (luồng duyệt, thông báo, phiếu hỗ trợ, bình luận, nhập xuất, báo cáo, cấu hình, việc chạy ngầm) | [erp/nen-tang/](erp/nen-tang/README.md) | |

⚠️ Sửa tài liệu chức năng của một phân hệ thì xem luôn có cần cập nhật **cẩm nang Kho skill / gói tri thức Trợ lý AI**
(`backend/app/modules/ai_skill/seed_handbook/`, `backend/app/modules/assistant/packs/`) và bài HDSD (`backend/scripts/seed_help_*.py`)
không — lệch với tài liệu là trợ lý trả lời sai mà không ai biết.

## Khác

- [agent-hub/](agent-hub/README.md) — bộ máy AI làm ra phần mềm (bot nhận ticket, sửa mã, deploy); sổ CR riêng [change-log-ai.md](tai-lieu-ky-thuat/change-log-ai.md).
- [he-agent/](he-agent/) — luật vận hành hệ agent (điều phối, mức tự quyết).
- [v1/](v1/) — mọi thứ thời Mini Tool Thu Mua V1 (yêu cầu tháng 6–7, thiết kế giao diện cũ, testcase cũ, `tasks.md`, dữ liệu mẫu). V1 còn chạy ở thumua.degoholding.vn tới đợt Đ-15, **không nhận tính năng mới**.
- [tai-lieu-chuc-nang/](tai-lieu-chuc-nang/README.md) — chỉ còn phần HRM chờ dời về `erp/hrm/`.
- `../help-center/README.md` — Trung tâm Hướng dẫn sử dụng (app riêng).
