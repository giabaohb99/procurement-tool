# Thiết kế: Nút "Lưu" vs Tự động lưu + Trạng thái tiến độ dòng ĐMH

> Tài liệu quyết định (design decision) cho: khi nào hiện nút **Lưu**, khi nào **tự động lưu**;
> và máy trạng thái tiến độ của **dòng Đơn mua hàng (ĐMH)** đồng bộ sang **Yêu cầu mua hàng (YCMH)**.

## 1. Vấn đề

Người dùng thấy **không đồng bộ**: ở màn Yêu cầu mua hàng khi phiếu *đã duyệt*, sửa trạng thái dòng thì
**tự lưu ngay, không có nút Lưu**; trong khi các chỗ khác lại có nút Lưu. Cần chốt quy tắc chung.

## 2. Nguyên tắc (đã chốt)

Phân biệt **2 loại thao tác** theo bản chất, KHÔNG gom về một kiểu:

| Loại | Cơ chế | Áp dụng ở |
|---|---|---|
| **Sửa theo LÔ** (nhiều trường/nhiều dòng, lưu 1 lần) | Nút **Lưu** (bấm mới ghi) | Mọi màn khi **Nháp / Bị trả lại**; **ĐMH khi đã duyệt** (nhập nhiều lần giao + SL nhận + đính kèm) |
| **Cập nhật 1 TRƯỜNG vận hành** | **Auto-save + toast** ngay khi đổi | Trạng thái tiến độ dòng ĐMH; trạng thái dòng / NSTM phụ trách trên YCMH khi đã duyệt |

**Lý do:** nhập liệu nhận hàng trên ĐMH (nhiều lần giao, chứng từ đính kèm) là thao tác theo lô — bắt
buộc phải có nút Lưu. Ngược lại, đổi 1 ô trạng thái là hành động đơn lẻ, auto-save cho nhanh & liền mạch.

### Kết luận đề xuất "bỏ nút Lưu ở trạng thái khác Nháp trên ĐMH"
**KHÔNG bỏ.** ĐMH sau duyệt là nơi nhập dữ liệu nhận hàng theo lô → cần nút Lưu. Chỉ **ghi chú rõ
"tự động lưu"** cạnh các ô auto-save (trạng thái dòng, NSTM) để người dùng không tưởng là lỗi.

## 3. Áp dụng từng màn

- **ĐMH (`PurchaseOrderDetail`)**
  - Nút **Lưu/Tạo**: giữ ở Nháp và ở Đã duyệt/Đang giao/Đã nhận (cho phần lần giao). Làm **to hơn** cho dễ thấy.
  - **Trạng thái tiến độ dòng**: dropdown auto-save (đã có), hiển thị cả trong **popup chi tiết dòng**.
  - Bỏ nút **Nhân bản** trong chi tiết (đã chuyển ra danh sách).
  - **NSPT phụ trách**: chỉ admin/người có quyền duyệt được gán; KHÔNG auto-gán từ YCMH.
- **YCMH (`PurchaseRequestDetail`) & YCKS (`SurveyRequestDetail`)**
  - Nháp/Bị trả lại: nút **Lưu** (như hiện tại).
  - Đã duyệt: cập nhật trạng thái dòng / NSTM = **auto-save + toast**; thêm **ghi chú nhỏ "· tự động lưu"** cạnh ô.

## 4. Máy trạng thái tiến độ dòng ĐMH (`POItem.progress_status`)

Người phụ trách chọn tay, **có điều kiện chặn (cộng dồn)**, KHÔNG tự động, đã bỏ "Chưa gửi ĐMH cho KT":

| Trạng thái | Điều kiện chuyển sang | Màu |
|---|---|---|
| Chưa đặt hàng | (khởi tạo) | xám |
| Đã đặt hàng | phiếu có **Mã Misa** | xanh dương |
| Đã nhận hàng | **SL nhận ≥ SL đặt** | teal |
| Đã gửi ĐMH cho KT | có **Số hóa đơn** | tím |
| Hoàn thành | **đã thanh toán dòng** (tạm `is_line_paid=True`, mở sau) — **điểm cuối, khóa** | xanh lá |
| Tạm ngưng | có **lý do** (lưu trạng thái cũ → *Tiếp tục* khôi phục) | vàng |
| Hủy đơn | có **lý do** — **điểm cuối, khóa** | đỏ |

## 5. Đồng bộ ĐMH → YCMH

- Liên kết qua `pr_code` + `product_code`. 1 sản phẩm có thể ở nhiều dòng ĐMH.
- Trạng thái dòng YCMH = **mức kém tiến nhất** (min) trong các dòng ĐMH đang chạy của sản phẩm đó
  (bỏ dòng Hủy/Tạm ngưng). Nếu **mọi** dòng ĐMH của sản phẩm đều Hủy → dòng YCMH = **Hủy đơn**.
- Trạng thái **phiếu** YCMH suy lại: **mọi dòng KHÔNG bị Hủy đều Hoàn thành → phiếu Hoàn thành**
  (1 dòng hủy + phần còn lại đủ = vẫn hoàn thành).
- Chạy sync khi: đổi trạng thái 1 dòng ĐMH · Hủy/Từ chối cả đơn ĐMH.
