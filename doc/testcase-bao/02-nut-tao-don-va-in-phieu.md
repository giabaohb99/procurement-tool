# 02 — Một nút *Tạo đơn*, một nút *In phiếu*

> **bao-CR-420** (bỏ hai cái sổ xuống, chọn đường theo vai trò) ·
> **bao-CR-421** (hộp hỏi trước khi gom thêm đơn)
> Màn `/procurement/purchase-requests/<id>` · tài liệu §H.6, §H.10.6

## Điều cốt lõi phải giữ

Nhãn nút là **"Tạo đơn"** và **"In phiếu"** — *giống hệt nhau với mọi vai trò*.
Đường chạy bên trong đổi theo vai trò, nhưng **chữ trên nút thì không**. Nếu thấy
nút đổi tên theo người đăng nhập thì ca đó **Không đạt**, kể cả khi chức năng chạy
đúng: hai người ngồi cạnh nhau mà mô tả cùng một nút bằng hai cái tên thì gọi điện
chỉ việc cho nhau không ai hiểu ai.

---

## Nhóm A — Nút *Tạo đơn*

**TC-420-01 — Chỉ còn một nút, không sổ xuống**
1. Đăng nhập `DEMO_MANAGER_PURCHASE`. Mở một phiếu đang mở, đã có dòng chốt phương án.
2. Nhìn thanh lệnh đầu trang.
- Mong đợi:
  - Có đúng **một** nút chữ **Tạo đơn**.
  - Bấm vào là **ra thẳng hộp xác nhận**, không xổ ra danh sách để chọn tiếp.
  - Nhãn vẫn là "Tạo đơn" khi thu hẹp cửa sổ trình duyệt (không đổi theo bề ngang màn hình).
- Kết quả:

**TC-420-02 — Phiếu đã chốt phương án thì đi đường gom**
1. Vẫn phiếu trên (có dòng chốt hoàn thành xử lý, còn dòng chưa nằm trên đơn nào).
2. Bấm **Tạo đơn**.
- Mong đợi: hộp xác nhận tiêu đề **"Tạo đơn mua hàng theo phương án"**, nút đồng ý ghi **"Tạo đơn nháp"**.
- Mong đợi thêm: nội dung nói rõ sẽ gom theo nhà cung cấp, dòng chưa có nhà cung cấp
  gom vào một đơn riêng, dòng đã nằm trên đơn sẽ bỏ qua.
- Đồng ý rồi kiểm: đơn sinh ra **có sẵn nhà cung cấp và giá đã khảo sát**.
- Đây là chỗ thứ tự ưu tiên có nghĩa: lập tay lúc này sẽ ra đơn thiếu đúng phần việc
  nhân sự thu mua vừa làm xong.
- Kết quả:

**TC-420-03 — Phiếu chưa ai chốt phương án thì đi đường lập tay**
1. Mở một phiếu đã duyệt nhưng **chưa dòng nào chốt hoàn thành xử lý phương án**.
2. Bấm **Tạo đơn**.
- Mong đợi:
  - Nhãn nút vẫn là **Tạo đơn** (không đổi chữ).
  - Bấm vào là sang màn lập đơn mua hàng, với các dòng còn phải mua điền sẵn.
- Kết quả:

**TC-420-04 — Hết dòng gom được thì nút biến mất**
1. Lấy một phiếu mà **mọi dòng đã nằm trên đơn mua hàng** và cũng không còn dòng nào chưa đặt đủ.
- Mong đợi: **không có nút Tạo đơn** trên thanh lệnh.
- Mong đợi: không có cách nào bấm ra lỗi 400 "Không còn dòng nào tạo được đơn".
- Lý do: khách từng tưởng đó là lỗi trong khi đơn đã tạo xong rồi (15/09).
- Kết quả:

**TC-420-05 — Người yêu cầu không thấy nút**
1. Đăng nhập `DEMONV` (không có `purchase_order:create`). Mở phiếu của chính mình.
- Mong đợi: **không có nút Tạo đơn**, ở mọi trạng thái phiếu.
- Kết quả:

---

## Nhóm B — Hộp hỏi khi phiếu đã có đơn (bao-CR-421)

**TC-421-01 — Phiếu đã có đơn thì hộp phải nói ra (ca chính)**
1. `DEMO_MANAGER_PURCHASE`, mở một phiếu **đã có 1–3 đơn mua hàng** và vẫn còn dòng gom được.
2. Bấm **Tạo đơn**.
- Mong đợi:
  - Tiêu đề hộp đổi thành **"Phiếu này đã có đơn mua hàng"** (khác hẳn TC-420-02).
  - Câu đầu ghi đúng số đơn: *"Phiếu <mã> đã có n đơn mua hàng: <mã đơn 1>, <mã đơn 2>…"*
  - Kể **đúng các mã đơn đang có**, đối chiếu với thẻ *Chứng từ liên quan* bên dưới.
  - Có câu trấn an: chỉ gom thêm dòng CHƯA nằm trên đơn nào, đơn đang có không bị đụng.
  - Câu hỏi cuối: *"Vẫn tạo thêm đơn nháp cho phiếu này?"*
  - Nút đồng ý ghi **"Tạo thêm đơn nháp"** (không phải "Tạo đơn nháp").
- Vì sao cần: nút nằm ngay đầu trang, bấm một cái là ra đơn nháp. Người thu mua mở
  lại phiếu cũ rất dễ bấm thêm lần nữa mà không nhớ hôm trước đã gom rồi.
- Kết quả:

**TC-421-02 — Phiếu có trên ba đơn thì đếm gộp**
1. Tìm hoặc dựng một phiếu có **từ 4 đơn trở lên**. Bấm **Tạo đơn**.
- Mong đợi: kể **đúng ba mã đầu**, rồi **"và n đơn khác"** với `n` = tổng trừ 3.
- Lý do: phiếu gom nhiều nhà cung cấp ra cả chục đơn, kể hết thì câu dài hơn cả hộp.
- Kết quả:

**TC-421-03 — Phiếu chưa có đơn thì giữ nguyên câu cũ**
1. Mở phiếu chưa lập đơn nào, bấm **Tạo đơn**.
- Mong đợi: đúng hộp ở TC-420-02, **không** có chữ "đã có đơn" nào.
- Kết quả:

**TC-421-04 — Bấm khi danh sách đơn chưa về**
1. Mở phiếu đã có đơn rồi bấm **Tạo đơn** **ngay lập tức**, đừng chờ trang vẽ xong.
- Mong đợi: hộp rơi về câu cũ (TC-420-02) — **nút vẫn bấm được, không bị chặn, không treo**.
- Lý do: danh sách đơn dùng chung truy vấn với thẻ *Chứng từ liên quan*; chưa về thì
  thà nói ít hơn chứ không khóa nút.
- Kết quả:

**TC-421-05 — Bấm Hủy thì không tạo gì**
1. Ở hộp TC-421-01, bấm Hủy.
- Mong đợi: không đơn nào sinh ra; số đơn ở thẻ *Chứng từ liên quan* giữ nguyên.
- Kết quả:

---

## Nhóm C — Nút *In phiếu*

**TC-420-06 — Thu mua được đưa thẳng tới bản tách theo nhà cung cấp**
1. `DEMO_MANAGER_PURCHASE` (có `supplier:read`), mở phiếu **có dòng đã chốt phương án**.
2. Bấm **In phiếu**.
- Mong đợi:
  - Nút chữ **In phiếu**, một nút, không sổ xuống.
  - Mở tab mới ra **bản tách theo nhà cung cấp** — thanh công cụ ghi *In / Lưu PDF (n trang)*.
  - Trên thanh công cụ đó có nút **"Xem tờ phiếu gốc"**.
- Kết quả:

**TC-420-07 — Người yêu cầu được đưa tới tờ phiếu gốc**
1. `DEMONV` (không có quyền xem nhà cung cấp), mở phiếu của mình, bấm **In phiếu**.
- Mong đợi:
  - Nhãn nút **vẫn là "In phiếu"**, y hệt TC-420-06.
  - Mở ra **tờ phiếu gốc**.
  - Trên thanh công cụ **không** có nút "Xem bản tách theo nhà cung cấp".
- Kết quả:

**TC-420-08 — Lối bắc sang nhau, hai chiều**
1. Từ bản tách (TC-420-06), bấm **Xem tờ phiếu gốc** → ra tờ gốc của **đúng phiếu đó**.
2. Ở tờ gốc, bấm **Xem bản tách theo nhà cung cấp** → quay lại bản tách của đúng phiếu đó.
- Mong đợi: không bản in nào biến mất khỏi giao diện; đi vòng qua lại vẫn đúng một phiếu.
- Kết quả:

**TC-420-09 — Mở bản in từ ĐƠN MUA HÀNG thì không có lối bắc**
1. Mở chi tiết một **đơn mua hàng**, bấm in phiếu yêu cầu từ trong đó.
- Mong đợi: tờ in mở ra **KHÔNG có** nút "Xem bản tách theo nhà cung cấp".
- Lý do: số trên đường dẫn lúc đó là số của **đơn**, không phải của phiếu — bắc sang sẽ ra nhầm phiếu.
- Đây là ca dễ bỏ sót nhất trong cả tệp này.
- Kết quả:

**TC-420-10 — Phiếu đã đóng vẫn in được**
1. Mở một phiếu đã hoàn thành hoặc đã hủy, bấm **In phiếu**.
- Mong đợi: vẫn in được để lưu hồ sơ.
- Kết quả:

---

## Ma trận nhanh — nút nào hiện với ai

| Tình huống | Nút *Tạo đơn* | Đường chạy | Nút *In phiếu* | Bản in mở ra |
|---|:--:|---|:--:|---|
| Thu mua · phiếu có phương án chốt, còn dòng gom | x | gom theo nhà cung cấp | x | bản tách theo NCC |
| Thu mua · phiếu chưa ai chốt phương án | x | lập tay | x | tờ phiếu gốc (chưa có dòng chốt) |
| Thu mua · mọi dòng đã lên đơn | - | — | x | bản tách theo NCC |
| Người yêu cầu (`DEMONV`) | - | — | x | tờ phiếu gốc |
