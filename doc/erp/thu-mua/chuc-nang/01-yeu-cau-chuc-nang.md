# YÊU CẦU CHỨC NĂNG — THU MUA

| | |
|---|---|
| Bản | 0.2 |
| Ngày | 05/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712, td-0311 · CR chính trong tài liệu cũ: CR-034, CR-068, CR-108, CR-268, bao-CR-310, bao-CR-388, bao-CR-414, bao-CR-422 |

Tệp này là **mục lục chức năng**: mỗi chức năng một dòng tóm tắt và liên kết tới tài liệu chi tiết đã có ở
`chuc-nang/10..20`. Chi tiết từng trường, từng nút vẫn nằm ở tài liệu gốc (luật *một sự thật một chỗ*); sửa nghiệp vụ thì
sửa tài liệu gốc trước, rồi chỉnh dòng tóm tắt ở đây nếu nghĩa đổi.

**Cách đọc cột Trạng thái.** Tài liệu cũ không ghi rõ chức năng nào đã lên prod, nên phần lớn ghi *chưa ghi*. Chữ
*có mã* nghĩa là bảng fit-gap [nghien-cuu/11](../nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md) (soát nhánh
`erp-v2` ngày 30/10/2026) xác nhận đã có mã; nó không nói đã lên prod hay chưa.

**Rà 05/11/2026 (td-0311):** từ đợt phát hành 2.14.0 ngày 05/11/2026 nhánh `main` (prod) trùng `erp-v2` (`dae5957b`), và mọi màn, đường API trong bảng mục 2 đều có trong mã (`frontend-v2/src/shared/constants/app-routes.ts`, bảng [api.md](../tai-lieu-ky-thuat/api.md)). Vì vậy cột Trạng thái ghi *có trên prod 05/11*; phần *có mã (doc 11 …)* giữ lại để tra bảng fit-gap.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Người yêu cầu (`employee`, tên trong seed: *Nhân sự*) | Lập YCBG, YCMH của mình, gửi duyệt, chọn phương án, chuyển Hoàn thành YCBG ([11 mục Vai trò](11-yeu-cau-khao-sat.md), [12 mục Vai trò](12-yeu-cau-mua-hang.md)) |
| Trưởng bộ phận (`dept_head`) | Duyệt, trả về, từ chối YCBG, YCMH chặng 1 của phòng mình; không điều phối (CR-034) |
| Quản lý thu mua (`pur_admin`; tài liệu chi phí thu mua ghi thêm `pur_manager`, `pur_dept_manager`) | Duyệt lần 2 (điều phối) YCMH, trả về, từ chối, hoàn thành; ghi nhận đã chi YCTT; mở lại giai đoạn chi phí |
| Nhân sự thu mua — NSTM (phạm vi `proc`, `dept_proc`) | Xử lý YCBG (quyền `process`), gắn phương án, cập nhật dòng YCMH, lập ĐMH, ghi lần giao |
| Người duyệt ĐMH, YCTT (quyền `approve`) | Duyệt, trả về, từ chối, hủy duyệt ĐMH; duyệt YCTT |
| Kế toán (không có vai trò chuẩn trong `seed.py`; từng hệ tự tạo vai trò và tick quyền) | Nhận bộ chứng từ ĐMH, xác nhận thanh toán theo dòng ([13 mục B.8c, B.23](13-don-mua-hang.md)) |
| Admin | Toàn quyền; bật tắt công tắc điều phối `pr_dispatch_enabled` |

## 2. Danh sách chức năng

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-TM-01 | Yêu cầu báo giá (YCBG): lập, duyệt, NSTM xử lý, phương án ẩn danh NCC, sinh YCMH gom theo NCC — [11](11-yeu-cau-khao-sat.md) | Người yêu cầu, TBP, NSTM | `/procurement/survey-requests`, `.../:id/process` | có trên prod 05/11 · có mã (doc 11 C1, C2) | CR-018, CR-026, CR-075 |
| CN-TM-02 | Tiến độ báo giá theo dòng YCBG — [11 mục H](11-yeu-cau-khao-sat.md) | NSTM, quản lý | `/procurement/survey-progress` | có trên prod 05/11 | CR-075 |
| CN-TM-03 | Phiếu khảo sát NCC và sản phẩm, duyệt từng dòng — [10](10-phieu-khao-sat.md) | NSPT, TP/QL | `/procurement/surveys` | có trên prod 05/11 · có mã (doc 11 C3) | CR-111 |
| CN-TM-04 | Báo cáo thực hiện: chuỗi việc sau duyệt (giai đoạn, hồ sơ, người phụ trách) trên YCBG, mở rộng sang ĐMH — [19](19-bao-cao-thuc-hien-ycbg.md), [brief](../nghien-cuu/01-brief-bao-cao-thuc-hien-ycbg.md) | NSTM, người yêu cầu | Thẻ trên chi tiết YCBG và ĐMH | Có (trên YCBG, theo brief: dev + prod từ 12/09/2026); phần ĐMH (bao-CR-602) có trên prod 05/11 | bao-CR-388..393, bao-CR-602 |
| CN-TM-05 | Yêu cầu mua hàng (YCMH): lập, duyệt chặng 1, điều phối chặng 2 tự phân NSTM, theo dõi trạng thái dòng — [12](12-yeu-cau-mua-hang.md) | Người yêu cầu, TBP, QL thu mua, NSTM | `/procurement/purchase-requests` | có trên prod 05/11 · có mã (doc 11 B1, B4) | CR-034, CR-034a |
| CN-TM-06 | Phương án trên dòng YCMH (kể cả *Phương án 0*), chốt chọn, sinh đơn nháp theo NCC — [12 mục H](12-yeu-cau-mua-hang.md) | NSTM, người yêu cầu | `/procurement/purchase-requests/:id/process` | Dev (tài liệu ghi deploy dev 15/09/2026) | bao-CR-310, bao-CR-419, bao-CR-420, bao-CR-421 |
| CN-TM-07 | Bản in phiếu đề xuất YCMH, bản in theo NCC, khối xét duyệt tự điền chữ ký — [12 mục F, H.6](12-yeu-cau-mua-hang.md) | Người yêu cầu, NSTM | `/print/purchase-request/:id`, `/print/purchase-request-suppliers/:id` | có trên prod 05/11 | CR-036, bao-CR-397, bao-CR-420 |
| CN-TM-08 | Chứng từ liên quan trên YCMH — [12 mục I](12-yeu-cau-mua-hang.md), [kiểm thử 01](../kiem-thu/01-chung-tu-lien-quan-ycmh.md) | Mọi người xem phiếu | Thẻ trên chi tiết YCMH | Dev (theo [mục lục kiểm thử](../kiem-thu/00-muc-luc.md), dev 19/09/2026) | bao-CR-422 |
| CN-TM-09 | Đơn mua hàng (ĐMH): lập từ phương án, duyệt, khóa sau duyệt, hủy duyệt, hủy đơn, nhân bản, mở lại — [13 mục A, B, F, G](13-don-mua-hang.md) | NSPT, NSTM, người duyệt | `/procurement/purchase-orders` | có trên prod 05/11 · có mã (doc 11 D1–D3) | CR-095, CR-108 |
| CN-TM-10 | Lần giao và nhận hàng trên dòng ĐMH; lưu đơn tự sinh phiếu nhập ngầm, dòng sổ kho, công nợ — [13 mục C](13-don-mua-hang.md) | NSTM | Popup chi tiết dòng ĐMH | có trên prod 05/11 · có mã (doc 11 E1 một phần, E2) | bao-CR-319 |
| CN-TM-11 | Tiến độ dòng ĐMH tự nâng bước, liên kết ngược về YCMH; màn Tiến độ đơn mua hàng — [13 mục H](13-don-mua-hang.md) | NSTM, quản lý | `/procurement/purchase-progress` | có trên prod 05/11 | bao-CR-691 |
| CN-TM-12 | Bản in ĐMH (hai mẫu A4, mẫu nhập khẩu) và chứng từ đính kèm — [13 mục D, E](13-don-mua-hang.md) | NSTM, kế toán | `/print/purchase-order/:id`, `/print/purchase-order-mh/:id` | có trên prod 05/11 | bao-CR-321, bao-CR-322 |
| CN-TM-13 | Công nợ phải trả: tự sinh theo ba luồng (hàng, cước, chi phí lô nhập khẩu), tuổi nợ, thẻ tổng — [15 phần Công nợ](15-ton-kho-cong-no.md) | Thu mua, kế toán | `/finance/payables` | có trên prod 05/11 · có mã (doc 11 G2) | bao-CR-275, bao-CR-319 |
| CN-TM-14 | Yêu cầu thanh toán: gom nhiều khoản nợ một NCC, duyệt, ghi nhận đã chi, in mẫu 002/BM/PKT — [14](14-yeu-cau-thanh-toan.md) | Người lập, người duyệt, QL thu mua | `/finance/payment-requests` | có trên prod 05/11 · có mã (doc 11 G3) | CR-035, CR-066 |
| CN-TM-15 | Thanh toán trước và tiền treo, cấn trừ vào nợ hàng về sau — [14 mục F](14-yeu-cau-thanh-toan.md) | QL thu mua | Màn YCTT, Công nợ | có trên prod 05/11 · có mã (doc 11 G4) | CR-268 |
| CN-TM-16 | Danh mục nhà cung cấp, thẻ *Công nợ và Đánh giá* trên chi tiết NCC — [16 mục Nhà cung cấp](16-danh-muc.md), [15 mục H](15-ton-kho-cong-no.md) | Thu mua | `/production/suppliers` | có trên prod 05/11 · có mã (doc 11 A4) | bao-CR-321 |
| CN-TM-17 | Danh mục hợp đồng theo đối tác, pháp nhân ký, hạn hiệu lực — [16 mục Hợp đồng](16-danh-muc.md) | Thu mua | `/production/contracts` | có trên prod 05/11 · có mã một phần (doc 11 A7) | CR-118 |
| CN-TM-18 | Phân công NSTM chính, dự phòng theo phân loại (và theo phòng tự mua) — [16 mục Phân công phụ trách](16-danh-muc.md) | QL thu mua | `/procurement/category-assignees` | có trên prod 05/11 | bao-CR-414 |
| CN-TM-19 | Lịch sử mua hàng theo mã hàng và NCC, popup lấy giá khi lập đơn, che NCC với người không có quyền — [18](18-lich-su-mua-hang.md) | NSTM, người lập phiếu | Tab trên chi tiết SP, NCC; ô Mã hàng | có trên prod 05/11 · có mã (doc 11 H3) | CR-060 |
| CN-TM-20 | Báo cáo mua hàng (nhiều tab) và màn Chi tiết YC mua hàng — [17 mục Báo cáo mua hàng](17-he-thong-bao-cao.md) | Quản lý | `/procurement/purchase-report`, `/procurement/pr-lines-report` | có trên prod 05/11 · có mã (doc 11 H1) | bao-CR-347, bao-CR-691 |
| CN-TM-21 | Báo cáo khảo sát — [17 mục Báo cáo khảo sát](17-he-thong-bao-cao.md) | Quản lý | `/procurement/survey-report` | có trên prod 05/11 | không tìm thấy mã CR (có từ bản dựng đầu) |
| CN-TM-22 | Xuất Excel danh sách YCBG, YCMH, ĐMH, Tiến độ — [11 mục G](11-yeu-cau-khao-sat.md), [12 mục G](12-yeu-cau-mua-hang.md), [13 mục J](13-don-mua-hang.md) | Mọi người có quyền `export` | Nút Xuất trên danh sách | có trên prod 05/11 | CR-068 |
| CN-TM-23 | Phòng tự mua hàng: bậc phạm vi `dept_proc`, bộ tài khoản riêng, công ty con thu hẹp — [20](20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md) | Admin | Phân quyền tài khoản | có trên prod 05/11 | bao-CR-414, bao-CR-480 |
| CN-TM-24 | Danh mục và quản trị dùng chung đang được mô tả trong tài liệu thu mua: phòng ban, công ty ([16](16-danh-muc.md)); nhân sự, tài khoản, vai trò, cấu hình hệ thống ([17](17-he-thong-bao-cao.md)) | Admin | Nhiều màn | có trên prod 05/11 | CR-022, CR-023, CR-037 |

Danh mục sản phẩm, ĐVT, phân loại, thương hiệu thuộc phân hệ [Mặt hàng](../../mat-hang/chuc-nang/01-yeu-cau-chuc-nang.md);
màn Tồn kho và danh mục Kho thuộc phân hệ [Kho](../../kho/chuc-nang/01-yeu-cau-chuc-nang.md); đơn nhập khẩu và chi phí thu
mua thuộc phân hệ [Nhập khẩu](../../nhap-khau/chuc-nang/01-yeu-cau-chuc-nang.md). Tài liệu gốc của các phần đó vẫn nằm ở
`16`, `15`, `13 mục K` cho tới khi được dời.

## 3. Chi tiết từng chức năng

### CN-TM-01 — Yêu cầu báo giá (YCBG)

- **Mục đích:** ghi nhu cầu hỏi giá của bộ phận nghiệp vụ, chuyển NSTM khảo sát, để người yêu cầu chọn phương án mà không thấy tên NCC.
- **Luồng chính:** lập phiếu nhiều dòng → gửi duyệt → TBP duyệt (tự sang *Đang xử lý*, gán NSTM theo phân loại) → NSTM gắn phương án ở màn Xử lý → chốt *Đã khảo sát* → người yêu cầu chọn phương án, bấm tạo YCMH (gom theo NCC) → Hoàn thành.
- **Luật nghiệp vụ:** phiếu chỉ sang *Đã khảo sát* khi mọi dòng của mọi NSTM đã có phương án hoặc được chốt rỗng; YCBG tự sang *Hoàn thành* khi mọi YCMH sinh ra đã hoàn thành. Chi tiết ở [11 mục Vòng đời, mục E](11-yeu-cau-khao-sat.md).
- **Dữ liệu:** đầu phiếu (công ty nhận hóa đơn, người yêu cầu, bộ phận, TBP, mục đích); dòng (phân loại, thông số, số lượng, ĐVT, giá đề xuất, ảnh); phương án là bản chụp từ phiếu khảo sát. Danh sách trường ở [11 mục A, B, C](11-yeu-cau-khao-sat.md).
- **Quyền:** entity `survey_request` (`create`, `write`, `approve`, `process`, `export`, `delete`); phạm vi theo `SCOPE_FIELDS` (công ty, phòng, phòng xử lý, người tạo). Bảng quyền ở [11 mục F](11-yeu-cau-khao-sat.md).
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi câu báo lỗi cụ thể trong tài liệu cũ.
- **Liên quan:** CN-TM-03 (phiếu khảo sát làm nguồn phương án), CN-TM-05 (YCMH được sinh), CN-TM-04; công cụ AI `draft_survey_request`.

### CN-TM-05 — Yêu cầu mua hàng (YCMH)

- **Mục đích:** ghi nhu cầu mua vật tư, hàng hóa, dịch vụ của các phòng và theo dõi từng dòng tới khi có hàng.
- **Luồng chính:** lập → gửi duyệt → TBP duyệt (*Đã duyệt*, chưa có NSTM) → quản lý thu mua duyệt lần 2 (*Đã điều phối*, tự phân NSTM theo phân loại) → NSTM xử lý dòng, lập ĐMH → *Đang xử lý* → *Hoàn thành* khi mọi dòng xong hoặc hủy.
- **Luật nghiệp vụ:** chỉ *Nháp* và *Bị trả lại* sửa được nội dung; trả về thì xóa NSTM và đặt lại trạng thái dòng; công tắc `pr_dispatch_enabled` tắt thì bỏ chặng 2; máy chủ chặn tạo ĐMH từ YCMH chưa điều phối (`_ensure_pr_dispatched`). Chi tiết ở [12 mục Vòng đời, mục C](12-yeu-cau-mua-hang.md).
- **Dữ liệu:** đầu phiếu (mã, công ty, người yêu cầu, TBP, đơn gấp, mục đích, NCC đề xuất hai cụm, báo giá đính kèm, VAT); dòng (mã hàng, số lượng, ĐVT, giá, kho nhận, ngày cần hàng, trạng thái dòng). Danh sách ở [12 mục A, B](12-yeu-cau-mua-hang.md).
- **Quyền:** entity `purchase_request` (`create`, `write`, `approve`, `cancel`, `export`, `delete`); duyệt chặng 1 phạm vi `dept`, điều phối phạm vi `proc` hoặc `all`. Bảng ở [12 mục D](12-yeu-cau-mua-hang.md).
- **Ngoại lệ / lỗi người dùng gặp:** tạo ĐMH từ YCMH chưa điều phối báo *"YCMH … chưa được điều phối (chưa có nhân sự phụ trách)"*; từ YCMH bị từ chối báo *"đã bị từ chối"*; gọi điều phối khi công tắc tắt trả lỗi 400.
- **Liên quan:** CN-TM-06, CN-TM-07, CN-TM-08, CN-TM-09; công cụ AI `draft_purchase_request`, `my_procurement_requests`, `pending_procurement_approvals`.

### CN-TM-09 — Đơn mua hàng (ĐMH)

- **Mục đích:** ghi quyết định mua chính thức với một NCC: dòng hàng, số lượng, đơn giá, lịch giao nhiều lần.
- **Luồng chính:** lập (từ phương án đã chọn hoặc tay) → gửi duyệt → duyệt → giao nhận nhiều lần (*Đã nhận một phần*, *Đã nhận đủ*) → *Hoàn thành*; có Hủy duyệt về Nháp, Hủy đơn, Nhân bản, Mở lại.
- **Luật nghiệp vụ:** từ *Đã duyệt* nội dung khóa, chỉ còn năm ô phát sinh sau duyệt và khối giao hàng (CR-108); Hủy duyệt bị chặn khi đã nhận hàng, có dòng *Hoàn thành* hoặc có YCTT chưa hủy; chặn ở `block_edit_approved_order()`. Chi tiết ở [13 mục Vòng đời, mục F](13-don-mua-hang.md).
- **Dữ liệu:** đầu đơn (NCC, công ty, ngày đặt, VAT, hình thức thanh toán, loại đơn, tiền tệ, tỷ giá); dòng (mã hàng, số lượng đặt, đơn giá, VAT, kho nhận). Danh sách ở [13 mục A, B](13-don-mua-hang.md).
- **Quyền:** entity `purchase_order` (`create`, `write`, `approve`, `cancel`, `print`, `export`, `delete`); phạm vi theo `SCOPE_FIELDS`. Bảng ở [13 mục G](13-don-mua-hang.md).
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi câu báo lỗi cụ thể trong tài liệu cũ.
- **Liên quan:** CN-TM-10, CN-TM-11, CN-TM-13; phân hệ Nhập khẩu (CN-NK-01, CN-NK-03); công cụ AI `recent_purchase_orders`, `procurement_doc_read`.

### CN-TM-10 — Lần giao và nhận hàng trên ĐMH

- **Mục đích:** ghi từng đợt NCC giao hàng cho một dòng đơn và cập nhật tồn, công nợ theo số nhận.
- **Luồng chính:** ở đơn *Đã duyệt*, mở chi tiết dòng, thêm lần giao (ngày hẹn, kho, số giao, số nhận) → lưu đơn → hệ thống sinh hoặc ghi đè phiếu nhập ngầm, dòng sổ kho, công nợ hàng (và cước nếu có).
- **Luật nghiệp vụ:** lần giao về 0 hoặc bị xóa thì xóa cả phiếu nhập, dòng sổ kho, công nợ (chặn khi công nợ đã trả hoặc đã vào YCTT). Chi tiết ở [13 mục C](13-don-mua-hang.md) và [15 mục C, D](15-ton-kho-cong-no.md).
- **Dữ liệu:** trường lần giao ở [13 mục C](13-don-mua-hang.md).
- **Quyền:** `purchase_order.write`, đơn ở `approved` / `partial` / `received`.
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi.
- **Liên quan:** phân hệ [Nhận hàng](../../nhan-hang/chuc-nang/01-yeu-cau-chuc-nang.md) (đề xuất tách phiếu nhập do thủ kho lập), [Kho](../../kho/chuc-nang/01-yeu-cau-chuc-nang.md).

### CN-TM-13 — Công nợ phải trả

- **Mục đích:** theo dõi nợ tiền hàng, nợ cước, nợ chi phí lô nhập khẩu với từng NCC, tuổi nợ, hạn trả.
- **Luồng chính:** công nợ sinh tự động khi lưu số nhận trên ĐMH (không tạo tay) → người dùng lọc, xem tuổi nợ → chọn khoản nợ để lập YCTT.
- **Luật nghiệp vụ:** một dòng nợ ứng một lần giao × một luồng (`goods`, `shipping`) hoặc một dòng chi phí (`import_cost`). Chi tiết ở [15 phần Công nợ, mục D, F](15-ton-kho-cong-no.md).
- **Dữ liệu:** bảng `tab_payable`; cột và bộ lọc ở [15 mục B, C](15-ton-kho-cong-no.md).
- **Quyền:** `payable.read`, `payable.export`, `payable.write` (cấn trừ tiền treo); phạm vi công ty, phòng (`department_id` là phòng xử lý đơn lúc nợ sinh), người tạo.
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi.
- **Liên quan:** CN-TM-14, CN-TM-15; công cụ AI `payable_lookup`.

### CN-TM-14 — Yêu cầu thanh toán (YCTT)

- **Mục đích:** lập phiếu đề nghị trả tiền cho một NCC, gom nhiều khoản nợ, trừ nợ khi ghi nhận đã chi.
- **Luồng chính:** chọn khoản nợ trên màn Công nợ hoặc ĐMH (hoặc mở form trắng) → *Nháp* → gửi duyệt → duyệt → *Ghi nhận đã chi*, hệ thống cộng `paid_amount` từng khoản.
- **Luật nghiệp vụ:** mỗi phiếu một NCC và một loại nợ; chỉ *Nháp* sửa được; gửi duyệt bị chặn khi có dòng chưa khớp khoản nợ còn nợ (CR-066). Chi tiết ở [14 mục C](14-yeu-cau-thanh-toan.md).
- **Dữ liệu:** [14 mục A, B](14-yeu-cau-thanh-toan.md).
- **Quyền:** entity `payment_request` (`create`, `write`, `approve`, `print`, `export`, `delete`); bảng ở [14 mục D](14-yeu-cau-thanh-toan.md).
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi câu báo lỗi cụ thể.
- **Liên quan:** CN-TM-13, CN-TM-15; công cụ AI `draft_payment_request`, `payment_request_read`.

## 4. Luồng trạng thái chứng từ

Bảng đầy đủ (giá trị DB, nút, điều kiện chuyển) nằm ở tài liệu gốc; dưới đây chỉ là luồng chính.

```
YCBG: Nháp → Chờ duyệt → (Đã duyệt) → Đang xử lý → Đã khảo sát → Đã tạo YCMH → Hoàn thành
      nhánh: Bị trả lại, Đã từ chối                                  — 11 mục Vòng đời
YCMH: Nháp → Chờ duyệt → Đã duyệt → Đã điều phối → Đang xử lý → Hoàn thành
      nhánh: Bị trả lại, Đã từ chối                                  — 12 mục Vòng đời
ĐMH:  Nháp → Chờ duyệt → Đã duyệt → Đã nhận một phần → Đã nhận đủ → Hoàn thành
      nhánh: Bị trả lại, Đã từ chối / Đã hủy; Hủy duyệt về Nháp      — 13 mục Vòng đời
YCTT: Nháp → Chờ duyệt → Đã duyệt → Đã chi                           — 14 mục Vòng đời
Phiếu khảo sát: Nháp → Chờ duyệt → Đã duyệt; nhánh Bị trả lại, Đã từ chối — 10 mục Vòng đời
```

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Mười chỗ hở đáng làm nhất của luồng thu mua, kho (số từ chối, trả hàng NCC, phiếu nhập của thủ kho, hóa đơn NCC…) — làm theo nấc nào | Đại ca | chưa có |
| 2 | Các nợ còn treo của luồng phương án (danh sách ở [12 mục H.9](12-yeu-cau-mua-hang.md)) | Agent 1 | chưa có |
| 3 | Những phần chưa có của Báo cáo thực hiện ([19 mục *Những thứ CHƯA có*](19-bao-cao-thuc-hien-ycbg.md)) | Đại ca | chưa có |
| 4 | Có dời phần phòng ban, công ty (tài liệu 16) và quản trị hệ thống (tài liệu 17) sang phân hệ nền tảng không | Agent 1 | chưa có |

Câu 1 lấy từ [nghien-cuu/11 mục 6](../nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md).
