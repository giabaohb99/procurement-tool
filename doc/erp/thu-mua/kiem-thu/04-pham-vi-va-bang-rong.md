# 04 — Phạm vi dữ liệu và câu chữ khi bảng rỗng

> Liên quan **bao-CR-414** (bậc `dept_proc`, phòng tự mua hàng) và **bao-CR-422**.
> Đây không phải kịch bản của một CR mà là **một loại lỗi**, nên để riêng một tệp.

## Loại lỗi này là gì

Máy chủ lọc bớt dòng theo phạm vi người đăng nhập rồi trả về một mảng rỗng. Giao
diện nhận mảng rỗng và nói đúng thứ nó nhận được: *"chưa có gì"*. **Không tầng nào
sai riêng — chỉ có kết luận là sai.**

Ba tình huống dưới đây hôm nay nhìn giống hệt nhau trên màn hình:

| Sự thật | Màn hình nói |
|---|---|
| Chưa ai lập chứng từ nào | "Chưa có …" |
| Có, nhưng ngoài phạm vi của bạn | "Chưa có …" |
| Có, nhưng bạn không có quyền đọc loại này | "Chưa có …" (hoặc khu đó ẩn hẳn) |

CLAUDE.md đã ghi thành luật từ duoc-CR-322: *câu "bảng rỗng" phải phân biệt rỗng vì
bộ lọc với rỗng vì chưa có gì*. Tệp này là chỗ đi soát xem luật đó được giữ tới đâu.

## Vì sao phải kiểm tay, không giao cho máy

Bài Vitest dựng thẳng component rồi **tự cấp dữ liệu cho nó**. Bài kiểm thẻ *Chứng từ
liên quan* cấp cho nó mảng rỗng rồi khẳng định nó hiện câu rỗng — bài đó **xanh dù
máy chủ có lọc mất đơn hay không**, vì máy chủ không tham gia. Bài kiểm chỉ chứng
minh được "cho vào rỗng thì hiện câu rỗng", đúng phần dễ, không đụng tới phần sai.

Bài pytest backend thì ngược lại: nó biết máy chủ trả gì, nhưng không biết màn hình
nói gì với con số đó.

Chỗ nối giữa hai tầng là chỗ lỗi nằm, và chỉ có **đăng nhập bằng tài khoản hẹp rồi
đi một vòng** mới đi qua được chỗ đó.

---

## Phần đã có máy chạy

`test/e2e/test_v2_pham_vi_giao_dien.py` — Playwright, đăng nhập thật bằng tài khoản
hẹp rồi đi một vòng. Chạy:

```bash
python -m pytest test/e2e/test_v2_pham_vi_giao_dien.py -v
```

Lần chạy đầu tiên 19/09/2026: **6 xanh · 1 bỏ qua · 54 giây**.

| Bài | Canh điều gì | Kết quả 19/09 |
|---|---|---|
| E1 | Tài khoản hẹp thấy ÍT phân hệ hơn quản trị, và không thẻ nào khóa | xanh (9 thẻ so với 15) |
| E1b | Vào phân hệ mở được thì mọi mục menu trái bấm được | xanh |
| E2 | Gõ thẳng URL ngoài quyền thì bị chặn tử tế, không trang trắng | xanh |
| E3 | Id ngoài phạm vi ra "Không tìm thấy", không khung trắng | xanh |
| E4 | Đổi phạm vi rồi đăng nhập lại thấy đổi | **bỏ qua** — bài này GHI vào dữ liệu, chờ chọn tài khoản demo dùng một lần |
| E5 | Đi một vòng 5 màn: không lỗi console, không lời gọi 403 nào bị nuốt | xanh |
| E6 | Bảng rỗng luôn kèm câu giải thích, không để ô trống | xanh |

Ba điều đo được khi chạy, đáng ghi lại:

 · Tài khoản hẹp vào **Đơn mua hàng** bị chặn **cả trang**, có câu tử tế:
   *"Tài khoản của bạn chưa được cấp quyền xem màn hình này."* — đây là cách nói ĐÚNG.
 · Tài khoản hẹp vào **Yêu cầu mua hàng** thì vào được, bảng rỗng, ghi
   *"Không tìm thấy yêu cầu mua hàng nào."* — câu này **vẫn mập mờ**.
 · Đi hết vòng **không lời gọi API nào trả 403**, tức cổng quyền chặn ở tầng đường dẫn
   trước khi gọi, chứ không phải mở trang ra rồi để máy chủ bắn lỗi.

Bẫy khi chạy: vào một đường dẫn **lần đầu** thì Vite mới dịch cả nhánh module đó, đo
được hơn 30 giây trên máy đang gánh 11 container; lần thứ hai còn khoảng 4 giây. Chạy
cả 7 bài một lượt lúc máy chưa ấm thì driver Playwright chết giữa chừng. Kẹt thì chạy
lẻ từng bài.

---

## Phần phải kiểm tay

**TC-PV-01 — Thẻ *Chứng từ liên quan* với tài khoản phạm vi hẹp (ca chính)**
1. Bằng `admin`, tìm một phiếu **có đơn mua hàng**, ghi lại mã phiếu và số đơn.
2. Đăng nhập tài khoản vai trò `dept_proc` thuộc **phòng khác** với phòng đã lập đơn.
3. Mở đúng phiếu đó, xem thẻ *Chứng từ liên quan*.
- Thấy hôm nay: **"Chưa có đơn mua hàng nào được lập từ phiếu này."**
- Đúng ra phải nói: phiếu CÓ đơn, nhưng bạn không được xem chi tiết.
- **Ca này hiện KHÔNG ĐẠT về nghiệp vụ. Đã biết, chưa chữa, không phải lỗi mới.**
- Ghi nhận (mã phiếu · số đơn admin thấy · tài khoản dùng · thấy gì):

**TC-PV-02 — Danh sách Yêu cầu mua hàng với tài khoản hẹp**
1. Đăng nhập `DEMONV`, vào `/procurement/purchase-requests`.
- Thấy hôm nay: **"Không tìm thấy yêu cầu mua hàng nào."**
- Câu này dùng chung cho cả *lọc ra không thấy* lẫn *phạm vi che mất*, nên cùng loại
  mập mờ với TC-PV-01 — chỉ nhẹ hơn, vì ở đây người dùng còn thấy thanh bộ lọc phía
  trên và tự đoán được là mình vừa lọc.
- Ghi nhận:

**TC-PV-03 — Đơn mua hàng: chặn cả trang (ca ĐẠT, giữ làm mẫu)**
1. `DEMONV` vào `/procurement/purchase-orders`.
- Mong đợi: trang 403 với câu *"Tài khoản của bạn chưa được cấp quyền xem màn hình này.
  Hãy liên hệ quản trị nếu cần."* và nút **Về màn chọn phân hệ**.
- Đây là cách nói **đúng**, giữ ca này làm mẫu để đối chiếu với TC-PV-01 và 02.
- Kết quả:

**TC-PV-04 — Không màn nào nuốt 403 trong im lặng**
1. Mở DevTools tab Network, đăng nhập `DEMONV`, đi qua: màn chọn phân hệ → Thu mua →
   Yêu cầu mua hàng → Đơn mua hàng → Nghỉ phép.
- Mong đợi: **không lời gọi nào trả 403**.
- Vì sao phải mở Network: 403 trên GET **không bật thông báo lỗi** (chỉ POST/PATCH/PUT/DELETE
  mới bật). Một màn bắn 403 rồi hiện bảng rỗng là **hoàn toàn im lặng** với người dùng;
  chỗ duy nhất nhìn thấy nó là tab Network.
- Bài E5 đã canh chỗ này tự động, ca tay chỉ dùng khi thêm màn mới chưa kịp đưa vào E5.
- Kết quả:

---

## Quyết định đang chặn

Chữa được TC-PV-01 hay không phụ thuộc một câu chưa chốt:

> **API có trả thêm số chứng từ nằm ngoài phạm vi hay không?**

 · **Có** — thẻ nói được *"Phiếu có 3 đơn, bạn không có quyền xem chi tiết"*. Bài kiểm
   khẳng định được **chữ đúng**. Đổi lại: con số đó tự nó đã tiết lộ rằng bản ghi có
   thật, tức là hở đúng thứ mà luật "trả 404 cho cả không tồn tại lẫn ngoài phạm vi"
   đang cố giấu. Phải cân xem chỗ nào đáng giấu, chỗ nào không.
 · **Không** — giữ nguyên câu hôm nay. Bài kiểm chỉ khẳng định được **có chữ**, tức
   khóa cái mập mờ lại cho khỏi tệ thêm chứ chưa chữa.

Chốt xong câu này mới viết được ca kiểm khẳng định đúng thứ cần khẳng định. Trước đó,
TC-PV-01 và TC-PV-02 để ở dạng **ghi nhận** — chạy, chép lại thấy gì, không chấm đạt.
