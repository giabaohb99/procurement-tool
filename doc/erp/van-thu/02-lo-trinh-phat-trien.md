# 02 · LỘ TRÌNH PHÁT TRIỂN QUẢN LÝ VĂN THƯ

> Xây trên mã nguồn Thu mua đang chạy
> Danh sách tính năng ở [`01`](./01-danh-sach-tinh-nang.md) · đánh giá và câu hỏi ở [`00`](./00-danh-gia-va-cau-hoi.md)
> **Tài liệu này chia theo phase, không đặt mốc thời gian.** Thứ tự và điều kiện chuyển phase mới là thứ quan trọng.

---

## 1. Tóm tắt

**10 phase**, đánh số từ 0. Phase 0 đến 7 là bản đầu tiên; phase 8 và 9 làm sau khi đã dùng thật.

| Phase | Tên | Ra được cái gì |
|---|---|---|
| **0** | Vá nền | Hệ Thu mua đủ an toàn để chứa văn bản mật |
| **1** | Danh mục và số hiệu | Khai được 32 loại văn bản, cấp được số không trùng |
| **2** | Yêu cầu, soạn thảo, phiên bản | Một người soạn được văn bản từ đầu tới cuối |
| **3** | Bộ máy phê duyệt dùng chung | Khai luồng duyệt bằng giao diện, không sửa mã |
| **4** | Ban hành, phạm vi, clone | Ban hành cho 13 pháp nhân, clone xuống công ty con |
| **5** | Quyền truy cập và tra cứu | Văn bản mật chỉ người có thẩm quyền thấy |
| **6** | Chuyển dữ liệu và chạy thử | Người thật dùng trên dev, có dữ liệu thật |
| **7** | Đưa vào dùng thật | Chạy trên prod, bắt đầu từ một pháp nhân |
| **8** | Chuyển Thu mua sang bộ máy duyệt mới | Bỏ 5 luồng viết tay trong mã |
| **9** | Mở rộng | AI, sổ đi đến, ký số, xác nhận đã đọc |

Cách đọc mỗi phase: **làm gì** · **xong là kiểm được cái gì** · **chưa xong thì không được sang phase sau**.

---

## 2. Nguyên tắc xếp thứ tự

1. **Vá nền trước, thêm tính năng sau.** Đưa văn bản mật vào một hệ mà tệp đính kèm còn tải được không cần quyền là tạo ra sự cố chứ không phải tạo ra sản phẩm.
2. **Bảng dữ liệu tạo đủ từ đầu, tính năng bật dần.** Thêm cột vào bảng trống thì dễ; thêm cột vào bảng đã có vài chục nghìn dòng thì phải canh giờ dừng hệ thống. Nên các bảng ở nhóm "phase sau" vẫn tạo trong phase 1 và 2, chỉ là chưa có màn hình.
3. **Bộ máy duyệt làm một lần, dùng cho cả hai bên.** Nhưng Thu mua **không chuyển sang ngay** — chạy song song, chuyển ở phase 8 sau khi văn thư đã sống ổn.
4. **Mỗi phase kết thúc phải deploy được lên dev và cho người thật bấm thử.** Không có phase nào mà ngoài đội phần mềm không ai nhìn thấy gì.
5. **Phase 0 tới 3 không chờ câu trả lời nào.** 17 câu hỏi ở `00` chỉ chặn phase 4 trở đi.

---

## 3. Sơ đồ phụ thuộc

```
Phase 0  Vá nền
   |
Phase 1  Danh mục và số hiệu
   |
Phase 2  Yêu cầu, soạn thảo, phiên bản
   |
   +-------------------+
   |                   |
Phase 3            Phase 5
Bộ máy duyệt       Quyền truy cập
   |               và tra cứu
Phase 4                |
Ban hành, clone        |
   |                   |
   +--------+----------+
            |
      Phase 6  Chuyển dữ liệu và chạy thử
            |
      Phase 7  Đưa vào dùng thật
            |
      +-----+-----+
      |           |
   Phase 8     Phase 9
   Thu mua     Mở rộng
```

Phase 3 và phase 5 **làm song song được** nếu có hai người. Phase 4 phải chờ phase 3 vì nó dùng bộ máy duyệt.

---

## 4. Phase 0 · Vá nền

Phase duy nhất **không sinh ra tính năng nào người dùng nhìn thấy**, và cũng là phase duy nhất **chạm vào hệ Thu mua đang chạy thật**.

| Việc | Mã ở `01` |
|---|---|
| Viết kiểm thử tự động cho 5 luồng duyệt hiện tại của Thu mua | N01 |
| Bộ nhớ đệm quyền chuyển sang Redis, kèm kênh xóa đệm tức thì | N04 |
| Kho tệp thành riêng tư hoàn toàn, ngừng ghi link công khai | N02 |
| Link tạm có kiểm quyền, ghi nhật ký mọi lượt xem và tải | N03, H03 |
| Chuyển các tệp cũ sang đường tải mới | N02 |
| Phạm vi phòng ban khớp bằng ID thay vì khớp bằng tên | N05 |
| Vá loại trừ phòng ban đang lưu được nhưng không có tác dụng | N07 |
| Vá nhật ký thao tác: phải có quyền, phải theo phạm vi, chỉ ghi thêm | N06, M01 |
| Thêm cột phân hệ cho thông báo | N08 |
| Gom nhóm màn hình phân quyền theo phân hệ | N09 |

**Xong là kiểm được:**
- Chạy 5 kiểm thử luồng duyệt Thu mua, tất cả xanh.
- Lấy một link tệp bất kỳ trong cơ sở dữ liệu, dán vào trình duyệt ẩn danh → **không xem được**.
- Đổi tên một phòng ban → quyền của người trong phòng đó **không đổi**.
- Đặt loại trừ một phòng ban → người phòng đó **thật sự không thấy** dữ liệu nữa.
- Đăng nhập bằng tài khoản không có quyền nhật ký, gọi trang nhật ký → **bị từ chối**.
- Thu hồi một vai trò → tài khoản đó **mất quyền gần như ngay**, không phải chờ hết hạn bộ nhớ đệm.

**Rủi ro:** đây là phase duy nhất có thể làm hỏng việc đang chạy. Cách giảm: N01 làm trước tiên; mỗi việc là một lần deploy riêng chứ không dồn cuối phase; deploy dev trước, theo dõi vài ngày rồi mới lên prod; mỗi việc có đường lui bằng cờ bật tắt.

**Vì sao phần này nặng dù chỉ là vá lỗi:** phần tốn công nhất không phải viết mã mà là N01 và việc chuyển tệp cũ sang đường mới. Không có N01 thì mọi phase sau đều là đi trên băng mỏng — sửa gì cũng không biết có làm hỏng Thu mua không.

**Điều kiện chuyển phase:** cả sáu bài kiểm ở trên đều đạt, và bản vá đã chạy trên prod ổn định.

---

## 5. Phase 1 · Danh mục và số hiệu

| Việc | Mã |
|---|---|
| Bảng loại văn bản, nhập 32 loại theo danh mục đã có | A01, A02 |
| **Loại thứ 33 Trích lục** — chỉ làm nếu Hành chính đồng ý ở câu B12. Khai `id_scheme = 2`, `needs_decision = FALSE` | C20 |
| Mã số hiệu cho 13 pháp nhân và cho phòng ban | A04, A05 |
| Bảng nối phòng ban với pháp nhân, kèm trưởng phòng theo từng pháp nhân | A06 |
| Bộ cấp số chống trùng, hai kiểu định danh | D01, D02, D03, D04 |
| Văn bản hủy vẫn giữ số, không cho đổi mã sau khi đã cấp số | D05, D07 |
| Danh mục đối tác và cơ quan gửi nhận | A07 |
| **Tạo trước các bảng của phase sau** — sổ đi, sổ đến, xác nhận đã đọc, văn bản pháp luật. Chỉ bảng, chưa màn hình | S01, S02, J06 |

**Xong là kiểm được:**
- Mở 100 kết nối cùng lúc xin cấp số cho cùng một loại cùng một pháp nhân → nhận được đúng **100 số liên tiếp, không trùng, không nhảy cóc**. Bài kiểm bắt buộc, không được bỏ qua vì "chắc là ổn".
- Hủy một văn bản → số của nó **không quay lại** cho văn bản sau dùng.
- Đổi sang năm mới → sổ theo năm đếm lại từ 1, sổ mã tài liệu bất biến thì không.

**Điều kiện chuyển phase:** bài kiểm 100 kết nối đạt.

---

## 6. Phase 2 · Yêu cầu, soạn thảo, phiên bản

| Việc | Mã |
|---|---|
| Yêu cầu văn bản: ba loại, lý do bắt buộc, gợi ý văn bản đã có | B01, B05 |
| Chặn soạn khi chưa có yêu cầu được duyệt; cấu hình loại được bỏ qua bước này | B03, B06 |
| Sinh bản nháp từ yêu cầu, theo dõi yêu cầu | B04, B07 |
| Bản ghi văn bản, bộ trường chung, tệp mẫu theo loại | C01, C02 |
| Phiên bản bất biến, lý do sửa bắt buộc, khóa sửa sau khi duyệt | C04, C05, C07 |
| **Sửa văn bản đã ban hành**: mở phiên bản mới, một văn bản một bản nháp, phân loại sửa lớn hay nhỏ, bản cũ vẫn hiệu lực trong lúc soạn, ngày hiệu lực riêng của phiên bản, băng cảnh báo trên bản cũ | C13–C18 |
| Tệp đính kèm đi qua đường riêng tư, mã băm toàn vẹn | C03, C06 |
| Ghi số hiệu cũ của văn bản giấy để tìm ra được | C12 |
| Quan hệ cha con: bảng quy tắc, form tự hiện ô, chặn thiếu quan hệ, cấm vòng lặp, cây tài liệu | E01–E06 |
| **Bản trích nội bộ**: tách một phần nội dung bản gốc thành văn bản riêng mức mật thấp hơn | C19 |
| **Quan hệ *trích từ*** cùng ba ràng buộc khóa cứng, và cột ghi bản trích lấy từ phiên bản nào của gốc | E11 |
| Chuyển ảnh thành văn bản, đặt ảnh gốc cạnh bản nháp để đối chiếu, cờ tắt AI | L01, L02, L07 |

Bước duyệt yêu cầu ở phase này dùng **luồng một bước viết tay tạm thời** — đúng kiểu 5 luồng Thu mua đang có. Phase 3 sẽ thay bằng bộ máy chung. Làm vậy để phase 2 cho người thật bấm thử được ngay, không phải chờ bộ máy duyệt.

**Xong là kiểm được:** một người đi hết đường — xin phép soạn, được duyệt, soạn, chụp ảnh văn bản giấy cho AI đọc, sửa lại, đính kèm tệp, khai văn bản cha, tạo phiên bản thứ hai với lý do sửa. Và **phiên bản thứ nhất vẫn còn nguyên, không bị đè**.

Và năm phép thử nữa:
- Khai một Hướng dẫn công việc mà không chọn Quy trình nó hướng dẫn → **không gửi duyệt được**.
- Hai người cùng bấm "mở phiên bản mới" trên một văn bản → **chỉ một người mở được**, người kia thấy báo ai đang giữ bản nháp.
- Trong lúc bản 2.0 còn đang duyệt, mở văn bản ra xem → **vẫn thấy bản 1.0, vẫn ghi là có hiệu lực**.
- Tạo bản trích từ một văn bản mức Tuyệt mật rồi đặt mức mật **cao hơn gốc** → bị chặn. Đặt thấp hơn thì được, và trên bản trích thấy ghi rõ trích từ phiên bản nào.
- Bản gốc lên phiên bản 2.0 → mọi bản trích của nó **tự chuyển sang trạng thái cần rà lại**, không cần ai bấm gì. Bãi bỏ bản gốc → bản trích **hết hiệu lực theo**.

**Điều kiện chuyển phase:** đường đi trên chạy được từ đầu tới cuối trên dev, có ít nhất 3 người ngoài đội phần mềm bấm thử.

---

## 7. Phase 3 · Bộ máy phê duyệt dùng chung

Phase nặng nhất, 20 tính năng bản đầu. Chi tiết lấy gì từ Lark ở [`03`](./03-lark-approver.md).

| Việc | Mã |
|---|---|
| Mô hình dữ liệu: luồng, bước, phiên chạy, việc, hành động | I01, I02 |
| Phiên bản của luồng — phiếu đang chạy giữ nguyên luồng cũ | I21 |
| Sáu cách chọn người duyệt | I03 |
| Chạy phiên: cấp việc, duyệt, từ chối, trả lại đúng bước, rút lại | I09, I10, I11 |
| Nhiều người trong một bước, ba chế độ | I05 |
| Rẽ nhánh theo điều kiện, có nhánh mặc định | I04 |
| **Trùng thao tác thì bỏ qua** — ba mức cấu hình | I06 |
| **Người duyệt nghỉ việc thì chỉ định người khác** | I07 |
| Chặn tự duyệt, ủy quyền có thời hạn | I08, I12 |
| Việc của tôi, người nhận bản sao, ý kiến và tệp khi duyệt | I15, I16, I17 |
| Hạn duyệt và nhắc, bản in dấu vết duyệt | I18, I20 |
| Bàn giao hàng loạt khi có người nghỉ việc | I23 |
| Cờ bật tắt theo loại chứng từ | I26 |
| Chuyển luồng duyệt yêu cầu văn bản ở phase 2 sang bộ máy mới | |

**Xong là kiểm được:**
- Khai một luồng 4 bước bằng giao diện, **không sửa dòng mã nào**, không deploy lại, phiếu chạy đúng qua 4 người.
- Người ở bước 1 cũng là người ở bước 3 → hệ thống tự bỏ qua bước 3, và **nhật ký ghi rõ lý do bỏ qua**.
- Tắt trạng thái một nhân sự đang giữ 3 phiếu → 3 phiếu chuyển sang người thay thế, **không phiếu nào tự động duyệt qua**.
- Sửa luồng khi có 5 phiếu đang chạy → 5 phiếu đó vẫn đi theo luồng cũ tới khi kết thúc.
- Tạo một phiếu không khớp điều kiện nhánh nào → rơi vào nhánh mặc định, **không biến mất khỏi mọi danh sách**.
- **Chạy lại 5 kiểm thử Thu mua ở N01 → vẫn xanh.** Bộ máy mới chưa bật cho Thu mua nên không được phép ảnh hưởng gì.

**Việc nên làm trước khi viết dòng mã đầu tiên:** lấy 5 luồng thật của Thu mua cộng 3 luồng văn thư (duyệt yêu cầu, duyệt nội dung, duyệt bản clone), **khai thử cả 8 luồng ra giấy** bằng đúng mô hình dữ liệu định làm. Chỗ nào khai không nổi thì mô hình còn thiếu — sửa lúc còn trên giấy rẻ hơn nhiều so với sửa khi đã có phiếu chạy trong đó.

**Điều kiện chuyển phase:** sáu bài kiểm ở trên đều đạt.

---

## 8. Phase 4 · Ban hành, phạm vi, clone

Phase này **cần câu trả lời cho B5 (bản clone có phải duyệt lại không) và B6 (pháp nhân con im lặng quá lâu thì sao)**. Chưa có thì làm phần phạm vi trước, để phần clone lại sau.

| Việc | Mã |
|---|---|
| Vòng đời văn bản, ban hành, ký điện tử nội bộ, ghi rõ loại chữ ký | J01, J02, J03, J04 |
| Phạm vi ba kiểu, bao gồm và loại trừ, bắt buộc kèm pháp nhân, áp cho đơn vị con | F01, F02, F03, F04 |
| Màn hình "văn bản áp dụng cho tôi", thông báo theo phạm vi | F05, J05 |
| **Clone xuống pháp nhân con**: tạo nháp, giữ liên kết ngược, số hiệu riêng | F06, F07, F08 |
| Gửi thư kèm bản nháp, bảng theo dõi các bản clone | F09, F10 |
| Bản gốc lên phiên bản thì đánh dấu con cần rà lại | F11 |
| Màn hình chọn cơ chế lúc ban hành: gắn phạm vi hay clone | F13 |
| Cảnh báo tác động khi sửa cha, xử lý khi bãi bỏ cha | E07, E08 |
| **Sửa văn bản hành chính bằng cách ra văn bản mới**: nhãn "đã bị sửa đổi" trên bản cũ, tác động tự động của quan hệ thay thế và bãi bỏ | J10 |
| Quyết định ban hành kiểm ở mức phiên bản | J11 |

**Xong là kiểm được:**
- Ban hành một quyết định của Tập đoàn cho toàn bộ 13 pháp nhân bằng **một văn bản** → tất cả nhân sự trong phạm vi nhận thông báo.
- Ra Quyết định 47 sửa đổi Quyết định 15 → mở Quyết định 15 **thấy ngay nhãn cảnh báo và đường dẫn sang 47**; Quyết định 15 vẫn ở trạng thái có hiệu lực, số hiệu và nội dung không đổi một chữ.
- Ban hành theo cơ chế **clone** → mỗi pháp nhân có một bản nháp riêng, mỗi bản mang số hiệu của chính pháp nhân đó, mỗi bản đều dẫn ngược về bản gốc và **không có nút nào xóa được liên kết đó**.
- Mở bảng theo dõi clone → trả lời được ngay câu "12 công ty con đang ở phiên bản nào, ai chưa đụng tới".
- Bản gốc lên phiên bản 2.0 → mọi bản clone đang ở 1.0 tự chuyển sang "cần rà lại", người phụ trách nhận thông báo.
- Chọn phạm vi là một phòng ban mà quên chọn pháp nhân → **hệ thống chặn**, không cho lưu.

**Điều kiện chuyển phase:** sáu bài kiểm ở trên đều đạt.

---

## 9. Phase 5 · Quyền truy cập và tra cứu

Cần câu trả lời B3 (mấy mức mật, ai được cấp mức cao). Làm song song với phase 3 và 4 được nếu có người thứ hai.

| Việc | Mã |
|---|---|
| Mức mật của văn bản, mức mật được phép của từng người, loại văn bản bảo mật | G03, G04, G10 |
| Chia sẻ đích danh trên từng văn bản, có thời hạn | G05 |
| Cấm luôn thắng cho phép, chia sẻ không tự vượt được mức mật | G06, G07 |
| **Chia sẻ**: nhóm tự đặt, chia đặc cách vượt mức mật có duyệt và có hạn, màn hình chọn cách xử lý thay vì báo lỗi, hạ mức mật qua duyệt, không lan xuống con và không chia tiếp | G14–G17, G19 |
| Nút "tạo bản trích" trên màn hình chia sẻ, và danh sách bản trích khi mở bản gốc. **Phần soạn và phần quan hệ đã làm ở phase 2** | G18 → C19, E11 |
| **Thu hồi**: giữ dấu vết, hiện ai đã kịp tải, thu hồi tự động, nhật ký | G20, G21, G22, G24 |
| Mức Tuyệt mật chặn tải, chỉ xem trên web có dấu chìm mang tên người xem | G09 |
| Nghỉ việc là mất quyền ngay | G11 |
| Phạm vi dữ liệu mới: pháp nhân của mình và toàn bộ công ty con | G02 |
| Danh sách, bộ lọc, tìm theo tiêu đề và số hiệu, trang chi tiết, trang chủ theo vai | K01, K02, K04, K06 |
| **Kết quả tìm luôn đi qua kiểm quyền** | K03 |

**Xong là kiểm được:** tạo một văn bản mức Tuyệt mật, đăng nhập bằng tài khoản mức Nội bộ, thử đủ **bốn chỗ**:

| Thử | Kết quả phải là |
|---|---|
| Mở danh sách văn bản | Không thấy, kể cả tiêu đề |
| Tìm theo đúng số hiệu | Không ra kết quả nào |
| Gọi thẳng địa chỉ trang chi tiết | Bị từ chối |
| Gọi thẳng địa chỉ tải tệp | Bị từ chối |

Thiếu một trong bốn chỗ là chưa đạt. Và thêm bốn bài nữa về chia sẻ và thu hồi:

| Thử | Kết quả phải là |
|---|---|
| Chia sẻ thường văn bản Tuyệt mật đó cho tài khoản mức Nội bộ | **Vẫn không xem được**, và màn hình hiện bốn cách xử lý chứ không hiện câu "không đủ quyền" |
| Chia đặc cách, có người đủ mức mật duyệt, hạn 7 ngày | Xem được trên web, **không có nút tải**, có dấu chìm mang tên người xem |
| Qua ngày thứ 8 | Tự mất quyền, không ai phải bấm gì |
| Thu hồi tay giữa chừng | Mất quyền trong vài giây (không phải 60 giây), dòng chia sẻ **vẫn còn trong nhật ký**, và màn hình hiện ai đã kịp tải tệp về |

**Điều kiện chuyển phase:** cả tám bài kiểm đạt.

---

## 10. Phase 6 · Chuyển dữ liệu và chạy thử

| Việc |
|---|
| Nhập 32 loại văn bản, 13 mã pháp nhân, mã phòng ban, quy tắc cha con — bản chính thức đã được Pháp chế duyệt |
| Nhập tệp mẫu cho từng loại văn bản |
| Khai luồng duyệt thật cho từng loại văn bản |
| Đưa văn bản đang hiệu lực vào hệ thống, ưu tiên quy chế và quy trình đang dùng hàng ngày |
| Đối chiếu số lượng, kiểm tra ngẫu nhiên khoảng 30 văn bản |
| Cho 10–15 người thật dùng trên dev, mỗi ngày ghi nhận lỗi và sửa |

Phần "đưa văn bản cũ vào" là **việc của người, không phải việc của máy** — cần người của Hành chính và Pháp chế bỏ công thật. Nếu tới phase này chưa có ai được giao, phase 6 đứng lại. Đây là chỗ dễ tắc nhất sau phase 0, và cũng là việc **bắt đầu song song được ngay từ bây giờ** chứ không cần chờ phần mềm.

**Điều kiện chuyển phase:** người thật dùng được hết một vòng nghiệp vụ mà không cần đội phần mềm ngồi cạnh.

---

## 11. Phase 7 · Đưa vào dùng thật

| Việc |
|---|
| Sửa nốt lỗi từ chạy thử, chốt danh sách "không sửa nữa trong bản này" |
| Viết hướng dẫn sử dụng, đưa lên Trung tâm hướng dẫn đang có |
| Đào tạo: một buổi cho người soạn, một buổi cho người duyệt, một buổi cho quản trị |
| Deploy prod, bật cho **một pháp nhân trước** |
| Theo dõi, rồi mở rộng dần ra các pháp nhân còn lại |

**Sáu điều kiện để bật trên prod:**

| # | Điều kiện |
|---|---|
| 1 | Không còn lỗi mức chặn |
| 2 | 5 kiểm thử luồng duyệt Thu mua vẫn xanh |
| 3 | Bài kiểm cấp số 100 kết nối vẫn đúng |
| 4 | Bài kiểm bốn chỗ về mức mật ở phase 5 vẫn đúng |
| 5 | Có người của Hành chính nhận vai trò quản trị văn thư — không để đội phần mềm giữ |
| 6 | Có đường lui: tắt phân hệ văn thư mà Thu mua vẫn chạy bình thường |

Bật cho một pháp nhân trước chứ không bật cả 13 cùng lúc. Sai sót phát hiện ở pháp nhân đầu thì sửa cho 12 nơi còn lại; bật hết một lượt thì sai sót nhân lên 13 lần.

---

## 12. Phase 8 · Chuyển Thu mua sang bộ máy duyệt mới

**Tùy chọn, không bắt buộc.** Điều kiện mở: văn thư đã chạy thật một thời gian đủ dài, không có sự cố về duyệt.

Cách làm: **mỗi lần một luồng**, theo thứ tự rủi ro tăng dần.

| Thứ tự | Luồng | Vì sao xếp ở đây |
|---|---|---|
| 1 | Yêu cầu khảo sát | Ít tiền, ít người liên quan, sai thì sửa dễ |
| 2 | Khảo sát | |
| 3 | Yêu cầu mua hàng | |
| 4 | Đơn mua hàng | Có tiền, có nhà cung cấp bên ngoài |
| 5 | Yêu cầu thanh toán | Rủi ro cao nhất, làm cuối |

Mỗi luồng bật bằng cờ, tắt cờ là quay lại đường cũ ngay. Chạy song song một thời gian trước khi bỏ mã cũ.

Xong phase này thì Thu mua có được miễn phí những thứ 5 luồng viết tay hiện nay không có: ủy quyền có thời hạn, trả lại đúng bước, nhắc quá hạn, bàn giao hàng loạt khi nghỉ việc, bản in dấu vết duyệt.

---

## 13. Phase 9 · Mở rộng

Không có thứ tự cứng. Xếp theo giá trị trên công sức, làm khi có chỗ trống.

| Việc | Mã | Điều kiện mở |
|---|---|---|
| Xác nhận đã đọc và báo cáo ai đã đọc ai chưa | J06, J07 | Trả lời câu hỏi ở `00` |
| Sổ văn bản đi và sổ văn bản đến | S01–S03 | Trả lời A1 |
| Nhắc rà soát định kỳ, cảnh báo sắp hết hiệu lực | M07, M08 | Không |
| Cảnh báo trùng nội dung bằng AI | L04 | Có đủ vài trăm văn bản trong kho |
| Hỏi đáp trên kho văn bản | L06 | Sau L04 |
| Tìm toàn văn tiếng Việt không dấu | K05 | Trả lời C4 |
| Ký số có giá trị pháp lý | J08 | Trả lời A2, cần mua chứng thư số |
| Xem tệp trên web không cần tải, dấu chìm động, tách quyền xem và tải | C10, C11, G08, G09 | Làm theo đúng thứ tự này |
| Form nhập trên web cho 3–5 loại dùng nhiều nhất | C09 | Trả lời B1 |
| Bảng điều khiển văn thư | M09 | Không |
| So sánh hai phiên bản | C08 | Không |

---

## 14. Chia việc cho nhiều người

| Phase | Chia được không |
|---|---|
| 0 | **Khó chia.** Các việc đụng cùng chỗ trong nền, hai người sửa song song là rối |
| 1, 2 | Chia được phần nhập liệu danh mục, phần viết mã thì khó |
| 3 và 5 | **Chia đôi tốt nhất** — một người làm bộ máy duyệt, một người làm quyền truy cập và tra cứu. Hai phần gần như không đụng nhau |
| 4 | Chia được: phạm vi và clone là hai mảng tách rời |
| 6 | **Càng nhiều người càng tốt** — phần lớn là nhập liệu, không phải viết mã |
| 7 | Đào tạo và viết hướng dẫn tách được khỏi việc sửa lỗi |

Người thứ hai vào giữa chừng thì mất một quãng để hiểu mã nguồn — chia đôi việc **không có nghĩa là xong nhanh gấp đôi**.

Nếu có thực tập sinh: giao được A01, A07 và toàn bộ phần nhập liệu ở phase 6. **Không giao việc nào chạm vào phân quyền, cấp số hay bộ máy duyệt.** Và chỉ làm trên môi trường dev, không có tài khoản prod.

---

## 15. Làm song song được và không được

| Làm song song được | Vì sao |
|---|---|
| Nhập 32 loại văn bản, mã pháp nhân, mã phòng ban — từ phase 1 | Việc của người, không chặn việc viết mã |
| Viết hướng dẫn sử dụng — từ phase 2 | Màn hình đã tương đối ổn định |
| **Rà soát và số hóa văn bản giấy đang hiệu lực — bắt đầu ngay từ bây giờ** | Không phụ thuộc phần mềm chút nào, và là phần dễ tắc nhất |
| Trả lời 17 câu hỏi ở `00` | Chỉ chặn phase 4 trở đi |
| Phase 3 với phase 5 | Hai mảng gần như không đụng nhau |

| Không làm song song được | Vì sao |
|---|---|
| Phase 0 với bất cứ phase nào khác | Đụng vào nền, làm chồng lên là không biết lỗi ở đâu |
| Phase 3 với phase 4 | Phase 4 dùng bộ máy duyệt của phase 3 |
| Phase 8 với phase 7 | Chuyển Thu mua sang bộ máy mới đồng thời với việc đưa văn thư vào dùng thật — hỏng một cái là không biết tại cái nào |

---

## 16. Rủi ro và cách xử lý

| Rủi ro | Khả năng | Nếu xảy ra | Cách giảm |
|---|---|---|---|
| Phase 0 làm gián đoạn Thu mua | Trung bình | Vài trăm người không làm việc được | N01 làm trước tiên; mỗi việc một lần deploy; đường lui bằng cờ; deploy dev trước |
| Cấp số bị trùng khi nhiều người bấm cùng lúc | Thấp nếu làm đúng | Hai văn bản cùng số, hỏng giá trị pháp lý | Khóa dòng bộ đếm, ràng buộc duy nhất ở tầng dữ liệu, bài kiểm 100 kết nối |
| Không có người của Hành chính nhận việc số hóa văn bản cũ | **Cao** | Phase 6 tắc, hệ thống rỗng không ai dùng | Chốt người phụ trách ngay, bắt đầu số hóa song song từ bây giờ |
| 17 câu hỏi ở `00` không được trả lời | Trung bình | Phase 4 và 5 phải đoán, làm xong lại sửa | Gom vào một buổi họp; câu nào chưa có thì ghi giả định vào tài liệu và làm theo giả định đó |
| Yêu cầu thay đổi phát sinh liên tục trong lúc làm | **Cao** | Lộ trình giãn dần, không ai thấy | Áp quy trình kiểm soát thay đổi đã có; yêu cầu mới mặc định vào phase 9, muốn vào bản đầu thì phải chỉ ra bỏ tính năng nào |
| Bộ máy duyệt làm xong nhưng không đủ mềm, vẫn phải sửa mã cho từng loại | Trung bình | Mất công gấp đôi | Khai thử 8 luồng ra giấy trước khi viết mã, như mục 7 |
| Đưa văn bản mật vào trước khi phase 0 xong | Thấp | Rò rỉ, không thu hồi lại được | Không mở tài khoản văn thư trên prod cho tới khi phase 0 đạt |

---

## 17. Ảnh hưởng tới các tài liệu đang có

| Tài liệu | Ảnh hưởng |
|---|---|
| [`01` Ngắn hạn 2026](../01-ngan-han-2026.md) | Bước 1 khảo sát nghiệp vụ HRM và bước 6 HRM **lùi lại phía sau văn thư**. Bước 5 bộ máy duyệt dùng chung **được làm sớm hơn** — chính là phase 3 ở đây |
| [`06` Lộ trình nền tảng và HRM](../06-lo-trinh-nen-tang-va-hrm.md) | Các hạng mục PQ11, PQ13, PQ14, DB15, H17, H18 **được làm trong phase 0**, sớm hơn thứ tự cũ |
| [`08` Danh sách task củng cố](../08-danh-sach-task-cung-co.md) | Các task CC tương ứng với nhóm N chuyển lên đầu; phần còn lại giữ nguyên thứ tự |
| [`10` Báo cáo WorkHub](../10-lo-trinh-phat-trien-hrm.md) | Mốc thời gian trong báo cáo không còn đúng. Phân hệ Văn bản **được làm trước phân hệ Con người**, ngược với thứ tự đã trình. Cần cập nhật mục 7.3 khi báo cáo lần tới |
| [`09` Phúc lợi điểm và POS](../09-phuc-loi-diem-va-pos.md) | Không đổi. Phần gọi thử API POS365 vẫn làm song song được vì không đụng mã nguồn |

Bốn tài liệu trên **chưa sửa** — chờ chốt lộ trình này rồi sửa một lần, tránh sửa đi sửa lại.

---

## 18. Việc bắt đầu ngay, không chờ gì

| Việc | Ai | Chờ ai không |
|---|---|---|
| Bắt đầu N01 — viết kiểm thử tự động cho 5 luồng duyệt Thu mua | Đội phần mềm | **Không chờ gì** |
| Bắt đầu rà soát và số hóa văn bản giấy đang hiệu lực | Hành chính | Không chờ phần mềm |
| Gửi 17 câu hỏi ở [`00`](./00-danh-gia-va-cau-hoi.md) cho người quyết, hẹn buổi trả lời | Chủ trì | |
| Chốt ai của Hành chính phụ trách quản trị văn thư về sau | Ban lãnh đạo | |
| Đưa 32 loại văn bản, 13 mã pháp nhân, mã phòng ban sang Pháp chế duyệt | Hành chính | |

---

Tiếp theo: [`03` Tính năng Lark Approver](./03-lark-approver.md) · [`04` Các bảng dữ liệu](./04-bang-du-lieu.md)
