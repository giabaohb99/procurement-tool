# Đồng bộ vị trí nút thao tác Thu mua v1 → v2 (duoc-CR-737)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1.0 | 06/11/2026 | Anh Được | Hiệu lực | duoc-CR-737 |

Trạng thái kế hoạch: xong (trừ mục Việc nợ) · Nhánh `erp-v2` · Chỉ sửa `frontend-v2/`.

## Mục tiêu

Người dùng dời từ v1 (`frontend/`) sang v2 tìm nút ở đúng chỗ cũ. Bản v1 là chuẩn.

## Phạm vi đã chốt (06/11/2026)

1. **Chỉ đổi vị trí + thứ tự.** Giữ nguyên kiểu nút (đặc / viền) và nhãn của v2.
2. Nút v1 có mà v2 thiếu: **để đợt sau** (mục *Việc nợ* dưới đây).
3. Nút chỉ v2 có: **giữ**, xếp vào chỗ hợp lý. Riêng *Lưu duyệt dòng* trên đầu trang Phiếu khảo sát thì
   bỏ khỏi đầu trang, chỉ để trong popup dòng như v1.
4. Cụm nút của bảng dòng (Xóa đã chọn · Thêm dòng · Thêm nhiều) dời lên **góc phải tiêu đề thẻ** như v1.
5. Khổ điện thoại giữ luật cũ: nút đặc để ngoài, nút viền gom vào `⋯`.

## Khung dùng chung (đã làm)

`shared/ui/detail-page-header.tsx` có thêm prop `actions: HeaderActionList` — mảng
`{ key, node, primary?, group?: 'utility' | 'workflow' }`. Khổ rộng: nhóm `utility` · vạch ngăn · nhóm
`workflow`, đúng thứ tự khai. Khổ hẹp: nút `primary` ở ngoài, còn lại vào `⋯`. `primaryActions` /
`secondaryActions` cũ vẫn chạy cho các màn khác.

## Thứ tự đích từng màn (nhãn v2 giữ nguyên)

### Chi tiết YCMH — `purchase-request-detail-page.tsx`
- Tiện ích: In phiếu · Nhân bản · Xóa. **Hiện cả ở chế độ sửa** với phiếu đã lưu (phiếu nháp luôn mở ở
  chế độ sửa, v1 thì luôn thấy ba nút này).
- Quy trình, chế độ sửa: Lưu · Lưu & gửi duyệt · Hủy sửa.
- Quy trình, chế độ xem: Sửa · Gửi duyệt · Duyệt · Trả về · Từ chối · Duyệt điều phối · Chuyển phòng xử lý ·
  Xử lý phương án · Tạo đơn · Hoàn thành · Từ chối (muộn).
- Thẻ dòng: Xóa đã chọn (n) · Thêm SP / Thêm dòng ở góc phải tiêu đề thẻ; Thêm nhiều ở dưới bảng như v1.

### Chi tiết YCBG — `survey-request-detail-page.tsx`
- Một dãy (v1 không có vạch ngăn): Lưu · Gửi duyệt · Duyệt · Từ chối · Xử lý khảo sát · Chuyển phòng xử lý ·
  Trả về · Tạo phiếu khảo sát · Tạo YCMH · Chuyển Hoàn thành · Đã tạo N phiếu YCMH · Nhân bản · Xóa.
- Thẻ dòng: Xóa đã chọn (n) · Thêm dòng ở góc phải tiêu đề thẻ.

### Chi tiết Phiếu khảo sát — `survey-detail-page.tsx`
- Lưu · Gửi duyệt · Duyệt · Trả về · Từ chối · Xóa. Bỏ *Lưu duyệt dòng* khỏi đầu trang.
- Hai thẻ bảng: Xóa dòng đã chọn (n) · Thêm dòng · Thêm nhiều ở góc phải tiêu đề thẻ.

### Xử lý khảo sát — `survey-request-process-page.tsx` + `survey-request-process-card.tsx`
- *Lấy từ khảo sát* lên góc phải đầu trang; *Chốt hoàn thành khảo sát* ở chân, canh phải.
- Mỗi sản phẩm: bộ lọc + bảng kết quả trước, bảng option đã gắn sau.
- Bộ lọc: Phân loại · NCC · ô tìm · Về phân loại dòng · Bỏ lọc. Cột (+) gắn option là cột cuối.

### Chi tiết ĐMH — `purchase-order-detail-page.tsx`
- Tiện ích: Tạo yêu cầu thanh toán · In ▾ · Nhân bản · Hủy đơn · Xóa.
- Quy trình: Gửi duyệt · Duyệt · Trả về · Từ chối · Hủy duyệt · Hoàn thành · Mở lại · Lưu / Tạo đơn (cuối).
- Thẻ dòng hàng: Xóa đã chọn (n) · Thêm dòng ở góc phải tiêu đề thẻ.
- Thẻ chi phí thu mua: (Chốt…) · Dự toán → Tạm tính · Tạm tính → Quyết toán · Quyết toán n dòng · Quyết toán
  tất cả · Mở lại · Tạo YCTT · Thêm chi phí. Dòng chi phí: Chi tiết · Mở lại dòng · Xóa.

### Danh sách YCMH / YCBG / Phiếu khảo sát / ĐMH
Thứ tự đã khớp (Xuất Excel → Thêm). Không sửa.

## Việc nợ (v1 có, v2 thiếu — làm đợt sau)

- YCMH: nút *Tạo yêu cầu báo giá* khi phiếu bị từ chối / hủy; nút *Nhân đôi* ở từng dòng.
- ĐMH: *Thêm nhiều* dòng; *Tạm ngưng / Hủy / Tiếp tục* trong popup dòng; *Hủy đơn* chưa chặn khi có dòng đã
  hoàn thành.
- Xử lý khảo sát: tick nhiều dòng + *Thêm N dòng đã chọn làm option*.
- Danh sách: tick dòng để *Xuất Excel (n)* dòng đã chọn.
- Phiếu khảo sát: huy hiệu mã YCBG / PYC trên đầu trang.
- ĐMH: chỗ đổi trạng thái hồ sơ chứng từ (v1 ở đầu thẻ chứng từ, v2 ở thẻ thông tin).

## Lượt b (06/11/2026, chiều)

- Ẩn nút **Nhân bản** cả phiếu ở đầu trang chi tiết YCMH, YCBG, ĐMH (vẫn còn ở danh sách).
- Tô màu nút viền theo nghĩa màu v1 qua `shared/ui/action-tone.ts`: accent (chữ xanh) · warning (cam) · danger (đỏ) ·
  success (xanh lá); nút đặc giữ nguyên.

## Tiến độ

- [x] Khung `DetailPageHeader` + bài kiểm
- [x] YCMH + YCBG
- [x] ĐMH + Phiếu khảo sát + Xử lý khảo sát
- [x] typecheck · lint · vitest `src/modules/procurement` + `src/shared/ui`
- [x] Soát trên trình duyệt
