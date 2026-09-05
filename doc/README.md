# Tài liệu dự án — Mini Tool Thu Mua

Đã gom nhóm cho dễ quản lý. **Vào lần đầu thì đọc 3 file này trước:**

| Muốn biết | Đọc |
|---|---|
| Hệ thống làm được gì, màn nào chạy ra sao | [tai-lieu-chuc-nang/00-muc-luc.md](tai-lieu-chuc-nang/00-muc-luc.md) |
| Ai đổi gì, khi nào, ảnh hưởng ra sao (+ nhật ký deploy, quyết định đã chốt) | [tai-lieu-ky-thuat/change-log.md](tai-lieu-ky-thuat/change-log.md) |
| Xây bằng cách nào (kiến trúc, DB, API, phân quyền) | [tai-lieu-ky-thuat/technical-design.md](tai-lieu-ky-thuat/technical-design.md) |

## tai-lieu-chuc-nang/ — Tài liệu chức năng (nghiệp vụ, cho người dùng & BA)
- `00-muc-luc.md` — mục lục; `01`…`17` theo từng phân hệ (Phiếu khảo sát, YCBG, YCMH, ĐMH, YCTT, Tồn kho & Công nợ, Danh mục, Báo cáo, Thông báo & Trang cá nhân, Phiếu hỗ trợ, Bình luận, Lịch sử mua hàng, Trung tâm HDSD, Văn thư, **Dự án — quản lý công việc**, **Nghỉ phép**)
- ⚠️ Sửa tài liệu chức năng của một phân hệ thì xem luôn có cần cập nhật **gói tri thức Trợ lý AI** không: `backend/app/modules/assistant/packs/` — gói đó nạp thẳng vào system prompt mỗi lượt hỏi, lệch với tài liệu là trợ lý trả lời sai mà không ai biết.

## tai-lieu-ky-thuat/ — Tài liệu kỹ thuật
- `change-log.md` — **sổ CR** (mỗi thay đổi 1 dòng) + việc còn nợ + quyết định đã chốt (D-xxx) + **nhật ký deploy**
- `technical-design.md`, `thiet-ke-ky-thuat-chi-tiet.md`, `so-do-ky-thuat.md` — TDD
- `mo-hinh-du-lieu-san-pham.md` — **đọc trước khi đụng vào cấu trúc Sản phẩm**: vì sao `tab_product` là bảng variant, thuộc tính động, tầng họ sản phẩm, hợp đồng "chọn mã VTBB → tự động điền", và danh sách việc CẤM làm
- `quy-trinh-tai-lieu.md` — quy trình tài liệu & kiểm soát thay đổi (tài liệu nào ra đời khi nào)

## yeu-cau/ — Yêu cầu nghiệp vụ
- `Requirement_Mini_Tool_Thu_Mua.md` — tổng quan hệ thống
- `Requirement_Features_Detail.md` — chi tiết tính năng
- `Requirement_KhaoSat_NCC_SP.md` — khảo sát NCC / sản phẩm
- `Requirement_YeuCauMua_ChiTiet.md` — chi tiết Yêu cầu mua (form item, luồng, VAT/thời gian theo dòng)
- `Requirement_PO_Detail.md`, `Requirement_PO_GR_CongNo.md` — đơn mua / nhận / công nợ
- `Requirement_BaoCao_MuaHang.md` — báo cáo
- `Requirement_Email_Approval.md`, `Requirement_Phase34_UX.md` — email/UX
- `Mapping_Sheet06_TienDoMuaHang.md` — map cột Sheet 6

## thiet-ke/ — Thiết kế giao diện
- `Thiet_Ke_Giao_Dien.md` — hệ thiết kế + dashboard (Horizon, màu logo)
- `Dashboard_Spec_UXUI.md` — bản mô tả dashboard cho UX/UI
- `AI_Gen_Prompt.md` — prompt gen UI bằng AI

## phan-quyen/ — Phân quyền
- `Thiet_Ke_Phan_Quyen.md` — thiết kế RBAC + phạm vi (grant)
- `Requirement_VaiTro.md` — vai trò
- `Plan_PhanQuyen_PYC.md` — plan phân quyền Yêu cầu mua
- `Plan_Dashboard_Menu_Quyen.md` — quyền → menu → dashboard
- `Test_PhanQuyen_PYC.md` — kịch bản test + tài khoản mẫu

## chung/ — Tham chiếu dev & vận hành
- `Deploy_VPS.md` — runbook deploy prod/dev trên VPS (kèm cách nạp nội dung Trung tâm Hướng dẫn)
- `Go_Live_Checklist.md` — checklist trước khi chạy thật
- `CHANGELOG.md` — nhật ký theo ngày (bản ngắn, đọc nhanh)
- `FEATURE_CHECKLIST.md`, `NAMING_CONVENTIONS.md`, `Plan_Celery_Worker.md`

## Khác
- `testcase/` — kịch bản test tay; `ke-hoach-import/`, `ke-hoach-celery/`, `dat-xe-duyet-dau/` — kế hoạch từng mảng
  - `dat-xe-duyet-dau/` — **Phân hệ Đặt xe nội bộ** (kế hoạch + tiến độ theo phase). Xem `README.md` + `TIEN-DO.md`.
- `datamau/`, `sheet/` — dữ liệu mẫu / bảng gốc
- `../TASKS.md` — tiến độ triển khai
- `../help-center/README.md` — Trung tâm Hướng dẫn sử dụng (app riêng)
