# DANH SÁCH MÀN HÌNH — VĂN THƯ · CỘNG TÁC · HỆ THỐNG (frontend-v2)

Bản 1.0 — 28/08/2026. Nguồn sự thật là `routes.tsx` của từng phân hệ.

---

## Phân hệ Văn bản (`document`)

Soạn thảo, duyệt, ban hành và tra cứu văn bản nội bộ. Trục là **loại × pháp nhân ban hành × phiên bản**; sổ văn bản cấp thêm một số thứ tự riêng và chia quyền xem theo quyển. Backend thật tại `/api/documents`, `/api/doc-types`, `/api/external-parties`, `/api/document-books`. Khóa phân hệ: `entity: 'document'`.

**Mục menu (nav):**

| Mục menu | Nhóm | Khóa quyền |
|---|---|---|
| Tổng quan | — | Không khóa |
| Văn bản | Nghiệp vụ | Không khóa — tab Văn bản đến mở công khai cho mọi tài khoản; tab Văn bản đi tự ẩn khi thiếu `document.read` |
| Chờ tôi duyệt | Nghiệp vụ | Không khóa — người duyệt thường không có vai trò Văn bản, gác bằng `document.read` là ẩn việc của chính họ |
| Sổ văn bản | Nghiệp vụ | Không khóa — thành viên sổ không cần vai trò; backend lọc theo từng quyển |
| Thiết lập văn bản | Danh mục | `entities: [doc_type, doc_template, security_level, external_party]` — bất kỳ khóa nào là vào được, trang tự ẩn tab thiếu quyền (CR-157) |
| Quy tắc đánh số | Danh mục | `entity: doc_numbering_rule` |
| Quy tắc quan hệ | Danh mục | `entity: doc_link_rule` |

Tổng: **23 màn trong phân hệ** (không tính redirect `/document/applied-to-me`) + **1 màn in** khai ở `app-router.tsx` ngoài `ModuleLayout`.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Tổng quan Văn bản | `/document` | `pages/document-dashboard-page.tsx` | KPI (số văn bản ban hành, chờ duyệt, quá hạn) + biểu đồ cột phát hành 12 tháng + donut theo loại + ma trận ưu tiên + danh sách việc cần xử lý. Một lần gọi `/api/documents/dashboard`, backend lọc đúng phạm vi như danh sách văn bản. Bộ lọc theo pháp nhân / phòng ban / khoảng ngày (tuỳ chọn). |
| Danh sách Văn bản | `/document/documents` | `pages/document-list-page.tsx` | Hai tab: «Văn bản đến» gọi `/api/documents/applies-to-me` (mở cho mọi tài khoản đăng nhập, không cần `document.read`); «Văn bản đi» gọi `/api/documents` (cần `document.read`, tab tự ẩn khi thiếu). Đổi tab thì xóa sạch tham số URL trừ `?tab=`. Mặc định tab Đi. |
| Soạn văn bản mới | `/document/documents/new` | `pages/document-create-page.tsx` | Form 2 bước: bước 1 — thông tin chính (loại, tên, pháp nhân, phòng chủ trì); bước 2 — phạm vi áp dụng và quyền truy cập. Hỗ trợ nhân bản từ văn bản cũ (`documentCloneApi`) và dự thảo từ trợ lý AI (`parseAssistantLeaveDraft`). |
| Chi tiết Văn bản | `/document/documents/:id` | `pages/document-detail-page.tsx` | Soạn thảo Rich Text (TipTap) với cỡ trang A4, tự động lưu nháp. Các tab: nội dung, quy trình duyệt, phạm vi, chữ ký, đính kèm. Hành động: lưu nháp, gửi duyệt, duyệt/trả lại, ban hành, thu hồi, in, tải DOCX. Quản lý phiên bản (`useDocumentVersions`). |
| Chờ tôi duyệt | `/document/pending-approval` | `pages/document-pending-approval-page.tsx` | Bảng việc chờ ký của chính người đang đăng nhập — gọi API nội bộ `ApprovalInboxTable`. Việc chưa làm xếp trên, việc đã duyệt gần đây xếp dưới, phân biệt bằng huy hiệu. Bấm vào dòng để mở văn bản đọc rồi duyệt tại đó; không có nút duyệt ngay trên dòng. |
| Danh sách Sổ văn bản | `/document/books` | `pages/document-book-page.tsx` | Ba tab theo loại sổ (đến / đi / nội bộ). Lọc theo pháp nhân (mượn `company.read` từ HR, tự tắt query khi thiếu quyền) và năm. Bộ đếm số và danh sách văn bản xem được sau khi bấm vào từng sổ. Tất cả bộ lọc ghi lên URL. |
| Mở sổ / Xem sổ (tạo mới) | `/document/books/new` | `pages/document-book-detail-page.tsx` | Form khai sổ mới: tên, mã, loại, pháp nhân, người quản lý, người xem. Sổ chưa tồn tại nên không có bộ đếm và danh sách văn bản. |
| Mở sổ / Xem sổ (chi tiết) | `/document/books/:id` | `pages/document-book-detail-page.tsx` | Ba khối: khai báo sổ → bộ đếm (chọn năm) → danh sách văn bản đã vào sổ. Cho phép sửa thông tin sổ và xóa sổ (khi không còn văn bản nào). |
| Thiết lập văn bản | `/document/settings` | `pages/document-settings-page.tsx` | Bốn tab: «Loại văn bản» (`doc_type`), «Thư viện văn bản mẫu» (`doc_template`), «Mức mật / khẩn» (`security_level`), «Đơn vị gửi nhận» (`external_party`). Mỗi tab tự ẩn khi thiếu quyền tương ứng (CR-157). Thêm/sửa mở sang trang riêng. |
| Danh sách Quy tắc đánh số | `/document/numbering-rules` | `pages/document-numbering-rules-page.tsx` | Ba tab theo chiều (đến / đi / nội bộ). Bảng `CatalogTable` hiển thị mẫu số, phạm vi loại văn bản và phạm vi sổ của mỗi quy tắc. Thêm/sửa đi sang trang riêng thay vì hộp thoại (form dài). |
| Tạo Quy tắc đánh số | `/document/numbering-rules/new` | `pages/document-numbering-rule-detail-page.tsx` | Form khai quy tắc: mẫu số, chiều văn bản, phạm vi loại và phạm vi sổ áp dụng. |
| Sửa Quy tắc đánh số | `/document/numbering-rules/:id` | `pages/document-numbering-rule-detail-page.tsx` | Cùng component với màn tạo; tải bản ghi qua `useDocumentNumberingRule(id)`. |
| Danh sách Quy tắc quan hệ | `/document/link-rules` | `pages/document-link-rules-page.tsx` | Bảng nhỏ (~15–25 dòng) khai quan hệ cha–con giữa các loại văn bản (E01). Quyết định ô quan hệ nào hiện trong form soạn thảo và loại nào bị chặn gửi duyệt khi thiếu quan hệ bắt buộc. |
| Tạo Quy tắc quan hệ | `/document/link-rules/new` | `pages/document-link-rule-detail-page.tsx` | Form khai quan hệ mới. |
| Sửa Quy tắc quan hệ | `/document/link-rules/:id` | `pages/document-link-rule-detail-page.tsx` | Cùng component với màn tạo. |
| Tạo Loại văn bản | `/document/types/new` | `pages/document-type-detail-page.tsx` | Form tạo loại văn bản: tên, mã, mức mật mặc định, bước bắt buộc. Vào được qua tab «Loại văn bản» ở màn Thiết lập. |
| Sửa Loại văn bản | `/document/types/:id` | `pages/document-type-detail-page.tsx` | Cùng component với màn tạo. |
| Tạo Văn bản mẫu | `/document/templates/new` | `pages/document-template-detail-page.tsx` | Form tạo nội dung mẫu theo loại văn bản; dùng làm điểm bắt đầu khi soạn thảo. |
| Sửa Văn bản mẫu | `/document/templates/:id` | `pages/document-template-detail-page.tsx` | Cùng component với màn tạo. |
| Tạo Đơn vị gửi nhận | `/document/partners/new` | `pages/document-partner-detail-page.tsx` | Form tạo đơn vị bên ngoài (cơ quan nhà nước, đối tác…) dùng trong trường «Đơn vị gửi / nhận» khi soạn văn bản. |
| Sửa Đơn vị gửi nhận | `/document/partners/:id` | `pages/document-partner-detail-page.tsx` | Cùng component với màn tạo. |
| Tạo Mức mật / khẩn | `/document/security-levels/new` | `pages/security-level-detail-page.tsx` | Form tạo mức mật (danh mục CRUD từ 22/08/2026, trước đó khai cứng). |
| Sửa Mức mật / khẩn | `/document/security-levels/:id` | `pages/security-level-detail-page.tsx` | Cùng component với màn tạo. |
| Bản in Văn bản | `/print/document/:id` | `pages/document-print-page.tsx` | Khai ở `app-router.tsx`, ngoài `ModuleLayout` (không menu, không thanh tiêu đề). In bản đang dùng hoặc chọn bản qua `?version=`. Bản nháp in được nhưng đóng chữ chìm «BẢN NHÁP». |

---

## Phân hệ Phê duyệt (`approval`)

Bộ máy duyệt dùng chung — **chỉ còn phần cấu hình** (21/08/2026). Màn «Việc của tôi» đã xóa; hộp việc nay nằm trong chính phân hệ của chứng từ («Chờ tôi duyệt» của Văn bản). Trang gốc `/approval` chuyển hướng sang danh sách luồng. Khóa phân hệ: `entity: 'approval_flow'`.

**Mục menu (nav):**

| Mục menu | Nhóm | Khóa quyền |
|---|---|---|
| Luồng duyệt | Cấu hình | `entity: approval_flow` |
| Bật bộ máy duyệt | Cấu hình | `entity: approval_flow` |

Tổng: **4 màn** (không tính redirect gốc).

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Danh sách Luồng duyệt | `/approval/flows` | `pages/approval-flow-list-page.tsx` | Bảng khai báo các luồng duyệt với bộ lọc `ConditionalFilter`. Hiển thị loại chứng từ, trạng thái (đang chạy / tạm dừng / chưa dùng), điều kiện kích hoạt. Có nút xóa luồng và điều hướng sang Designer. |
| Khai / Sửa Luồng duyệt | `/approval/flows/new` | `pages/approval-flow-designer-page.tsx` | Canvas kéo thả React Flow toàn màn hình. Bảng phải thu gọn được: cài đặt luồng, thêm bước, sửa bước. Mỗi bước khai người duyệt và điều kiện. |
| Sửa Luồng duyệt | `/approval/flows/:id` | `pages/approval-flow-designer-page.tsx` | Cùng component với màn tạo; tải luồng qua `useApprovalFlow(id)`. |
| Bật bộ máy duyệt | `/approval/engine` | `pages/approval-engine-page.tsx` | Danh sách loại chứng từ kèm công tắc bật/tắt bộ máy duyệt mới. Tắt một loại thì loại đó quay về đường duyệt cũ ngay, phiếu đã bắt đầu vẫn chạy tiếp cho hết (I26). Tách thành màn riêng vì đây là công tắc mức hệ thống, dùng vài lần một năm. |

---

## Phân hệ Diễn đàn (`forum`)

Bảng tin nội bộ kiểu mạng xã hội cho toàn công ty (QĐ-D6). `customLayout: true` — cả nhánh `/forum` chạy trong `ForumLayout` một cột riêng, không dùng `ModuleLayout` của các phân hệ khác. Không khai `entity`: ai đăng nhập cũng vào được; quyền xem TỪNG BÀI do backend lọc theo `audience` (doc `erp/dien-dan/01` mục 4.2), không theo RBAC grant.

**Mục menu (nav):**

| Mục menu | Khóa quyền |
|---|---|
| Bảng tin | Không khóa |
| Thông báo | Không khóa |
| Trang của tôi | Không khóa |

Tổng: **5 màn**.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Bảng tin | `/forum` | `pages/forum-feed-page.tsx` | Ô đăng bài (F3) trên cùng; cuộn vô hạn qua `IntersectionObserver`; dải tối đa 2 bài ghim đầu feed (F9a); nút nổi «Có bài viết mới» khi máy chủ có bài mới hơn màn hình. Gọi `/api/forum/posts` phân trang cursor. |
| Thông báo (ghim) | `/forum/announcements` | `pages/forum-announcements-page.tsx` | Toàn bộ bài đang được quản trị viên ghim, sắp theo mốc ghim mới → cũ (F9a/CR-199). Không phân trang vì ghim chỉ vài bài. Dùng khi cần xem nhanh tất cả thông báo còn hiệu lực (nghỉ lễ, quy định mới…). |
| Chi tiết bài viết | `/forum/posts/:id` | `pages/forum-post-page.tsx` | Đích của link chia sẻ và thông báo. Hiển thị `PostCard` và `PostComments`. Ngoài đối tượng xem (403) hoặc bài đã xóa (404) đều trả cùng một thông báo lỗi — không lộ bài có tồn tại hay không. |
| Trang cá nhân (chính mình) | `/forum/me` | `pages/forum-profile-page.tsx` | Ô đăng bài, cuộn vô hạn bài của chính mình kể cả bài bị ẩn. Dùng `useUserPosts(userId)` với `userId` từ `useAuth`. |
| Trang cá nhân (người khác) | `/forum/users/:id` | `pages/forum-profile-page.tsx` | Cùng component với màn «Trang của tôi»; chỉ hiện bài mình thuộc đối tượng xem. Tên/avatar lấy từ `location.state` của link dẫn tới hoặc từ bài đầu tiên tải về. |

---

## Phân hệ Hỗ trợ (`support`)

Phiếu hỗ trợ người dùng (ticket). Backend giới hạn theo phạm vi: người gửi chỉ thấy phiếu của mình; người có vai trò `support` (proxy FE: `can('ticket','delete')`) thấy tất cả, nhận và trả phiếu. Khóa phân hệ: `entity: 'ticket'`.

**Mục menu (nav):**

| Mục menu | Khóa quyền |
|---|---|
| Phiếu hỗ trợ | `entity: ticket` |

Tổng: **2 màn**.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Danh sách Phiếu hỗ trợ | `/support` | `pages/ticket-list-page.tsx` | Bảng `DataTable` phân trang, lọc theo trạng thái / độ ưu tiên / từ khóa. Vai trò `support` thấy thêm ô lọc «Người xử lý» (tất cả / chưa ai nhận / tôi đang xử lý) và nút «Nhận». Người gửi thông thường chỉ thấy phiếu của mình. |
| Chi tiết Phiếu hỗ trợ | `/support/tickets/:id` | `pages/ticket-detail-page.tsx` | Thread trao đổi dạng chat, đính kèm ảnh với `ImageLightbox`. Hành động: nhận phiếu, giao cho người khác, đổi trạng thái (mở / đang xử lý / đã giải quyết / đóng), trả lời. Route đặt ở `/support/tickets/:id` để link thông báo kiểu cũ `/tickets/{id}` dịch được sang (xem `notification-link.ts`). |

---

## Phân hệ Trợ lý AI (`assistant`)

Hỏi đáp trên nền gói tri thức nội bộ (AI-1). Chỉ ban lãnh đạo thấy: gác bằng `entity: 'assistant'` (backend seed `assistant.read` cho `admin / pur_manager / company_head`). Bật/tắt sâu hơn bằng cờ `AI_ENABLED` ở máy chủ; khi tắt, endpoint trả 403 và trang tự hiện thông báo chưa sẵn sàng.

**Mục menu (nav):**

| Mục menu | Khóa quyền |
|---|---|
| Trợ lý AI | `entity: assistant` |

Tổng: **1 màn**.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Trợ lý AI | `/assistant` | `pages/assistant-page.tsx` | Giao diện chat hai cột: sidebar danh sách hội thoại (trái) + khung chat (phải). Hội thoại đang mở đeo id qua `?c=`, không tách route riêng. Chọn nhà cung cấp AI qua dropdown. Hỗ trợ gợi ý trả lời (`ReplyOffers`), đính kèm tệp (`FileOffer`) và soạn nháp (`DraftOffer`). |

---

## Phân hệ Quản trị (`system`)

Cấu hình hệ thống, sao lưu CSDL, nhật ký thao tác, hộp thư gửi và nhập/xuất dữ liệu. Phân quyền tài khoản KHÔNG nằm ở đây mà ở phân hệ Nhân sự. Khóa phân hệ: `entity: 'setting'`. Tất cả màn gác thêm `manage: true` ở nav để chỉ admin hệ thống thấy.

**Mục menu (nav):**

| Mục menu | Nhóm | Khóa quyền |
|---|---|---|
| Tổng quan | — | `entity: setting, manage: true` |
| Cấu hình hệ thống | — | `entity: setting, manage: true` |
| Sao lưu CSDL | — | `entity: backup, manage: true` |
| Hộp thư gửi | — | `entity: mailbox, manage: true` |
| Nhật ký hệ thống | — | `entity: setting, manage: true` |
| Nhập dữ liệu | Nhập / Xuất dữ liệu | `entity: import` |
| Xuất dữ liệu | Nhập / Xuất dữ liệu | `entity: setting` |

Tổng: **9 màn**.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Tổng quan Quản trị | `/system` | `pages/system-dashboard-page.tsx` | Lưới lối tắt (Cấu hình hệ thống, Sao lưu CSDL, Nhật ký thao tác, Phân quyền tài khoản). Tự kiểm `can('setting','write')` và `can('backup','read')`, hiện thông báo 403 nếu không có cả hai. |
| Cấu hình hệ thống | `/system/settings` | `pages/setting-page.tsx` | Ba nhóm cài đặt chạy nóng: «Quy trình duyệt», «Email (SMTP)» và «Lưu trữ (R2/S3)». Lưu ở DB (không phải `.env`), áp dụng ngay không cần restart. Gác `setting.write`. |
| Sao lưu CSDL | `/system/backups` | `pages/backup-list-page.tsx` | Bảng danh sách bản sao lưu với thời gian, kích thước, trạng thái. Hành động: chạy sao lưu thủ công, tải file về, xóa bản cũ. Gác `backup.create/delete` tương ứng. |
| Hộp thư gửi | `/system/mailboxes` | `pages/mailbox-list-page.tsx` | Quản lý danh sách hộp thư SMTP dùng khi ban hành văn bản (từ 26/08/2026). Hai thông tin cốt lõi của mỗi hàng: địa chỉ gửi được và ai được gửi danh nghĩa. Hộp thiếu SMTP vẫn hiện nhưng tô dấu đỏ. Thêm/sửa qua `MailboxFormDialog`. |
| Nhật ký hệ thống | `/system/audit-logs` | `pages/audit-log-list-page.tsx` | Bảng nhật ký thao tác toàn hệ (`ConditionalFilter`): lọc theo thực thể, hành động, người thực hiện, khoảng thời gian. Tô màu badge theo loại hành động (create/update/delete/submitted/approved/rejected/paid). Bấm vào dòng xem chi tiết payload thay đổi. |
| Nhập dữ liệu | `/system/imports` | `pages/import-list-page.tsx` | Danh sách các lần nạp dữ liệu hàng loạt. Hỗ trợ hai chế độ: kiểm tra trước (`dry-run`) và áp dụng thật (`apply`). Nút upload mở `ImportUploadDialog`. Lọc theo module, chế độ, trạng thái, khoảng ngày. |
| Chi tiết lần nhập | `/system/imports/:id` | `pages/import-detail-page.tsx` | Kết quả chi tiết của một lần nạp: tổng dòng, dòng lỗi/cảnh báo/đã xem xét (REVIEW). Bảng phân trang theo cấp (`error/warning/review`). Hành động: áp dụng lại (nếu còn ở `dry-run`) và hoàn tác (nếu đã `apply`). |
| Xuất dữ liệu | `/system/exports` | `pages/export-list-page.tsx` | Nhật ký các lần xuất dữ liệu: thực thể, định dạng (xlsx/csv), người tạo, khoảng thời gian. Nút «Xuất mới» mở `ExportRunDialog`. Lọc theo thực thể, định dạng, người tạo, tên file. |
| Chi tiết lần xuất | `/system/exports/:id` | `pages/export-detail-page.tsx` | Thông tin file xuất: thực thể, định dạng, kích thước, ngày tạo. Nút tải file về (`useDownloadExportFile`). Badge tô màu theo định dạng (xlsx xanh / csv còn lại). |

---

## Phân hệ Giao diện (`appearance`)

Tuỳ chỉnh bảng màu cá nhân — không phải cấu hình toàn hệ. Cố ý không khai `entity`: bất kỳ tài khoản đăng nhập nào đều đổi được phần của mình. Backend gác bằng `get_current_user`, không bằng `require(...)`.

**Mục menu (nav):**

| Mục menu | Khóa quyền |
|---|---|
| Bảng màu | Không khóa |

Tổng: **1 màn**.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Giao diện / Bảng màu | `/appearance` | `pages/appearance-page.tsx` | Lưới thẻ chọn bảng màu (`ThemePresetPicker`). Lưu tại máy chủ qua `tab_user_preference` — đăng nhập ở máy khác vẫn giữ nguyên. Bấm là đổi ngay, không cần lưu. Cố ý không có công tắc Sáng/Tối/Hệ thống (vốn đã nằm trong popover ảnh đại diện, xem ghi chú 27/08/2026). |

---

## Phân hệ Hướng dẫn sử dụng (`help-center`)

Không có màn hình trong app này. Đây là một app riêng (`help-center/`, cổng 8082) dùng chung backend và tài khoản. Ô này chỉ là thẻ trên màn chọn phân hệ; bấm vào mở tab mới. Người có quyền `help_article.write` được bàn giao phiên qua hash `#t=...&r=...` để vào thẳng khu quản trị mà không đăng nhập lại. Không khai `routes`, không khai `nav`.

---

## Màn ngoài phân hệ (`app/pages` và `core/auth/pages`)

Các màn dùng chung hoặc không thuộc nghiệp vụ của riêng phân hệ nào; đứng ở `LauncherLayout` (sau đăng nhập) hoặc `AuthLayout` (trước đăng nhập). Khai tập trung ở `src/app/router/app-router.tsx`.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Chọn phân hệ (trang chủ) | `/` | `app/pages/module-launcher-page.tsx` | Lưới thẻ phân hệ sau khi đăng nhập. Một lưới duy nhất cho ba trạng thái: sẵn sàng / chưa có quyền / sắp có (`enabled: false`). Thẻ sẵn sàng xếp lên đầu. Không có menu trái. |
| Thông báo (chuyển hướng) | `/notifications` | — | Trang riêng đã bỏ (CR-215) — route chỉ còn chuyển hướng về `/me?tab=notifications` cho link cũ khỏi chết. |
| Trang cá nhân | `/me` | `app/pages/profile-page.tsx` | Năm tab: «Thông tin cá nhân» (xem hồ sơ, đổi chữ ký, đổi mật khẩu); «Việc cần làm» (chứng từ chờ duyệt của bộ máy duyệt + YCMH/YCBG/ĐMH/giao trễ/công nợ chờ xử lý — đánh dấu xong lưu server theo user vào `tab_user_task_dismiss`, ẩn cả ở chuông cảnh báo nhờ chung `task_key`, khôi phục được; CR-215); «Thông báo» (bản đầy đủ của chuông: tab Tất cả / Chưa đọc, tìm kiếm, đánh dấu đã đọc, xóa); «Yêu cầu hỗ trợ» (phiếu ticket đã gửi, ẩn khi thiếu `ticket.read`); «Giao diện» (chọn bảng màu). |
| Đăng nhập | `/login` | `core/auth/pages/login-page.tsx` | Form đăng nhập bằng tài khoản nội bộ. Màn công khai trong `AuthLayout`. |
| Quên mật khẩu | `/forgot-password` | `core/auth/pages/forgot-password-page.tsx` | Nhập email để nhận link đặt lại mật khẩu. Màn công khai. |
| Đặt lại mật khẩu | `/reset-password` | `core/auth/pages/reset-password-page.tsx` | Mở từ link trong email khôi phục, kèm `?token=`. Màn công khai. |
| Bản in Văn bản | `/print/document/:id` | `modules/document/pages/document-print-page.tsx` | Khai ở `app-router.tsx` ngoài `ModuleLayout`; chi tiết xem dòng tương ứng trong bảng Phân hệ Văn bản. |

---

## Ghi chú chung

- **Diễn đàn dùng `customLayout: true`**: toàn nhánh `/forum` chạy trong `ForumLayout` riêng — một cột kiểu bảng tin, không có sidebar nghiệp vụ của `ModuleLayout`. Router đặt `ForumLayout` như một route shell, lỗi của layout thay cả màn, lỗi của trang con chỉ thay phần `Outlet`.
- **Ba màn in ngoài khung**: `/print/document/:id`, `/print/purchase-request/:id`, `/print/purchase-order/:id` và `/print/payment-request/:id` đều khai ở `app-router.tsx` bên ngoài `ModuleLayout` — không menu, không thanh tiêu đề. Chỉ màn in của Văn bản nằm trong phạm vi tài liệu này.
- **Thẻ phân hệ mở/khóa theo `module-visibility`**: màn chọn phân hệ không gác theo `module.entity` mà gọi `canOpenModule(module, can)` — khóa khi không thấy được MỤC NÀO bên trong, không phải khi thiếu quyền trên entity gốc của phân hệ.
- **Ba mục menu không khóa trong Văn bản**: «Văn bản», «Chờ tôi duyệt» và «Sổ văn bản» đều bỏ `entity` có chủ đích — người duyệt và thành viên sổ thường không có vai trò Văn bản; gác các mục này là giấu việc của chính họ khỏi mắt họ.
- **Phê duyệt chỉ còn cấu hình** (21/08/2026): màn «Việc của tôi» (`/approval/my-tasks`) đã xóa. Muốn bật hộp việc cho phân hệ khác thì dựng màn «Chờ tôi duyệt» trong chính phân hệ đó (như Văn bản đã làm), không gọi lại màn gom chung.
- **Trợ lý AI (AI-1)**: gác bằng `entity: assistant`; bật/tắt thêm ở máy chủ bằng `AI_ENABLED`. AI-2 (RAG toàn hệ lọc theo role) chưa xây dựng.
- **Hộp thư gửi** (`/system/mailboxes`): danh mục mới từ 26/08/2026, phục vụ tính năng ban hành văn bản qua email danh nghĩa địa chỉ khác. Hộp thiếu SMTP cấu hình vẫn hiện bảng, tô dấu đỏ để người quản trị biết cần hoàn thiện.
