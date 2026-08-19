# DANH MỤC CHỜ QUYẾT

| | |
|---|---|
| Bản | **1.1 — 12/08/2026** (thêm C15; chuyển bốn câu về phòng ban, xuất dữ liệu và phân quyền trường sang mục "Đã chốt") |
| Dùng để làm gì | Danh sách những việc **đội phần mềm không tự quyết được**, đang chặn hoặc sắp chặn tiến độ |
| Ai đọc | Người chủ trì, ban lãnh đạo |
| Liên quan | [`01` Ngắn hạn](./01-ngan-han-2026.md) · [`02` Dài hạn](./02-dai-han.md) · [`03` Câu hỏi khảo sát HRM](./03-cau-hoi-khao-sat-hrm.md) |

---

## Cách đọc bảng này

- **Đang chặn** — không có câu trả lời thì công việc đứng, không có cách đi vòng.
- **Sắp chặn** — còn đi tiếp được một thời gian, nhưng có hạn cuối.
- **Chờ nhưng chưa chặn** — cần chốt trước một vòng sau, chưa ảnh hưởng năm nay.

Mỗi mục ghi rõ: **ai quyết được**, **hạn nào**, và **nếu quá hạn thì phần mềm làm gì**. Cột cuối quan trọng nhất — nó nói trước hậu quả, để lúc trượt lịch không phải tranh cãi nguyên nhân.

---

## 1. Đang chặn

### C1 — Ai chủ trì khảo sát nghiệp vụ, và phòng Nhân sự cử ai làm đầu mối

| | |
|---|---|
| Chặn việc gì | Toàn bộ bước 0, kéo theo cả bước 4 (HRM) |
| Ai quyết | Ban lãnh đạo |
| Hạn | **20/08/2026** — để kịp lịch nửa sau T8 |
| Quá hạn thì sao | Bước 0 kéo dài vô hạn. Lịch T9 trượt, HRM trượt theo. Không có cách đi vòng: đội phần mềm không tự bịa được nghiệp vụ nhân sự |

**Đề xuất để trình:**

Cần hai vai, không phải một.

| Vai | Làm gì | Mất bao nhiêu thời gian |
|---|---|---|
| **Người chủ trì khảo sát** | Xếp lịch phỏng vấn, chốt biên bản, đẩy các bộ phận trả lời, ký bảng phạm vi HRM | Khoảng nửa ngày mỗi tuần, trong 6 tuần |
| **Đầu mối phòng Nhân sự** | Trả lời bộ câu hỏi `03`, cung cấp 12 tài liệu ở phần F, xác nhận biên bản, xác nhận cách tính khi làm tới lương | Khoảng 1 ngày mỗi tuần, trong 6 tuần, sau đó rải rác khi nghiệm thu |

Yêu cầu tối thiểu với đầu mối Nhân sự: **đang trực tiếp làm việc đó hằng ngày**, không phải người chỉ nghe kể lại. Nếu chỉ cử được người quản lý mà không cử người làm, thì phải cho phép đội phỏng vấn tiếp cận người làm.

Lý do phải có người chủ trì riêng: file `ke-hoach/01` mục 5 đã ghi lại, **chưa hạn nào chờ bộ phận khác được giữ đúng.** Không có ai chịu trách nhiệm đẩy thì lịch trượt là chuyện đã xảy ra nhiều lần, không phải rủi ro giả định.

---

### C2 — Phạm vi HRM bản 1: có làm lương không, có làm chấm công không

| | |
|---|---|
| Chặn việc gì | Bước 4 (HR1–HR13). Đây là mục quyết định khối lượng lớn nhất của cả kế hoạch |
| Ai quyết | Ban lãnh đạo, dựa trên kết quả khảo sát |
| Hạn | **Nửa đầu T9/2026**, cùng lúc với bảng chốt phạm vi ký duyệt |
| Quá hạn thì sao | Đội phần mềm mặc định **không làm lương, không làm chấm công** trong bản 1, và bắt đầu từ hồ sơ, hợp đồng, nghỉ phép. Đổi ý sau tháng 10 thì không kịp trong năm nay |

**Cách trả lời:** không trả lời bằng cảm tính. Đi khảo sát theo phần B của [`03`](./03-cau-hoi-khao-sat-hrm.md), rồi áp quy tắc kết luận đã ghi sẵn ở đó.

**Khuyến nghị của đội phần mềm nếu phải chọn ngay hôm nay:**

| Mảng | Khuyến nghị | Vì sao |
|---|---|---|
| Lương | **Không làm trong bản 1** | Hồ sơ sai thì sửa. Lương sai thì nhân viên chịu thiệt và công ty chịu trách nhiệm pháp lý. Làm sau khi phần dữ liệu đầu vào đã chạy đúng ít nhất một quý |
| Chấm công | **Làm phần nhập và tổng hợp, nếu máy chấm công xuất được dữ liệu** | Đây là phần có ích ngay và cũng là ca dùng thật đầu tiên cho module webhook. Nhưng nếu có nhiều loại ca thì hoãn — ca kíp là phần dễ bị đánh giá thấp khối lượng nhất |

---

## 2. Sắp chặn

### C3 — Ngày đổi giao diện cho người dùng thật trong T10

| | |
|---|---|
| Chặn việc gì | FE11, FE12 |
| Ai quyết | Người chủ trì, thống nhất với các bộ phận đang dùng Thu mua |
| Hạn | **Cuối T9/2026**, ngay sau khi lưới biểu tượng chạy được ở môi trường thử |
| Quá hạn thì sao | Đội phần mềm tự chọn một ngày trong nửa đầu T10 và thông báo trước 5 ngày làm việc |

**Ghi chú:** đây là lần đầu người dùng thật thấy giao diện đổi. Việc đổi có đường lui — bật lại giao diện cũ được, theo quy tắc 2. Nên chọn ngày **không trùng cuối tháng**, vì cuối tháng là lúc bộ phận thu mua chốt số.

Cần chốt kèm ba thứ: ngày cụ thể, ai thông báo cho người dùng, và ai trực trong hai ngày đầu để nhận phản ánh.

---

### C4 — Tích hợp ra ngoài đầu tiên là với hệ thống nào

| | |
|---|---|
| Chặn việc gì | Thứ tự trong bước 5 — cụ thể là WH12, WH13, WH15. **Không chặn phần lõi WH1–WH11** |
| Ai quyết | Ban lãnh đạo |
| Hạn | **Cuối T11/2026** |
| Quá hạn thì sao | Phần lõi webhook vẫn làm xong và chạy được. Chỉ là chưa nối với ai. Không mất công gì |

**Đã chốt phần nguyên tắc:** viết hạ tầng trước, chưa cần biết nối với ai. Phần lõi không phụ thuộc vào đối tượng nối.

**Ứng viên gần nhất:** đồng bộ đơn hàng. Cần trả lời thêm ba câu trước khi chốt:

| # | Câu hỏi |
|---|---|
| 1 | Đồng bộ đơn hàng với hệ thống nào cụ thể — hệ thống của khách, sàn, hay phần mềm nội bộ khác? |
| 2 | Một chiều hay hai chiều? Ai là nguồn đúng khi hai bên lệch nhau? |
| 3 | Bên kia có sẵn đầu nối chưa, hay phải chờ họ làm? |

Câu 3 quyết định có kịp trong năm nay hay không, vì phụ thuộc bên ngoài.

**Ứng viên thứ hai, nên cân nhắc:** máy chấm công. Nếu C2 kết luận là có làm chấm công, thì đây là ca dùng thật nằm ngay trong nhà, không phải chờ ai, và kiểm chứng được toàn bộ phần lõi webhook trước khi đem nối với hệ thống bên ngoài.

---

## 2b. Sinh ra từ tài liệu `06` — chặn phần nền và HRM

Ba câu này xuất hiện ngày 11/08/2026 khi đọc lại mã nguồn để viết [`06` Lộ trình nền tảng và HRM](./06-lo-trinh-nen-tang-va-hrm.md). Khác ba mục ở phần 1 và 2 ở chỗ: **hai trong ba câu này không sửa lại được sau khi đã có dữ liệu.**

| # | Việc | Ai quyết | Chốt trước khi nào | Chặn gì | Quá hạn thì sao |
|---|---|---|---|---|---|
| C12 | Chuẩn hóa trạng thái sang số có áp cho cả bảng cũ hay chỉ bảng mới | Đội phần mềm | Trước khi bắt đầu H1 | H1, và mọi báo cáo gộp số liệu giữa hai phân hệ | Mặc định: **chỉ áp bảng mới**, bảng cũ chuyển dần từng module. Chọn mặc định thì báo cáo xuyên phân hệ phải đợi |
| C13 | Một người làm cho nhiều pháp nhân thì một hồ sơ gắn nhiều pháp nhân, hay mỗi pháp nhân một hồ sơ | Phòng Nhân sự cùng Ban điều hành | Trước khi viết bảng nhân viên (N1) | Toàn bộ HRM | Mặc định: **một hồ sơ gắn nhiều pháp nhân**, vì gộp lại dễ hơn tách ra. **Chọn sai thì không sửa được sau khi đã nhập dữ liệu** |
| C14 | Bản 1 chạy thật cho mấy pháp nhân | Ban điều hành | Trước H3 | H3, và cách đánh số chứng từ | Mặc định: **khai đủ cấu trúc cho nhiều pháp nhân, bản 1 chạy một pháp nhân**. Làm ngược lại thì sau này phải trả lời câu "dòng cũ thuộc pháp nhân nào" mà không còn dữ liệu để trả lời |
| **C15** | **Ai làm lộ trình ERP, và có được tách khỏi luồng xử lý yêu cầu thay đổi của Thu mua không** | Ban lãnh đạo | **Trước khi chốt bất kỳ mốc thời gian nào** | Toàn bộ lịch của [`01`](./01-ngan-han-2026.md) | Đo được: CR-034 đến CR-061 rơi gọn trong khoảng năm ngày làm việc — **xấp xỉ một yêu cầu thay đổi mỗi ngày** từ Thu mua đang chạy thật. Lộ trình hiện tại **chưa trừ phần công đó ra**. Quá hạn thì mọi mốc trong `01` phải hiểu là "sau khi trừ việc Thu mua", tức là **không có mốc** |

---

## 3. Chờ nhưng chưa chặn năm nay

| # | Việc | Ai quyết | Chốt trước khi nào | Ghi chú |
|---|---|---|---|---|
| C5 | Có làm vị trí kho, lô, hạn dùng hay không | Bộ phận sản xuất và kho | Trước khi viết BOM, vòng 2 | Đổi cấu trúc bảng tồn kho. Chốt sau thì phải làm lại |
| C6 | Giá thành thuộc phân hệ MFM hay Kế toán | Ban lãnh đạo và kế toán | Đầu vòng 2 | Ranh giới không rõ thì hai bên cùng làm hoặc cùng bỏ |
| C7 | Kế toán tự viết hay nối phần mềm có sẵn | Ban lãnh đạo | Trước vòng 3 | Khuyến nghị của đội phần mềm là **nối**, lý do ở [`02` mục 5](./02-dai-han.md) |
| C8 | Mâu thuẫn về mảng bán hàng ở `ke-hoach/02` mục 30.4 | Ban lãnh đạo | Trước vòng 4 | Đã nêu từ trước, chưa được giải quyết |
| C11 | CRM có cần đẩy lên trước Kế toán không | Ban lãnh đạo | Trước vòng 3 | Hai vòng này đổi chỗ được cho nhau. Phụ thuộc ưu tiên kinh doanh, không phụ thuộc kỹ thuật |
| C9 | Phạm vi nhóm H — kế toán mua hàng ở `ke-hoach/02` | Ban lãnh đạo | Khi bộ tài liệu cũ được chốt lại | Đang hiểu là công nợ nhà cung cấp cộng cầu nối bút toán. Con số ước lượng của nhóm đó dựa trên cách hiểu này |
| C10 | Bộ tài liệu `ke-hoach/00`–`04` xử lý thế nào | Ban lãnh đạo | Khi hướng ERP được duyệt | Hai bộ mô tả hai hướng khác nhau. Duyệt hướng này thì bộ cũ nghỉ |

---

## 4. Đã chốt

Ghi lại để không hỏi lại.

| # | Việc | Chốt ngày | Kết luận |
|---|---|---|---|
| Đ1 | Có đổi cơ sở dữ liệu cũ không | 10/08/2026 | **Không.** Thành quy tắc 1 — chỉ thêm, không sửa. Nợ kỹ thuật được dời và ghi lịch trả ở [`02` mục 6](./02-dai-han.md) |
| Đ2 | Có chép nghiệp vụ từ phần mềm nguồn mở không | 10/08/2026 | **Không.** Thay bằng tự đi khảo sát nghiệp vụ ở bước 0 |
| Đ3 | Help Center và Project-M có vào lưới biểu tượng không | 10/08/2026 | **Có.** Thành FE10a–FE10e ở [`01` mục 5.1](./01-ngan-han-2026.md) |
| Đ4 | Có làm module webhook trong năm nay không | 10/08/2026 | **Có.** Phần lõi WH1–WH11 trong T12. Nguyên tắc: viết hạ tầng trước, chưa cần biết nối với ai |
| Đ5 | Phân hệ nào làm trước | 10/08/2026 | **HRM trước, MFM sau.** Lý do ở [`02` mục 2](./02-dai-han.md) |
| Đ6 | Tài liệu hướng ERP để chung hay để riêng | 10/08/2026 | **Để riêng thư mục `ke-hoach/erp/`**, tách ngắn hạn và dài hạn |
| **Đ7** | Phòng ban có làm **cây nhiều cấp** trong HRM không | 12/08/2026 | **Không làm.** Giữ **một cấp phẳng**. Bảng phòng ban đã có sẵn cột `parent` từ trước nhưng để nguyên, không khai thác. Lý do: làm cây thì "phạm vi phòng ban" buộc phải đổi nghĩa thành "phòng mình và các phòng con", khiến **người dùng Thu mua đang chạy thật đột nhiên thấy nhiều chứng từ hơn** — đổi hành vi hệ chạy thật vì một việc của HRM. Bỏ ra khỏi N1 ở [`06` mục 6](./06-lo-trinh-nen-tang-va-hrm.md) |
| **Đ8** | Phạm vi phòng ban so theo **tên** hay theo **id** | 12/08/2026 | **Theo `dept_id`.** Hiện đang so bằng chuỗi tiếng Việt, nên đổi tên một phòng là chứng từ cũ rơi khỏi phạm vi, im lặng. Thành hạng mục **H16** ở [`06` mục 5](./06-lo-trinh-nen-tang-va-hrm.md), làm cùng đợt H1 |
| **Đ9** | Endpoint xuất dữ liệu xử lý thế nào | 12/08/2026 | **Bắt buộc kiểm quyền `export`, và ghi một dòng nhật ký cho mỗi lần xuất** (ai, lúc nào, bảng nào, bao nhiêu dòng, bộ lọc gì). Hiện chỉ 1 trên 11 endpoint xuất kiểm quyền này. Vào **H4** phần (b) và (c) |
| **Đ10** | Có làm phân quyền mức trường không (lương, căn cước) | 12/08/2026 | **Có.** Thành hạng mục **H15**, đặt ở vòng V0-c, **chặn N2** — phải chốt trước khi thiết kế bảng hợp đồng lao động, vì vá sau là sửa lại cả API lẫn giao diện |

---

## 5. Nhắc lại một điều

Bảng này chỉ có ích nếu được mở ra trong mỗi buổi họp tiến độ. Danh mục chờ quyết mà không ai đọc thì không khác gì không có — việc vẫn đứng, chỉ là đứng mà không ai biết vì sao.
