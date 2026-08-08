# CHANGELOG — Nhật ký thay đổi

Ghi theo ngày (mới nhất trên cùng) + tổng hợp công việc theo **GitHub Issues** (repo `giabaohb99/procurement-tool`).

---

## Nhật ký theo ngày

### 2026-08-08
- **Mã hàng duy nhất trên phiếu** (CR-047): trên **Yêu cầu mua hàng** và **Đơn mua hàng**, mỗi mã hàng chỉ được đứng ở **1 dòng**. Trước đây cùng một mã đặt ở 2 dòng làm **tiến độ số lượng bị nhân đôi** (ví dụ dòng yêu cầu 2.000 mà hiện đã đặt 2.109 ở cả hai dòng, hoặc 8 dòng cùng mã trên một đơn), kéo theo trạng thái dòng và trạng thái phiếu sai. Cần mua thêm cùng một mã thì **cộng số lượng vào một dòng**. Ô mã hàng bị trùng được **tô đỏ ngay khi nhập**, bấm Lưu sẽ báo rõ mã nào trùng. Phiếu **cũ đã lỡ trùng vẫn sửa và lưu lại được** (chỉ chặn khi trùng thêm), vì dòng đã Hoàn thành/Hủy đơn không xóa được — mời phòng TM gộp tay giúp các dòng trùng còn tồn. Tạo YCMH từ Yêu cầu báo giá cũng bị chặn nếu 2 phương án của cùng một NCC gắn trùng mã VTBB.
- **Đơn giá lịch sử mua hàng** (CR-046): vá nốt phần sót của CR-041 — cột đơn giá trong **Lịch sử mua hàng** trước vẫn cắt còn 2 số lẻ, nay giữ đủ **4 số lẻ** như các màn khác (migration `c1f7b9d34e02`).
- **Kế hoạch cấu trúc dữ liệu Sản phẩm**: chốt phương án thuộc tính động cho Sản phẩm (lọc theo kích thước / chất liệu / màu… mà không phải thêm cột) — viết đủ tới mức bảng và các bước di trú tại `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md`. **Ghi nhận trước, chưa triển khai.**

### 2026-08-07
- **Hiển thị tiền** (CR-039): danh sách YCMH / ĐMH / YCTT, Công nợ, Tiến độ mua hàng, Tồn kho, Chi tiết NCC và Báo cáo hết hiện tiền lẻ kiểu `4.760.000,08 đ` — **tiền làm tròn về đồng**, **đơn giá vẫn giữ đủ 4 số lẻ** (bảng Lịch sử mua hàng trước đó cắt mất chữ số thứ 4 của đơn giá, nay đúng). Hai hàm dùng chung `fmtVND` / `fmtPrice` ở `frontend/src/utils/money.ts`; **dữ liệu trong CSDL không đổi**.
- **Trung tâm Hướng dẫn sử dụng** (CR-038): thêm script `backend/scripts/import_help_content.py` để mang nội dung từ máy soạn sang môi trường khác (chạy thử trước, `--nap` mới ghi; khớp theo tiêu đề, không xóa gì). Dev và prod đã có đủ **34 bài + 11 câu hỏi thường gặp**. Tên miền: `help.degoholding.vn` (prod), `devhelp.degoholding.vn` (dev).
- **Tài khoản** (CR-037): màn *Phân quyền tài khoản* lọc được **Chưa gán vai trò / Mồ côi**, khóa–mở khóa và xóa hẳn tài khoản mồ côi; **tài khoản còn gắn hồ sơ nhân sự thì không xóa được** kể cả khi đã khóa (báo đúng mã + tên nhân sự). Tài khoản mới không chọn vai trò thì tự nhận vai trò **Nhân sự**. Prod đã dọn 5 tài khoản mồ côi tồn từ trước.
- **Deploy prod**: đẩy trọn CR-029 → CR-039, chạy 14 migration. Phòng TM cần biết 2 thay đổi hành vi: YCMH có thêm chặng **"Đã điều phối"** (duyệt 2 bước mới tạo được ĐMH — tắt được ở Cấu hình hệ thống) và YCTT chọn được **Chuyển khoản / Tiền mặt**.
- **Lịch sử mua hàng** (CR-040): mỗi dòng ĐMH khi sang **Hoàn thành** được chụp lại thành một bản ghi lịch sử (NCC, ĐVT, SL, đơn giá, VAT, ngày). Xem ở tab **Lịch sử mua hàng** trong chi tiết Sản phẩm và chi tiết Nhà cung cấp; khi lập YCMH / ĐMH, ô Mã hàng có nút mở lịch sử để **tham chiếu giá cũ** — chọn 1 dòng thì điền sẵn ĐVT/SL/đơn giá/VAT, **không tự lưu**. Dữ liệu mua hàng cũ nạp từ file khảo sát được gắn nhãn **"Dữ liệu cũ"** (không bấm sang đơn được). Chi tiết: `04-don-mua-hang.md` mục I.
- **Đơn giá 4 số thập phân** (CR-041): các cột đơn giá (YCMH, khảo sát, ĐMH, lịch sử mua hàng…) lưu và nhập được **tối đa 4 số lẻ** thay vì 2 — phục vụ hàng đơn giá rất nhỏ. Các cột **tiền** vẫn 2 số lẻ và hiển thị làm tròn về đồng.
- **Chi tiền vào công nợ** (CR-044): sửa lỗi phân bổ tiền khi bấm "Đã chi" — trước đây tiền có thể dồn vào khoản nợ **đã tất toán** làm **công nợ âm**, còn khoản thật sự còn nợ vẫn treo nên dòng ĐMH không bao giờ đạt "Hoàn thành" (và do đó không sinh Lịch sử mua hàng). Nay chỉ rải vào khoản còn dư nợ, phần trả dư ghi vào đúng khoản của dòng phiếu. **Công nợ đã bị âm từ trước phải sửa tay.**
- **Bộ lọc lưu trên đường dẫn** (CR-045): điều kiện lọc/tìm kiếm ở các màn danh sách được ghi vào URL, nên F5 hoặc gửi link cho người khác vẫn giữ nguyên bộ lọc; nút Quay lại của trình duyệt không bị kẹt vì mỗi lần đổi lọc chỉ **thay** URL chứ không thêm bước lịch sử.
- **Sản phẩm → Đơn mua hàng**: thêm trường **Thông số kỹ thuật** (`product.specs`) cho danh mục Sản phẩm (kèm cột Import/Export CSV); tự điền vào ô **Xuất xứ / TSKT / chất liệu** của dòng hàng ĐMH — điền ngay khi chọn SP trên giao diện, và điền lại ở backend lúc lưu cho dòng MỚI còn trống (để ĐMH tạo từ PYC cũng có TSKT).
- **Trang cá nhân** `/me`: thêm thẻ **Chữ ký cá nhân** — tải ảnh chữ ký lên (`tab_user.signature`), xem trước trên nền carô, đổi / gỡ. Ảnh được **tự tách nền trắng** (tùy chọn, mặc định bật) và **thu nhỏ về tối đa 800×400px** ngay tại trình duyệt trước khi tải lên để tiết kiệm dung lượng storage.
- **In phiếu PYC** (mẫu thường): tự chèn ảnh chữ ký + họ tên cho 3 ô — "Người lập" (người yêu cầu, tra theo `requester_id`), "TP/BP đề xuất" (người bấm Duyệt bước 1), "TP/BP mua hàng" (người bấm Điều phối bước 2, theo luồng CR-034); tra người duyệt từ audit log và chỉ in từ mốc trạng thái tương ứng trở đi (phiếu bị trả về thì rỗng lại). Ô "Giám đốc" để trống ký tay. Mẫu thuế không áp dụng. Thêm dòng ghi chú "Phiếu này được in từ hệ thống thu mua".
- **Phòng ban**: dựng lại bố cục màn chi tiết theo mẫu trang Công ty (thẻ danh tính + chip, form chia nhóm ĐỊNH DANH / PHỤ TRÁCH / TỔ CHỨC); seed LOCAL nạp sẵn 9 phòng ban mẫu `PBA001`–`PBA009`.

### 2026-07-15
- **PWA & Web Push** (#85): PWA cài được (installable, cache, nhắc cập nhật) + banner mời cài; Web Push (VAPID + pywebpush) đẩy thông báo tới thiết bị; toggle banner qua `VITE_PWA_INSTALL_PROMPT`; VAPID private key chuyển sang ENV.
- **Thông báo** (#77): chia theo cấp nhân sự + bỏ gộp; bổ sung thông báo cho **YCKS** và **YCTT** (trước thiếu hẳn); PYC trả về/hủy báo người tạo; chuyển sang toast.
- **Đơn mua hàng**: tiền theo dòng + nút tạo YCTT (2 tab); ĐVVC 3 trạng thái; "Đã nhận một phần"; giới hạn xem theo NSPT; nút "Từ chối" chỉ ở bước gửi duyệt, đơn đã duyệt đổi thành "Hủy" (chặn khi có dòng Hoàn thành + bắt buộc lý do); **tự điền NSPT** (từ YCMH → người phụ trách dòng; trực tiếp → người tạo).
- **Báo cáo**: sửa số liệu (lọc `is_deleted`, chỉ đơn thật), bỏ "(Không rõ)", bỏ viết tắt, thêm lọc bộ phận, phân trang, mobile responsive.
- **Phân quyền**: Quản lý thu mua = toàn quyền nghiệp vụ (như admin, trừ user/role/setting); Admin thu mua = CRUD danh mục + đọc `proc`.
- **Tài khoản**: đặt mật khẩu tự tạo tài khoản đăng nhập; mặc định vai trò "Nhân sự (cơ bản)"; gộp/xóa vai trò legacy "Nhân viên" (STAFF).
- **Đăng nhập/Email**: đăng nhập Google (wire `VITE_GOOGLE_CLIENT_ID`); reset mật khẩu gửi được dù email chung tắt.
- **In phiếu thanh toán** (#86): điền chức vụ/bộ phận/trưởng BP + ngân hàng NCC; thu hẹp header bảng.
- **Data**: sync ngân hàng NCC dev→VPS (31 NCC); backfill NSPT 12 đơn cũ.

---

## Tổng hợp theo GitHub Issues (đã hoàn thành — CLOSED)

### Yêu cầu khảo sát / Phiếu khảo sát / Xử lý khảo sát
- #2 Fix lỗi giao diện khảo sát
- #4 Đính kèm file khảo sát: upload ngay + tách 2 bảng
- #5 Nháp khảo sát: cho lưu dòng dở dang + fix lỗi 422
- #9 Luật nút phiếu khảo sát theo trạng thái
- #11 Fix UI khảo sát: ô Duyệt lòi cột, bỏ Thành tiền, số 0, NCC
- #12 Báo cáo khảo sát (giao diện)
- #14 Chỉnh UI input + custom select trang Yêu cầu khảo sát
- #15 API xóa nhiều phiếu khảo sát (xóa mềm + migration)
- #18 Xử lý khảo sát: xóa hết options → trạng thái Đang xử lý
- #19 Chốt khảo sát bắt buộc chọn mã SP hệ thống
- #26 Phân bổ NSTM: thấy & khảo sát SP của NSTM khác
- #28 Sửa UI kết quả khảo sát
- #37 Liên kết Yêu cầu khảo sát ↔ Phiếu khảo sát
- #39 Fix loạt lỗi khảo sát sau test
- #40 Xử lý khảo sát: phân trang + giới hạn 5 phương án/sản phẩm
- #46 Yêu cầu khảo sát (module)
- #47 Thêm cột Mục đích vào bảng Yêu cầu khảo sát
- #49 Fix bug thêm option không lấy theo phân loại sản phẩm
- #50 Case NSTM xử lý khảo sát trên YCKS đã chốt hoàn thành
- #51 Case NSYC thao tác YCKS trạng thái Đã khảo sát
- #54 Case thấy YCKS trạng thái Chờ duyệt (TBP của NSYC)
- #55 Case NSTM chốt hoàn thành khảo sát
- #69 Case YCKS đã được TBP NSYC phê duyệt
- #73 Case trên phiếu khảo sát
- #74 Phiếu khảo sát bị trả lại → trạng thái "Bị trả lại"
- #76 Bảng kết quả khảo sát được duyệt: thêm cột NCC

### Yêu cầu mua hàng (PYC/YCMH)
- #3 Mã SP hệ thống: option khảo sát → Yêu cầu mua hàng
- #8 Validate gửi duyệt: tô đỏ ô thiếu + báo theo dòng
- #13 Xóa nhiều + popup xác nhận + chặn xóa
- #16 Dời phần Lưu và Gửi duyệt lên trên
- #17 Tách Lưu và Gửi duyệt riêng + option hỏi gửi duyệt
- #20 Ngày tiếp nhận: "---" → "Chưa có ngày tiếp nhận"
- #30 Kho nhận dùng mã viết tắt thay tên
- #33 Ẩn nút chọn báo giá/file đính kèm với YCMH đã duyệt
- #34 Thêm cột phân bổ khi QLTM phân bổ công việc
- #35 Nút tạo đơn mua hàng trên phiếu YCMH
- #44 Ẩn cột NSTM phụ trách với vai trò NSYC / TBP NSYC
- #45 NSPT hiển thị tên nhân sự thay cho tên đăng nhập
- #52 Case NSYC thao tác trên YCMH tạo ra từ YCKS
- #58 Nút Lưu bỏ popup gửi duyệt; bắt buộc Mã hàng + Ngày cần hàng mỗi dòng
- #63 Popup chi tiết dòng bấm Xong tự lưu phiếu
- #67 Hiển thị số đơn PO trong YCMH + điều hướng sang ĐMH
- #68 Bấm mã PYC điều hướng về Yêu cầu mua hàng tương ứng

### Đơn mua hàng (ĐMH/PO)
- #41 Sửa form in đề xuất khớp Excel + đơn PO số 0 → trống
- #42 Quy tắc chuyển trạng thái ĐMH khi điền dữ liệu
- #43 Hiển thị "Đã lưu thành công" khi lưu Đơn mua hàng
- *(2026-07-15: tiền theo dòng, tạo YCTT, ĐVVC 3 trạng thái, giới hạn NSPT, Từ chối→Hủy, tự điền NSPT — xem nhật ký ngày)*

### Form in / mẫu in
- #27 Sửa UI phiếu in Yêu cầu mua hàng
- #31 Mẫu in phiếu đề xuất mua hàng hóa/dịch vụ
- #32 Mẫu form in phiếu đề xuất mua hàng hóa/dịch vụ (có thuế)
- #56 Chỉnh form in YCMH + fix lỗi phân trang trên phiếu
- #86 Cập nhật UI phiếu in hiển thị TK ngân hàng NCC + thông tin nhân viên

### Tồn kho / Công nợ / Dashboard
- #59 Thêm filter công nợ khi nhảy từ dashboard vào
- #60 Ẩn trường tạo Yêu cầu mua hàng trên dashboard
- #61 Chỉnh filter công nợ + logic xử lý công nợ
- #64 Thêm filter cho cụm mua hàng (YCKS + YCMH + ĐMH)
- #66 Chỉnh logic + hiển thị ở tồn kho

### Danh mục / Phòng ban / Phân công
- #65 Chỉnh sửa DB cho phần phân loại
- #70 Tìm kiếm chung theo phòng ban/trưởng bộ phận; chi tiết hiện nhân sự thuộc phòng
- #71 Search phòng ban thêm trưởng phòng + hiện nhân sự thuộc phòng ở chi tiết
- #72 Trang phân công phụ trách: phân trang + sort + ghi log
- #75 Bảng sản phẩm: trường Phân loại từ text → chọn option

### Thông báo / PWA
- #77 Chức năng thông báo + trang thông báo + trang việc cần làm + trang cá nhân
- #85 Cài PWA vào hệ thống DEGO

### Nền tảng / Hệ thống / Demo / Tài liệu
- #6 Thay `alert()` bằng toast dùng chung
- #7 Modal xác nhận chung thay `confirm()`/`prompt()`
- #10 Fix lệch giờ +7 (hiển thị giờ VN)
- #21 Fix ImportError API (Attachment) + deploy VPS
- #22 Bộ tài liệu chức năng (`doc/tai-lieu-chuc-nang`)
- #23 Sửa data demo VPS: NSPT + Phân công phụ trách phòng Thu mua
- #25 Thêm mục chuyển đổi tài khoản để test & demo
- #38 Bộ tài liệu chức năng: 8 file
- #48 Click vùng tối ngoài popup → không thoát popup
- #53 Case đăng nhập vai trò Nhân viên (NSU221)
- #57 Test + fix lỗi trên yêu cầu thu mua

---

## Còn mở (OPEN — chưa hoàn thành)

- #1 Chuẩn bị data chung trên VPS + mở cổng DB cho dev vào
- #24 Phiếu khảo sát: chức vụ chưa tự fill theo nhân sự (lấy từ vai trò trên bảng nhân sự)
- #29 Tạo yêu cầu khảo sát: không nhập được tên nhà cung cấp mới
- #36 NSTM tạo đơn mua hàng: trường Mã đơn Misa không bắt buộc
- #62 Check báo cáo so với Excel (thiếu/dư thông tin) + xuất Excel báo cáo
- #78 YCKS → Xử lý khảo sát: dữ liệu lấy từ khảo sát chưa loại trừ trường hợp Không duyệt
- #79 Thêm cột trên In phiếu đề xuất mua hàng hóa/dịch vụ
- #80 Kiểm tra + fix email thông báo (để email người sử dụng)
- #81 Thiết kế lại giao diện email được gửi
- #82 Hiển thị thông tin NCC ra phiếu đề xuất khi phiếu tạo từ YCKS
- #83 Viết tài liệu phần Tồn kho, Công nợ, Yêu cầu thanh toán
- #84 Case khi NSTM tạo đơn mua hàng trên phiếu YCMH
- #87 Fix đăng nhập Google trên tool thu mua
