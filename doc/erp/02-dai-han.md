# DÀI HẠN — LỘ TRÌNH PHÂN HỆ

| | |
|---|---|
| Bản | 1.1 — 10/08/2026 |
| Đối tượng đọc | Ban lãnh đạo · Gia Bảo · Được |
| Trả lời câu hỏi | ERP gồm những module gì, và làm theo thứ tự nào |
| Mức chi tiết | Đầu mục. **Không có mốc thời gian, không có số người-ngày** |
| Liên quan | [`01` Ngắn hạn](./01-ngan-han-2026.md) · [`04` Danh mục chờ quyết](./04-danh-muc-cho.md) |

> **Đây là kế hoạch dài hạn, không phải cam kết.** Thứ tự dưới đây là thứ tự hiệu quả nhất theo điều kiện hiện nay. **Tùy điều kiện thực tế và kế hoạch kinh doanh, thứ tự và phạm vi có thể thay đổi.** Cái không đổi là nguyên tắc: mỗi vòng phải có một phân hệ chạy thật rồi mới sang vòng sau.

---

## 1. Thứ tự các vòng

ERP của DEGO gồm sáu phân hệ. Không làm cùng lúc — làm từng vòng, mỗi vòng đưa một phân hệ vào chạy thật.

| Vòng | Phân hệ | Trạng thái |
|---|---|---|
| Vòng 0 | **Thu mua** | Đã chạy — đang là hệ thống thật của công ty |
| Vòng 1 | **Nhân sự (HRM)** | Đang làm — xem [`01` Ngắn hạn](./01-ngan-han-2026.md) |
| Vòng 2 | **Sản xuất và kho (MFM)** | Chưa khảo sát |
| Vòng 3 | **Kế toán** | Chưa khảo sát. Nhiều khả năng **nối chứ không tự viết** |
| Vòng 4 | **Bán hàng (CRM)** | Chưa khảo sát |
| Xuyên suốt | **Dùng chung** | Mỗi vòng bồi thêm một phần |

---

## 2. Vì sao theo thứ tự này

| Thứ tự | Lý do |
|---|---|
| **HRM trước** | Nền sẵn nhiều nhất — bảng nhân sự đã có công ty, phòng ban, đã nối với tài khoản đăng nhập. Và nó là phép thử khắc nghiệt nhất cho phần phân quyền: nếu HRM phân quyền đúng thì phân hệ nào cũng đúng |
| **MFM thứ hai** | Nối trực tiếp với Thu mua đang chạy: mua nguyên vật liệu, nhập kho, xuất cho sản xuất. Dữ liệu đã có sẵn một nửa. Đây cũng là chỗ công ty đau nhất về số liệu |
| **Kế toán thứ ba** | Sau MFM là đã có đủ hai đầu chi phí lớn nhất — mua vào và sản xuất — đủ để hạch toán và ra giá thành. Phần lớn công việc ở vòng này là đầu nối chứ không phải viết mới, nên đặt sớm được |
| **CRM sau cùng** | Cần đầu ra của sản xuất. Làm trước MFM thì bán được đơn nhưng không biết có làm kịp không, không biết còn hàng không |

**Nguyên tắc chung:** đi theo dòng chảy vật chất và tiền của công ty — mua vào, sản xuất, ghi sổ, bán ra. Không đi theo phòng ban nào kêu to nhất.

**Chỗ có thể đổi:** nếu mảng bán hàng thành ưu tiên kinh doanh, CRM đổi chỗ với Kế toán được. Ngược lại thì không — MFM không đứng trước HRM được, vì phần phân quyền chưa qua phép thử.

---

## 3. Danh sách module

Bản đồ tổng thể của ERP. Ô nào đã có thì không làm lại, chỉ bồi thêm.

### 3.1 Thu mua — vòng 0, đã chạy

| Module | Trạng thái |
|---|---|
| Yêu cầu mua hàng | Đã có |
| Yêu cầu khảo sát giá | Đã có |
| Khảo sát và so sánh giá | Đã có |
| Đơn mua hàng | Đã có |
| Nhà cung cấp | Đã có |
| Hợp đồng mua | Đã có |
| Nhận hàng và nghiệm thu | Đã có |
| Yêu cầu thanh toán | Đã có |
| Công nợ phải trả | Đã có |
| Hồ sơ chứng từ | Đã có |
| Báo cáo thu mua | Đã có, bồi thêm dần |

### 3.2 Nhân sự (HRM) — vòng 1

| Module | Ghi chú |
|---|---|
| Hồ sơ nhân sự | Đã có phần khung, phải mở rộng |
| Cơ cấu tổ chức và chức danh | Đã có phòng ban, chưa có chức danh |
| Hợp đồng lao động | Chưa có |
| Phân công và điều chuyển | Chưa có |
| Tuyển dụng | Chưa có |
| Nghỉ phép | Chưa có |
| Chấm công | **Chờ chốt phạm vi** — [`04` mục C2](./04-danh-muc-cho.md) |
| Lương và phúc lợi | **Chờ chốt phạm vi** — [`04` mục C2](./04-danh-muc-cho.md) |
| Bảo hiểm | Chưa có |
| Đánh giá | Chưa có |
| Đào tạo | Chưa có |
| Nghỉ việc và bàn giao | Chưa có |
| Báo cáo nhân sự | Chưa có |

Phạm vi bản 1 chốt sau khảo sát, theo bộ câu hỏi [`03`](./03-cau-hoi-khao-sat-hrm.md).

### 3.3 Sản xuất và kho (MFM) — vòng 2

| Module | Ghi chú |
|---|---|
| Danh mục sản phẩm nhiều cấp | Bảng sản phẩm cha làm sẵn ở vòng 1 (việc DB6) |
| Định mức nguyên vật liệu (BOM) | Nhiều cấp, có phiên bản, có hiệu lực theo ngày |
| Kế hoạch sản xuất | |
| Lệnh sản xuất | |
| Công đoạn và tổ sản xuất | Nối với HRM nếu có lương theo sản phẩm |
| Xuất nguyên liệu, nhập thành phẩm | |
| Tồn kho | Đã có từ Thu mua — phải rà lại xem có đủ chặt không |
| Luân chuyển kho | Đã có từ Thu mua |
| Kiểm kê | |
| Vị trí kho, lô, hạn dùng | **Chờ chốt** — [`04` mục C5](./04-danh-muc-cho.md) |
| Chất lượng | Chốt sau khi khảo sát |
| Giá thành | **Ranh giới với Kế toán chưa rõ** — [`04` mục C6](./04-danh-muc-cho.md) |
| Bảo trì máy móc | Chốt sau khi khảo sát |
| Báo cáo sản xuất và kho | |

### 3.4 Kế toán — vòng 3

| Module | Ghi chú |
|---|---|
| Hệ thống tài khoản | Chỉ khi tự viết |
| Bút toán và sổ cái | Chỉ khi tự viết |
| Công nợ phải trả | Đã có bên Thu mua, cần cầu nối |
| Công nợ phải thu | Cần CRM, hoặc làm độc lập |
| Thu chi và ngân hàng | |
| Tài sản cố định và khấu hao | |
| Giá thành | Ranh giới với MFM |
| Thuế và hóa đơn | Theo quy định nhà nước |
| Báo cáo tài chính | Theo mẫu quy định |
| **Đầu nối sang phần mềm kế toán** | Đây mới là phần khả năng cao sẽ làm — xem mục 5 |

### 3.5 Bán hàng (CRM) — vòng 4

| Module | Ghi chú |
|---|---|
| Khách hàng | |
| Liên hệ và lịch sử tiếp xúc | |
| Cơ hội bán hàng | |
| Báo giá bán | Đối xứng với khảo sát giá bên Thu mua — dùng lại được nhiều |
| Đơn bán hàng | |
| Giao hàng | Nối với kho ở MFM |
| Công nợ phải thu | Đối xứng với công nợ phải trả đã có |
| Chính sách giá và chiết khấu | |
| Chăm sóc sau bán | Nối được với module Phiếu hỗ trợ đã có |
| Báo cáo bán hàng | |

**Ghi chú:** file `ke-hoach/02` mục 30.4 đã nêu một mâu thuẫn về mảng bán hàng chưa được giải quyết. Phải mở lại và chốt trước khi bắt đầu vòng này.

### 3.6 Dùng chung — bồi thêm mỗi vòng

| Module | Trạng thái |
|---|---|
| Tài khoản và phân quyền | Đã có — vá và gom theo phân hệ ở vòng 1 |
| Danh mục dùng chung | Đã có, mở rộng dần |
| Công ty và phòng ban | Đã có |
| Luồng duyệt dùng chung | Làm ở vòng 1 |
| Thông báo | Đã có — chuông, đẩy, thư |
| Tệp đính kèm và chứng từ | Đã có |
| Nhật ký thao tác | Đã có |
| Nhập liệu hàng loạt | Đã có |
| Webhook và đầu nối ra ngoài | Làm ở vòng 1 |
| Báo cáo và bảng số liệu | Bồi mỗi vòng |
| Trung tâm hướng dẫn sử dụng | Đã có, app riêng |
| Quản lý dự án (Project-M) | Đã có, app riêng |
| Phiếu hỗ trợ | Đã có |
| Sao lưu và phục hồi | Đã có |

---

## 4. Ba việc nền của vòng 2

Ghi riêng vì đây là ba thứ làm sai thì cả phân hệ sản xuất sai theo.

1. **Rà lại sổ kho.** Bảng tồn kho hiện có được viết cho mua hàng, chưa chắc đủ chặt để làm nền sản xuất: chặn âm kho, giá vốn, chốt kỳ. Sổ kho không chặt thì mọi số liệu sản xuất phía trên đều sai.
2. **Chốt có làm vị trí kho, lô, hạn dùng hay không.** Quyết định này đổi cấu trúc bảng tồn kho, phải chốt **trước** khi viết BOM.
3. **Thêm công ty cho kho** — làm ở vòng 1 (việc DB5), nhưng chỉ dùng thật khi có nhiều nhà máy.

**Điều kiện bắt đầu vòng 2:** HRM đã chạy thật và không còn lỗi chặn · khảo sát nghiệp vụ sản xuất xong, có biên bản xác nhận · bảng sản phẩm cha (DB6) đã có và đã dùng thật.

---

## 5. Kế toán — nối chứ không tự viết

| Vì sao | |
|---|---|
| Kế toán do luật định | Chế độ kế toán, mẫu báo cáo tài chính, quyết toán thuế đều theo quy định nhà nước và đổi theo văn bản pháp luật |
| Đã có phần mềm chuyên | Thị trường Việt Nam có sẵn phần mềm kế toán được cập nhật theo luật. Tự viết là gánh nghĩa vụ cập nhật pháp lý vĩnh viễn |
| Rủi ro không đối xứng | Phần mềm mua hàng tính sai thì sửa. Phần mềm kế toán tính sai thì làm việc với cơ quan thuế |

**Việc của đội phần mềm ở vòng này là đầu nối:** xuất bút toán từ Thu mua, MFM, CRM sang phần mềm kế toán, và màn hình đối chiếu. Chính là chỗ dùng thật của module webhook làm ở vòng 1.

Quyết định "tự viết hay nối" phải chốt **trước** vòng 3, không phải trong lúc làm — xem [`04` mục C7](./04-danh-muc-cho.md).

---

## 6. Nợ kỹ thuật đã dời — trả ở vòng nào

Vòng 1 chấp nhận không đụng cơ sở dữ liệu cũ. Đó là dời nợ chứ không phải hết nợ. Ghi ra đây để không ai quên.

| Nợ | Trả ở vòng nào | Nếu không trả |
|---|---|---|
| Trạng thái tồn tại hai kiểu: chuỗi tiếng Việt ở bảng cũ, mã ở bảng mới | Vòng 2, khi có cửa sổ bảo trì đầu tiên | Mỗi báo cáo liên phân hệ phải đi qua bảng quy đổi. Càng nhiều phân hệ càng dễ sai |
| Cột `created_by` không nói rõ là tài khoản hay nhân sự | Vòng 2 hoặc vòng 3 | Người mới vào sẽ hiểu nhầm. Đã có tiền lệ với `assignee_id` |
| 75 file migration chưa gộp mốc | Trước vòng 3 | Năm phân hệ thì thành ba trăm file, dựng môi trường mới mất hàng giờ |
| Chưa có kiểm thử tự động đầy đủ | Bồi dần mỗi vòng | Càng nhiều phân hệ, sửa một chỗ càng dễ vỡ chỗ khác mà không ai biết |

---

## 7. Cái gì bồi thêm ở mỗi vòng

Phần dùng chung không làm một lần xong.

| | Vòng 1 (HRM) | Vòng 2 (MFM) | Vòng 3 (Kế toán) | Vòng 4 (CRM) |
|---|---|---|---|---|
| Phân quyền | Vá lỗ hổng phạm vi, gom theo phân hệ | Thêm phạm vi theo kho, theo nhà máy | Thêm phạm vi theo pháp nhân, theo kỳ kế toán | Thêm phạm vi theo vùng, theo nhân viên bán hàng |
| Luồng duyệt | Làm luồng duyệt dùng chung | Duyệt lệnh sản xuất, duyệt xuất kho | Duyệt bút toán, khóa sổ | Duyệt báo giá, duyệt chiết khấu |
| Báo cáo | Báo cáo nhân sự | Báo cáo sản xuất, giá thành | Báo cáo tài chính, đối chiếu | Báo cáo bán hàng, công nợ phải thu |
| Tích hợp | Module webhook phần lõi | Đồng bộ hai chiều, đối chiếu lệch | Đầu nối phần mềm kế toán | Đầu nối kênh bán |
| Hạ tầng | Nhật ký lỗi, giám sát, hàng đợi | Kiểm thử tải, tối ưu truy vấn | Lưu vết không sửa được | Sao lưu và phục hồi theo phân hệ |

---

## 8. Ba điều kiện để lộ trình này không vỡ

1. **Mỗi vòng phải có một phân hệ chạy thật, không phải chạy demo.** Làm nửa vời ba phân hệ tệ hơn làm xong một.
2. **Khảo sát nghiệp vụ phải xong trước khi viết code của vòng đó.** Vòng 1 đã ghi rõ cách làm, các vòng sau lặp lại đúng khuôn đó.
3. **Bộ phận nghiệp vụ phải cử được đầu mối cho từng vòng.** Đây là điều kiện thường bị coi nhẹ và thường là nguyên nhân trượt lịch thật sự — file `ke-hoach/01` mục 5 đã ghi là chưa hạn nào chờ bộ phận khác được giữ đúng.

---

## 9. Cái gì không nằm trong lộ trình này

| | Vì sao |
|---|---|
| Đa ngôn ngữ | Chưa có nhu cầu thật |
| Ứng dụng di động riêng | Web đã chạy được trên điện thoại. Làm app riêng là nhân đôi khối lượng bảo trì |
| Bán sản phẩm ra ngoài | Là mục tiêu khác hẳn: cần đa khách hàng, cần hỗ trợ, cần bản quyền. Nếu có ý định thì phải bàn từ đầu chứ không chuyển đổi sau |
| Đổi khung công nghệ | Không có lý do kỹ thuật nào đủ mạnh |
