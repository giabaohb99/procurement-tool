# BÁO CÁO KẾ HOẠCH TRIỂN KHAI
## Hệ thống Quản trị Nội bộ DEGO WorkHub

| | |
|---|---|
| **Mã tài liệu** | BC-DEGO-IT-001-2026 |
| **Phiên bản** | 2.0 |
| **Ngày ban hành** | 12/08/2026 |
| **Đơn vị soạn thảo** | Đội Công nghệ thông tin |
| **Loại tài liệu** | Báo cáo kế hoạch triển khai |
| **Trả lời cho** | `SRS-HOLDING-IT-001-2026` — Tài liệu yêu cầu phần mềm DEGO WorkHub, bản 1.1, ngày 11/08/2026 |
| **Trạng thái** | Trình duyệt |
| **Phạm vi áp dụng** | Toàn tập đoàn DEGO Holding |

### Bảng phê duyệt

| Vai trò | Họ tên | Nội dung xác nhận | Ngày | Ký |
|---|---|---|---|---|
| Người lập | Đội Công nghệ thông tin | Số liệu hiện trạng là số đếm được trên mã nguồn, không phải ước lượng | | |
| Người rà soát | Văn phòng Điều hành | Thứ tự triển khai và phạm vi từng giai đoạn đúng nhu cầu quản trị | | |
| Người phê duyệt | Tổng Giám đốc | Chốt lộ trình, chốt nhân lực, chốt các nội dung tại mục 11 | | |

---

## MỤC LỤC

1. Mục đích của báo cáo
2. Kết luận và khuyến nghị
3. Điểm xuất phát — hệ thống hiện có làm nền cho WorkHub
4. Cách làm: sửa nền, phỏng vấn chốt ưu tiên, rồi xây từng phân hệ
5. Việc phải làm trên nền trước khi lắp WorkHub
6. Kế hoạch cho từng phân hệ của WorkHub
7. Lộ trình và mốc thời gian
8. Nhân lực
9. Danh mục mở rộng ngoài phạm vi bản 1
10. Nghiệm thu và điều kiện thành công ngoài phần mềm
11. Nội dung cần Ban lãnh đạo quyết định
12. Rủi ro
- Phụ lục A — Bảng thuật ngữ

---

## 1. MỤC ĐÍCH CỦA BÁO CÁO

`SRS-HOLDING-IT-001-2026` mô tả **DEGO WorkHub phải làm được những gì** — 12 phân hệ, khoảng 300 tài khoản, trên 10 công ty thành viên. Báo cáo này trả lời phần còn lại: **làm thế nào để có nó, theo thứ tự nào, mất bao lâu, cần bao nhiêu người.**

Bốn câu hỏi cụ thể mà báo cáo này trả lời:

| Câu hỏi | Trả lời ở mục |
|---|---|
| Bắt đầu từ đâu — xây mới hay dùng lại phần mềm đang chạy | Mục 3 |
| Cách quyết định làm chức năng nào trước | Mục 4 |
| Bao giờ có từng phân hệ | Mục 7 |
| Cần bao nhiêu người, có phải tuyển thêm không | Mục 8 |

Báo cáo này **không thay thế** tài liệu yêu cầu phần mềm. Mọi mô tả chức năng vẫn lấy theo tài liệu đó. Chỗ nào báo cáo này đề nghị khác đi so với lộ trình gợi ý trong tài liệu yêu cầu, đều được nêu rõ kèm lý do và đưa thành một nội dung cần quyết định tại mục 11.

**Quy ước giữ nguyên theo tài liệu yêu cầu:** mã chức năng dạng `FR-[PHÂN HỆ]-[NN]`, mã yêu cầu phi chức năng dạng `NFR-[NN]`, mỗi yêu cầu viết bắt đầu bằng "Hệ thống phải...", mức ưu tiên **B — Bắt buộc · N — Nên có · T — Tương lai**.

---

## 2. KẾT LUẬN VÀ KHUYẾN NGHỊ

### 2.1. Bốn kết luận

**Một — Không xây WorkHub từ đầu. Xây trên nền đang chạy.**
Tập đoàn đã có một phần mềm nội bộ vận hành thật: **20.674 dòng mã, 36 phân hệ nghiệp vụ nhỏ, 265 điểm giao tiếp, 57 bảng dữ liệu**, người dùng thật sử dụng hằng ngày cho công tác thu mua. Phần mềm này đã sẵn có bốn thứ mà WorkHub cần và mất nhiều thời gian nhất để xây lại: cơ chế đăng nhập, cơ chế phân quyền theo vai trò, cơ chế giới hạn phạm vi dữ liệu, và hệ thống thông báo ba kênh. Bỏ đi để xây mới là bỏ khoảng một năm công đã trả.

**Hai — Nhưng nền đó chưa đủ chắc để gánh dữ liệu nhân sự, và phải sửa trước.**
Rà soát ngày 12/08/2026 phát hiện **bốn lỗ hổng đang có hiệu lực trên hệ thống chạy thật**, trong đó ba lỗ hổng sẽ đi thẳng vào dữ liệu lương, hợp đồng lao động và giấy tờ tùy thân ngay khi phân hệ Nhân sự có dữ liệu. Chi tiết tại mục 3.3. Đây là lý do giai đoạn đầu tiên của lộ trình là **sửa nền**, không phải xây phân hệ mới.

**Ba — Không quyết chức năng nào làm trước bằng cách ngồi bàn. Quyết bằng phỏng vấn.**
Cách làm đề xuất: lấy danh mục chức năng chuẩn từ các nền tảng lớn, mang đi phỏng vấn từng phòng ban, chấm mức ưu tiên dựa trên câu trả lời có ghi biên bản, sửa lại cho vừa thực tế, dựng bản chạy được cho người dùng thật bấm, rồi mới chốt. Quy trình sáu bước tại mục 4.

**Bốn — Nửa năm là đạt được, nhưng chỉ đến hết phần nền và phần con người.**
Mốc **15/02/2027**: nền đã sửa xong, phân hệ Tổ chức và phân hệ Nhân sự chạy thật, khoảng 300 hồ sơ nhân sự số hóa và đối chiếu khớp. Các phân hệ còn lại của WorkHub — Văn bản, Công việc, Đào tạo, Góp ý, Báo cáo — kéo dài đến hết 2027 và sang 2028. Đây là chương trình nhiều năm, không phải một dự án nửa năm.

### 2.2. Ba khuyến nghị cần quyết ngay

| # | Khuyến nghị | Vì sao gấp |
|---|---|---|
| 1 | **Cho phép bắt đầu ngay phần vá bốn lỗ hổng**, không chờ phê duyệt toàn bộ lộ trình. Khối lượng vài ngày công | Bốn lỗ hổng đang hở **ngay lúc này**. Chờ phê duyệt thêm một tháng là hở thêm một tháng, mà việc vá không phụ thuộc vào việc lộ trình có được duyệt hay không |
| 2 | **Tách một người ra khỏi hàng chờ yêu cầu thay đổi của phần mềm Thu mua** | Đo được: phần mềm đang chạy phát sinh **xấp xỉ một yêu cầu thay đổi mỗi ngày làm việc**. Không tách người thì mốc 15/02/2027 trượt sang tháng 4–5/2027. Phép tính tại mục 8.2 |
| 3 | **Tuyển thêm một người từ tháng 9/2026** | Không phải để rút ngắn nửa năm này — người mới cần hai đến ba tháng đào tạo nên đóng góp trong nửa năm đầu là nhỏ. Tuyển vì phần việc **sau** phân hệ Nhân sự dài gấp nhiều lần phần trước, và vì hiện đang có công cụ vận hành chỉ một người biết dùng |

---

## 3. ĐIỂM XUẤT PHÁT — HỆ THỐNG HIỆN CÓ LÀM NỀN CHO WORKHUB

### 3.1. Tập đoàn đang có gì

Phần mềm quản lý Thu mua, xây trong nội bộ, đang vận hành trên hai môi trường tách biệt (môi trường chạy thật và môi trường thử nghiệm), có sao lưu tự động hai lần mỗi ngày.

| Hạng mục | Số đo ngày 12/08/2026 |
|---|---|
| Quy mô mã nguồn phía máy chủ | 20.674 dòng |
| Số phân hệ nghiệp vụ nhỏ | 36 |
| Số điểm giao tiếp (chức năng gọi được) | 265 |
| Số bảng dữ liệu | 57 |
| Số bước thay đổi cấu trúc dữ liệu đã chạy | 75 |
| Số bộ kiểm thử tự động | 27 |
| Công nghệ | Python FastAPI · MySQL 8.4 · React · Docker |

### 3.2. Cái gì dùng lại được cho WorkHub

Đây là phần trả lời câu "vì sao không xây mới". Bốn hạng mục dưới đây là phần tốn thời gian nhất của bất kỳ hệ thống quản trị nội bộ nào, và tập đoàn **đã có, đã chạy thật, đã qua kiểm chứng bằng người dùng**:

| Hạng mục WorkHub cần | Hiện trạng | Đỡ được bao nhiêu |
|---|---|---|
| **Đăng nhập và quản lý tài khoản** | Đã có, đã nối tài khoản đăng nhập với hồ sơ nhân sự | Gần như đủ. Còn thiếu xác thực hai lớp |
| **Phân quyền theo vai trò** | Đã có ma trận quyền: mỗi vai trò được làm gì trên loại dữ liệu nào | Đủ về cơ chế. Cần rà lại danh sách vai trò theo góc nhìn tập đoàn |
| **Giới hạn phạm vi dữ liệu** | Đã có, và **mềm hơn mặt bằng phần mềm thương mại**: cấp theo từng lượt gán vai trò, có bao gồm và loại trừ theo pháp nhân, phòng ban, từng nhân sự | Cơ chế đủ mạnh. Nhưng đang bị bỏ sót ở nhiều chỗ — xem mục 3.3 |
| **Thông báo ba kênh** | Đã chạy thật: thông báo trong ứng dụng, thư điện tử, thông báo đẩy trên trình duyệt | Đủ cho phân hệ Thông báo của WorkHub, trừ kênh Zalo |
| **Nhật ký thao tác** | Đã có, ghi giá trị trước và sau mỗi lần sửa, có gom theo tháng | Đủ về cơ chế ghi. Thiếu phần kiểm quyền khi đọc, và thiếu chính sách lưu trữ dài hạn |
| **Sao lưu tự động** | Chạy hai lần mỗi ngày lên lưu trữ đám mây | Tốt hơn mức tài liệu yêu cầu đặt ra. Nhưng **chưa từng thử phục hồi** |
| **Hạ tầng vận hành** | Đóng gói bằng Docker, có tên miền riêng, có chứng chỉ bảo mật, có tiến trình chạy nền theo lịch | Đủ để mở rộng, không phải dựng lại |

Ngoài ra, tập đoàn đã có ba ứng dụng nội bộ khác đang chạy, **dùng chung máy chủ và chung tài khoản đăng nhập** với phần mềm Thu mua: Trung tâm Hướng dẫn sử dụng, công cụ Quản lý Dự án cho Ban điều hành, và Phiếu hỗ trợ. Ba ứng dụng này phủ được một phần của ba phân hệ WorkHub — chi tiết tại mục 6.

### 3.3. Cái gì phải sửa — bốn lỗ hổng đang hở

Không phải rủi ro tương lai. Rà soát ngày 12/08/2026, cả bốn đang có hiệu lực trên hệ thống chạy thật:

| # | Lỗ hổng | Hậu quả cụ thể nếu WorkHub lắp lên nền này |
|---|---|---|
| 1 | Chức năng **xem hồ sơ nhân sự theo mã** và **11 chức năng xuất tệp** không kiểm tra phạm vi dữ liệu | Người có quyền đọc nhân sự xem được hồ sơ bất kỳ bằng cách đoán số thứ tự; và tải về toàn bộ danh sách nhân sự của mọi công ty thành viên bằng một lần bấm. Trong 11 chức năng xuất tệp, **chỉ 1 chức năng kiểm tra quyền xuất** |
| 2 | Cấu hình **loại trừ phòng ban** trên dữ liệu nhân sự lưu được nhưng **không có tác dụng** | Người quản trị chọn "trừ phòng Nhân sự", hệ thống báo lưu thành công, và người ta tin là đã cấm. Đây là loại lỗi nguy hiểm nhất vì nó tạo cảm giác an toàn giả |
| 3 | Tệp đính kèm trả về **đường dẫn công khai vĩnh viễn**, thư mục tệp không kiểm tra đăng nhập, tên tệp đoán được theo quy luật | Hợp đồng, hóa đơn, giấy tờ tùy thân: ai có đường dẫn là tải được, không cần đăng nhập, kể cả người đã nghỉ việc còn giữ đường dẫn cũ. **Phân hệ Nhân sự và phân hệ Văn bản đều lưu tài liệu bằng cơ chế này** |
| 4 | Nhật ký thao tác **đọc tự do**; bỏ trống mã bản ghi thì trả về nhật ký của mọi bản ghi | Nhật ký chứa giá trị trước và sau của mọi lần sửa. Đây là đường vòng đọc được đúng phần dữ liệu mà cơ chế phạm vi đang che |

**Ba trong bốn lỗ hổng này đi thẳng vào phạm vi của phân hệ Nhân sự.** Riêng lỗ hổng số 3 không thể vá bằng cách chỉnh phạm vi dữ liệu, vì hợp đồng lao động và giấy tờ tùy thân là **tệp**, không phải dòng trong bảng.

Khối lượng vá: **vài ngày công**. Đây là căn cứ của khuyến nghị số 1 tại mục 2.2.

### 3.4. Ba khoảng cách kỹ thuật khác, lớn hơn nhưng không gấp

| # | Khoảng cách | Đo được | Vì sao WorkHub cần |
|---|---|---|---|
| 1 | **Phạm vi dữ liệu đang phải khai bằng tay ở từng chỗ** | 97 chức năng đọc dữ liệu, nhưng chỉ **38 chỗ** có gọi hàm áp phạm vi. **9 trên 28** loại dữ liệu được khai phạm vi; 19 loại còn lại không lọc theo chiều nào | WorkHub có 12 phân hệ và khoảng 300 người dùng ở trên 10 pháp nhân. Cơ chế "nhớ thì gọi, quên thì hở" không chịu được quy mô đó. Phải đổi thành: **quên khai là hệ thống báo lỗi, không phải trả hết** |
| 2 | **Chưa sẵn sàng cho nhiều pháp nhân** | **15 trên 57 bảng** có cột đánh dấu công ty thành viên. Thiếu 42 bảng | Tài liệu yêu cầu nêu rõ tập đoàn có trên 10 công ty thành viên và có vai trò "Nhân sự công ty" tách khỏi "Nhân sự tập đoàn". Thêm cột phân định pháp nhân **sau khi đã có dữ liệu** là việc rất khó sửa lại |
| 3 | **Không có bộ máy phê duyệt dùng chung** | Hiện có 5 luồng phê duyệt, mỗi luồng viết riêng trong từng phân hệ nghiệp vụ | Tài liệu yêu cầu xếp phân hệ Luồng phê duyệt vào **tầng nền tảng**, và gần như mọi phân hệ nghiệp vụ đều cần nó: ban hành văn bản, quyết định nhân sự, duyệt kết quả công việc, duyệt cấp phúc lợi. Viết luồng thứ sáu, thứ bảy theo cách cũ là nhân bản một vấn đề |

Ngoài ra: hệ thống hiện có **1 lớp xử lý trung gian duy nhất**, chưa có mã định danh cho từng lượt gọi, chưa có nhật ký truy cập, và chưa có bộ xử lý lỗi chung — nên khi có sự cố thì không truy được ai đã làm gì. Với phần mềm một phân hệ thì chấp nhận được; với hệ thống lưu dữ liệu nhân sự của 300 người thì không.

---

## 4. CÁCH LÀM: SỬA NỀN, PHỎNG VẤN CHỐT ƯU TIÊN, RỒI XÂY TỪNG PHÂN HỆ

### 4.1. Ba bước lớn

```
Bước 1 — SỬA NỀN            Bước 2 — PHỎNG VẤN CHỐT ƯU TIÊN     Bước 3 — XÂY TỪNG PHÂN HỆ
Vá lỗ hổng đang hở          Lấy danh mục chức năng chuẩn        Theo thứ tự đã chốt
Làm phần dùng chung         Mang đi hỏi từng phòng ban          Mỗi phân hệ một vòng khảo sát
Chuẩn hóa dữ liệu           Chấm mức ưu tiên B / N / T          Demo hai tuần một lần
Bộ máy phê duyệt chung      Sửa lại cho vừa thực tế             Nghiệm thu bằng người dùng thật
Khung nhiều phân hệ         Demo, lấy ý kiến, rồi chốt
```

Bước 1 và bước 2 **chạy song song**, không xếp hàng. Đội phần mềm sửa nền trong khi Văn phòng Điều hành đi phỏng vấn. Đây là chỗ tiết kiệm được nhiều thời gian nhất của cả lộ trình: phần sửa nền không cần chờ kết quả phỏng vấn, và phần phỏng vấn không cần chờ mã nguồn.

### 4.2. Bước 2 chi tiết — quy trình khảo sát sáu bước

Vì sao không hỏi thẳng "các anh chị cần chức năng gì":

| Cách làm | Hỏng ở đâu |
|---|---|
| Chỉ hỏi người dùng muốn gì | Người dùng mô tả cái họ đang làm bằng Excel, không mô tả cái họ chưa biết là có. Kết quả là tin học hóa một quy trình thủ công và giữ nguyên mọi chỗ dở của nó |
| Chỉ chép hệ thống nước ngoài | Ra một phần mềm đủ tính năng mà không ai dùng, vì nó giả định một cách vận hành khác |

Quy trình đề xuất đi từ chuẩn quốc tế **xuống** thực tế, sáu bước:

| Bước | Làm gì | Đầu ra kiểm chứng được | Ai chủ trì |
|---|---|---|---|
| **KS1 — Lấy danh mục chuẩn** | Trích danh sách chức năng từ các nền tảng quản trị nhân sự và quản trị doanh nghiệp lớn, gộp với danh sách chức năng trong tài liệu yêu cầu WorkHub, thành **một bảng đối chiếu**, mỗi dòng một chức năng | Bảng có cột: tên chức năng · nguồn · mô tả một câu · dữ liệu nó cần | Đội Công nghệ thông tin |
| **KS2 — Mang đi hỏi** | Cầm bảng đi phỏng vấn từng phòng. Với mỗi dòng hỏi đúng ba câu: **hiện đang làm bằng gì · một tháng phát sinh bao nhiêu lần · nếu không có thì hỏng chuyện gì** | Biên bản phỏng vấn có chữ ký người được phỏng vấn. Bảng điền xong ba cột trả lời | Văn phòng Điều hành chủ trì, Công nghệ thông tin ghi |
| **KS3 — Chấm ưu tiên** | Mỗi dòng nhận một mức **B / N / T**. Quy tắc chấm: mức **B** chỉ dành cho chức năng mà **không có thì một quy trình có thật bị đứt** — không dành cho chức năng "nên có cho đủ bộ" | Bảng có cột mức, và **số dòng mức B không vượt quá 40% tổng số dòng**. Vượt là chấm chưa nghiêm | Ban điều hành duyệt |
| **KS4 — Sửa cho vừa** | Mỗi dòng mức B viết lại thành yêu cầu "Hệ thống phải..." theo thực tế DEGO, không giữ nguyên cách nói của phần mềm nguồn. Chỗ nào phần mềm ngoài làm phức tạp hơn nhu cầu thì **ghi rõ phần cắt bỏ và lý do** | Danh sách yêu cầu có mã, có mức, có ghi chú "cắt gì so với bản gốc" | Đội Công nghệ thông tin |
| **KS5 — Demo và lấy ý kiến** | Dựng bản chạy được cho người dùng thật bấm trên môi trường thử nghiệm. **Không trình bày bằng ảnh chụp màn hình hay bản vẽ** | Biên bản demo: ai bấm, chỗ nào vướng, sửa gì | Công nghệ thông tin trình, phòng nghiệp vụ bấm |
| **KS6 — Chốt hoặc quay lại KS4** | Đạt thì chuyển sang xây bản chính thức. Không đạt thì ghi lý do và quay lại KS4. **Quá hai vòng chưa đạt thì đưa lên Ban điều hành**, không lặp vòng ba | Yêu cầu được đánh dấu đã chốt và khóa lại | Người chủ trì |

### 4.3. Nguồn của danh mục chức năng ở bước KS1

| Nguồn | Loại | Dùng cho phần nào | Mức tin cậy hiện tại |
|---|---|---|---|
| **Tài liệu yêu cầu WorkHub** | Nội bộ, bản 1.1 đã ban hành | **Nguồn chính** — toàn bộ 12 phân hệ | Cao |
| **HrOnline** | Phần mềm nhân sự thương mại Việt Nam | Nhân sự: hồ sơ, hợp đồng, nghỉ phép, tiền lương | Cao — đã khảo sát trực tiếp **59 chức năng**, có đường dẫn và danh sách trường |
| **Odoo Community** | Bộ phần mềm quản trị doanh nghiệp mã nguồn mở | Cách chia phân hệ nhân sự: hồ sơ, tuyển dụng, nghỉ phép, chấm công, đánh giá | Trung bình — mới ở mức nắm cách chia phân hệ, **phải khảo sát lại ở bước KS1** |
| **ERPNext** | Hệ thống quản trị nguồn lực mã nguồn mở | Cách nối phân hệ nhân sự với các phân hệ khác | Trung bình — **phải khảo sát lại ở bước KS1** |

### 4.4. Bốn quy tắc bắt buộc của cách làm này

| # | Quy tắc | Vì sao |
|---|---|---|
| 1 | **Bảng đối chiếu không bao giờ trở thành bản đặc tả.** Nó là danh mục để hỏi, không phải danh mục để làm | Chép cấu trúc dữ liệu của phần mềm ngoài là kế thừa luôn cả giả định vận hành của họ. Đây là quyết định đã chốt trong nội bộ đội phần mềm |
| 2 | **Mỗi nửa tháng kết thúc bằng một buổi trình diễn cho Ban lãnh đạo**, kể cả khi phần việc trong kỳ là phần nền không nhìn thấy được — khi đó trình diễn bằng bộ kiểm thử tự động chạy trước mặt người xem | Nguyên tắc quản trị này lấy đúng theo tài liệu yêu cầu WorkHub. Nó là cách rẻ nhất để phát hiện đi sai hướng |
| 3 | **Người dùng thật phải chạm vào trước khi chốt.** Không nhận "đã lập trình xong" làm bằng chứng nghiệm thu | Một chức năng chạy đúng kỹ thuật vẫn có thể sai nghiệp vụ, và chỉ người làm nghiệp vụ phát hiện ra |
| 4 | **Yêu cầu đã chốt thì khóa.** Thay đổi sau đó phải ghi thành văn bản và thành phiên bản mới của tài liệu | Không có quy tắc này thì phạm vi trôi liên tục và không mốc nào giữ được |

### 4.5. Vai trò của trí tuệ nhân tạo trong lộ trình

Đội phần mềm sử dụng công cụ trí tuệ nhân tạo hỗ trợ lập trình. Cần nói rõ nó giúp chỗ nào để con số ở mục 8 được hiểu đúng:

| Loại việc | Mức hỗ trợ | Rút ngắn ước tính |
|---|---|---|
| Chuyển 36 phân hệ nghiệp vụ sang phần dùng chung | Nhiều — việc lặp, có khuôn mẫu rõ, kiểm chứng được bằng bộ kiểm cũ | 30 – 40% |
| Chuẩn hóa 11 cột dữ liệu đang lưu tiếng Việt | Nhiều — cùng một khuôn lặp 11 lần | 30 – 40% |
| Dựng phân hệ danh mục mới | Nhiều | 30% |
| Viết bộ kiểm thử | Trung bình — sinh khung nhanh, nhưng vẫn phải tự chứng minh bộ kiểm bắt được vi phạm thật | 20% |
| **Phỏng vấn nghiệp vụ, chốt phạm vi** | **Gần như không** — việc của con người ngồi với con người | 0% |
| **Đối chiếu dữ liệu thật khi chuyển đổi** | **Gần như không, và không được để làm thay** — sai ở đây là hỏng dữ liệu đang chạy | 0% |

**Kết luận dùng cho phép tính ở mục 8: rút ngắn khoảng 15% tổng khối lượng**, không phải 40%. Lý do: phần việc nó giúp nhiều nhất chỉ chiếm khoảng một phần ba lộ trình, và ba thứ chặn tiến độ nặng nhất — phỏng vấn, chốt phạm vi, đối chiếu dữ liệu thật — nằm đúng ở chỗ nó không giúp được.

---

## 5. VIỆC PHẢI LÀM TRÊN NỀN TRƯỚC KHI LẮP WORKHUB

Đây là bước 1 tại mục 4.1. Các yêu cầu dưới đây **không có trong tài liệu yêu cầu WorkHub**, vì tài liệu đó viết theo giả định xây mới. Chúng là điều kiện để nền hiện có gánh được 12 phân hệ.

### 5.1. Nhóm vá gấp

| Mã | Yêu cầu | Mức |
|---|---|---|
| FR-NEN-01 | Hệ thống phải áp giới hạn phạm vi dữ liệu cho **mọi** đường đọc, gồm cả xem chi tiết theo mã và xuất tệp, không chỉ đường xem danh sách | **B** |
| FR-NEN-02 | Hệ thống phải làm cho cấu hình bao gồm và loại trừ theo phòng ban, theo nhân sự **có hiệu lực thật** trên mọi loại dữ liệu đã khai báo | **B** |
| FR-NEN-03 | Hệ thống phải buộc mọi lượt tải tệp đính kèm đi qua kiểm tra đăng nhập, kiểm tra quyền và phạm vi **của chứng từ chủ quản**, và cấp đường dẫn có hạn giờ thay vì đường dẫn công khai vĩnh viễn | **B** |
| FR-NEN-04 | Hệ thống phải kiểm tra quyền và áp phạm vi khi đọc nhật ký thao tác, và che các trường nhạy cảm trong nội dung trước và sau khi sửa | **B** |
| FR-NEN-05 | Hệ thống phải kiểm tra quyền xuất tệp riêng biệt với quyền xem, và ghi nhật ký mỗi lượt xuất kèm bộ lọc đã dùng | **B** |

### 5.2. Nhóm phần dùng chung

| Mã | Yêu cầu | Mức |
|---|---|---|
| FR-NEN-06 | Hệ thống phải **báo lỗi khi gặp loại dữ liệu chưa khai báo phạm vi**, thay vì lặng lẽ trả về toàn bộ | **B** |
| FR-NEN-07 | Hệ thống phải có phần dùng chung sao cho xây một phân hệ danh mục mới **dưới 50 dòng mã** mà vẫn tự động có đầy đủ phân quyền, phạm vi, nhật ký, phân trang, tìm kiếm và xuất tệp | **B** |
| FR-NEN-08 | Hệ thống phải sinh **mã định danh cho mỗi lượt gọi**, trả về trong phản hồi lỗi và ghi vào mọi dòng nhật ký của lượt đó | **B** |
| FR-NEN-09 | Hệ thống phải ghi **nhật ký truy cập**: ai gọi chức năng nào, lúc nào, trả về bao nhiêu dòng | **B** |
| FR-NEN-10 | Hệ thống phải trả về **đúng một khuôn phản hồi** cho mọi loại lỗi, kể cả lỗi chưa lường trước, và không để lộ thông tin kỹ thuật nội bộ ra ngoài | **B** |
| FR-NEN-11 | Hệ thống phải cho phép **thu hồi phiên đăng nhập ngay lập tức**: khóa một tài khoản là tài khoản đó mất quyền trong vài giây | **B** |
| FR-NEN-12 | Hệ thống phải có **bộ kiểm thử tự động** chặn việc đưa lên bản chạy thật khi vi phạm các quy ước nền | **B** |
| FR-NEN-13 | Hệ thống phải có **giới hạn tần suất gọi** có hiệu lực trên toàn bộ chức năng, không chỉ trên chức năng đăng nhập | N |

### 5.3. Nhóm chuẩn hóa dữ liệu

| Mã | Yêu cầu | Mức |
|---|---|---|
| FR-NEN-14 | Hệ thống phải lưu các giá trị trạng thái, loại, mức bằng **mã quy ước cố định**, không lưu chuỗi tiếng Việt — hiện có **11 cột** đang lưu tiếng Việt | **B** |
| FR-NEN-15 | Hệ thống phải có **cột phân định công ty thành viên trên mọi bảng nghiệp vụ** — hiện thiếu **42 trên 57 bảng** | **B** |
| FR-NEN-16 | Hệ thống phải lọc phạm vi phòng ban **theo mã phòng ban**, không so sánh bằng tên phòng ban | **B** |
| FR-NEN-17 | Hệ thống phải dựng lại được từ cơ sở dữ liệu trống bằng cách chạy đủ chuỗi bước thay đổi cấu trúc từ đầu | **B** |

### 5.4. Nhóm nền cho phân hệ

| Mã | Yêu cầu | Mức |
|---|---|---|
| FR-NEN-18 | Hệ thống phải có **phân quyền tới mức từng trường dữ liệu**: trường bị che thì không xuất hiện trong dữ liệu trả về, áp dụng cho cả đường xuất tệp và đường tích hợp | **B** |
| FR-NEN-19 | Hệ thống phải có **bộ máy phê duyệt dùng chung**: thêm loại chứng từ cần duyệt chỉ bằng khai báo cấu hình; người duyệt khai theo vai trò tương đối chứ không theo tên người; có nhiều bậc; có ủy quyền khi vắng; và **giữ nguyên phiên bản luồng cho hồ sơ đang trình dở** | **B** |
| FR-NEN-20 | Hệ thống phải khai báo danh sách phân hệ tại **đúng một nơi**, và kiểm tra lúc khởi động rằng mọi loại dữ liệu thuộc đúng một phân hệ | **B** |
| FR-NEN-21 | Hệ thống phải hiển thị **lưới biểu tượng phân hệ** sau khi đăng nhập, chỉ hiện phân hệ mà người dùng có quyền | **B** |
| FR-NEN-22 | Hệ thống phải **giữ nguyên toàn bộ đường dẫn hiện có của phần mềm Thu mua** khi chuyển sang khung nhiều phân hệ | **B** |
| FR-NEN-23 | Hệ thống phải cho phép bật tắt khung nhiều phân hệ bằng công tắc cấu hình, để có đường lui | **B** |

### 5.5. Yêu cầu phi chức năng — điều chỉnh so với tài liệu yêu cầu

Giữ nguyên phần lớn chương 5 của tài liệu yêu cầu. Bốn điều chỉnh, đều có căn cứ từ hạ tầng thật:

| Mã | Yêu cầu | Điều chỉnh so với tài liệu yêu cầu |
|---|---|---|
| NFR-01 | Hệ thống phải phục vụ khoảng 300 tài khoản, 100 người dùng đồng thời, phản hồi màn hình thông thường dưới 3 giây | Giữ nguyên |
| NFR-02 | Hệ thống phải chạy trên giao thức bảo mật và **bắt buộc xác thực hai lớp cho vai trò nhân sự và quản trị hệ thống** | Giữ nguyên. **Hiện chưa có** — phải bổ sung trước khi phân hệ Nhân sự có dữ liệu thật |
| NFR-03 | Hệ thống phải sao lưu tự động và có **đợt thử phục hồi định kỳ hằng quý** | Sao lưu đang chạy **hai lần mỗi ngày**, tốt hơn mức yêu cầu. Nhưng **chưa từng thử phục hồi** — đây là việc một ngày công, đề nghị làm ngay |
| NFR-04 | Hệ thống phải đạt điểm phục hồi trong vòng **12 giờ** và thời gian phục hồi trong vòng **8 giờ làm việc** | **Chặt hơn** mức 24 giờ trong tài liệu yêu cầu, vì sao lưu đã chạy hai lần mỗi ngày |
| NFR-05 | Hệ thống phải ghi nhật ký thao tác bất biến, giữ **tối thiểu 5 năm**, ghi cả hành vi **xem và tải**, tra được theo người, theo đối tượng, theo khoảng thời gian | Giữ nguyên. Hiện đã ghi hành vi sửa, **chưa ghi hành vi xem và tải**, và chưa có chính sách lưu 5 năm |
| NFR-06 | Hệ thống phải mã hóa tệp lưu trữ | Giữ nguyên, nhưng **phải làm sau FR-NEN-03** — mã hóa một đường đi còn đang hở là vô nghĩa |
| NFR-07 | Hệ thống phải chạy trên **MySQL 8.4** | **Khác tài liệu yêu cầu**, vốn gợi ý PostgreSQL. Đề nghị giữ MySQL 8.4: hệ thống đang chạy thật trên nền này với 57 bảng và 75 bước thay đổi cấu trúc; đổi hệ quản trị cơ sở dữ liệu không mang lại giá trị nghiệp vụ nào mà chỉ thêm rủi ro |
| NFR-08 | Hệ thống phải hiển thị và xử lý đúng tiếng Việt ở mọi tầng, gồm cả tệp xuất ra | Giữ nguyên |
| NFR-09 | Hệ thống phải chạy tốt trên trình duyệt phổ biến bản mới, trên máy tính và điện thoại | Giữ nguyên. Giao diện hiện đã đáp ứng phần lớn |
| NFR-10 | Hệ thống phải tuân thủ Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân, và nguyên tắc kiểm soát tài liệu tại điều 7.5 của ISO 9001:2015 | Giữ nguyên |

---

## 6. KẾ HOẠCH CHO TỪNG PHÂN HỆ CỦA WORKHUB

Mười hai phân hệ theo tài liệu yêu cầu, cộng một phân hệ đề nghị bổ sung. Mỗi phân hệ ghi rõ: nền hiện có đỡ được bao nhiêu, phải xây thêm gì, phụ thuộc vào đâu.

### 6.1. Tầng nền tảng

**ORG — Tổ chức và phân quyền**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 60%.** Đã có ma trận quyền theo vai trò, cơ chế phạm vi dữ liệu theo từng lượt gán vai trò, bảng phòng ban và bảng công ty |
| Phải xây thêm | Rà lại danh sách vai trò theo bảy vai trò ở góc nhìn tập đoàn; quản lý danh mục chức danh chuẩn toàn tập đoàn; phân quyền tới mức từng trường; và toàn bộ nhóm vá tại mục 5.1 |
| Phụ thuộc | Không phụ thuộc phân hệ nào. **Mọi phân hệ khác phụ thuộc vào nó** |
| Điểm cần Ban lãnh đạo quyết | Tài liệu yêu cầu đặt **vị trí công việc làm thực thể trung tâm**, có "bộ yêu cầu vị trí" và suy quyền từ vị trí. Nền hiện tại coi chức danh là một danh mục và cấp quyền theo vai trò. Đây là khác biệt kiến trúc thật, phải quyết **trước khi tạo bảng** — mục 11 |

**WF — Luồng phê duyệt**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 20%.** Có 5 luồng phê duyệt đang chạy thật, nhưng mỗi luồng viết riêng, không dùng lại được |
| Phải xây thêm | Toàn bộ bộ máy dùng chung: khai báo cấu hình để thêm loại chứng từ, người duyệt theo vai trò tương đối, nhiều bậc, ủy quyền khi vắng, giữ phiên bản luồng cho hồ sơ đang trình dở, nhắc quá hạn |
| Phụ thuộc | Cần chuẩn hóa phòng ban theo mã và cột công ty thành viên xong trước |
| Ghi chú | Đây là **hạng mục lớn nhất của bước sửa nền**, và cũng là hạng mục đáng giá nhất: ban hành văn bản, quyết định nhân sự, duyệt kết quả công việc, duyệt cấp phúc lợi đều dùng chung nó |

**AUD — Nhật ký hệ thống**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 70%.** Đã ghi giá trị trước và sau mỗi lần sửa, có gom theo tháng |
| Phải xây thêm | Kiểm tra quyền khi đọc nhật ký; ghi thêm hành vi xem và tải; chính sách lưu tối thiểu 5 năm; màn hình tra cứu theo người, theo đối tượng, theo khoảng thời gian |
| Phụ thuộc | Không |

### 6.2. Tầng nghiệp vụ

**HRM — Quản lý nhân sự**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 30%.** Đã có bảng nhân sự và đã nối với tài khoản đăng nhập |
| Phải xây thêm, chia ba bậc | **Bậc 1** — danh mục cơ cấu tổ chức, hồ sơ nhân viên, phân quyền xem hồ sơ, dòng thời gian công tác, nhập dữ liệu nhân sự hiện có và đối chiếu. **Bậc 2** — hợp đồng lao động và cảnh báo hết hạn, giấy tờ và bằng cấp, quyết định nhân sự đi qua phê duyệt. **Bậc 3** — nghỉ phép tự nộp và duyệt trên web, nhân viên tự xem và đề nghị sửa hồ sơ, báo cáo nhân sự |
| Phụ thuộc | **Bắt buộc phải có phân quyền tới mức từng trường trước khi tạo bảng hợp đồng lao động.** Bậc 2 và bậc 3 cần bộ máy phê duyệt dùng chung |
| Hai bài học từ khảo sát phần mềm thương mại | (1) Hồ sơ nhân viên có khoảng 90 trường nhưng lúc tạo chỉ hỏi **12 trường** — bắt điền đủ ngay thì không ai nhập và dữ liệu thành rác. (2) Quy tắc nghỉ phép là **dữ liệu cấu hình, không phải mã nguồn** — họ khai 15 loại nghỉ trong một bảng cấu hình khoảng 50 cột |
| Điểm cần Ban lãnh đạo quyết | Tài liệu yêu cầu xếp **nghỉ phép và chấm công ra ngoài phạm vi**. Báo cáo này đề nghị **đưa nghỉ phép vào**: hồ sơ và hợp đồng là thứ một phòng dùng, nghỉ phép là thứ 300 người dùng — mục 11 |

**DOC — Quản lý văn bản**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 25%.** Trung tâm Hướng dẫn sử dụng đã chạy thật, chung tài khoản đăng nhập, đã có phần soạn nội dung và phân quyền xem, và đã xử lý làm sạch nội dung đưa từ ngoài vào |
| Phải xây thêm | Danh mục loại văn bản và sinh mã tự động; vòng đời soạn thảo đến lưu trữ; quản lý phiên bản có đánh dấu bản hết hiệu lực; xác nhận đã đọc và hiểu có theo dõi; tìm kiếm toàn văn trong tệp đính kèm |
| Phụ thuộc | **Bắt buộc phải vá lỗ hổng tệp đính kèm trước.** Cần bộ máy phê duyệt cho quy trình ban hành |
| Điểm cần Ban lãnh đạo quyết | Mở rộng Trung tâm Hướng dẫn sử dụng hay xây phân hệ mới — mục 11 |

**PAY — Phiếu lương điện tử**

| | |
|---|---|
| Nền hiện có đỡ được | **0%** |
| Phải xây thêm | Nhập bảng lương từ tệp Excel, đối chiếu theo mã nhân viên, phát phiếu, mỗi người chỉ xem phiếu của mình, ghi nhật ký từng lượt xem |
| Phụ thuộc | Phân hệ Nhân sự bậc 1. **Bắt buộc phải có phân quyền tới mức từng trường** |
| Ghi chú quan trọng | Tài liệu yêu cầu **không tính lương**, chỉ nhập và phát phiếu. Khảo sát phần mềm thương mại độc lập đi tới cùng kết luận: không đơn vị nào viết cứng công thức lương, họ làm cả một bộ máy công thức có hàm điều kiện và hàm làm tròn để khách tự khai. Làm tính lương không phải làm một màn hình mà là làm một ngôn ngữ kịch bản thu nhỏ. **Đề nghị giữ nguyên phạm vi: không tính lương** |

**LMS — Đào tạo nội bộ**

| | |
|---|---|
| Nền hiện có đỡ được | **0%** |
| Phải xây thêm | Toàn bộ: khóa học sinh từ tài liệu, giao khóa học theo vị trí, ngân hàng câu hỏi, chấm tự động, chứng chỉ có hạn và nhắc đào tạo lại |
| Phụ thuộc | Phân hệ Văn bản (nguồn tài liệu học) và phân hệ Tổ chức (bộ yêu cầu vị trí) |

**TASK — Quản lý công việc**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 30%.** Công cụ Quản lý Dự án cho Ban điều hành đã chạy thật, chung máy chủ và chung tài khoản |
| Phải xây thêm | Bảng công việc dạng thẻ, việc con, giao việc định kỳ, duyệt kết quả đạt hoặc chưa đạt, báo cáo công việc theo kỳ |
| Phụ thuộc | Bộ máy phê duyệt dùng chung; phân hệ Nhân sự để biết ai thuộc phòng nào |
| Điểm cần Ban lãnh đạo quyết | Mở rộng công cụ Quản lý Dự án hiện có hay xây phân hệ mới cho toàn tập đoàn — hai nhóm người dùng khác nhau, mục 11 |

**FDB — Góp ý và phản hồi**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 40%.** Phiếu hỗ trợ đã chạy trên cả hai môi trường, có phân công người phụ trách và có luồng xử lý |
| Phải xây thêm | Kênh góp ý **ẩn danh** — và đây là phần khó nhất, vì phải không lưu bất cứ thứ gì truy ngược được danh tính, **kể cả trong nhật ký thao tác**, đồng thời vẫn cấp được mã tra cứu cho người gửi |
| Phụ thuộc | Mâu thuẫn kỹ thuật trực tiếp với yêu cầu ghi nhật ký đầy đủ. **Phải thiết kế đường ghi riêng, không dùng chung** |

### 6.3. Tầng giao tiếp

**POR — Trang cá nhân**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 20%.** Có màn hình thông báo cá nhân, chưa có trang gộp |
| Phải xây thêm | Trang "Việc của tôi" gộp mọi thứ đang chờ người dùng xử lý, bất kể sinh ra từ phân hệ nào |
| Phụ thuộc | Có bao nhiêu phân hệ thì trang này mới có bấy nhiêu nội dung. Làm phần khung sớm, bổ sung nguồn dần |

**NTF — Thông báo và nhắc việc**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 70%.** Thông báo trong ứng dụng, thư điện tử và thông báo đẩy trên trình duyệt đều đã chạy thật |
| Phải xây thêm | Bộ quy tắc cảnh báo cấu hình được (nhắc trước bao nhiêu ngày, nhắc ai); kênh Zalo |
| Phụ thuộc | Không |

**RPT — Báo cáo và bảng điều khiển**

| | |
|---|---|
| Nền hiện có đỡ được | **Khoảng 25%.** Đã có báo cáo cho nghiệp vụ thu mua |
| Phải xây thêm | Bảng điều khiển theo vai trò cho Ban lãnh đạo, trưởng bộ phận, nhân sự, người quản trị tài liệu |
| Phụ thuộc | **Bắt buộc phải chuẩn hóa dữ liệu trạng thái trước.** Còn 11 cột lưu tiếng Việt thì không gộp số liệu xuyên phân hệ được |

### 6.4. Phân hệ đề nghị bổ sung — Phúc lợi và Bán lẻ

Không có trong tài liệu yêu cầu WorkHub. Đề nghị bổ sung vì là nhu cầu có thật và đã được nêu: tập đoàn có một quán cà phê, mỗi nhân sự tùy chức vụ được cấp một số điểm mỗi tháng để tiêu tại quầy, quán đang chạy trên phần mềm bán hàng POS365.

Phân hệ này tách làm **hai phần độc lập**, vì một phần tự chủ hoàn toàn còn một phần phụ thuộc năng lực kỹ thuật của bên thứ ba:

| Phần | Nội dung | Phụ thuộc |
|---|---|---|
| **A — Chính sách điểm** | Danh mục định mức điểm theo chức danh; sổ cái ghi mọi biến động điểm; cấp điểm theo kỳ có bước xem trước và có phê duyệt; xử lý người vào và người nghỉ trong kỳ; nhân viên tự xem số dư | **Tự chủ hoàn toàn.** Chỉ cần phân hệ Nhân sự bậc 1 (để có chức danh) và bộ máy phê duyệt |
| **B — Đầu nối phần mềm bán hàng** | Ghép nhân sự với khách hàng bên phần mềm bán hàng; đẩy điểm sang quầy; kéo về dữ liệu tiêu điểm; đối chiếu chênh lệch hằng ngày | **Phụ thuộc bên thứ ba.** Chưa xác định được phần mềm bán hàng có cho ghi dữ liệu bằng khóa máy hay không |

**Việc đầu tiên của phần B không phải viết mã, mà là hai ngày công gọi thử giao diện kỹ thuật của phần mềm bán hàng** để trả lời chín câu, trong đó ba câu quyết định: có cấp được khóa truy cập cho máy không (hay chỉ đăng nhập bằng người), có ghi được điểm vào không (hay chỉ đọc được), và trường nào mới là số dư mà quầy trừ khi bán hàng. **Nếu câu trả lời là không ghi được, phần B không tồn tại** và thay bằng một màn hình tra cứu số dư cho thu ngân.

**Đề nghị chạy tay tháng đầu tiên.** Vài chục người thì cấp điểm bằng bảng tính mất khoảng nửa giờ mỗi tháng, trong khi phần mềm hóa mất vài tuần công. Tháng chạy tay là cách rẻ nhất để phát hiện các quy tắc nghiệp vụ chưa được trả lời — trong đó có một câu mà đội phần mềm **không tự trả lời được**: phúc lợi này có tính thuế thu nhập cá nhân không. Câu đó phải hỏi kế toán trước khi bàn giao số liệu.

**Đề nghị không tự viết phần mềm bán hàng tại quầy trong năm 2026.** Màn hình bán hàng là phần dễ nhất. Phần đắt là chạy khi mất mạng, phần cứng đầu đọc và máy in, hóa đơn điện tử theo quy định nhà nước, ca kíp kiểm quỹ, và trừ kho theo định lượng. Phần mềm hiện tại đang chạy được, nên viết lại để **bằng** cái đang có là bỏ vài tháng công đổi lấy con số không.

---

## 7. LỘ TRÌNH VÀ MỐC THỜI GIAN

### 7.1. Cách đọc phần này

Ba điều phải nói trước:

1. Ngày ở đây là **ngày dự kiến có điều kiện**, không phải ngày cam kết giao hàng.
2. **Toàn bộ mốc phụ thuộc vào việc có tách được một người ra khỏi hàng chờ yêu cầu thay đổi của phần mềm Thu mua hay không.** Chưa có quyết định đó thì bảng dưới là **thứ tự**, không phải **ngày**.
3. Bảng dưới tính theo kịch bản: hai người hiện có, một người được tách khoảng 70% thời gian, có công cụ trí tuệ nhân tạo hỗ trợ.

### 7.2. Sáu giai đoạn

| Giai đoạn | Nội dung | Thời lượng | Kết quả dùng được khi kết thúc |
|---|---|---|---|
| **GĐ 0 — Sửa nền** | Toàn bộ mục 5 | **3,5 tháng** | Nền chịu được dữ liệu nhân sự. Xây một phân hệ danh mục mới dưới 50 dòng mã. Thêm loại chứng từ cần duyệt chỉ bằng khai báo cấu hình. Người dùng thấy lưới biểu tượng phân hệ |
| **GĐ 1 — Tổ chức và Con người** | ORG đầy đủ · HRM ba bậc · POR mức tối thiểu · NTF bộ quy tắc cảnh báo · AUD hoàn thiện | **2,5 tháng** | **Khoảng 300 hồ sơ nhân sự số hóa và đối chiếu khớp.** Nhân viên tự nộp đơn nghỉ phép, trưởng phòng duyệt trên web. Hợp đồng sắp hết hạn có cảnh báo tự động |
| **GĐ 2 — Văn bản** | DOC đầy đủ · WF cho quy trình ban hành · tìm kiếm toàn văn | **2 – 2,5 tháng** | Văn bản có mã tự động, có phiên bản, có xác nhận đã đọc. Đủ điều kiện cho ISO 9001 điều 7.5 |
| **GĐ 3 — Phúc lợi và Bán lẻ** | Phần A chính sách điểm · phần B đầu nối nếu khả thi | **1,5 – 2 tháng** | Cấp điểm theo chức danh chạy tự động, có duyệt, có sổ cái, có đối chiếu |
| **GĐ 4 — Công việc và Học tập** | TASK · LMS · FDB · RPT · PAY | **3 – 4 tháng** | Giao việc và theo dõi trên hệ thống. Đào tạo nội bộ có chứng chỉ. Bảng điều khiển cho Ban lãnh đạo |
| **GĐ 5 — Hiệu quả và Năng lực** | Quản lý mục tiêu · đánh giá theo kỳ · khung năng lực · kế hoạch phát triển cá nhân | Theo nhu cầu | Chỉ bắt đầu sau khi GĐ 4 chạy ổn định tối thiểu 3 tháng |

Sau GĐ 5 là nhóm mở rộng của tài liệu yêu cầu: quản lý dự án đầy đủ, trao đổi nội bộ, trợ lý tri thức, phân tích bằng trí tuệ nhân tạo, tích hợp kế toán và chấm công.

### 7.3. Một đề nghị khác so với lộ trình gợi ý trong tài liệu yêu cầu

Tài liệu yêu cầu gợi ý giai đoạn 1A gồm **Tổ chức và Văn bản** đi cùng nhau, rồi giai đoạn 1B mới đến **Con người**. Báo cáo này đề nghị **tách Văn bản ra sau Con người**, tức thứ tự thành: Tổ chức → Con người → Văn bản.

Ba lý do:

| # | Lý do |
|---|---|
| 1 | **Hồ sơ nhân sự là dữ liệu gốc mà mọi phân hệ sau đều đọc.** Văn bản cần biết ai ký, Đào tạo cần biết ai học, Công việc cần biết ai thuộc phòng nào, Phúc lợi cần biết ai giữ chức danh gì. Có hồ sơ trước thì các phân hệ sau đều rẻ hơn |
| 2 | **Phân hệ Nhân sự rẻ hơn phân hệ Văn bản trên nền hiện có**, vì đã sẵn bảng nhân sự và đã nối với tài khoản đăng nhập; trong khi phân hệ Văn bản gần như phải xây mới phần vòng đời và phần phiên bản |
| 3 | **Trung tâm Hướng dẫn sử dụng đang gánh tạm** nhu cầu tra cứu tài liệu nội bộ, nên hoãn phân hệ Văn bản không để lại khoảng trống ngay lập tức. Trong khi hồ sơ nhân sự hiện vẫn nằm trên tệp rời |

Đây là đề nghị, không phải quyết định của đội phần mềm. Đưa vào mục 11 để Ban lãnh đạo chốt.

### 7.4. Lịch theo nửa tháng đến mốc nửa năm

| Kỳ | Nội dung | Trình diễn cuối kỳ cho Ban lãnh đạo |
|---|---|---|
| **Nửa sau T8/2026** | Vá bốn lỗ hổng. Bắt đầu ghi nhật ký truy cập. **Song song: bắt đầu phỏng vấn — bước KS1 và KS2** | Dán đường dẫn tệp hợp đồng vào cửa sổ trình duyệt ẩn danh: bị chặn. Mở hồ sơ nhân sự phòng khác bằng mã trực tiếp: bị từ chối |
| **Nửa đầu T9/2026** | Phần dùng chung: khuôn mã lỗi, khuôn ngữ cảnh gọi. **Phỏng vấn kết thúc, chấm ưu tiên, ký bảng chốt phạm vi phân hệ Nhân sự** | **Bảng chốt phạm vi phân hệ Nhân sự có chữ ký.** Đây là mốc chặn lớn nhất của cả lộ trình |
| **Nửa sau T9/2026** | Phần dùng chung: tầng truy vấn và tầng nghiệp vụ nền | Xây một phân hệ danh mục mới từ đầu, trước mặt người xem, dưới 50 dòng mã, và nó tự có đầy đủ phân quyền |
| **Nửa đầu T10/2026** | Bộ kiểm thử quy ước nền. Bật kiểm tra quyền xuất tệp **sau khi đã đọc hai tuần nhật ký để biết ai đang thực sự xuất** | Cố tình vi phạm một quy ước trong nhánh nháp: bộ kiểm báo đỏ đúng quy ước đó |
| **Nửa sau T10/2026** | Chuẩn hóa phòng ban theo mã. Cột công ty thành viên cho nhóm bảng nhân sự. Phân quyền tới mức từng trường. **Song song: hai ngày gọi thử phần mềm bán hàng** | Đổi tên một phòng ban trên môi trường thử: chứng từ cũ vẫn nằm đúng phạm vi. Và: biết được phần B của phân hệ quán cà phê có làm được hay không |
| **Nửa đầu T11/2026** | Khung nhiều phân hệ và lưới biểu tượng | **Lưới biểu tượng phân hệ chạy thật.** Mở 20 đường dẫn cũ lấy ngẫu nhiên từ dữ liệu thông báo đã gửi: vẫn vào đúng chỗ |
| **Nửa sau T11/2026** | Bộ máy phê duyệt dùng chung, kèm phép thử chuyển một loại chứng từ Thu mua sang | Người dùng Thu mua **không nhận ra gì thay đổi**. Đó chính là tiêu chí đạt |
| **Nửa đầu T12/2026** | Phân hệ Nhân sự bậc 1: danh mục cơ cấu, hồ sơ nhân viên, phân quyền xem | Chứng minh phân quyền bằng bộ kiểm tự động, gồm cả trường hợp mở bằng mã trực tiếp và trường hợp xuất tệp |
| **Nửa sau T12/2026** | Nhập dữ liệu nhân sự hiện có và đối chiếu | **Số trên hệ thống khớp số phòng Nhân sự đang giữ, từng người một.** Không khớp thì không qua kỳ này |
| **Nửa đầu T1/2027** | Phân hệ Nhân sự bậc 2: hợp đồng lao động, giấy tờ, quyết định nhân sự | Danh sách hợp đồng sắp hết hạn chạy thật. Mức lương chỉ hiện với người được cấp quyền trên trường đó |
| **Nửa sau T1/2027** | Phân hệ Nhân sự bậc 3: nghỉ phép, tự phục vụ | Một nhân viên thật nộp đơn nghỉ phép, một trưởng phòng thật duyệt trên web, số ngày phép còn lại giảm đúng |
| **Nửa đầu T2/2027** | Báo cáo nhân sự, trang cá nhân mức tối thiểu, một vòng quay lại sửa nền | **Phân hệ Tổ chức và phân hệ Nhân sự vận hành chính thức** |
| **MỐC 15/02/2027** | | **Nền đã sửa xong. Hai phân hệ WorkHub chạy thật. Thu mua trở thành một phân hệ, không gián đoạn ngày nào** |

Sau mốc này: phân hệ Văn bản tháng 2–4/2027; phân hệ Phúc lợi và Bán lẻ tháng 4–5/2027; nhóm Công việc, Đào tạo, Góp ý, Báo cáo, Phiếu lương từ quý 3/2027 sang 2028.

### 7.5. Thứ tự cắt khi trượt lịch

Quyết trước để lúc trượt không phải tranh luận:

| Thứ tự | Cắt cái gì | Vì sao cắt được |
|---|---|---|
| Cắt đầu tiên | Báo cáo nhân sự; trang cá nhân gộp | Chạy tạm bằng chức năng xuất tệp |
| Cắt thứ hai | Đưa Trung tâm Hướng dẫn sử dụng và công cụ Quản lý Dự án vào lưới biểu tượng | Hai ứng dụng đó đang chạy riêng và người dùng đã quen |
| Cắt thứ ba | Phân hệ Phúc lợi và Bán lẻ đẩy lùi | Có phương án chạy tay bằng bảng tính |
| Cắt thứ tư | Nghỉ phép và tự phục vụ đẩy sang bản 2 | Đau, vì đây là phần 300 người cảm nhận được giá trị. Nhưng hồ sơ và hợp đồng vẫn dùng được nếu thiếu phần này |
| **Không cắt** | **Toàn bộ nhóm vá gấp · phần dùng chung · bộ kiểm thử quy ước nền · phân quyền tới mức từng trường · bộ máy phê duyệt** | Cắt nhóm vá là để lỗ hổng hở khi hệ thống đã có dữ liệu lương và giấy tờ tùy thân. Cắt phần dùng chung là hơn mười phân hệ xây ra rồi phải dọn lại. Cắt bộ máy phê duyệt là sinh ra luồng duyệt viết tay thứ sáu, thứ bảy |

---

## 8. NHÂN LỰC

### 8.1. Cách tính

Đơn vị: **tuần-người thuần** — một tuần làm việc của một người, đã trừ họp, nghỉ và thời gian bảo trì phần mềm đang chạy.

| Giai đoạn | Tuần-người thuần |
|---|---|
| GĐ 0 — Sửa nền | 31 – 43 |
| GĐ 1 — Tổ chức và Con người | 11 – 17 |
| **Cộng đến mốc 15/02/2027** | **42 – 60** |
| Trừ khoảng 15% nhờ trí tuệ nhân tạo | **36 – 51** |

Nửa năm từ 15/08/2026 đến 15/02/2027 là **26 tuần lịch**.

### 8.2. Ba kịch bản

| | **Kịch bản A** — hai người hiện có, một người được tách 70% khỏi hàng chờ yêu cầu thay đổi | **Kịch bản B** — hai người hiện có, không ai được tách | **Kịch bản C** — kịch bản A cộng một người mới từ tháng 9 |
|---|---|---|---|
| Năng lực trong 26 tuần | ~**30 tuần-người** | ~**23 tuần-người** | ~**38 tuần-người** |
| Người mới đóng góp | — | — | Tháng 1–2: **âm 3** (chi phí kèm cặp). Tháng 3–4: +4. Tháng 5–6: +7. **Cộng khoảng +8** |
| Cần | 36 – 51 | 36 – 51 | 36 – 51 |
| **Kết quả** | **Thiếu 6 – 21.** Đạt mốc 15/02/2027 **nếu cắt theo đúng thứ tự tại mục 7.5** | **Thiếu 13 – 28. Không đạt**, trượt sang khoảng **tháng 4 – 5/2027** | **Thiếu 0 – 13.** Đạt, và **dư năng lực từ tháng thứ bảy trở đi** |

Cơ sở của phép trừ bảo trì: phần mềm Thu mua đang chạy thật phát sinh **xấp xỉ một yêu cầu thay đổi mỗi ngày làm việc**. Đây là con số cần được xác nhận lại, nhưng dù sai lệch theo hướng nào thì khoảng cách giữa ba kịch bản vẫn lớn hơn sai số của nó.

### 8.3. Về việc tuyển thêm người

Người mới đóng góp khoảng **+8 tuần-người trong nửa năm đầu** — đủ để kéo kịch bản A từ "phải cắt phạm vi" thành "không phải cắt", **không đủ để rút ngắn mốc**, vì hai đến ba tháng đầu là đào tạo.

**Khuyến nghị vẫn là tuyển từ tháng 9/2026**, với ba căn cứ khác:

| # | Căn cứ |
|---|---|
| 1 | **Phần việc sau phân hệ Nhân sự dài gấp nhiều lần phần trước.** Các phân hệ còn lại của WorkHub là chương trình hai đến ba năm. Nửa năm này chỉ là đoạn đầu |
| 2 | **Đang có phụ thuộc vào một người.** Công cụ đồng bộ dữ liệu giữa các môi trường hiện là kịch bản chạy tay nằm trên máy một người, chưa đưa vào kho mã chung. Đây là rủi ro vận hành, không phải rủi ro tiến độ |
| 3 | **Chi phí kèm cặp trả một lần, năng lực giữ lại nhiều năm.** Trả hai đến ba tháng bây giờ rẻ hơn trả đúng khoản đó vào lúc đang chạy nước rút của một phân hệ khác. Tuyển muộn hơn 15/09/2026 thì phần đóng góp trong nửa năm này gần bằng không |

### 8.4. Người mới làm gì trong hai đến ba tháng đầu

Nguyên tắc phân việc: **việc lặp và kiểm chứng được thì giao; việc quyết định và việc động vào dữ liệu thật thì không.**

| Giao được ngay | Không giao trong ba tháng đầu |
|---|---|
| Chuyển các phân hệ nghiệp vụ sang phần dùng chung — có khuôn mẫu, có bộ kiểm cũ xác nhận | Vá lỗ hổng phạm vi và phân quyền — sai một chỗ là hở dữ liệu |
| Chuẩn hóa các cột trạng thái ở nhóm bảng ít liên đới | Thêm cột công ty thành viên trên dữ liệu thật — sai là hỏng dữ liệu không lui được |
| Viết bộ kiểm thử quy ước nền | Đầu nối phần mềm bán hàng — dính tiền và dính hệ thống bên ngoài |
| Phần giao diện: lưới biểu tượng, điều hướng | Chủ trì phỏng vấn, chốt phạm vi nghiệp vụ |
| Xây phân hệ danh mục mới sau khi đã có phần dùng chung | Thao tác trực tiếp trên hệ thống chạy thật |

**Ràng buộc bắt buộc:** người mới làm việc trên môi trường thử nghiệm, không truy cập hệ thống chạy thật, không có công cụ truy vấn cơ sở dữ liệu trực tiếp, và ký cam kết bảo mật trước khi được cấp tài khoản.

---

## 9. DANH MỤC MỞ RỘNG NGOÀI PHẠM VI BẢN 1

Những việc đã nhận diện nhưng chưa có chỗ trong lịch đến 15/02/2027. Ghi ra để không phải phát hiện lại, và để khi có chỗ trống thì biết lấy gì lấp vào.

**Quy tắc:** một mục chỉ rời khỏi danh mục này khi có đủ ba thứ — mã yêu cầu, mức ưu tiên đã được duyệt, và một giai đoạn cụ thể.

| # | Nội dung | Mức | Vòng dự kiến | Ghi chú |
|---|---|---|---|---|
| 1 | **Xác thực hai lớp bắt buộc cho vai trò nhân sự và quản trị** | **B** | Nên chen vào GĐ 1, **trước khi phân hệ Nhân sự có dữ liệu thật** | Bật muộn thì vướng thói quen người dùng đã hình thành |
| 2 | **Đợt thử phục hồi sao lưu định kỳ hằng quý** | **B** | Chen vào bất kỳ lúc nào — **việc một ngày công** | Sao lưu chạy hai lần mỗi ngày nhưng **chưa từng phục hồi thử**. Bản sao lưu chưa phục hồi thử là bản sao lưu chưa tồn tại |
| 3 | **Đưa công cụ đồng bộ dữ liệu giữa môi trường vào kho mã chung** | **B** | Chen vào GĐ 0 | Gỡ phụ thuộc vào một người |
| 4 | **Chính sách lưu nhật ký tối thiểu 5 năm và màn hình tra cứu** | **B** | GĐ 0 phần chính sách, GĐ 2 phần công cụ | |
| 5 | **Mô hình lấy vị trí công việc làm trung tâm** — bộ yêu cầu vị trí, tự sinh việc khi gán vị trí | N | Phải quyết **trước** GĐ 1 | Quyết sau khi đã tạo bảng nhân sự là phải làm lại |
| 6 | **Mã hóa tệp lưu trữ** | N | Sau khi vá xong đường tải tệp | |
| 7 | **Kênh Zalo cho thông báo** | T | Sau GĐ 2 | Cần chốt dùng tài khoản Zalo chính thức hay kênh tự vận hành |
| 8 | **Phiếu lương điện tử** | N | GĐ 4 | Cần phân quyền tới mức từng trường |
| 9 | **Góp ý ẩn danh** | N | GĐ 4 | Mâu thuẫn kỹ thuật với yêu cầu ghi nhật ký đầy đủ, phải thiết kế đường ghi riêng |
| 10 | **Chấm công** | T | Chưa xếp | Tài liệu yêu cầu xếp ngoài phạm vi. Nếu làm thì đây là trường hợp tích hợp đi vào đầu tiên |
| 11 | **Quản lý mục tiêu, đánh giá theo kỳ, khung năng lực** | T | GĐ 5 | Chỉ sau khi GĐ 4 chạy ổn định 3 tháng |
| 12 | **Trợ lý tri thức hỏi đáp quy trình, có dẫn nguồn** | T | Sau phân hệ Văn bản | Không có phân hệ Văn bản thì không có nguồn để dẫn |
| 13 | **Trao đổi nội bộ trong hệ thống** | T | Chưa xếp | |
| 14 | **Quản lý dự án đầy đủ có biểu đồ tiến độ** | T | Chưa xếp | |
| 15 | **Tích hợp với phần mềm kế toán** | T | Chưa xếp | |
| 16 | **Cơ chế phát sự kiện cho hệ thống bên ngoài** | N | Chạy song song được từ sau GĐ 0 | Chưa có trường hợp sử dụng chốt |

**Ba mục đáng chen vào sớm nhất dù đang ở danh mục này:** số 2 (thử phục hồi sao lưu), số 3 (gỡ phụ thuộc một người), số 5 (quyết mô hình vị trí công việc trước khi tạo bảng).

---

## 10. NGHIỆM THU VÀ ĐIỀU KIỆN THÀNH CÔNG NGOÀI PHẦN MỀM

### 10.1. Nguyên tắc nghiệm thu

Bốn nguyên tắc đầu lấy theo tài liệu yêu cầu, hai nguyên tắc sau bổ sung từ thực tế rà soát:

| # | Nguyên tắc |
|---|---|
| 1 | Mỗi yêu cầu mức **B** phải có ít nhất một kịch bản kiểm thử. Giai đoạn chỉ được nghiệm thu khi **toàn bộ** yêu cầu mức B của giai đoạn đó đạt |
| 2 | Đội phần mềm lập và cập nhật **ma trận truy vết** — bảng đối chiếu từng yêu cầu với chức năng đã xây và kịch bản kiểm thử |
| 3 | Trước khi dùng chính thức, mỗi giai đoạn có đợt chạy thử với người dùng thật **tối thiểu hai tuần** tại một đơn vị làm điểm, rồi mới nhân rộng |
| 4 | Mọi thay đổi phạm vi phải ghi bằng văn bản và thành phiên bản mới của tài liệu |
| 5 | **Bổ sung:** không nhận "đã lập trình xong" làm bằng chứng. Điều kiện nghiệm thu phải là thứ **kiểm chứng lại được** bởi người khác |
| 6 | **Bổ sung:** với mỗi cấu hình bảo mật, bộ kiểm phải chứng minh **nó có tác dụng**, không phải chứng minh nó lưu được. Rà soát đã phát hiện **hai trường hợp** cấu hình có màn hình đầy đủ nhưng không có hiệu lực |

### 10.2. Bảy tiêu chí nghiệm thu mốc 15/02/2027

Mốc coi là đạt khi cả bảy điều dưới đây làm được trước mặt người kiểm:

| # | Tiêu chí | Cách kiểm |
|---|---|---|
| 1 | Không còn lỗ hổng nào trong bốn lỗ hổng tại mục 3.3 | Dán đường dẫn tệp hợp đồng vào cửa sổ ẩn danh: bị chặn. Mở hồ sơ nhân sự ngoài phạm vi bằng mã trực tiếp: bị từ chối. Đọc nhật ký của chứng từ ngoài phạm vi: không ra dòng nào. Đặt loại trừ một phòng ban rồi đếm lại: số dòng giảm đúng |
| 2 | Thêm loại dữ liệu mới mà quên khai phạm vi thì **hệ thống báo lỗi ngay** | Tạo một loại dữ liệu nháp, chạy thử |
| 3 | Xây một phân hệ danh mục mới **dưới 50 dòng mã** mà vẫn đủ quyền, phạm vi, nhật ký, phân trang, xuất tệp | Xây trực tiếp trước mặt người kiểm |
| 4 | Người dùng Thu mua đăng nhập vẫn vào thẳng công việc cũ; **20 đường dẫn cũ lấy ngẫu nhiên** từ dữ liệu thông báo đã gửi vẫn vào đúng chỗ | Thử toàn bộ 20 đường dẫn |
| 5 | Thêm một loại chứng từ cần duyệt **chỉ bằng khai báo cấu hình**, không viết dòng mã nào | Thêm một loại nháp trước mặt người kiểm |
| 6 | **Số nhân sự trên hệ thống khớp số phòng Nhân sự đang giữ, từng người một** | Đối chiếu toàn bộ, không lấy mẫu |
| 7 | Một nhân viên thật nộp đơn nghỉ phép, một trưởng phòng thật duyệt trên web, số ngày phép còn lại giảm đúng | Chạy với người thật, không dùng tài khoản kiểm thử |

### 10.3. Điều kiện thành công ngoài phần mềm

Không phần mềm nào thay được sáu điều dưới đây:

| # | Điều kiện | Ai chịu trách nhiệm | Hạn |
|---|---|---|---|
| 1 | **Quyết định về nhân lực**: ai làm chương trình này, và người đó có được tách khỏi hàng chờ yêu cầu thay đổi của Thu mua không | Ban lãnh đạo | **Trước khi bắt đầu phần dùng chung.** Đây là điều kiện chặn nặng nhất |
| 2 | **Chốt danh sách chức danh chuẩn toàn tập đoàn** — dữ liệu gốc quan trọng nhất của phân hệ Nhân sự | Văn phòng Điều hành chủ trì cùng các trưởng bộ phận | Trước GĐ 1 |
| 3 | **Mỗi công ty thành viên cử một đầu mối** chịu trách nhiệm nhập và xác nhận hồ sơ nhân sự | Giám đốc từng công ty thành viên | Trong GĐ 1 |
| 4 | **Chỉ định người quản trị tài liệu cấp tập đoàn** trước khi phân hệ Văn bản chạy thật | Tổng Giám đốc | Trước GĐ 2 |
| 5 | **Ban lãnh đạo giữ lịch xem trình diễn hai tuần một lần** suốt các giai đoạn phát triển | Ban lãnh đạo | Xuyên suốt |
| 6 | **Ban hành quy định hiệu lực**: kể từ ngày ấn định, việc hoặc văn bản không có trên hệ thống là chưa được ghi nhận | Tổng Giám đốc | Khi từng phân hệ chạy thật |

---

## 11. NỘI DUNG CẦN BAN LÃNH ĐẠO QUYẾT ĐỊNH

Bảy nội dung. Mỗi nội dung có giá trị mặc định nếu quá hạn chưa có quyết định, trừ nội dung số 1.

| # | Nội dung | Người quyết | Hạn | Chặn gì | Mặc định nếu quá hạn |
|---|---|---|---|---|---|
| 1 | **Nhân lực**: ai làm chương trình này, có tách người khỏi hàng chờ yêu cầu thay đổi của Thu mua không, có tuyển thêm từ tháng 9 không | Ban lãnh đạo | **Trước 15/09/2026** | Toàn bộ mốc tại mục 7 | **Không có mặc định.** Chưa quyết thì mục 7 là thứ tự, không phải ngày |
| 2 | **Thứ tự: Văn bản trước hay Con người trước** — tài liệu yêu cầu gợi ý Văn bản đi cùng Tổ chức ở giai đoạn đầu; báo cáo này đề nghị đưa Con người lên trước, lý do tại mục 7.3 | Tổng Giám đốc | Trước GĐ 1 | Toàn bộ mục 7 | Theo đề nghị của báo cáo: Tổ chức → Con người → Văn bản |
| 3 | **Có áp mô hình lấy vị trí công việc làm trung tâm không** — tài liệu yêu cầu đặt vị trí làm thực thể trung tâm và suy quyền từ vị trí; nền hiện tại coi chức danh là danh mục và cấp quyền theo vai trò | Ban điều hành, theo đề xuất của Công nghệ thông tin và Nhân sự | **Trước GĐ 1** | Thiết kế bảng của phân hệ Nhân sự. **Quyết sau khi đã tạo bảng là phải làm lại** | Chưa áp trong bản 1, chức danh giữ dạng danh mục, nhưng **thiết kế bảng phải chừa chỗ** để lắp vào sau mà không phải chuyển dữ liệu |
| 4 | **Nghỉ phép có nằm trong phạm vi không** — tài liệu yêu cầu xếp ra ngoài; báo cáo này đề nghị đưa vào | Ban điều hành cùng phòng Nhân sự | Trước GĐ 1 | Phạm vi phân hệ Nhân sự bậc 3 | **Làm.** Hồ sơ và hợp đồng là thứ một phòng dùng; nghỉ phép là thứ 300 người dùng |
| 5 | **Phân hệ Văn bản: mở rộng Trung tâm Hướng dẫn sử dụng hay xây mới** | Ban điều hành | Trước GĐ 2 | Kế hoạch GĐ 2 | Mở rộng cái đang chạy, vì nội dung và người dùng đã ở đó |
| 6 | **Phân hệ Công việc: mở rộng công cụ Quản lý Dự án hay xây mới** | Ban điều hành | Trước GĐ 4 | Kế hoạch GĐ 4 | Giữ công cụ hiện có cho Ban điều hành, xây phân hệ Công việc toàn tập đoàn riêng — hai nhóm người dùng khác nhau |
| 7 | **Bật xác thực hai lớp cho vai trò nhân sự và quản trị từ khi nào** | Tổng Giám đốc, theo đề xuất Công nghệ thông tin | Trước khi phân hệ Nhân sự có dữ liệu thật | Không chặn kỹ thuật, nhưng bật muộn thì vướng thói quen người dùng | Bật cùng lúc với GĐ 1 |

Ngoài bảy nội dung trên, phân hệ Phúc lợi và Bán lẻ cần thêm **mười câu hỏi nghiệp vụ** được trả lời trước khi lập trình — trong đó có câu phúc lợi này có tính thuế thu nhập cá nhân không, là câu đội phần mềm không tự trả lời được.

---

## 12. RỦI RO

| # | Rủi ro | Dấu hiệu sớm | Chặn bằng gì |
|---|---|---|---|
| 1 | **Lịch trượt vì đội vẫn gánh phần mềm đang chạy** | Yêu cầu thay đổi của Thu mua vẫn vào đều mà không ai được rút khỏi lộ trình | Nội dung số 1 tại mục 11. Kịch bản B tại mục 8.2 cho thấy hậu quả: trượt hai đến ba tháng |
| 2 | **Lộ dữ liệu lương và giấy tờ tùy thân** | **Không có dấu hiệu sớm** — loại rủi ro chỉ biết khi đã xảy ra. Và kiểu bỏ sót gây ra nó **đã xảy ra bốn lần** | Nhóm vá gấp làm trước tất cả. Phân quyền tới mức từng trường xong trước khi thiết kế bảng hợp đồng lao động. Không ngoại lệ |
| 3 | **Cấu hình bảo mật có màn hình nhưng không có tác dụng** | Không có dấu hiệu nào — đó chính là điểm nguy. Đã có **hai trường hợp thật** | Nguyên tắc nghiệm thu số 6 tại mục 10.1 |
| 4 | **Phạm vi phình ra khi phỏng vấn** | Xuất hiện yêu cầu "tiện thể làm luôn" trong biên bản phỏng vấn | Quy tắc cứng ở bước KS3: **số dòng mức B không quá 40%**. Yêu cầu mới vào danh mục chờ, không chen ngang |
| 5 | **Phần dùng chung bị hoãn tới sau phân hệ Nhân sự** | Phân hệ Nhân sự đầu tiên xây xong mà chưa có phần dùng chung | Phần dùng chung nằm trong danh sách **không cắt** tại mục 7.5 |
| 6 | **Bộ máy phê duyệt bị coi là việc kỹ thuật để sau** | Có đề nghị "làm Nhân sự trước, duyệt tính sau" | Tài liệu yêu cầu xếp Luồng phê duyệt vào **tầng nền tảng**, không phải tầng nghiệp vụ. Đây là nền dùng chung, không phải việc riêng của phân hệ Nhân sự |
| 7 | **Người mới không lên được trong ba tháng** | Hết tháng thứ ba vẫn cần rà từng dòng mã người đó viết | Phân việc theo mục 8.4. Nếu tháng thứ ba chưa đạt thì **hạ kỳ vọng xuống kịch bản A**, không kéo dài kèm cặp vô hạn |
| 8 | **Đầu nối phần mềm bán hàng không khả thi nhưng đã hứa với quán** | Có lịch hẹn triển khai trước khi có kết quả gọi thử | Phần B của phân hệ Phúc lợi có điều kiện vào ghi rõ. Và có phương án chạy tay viết sẵn để không phải hứa |
| 9 | **Chuẩn hóa dữ liệu làm vỡ hệ thống đang chạy** | Người dùng báo chứng từ mất trạng thái | Hai cột chạy song song, không xóa cột cũ trước một tháng. Có đường lui ở mọi bước trừ bước cuối |
| 10 | **Nhiều pháp nhân bị bỏ tới lúc cần mới làm** | Có yêu cầu tách báo cáo theo công ty con | Cột công ty thành viên nằm ở GĐ 0. **Thêm cột phân định pháp nhân sau khi đã có dữ liệu là việc rất khó sửa lại.** Tập đoàn có trên 10 công ty thành viên nên nhu cầu này chắc chắn đến |
| 11 | **Nhiệt tình lúc đầu, không ai duy trì dữ liệu** | Sau ba tháng, hồ sơ nhân sự không còn ai cập nhật | Điều kiện số 3 và số 6 tại mục 10.3. Đây là rủi ro của tổ chức, phần mềm không chặn được |

---

## PHỤ LỤC A — BẢNG THUẬT NGỮ

| Thuật ngữ | Giải thích |
|---|---|
| **Phân hệ** | Một mảng nghiệp vụ có thể bật tắt độc lập trong cùng một hệ thống: Tổ chức, Nhân sự, Văn bản, Thu mua |
| **Phạm vi dữ liệu** | Giới hạn xem được: cùng một quyền đọc, nhưng người này thấy dữ liệu phòng mình, người kia thấy toàn công ty. Khác với **quyền hành động** là được làm gì |
| **Phân quyền tới mức từng trường** | Che từng ô dữ liệu chứ không chỉ từng bản ghi: trưởng phòng xem được hồ sơ nhân viên nhưng không xem được cột mức lương |
| **Phần dùng chung** | Phần mã nguồn viết một lần cho mọi phân hệ dùng lại: kiểm quyền, áp phạm vi, ghi nhật ký, phân trang, xuất tệp |
| **Bộ máy phê duyệt dùng chung** | Cơ chế duyệt khai báo bằng cấu hình, dùng chung cho mọi loại chứng từ, thay vì mỗi phân hệ tự viết luồng riêng |
| **Nguyên tắc chặn khi chưa khai báo** | Gặp tình huống chưa khai báo thì **từ chối**, không phải cho qua. Ngược lại là cho qua khi chưa khai báo — chính là lỗ hổng đang có |
| **Bước thay đổi cấu trúc dữ liệu** | Một thao tác sửa cấu trúc cơ sở dữ liệu, có thứ tự, chạy lại được từ đầu, có đường lui |
| **Điểm phục hồi** | Khoảng dữ liệu tối đa có thể mất khi xảy ra sự cố. Sao lưu hai lần mỗi ngày tương ứng điểm phục hồi 12 giờ |
| **Thời gian phục hồi** | Thời gian tối đa để đưa hệ thống chạy lại sau sự cố |
| **Tuần-người thuần** | Một tuần làm việc của một người sau khi đã trừ họp, nghỉ và bảo trì. Đơn vị dùng tại mục 8 |
| **Yêu cầu thay đổi** | Một đề nghị sửa đổi từ người dùng của hệ thống đang chạy. Đo được: xấp xỉ một yêu cầu mỗi ngày làm việc |
| **Công tắc cấu hình** | Cách bật tắt một chức năng mà không phải triển khai lại phần mềm. Dùng để có đường lui |
| **Sổ cái chỉ ghi thêm** | Bảng chỉ thêm dòng, không sửa và không xóa dòng cũ; sửa sai bằng bút toán đảo. Cách lưu bắt buộc với thứ mang giá trị như tiền hoặc điểm |
| **Phần mềm bán hàng tại quầy** | Phần mềm thu ngân của quán cà phê. Hiện đang dùng POS365 |

---

*Hết báo cáo.*
