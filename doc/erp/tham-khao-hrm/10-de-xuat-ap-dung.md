# ĐỀ XUẤT ÁP DỤNG — LẤY GÌ, THEO THỨ TỰ NÀO, SỬA GÌ

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Dùng để làm gì | Chuyển kết quả khảo sát thành **thứ tự làm việc** và **danh sách sửa đổi trên mã nguồn hiện có** |
| Ai đọc | Đội phần mềm, người chủ trì, ban lãnh đạo |
| Quan hệ với các mục khác | Đây là **mục quyết định thứ tự chung**. Cột "Nên lấy" trong từng mục tính năng chỉ xét riêng trong mục đó; chỗ nào khác nhau thì lấy theo tài liệu này |

---

## 1. Kết luận trong một trang

Khảo sát 66 màn hình của một hệ thống HRM thương mại đã chạy thật. Ba kết luận:

**Kết luận 1 — Phần nền phân quyền của mình không phải làm lại.**

Mô hình của họ là hai trục: hành động theo nhóm quyền, phạm vi dữ liệu theo ba mức. Mô hình của Thu mua cũng là hai trục, nhưng trục phạm vi mềm hơn — cấp theo từng lượt (người dùng × vai trò), nhiều chiều, thay vì ba mức cố định. **Giữ nguyên mô hình. Chỉ mở rộng.** Ba việc mở rộng cụ thể ở mục 3.1.

**Kết luận 2 — Thứ đáng lấy nhất không phải là một tính năng nhân sự.**

Là **bộ máy duyệt dùng chung**. Một màn hình cấu hình phục vụ 88 loại chứng từ, khai được vai tương đối ("người quản lý trực tiếp") thay vì gọi đích danh. Thu mua hiện duyệt cứng trong mã nguồn — chịu được với vài loại chứng từ, không chịu được với một ERP nhiều phân hệ.

Cái này **không thuộc HRM**. Nó thuộc phần nền, và phải làm trước HRM chứ không phải làm trong HRM. Làm HRM trước rồi mới làm bộ máy duyệt nghĩa là viết luồng duyệt cứng cho đơn nghỉ phép rồi vứt đi.

**Kết luận 3 — Không làm lương trong bản 1, và bây giờ có bằng chứng chứ không phải chỉ có ý kiến.**

Họ không viết cứng công thức lương. Họ làm **một bộ máy công thức**: người dùng khai cột, viết công thức bằng một ngôn ngữ nhỏ có `IIF`, `isnull`, `round`, các toán tử số học và so sánh, tham chiếu tới cột khác bằng từ khóa. Nghĩa là làm lương không phải làm một màn hình — là làm một ngôn ngữ kịch bản thu nhỏ, cộng màn hình khai công thức, cộng trình kiểm tra công thức sai, cộng xử lý tham chiếu vòng.

Đây là câu nên đưa nguyên văn vào buổi trình bày khi trả lời mục C2 trong [danh mục chờ quyết](../04-danh-muc-cho.md).

---

## 2. Bốn tiêu chí xếp thứ tự

Thứ tự trong tài liệu này không xếp theo "cái nào hay hơn". Xếp theo bốn tiêu chí, theo đúng thứ tự ưu tiên:

| # | Tiêu chí | Câu hỏi |
|---|---|---|
| 1 | **Cái gì chặn cái gì** | Làm B trước A thì có phải vứt đi phần nào không |
| 2 | **Bao nhiêu người dùng** | Cả công ty dùng, hay chỉ hai người trong phòng Nhân sự dùng |
| 3 | **Sai thì hậu quả tới đâu** | Sai hồ sơ thì sửa. Sai lương thì nhân viên chịu thiệt và công ty chịu trách nhiệm pháp lý |
| 4 | **Có phụ thuộc bên ngoài không** | Chờ máy chấm công, chờ phòng ban trả lời, chờ quyết định của lãnh đạo |

Tiêu chí 1 quan trọng hơn cả ba tiêu chí còn lại cộng lại. Một tính năng có ích mà làm sai thứ tự thì phần lớn công sức bỏ đi.

---

## 3. Bốn vòng

### 3.1 Vòng 0 — Gia cố nền. Làm ngay, không chờ khảo sát nghiệp vụ

Đây là những việc **không phụ thuộc kết quả phỏng vấn phòng Nhân sự**, nên không có lý do gì để chờ. Và cả bốn việc đều đắt hơn nhiều nếu làm sau khi đã có dữ liệu nhân sự trong hệ thống.

| # | Việc | Vì sao ngay | Khối lượng |
|---|---|---|---|
| V0-1 | **Khai đủ phạm vi dữ liệu cho toàn bộ đối tượng, và đổi hành vi khi thiếu khai từ "bỏ qua" thành "chặn"** | `SCOPE_FIELDS` hiện khai 9 trên 29 đối tượng. Thiếu một chiều thì hệ thống **im lặng không lọc** — tức trả về nhiều dữ liệu hơn mức được phép mà không báo gì. Dữ liệu thu mua rò rỉ giữa phòng ban là khó chịu; dữ liệu lương rò rỉ là chuyện khác hẳn | Nhỏ về mã, vừa về rà soát |
| V0-2 | **Tách `xuất file` và `nhập file` thành hành động riêng trong ma trận quyền** | Hiện ai xem được thì xuất được. Với dữ liệu nhân sự, khác biệt giữa "xem một hồ sơ trên màn hình" và "tải cả bảng về máy" là khác biệt về mức rủi ro, không phải về tiện dụng | Nhỏ |
| V0-3 | **Bộ máy duyệt dùng chung** — khai luồng bằng dữ liệu, có vai tương đối | Kết luận 2 ở trên. Mọi chứng từ HRM sau này cắm vào. Làm sau thì phải viết bỏ đi từng luồng cứng đã viết | **Lớn.** Đây là hạng mục nặng nhất của vòng 0 |
| V0-4 | **Màn hình kiểm tra trước khi khóa tài khoản** — hiện danh sách chứng từ đang chờ người này duyệt, và các quy trình có người này làm bước duyệt | Rủi ro này đang có ở Thu mua hôm nay. Người nghỉ việc mà đang giữ 7 chứng từ chờ duyệt thì 7 chứng từ kẹt, và không ai biết cho tới khi có người kêu | Nhỏ |

**Ba việc V0-1, V0-2, V0-4 đều nhỏ và đều nên làm trong tháng 8 và tháng 9**, song song với bước 0 khảo sát nghiệp vụ. Chúng không chiếm người của việc khảo sát.

**V0-3 là việc lớn và cần quyết định sớm** vì nó đứng trước toàn bộ vòng 1. Đề nghị: bắt đầu bằng đúng các loại chứng từ Thu mua đang có, cộng thêm chỗ trống cho đơn từ. Không cần 88 loại. Không lấy phần bộ dựng biểu mẫu của họ.

**Về khuôn chứng từ chung:** khi làm V0-3, làm luôn khuôn chứng từ (số phiếu, trạng thái, tệp đính kèm, bản PDF ký, lịch sử duyệt dùng chung khóa bằng `loaiChungTu` + `maPhieu`). Chi tiết ở [`09` mục 4.3](./09-phong-doan-co-so-du-lieu.md). Đây là quyết định kiến trúc quan trọng hơn mọi chi tiết nghiệp vụ trong bộ tài liệu này.

---

### 3.2 Vòng 1 — HRM cơ bản. Sau khi có kết quả khảo sát

Nguyên tắc của vòng này: **làm phần dữ liệu nền và phần cả công ty dùng. Không làm phần tính toán.**

| # | Việc | Lấy từ mục nào | Vì sao ở vòng 1 |
|---|---|---|---|
| V1-1 | **Danh mục tổ chức** — phòng ban có cấp cha con, chức danh, cấp bậc, pháp nhân, hình thức nhân viên | [`01`](./01-nhan-su.md) | Mọi thứ khác móc vào đây. Không có nó thì không có phạm vi dữ liệu theo phòng ban, không có vai tương đối trong duyệt |
| V1-2 | **Hồ sơ nhân viên — khoảng 30 trường, không phải 90** | [`01`](./01-nhan-su.md) | Màn hình trung tâm. Chi tiết đáng lấy: hồ sơ đầy đủ 90 trường nhưng **thêm mới chỉ hỏi 12**. Bắt điền đủ ngay từ đầu thì không ai nhập |
| V1-3 | **Trường `nguoiQuanLy` và tính đúng cây quản lý** | [`01`](./01-nhan-su.md) | Không phải để hiển thị. Đây là dữ liệu mà vai tương đối trong bộ máy duyệt dùng. Sai trường này thì đơn từ chạy sai đường, và sai kiểu im lặng |
| V1-4 | **Phân quyền theo trường cho nhóm trường nhạy cảm** | [`08`](./08-he-thong-va-phan-quyen.md) | Lương, căn cước, tài khoản ngân hàng, hồ sơ sức khỏe nằm chung màn hình với trường bình thường. Phân quyền theo màn hình không giải được. **Thêm sau khi hồ sơ đã chạy thật là việc đắt**, vì phải rà lại từng chỗ hiển thị |
| V1-5 | **Hợp đồng lao động + báo cáo "Hợp đồng sắp hết hạn"** | [`01`](./01-nhan-su.md), [`08`](./08-he-thong-va-phan-quyen.md) | Hợp đồng hết hạn mà không ai nhớ là rủi ro pháp lý thật. Đây là lý do dễ giải thích nhất cho việc đầu tư phần mềm nhân sự. Kèm thông báo chủ động, không chỉ là báo cáo phải mở ra xem |
| V1-6 | **Cấu hình loại đơn từ — bản gọn, khoảng 12 trường thay vì 50** | [`02`](./02-don-tu-va-duyet.md) | Không có nó thì mọi luật nghỉ phép nằm trong mã nguồn. Bắt buộc giữ bảng bậc số ngày phép theo thâm niên — luật quy định 5 năm thêm 1 ngày, và quy định đổi thì sửa dữ liệu chứ không sửa mã |
| V1-7 | **Đơn nghỉ phép + quỹ phép năm** | [`02`](./02-don-tu-va-duyet.md), [`03`](./03-cham-cong.md) | **Đây là tính năng cả công ty dùng.** Tỷ lệ số người được lợi trên số công bỏ ra cao nhất trong toàn bộ HRM. Bắt buộc giữ: hiện số phép còn lại ngay trên form lúc nộp |
| V1-8 | **Quyết định điều chuyển và bổ nhiệm** | [`05`](./05-quyet-dinh-nhan-su.md) | Loại quyết định phát sinh nhiều nhất, và là thứ giữ cho sơ đồ tổ chức đúng theo thời gian. Bắt buộc giữ: một phiếu nhiều người, ngày hiệu lực trên từng dòng, có kiêm nhiệm |

**Cái không làm ở vòng 1, và lý do:**

| Không làm | Lý do |
|---|---|
| Chấm công | Phụ thuộc máy chấm công xuất được dữ liệu, phụ thuộc quyết định C2. Và bảng công là mục có khối lượng bị đánh giá thấp nhiều nhất — riêng màn hình xử lý lỗi dữ liệu đã là một khối lượng riêng |
| Lương | Kết luận 3 |
| Tuyển dụng | Phòng Nhân sự tuyển vài chục người một năm. Ít người dùng, ít việc lặp. Để sau |
| Đánh giá | Phụ thuộc tiêu chí đánh giá của công ty, mà công ty đang trong quá trình chuẩn hóa nghiệp vụ. Làm bây giờ là làm trên nền chưa ổn định |
| Tài sản | Phụ thuộc hồ sơ nhân viên và bộ máy duyệt. Sau khi có cả hai thì rẻ |
| Bảo hiểm | Cần nối cổng bảo hiểm xã hội điện tử. Phụ thuộc bên ngoài |

---

### 3.3 Vòng 2 — Mở rộng

| # | Việc | Lấy từ mục nào | Điều kiện để bắt đầu |
|---|---|---|---|
| V2-1 | Onboarding và Offboarding — danh sách việc khi một người vào và ra | [`08`](./08-he-thong-va-phan-quyen.md) | Sau V1-2 |
| V2-2 | Quyết định thôi việc đầy đủ, với các thẻ bàn giao | [`05`](./05-quyet-dinh-nhan-su.md) | Sau V0-4 và V2-3 |
| V2-3 | Tài sản: danh sách, nhập, xuất, biên bản bàn giao | [`07`](./07-workspace-tai-san.md) | Sau V1-2 và V0-3 |
| V2-4 | Chấm công: thiết lập ca, phân ca, bảng công, đơn bổ sung công, đơn tăng ca | [`03`](./03-cham-cong.md), [`02`](./02-don-tu-va-duyet.md) | **Chỉ khi C2 kết luận là có làm.** Thứ tự bắt buộc: thiết lập ca trước, phân ca sau, bảng công sau cùng |
| V2-5 | Các quyết định nhân sự còn lại, dùng khuôn chung | [`05`](./05-quyet-dinh-nhan-su.md) | Sau V1-8 |
| V2-6 | Sơ đồ tổ chức vẽ từ dữ liệu | [`01`](./01-nhan-su.md) | Sau V1-1 và V1-3 |

---

### 3.4 Vòng 3 — Phần nặng, chỉ làm sau khi vòng 1 đã chạy thật ít nhất một quý

| # | Việc | Điều kiện |
|---|---|---|
| V3-1 | Tiền lương | Trả lời xong bốn câu hỏi thiết kế ở [`09` mục 5](./09-phong-doan-co-so-du-lieu.md), đặc biệt câu 1 về cách lưu kết quả lương. Và chỉ sau khi chấm công đã chạy đúng một quý |
| V3-2 | Đánh giá | Sau khi công ty đã chốt bộ tiêu chí. Nối với lương thì làm cùng V3-1 |
| V3-3 | Tuyển dụng | Không phụ thuộc gì gắt, nên đẩy được lên sớm nếu có nhu cầu kinh doanh |
| V3-4 | Bảo hiểm | Phụ thuộc cổng bảo hiểm xã hội điện tử |
| V3-5 | Dashboard động, nhúng công cụ báo cáo ngoài | Quyết định công cụ báo cáo trước |

---

## 4. Danh sách không lấy

Ghi rõ để khỏi bàn lại.

| Không lấy | Lý do |
|---|---|
| Bộ dựng biểu mẫu (`CauHinhDeXuat`, "Form HTML") | Mạnh, nhưng ba năm sau có 80 loại form không ai biết cái nào còn dùng. Nếu sau này làm thì bắt buộc mỗi form có người chịu trách nhiệm và cơ chế ngừng dùng |
| Trường động mở cho mọi màn hình | Đánh đổi ở [`09` mục 4.2](./09-phong-doan-co-so-du-lieu.md). Nếu làm thì chỉ mở cho hồ sơ nhân viên, có trần số trường |
| Truyền thông nội bộ, Chat | Đã có công cụ bên ngoài. Tự xây không thu lại giá trị |
| Công văn, Ký số | Thuộc khối hành chính. Ký số còn cần hạ tầng USB token |
| Dự án, Quản lý công việc | Project-M đang phục vụ. Nếu thiếu Gantt thì bổ sung vào Project-M, không bê màn hình mới về |
| E-Learning | Ngoài phạm vi khảo sát ngay từ đầu |
| Điều chỉnh hợp đồng như một màn hình riêng | Trùng chức năng với quyết định điều chỉnh lương. Gộp làm một |
| Khóa nhóm quyền là chuỗi tiếng Việt | Chính họ đã dính lỗi mã hóa và trùng nhóm. Giữ cách của mình |
| Ba mức phạm vi dữ liệu cố định | Mô hình của mình mềm hơn. Không hạ cấp |

**Về khối Workspace nói chung:** đây không phải nghiệp vụ nhân sự. Gộp nó vào phạm vi HRM sẽ làm phạm vi phình gấp đôi mà không phục vụ mục tiêu nào. Liệt kê trong [`07`](./07-workspace-tai-san.md) là để lúc đi khảo sát còn hỏi được, không phải để đưa vào kế hoạch.

---

## 5. Cụ thể phải sửa gì trên mã nguồn hiện có

Phần này trả lời trực tiếp câu "cần chỉnh sửa gì". Chia hai loại: sửa để mở đường cho HRM, và sửa vì tự nó là lỗ hổng.

### 5.1 Sửa vì tự nó là vấn đề, làm ngay

| # | Chỗ sửa | Hiện trạng | Sửa thành |
|---|---|---|---|
| S1 | Khai phạm vi dữ liệu | 9 trên 29 đối tượng có khai. Thiếu khai thì **im lặng không lọc** | Khai đủ. Và đổi hành vi: thiếu khai thì **chặn**, không bỏ qua. Chấp nhận vỡ vài chỗ lúc triển khai còn hơn rò rỉ |
| S2 | Ma trận hành động | 4 hành động | Thêm `xuất file` và `nhập file`. Mặc định tắt cho mọi vai trò trừ quản trị, rồi mở dần |
| S3 | Xóa hoặc khóa tài khoản | Không kiểm tra gì | Chặn lại nếu người đó đang là bước duyệt hoặc đang giữ chứng từ chờ duyệt. Hiện danh sách ra |
| S4 | Bộ nhớ đệm quyền | Đã có `perm_cache_clear`, nhưng phải nhớ gọi tay | Khi thêm đối tượng và vai trò cho HRM, số chỗ phải nhớ gọi tăng lên. Rà lại toàn bộ chỗ sửa vai trò và lượt cấp |

### 5.2 Sửa để mở đường cho HRM

| # | Chỗ sửa | Vì sao | Ghi chú |
|---|---|---|---|
| S5 | Trạng thái chứng từ đang lưu bằng chuỗi tiếng Việt | Bộ máy duyệt dùng chung cần đọc và ghi trạng thái theo một quy ước thống nhất. Chuỗi tiếng Việt tự do thì không dùng chung được | Đây là nợ kỹ thuật đã biết. Bộ máy duyệt là lý do phải trả nợ ngay chứ không dời thêm |
| S6 | Chưa có khuôn chứng từ chung | Mỗi loại chứng từ tự định nghĩa. Với ERP nhiều phân hệ thì mỗi phân hệ lại viết lại phần đính kèm, phần in, phần duyệt | Làm cùng lúc với V0-3 |
| S7 | `company_id` mới có ở 14 trên 31 tệp mô hình | Hồ sơ nhân viên có `pháp nhân`, và điều chuyển giữa pháp nhân là nghiệp vụ thật | Quyết định trước: HRM bản 1 có làm nhiều pháp nhân không. Nếu có thì phải khai đủ trước khi nhập dữ liệu |
| S8 | Chưa có tầng phân quyền theo trường | V1-4 | Bản đầu không cần màn hình cấu hình. Khai cứng một nhóm trường nhạy cảm và một quyền riêng để xem nhóm đó |
| S9 | 75 migration chưa gộp | Không chặn gì, nhưng HRM sẽ thêm hàng chục migration nữa | Gộp trước khi bắt đầu vòng 1, không phải sau |
| S10 | `all_models.py` | `alembic --autogenerate` chỉ nhìn thấy mô hình được nhập ở đây | Nhắc lại vì HRM sẽ thêm nhiều mô hình một lúc, và quên nhập là lỗi im lặng |

### 5.3 Cái không sửa

| Không sửa | Vì sao |
|---|---|
| Mô hình phân quyền hai trục | Kết luận 1. Mô hình đúng, và mềm hơn của họ. Chỉ mở rộng, không thiết kế lại |
| Cách đặt tên cột kiểu lạc đà không dấu | Đọc là hiểu. Họ cũng vậy |
| Cơ sở dữ liệu cũ của Thu mua | Quy tắc 1 của bộ tài liệu ERP: chỉ thêm, không sửa. Thu mua đang chạy thật, không có cửa sổ dừng |

---

## 6. Kết quả khảo sát này ảnh hưởng tới tài liệu nào

| Tài liệu | Ảnh hưởng |
|---|---|
| [`04` Danh mục chờ quyết](../04-danh-muc-cho.md), mục **C2** | Khuyến nghị "không làm lương trong bản 1" giờ có bằng chứng: lương là một bộ máy công thức, không phải một màn hình. Nên đưa nguyên văn vào phần trình bày C2 |
| [`01` Ngắn hạn](../01-ngan-han-2026.md) | **Bộ máy duyệt dùng chung phải được đưa lên thành hạng mục của phần nền, đứng trước bước 4 (HRM).** Hiện chưa có trong danh sách. Đây là thay đổi lớn nhất mà khảo sát này gây ra cho kế hoạch |
| [`03` Câu hỏi khảo sát HRM](../03-cau-hoi-khao-sat-hrm.md) | Phải thêm phần hỏi về **phân quyền xem theo trường** trên hồ sơ nhân viên — ai được xem lương, căn cước, tài khoản ngân hàng, hồ sơ sức khỏe. Đây là hạng mục dễ sót và đắt khi thêm sau |
| [`03` Câu hỏi khảo sát HRM](../03-cau-hoi-khao-sat-hrm.md) | Thêm câu về **chấm công khi đi công tác** — chỗ mọi hệ thống chấm công theo vị trí đều vướng |
| [`02` Dài hạn](../02-dai-han.md) | Không đổi. Thứ tự phân hệ HRM → MFM → Kế toán → CRM vẫn đứng |

---

## 7. Cách dùng tài liệu này

Ba cách dùng đúng:

1. **Xếp lịch.** Bốn vòng ở mục 3 là đầu vào để viết lịch. Không phải là lịch.
2. **Chốt phạm vi.** Khi có bảng chốt phạm vi HRM bản 1 để ký, đối chiếu với vòng 1 ở mục 3.2. Cái gì trong vòng 1 mà không có trong bảng chốt thì phải hỏi vì sao.
3. **Rà mã nguồn.** Mục 5 là danh sách việc kỹ thuật, dùng được ngay mà không cần chờ ai quyết.

Một cách dùng sai, nói rõ để tránh: **không dùng tài liệu này thay cho khảo sát nghiệp vụ.** Quyết định Đ2 vẫn đứng — không chép nghiệp vụ từ phần mềm ngoài. Những gì viết ở đây là **thứ tự kỹ thuật và chi tiết đáng học**, không phải nghiệp vụ của công ty mình. Nghiệp vụ vẫn phải sinh ra từ phỏng vấn ở bước 0.

Hai thứ đó không mâu thuẫn. Biết trước "làm lương là làm bộ máy công thức" không phải là chép nghiệp vụ — đó là biết trước cái giá phải trả trước khi hứa với lãnh đạo.
