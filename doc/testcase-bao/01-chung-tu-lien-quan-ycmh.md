# 01 — Thẻ *Chứng từ liên quan* trên phiếu yêu cầu mua hàng

> **bao-CR-422** · màn `/procurement/purchase-requests/<id>` trên giao diện mới.
> Tài liệu chức năng: [03-yeu-cau-mua-hang.md](../tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md) §I

## Vì sao phải kiểm tay

Thẻ này chữa hai chỗ khuất. Một, máy chủ trước đây chỉ trả **một** yêu cầu báo giá
nguồn (`limit(1)`) trong khi một phiếu gom được nhiều dòng từ nhiều yêu cầu khác
nhau — phiếu gom từ hai nguồn trở lên bị giấu mất các nguồn sau. Hai, danh sách đơn
mua hàng nấp sau một nút **tự ẩn khi chưa có đơn nào**, tức đúng lúc người dùng
muốn biết "phiếu này lập đơn chưa" thì màn hình im lặng.

Cả hai đều là lỗi **chỉ lộ ra trên dữ liệu thật**: phải có sẵn một phiếu gom từ
nhiều nguồn, và phải có một phiếu chưa lập đơn nào.

## Chuẩn bị dữ liệu

Trước khi chạy, tìm sẵn bốn phiếu (ghi mã vào đây để lần sau chạy lại cho nhanh):

| Loại phiếu | Mã phiếu | Tìm bằng cách |
|---|---|---|
| Sinh từ **một** yêu cầu báo giá | | mở một YCBG đã chốt phương án, theo đường sinh phiếu |
| Gom từ **hai yêu cầu báo giá trở lên** | | phiếu có ô *Từ yêu cầu báo giá* kèm chú *và n phiếu nữa* |
| **Lập tay**, không từ yêu cầu báo giá nào | | tạo mới thẳng ở màn Yêu cầu mua hàng |
| **Chưa có** đơn mua hàng nào | | phiếu vừa duyệt, chưa ai bấm tạo đơn |

Loại thứ hai là loại khó kiếm nhất và cũng là loại quan trọng nhất — không có nó
thì coi như chưa kiểm được thứ CR này chữa.

---

## Nhóm A — Khu *Yêu cầu báo giá nguồn*

**TC-422-01 — Phiếu sinh từ một yêu cầu báo giá**
1. Đăng nhập `admin`. Mở phiếu loại 1.
2. Cuộn xuống thẻ **Chứng từ liên quan** (nằm dưới thẻ *Phương án*).
- Mong đợi:
  - Tiêu đề khu ghi **Yêu cầu báo giá nguồn (1)**.
  - Bảng có đúng 1 dòng, đủ bốn cột: Mã YCBG · Ngày yêu cầu · Người yêu cầu · Trạng thái.
  - Mã YCBG là chữ xanh bấm được, có dấu mũi tên chéo.
- Kết quả:

**TC-422-02 — Phiếu gom từ nhiều yêu cầu báo giá (ca chính)**
1. Vẫn `admin`. Mở phiếu loại 2.
2. Đếm số dòng ở khu *Yêu cầu báo giá nguồn*.
3. Cuộn lên thẻ **Thông tin chung**, xem ô *Từ yêu cầu báo giá*.
- Mong đợi:
  - Số trong ngoặc ở tiêu đề khu **bằng đúng** số dòng trong bảng, và **lớn hơn 1**.
  - Ô *Từ yêu cầu báo giá* hiện mã phiếu nguồn ĐẦU TIÊN, kèm chú **và n phiếu nữa**,
    với `n` = số dòng trừ 1.
  - Bấm từng mã trong bảng đều sang đúng chi tiết yêu cầu báo giá đó.
- Đây là ca chứng minh lỗi `limit(1)` đã hết. Trước CR-422 bảng này chỉ có một dòng.
- Kết quả:

**TC-422-03 — Phiếu lập tay**
1. Mở phiếu loại 3.
- Mong đợi:
  - Tiêu đề khu ghi **Yêu cầu báo giá nguồn (0)**.
  - Dưới đó là câu **"Phiếu này lập tay, không sinh ra từ yêu cầu báo giá nào."**
  - **Không** phải khung trống, không phải bảng rỗng không chữ.
- Kết quả:

**TC-422-04 — Người không có quyền đọc yêu cầu báo giá**
1. Đăng nhập một tài khoản **không** có quyền `survey_request:read` (dựng bằng cách bỏ
   quyền đó ở màn Vai trò & quyền, hoặc dùng tài khoản đã có sẵn).
2. Mở phiếu loại 1 hoặc 2.
- Mong đợi:
  - Mã YCBG vẫn hiện nhưng là **chữ đen thường, không bấm được**.
  - Không có mũi tên chéo, không có liên kết.
  - Bảng vẫn đủ cột, không biến mất.
- Lý do: bày mã ra thì người ta còn hỏi được đồng nghiệp; để bấm vào rồi ăn 403 mới là tệ.
- Kết quả:

---

## Nhóm B — Khu *Đơn mua hàng đã lập*

**TC-422-05 — Phiếu chưa có đơn nào (ca chính)**
1. Đăng nhập `admin` hoặc `DEMO_MANAGER_PURCHASE`. Mở phiếu loại 4.
- Mong đợi:
  - Thẻ **Chứng từ liên quan vẫn đứng đó**, không biến mất.
  - Khu dưới ghi **Đơn mua hàng đã lập (0)**.
  - Câu **"Chưa có đơn mua hàng nào được lập từ phiếu này."**
- Đây là ca chứng minh cái nút tự ẩn đã bị thay. Trước CR-422, màn này không có chỗ nào nói.
- Kết quả:

**TC-422-06 — Phiếu đã có đơn**
1. Mở một phiếu đã lập đơn.
- Mong đợi:
  - Số trong ngoặc bằng số dòng trong bảng.
  - Đủ năm cột: Mã ĐMH · Ngày đặt · Nhà cung cấp · Tổng tiền (canh phải, có chữ `đ`) · Trạng thái.
  - Đơn chưa gán nhà cung cấp thì cột Nhà cung cấp ghi **Chưa có NCC** chứ không để trống.
  - Bấm mã ĐMH sang đúng chi tiết đơn đó.
- Kết quả:

**TC-422-07 — Người yêu cầu, không có quyền đọc đơn mua hàng**
1. Đăng nhập `DEMONV`. Mở một phiếu **của chính mình** đã có đơn.
2. Mở DevTools tab **Network**, lọc chữ `purchase-order`, rồi tải lại trang.
- Mong đợi:
  - Khu *Đơn mua hàng đã lập* **ẩn hẳn** — không tiêu đề, không câu rỗng, không bảng.
  - Khu *Yêu cầu báo giá nguồn* vẫn còn.
  - Tab Network **không có lời gọi nào tới đơn mua hàng**, và dĩ nhiên không có 403 nào.
- Ca này kiểm hai thứ một lúc: giấu đúng, và **không gọi máy chủ để ăn 403**.
  Gọi rồi nuốt lỗi thì nhìn ngoài y hệt, nên bắt buộc phải mở Network mới phân biệt được.
- Kết quả:

**TC-422-08 — Máy chủ không trả lời được danh sách đơn**
1. Mở phiếu bất kỳ bằng tài khoản có quyền đọc đơn.
2. Trong DevTools, chặn đường gọi danh sách đơn mua hàng (tab Network, chuột phải → Block request URL), tải lại.
- Mong đợi: câu **"Chưa đọc được danh sách đơn mua hàng, thử tải lại trang."**
- Mong đợi thêm: câu này **khác hẳn** câu "Chưa có đơn mua hàng nào" ở TC-422-05.
  Hỏng đường truyền và chưa có đơn là hai chuyện, không được nói giống nhau.
- Kết quả:

---

## Nhóm C — Không làm hỏng chỗ cũ

**TC-422-09 — Phạm vi dữ liệu che mất đơn (ca ĐANG SAI, biết rồi)**
1. Đăng nhập tài khoản **phạm vi hẹp** có quyền đọc đơn mua hàng nhưng không bao
   trùm phòng đã lập đơn (ví dụ vai trò `dept_proc` của phòng khác — xem bao-CR-414).
2. Mở một phiếu mà `admin` nhìn vào **thấy rõ là có đơn**.
- Mong đợi **theo mã nguồn hôm nay**: câu "Chưa có đơn mua hàng nào được lập từ phiếu này."
- Mong đợi **đúng nghiệp vụ**: phải nói được là phiếu CÓ đơn nhưng mình không được xem.
- **Ca này hiện KHÔNG ĐẠT theo nghĩa nghiệp vụ, và đó là điều đã biết, không phải lỗi mới.**
  Máy chủ lọc mất dòng theo phạm vi rồi trả mảng rỗng; giao diện nhận mảng rỗng thì
  nói đúng thứ nó nhận được. Không tầng nào sai riêng, chỉ kết luận là sai.
  Chữa được hay không phụ thuộc một quyết định chưa chốt: API có trả thêm **số đơn
  nằm ngoài phạm vi** hay không. Xem [04-pham-vi-va-bang-rong.md](04-pham-vi-va-bang-rong.md).
- Ghi nhận khi chạy (mã phiếu, tài khoản, thấy gì):

**TC-422-10 — Giao diện cũ không đổi**
1. Mở **cùng mã phiếu** ở TC-422-02 trên giao diện cũ (cổng 8080 / `devthumua`).
- Mong đợi:
  - Ô *Từ yêu cầu báo giá* vẫn hiện, vẫn đúng mã phiếu nguồn đầu tiên như trước.
  - Không chỗ nào vỡ, không chỗ nào trống ra.
- Lý do: máy chủ chỉ **thêm** khóa `survey_requests`, hai khóa cũ
  `survey_request_id` / `survey_request_code` giữ nguyên tên và nguyên nghĩa.
  Ca này canh cho lời hứa đó.
- Kết quả:

**TC-422-11 — Bản in không đổi**
1. Từ phiếu ở TC-422-02, bấm **In phiếu**.
- Mong đợi: tờ in ra vẫn có dòng yêu cầu báo giá nguồn như trước, không lỗi, không trống.
- Kết quả:

---

## Ma trận nhanh — ai thấy gì trên thẻ

| Khu | `admin` | Thu mua | `DEMONV` (người yêu cầu) | Không có quyền đọc YCBG |
|---|:--:|:--:|:--:|:--:|
| Thẻ *Chứng từ liên quan* | x | x | x | x |
| Khu *Yêu cầu báo giá nguồn* | x | x | x | x |
| Mã YCBG bấm được | x | x | x | - |
| Khu *Đơn mua hàng đã lập* | x | x | - | tùy quyền đơn |
| Mã ĐMH bấm được | x | x | - | tùy quyền đơn |
