# Kiểm lại trên trình duyệt: nghỉ phép duoc-CR-713 → 717 (stack LOCAL)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | Agent 2 (tài liệu và kiểm thử) | Hiệu lực | duoc-CR-713, 714, 715, 716, 717 |

- **Ngày:** 03/11/2026, Asia/Ho_Chi_Minh · **Máy:** macOS, Docker Compose (api, db, erp, redis đều lên sau khi khởi động lại)
- **Ứng dụng:** http://localhost:8083 (frontend-v2) · API http://localhost:8000 · tài khoản **Dego Admin (DEGO0001)**, vai trò admin, phiên có sẵn (không phải đăng nhập lại; menu đủ mục mới)
- **Công cụ:** chrome-devtools MCP, một trang, khổ 1440×900, đo bằng `getBoundingClientRect()`; console + network soát trên từng trang
- **Không đụng dev / prod.** Không chạy pytest / vitest.

## Kết quả tóm tắt

| # | Mục | Kết quả |
|---|---|---|
| 1 | Loại nghỉ: bố cục phẳng, Mã / Tên thẳng hàng, Lưu chỉ ở tab Thông tin, nháp Hạn mức theo nhóm còn khi đổi tab | ĐẠT |
| 1b | (Thêm theo điều phối) Thêm chính sách: 2 cột trải hết bề rộng; Loại nghỉ: nhóm từ 3 ô trở lên ra 3 cột; hàng nhãn thẳng | ĐẠT |
| 2 | Tạo chính sách **TEST CR-717 E2E**, Phép năm 15 ngày, thử 12,5 và ô trống | ĐẠT |
| 3 | Phân bổ một người + xem trước + chi tiết quỹ; trang hàng loạt; dọn dữ liệu thử có tính lại | ĐẠT (có 1 lỗi nhỏ backend về nhật ký, xem L1) |
| 4 | Quỹ phép năm: tab Theo nhân sự, hộp Cấp quỹ năm, hộp Đối chiếu kết sổ | ĐẠT |
| 5 | Báo cáo Làm việc vào ngày lễ, ngày nghỉ + cột Nghỉ bù cộng thêm ở báo cáo Quỹ phép năm | ĐẠT |
| 6 | Nghỉ bù: danh sách, chi tiết, chặn ngày tương lai | ĐẠT |
| 7 | Cài đặt nhân sự: 3 tab, không lặp tiêu đề, có Lưu | ĐẠT |
| 8 | Ngày cấm nghỉ: danh sách | ĐẠT |
| 9 | Console + API 4xx/5xx | ĐẠT (chỉ 1 lỗi 404 vô hại sau khi xóa, xem L2) |

## Chi tiết từng mục

### 1. Loại nghỉ (/hr/leave-types/7, **Nghỉ bù**)

- Bố cục phẳng: các nhóm **Quỹ phép và lương**, **Điều kiện áp dụng**, **Số dư cuối năm** là đoạn có tiêu đề gập được, không bọc thẻ; form không tràn ngang (`scrollWidth - clientWidth = 0`).
- Hàng đầu: ô chỉ xem **Mã loại nghỉ** (có nút (i) **Xem giải thích**) top = 199px, cao 36px; ô **Tên loại nghỉ** top = 199px, cao 36px → lệch 0px.
- Nút **Lưu** / **Xóa** ở đầu trang chỉ có ở tab **Thông tin**; sang **Bậc thâm niên** và **Hạn mức theo nhóm** thì mất (kiểm bằng DOM).
- Tab **Hạn mức theo nhóm**: chọn Hình thức nhân viên = **Thử việc**, 12 ngày → **Thêm dòng** → hiện dòng nháp + **Có thay đổi chưa lưu**. Sang **Thông tin**, rồi **Bậc thâm niên**, rồi quay lại → dòng **Hình thức nhân viên: Thử việc · 12 ngày/năm** vẫn còn. Không bấm **Lưu hạn mức** (rời trang bỏ nháp, không ghi gì vào DB).

### 1b. Kiểm thêm theo điều phối (bố cục `shared/crud` mới)

Tải lại không dùng bộ nhớ đệm trước khi đo.

- **/hr/leave-policies/new:** **Mã chính sách** left 280 / right 836 (rộng 556); **Tên chính sách** left 860 / right 1416 (rộng 556); **Ghi chú** left 280 / right 1416 (rộng 1136). Mép phải Tên = mép phải Ghi chú, lệch 0px. Hai ô cùng top 159px; hai nhãn cùng top 136px.
- **/hr/leave-types/7:**
  - Nhóm **Quỹ phép và lương** (3 ô): Hạn mức mỗi năm 280–643, Cách cấp quỹ 667–1029, Cho ứng phép tối đa 1053–1416 → 3 cột, mỗi cột rộng 363, ô cùng top 406, nhãn cùng top 383.
  - Nhóm **Điều kiện áp dụng** (3 ô): Áp dụng cho giới tính / Tối đa mỗi lần nghỉ / Dùng được sau → 3 cột như trên, ô cùng top 567, nhãn cùng top 544.
  - Hàng đầu (2 ô): Mã loại nghỉ 280–836, Tên loại nghỉ 860–1416; ô cùng top 199, nhãn cùng top 176.
  - **Cách xử lý số dư** (nhóm có 1 ô) rộng nửa trang 280–836; **Ghi chú** trải hết 280–1416. Mép phải mọi hàng là 1416.

### 2. Chính sách nghỉ phép

- **Thêm chính sách** → mã `TEST-CR717-E2E`, tên **TEST CR-717 E2E** → **Tạo chính sách** → báo **Đã thêm chính sách nghỉ phép**, chuyển sang /hr/leave-policies/16 với 3 tab **Thông tin / Loại nghỉ & số ngày / Đang phân bổ**.
- Tab **Loại nghỉ & số ngày**: xóa trắng ô **Số ngày mỗi năm** rồi **Thêm dòng** → báo lỗi ngay dưới ô **Nhập số ngày (VD 12 hoặc 12,5).**, không thêm dòng. Gõ `12,5` → dòng **Phép năm 12,5 ngày/năm** (nhận dấu phẩy). Sửa thành 15 → **Thêm dòng** ghi đè → **Lưu số ngày** → báo **Đã lưu loại nghỉ & số ngày của chính sách**, dòng **Phép năm 15 ngày/năm**.

### 3. Phân bổ chính sách

- **Phân bổ** (một người): Nhân sự = **Nguyễn Nhân Viên (DEMONV)**, chính sách TEST CR-717 E2E, tick **Tính lại hạn mức năm nay cho quỹ đã cấp** (mặc định bật).
  - Xem trước hiện ngay: **Chính sách hiện tại: Chưa có**; Phép năm **12 → 12,5** (từ 03/11). Đổi Từ ngày sang **01/07/2026** → **12 → 13,5** (đúng 12 + 3 × 6/12).
  - Bấm **Phân bổ** → báo **Đã phân bổ chính sách · Quỹ phép năm nay: tính lại 1 dòng quỹ.**; dòng #23 **Đang hiệu lực**.
- Chi tiết quỹ /hr/leave-balances/236 (DEMONV, Phép năm 2026): **Chính sách đang áp hôm nay: TEST CR-717 E2E (01/07/2026 → Không thời hạn) — khai 15 ngày/năm cho loại nghỉ này.** Hạn mức 13.5, Lịch sử thao tác ghi **hạn mức Phép năm năm 2026 12 → 13.5 ngày**.
- **Phân bổ hàng loạt** (/hr/leave-policy-assignments/bulk):
  - Ô **Pháp nhân** có đủ danh sách; chọn pháp nhân xong thì ô **Phòng ban** có 18 phòng.
  - **Xem danh sách** bị khóa cho tới khi chọn chính sách (kèm dòng nhắc **Chọn chính sách.**).
  - Bỏ tick **Chỉ người chưa có chính sách hiệu lực hôm nay**, chọn pháp nhân DEGO HOLDING (id 1) → **145 người khớp · Phân bổ 144 người**. Đúng 1 dòng bị khóa ô chọn: DEMONV, cột lý do ghi **Nhân sự Nguyễn Nhân Viên đã có chính sách TEST CR-717 E2E từ 01/07/2026 đến không thời hạn.** Không bấm phân bổ hàng loạt.
- Dọn dữ liệu:
  - Mở hộp **Kết thúc** (có ô tick tính lại, bật sẵn) rồi **Hủy**.
  - **Xóa** → hộp **Xóa phân bổ chính sách?** có tick tính lại (bật sẵn) → **Xóa phân bổ** → báo **Đã xóa phân bổ · Quỹ phép năm nay: tính lại 1 dòng quỹ.**
  - Quỹ 236 trở về 12, ghi lịch sử **13.5 → 12 ngày**, dòng **Hôm nay không có chính sách nghỉ phép nào đang áp**.
  - Xóa chính sách 16 → **Đã xóa chính sách nghỉ phép**, danh sách chính sách trống như lúc đầu.

### 4. Quỹ phép năm (/hr/leave-balances)

- Tab **Theo nhân sự** (`?view=people`): bảng ma trận có cột Mã NV / Họ tên / Phòng ban / Phép năm / Nghỉ bù / Tổng còn lại, có lọc phòng ban, Đang làm, Năm 2026, nút **Xuất Excel**.
- **Cấp quỹ năm 2026**: hộp mở được, có lọc Loại nghỉ / Pháp nhân / Phòng ban / Hình thức nhân viên / Cấp bậc. Đã bấm **Hủy**, không cấp quỹ.
- **Đối chiếu kết sổ 2025**: hộp rộng 1024px (208–1232 trên khung 1440). `scrollWidth` 1022 = `clientWidth` 1022, không phần tử con nào lòi ra ngoài mép hộp. Lưu ý: năm 2025 local chưa kết sổ nên bảng 0 dòng; độ vừa khít mới đo với bảng rỗng.

### 5. Báo cáo

- **/report/holiday-work**: có mô tả, **Xem bảng chi tiết**, **Xuất Excel**; lọc phòng ban / loại ngày / kỳ / công ty; 4 thẻ KPI (Lượt đi làm 1, Số người 1, Trong đó ngày lễ 0, Ngày nghỉ bù được duyệt 1 ngày), biểu đồ xu hướng, bảng theo phòng ban.
  - Bấm **Gồm phiếu chờ duyệt** → URL thêm `include_pending=1`, gọi lại `/api/holiday-work-report/summary?include_pending=1&...` [200].
  - Số không đổi vì local không có phiếu chờ.
- **/report/leave-balance**: bảng **Chi tiết theo Loại nghỉ** có cột **Nghỉ bù cộng thêm**, tổng 1 ngày (Phép năm 0 ngày).

### 6. Nghỉ bù

- Danh sách /hr/leave-comp-requests: có **Lập phiếu nghỉ bù**, lọc **Của tôi** / trạng thái; dòng NB001 (Dego Admin, 01/11/2026, 1 ngày, Đã duyệt).
- Chi tiết /hr/leave-comp-requests/1: thông tin, nút **Hủy phiếu**, luồng duyệt 2 bước.
- Phiếu mới: chọn Ngày đã đi làm = **05/11/2026** (tương lai), điền lý do, bấm **Gửi duyệt** → lỗi ngay dưới ô **Ngày đi làm không được ở tương lai.** Không có lượt POST nào, không tạo phiếu.

### 7. Cài đặt nhân sự (/hr/settings)

- Breadcrumb **Nhân sự › Master › Cài đặt nhân sự**, chỉ một `h1` **Cài đặt nhân sự**; chữ này xuất hiện đúng 1 lần trong vùng nội dung → không lặp tiêu đề. Breadcrumb cuối trùng `h1` giống mẫu các trang khác (Phân bổ chính sách).
- 3 tab **Nhân viên / Nghỉ phép / Hợp đồng lao động** đều hiện nội dung; nút **Lưu** có ở cả 3 tab.
- Không sửa cài đặt nào.

### 8. Ngày cấm nghỉ (/hr/leave-blocks)

- Danh sách tải được (local chưa có khoảng nào, có câu nhắc rỗng); `/api/leave-block-periods` [200].

### 9. Console và API

- Console: trên mọi trang chỉ có cảnh báo `No HydrateFallback element provided...` của React Router lúc tải cả trang (bản dev, vô hại). Không có lỗi `error`.
- API: mọi lượt gọi trong các bước trên đều 200, trừ L2.

## Lỗi tìm thấy

### L1 (lỗi nhỏ, backend: Agent 4) Nhật ký của chính sách nghỉ phép lẫn sang trang Loại nghỉ cùng số id

- **Màn:** /hr/leave-types/2 (**Nghỉ không lương**), khối **Hoạt động**.
- **Tái hiện:** tạo, sửa rồi xóa một chính sách nghỉ phép có id trùng id một loại nghỉ (local: chính sách #2 **TEST CR-717 Cấp quản lý** tạo / xóa sáng 03/11). Mở /hr/leave-types/2.
- **Kỳ vọng:** khối Hoạt động của loại nghỉ chỉ có thao tác trên loại nghỉ đó.
- **Thực tế:** khối Hoạt động hiện **Dego Admin — Xóa · 4 giờ trước**, **đã chỉnh sửa** ×2, **đã tạo loại nghỉ**. Cả bốn dòng thật ra là của chính sách #2; loại nghỉ Nghỉ không lương chưa hề bị xóa. API `GET /api/audit-logs?entity=leave_type&entity_id=2` trả 4 dòng, trong đó có message **Cập nhật dòng của chính sách "TEST CR-717 Cấp quản lý"**. Chiều ngược lại cũng sai: trang chính sách gọi `audit-logs?entity=leave_type&entity_id=<id chính sách>`, nên sẽ hiện nhật ký của loại nghỉ cùng số.
- **Gốc:** `policy_controller.py` đặt `ENTITY = "leave_type"`, và `make_crud_router(prefix, entity, ...)` (`core/crud.py` dòng 128/146/160) dùng **cùng** tham số `entity` cho cả gác quyền lẫn `record(...)` nhật ký. **Ngày cấm nghỉ** (`block_period_router`, `catalog_controller.py`) cũng dựng với `"leave_type"`, nên có thể lẫn y như vậy.
- **Ảnh:** `doc/erp/hrm/plans/261103-nghi-phep-du-nhu-nexterp-duoc-cr-717/reports/e2e-retest-261103-loai-nghi-2-hoat-dong-lan-chinh-sach.jpeg`
- **Hướng gợi ý:** tách khóa nhật ký (vd `leave_policy`, `leave_block_period`) khỏi khóa quyền; frontend gọi `audit-logs` theo khóa mới.

### L2 (lỗi nhỏ, giao diện: Agent 3) Gọi lại chi tiết chính sách sau khi xóa ra 404

- **Màn:** /hr/leave-policies/16 → **Xóa** → xác nhận.
- **Thực tế:** sau `DELETE /api/leave-policies/16` [200] còn một lượt `GET /api/leave-policies/16` [404] trước khi chuyển về danh sách. Trên màn không hiện gì lạ.
- **Kỳ vọng:** bỏ hẳn (`removeQueries`) truy vấn chi tiết thay vì cho nó làm mới (invalidate) sau khi xóa, để không phát sinh 404 trong nhật ký.

### Quan sát nhỏ (chưa xếp là lỗi, để chủ khu cân nhắc)

1. **Định dạng số không đồng nhất:** xem trước phân bổ ghi `12,5` / `13,5` (dấu phẩy kiểu Việt). Danh sách Quỹ phép năm, trang chi tiết quỹ và Lịch sử thao tác lại ghi `13.5`, `5.5` (dấu chấm). Báo cáo ghi `3.076 ngày` (chấm phân nghìn).
2. **Lập phiếu nghỉ bù:** ô **Người nghỉ** hiện tạm số id `2` khoảng 1–2 giây trong lúc tải danh sách nhân sự, rồi mới thành **Dego Admin (DEGO0001)**.
3. **Lập phiếu nghỉ bù:** lịch vẫn cho chọn ngày tương lai (chỉ chặn lúc gửi), dù dòng gợi ý ghi **không chọn ngày tương lai**. Có thể khóa ngày sau hôm nay ngay trên lịch.
4. **Báo cáo ngày lễ:** khi bật **Gồm phiếu chờ duyệt**, thẻ KPI vẫn mang tên **Ngày nghỉ bù được duyệt**.
5. **Ô chọn loại nghỉ ở tab Loại nghỉ & số ngày** chỉ có **Phép năm**, dù **Nghỉ bù** cũng bật **Trừ vào quỹ phép năm**. Có thể là cố ý (loại nhận ngày nghỉ bù), cần chủ khu xác nhận.
6. **Dữ liệu local:** ô Pháp nhân có hai dòng **CÔNG TY TNHH DEGO HOLDING** (id 17 không có nhân sự nào; id 1 có 145 người). Đây là dữ liệu, không phải lỗi mã.

## Dữ liệu thử đã dọn

- Chính sách #16 TEST-CR717-E2E: đã xóa.
- Phân bổ #23 (DEMONV): đã xóa, có tính lại; quỹ Phép năm 2026 của DEMONV về lại 12.
- Không cấp quỹ, không kết sổ, không đổi cài đặt; nháp hạn mức theo nhóm của loại nghỉ 7 không lưu.
- Còn lại trong DB: các dòng nhật ký `tab_audit_log` sinh ra trong lúc thử (bình thường).

## Câu hỏi còn mở

- Quan sát 5: chính sách nghỉ phép có cố ý loại **Nghỉ bù** khỏi danh sách loại nghỉ không?
- Ô **Đối chiếu kết sổ** mới đo với bảng rỗng. Muốn chắc về tràn ngang khi có dữ liệu thì cần một bản sao DB đã kết sổ 2025 (không làm ở local hiện tại).

**Status:** DONE_WITH_CONCERNS
**Summary:** Cả 9 mục (và phần đo bố cục điều phối giao thêm) đều ĐẠT trên local. Có 2 lỗi nhỏ: L1 backend, nhật ký chính sách / ngày cấm nghỉ ghi chung khóa `leave_type` nên lẫn sang trang Loại nghỉ cùng id; L2 giao diện, một lượt GET 404 sau khi xóa chính sách. Không có lỗi chặn.
