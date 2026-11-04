# YÊU CẦU CHỨC NĂNG — ĐẶT XE NỘI BỘ

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (kế hoạch cũ ghi nhánh làm việc `pltgiang`) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · duoc-CR-681, duoc-CR-706, duoc-CR-682, duoc-CR-675 · bao-CR-596 |

Tệp này là chỉ mục yêu cầu: mỗi chức năng tóm tắt ngắn rồi trỏ về tài liệu cũ, chủ yếu là [10-dat-xe.md](10-dat-xe.md)
(gọi tắt là *TL10*), [phase-6-con-lai.md](../plans/dat-xe-duyet-dau/phase-6-con-lai.md) (*PHA 6*) và bộ
[đồng bộ app cũ](../tai-lieu-ky-thuat/dong-bo-app-cu/README.md).

## 1. Người dùng và vai trò

Nguồn: TL10 mục *Vai trò tham gia* và *Phân quyền*; mã vai trò đối chiếu `backend/app/seed.py`.

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Người đặt xe (`booking_requester`, phạm vi `own`) | Tạo, xem, sửa phiếu của mình, gửi duyệt, xuất Excel |
| Người duyệt (vai trò có `vehicle_booking.approve`) | Duyệt, yêu cầu chỉnh sửa, từ chối phiếu *Chờ duyệt* |
| Điều phối viên (`booking_dispatcher`, phạm vi `all`) | Điều phối một xe và một tài xế, điều phối lại, trả hoặc từ chối phiếu đang điều phối |
| Quản lý điều phối (`booking_manager`, phạm vi `all`) | Như điều phối viên, thêm quản danh mục Xe và Tài xế |
| Tài xế (`booking_driver`, phạm vi `assigned`) | Nhận, từ chối, bắt đầu, hoàn tất chuyến được phân cho mình |

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** · **Đang làm** · **Chưa** · **Bỏ**. *Chưa ghi* nghĩa là tài liệu cũ ghi đã có
trong mã nhưng không nói môi trường. Các mục PHA 0–6 ghi **Có** theo [đồng bộ app cũ §1](../tai-lieu-ky-thuat/dong-bo-app-cu/README.md#1-bối-cảnh):
"đã làm xong pha 0–6 và đã lên cả `main` (prod)" (15/09/2026).

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-DX-01 | Tạo, sửa, xóa mềm, nhân bản yêu cầu đặt xe hai loại: công tác và giao hàng ([TL10 mục A, B](10-dat-xe.md#a-thông-tin-chung-của-phiếu-header)) | Người đặt xe | `/vehicle-booking/new`, `/vehicle-booking/:id/edit` | Có | |
| CN-DX-02 | Chọn Công ty và Người duyệt trên phiếu; người cùng quyền cũng duyệt được; thư *Gửi duyệt* chỉ tới người được chọn ([TL10 mục A.10](10-dat-xe.md#10-công-ty-và-người-duyệt-chọn-trên-phiếu-company_id-first_approver_id--duoc-cr-681)) | Người đặt xe, người duyệt | Form phiếu, chi tiết phiếu | chưa ghi | duoc-CR-681, duoc-CR-706 |
| CN-DX-03 | Duyệt một bước: duyệt, yêu cầu chỉnh sửa, từ chối kèm lý do; người lập không tự duyệt (trừ phạm vi `all`) ([TL10 vòng đời](10-dat-xe.md#vòng-đời-trạng-thái-phiếu-status)) | Người duyệt | Chi tiết phiếu | Có | |
| CN-DX-04 | Luồng duyệt nhiều bước qua bộ máy duyệt dùng chung, bật bằng `ApprovalSwitch` ([TL10 luồng nhiều bước](10-dat-xe.md#luồng-duyệt-nhiều-bước-approval_bridge), PHA 6.1) | Người duyệt | Panel duyệt trong chi tiết phiếu | Có | |
| CN-DX-05 | Điều phối một xe và một tài xế, điều phối lại khi tài xế từ chối, trả hoặc từ chối phiếu đang điều phối; điều phối sớm vẫn cho ([TL10 mục C](10-dat-xe.md#c-điều-phối--chạy-chuyến-chỉ-xem-trên-chi-tiết-điền-qua-thao-tác)) | Điều phối viên | Chi tiết phiếu | Có | |
| CN-DX-06 | Chống trùng giờ khi điều phối và lọc nguồn tài xế theo vai trò ([PHA 6.3, 6.4](../plans/dat-xe-duyet-dau/phase-6-con-lai.md)) | Điều phối viên | Hộp thoại điều phối | Có | |
| CN-DX-07 | Thao tác tài xế (nhận, từ chối, bắt đầu, hoàn tất, ghi km và chi phí) và màn *Chuyến của tôi* ([TL10 vòng đời](10-dat-xe.md#vòng-đời-trạng-thái-phiếu-status), PHA 6.2) | Tài xế | Chi tiết phiếu, *Chuyến của tôi* | Có | |
| CN-DX-08 | Tự lái: form điền sẵn giấy phép lái xe của người đăng nhập nếu là tài xế | Người đặt xe | `GET /api/dispatch/my-driver` ([api.md](../tai-lieu-ky-thuat/api.md)) | chưa ghi (chưa có tài liệu chức năng) | |
| CN-DX-09 | Thông báo chuông và email theo bước, bật / tắt và sửa mẫu thư ([PHA 6.5](../plans/dat-xe-duyet-dau/phase-6-con-lai.md)) | Hệ thống, quản trị | Chuông, email, `/system/settings` | Có | |
| CN-DX-10 | Bản in phiếu đặt xe ([PHA 6.8](../plans/dat-xe-duyet-dau/phase-6-con-lai.md)) | Người xem được phiếu | `/print/vehicle-booking/:id` | Có | |
| CN-DX-11 | Danh mục Xe: nội bộ / thuê ngoài, doanh nghiệp / cá nhân, biển số duy nhất, nhập / xuất ([TL10 mục D](10-dat-xe.md#d-danh-mục-xe-apivehicles-entity-vehicle)) | Quản lý điều phối | `/vehicle-booking/vehicles` | Có | |
| CN-DX-12 | Danh mục Tài xế: nội bộ tìm nhân sự theo số điện thoại, thuê ngoài nhập tay ([TL10 mục E](10-dat-xe.md#e-danh-mục-tài-xế-apidrivers-entity-driver)) | Quản lý điều phối | `/vehicle-booking/drivers` | Có | |
| CN-DX-13 | Tổng quan theo vai trò, Timeline lịch tháng, báo cáo tổng hợp, xuất Excel theo bộ lọc | Theo quyền | `/api/vehicle-bookings/overview`, `/timeline`, `/summary`, `/export/xlsx` ([api.md](../tai-lieu-ky-thuat/api.md)) | chưa ghi (chưa có tài liệu chức năng) | duoc-CR-675 (quyền xuất) |
| CN-DX-14 | Đồng bộ app đặt xe cũ sang ERP: webhook, sổ đồng bộ, ba vòng quét bù ([vận hành §2](../tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md#2-hai-chiều-chạy-thế-nào-để-biết-tắt-cái-gì-khi-có-sự-cố)) | Hệ thống, người trực | `/system/sync-logs` | Có (công tắc nhận bật trên prod, vận hành §1) | |
| CN-DX-15 | Đồng bộ ERP sang app cũ (P3) ([p3-erp-sang-app-cu.md](../tai-lieu-ky-thuat/dong-bo-app-cu/p3-erp-sang-app-cu.md)) | Hệ thống | — | chưa ghi (đã dựng; công tắc tắt ở dev và prod, chốt 05/10/2026 chưa triển khai) | bao-CR-596 |
| CN-DX-16 | App cũ không đè thao tác đã làm trên ERP (Bước 0, cột `erp_action_at`) ([vận hành §8](../tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md#8-bước-0--app-cũ-không-đè-thao-tác-làm-trên-erp-duoc-cr-682-26102026)) | Hệ thống | — | chưa ghi (mã xong 26/10/2026, chờ deploy theo vận hành §7) | duoc-CR-682 |
| CN-DX-17 | Lập phiếu đặt xe qua Trợ lý AI | Người đặt xe | Trợ lý, cổng MCP | chưa ghi (có bài kiểm `test_assistant_lap_phieu_dat_xe_duyet_dau_kh_ai2_6.py`, chưa có tài liệu chức năng) | |
| CN-DX-18 | Cấp tài khoản đăng nhập cho tài xế thuê ngoài ([PHA 6.7](../plans/dat-xe-duyet-dau/phase-6-con-lai.md), TL10 mục E) | — | — | Chưa (tạm bỏ) | |
| CN-DX-19 | Đưa hộp thoại thao tác nhanh lên trang ([PHA 6.6](../plans/dat-xe-duyet-dau/phase-6-con-lai.md)) | — | — | Chưa (cân nhắc) | |

## 3. Chi tiết từng chức năng

### CN-DX-01 — Yêu cầu đặt xe

- **Mục đích:** đặt xe công tác hoặc giao hàng qua một phiếu có duyệt.
- **Luồng chính:** tạo → lưu nháp → gửi duyệt; chỉ *Nháp* và *Yêu cầu chỉnh sửa* cho sửa.
- **Luật nghiệp vụ và dữ liệu:** trường bắt buộc theo loại ở [TL10 mục B](10-dat-xe.md#b-khối-riêng-theo-loại); mã `DX` cấp
  qua *cửa xoay* để nhiều người tạo cùng lúc không trùng (TL10 mục A.10).
- **Quyền:** `vehicle_booking.create` / `write`.

### CN-DX-02 — Công ty và Người duyệt trên phiếu

- **Luật nghiệp vụ:** hai ô độc lập, bắt buộc khi gửi duyệt; danh sách người duyệt đúng bằng danh sách bước *Người có quyền
  duyệt*; không chọn chính mình; người cùng quyền mà phạm vi phủ phiếu cũng duyệt được, nhưng chuông và thư chỉ tới người
  được chọn; phiếu thấy được ở cả công ty chọn trên phiếu và công ty người tạo (`requester_company_id`) ([TL10 mục A.10](10-dat-xe.md#10-công-ty-và-người-duyệt-chọn-trên-phiếu-company_id-first_approver_id--duoc-cr-681)).
- **Quyền:** ô chọn đọc qua `GET /api/vehicle-bookings/pick-options`, gác `vehicle_booking.create`.

### CN-DX-04 — Luồng duyệt nhiều bước

- **Luật nghiệp vụ:** sáu luật đã trả giá ở [TL10](10-dat-xe.md#luồng-duyệt-nhiều-bước-approval_bridge): đang chạy luồng thì đóng
  năm cửa đổi trạng thái khác; hàm nhận kết cục tự kiểm trạng thái nguồn; ký xong ghi người và giờ duyệt; người đang giữ
  việc đọc được phiếu dù ngoài phạm vi; xóa phiếu dọn phiên duyệt; ô *Trưởng bộ phận phê duyệt* bộ máy không đọc tới.

### CN-DX-05 và CN-DX-07 — Điều phối và chạy chuyến

- **Luồng chính:** *Đã duyệt* → điều phối (xe + tài xế) → tài xế nhận → bắt đầu → hoàn tất (phiếu *Hoàn thành*).
- **Luật nghiệp vụ:** điều phối chỉ chặn phiếu đã hủy / từ chối / hoàn thành (quyết định 21/09/2026); người là tài xế chỉ
  đụng chuyến của mình, người không phải tài xế có quyền `write` được làm thay ([TL10 vòng đời](10-dat-xe.md#vòng-đời-trạng-thái-phiếu-status)).
- **Quyền:** `vehicle_booking.write` (điều phối và tài xế; tài xế phạm vi `assigned`).

### CN-DX-14 — Đồng bộ app cũ sang ERP

- **Mục đích:** giai đoạn 1 người dùng vẫn làm trên app cũ, ERP nhận đủ dữ liệu để điều phối và báo cáo.
- **Luật nghiệp vụ:** không mất phiếu, không đẻ phiếu trùng, không lệch trạng thái; chỉ đồng bộ kết cục duyệt (QĐ-I); đụng
  độ thì cú sau ghi đè theo giờ bấm (QĐ-J) ([tài liệu đồng bộ mục 2–5](../tai-lieu-ky-thuat/dong-bo-app-cu/README.md#2-mục-tiêu)).

## 4. Luồng trạng thái chứng từ

Bảng mã và điều kiện chuyển ở [TL10](10-dat-xe.md#vòng-đời-trạng-thái-phiếu-status). Tóm tắt:

```
Nháp → Chờ duyệt → Đã duyệt → Điều phối → Hoàn thành
       Chờ duyệt → Yêu cầu chỉnh sửa → (gửi lại) Chờ duyệt
       Chờ duyệt → Từ chối · Đã hủy
Trạng thái tài xế (khi Điều phối): Chờ tài xế → Đã nhận → Đang đi → Hoàn thành · Tài xế từ chối
```

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Mốc chuyển người dùng sang ERP và tắt app cũ (QĐ-J, điều kiện ở mục 8 tài liệu đồng bộ) | chưa có | chưa có |
| 2 | Có triển khai chiều ERP sang app cũ (P3) không, khi nào | chưa có | chưa có |
| 3 | Phiếu gốc app cũ đã thao tác trên ERP thì thống nhất làm tiếp trên ERP (đánh đổi của Bước 0, vận hành §8) | chưa có | chưa có |
