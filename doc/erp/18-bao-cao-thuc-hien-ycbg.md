# Brief — Khối «Báo cáo thực hiện» trên chi tiết Yêu cầu báo giá (YCBG)

> Bản mô tả yêu cầu, viết ngày 12/09/2026. Tính năng đã dựng xong trên nhánh làm việc
> (backend + `frontend-v2`), tài liệu này ghi lại **yêu cầu và hai khung nhìn** để làm
> căn cứ nghiệm thu và phát triển tiếp. Mẫu tham chiếu: artifact «Nhập khẩu K₂SO₄ & KNO₃»
> của Phòng Thu mua (11/09/2026).

## 1. Bài toán

Một phiếu YCBG được duyệt xong không có nghĩa là thương vụ xong — phía sau nó là một
chuỗi việc kéo dài hàng tuần tới hàng tháng: xin giấy phép, ký hợp đồng, sản xuất,
vận chuyển, kiểm tra chất lượng, thông quan, về kho. Trước đây chuỗi này nằm trong
file Excel/Zalo của từng nhân sự thu mua (NSTM); người yêu cầu muốn biết «hàng của
tôi tới đâu rồi» thì phải đi hỏi.

**Khối «Báo cáo thực hiện»** đưa chuỗi việc đó lên ngay trang chi tiết YCBG
(`/procurement/survey-requests/:id`): NSTM khai và cập nhật, mọi người liên quan
tới phiếu mở ra là thấy — cùng một nguồn sự thật, có dấu vết.

## 2. Khái niệm dữ liệu

| Khái niệm | Là gì | Ghi chú |
| --- | --- | --- |
| **Nút dòng hàng** (item) | Nhãn lọc theo mặt hàng của phiếu (vd «K₂SO₄», «KNO₃») | Thêm/đổi tên/xóa tự do; khởi tạo mặc định từ các dòng của phiếu. Xóa nút KHÔNG xóa hồ sơ — hồ sơ gắn nút chuyển về «Chung» |
| **Giai đoạn** (phase) | Một chặng của tiến trình (vd «Pháp lý & Giấy phép») | Có tên + diễn giải/nơi thực hiện; khởi tạo mặc định 5 chặng nhập khẩu, sửa/thêm/xóa tự do (còn hồ sơ thì chặn xóa) |
| **Hồ sơ** (doc) | Một đầu việc/chứng từ cần hoàn thành | Thuộc đúng 1 giai đoạn; gắn 1 nút dòng hàng hoặc «Chung» (hiện ở mọi nút); có mô tả, cờ **Bắt buộc**, ô **tệp/link**, **trạng thái**, danh sách **tiên quyết** |
| **Trạng thái hồ sơ** | `0` Chưa bắt đầu · `1` Đang làm · `2` Chờ duyệt · `3` Hoàn thành | Mã SỐ theo R2/QĐ-11 (`report_constants.py`) |
| **Tiên quyết** | Các hồ sơ phải Hoàn thành trước | Hồ sơ còn tiên quyết chưa xong thì **bị khóa** (không tick ✓ được); hệ chặn vòng lặp và tự gỡ tham chiếu khi hồ sơ tiên quyết bị xóa |

## 3. Hai khung nhìn

### 3.1. Người YÊU CẦU (người lập phiếu, TBP duyệt, người được xem phiếu)

Ai **mở được phiếu YCBG** (quyền `survey_request.read` + phạm vi dữ liệu) thì xem
được khối báo cáo — **chỉ xem, không sửa**. Câu hỏi họ cần trả lời trong 10 giây:

- **«Tới đâu rồi?»** — thanh tóm tắt `x/y hồ sơ · z%` trên đầu khối; khung
  **Tiến trình** bên phải cho biết mỗi mặt hàng đang đứng ở giai đoạn nào
  (điểm nhấp nháy, đánh số theo nút dòng hàng, trùng chặng thì gộp «+n»).
- **«Đang tắc ở đâu, vì sao?»** — hồ sơ bị khóa mờ đi kèm biểu tượng 🔒, rê chuột
  đọc «Chờ: …» liệt kê đúng những hồ sơ tiên quyết chưa xong.
- **«Cái gì bắt buộc mà chưa làm?»** — tag «Bắt buộc» đỏ + pill trạng thái từng dòng;
  lọc nhanh theo nút dòng hàng / trạng thái, tìm theo mọi ô chữ (bỏ dấu được).

Người xem **không thấy**: nút Khởi tạo, mọi nút thêm/sửa/xóa, bút chì; nút ✓ bị vô
hiệu. Phiếu **chưa có báo cáo thì khối tự ẩn** với họ — không bày một thẻ trắng.
Đây là tiện ích giao diện; chốt thật nằm ở backend (mục 4).

### 3.2. Người THỰC HIỆN (NS Thu mua — cờ `process` của `survey_request`)

Toàn quyền dựng và cập nhật báo cáo, ngay trên trang chi tiết phiếu:

1. **Khởi tạo** — phiếu chưa có báo cáo: bấm «Khởi tạo báo cáo mẫu» (5 giai đoạn
   nhập khẩu + một nút cho mỗi dòng hàng của phiếu, tên lấy từ mô tả dòng) rồi sửa
   lại cho hợp, hoặc «Thêm giai đoạn» dựng tay từ đầu. Bấm lặp không nhân đôi.
2. **Quản lý nút dòng hàng** — dấu `+` để thêm; bút chì **nằm chung khung** với tên
   nút để đổi tên/xóa. Xóa nút thì hồ sơ gắn nó chuyển về «Chung».
3. **Quản lý giai đoạn** — thêm/sửa tên + diễn giải; giai đoạn còn hồ sơ thì hệ
   chặn xóa và nói rõ còn bao nhiêu.
4. **Quản lý hồ sơ** — «Thêm hồ sơ» / bút chì từng dòng mở hộp thoại (theo case
   C-01: chỉ đóng bằng Hủy/X, form dở thì hỏi xác nhận): tiêu đề*, mô tả, dòng
   hàng, giai đoạn, bắt buộc?, trạng thái, tệp/link, danh sách tiên quyết
   (tick chọn từ các hồ sơ khác của phiếu; chọn thành vòng lặp là bị chặn ngay lúc lưu).
5. **Cập nhật nhanh** — nút ✓ đầu dòng gạt Hoàn thành ↔ Đang làm không cần mở hộp
   thoại; 📎 mở thẳng hộp sửa khi chưa có tệp. Hồ sơ đang khóa thì ✓ bị vô hiệu —
   muốn mở phải xong tiên quyết trước (hoặc gỡ tiên quyết trong hộp sửa).
6. **Mọi thao tác ghi đều vào Lịch sử thao tác** của phiếu («Báo cáo: thêm hồ sơ…»,
   «Báo cáo: xóa nút…») — ai làm gì lúc nào đều tra được.

### 3.3. Hành vi dùng chung cho cả hai khung nhìn

- **Lọc & tìm**: dãy nút «Tất cả + từng dòng hàng» (hồ sơ «Chung» hiện ở mọi nút);
  select trạng thái; ô tìm kiếm khớp **theo từng từ**, không dấu, soi tiêu đề + mô tả
  + tệp + nhãn trạng thái + tên nút (gõ `kno3` khớp «KNO₃»). Rỗng-vì-bộ-lọc có câu
  riêng, không lẫn với «Chưa có hồ sơ».
- **Thu gọn**: nút gấp/mở **tất cả** trên header + chevron từng giai đoạn; giai đoạn
  gấp hiện tóm tắt `n hồ sơ · %`. Đang tìm kiếm/lọc trạng thái thì tự mở hết để
  kết quả không bị giấu.
- **Mỗi hồ sơ MỘT dòng**: ✓ · tiêu đề · tag dòng hàng · «Bắt buộc» · mô tả (cắt bớt,
  tooltip đọc đủ) · 🔒 · 📎 · pill trạng thái · ✎ (icon-only).
- **Khung Tiến trình** (bên phải, ẩn dưới `lg`): mỗi giai đoạn một điểm từ trên
  xuống; chặng xong = xanh ✓; chặng hiện tại của mỗi track nhấp nháy (`animate-ping`);
  tiến độ tính theo **nút đang lọc**, cố ý không đổi theo từ khóa đang gõ.

## 4. Phân quyền & phạm vi (chốt thật)

- **Không có khóa quyền mới** — khối nằm trong màn chi tiết YCBG nên tái dùng khóa
  `survey_request` (luật «một khóa = một màn hình», CR-157).
- ĐỌC: `require(survey_request, read)`; GHI: `require(survey_request, process)`
  — cờ suy ra «là NS Thu mua». Vì `process` không phải action có trong grant,
  **phạm vi luôn hỏi theo `read`** qua `_in_scope` của phiếu cha: ngoài phạm vi là
  404, kể cả gõ thẳng id vào URL/API.

## 5. Nền kỹ thuật (tóm tắt)

- 3 bảng con của phiếu: `tab_survey_request_report_{item,phase,doc}`
  (migration `7816572fed52`); `depends` là cột JSON danh sách id, trần 30 phần tử;
  trần số dòng 50/50/500 mỗi phiếu (chống tràn `sort_order` SMALLINT).
- API: `GET/POST /api/survey-requests/{id}/report[...]` — mọi mutation trả về
  **nguyên khối mới**, frontend thay cache một lượt (`setQueryData`, không refetch).
- Mã nguồn chính: backend `app/modules/survey_request/report_*.py`; frontend
  `frontend-v2/src/modules/procurement/components/survey-report/*`,
  logic thuần + test ở `utils/survey-report-helpers.ts`; test backend
  `test/backend/test_bao_cao_thuc_hien_ycbg.py`.

## 6. Ngoài phạm vi bản này / việc còn lại

- **Tệp đính kèm thật**: ô 📎 hiện là chữ tự do (tên tệp hoặc link Drive) — chưa nối
  kho `attachment` của hệ. Muốn upload trực tiếp thì làm đợt sau.
- Trạng thái gấp/mở giai đoạn chưa nhớ theo người dùng (`localStorage`).
- Điều kiện rẽ nhánh/thông báo (vd nhắc hạn hồ sơ, deadline từng hồ sơ) chưa có —
  artifact gốc cũng chưa khai ngày hạn cho hồ sơ.
- Cấp số CR + ghi `change-log.md` + commit: chờ chốt prefix CR của người làm.
