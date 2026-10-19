# Quy trình thu mua DEGO (tri thức nền)

Đây là gói tri thức MẪU để trợ lý có ngữ cảnh nghiệp vụ. Người vận hành thay/bổ sung
bằng tài liệu thật của công ty.

## Luồng nghiệp vụ chính

Yêu cầu báo giá (YCBG) -> Khảo sát giá (NCC/Sản phẩm) -> Yêu cầu mua hàng (YCMH/PYC)
-> Đơn mua hàng (ĐMH/PO) -> Nhận hàng (GR) -> Công nợ (Payables) -> Yêu cầu thanh toán (YCTT).

- **Yêu cầu mua hàng**: với luồng khảo sát, chính **người tạo YCBG** (bộ phận có nhu cầu) chọn phương án khảo sát đã duyệt trên phiếu YCBG rồi bấm tạo YCMH — không phải Thu mua; với luồng mua trực tiếp (đã biết rõ mặt hàng và giá), người có nhu cầu tạo YCMH thẳng. Trưởng phòng duyệt theo phòng ban.
- **Yêu cầu báo giá / Khảo sát**: thu mua thu thập báo giá nhiều nhà cung cấp, chọn
  phương án. Khảo sát được duyệt mới dùng để lên đơn.

## Ai liên hệ nhà cung cấp (rất quan trọng, đừng nói sai)

Ở DEGO, người có nhu cầu (nhân sự các phòng ban) **KHÔNG tự liên hệ, không tự gửi yêu cầu
báo giá cho nhà cung cấp**. Việc lấy báo giá, làm việc với NCC là của **bộ phận Thu mua**.

Luồng đúng khi ai đó cần xin báo giá / cần mua một mặt hàng:
1. Người có nhu cầu lập phiếu **Yêu cầu báo giá (YCBG)** trên hệ thống (mã phiếu bắt đầu bằng YCBG — ví dụ YCBG260826001; trên màn hình gọi là "Yêu cầu báo giá"): điền mặt hàng, số lượng, thông số/yêu cầu, mục đích.
2. Gửi duyệt; trưởng bộ phận phê duyệt. Phiếu được duyệt mới chuyển sang **bộ phận Thu mua**.
3. **Bộ phận Thu mua** là bên đi liên hệ nhà cung cấp, xin và so báo giá qua **Phiếu khảo
   sát**; khảo sát được duyệt thì các phương án hiện trên phiếu YCBG.
4. **Người tạo YCBG** xem các phương án trên phiếu, chọn phương án cho từng dòng rồi bấm tạo
   **Yêu cầu mua hàng (YCMH)**; YCMH được duyệt xong, **Thu mua** mới tạo **Đơn mua hàng**.

Nếu đã biết rõ mặt hàng và giá (không cần khảo sát) thì lập thẳng **Yêu cầu mua hàng (YCMH)**.

Vì vậy khi người dùng hỏi cách xin báo giá / cách mua một mặt hàng, trợ lý hướng họ **lập
phiếu Yêu cầu báo giá trên hệ thống và gửi duyệt để chuyển bộ phận Thu mua**, TUYỆT ĐỐI
không bảo họ tự soạn thư hay tự gửi yêu cầu báo giá cho nhà cung cấp — trừ khi chính người
hỏi thuộc bộ phận Thu mua. Cần các bước thao tác chi tiết thì tra HDSD (search_docs).
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
