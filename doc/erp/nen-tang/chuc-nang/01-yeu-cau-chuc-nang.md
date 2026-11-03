# YÊU CẦU CHỨC NĂNG — NỀN TẢNG DÙNG CHUNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · CR-170..172 · bao-CR-312 · bao-CR-703 |

Tệp này là **mục lục chức năng**: mỗi dòng tóm tắt ngắn và trỏ tới tài liệu cũ đang giữ chi tiết (luật *một sự thật một
chỗ*). Muốn sửa luật nghiệp vụ thì sửa ở tài liệu được trỏ tới, rồi cập nhật dòng ở đây nếu tên hoặc trạng thái đổi.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Mọi người dùng đã đăng nhập | Nhận chuông, Web Push, email luồng duyệt của chính mình; dùng Trang cá nhân; gửi phiếu hỗ trợ (`ticket` phạm vi `own`); bình luận trên phiếu mình xem được; duyệt các bước đang chờ mình |
| Nhân viên hỗ trợ (`support`) | Xem mọi phiếu hỗ trợ, trả lời, nhận / gán, đổi mọi trạng thái (`ticket` đủ bốn quyền, phạm vi `all`) |
| Quản trị HDSD (`help_admin`) | Soạn bài, ảnh từng bước, FAQ, bố cục trang chủ Trung tâm trợ giúp (chỉ entity `help_article`) |
| Quản lý thu mua (`pur_manager`) | Nhận ngầm mọi entity không thuộc nhóm hệ thống, phạm vi `all` (trong đó có `ticket`) |
| Quản trị hệ thống (`admin` / `ADMINISTRATOR`) | Cấu hình, mẫu email, sao lưu, nhật ký, phiên đăng nhập, việc chạy ngầm, tài khoản, vai trò, phân quyền, nhập / xuất, khai luồng duyệt, giao báo cáo |
| Người giữ quyền `approval_flow.*` | Khai luồng duyệt, bật / tắt bộ máy duyệt theo loại chứng từ, ủy quyền, bàn giao việc chờ duyệt |

Nguồn: [`11`](11-ho-tro-ticket.md) mục 2 và 10, [`13`](13-trung-tam-hdsd.md) mục 3, [`api.md`](../tai-lieu-ky-thuat/api.md).

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**. *chưa ghi* = tài liệu nguồn
không nói rõ.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-NT-01 | Chuông thông báo trong ứng dụng và trang xem toàn bộ — [`10`](10-thong-bao-va-trang-ca-nhan.md) Phần I mục A–D, F | Mọi người | Chuông thanh tiêu đề, `/notifications` | chưa ghi | — |
| CN-NT-02 | Thông báo đẩy Web Push và cài ứng dụng PWA — [`10`](10-thong-bao-va-trang-ca-nhan.md) Phần I mục E, Phần III | Mọi người | `/me`, banner *Cài ứng dụng* | chưa ghi | — |
| CN-NT-03 | Email thông báo luồng duyệt, công tắc ba tầng và công tắc theo từng người — [`10`](10-thong-bao-va-trang-ca-nhan.md) Phần I mục G | Mọi người; quản trị | `/me`, hồ sơ Nhân sự, Phân quyền | chưa ghi | bao-CR-349 |
| CN-NT-04 | Trang cá nhân: thông tin, đổi mật khẩu, việc cần làm, thiết bị, lịch sử đăng nhập; khối tài khoản góc phải — [`10`](10-thong-bao-va-trang-ca-nhan.md) Phần I-B, Phần II | Mọi người | `/me` | chưa ghi | CR-028 · bao-CR-395 · bao-CR-400 |
| CN-NT-05 | Phiếu hỗ trợ nội bộ: gửi, trao đổi, nhận / gán, đổi trạng thái — [`11`](11-ho-tro-ticket.md) | Mọi người; nhóm Hỗ trợ | Popup *Gửi yêu cầu hỗ trợ*, `/me?tab=tickets`, `/tickets`, `/tickets/:id` | Dev | — |
| CN-NT-06 | Bình luận (Trao đổi) trên chứng từ: trả lời hai cấp, nhắc `@`, thích, đính kèm — [`12`](12-binh-luan-tren-chung-tu.md) | Người xem được phiếu | Cuối trang chi tiết YCMH, YCBG, Khảo sát, ĐMH | chưa ghi | CR-030 · CR-031 · CR-033 |
| CN-NT-07 | Trung tâm trợ giúp: bài viết theo cây, FAQ, tìm kiếm, nhập bài từ tệp — [`13`](13-trung-tam-hdsd.md) | Công khai (đọc); `help_admin` (ghi) | `help.degoholding.vn`, nút `?` cạnh chuông | Có | CR-019 · CR-052..054 |
| CN-NT-08 | Luồng duyệt dùng chung: khai luồng, bật / tắt theo loại chứng từ, việc chờ tôi, duyệt / từ chối / trả về / rút, ủy quyền, bàn giao khi nghỉ việc, bản in dấu vết — [Văn thư nhóm I](../../van-thu/chuc-nang/12-danh-sach-tinh-nang.md) mục I10..I26, đường `/api/approval*` ở [`api.md`](../tai-lieu-ky-thuat/api.md) | Người duyệt; người giữ `approval_flow` | Phân hệ Phê duyệt (Luồng duyệt, Bật bộ máy duyệt), trang chi tiết chứng từ | chưa ghi | CR-260 · duoc-CR-680 |
| CN-NT-09 | Tệp đính kèm dùng chung: tải lên, gắn vào phiếu, xem, tải về, nén cả chuỗi chứng từ — đường `/api/attachments` ở [`api.md`](../tai-lieu-ky-thuat/api.md), luật an toàn ở [sổ bảo mật](../../../tai-lieu-ky-thuat/van-hanh/so-ghi-nhan-loi-bao-mat.md) mục 2b | Người có quyền trên phiếu | Khối đính kèm trên chứng từ | chưa ghi | bao-CR-408 |
| CN-NT-10 | Nhập dữ liệu theo lô: chạy thử, ghi thật, hoàn tác đúng lô, tệp mẫu — [`16`](../tai-lieu-ky-thuat/16-quan-ly-import-export-v2.md) mục 2, 7, 8, 9.1 | Quản trị; người có quyền nhập | `/system/imports`, `/system/imports/:id` | Đang làm | CR-170 · duoc-CR-628 |
| CN-NT-11 | Xuất dữ liệu tập trung và nhật ký xuất — [`16`](../tai-lieu-ky-thuat/16-quan-ly-import-export-v2.md) mục 2.1, 9.2 | Người có quyền `export` | `/system/exports` | Đang làm | CR-171 · CR-172 |
| CN-NT-12 | Báo cáo và quyền xem từng báo cáo (lớp gác thứ ba `require_report`, giao theo người / phòng / pháp nhân / vai trò) — đường `/api/reports`, `/api/report-access` ở [`api.md`](../tai-lieu-ky-thuat/api.md), luật ở [`CLAUDE.md`](../../../../CLAUDE.md) | Người được giao báo cáo; quản trị | Phân hệ Báo cáo; tab Báo cáo ở Phân quyền tài khoản | chưa ghi | duoc-CR-562 |
| CN-NT-13 | Tổng quan, việc cần làm và cảnh báo hệ thống (`/api/dashboard`, `/api/alerts`) — [`api.md`](../tai-lieu-ky-thuat/api.md); cảnh báo cộng vào số trên chuông theo [`10`](10-thong-bao-va-trang-ca-nhan.md) mục A | Mọi người | Màn Tổng quan, chuông | chưa ghi | — |
| CN-NT-14 | Cấu hình hệ thống: cài đặt chung, thử gửi thư, thử kho lưu trữ, mẫu email thông báo, danh sách loại trừ email, hộp thư gửi — [`api.md`](../tai-lieu-ky-thuat/api.md) | Quản trị (`setting`, `mailbox`) | `/system`: Cấu hình hệ thống, Mẫu email thông báo, Hộp thư gửi | chưa ghi | — |
| CN-NT-15 | Việc chạy ngầm: danh sách việc theo lịch, lần chạy, công tắc — sổ `backend/app/modules/job_run/registry.py`, đường `/api/system/jobs` ở [`api.md`](../tai-lieu-ky-thuat/api.md) | Quản trị (`setting.read`) | `/system`: Việc chạy ngầm | chưa ghi | bao-CR-703 |
| CN-NT-16 | Nhật ký nghiệp vụ, nhật ký hệ thống gộp theo lượt gọi, phiên đăng nhập (đá phiên, đăng xuất mọi thiết bị) — [nhật ký và phiên đăng nhập](../../../tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md) mục 4, 5, 8 | Quản trị; mỗi người xem phiên của mình | `/system/logs`, Phiên đăng nhập, `/me` | Có | bao-CR-312 · bao-CR-313 · bao-CR-346 · bao-CR-360 · bao-CR-395 |
| CN-NT-17 | Sao lưu CSDL lên R2, tải bản sao lưu — đường `/api/backups` ở [`api.md`](../tai-lieu-ky-thuat/api.md) | Quản trị (`backup`) | `/system`: Sao lưu CSDL | Có | — |
| CN-NT-18 | Đăng nhập và xác thực: đăng nhập, Google, quên / đặt lại mật khẩu, làm mới phiên, chữ ký, ảnh đại diện — đường `/api/auth` ở [`api.md`](../tai-lieu-ky-thuat/api.md); chính sách mật khẩu ở [sổ bảo mật](../../../tai-lieu-ky-thuat/van-hanh/so-ghi-nhan-loi-bao-mat.md) BM-016 | Mọi người | Màn đăng nhập, `/me` | chưa ghi | bao-CR-405 |
| CN-NT-19 | Tài khoản, vai trò, ma trận quyền, phạm vi theo từng cặp người × vai trò; công ty, phòng ban — đường `/api/users`, `/api/roles`, `/api/companies`, `/api/departments` ở [`api.md`](../tai-lieu-ky-thuat/api.md); thiết kế ở [phân quyền](../../../tai-lieu-ky-thuat/phan-quyen/thiet-ke-phan-quyen.md) | Quản trị | `/system`: Phân quyền tài khoản | chưa ghi | — |
| CN-NT-20 | Sổ đồng bộ với hệ ngoài: xem, chạy lại dòng hỏng — đường `/api/sync-logs` ở [`api.md`](../tai-lieu-ky-thuat/api.md) | Quản trị (`sync_log`) | `/system`: Sổ đồng bộ | chưa ghi | — |
| CN-NT-21 | Theo dõi mức dùng: thu sự kiện giao diện, báo cáo dùng theo chức năng (báo cáo 15), hồ sơ cách làm việc (báo cáo 14), năng lực theo loại việc (báo cáo 16) — [theo dõi người dùng](../../../tai-lieu-ky-thuat/tracking-nguoi-dung-ho-so-ca-nhan.md), [năng lực theo loại việc](../../../tai-lieu-ky-thuat/nang-luc-theo-loai-viec.md) | Quản trị | Phân hệ Báo cáo | chưa ghi | duoc-CR-641 |
| CN-NT-22 | Bộ lọc nhanh và sắp xếp màn danh sách — [`14`](../tai-lieu-ky-thuat/14-filter-sort-man-danh-sach-v2.md) | Mọi người | Màn danh sách Thu mua, Sản xuất | Đang làm | CR-127 · kh-NT2-2 |
| CN-NT-23 | Xóa mềm dùng chung, ngưng dùng danh mục thay vì xóa — [`20`](../tai-lieu-ky-thuat/20-ra-soat-xoa-cung.md) | Người có quyền xóa | Màn danh sách / chi tiết | chưa ghi | ai-CR-169..191 |
| CN-NT-24 | Tùy chọn người dùng và nhãn trạng thái do backend cấp (`/api/me/preferences`, `/api/meta/statuses`) — [`api.md`](../tai-lieu-ky-thuat/api.md) | Mọi người | Mọi màn | chưa ghi | — |

## 3. Chi tiết từng chức năng

Chỉ viết cho sáu chức năng chính; các chức năng khác đọc ở tài liệu được trỏ trong bảng mục 2.

### CN-NT-01 — Chuông thông báo trong ứng dụng

- **Mục đích:** báo người dùng chứng từ liên quan tới họ đổi trạng thái mà không phải rời màn đang làm.
- **Luồng chính:** controller gọi `trigger_notification` sau thao tác đổi trạng thái → tạo dòng thông báo cho người nhận →
  đẩy Web Push (CN-NT-02) và email luồng duyệt (CN-NT-03) nếu bật → chuông tự làm mới 20 giây một lần.
- **Luật nghiệp vụ:** số trên chuông = chưa đọc + cảnh báo hệ thống; nhiều thông báo cùng chứng từ gộp một dòng; email
  chỉ dùng cho luồng duyệt, cấp tài khoản, đặt lại mật khẩu. Chi tiết: [`10`](10-thong-bao-va-trang-ca-nhan.md) Phần I.
- **Quyền:** không có entity riêng; mỗi người chỉ thấy thông báo của chính mình (cô lập theo `user_id`).
- **Liên quan:** công cụ AI chuyển chuông sang Telegram (`agent.forward_bells`, xem [`api.md`](../../tro-ly-ai/tai-lieu-ky-thuat/api.md) của Trợ lý AI).

### CN-NT-05 — Phiếu hỗ trợ nội bộ

- **Mục đích:** một kênh trong ứng dụng để nhân viên gửi yêu cầu hỗ trợ và trao đổi với nhóm Hỗ trợ.
- **Luồng chính:** người gửi mở popup → chọn chủ đề, nhóm, mức ưu tiên, đính kèm → nhóm Hỗ trợ nhận phiếu, trả lời →
  người gửi phản hồi hoặc đóng. Chi tiết: [`11`](11-ho-tro-ticket.md) mục 3–5.
- **Luật nghiệp vụ:** mọi phiếu về một nhóm Hỗ trợ; trường nhóm chỉ là nhãn phân loại; người gửi chỉ đặt được *Đã đóng*
  hoặc mở lại; nhận phiếu khi còn *Mới* thì tự sang *Đang xử lý*.
- **Quyền:** `ticket.read/create/write` phạm vi `own` cho vai trò cơ bản; `support` có thêm `delete`, phạm vi `all`.
  `SCOPE_FIELDS["ticket"]` lọc theo `company_id` và `created_by`.
- **Liên quan:** công cụ AI `ticket_create`, `my_tickets`; bot kéo phiếu giao cho bot (`agent.pull_tickets`).

### CN-NT-06 — Bình luận trên chứng từ

- **Mục đích:** trao đổi ngay trong phiếu thay cho nhắn rời qua Zalo / email.
- **Luật nghiệp vụ:** không có quyền riêng, thừa hưởng `read` và phạm vi của chứng từ; chỉ người viết xóa được, trừ người
  có `user:delete`; xóa là xóa cứng và cuốn theo phản hồi; chưa mở cho Yêu cầu thanh toán. Chi tiết:
  [`12`](12-binh-luan-tren-chung-tu.md) mục 1–4, 6.
- **Dữ liệu:** nội dung tối đa 5.000 ký tự, nhắc tối đa 20 người, tối đa 5 tệp mỗi bình luận (`comment/service.py`).

### CN-NT-08 — Luồng duyệt dùng chung

- **Mục đích:** một bộ máy duyệt cho mọi loại chứng từ (Văn thư, Đặt xe, Duyệt dấu...) thay cho đường duyệt
  riêng của từng phân hệ.
- **Luồng chính:** quản trị khai luồng và các bước (kéo thả, nhánh song song) → bật công tắc cho loại chứng từ → người
  duyệt thấy việc ở *Việc chờ tôi* → duyệt / từ chối / trả về; người nộp rút được khi chưa ai duyệt.
- **Luật nghiệp vụ:** duyệt không gác bằng `require(...)` mà bằng *có việc đang chờ mình*; tắt công tắc là quay về đường
  duyệt cũ ngay; ngưng ủy quyền là tắt, không xóa. Danh mục yêu cầu gốc I10..I26 ở
  [Văn thư nhóm I](../../van-thu/chuc-nang/12-danh-sach-tinh-nang.md); bước *Người có quyền duyệt (theo phân quyền)* ở
  bài [`seed_help_phe_duyet_theo_quyen.py`](../../../../backend/scripts/seed_help_phe_duyet_theo_quyen.py).
- **Quyền:** `approval_flow.read/create/write/delete/export`; báo cáo duyệt gác thêm báo cáo 12.
- **Liên quan:** công cụ AI `my_approval_tasks`, `propose_approval`; thu mua giữ luồng duyệt hiện tại (chốt 22/10/2026,
  [kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md)).

### CN-NT-10 — Nhập dữ liệu theo lô

- **Mục đích:** nhập hàng loạt có dấu vết, thử trước được, hoàn tác đúng lần nhập.
- **Luồng chính:** chọn loại dữ liệu, tải tệp mẫu → chạy thử (không ghi) → xem kết quả từng dòng → ghi thật từ đúng tệp đó
  → hoàn tác nếu sai. Chi tiết: [`16`](../tai-lieu-ky-thuat/16-quan-ly-import-export-v2.md) mục 4.3, 7, 8.
- **Luật nghiệp vụ:** mọi lần nhập là một lô trong `tab_import_batch`, log từng dòng; hoàn tác dùng `ImportChange`, không
  chụp cả bảng; Nhân sự và Phòng ban đã ngừng nhập CSV đồng bộ (trả 410), chuyển sang lô.
- **Quyền:** hiện gác bằng entity `import`; đổi sang action `import` trên từng entity là đợt Đ-13c (chưa làm).
- **Liên quan:** Tra cứu thị trường dùng lại khung lô này ([Hải quan](../../hai-quan/chuc-nang/01-yeu-cau-chuc-nang.md) CN-HQ-01).

### CN-NT-16 — Nhật ký và phiên đăng nhập

- **Mục đích:** truy được ai gọi gì, đổi gì, từ đâu; thu hồi được phiên khi lộ token hoặc nhân sự nghỉ việc.
- **Luồng chính:** middleware ghi mỗi lượt gọi vào `tab_request_log`; `record(...)` ghi câu chuyện vào `tab_audit_log`;
  sự kiện ORM ghi trước / sau từng cột vào `tab_change_log`; màn `/system/logs` gộp ba lớp theo `request_id`.
- **Luật nghiệp vụ:** chỉ tài khoản quản trị đọc nhật ký toàn hệ (BM-001); hồ sơ chuyển *Nghỉ việc* thì khóa tài khoản và
  cắt phiên cùng giao dịch (BM-015). Chi tiết: [nhật ký và phiên đăng nhập](../../../tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md).
- **Quyền:** `login_session.read/delete`; nhật ký gác theo luật mục 7 của tài liệu trên.

## 4. Luồng trạng thái chứng từ (nếu có)

Phiếu hỗ trợ ([`11`](11-ho-tro-ticket.md) mục 5):

```
Mới (open) → Đang xử lý (in_progress) ⇄ Đã trả lời (answered) → Đã đóng (closed)
Đã đóng → Đang xử lý (người gửi mở lại hoặc phản hồi)
```

Lô nhập dữ liệu ([`16`](../tai-lieu-ky-thuat/16-quan-ly-import-export-v2.md) mục 7, 8):

```
Chạy thử → Ghi thật → (Hoàn tác đúng lô)
```

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Danh mục Văn thư nhóm I còn ghi `[ ]` cho I10..I26 trong khi `api.md` đã có đường `/api/approvals/*` (I16, I17, I20, I23, I26): cập nhật trạng thái ở danh mục nào là nguồn đúng | Người phụ trách Văn thư | chưa có |
| 2 | Phiếu hỗ trợ trên prod đã bật chưa (tài liệu `11` chỉ nói về cờ build bản v1) | Người phụ trách nền tảng | chưa có |
| 3 | Ngày tắt `frontend/` cũ; tích hợp ngoài nào làm đầu tiên (C4); có dùng cây phòng ban cho phạm vi và báo cáo không | Đại ca | chưa có |
| 4 | `purchase_history` có cần lọc theo phạm vi không | Agent 1 đề xuất, đại ca chốt | chưa có |

Câu 3 và 4 lấy từ [kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md) §1.
