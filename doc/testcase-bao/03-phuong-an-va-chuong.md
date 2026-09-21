# 03 — Chuông luồng phương án và mốc chốt lựa chọn

> **bao-CR-419** · màn chọn phương án trên phiếu yêu cầu mua hàng · tài liệu §H.11

## Đọc kỹ trước khi kiểm: hai thứ đã bị tắt và bỏ có chủ ý

Tệp này khác ba tệp kia ở chỗ **phần lớn ca kiểm là canh cho một thứ KHÔNG xảy ra**.

1. **Hai cái chuông đang TẮT.** Công tắc `OPTION_BELLS_ENABLED` trong
   `backend/app/modules/purchase_request/option_service.py` đặt là `False`. Lý do:
   người nhận chuông thứ nhất là người yêu cầu, mà người yêu cầu phần lớn còn dùng
   giao diện cũ — bên đó màn chi tiết phiếu **không có khu phương án**, nên họ sẽ
   nhận lời mời vào chọn mà không có chỗ nào để chọn.
   Vậy nên: **chuông reo mới là Không đạt**, không reo mới là đúng.

2. **Nút "Chốt xong lựa chọn" đã bỏ hẳn.** Điều kiện bấm được của nó là mọi dòng đã
   chốt hoàn thành xử lý — tức tới lúc bấm được thì người yêu cầu vừa chọn xong ngay
   bên trên, nút không hỏi thêm điều gì họ chưa trả lời. Mà quên bấm thì phiếu nằm im
   và người quên không có cách nào biết, vì màn hình y hệt lúc đã bấm.
   Vậy nên: **thấy nút đó mọc lại là Không đạt**.

Bỏ nút **chứ không bỏ mốc**: hai cột `options_chosen_at` / `options_chosen_by`,
migration `f1c3a7b52d48`, đường API và mã việc đều giữ nguyên, để chỗ *chốt mua* sắp
làm ghi vào đúng chỗ đó.

---

## Nhóm A — Canh cho cái đã bỏ

**TC-419-01 — Màn chọn phương án không có nút chốt**
1. Đăng nhập tài khoản **người yêu cầu** của một phiếu đã được thu mua chốt hết dòng.
2. Mở phiếu, vào khu chọn phương án.
- Mong đợi:
  - Chọn được phương án trên từng dòng, lưu được.
  - **Không có** nút nào tên "Chốt xong lựa chọn" hay tương tự.
  - **Không có** dòng chữ kiểu "đã chốt lúc …".
- Kết quả:

**TC-419-02 — Sinh đơn không bị mốc chặn**
1. Vẫn phiếu trên, người yêu cầu chọn xong phương án nhưng **không bấm xác nhận gì thêm**
   (vì không còn nút nào để bấm).
2. Đổi sang tài khoản thu mua, bấm **Tạo đơn**.
- Mong đợi: gom đơn chạy bình thường.
- Lý do: sinh đơn chỉ đọc cờ đã chọn của **từng dòng**; mốc chốt xong lựa chọn chưa
  bao giờ là điều kiện chặn. Ca này canh cho lời hứa "không phiếu nào kẹt vì việc bỏ nút".
- Kết quả:

---

## Nhóm B — Canh cho chuông im

**TC-419-03 — Thu mua chốt hết dòng, người yêu cầu KHÔNG nhận chuông**
1. Tài khoản thu mua: chốt hoàn thành xử lý **dòng cuối cùng** của một phiếu.
2. Đổi sang tài khoản **người yêu cầu** của phiếu đó, mở chuông thông báo.
- Mong đợi: **không có** thông báo mời vào chọn phương án.
- Kết quả:

**TC-419-04 — Người yêu cầu chọn xong, thu mua KHÔNG nhận chuông**
1. Người yêu cầu chọn phương án cho các dòng.
2. Đổi sang tài khoản **nhân sự thu mua phụ trách dòng**, mở chuông.
- Mong đợi: **không có** thông báo báo đã chọn xong.
- Kết quả:

**TC-419-05 — Không chuông nào của luồng này lọt ra chỗ khác**
1. Sau khi chạy TC-419-03 và 04, mở chuông bằng `admin`.
- Mong đợi: không thông báo nào thuộc hai loại `pr_options_ready` / `pr_options_chosen`.
- Kết quả:

---

## Nhóm C — Ca dành cho ngày bật chuông lại

Chưa chạy được hôm nay. **Chỉ chạy khi đại ca chốt bật lại**, bằng cách đổi
`OPTION_BELLS_ENABLED = True` rồi dựng lại `api`. Ghi sẵn ở đây để hôm đó khỏi nghĩ lại.

Điều kiện tiên quyết trước khi bật: **người yêu cầu phải dùng được giao diện mới**,
vì chuông thứ nhất mời họ vào một khu mà giao diện cũ không có.

**TC-419-06 — Chuông thứ nhất reo đúng một lần cho cả phiếu**
1. Phiếu có **nhiều dòng, nhiều người thu mua phụ trách**.
2. Từng người chốt hoàn thành dòng của mình, người cuối cùng chốt sau cùng.
- Mong đợi:
  - Người yêu cầu nhận **đúng một** thông báo, đúng lúc người **cuối cùng** chốt.
  - Những lần chốt trước đó không reo.
- Kết quả:

**TC-419-07 — Chuông thứ hai gửi theo dòng, một người một chuông**
1. Phiếu có một nhân sự thu mua ôm **hai dòng trở lên**.
2. Người yêu cầu chốt xong lựa chọn (qua đường API, vì nút đã bỏ).
- Mong đợi: người đó nhận **đúng một** thông báo, không phải hai.
- Kết quả:

**TC-419-08 — Không reo ngược về chính người vừa bấm**
1. Dùng một tài khoản **vừa là người yêu cầu vừa có quyền thu mua** để bấm.
- Mong đợi: người bấm **không** nhận chuông do chính mình gây ra.
- Kết quả:

**TC-419-09 — Mở lại một dòng thì xóa mốc**
1. Phiếu đã ghi mốc chốt xong lựa chọn.
2. Thu mua **mở lại một dòng** để sửa tiếp.
- Mong đợi: mốc `options_chosen_at` / `options_chosen_by` **bị xóa**.
- Lý do: mở lại một dòng là mở lại cả vòng thương lượng.
- Kết quả:

---

## Kiểm mốc bằng API (không qua giao diện)

Nút đã bỏ nên mốc không bấm được từ màn hình. Muốn kiểm mốc vẫn ghi đúng thì gọi thẳng:

```bash
docker compose exec -T api pytest test/backend/test_chuong_phuong_an_cr419.py -v
```

10 bài trong tệp đó canh cả hai chiều chuông lẫn mốc, và canh cả cho nút khỏi bị
dựng lại theo quán tính. Lần đo gần nhất (19/09/2026): xanh.
