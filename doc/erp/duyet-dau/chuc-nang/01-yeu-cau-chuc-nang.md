# YÊU CẦU CHỨC NĂNG — DUYỆT DẤU

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (kế hoạch cũ ghi nhánh làm việc `pltgiang`) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · bao-CR-584 |

Tệp này là chỉ mục yêu cầu: mỗi chức năng tóm tắt ngắn rồi trỏ về tài liệu cũ, chủ yếu là
[10-duyet-dau.md](10-duyet-dau.md) (gọi tắt là *TL10*) và [tiến độ](../plans/duyet-dau-phase/tien-do.md).

## 1. Người dùng và vai trò

Nguồn: TL10 mục *Vai trò tham gia* và *Phân quyền*; mã vai trò đối chiếu `backend/app/seed.py`.

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Nhân viên tạo phiếu (vai trò sẵn có, `seal_request` read / create / write, phạm vi `own`) | Tạo, sửa khi còn Nháp hoặc bị yêu cầu chỉnh sửa, tải chứng từ chữ ký sống, gửi duyệt |
| Trưởng bộ phận (`seal_approver`, phạm vi `dept`) | Duyệt, yêu cầu chỉnh sửa, từ chối phiếu *Chờ duyệt* |
| Văn thư (`seal_clerk`) | Trên phiếu *Đã duyệt*: hoàn thành sau khi đóng dấu thật, yêu cầu chỉnh sửa, từ chối. Thấy phiếu công ty nào do bảng phân công văn thư quyết (`backend/app/seed_van_thu.py`) |
| Giám đốc công ty (`seal_director`, phạm vi `company`) | Nhận thông báo, xem phiếu đã duyệt của công ty mình; không phê duyệt |
| Quản trị con dấu (`seal_admin`, phạm vi `all`) | Quản danh mục loại con dấu, xem mọi phiếu |

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** · **Đang làm** · **Chưa** · **Bỏ**. *Chưa ghi* nghĩa là tài liệu cũ ghi là
đã làm trong mã nhưng không nói đã lên prod hay mới trên dev.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-DDAU-01 | Tạo, sửa, xóa, nhân bản yêu cầu đóng dấu; mã phiếu tự sinh `DD###` ([TL10 mục A](10-duyet-dau.md#a-thông-tin-chung-của-phiếu-header)) | Nhân viên | `/approval-seal/new`, `/approval-seal/:id/edit` | chưa ghi | |
| CN-DDAU-02 | Tải tệp chứng từ chữ ký sống (ảnh / PDF), bắt buộc ít nhất một tệp khi gửi duyệt; xem, mở tab mới, tải về ([TL10 mục B](10-duyet-dau.md#b-tệp-chứng-từ-chữ-ký-sống-yêu-cầu-cốt-lõi)) | Nhân viên, văn thư | Chi tiết phiếu | chưa ghi | |
| CN-DDAU-03 | Chọn trưởng bộ phận phê duyệt, mặc định theo phòng ban người tạo ([TL10 mục A.9](10-duyet-dau.md#9-trưởng-bộ-phận-phê-duyệt-first_approver_id)) | Nhân viên | Form phiếu | chưa ghi | |
| CN-DDAU-04 | Cổng 1 — trưởng bộ phận duyệt, yêu cầu chỉnh sửa, từ chối kèm lý do ([TL10 vòng đời](10-duyet-dau.md#vòng-đời-trạng-thái-phiếu-status)) | Trưởng bộ phận | Chi tiết phiếu | chưa ghi | |
| CN-DDAU-05 | Cổng 2 — văn thư hoàn thành (số bản, ghi chú đóng dấu), yêu cầu chỉnh sửa, từ chối ([TL10 mục C](10-duyet-dau.md#c-đóng-dấu--hoàn-thành-chỉ-xem-trên-chi-tiết-điền-qua-thao-tác)) | Văn thư | Chi tiết phiếu | chưa ghi | |
| CN-DDAU-06 | Thông báo chuông và email theo bước tới người tạo, văn thư, giám đốc ([tiến độ PHA 3](../plans/duyet-dau-phase/tien-do.md)) | Hệ thống | Chuông, email | chưa ghi | |
| CN-DDAU-07 | Nối bộ máy duyệt nhiều bước qua công tắc `ApprovalSwitch` ([tiến độ PHA 5](../plans/duyet-dau-phase/tien-do.md), [phase-5](../plans/duyet-dau-phase/phase-5-runtime-duyet-va-test.md)) | Người duyệt | Chi tiết phiếu | Đang làm (backend có; panel duyệt giao diện chưa làm) | |
| CN-DDAU-08 | Danh mục loại con dấu: thêm, sửa, tắt, nhập / xuất CSV ([TL10 mục D](10-duyet-dau.md#d-danh-mục-loại-con-dấu-apiseal-types-entity-seal_type)) | Quản trị con dấu | `/approval-seal/seal-types` | chưa ghi | |
| CN-DDAU-09 | Phân công văn thư theo công ty (một văn thư nhiều công ty, cờ văn thư tổng) | Quản trị | Màn *Phân công văn thư* (`/api/seal-clerks`, [api.md](../tai-lieu-ky-thuat/api.md)) | chưa ghi | |
| CN-DDAU-10 | Bản in phiếu nhúng ảnh chứng từ ([tiến độ PHA 4](../plans/duyet-dau-phase/tien-do.md)) | Mọi người xem được phiếu | `/print/approval-seal/:id` | chưa ghi | |
| CN-DDAU-11 | Tổng quan theo vai trò và báo cáo tổng hợp kèm xuất | Theo quyền | `GET /api/seal-requests/overview`, `/summary` ([api.md](../tai-lieu-ky-thuat/api.md)) | chưa ghi | |
| CN-DDAU-12 | Nhận phiếu đóng dấu từ app đặt xe cũ, thêm trạng thái *Đã trả hồ sơ* (QĐ-H) ([đồng bộ app cũ](../../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/README.md#3-những-gì-đã-chốt)) | Hệ thống | Sổ đồng bộ | Có (chiều app cũ sang ERP bật trên prod, [vận hành §1](../../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md#1-bản-đồ-hệ-thống--dev-và-prod-là-hai-bộ-riêng-không-chung-gì)) | |
| CN-DDAU-13 | Tách khối chứng từ chữ ký sống và ảnh ghi chú (`doc_type` signed_doc / note) ([TL10 mục H](10-duyet-dau.md#h-ghi-chú-đính-kèm-ảnh)) | Nhân viên, văn thư | Chi tiết phiếu | Chưa (hoãn, chờ quyết có làm không) | |
| CN-DDAU-14 | Lập phiếu đóng dấu qua Trợ lý AI | Nhân viên | Trợ lý, cổng MCP | chưa ghi (có bài kiểm `test_assistant_lap_phieu_dat_xe_duyet_dau_kh_ai2_6.py`, chưa có tài liệu chức năng) | |

## 3. Chi tiết từng chức năng

### CN-DDAU-01 và CN-DDAU-02 — Phiếu và tệp chứng từ

- **Mục đích:** xin đóng dấu kèm bằng chứng chữ ký sống.
- **Luồng chính:** tạo → lưu nháp → tải tệp → gửi duyệt.
- **Luật nghiệp vụ:** gửi duyệt kiểm có mục đích, loại con dấu, công ty, ít nhất một tệp; lưu nháp không kiểm. Chỉ *Nháp*
  và *Yêu cầu chỉnh sửa* cho sửa. Nhân bản không chép tệp ([TL10](10-duyet-dau.md#giao-diện-dùng-chung-2-màn)).
- **Dữ liệu:** bắt buộc mục đích, loại con dấu, công ty cần đóng dấu; số bản mặc định 1.
- **Quyền:** `seal_request.create` / `write`; xem tệp kế thừa quyền phiếu.
- **Ngoại lệ:** thiếu mục đích báo *"Vui lòng nhập mục đích sử dụng"*.

### CN-DDAU-04 và CN-DDAU-05 — Luồng duyệt hai cổng

- **Luồng chính:** *Chờ duyệt* → trưởng bộ phận duyệt → *Đã duyệt* → văn thư đóng dấu thật → *Hoàn thành*
  ([TL10 vòng đời](10-duyet-dau.md#vòng-đời-trạng-thái-phiếu-status)).
- **Luật nghiệp vụ:** mỗi bước kiểm quyền và trạng thái nguồn; lý do trả / từ chối ghi thêm vào ghi chú. Hệ không sinh
  dấu điện tử.
- **Quyền:** cổng 1 `seal_request.approve`; cổng 2 `seal_request.write`.
- **Liên quan:** CN-DDAU-06 (thông báo), CN-DDAU-07 (bộ máy nhiều bước).

### CN-DDAU-12 — Đồng bộ app cũ

- **Mục đích:** phiếu tạo và duyệt trên app đặt xe cũ sang ERP, không mất phiếu, không trùng, không lệch trạng thái.
- **Luật nghiệp vụ:** hai bộ máy duyệt giữ nguyên, chỉ đồng bộ kết cục (QĐ-I); chi tiết hợp đồng webhook ở
  [mô tả kỹ thuật](../../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/mo-ta-ky-thuat.md).

## 4. Luồng trạng thái chứng từ

Bảng mã và điều kiện chuyển ở [TL10](10-duyet-dau.md#vòng-đời-trạng-thái-phiếu-status). Tóm tắt:

```
Nháp → Chờ duyệt → Đã duyệt → Hoàn thành
       Chờ duyệt / Đã duyệt → Yêu cầu chỉnh sửa → (gửi lại) Chờ duyệt
       Chờ duyệt / Đã duyệt → Từ chối
       Đã hủy
```

## 5. Câu hỏi còn mở

Nguồn: [plans/duyet-dau-phase/README.md mục 4](../plans/duyet-dau-phase/README.md#4-các-quyết-định-chốt--còn-mở).

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| A | Giám đốc chỉ nhận thông báo hay thêm một cổng duyệt sau trưởng bộ phận? Mặc định: chỉ thông báo | chưa có | chưa có |
| B | Văn thư yêu cầu chỉnh sửa, gửi lại thì về trưởng bộ phận duyệt lại hay thẳng văn thư? Mặc định: về trưởng bộ phận | chưa có | chưa có |
| C | Chọn trưởng bộ phận thủ công hay luôn tự động theo phòng ban? Mặc định: tự động và cho chọn | chưa có | chưa có |
| D | Có làm tách khối chứng từ và ảnh ghi chú (CN-DDAU-13) không | chưa có | chưa có |
