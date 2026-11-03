# YÊU CẦU CHỨC NĂNG — VĂN THƯ (QUẢN LÝ VĂN BẢN)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · duoc-CR-629, duoc-CR-640 (bản lưu trữ hợp đồng lao động) · CR-111, CR-112, CR-114, CR-117 (theo tài liệu chức năng) |

Tệp này là **chỉ mục yêu cầu**: mỗi chức năng tóm tắt ngắn rồi trỏ về mục chi tiết trong tài liệu cũ, chủ yếu là
[10-van-thu-van-ban.md](10-van-thu-van-ban.md) (gọi tắt là *TL10*). Danh sách 174 tính năng thiết kế ban đầu (mã N01,
A01…) vẫn ở [12-danh-sach-tinh-nang.md](12-danh-sach-tinh-nang.md); mã `CN-VT-NN` ở đây là mã mới theo khuôn, không
thay mã cũ.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Người xem văn bản (`vanban_xem`) | Đọc văn bản trong phạm vi công ty (`document.read`) |
| Người soạn văn bản (`vanban_sua`) | Tạo, sửa, in, xuất văn bản trong phạm vi công ty; quản thư mục cấp công ty; không xóa, không duyệt |
| Người duyệt (vai trò có `document.approve`, hoặc người được giao trong luồng duyệt) | Duyệt và ban hành, trả lại, từ chối; xem việc ở màn *Chờ tôi duyệt* |
| Người soạn thảo của loại *Chờ người soạn ban hành* | Bấm *Ban hành* sau khi đã ký đủ ([TL10 §14.2](10-van-thu-van-ban.md#142-duyệt-xong-không-phải-lúc-nào-cũng-ban-hành)) |
| Quản lý sổ / người xem sổ | Thành viên của sổ văn bản, là một nguồn quyền đọc / sửa ([TL10 §6.4](10-van-thu-van-ban.md#64-sổ-văn-bản)) |
| Quản trị danh mục văn thư | Loại văn bản, văn bản mẫu, quy tắc đánh số, quy tắc quan hệ, mức mật, đơn vị gửi nhận (`doc_type`, `doc_template`, `doc_numbering_rule`, `doc_link_rule`, `security_level`, `external_party`) |
| Quản lý thư mục (`doc_folder.write`) | Quản thư mục văn bản; mức Quản lý đè cả dòng Cấm trên pháp nhân với tới (`.claude/rules/document-folders-search.md`) |
| Nhân sự (`labor_contract`, `labor_contract_template`) | Sinh bản lưu trữ hợp đồng lao động; quản mẫu hợp đồng lao động |
| Pháp nhân con | Cập nhật tình trạng xử lý bản clone của mình (`document.write`) |
| Mọi nhân viên | Xem *Văn bản áp dụng cho tôi* (không cần quyền riêng) |

Mã vai trò `vanban_xem`, `vanban_sua` lấy từ `backend/app/seed.py`; các vai trò khác chưa có mã seed riêng trong tài liệu
cũ.

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**. *Chưa ghi* nghĩa là tài
liệu cũ mô tả chức năng như đã có trong mã nhưng không ghi rõ đã lên prod hay mới trên dev.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-VT-01 | Tổng quan văn thư: 5 thẻ KPI, biểu đồ ban hành, ma trận ưu tiên, việc cần xử lý ([TL10 §15](10-van-thu-van-ban.md#15-danh-sách-tìm-kiếm-tổng-quan)) | Người có `document.read` | `/document` | chưa ghi | |
| CN-VT-02 | Danh sách văn bản: tìm nhanh, bộ lọc nâng cao, phân trang ở máy chủ, bản riêng nằm dưới bản gốc, xuất Excel ([TL10 §15](10-van-thu-van-ban.md#15-danh-sách-tìm-kiếm-tổng-quan)) | Người có `document.read` | `/document/documents` | chưa ghi | D-033 |
| CN-VT-03 | Tạo văn bản ba bước: thông tin chính, phạm vi áp dụng, thông tin bổ sung; xem trước số hiệu, gợi ý văn bản trùng, kiểm tra tiên quyết ([TL10 §3](10-van-thu-van-ban.md#3-tạo-văn-bản)) | Người soạn | `/document/documents/new` | chưa ghi | CR-112 |
| CN-VT-04 | Soạn thảo trên trang giấy theo thể thức, nhập tệp Word, bản in / xuất PDF ([TL10 §4](10-van-thu-van-ban.md#4-soạn-thảo)) | Người soạn | Tab *Soạn thảo*, `/print/document/:id` | chưa ghi | D-030, D-032 |
| CN-VT-05 | Phiên bản: mở phiên bản mới (sửa lớn / nhỏ), khóa một chiều, SHA-256 nội dung ([TL10 §5](10-van-thu-van-ban.md#5-phiên-bản), [05-vong-doi-phien-ban.md](../tai-lieu-ky-thuat/05-vong-doi-phien-ban.md)) | Người soạn | Tab *Phiên bản* | chưa ghi | |
| CN-VT-06 | Số hiệu và quy tắc đánh số: hai kiểu định danh, ba lớp chống trùng, quy tắc theo chiều và độ ưu tiên ([TL10 §6.1–6.3](10-van-thu-van-ban.md#6-số-hiệu-sổ-văn-bản-quy-tắc-đánh-số)) | Hệ thống, quản trị danh mục | `/document/numbering-rules` | chưa ghi | |
| CN-VT-07 | Sổ văn bản theo chiều (đến / đi / nội bộ), bộ đếm theo năm, thành viên sổ ([TL10 §6.4](10-van-thu-van-ban.md#64-sổ-văn-bản)) | Quản lý sổ | `/document/books` | chưa ghi | |
| CN-VT-08 | Phạm vi áp dụng theo pháp nhân / phòng ban / cá nhân (bao gồm, loại trừ, chọn nhiều) và màn *Văn bản áp dụng cho tôi* ([TL10 §7](10-van-thu-van-ban.md#7-phạm-vi-áp-dụng--văn-bản-này-ai-phải-làm-theo)) | Người soạn; mọi nhân viên | Bước 2 form tạo, `/document/applied-to-me` | chưa ghi | CR-117, D-028 |
| CN-VT-09 | Quyền truy cập từng văn bản: cho phép / cấm theo người, phòng, pháp nhân, vai trò; hạn hiệu lực; thu hồi ([TL10 §8](10-van-thu-van-ban.md#8-quyền-truy-cập-theo-từng-văn-bản)) | Người soạn, người có `document.write` | Form tạo, trang chi tiết | chưa ghi | |
| CN-VT-10 | Bản lưu trữ hợp đồng lao động: tự sinh văn bản loại HDLD theo hợp đồng ở Nhân sự ([TL10 §8.1](10-van-thu-van-ban.md#81-bản-lưu-trữ-hợp-đồng-lao-động)) | Nhân sự | Hồ sơ nhân sự, trang chi tiết văn bản | chưa ghi | duoc-CR-629, duoc-CR-640 |
| CN-VT-11 | Quan hệ giữa văn bản (mười loại), quy tắc quan hệ, cấm vòng lặp, cây tài liệu, tác động dây chuyền khi ban hành ([TL10 §9](10-van-thu-van-ban.md#9-quan-hệ-giữa-văn-bản)) | Người soạn, quản trị danh mục | Tab *Quan hệ*, `/document/link-rules` | chưa ghi | |
| CN-VT-12 | Bản trích: tách một phần văn bản đã ban hành, mức mật không vượt bản gốc ([TL10 §10](10-van-thu-van-ban.md#10-bản-trích)) | Người soạn | Trang chi tiết | chưa ghi | |
| CN-VT-13 | Clone cho pháp nhân con: kế hoạch clone, bản nháp sinh sau khi gốc ban hành, màn theo dõi phiên bản ([TL10 §11](10-van-thu-van-ban.md#11-clone-cho-pháp-nhân-con)) | Người soạn; pháp nhân con | Bước 2 form tạo, trang chi tiết | chưa ghi | |
| CN-VT-14 | Ghi nhận chữ ký trên phiên bản đã khóa, ba loại chữ ký, chỉ ghi thêm ([TL10 §12](10-van-thu-van-ban.md#12-chữ-ký)) | Người ký, văn thư | Trang chi tiết | chưa ghi | |
| CN-VT-15 | Phê duyệt một bước hoặc nhiều bước qua bộ máy duyệt dùng chung; duyệt ngay trong văn bản; *Chờ tôi duyệt*; đổi người duyệt giữa chừng; luồng riêng một pháp nhân ([TL10 §13](10-van-thu-van-ban.md#13-phê-duyệt)) | Người duyệt | Tab *Phê duyệt*, `/document/pending-approval` | Có (luồng duyệt Văn bản bật trên prod từ 22/10/2026, TL10 §13.1); phần còn lại chưa ghi | CR-111, CR-114, D-029 |
| CN-VT-16 | Ban hành: hộp thoại xem trước, trạng thái *Chờ ban hành*, chọn hộp thư gửi thông báo danh nghĩa ([TL10 §14](10-van-thu-van-ban.md#14-ban-hành)) | Người duyệt, người soạn | Hộp thoại ban hành, `/system/mailboxes` | chưa ghi | |
| CN-VT-17 | Đăng thông báo lên Diễn đàn khi ban hành (bài đã ghim, link về văn bản) ([lộ trình Diễn đàn, dòng F12](../../dien-dan/plans/02-lo-trinh-phase.md#đợt-2--sau-khi-mvp-sống)) | Người ban hành | Hộp thoại ban hành | chưa ghi (mã xong 27/08/2026 theo lộ trình) | CR-200 |
| CN-VT-18 | Danh mục và thiết lập: loại văn bản, thư viện văn bản mẫu, mẫu hợp đồng lao động, mức mật / độ khẩn, đơn vị gửi nhận ([TL10 §16](10-van-thu-van-ban.md#16-danh-mục-và-thiết-lập)) | Quản trị danh mục, Nhân sự | `/document/settings` | chưa ghi | duoc-CR-629b |
| CN-VT-19 | Thư mục văn bản và tìm toàn văn (siêu dữ liệu, nội dung soạn thảo, chữ trong tệp đính kèm) | Người có `doc_folder` / `document.read` | Cây thư mục, ô tìm | chưa ghi | |
| CN-VT-20 | Hồ sơ (dossier) và loại hồ sơ | chưa có tài liệu | Đường `/api/dossiers`, `/api/dossier-types` ([api.md](../tai-lieu-ky-thuat/api.md)) | chưa ghi | |
| CN-VT-21 | Nơi nhận và xác nhận đã đọc ([TL10 §17](10-van-thu-van-ban.md#17-chưa-làm--biết-trước-để-khỏi-tìm)) | — | — | Chưa (bảng đã khai, chưa có màn) | |
| CN-VT-22 | Sổ văn bản đến (văn bản từ ngoài gửi vào, `origin = 3`) | — | — | Chưa | |
| CN-VT-23 | Văn bản pháp luật ngoài (`origin = 2`) | — | — | Chưa (cột đã khai, chưa có màn) | |
| CN-VT-24 | Trích lục chính thức (khác bản trích nội bộ) | — | — | Chưa (chờ chốt nghiệp vụ, câu B12 ở [05-vong-doi-phien-ban.md](../tai-lieu-ky-thuat/05-vong-doi-phien-ban.md)) | |
| CN-VT-25 | Lớp kiểm quyền theo mức mật | — | — | Chưa (cột có, lớp chặn chưa làm) | |
| CN-VT-26 | Yêu cầu / xin phép soạn văn bản (nhóm B của danh sách cũ) | — | — | Bỏ (đã cắt khỏi phạm vi, TL10 §17) | |

Nguồn của CN-VT-19: luật cho người viết mã `.claude/rules/document-folders-search.md` và hướng dẫn sử dụng §22–28 trong
[du-lieu/mo-ta-luong-nghiep-vu-van-ban.pdf](../du-lieu/mo-ta-luong-nghiep-vu-van-ban.pdf). Chưa có mục tài liệu chức
năng dạng markdown cho thư mục; cần viết bổ sung.

## 3. Chi tiết từng chức năng

Chỉ viết cho chức năng chính; chi tiết đầy đủ nằm ở mục TL10 được trỏ, không chép lại.

### CN-VT-03 — Tạo văn bản

- **Mục đích:** lập văn bản nháp mới kèm đủ thông tin để đi duyệt.
- **Luồng chính:** bước 1 thông tin chính → bước 2 phạm vi áp dụng → bước 3 thông tin bổ sung; tạo xong hệ ghi tuần tự
  quyền, phạm vi, kế hoạch clone ([TL10 §3](10-van-thu-van-ban.md#3-tạo-văn-bản)).
- **Luật nghiệp vụ:** xem trước số hiệu không chiếm số; kiểm tra tiên quyết chỉ cảnh báo, cổng chặn thật nằm ở gửi duyệt.
- **Dữ liệu:** bắt buộc loại văn bản, pháp nhân ban hành, phòng chủ trì, trích yếu, người chịu trách nhiệm.
- **Quyền:** `document.create`.
- **Ngoại lệ:** phần ghi sau (quyền / phạm vi / clone) hỏng thì báo đúng tab để khai lại, trang chi tiết vẫn mở.
- **Liên quan:** CN-VT-06, CN-VT-08, CN-VT-09, CN-VT-13.

### CN-VT-05 — Phiên bản

- **Mục đích:** nội dung nằm ở phiên bản; sửa văn bản đã ban hành bằng phiên bản mới hoặc văn bản sửa đổi.
- **Luồng chính:** mở phiên bản mới, chọn sửa lớn / nhỏ, khai *Sửa gì*, gửi duyệt ([TL10 §5](10-van-thu-van-ban.md#5-phiên-bản)).
- **Luật nghiệp vụ:** mỗi văn bản nhiều nhất một phiên bản đang mở (ép ở tầng dữ liệu); phiên bản đã duyệt khóa vĩnh
  viễn; quy chế lên phiên bản giữ mã, quyết định thì ra văn bản sửa đổi
  ([05-vong-doi-phien-ban.md](../tai-lieu-ky-thuat/05-vong-doi-phien-ban.md)).
- **Quyền:** `document.write`.
- **Ngoại lệ:** hai người cùng mở phiên bản mới thì một người nhận câu báo ai đang giữ bản nháp.

### CN-VT-06 — Số hiệu và quy tắc đánh số

- **Mục đích:** cấp số hiệu không trùng, không gõ tay.
- **Luật nghiệp vụ:** khóa dòng bộ đếm + ràng buộc duy nhất + cấp trong cùng giao dịch; cấp một lần, bãi bỏ hay xóa không
  trả số; quy tắc đã cấp số thì khóa và không xóa được ([TL10 §6](10-van-thu-van-ban.md#6-số-hiệu-sổ-văn-bản-quy-tắc-đánh-số)).
- **Quyền:** `doc_numbering_rule.read/write`; xem trước số hiệu cần `document.read`.

### CN-VT-09 — Quyền truy cập từng văn bản

- **Mục đích:** lớp quyền thứ ba cho các ca phạm vi không diễn đạt được.
- **Luật nghiệp vụ:** thứ tự cấm đích danh → cho phép đích danh → thành viên sổ → phạm vi vai trò; cấm thắng tất cả kể
  cả người tạo và quản trị; thu hồi là đánh dấu; không được đọc trả 404 ([TL10 §8](10-van-thu-van-ban.md#8-quyền-truy-cập-theo-từng-văn-bản)).
- **Quyền:** xem bảng chia sẻ `document.read`; chia / thu hồi `document.write`.
- **Ngoại lệ:** người đang hoặc đã có việc trong phiên duyệt luôn đọc được văn bản.

### CN-VT-15 — Phê duyệt

- **Mục đích:** đưa văn bản qua một hoặc nhiều chặng ký trước khi ban hành.
- **Luồng chính:** gửi duyệt → (một bước) *Duyệt và ban hành* / *Trả lại*; (nhiều bước) phiếu chạy từng chặng, duyệt ngay
  trong văn bản ([TL10 §13](10-van-thu-van-ban.md#13-phê-duyệt)).
- **Luật nghiệp vụ:** đang duyệt thì đóng băng nội dung (409); rút phiếu về Nháp; không có nhánh tự chọn người thay; luồng
  riêng pháp nhân được xét trước luồng dùng chung; bản clone bắt buộc có luồng riêng khi dòng Văn bản đã bật.
- **Quyền:** `document.approve` (một bước); người được giao trong luồng (nhiều bước). Menu *Chờ tôi duyệt* không gác quyền.
- **Liên quan:** bộ máy duyệt dùng chung `approval`; các ca đã kiểm ở [11-van-thu-cac-ca-da-kiem.md §1](11-van-thu-cac-ca-da-kiem.md#1-phê-duyệt).

### CN-VT-16 — Ban hành

- **Mục đích:** cấp số, khóa phiên bản, vào sổ và chạy tác động dây chuyền.
- **Luồng chính:** hộp thoại xem trước (khối chặn đỏ, khối cảnh báo vàng) → Ban hành ([TL10 §14.1](10-van-thu-van-ban.md#141-hộp-thoại-ban-hành)).
- **Luật nghiệp vụ:** loại khai *Chờ người soạn ban hành* dừng ở trạng thái *Chờ ban hành*, chỉ người soạn thảo bấm được;
  chọn hộp thư gửi danh nghĩa được cấp đích danh, chốt ở tầng dịch vụ ([TL10 §14.2–14.3](10-van-thu-van-ban.md#142-duyệt-xong-không-phải-lúc-nào-cũng-ban-hành)).
- **Quyền:** `document.approve`; hộp thư theo entity `mailbox`.
- **Liên quan:** CN-VT-11 (tác động dây chuyền), CN-VT-17 (đăng thông báo diễn đàn).

## 4. Luồng trạng thái chứng từ

Mười một trạng thái và đường đi đầy đủ ở [TL10 §2](10-van-thu-van-ban.md#2-vòng-đời-văn-bản). Tóm tắt:

```
Nháp → Đang duyệt → (Trả lại / Rút phiếu → Nháp) · (Từ chối → Đã từ chối)
                  → Duyệt → Đã duyệt / Có hiệu lực, hoặc Chờ ban hành → Ban hành
Có hiệu lực → Đã thay thế · Hết hiệu lực · Bãi bỏ · Lưu trữ
```

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | 17 câu hỏi ở [nghien-cuu/00 mục 8](../nghien-cuu/00-danh-gia-va-cau-hoi.md) — chưa rà câu nào đã chốt | chưa có | chưa có |
| 2 | Bốn câu ở [05-vong-doi-phien-ban.md mục 9](../tai-lieu-ky-thuat/05-vong-doi-phien-ban.md), trong đó B12 chặn trích lục chính thức | chưa có | chưa có |
| 3 | Viết tài liệu chức năng cho thư mục văn bản (CN-VT-19) và hồ sơ (CN-VT-20) | chưa giao | chưa có |
