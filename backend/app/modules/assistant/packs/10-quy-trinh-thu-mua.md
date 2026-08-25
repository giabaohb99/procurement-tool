# Quy trình thu mua DEGO (tri thức nền)

Đây là gói tri thức MẪU để trợ lý có ngữ cảnh nghiệp vụ. Người vận hành thay/bổ sung
bằng tài liệu thật của công ty.

## Luồng nghiệp vụ chính

Yêu cầu mua hàng (YCMH/PYC) -> Khảo sát giá (NCC/Sản phẩm) -> Đơn mua hàng (ĐMH/PO)
-> Nhận hàng (GR) -> Công nợ (Payables) -> Yêu cầu thanh toán (YCTT).

- **Yêu cầu mua hàng**: người có nhu cầu lập, trưởng phòng duyệt theo phòng ban.
- **Yêu cầu báo giá / Khảo sát**: thu mua thu thập báo giá nhiều nhà cung cấp, chọn
  phương án. Khảo sát được duyệt mới dùng để lên đơn.
- **Đơn mua hàng**: chốt nhà cung cấp, số lượng, đơn giá, VAT. Có luồng duyệt riêng.
- **Nhận hàng**: ghi nhận hàng về, cập nhật tồn kho.
- **Công nợ & Thanh toán**: từ đơn/nhận hàng phát sinh công nợ; lập yêu cầu thanh toán
  để chi trả nhà cung cấp.

## Một số quy ước

- Đơn giá được phép tối đa 4 số lẻ; tiền hiển thị làm tròn về đồng.
- VAT lưu ở dạng tỷ lệ (0.08 nghĩa là 8%), không lưu số 8.
- Mỗi hợp đồng đứng tên một pháp nhân (công ty); phạm vi xem mặc định theo công ty.

## Ranh giới của trợ lý

- Trợ lý CHỈ trả lời trong phạm vi dữ liệu và tài liệu mà người hỏi được phép xem.
- Khi chưa chắc chắn hoặc thiếu dữ liệu, nói rõ là chưa đủ căn cứ, không bịa số liệu.
