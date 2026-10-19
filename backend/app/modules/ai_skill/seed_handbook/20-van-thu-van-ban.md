# Văn thư — quản lý văn bản (tri thức nền)

Phân hệ **Văn thư** (`/document`): soạn thảo, phê duyệt, ban hành, đánh số, phân
phối và theo dõi vòng đời văn bản nội bộ.

Gói này là **luật nghiệp vụ** — thứ trợ lý không được nói sai. Cần **các bước bấm
nút chi tiết** thì tra HDSD bằng `search_docs`, đừng tự bịa đường đi.

---

## 1. Vòng đời và mười một trạng thái

```
Nháp → Gửi duyệt (Đang duyệt) → Duyệt xong → Có hiệu lực
                 ├─ Trả về    (còn đường: sửa rồi gửi lại)
                 ├─ Rút phiếu (người nộp tự rút, về Nháp)
                 └─ Từ chối   (hết đường, phải Sao chép)
```

| Trạng thái | Nghĩa | Sửa được? |
|---|---|---|
| **Nháp** | Đang soạn | Có |
| **Đang duyệt** | Đã gửi đi, đóng băng toàn bộ | **Không** |
| **Chờ ban hành** | Ký đủ rồi, **chưa có số hiệu**, chờ người soạn bấm Ban hành | **Không** |
| **Đã duyệt** | **Đã ban hành xong**, có số hiệu, chỉ chưa tới ngày hiệu lực | Không |
| **Có hiệu lực** | Đang áp dụng | Không (phải mở phiên bản mới) |
| **Trả về** | Người duyệt trả lại | Có |
| **Đã từ chối** | Khoá hẳn | **Không** |
| **Đã thay thế** · **Hết hiệu lực** · **Bãi bỏ** · **Lưu trữ** | Đã kết thúc vòng đời | Không |

⚠️ **Đừng nhầm «Đã duyệt» với «Chờ ban hành».** Cả hai đều đã ký xong nhưng:
- **Đã duyệt** = *đã ban hành rồi*, **có số hiệu**, không ai phải làm gì nữa, chỉ chờ tới ngày hiệu lực.
- **Chờ ban hành** = *chưa ban hành*, **chưa có số hiệu**, đang chờ **một con người bấm nút**.

Nói nhầm là người dùng ngồi chờ một việc không bao giờ tới, hoặc bỏ quên một việc đang chờ họ.

---

## 2. Ba câu hỏi người dùng hay hỏi nhất

### 2.1 «Sao tôi không sửa được văn bản?»

**Không bao giờ trả lời chung chung "liên hệ quản trị".** Có ba lý do khác nhau và
**ba lối ra khác nhau** — phải hỏi/xem trạng thái rồi trả lời đúng cái:

| Trạng thái | Vì sao khoá | Lối ra |
|---|---|---|
| **Đang duyệt** | Người duyệt phải ký đúng bản họ đọc | **Rút phiếu** (nếu chưa ai ký), hoặc chờ người duyệt **trả lại** |
| **Chờ ban hành** | Chữ ký đã đặt lên nội dung này rồi | Nhờ người duyệt **trả lại** |
| **Đã từ chối** | Hết đường đi tiếp | Bấm **Sao chép** để có bản nháp mới |
| **Đã ban hành** (Đã duyệt / Có hiệu lực) | Số hiệu đã phát ra ngoài | **Mở phiên bản mới** (bản 2.0) rồi gửi duyệt |

Đang duyệt thì khoá **toàn bộ**, không chỉ thân bài: tiêu đề, mức mật, lề trang,
tệp đính kèm đều khoá.

### 2.2 «Sao tôi không thấy / không mở được văn bản này?»

⚠️ Hệ cố ý trả **404 (không tìm thấy)** thay vì 403 khi người dùng không được đọc —
vì 403 tự nó đã tiết lộ *"có văn bản đó tồn tại"*.

**Cho nên trợ lý TUYỆT ĐỐI không được nói «văn bản này không tồn tại».** Câu đúng là
*"bạn không nằm trong nhóm được xem văn bản này"*.

Quyền đọc một văn bản đến từ **năm nguồn**, chỉ cần một là đủ:
1. **Phạm vi vai trò** — quyền `document.read` kèm phạm vi dữ liệu (bản thân / phòng / công ty / tất cả).
2. **Phạm vi áp dụng** — người mà văn bản đó áp dụng cho.
3. **Chia đích danh** — được chia riêng cho cá nhân / phòng ban / vai trò.
4. **Thành viên quyển sổ** chứa văn bản.
5. **Đang hoặc đã duyệt** văn bản đó (chỉ mở quyền **đọc**, không cho sửa/ban hành).

⚠️ **Dòng CẤM đích danh thắng tất cả** — thắng cả dòng cho phép, thắng cả phạm vi
vai trò, thắng cả quyền theo sổ. Nếu ai đó bị cấm đích danh thì không nguồn nào ở
trên cứu được.

### 2.3 «Phiếu của tôi bị trả về hay bị từ chối?»

Ba nhịp **hoàn toàn khác nhau**, dùng sai từ là người dùng hiểu sai tình trạng:

| Nhịp | Ai làm | Còn đường đi tiếp? |
|---|---|---|
| **Trả về** | Người duyệt | **CÒN** — sửa rồi **gửi duyệt lại trên chính văn bản đó** |
| **Từ chối** | Người duyệt | **HẾT** — khoá sửa, muốn làm lại phải **Sao chép** ra bản mới |
| **Rút phiếu** | **Chính người nộp** | Về **Nháp**. Không ai trả gì cho ai |

Cả ba đều **bắt buộc ghi lý do**. Rút phiếu chỉ làm được **khi chưa ai ký**; đã có
chữ ký thì phải dùng Trả lại hoặc Từ chối.

---

## 3. Phê duyệt

- Luồng duyệt khai ở **Phê duyệt › Luồng duyệt** (`/approval/flows`); công tắc bật
  bộ máy nhiều bước ở `/approval/engine`. **Chưa bật công tắc thì luồng không chạy.**
- Luồng khai **đúng pháp nhân thắng luồng dùng chung**, bất kể độ ưu tiên.
- **Người nộp không tự duyệt phiếu của mình.**
- Không tìm được người duyệt và không có người dự phòng → **phiếu dừng lại và báo
  quản trị**, hệ **KHÔNG tự duyệt qua**. Đây là cố ý: văn bản có hiệu lực mà không ai
  chịu trách nhiệm là điều không được phép.
- Trùng người ở hai bước liền nhau thì tự bỏ qua và ghi rõ lý do.
- Uỷ quyền: có hạn, **không uỷ quyền dây chuyền**, **không uỷ quyền cho chính mình**,
  và không dùng chéo loại chứng từ.

⚠️ **Không hướng dẫn người dùng đi đường tắt.** Đang chạy trong luồng nhiều bước thì
nút «Duyệt và ban hành» của luồng cũ bị chặn — đó là chốt chặn, không phải lỗi.

---

## 4. Ban hành

Ban hành **không lùi lại được**:
- **Số hiệu cấp ra là vĩnh viễn.** Bãi bỏ văn bản **không trả số về** cho văn bản sau dùng.
- Phiên bản bị **khoá một chiều**.
- Văn bản đã có số hiệu thì **không đổi được loại và pháp nhân ban hành** (hai thứ đó
  nằm trong chính chuỗi số).
- Muốn gỡ bỏ một văn bản đã ban hành: **Bãi bỏ**, không phải Xoá. Chỉ xoá được khi
  còn *Nháp* **và** chưa cấp số.

Loại nào khai *"ban hành phải kèm Quyết định"* mà thiếu thì bị chặn — phải khai quan
hệ **«Kèm theo»** tới Quyết định ban hành ở tab Quan hệ.

### 4.1 Duyệt xong KHÔNG phải lúc nào cũng ban hành

Cột **«Chờ người soạn ban hành»** trên *Loại văn bản* (`/document/settings?tab=types`)
quyết định nhịp cuối:

- **Tắt** (mặc định, hầu hết loại): ký đủ chữ ký là **ban hành luôn**.
- **Bật**: dừng ở **Chờ ban hành**, và **chỉ NGƯỜI SOẠN THẢO** bấm được nút Ban hành.
  Người có quyền duyệt **cũng không bấm thay được** — người ký đã ký xong phần của họ,
  phát hành là trách nhiệm khác.

Nếu người dùng hỏi *"duyệt xong rồi sao chưa có số hiệu?"* → gần như chắc chắn là loại
này, và việc đang chờ **chính họ** (nếu họ là người soạn) bấm Ban hành.

### 4.2 Gửi thông báo danh nghĩa địa chỉ khác

Lúc bấm Ban hành có ô **«Gửi thông báo danh nghĩa»**: chọn hộp thư để thư báo đi dưới
tên một phòng ban thay vì địa chỉ cá nhân — ví dụ nhân sự hành chính đăng nhập bằng
tài khoản của mình nhưng gửi Thông báo nghỉ lễ danh nghĩa `hr@...`.

- Hộp thư khai ở **Quản trị › Hộp thư gửi** (`/system/mailboxes`).
- **Chỉ hiện những hộp thư mà chính người đó được cấp.** Không được cấp thì không chọn được —
  hướng họ đề nghị quản trị thêm vào hộp thư, đừng bảo họ tự đổi email cá nhân.
- Không chọn gì thì gửi bằng địa chỉ hệ thống như trước (đây là **thêm lựa chọn**, không bắt buộc).

---

## 5. Phạm vi áp dụng và bản riêng cho pháp nhân con

**Phạm vi áp dụng** = *"văn bản này ai phải làm theo"*, khác hẳn *"ai được đọc"*.

- **Không khai dòng nào** → áp cho **toàn bộ pháp nhân ban hành**.
- Khai một dòng là **tắt mặc định** đó đi.
- **Loại trừ thắng bao gồm.** Người bị loại trừ gõ thẳng đường dẫn cũng không vào được.
- *Gồm đơn vị con* chỉ có nghĩa với chiều pháp nhân. **Tập đoàn không tick cờ đó thì
  không lan xuống công ty con.**

**Bản riêng (clone):** nếu phạm vi có pháp nhân khác nơi ban hành thì lúc ban hành,
**mỗi pháp nhân đó nhận ngay một bản nháp riêng** — chép nội dung gốc, để họ sửa cho
đúng công ty mình rồi **tự ban hành với số hiệu của chính họ**.

- Bản gốc lên bản 2.0 **không đẻ thêm bản thứ hai**; bản con bị đánh dấu **cần rà lại**
  và người phụ trách được báo.
- Pháp nhân con **phải có luồng duyệt riêng** của mình. Chưa khai thì gửi duyệt bản
  riêng sẽ bị chặn — hướng họ khai luồng cho pháp nhân đó, đừng bảo dùng luồng chung.

---

## 6. Văn bản cá nhân (đơn nghỉ phép…)

Loại văn bản đánh dấu **cá nhân** thì **thoát khỏi phạm vi vai trò**:

- Đồng nghiệp cùng phòng **không thấy** đơn nghỉ phép, dù vẫn thấy văn bản thường cùng công ty.
- Thành viên sổ và phạm vi áp dụng **cũng không mở được**.
- Chỉ những người **có chân trong tờ đơn** mới thấy: người nghỉ · người lập hộ ·
  người đang/đã duyệt · người được chia đích danh · vai trò phạm vi *tất cả* (HR, quản trị).

⚠️ **Trợ lý tuyệt đối không tiết lộ tiêu đề, nội dung hay sự tồn tại của đơn nghỉ phép
của người khác** — kể cả khi người hỏi là quản lý, trừ khi chính hệ thống trả dữ liệu
đó ra cho họ. Ô tìm kiếm của hệ cũng đã được bịt để không lộ tiêu đề đơn.

---

## 7. Tệp đính kèm

- Đính kèm văn bản **không phát link công khai** — chỉ mở được qua đường tải có kiểm quyền.
- Có thể đặt **hạn xem**: quá hạn là không mở được nữa (báo rõ ngày hết hạn).
- **Mỗi lượt mở/tải đều ghi nhật ký** trên chính văn bản, và mở quá nhiều trong một
  khoảng thời gian sẽ sinh cảnh báo cho quản trị.

Nói cho người dùng biết điều này khi họ hỏi về chia sẻ tài liệu mật — nó là tính năng,
không phải để doạ.

---

## 8. Từ dùng đúng như trên màn hình

Dùng sai từ là người dùng tìm không ra nút:

| Nói thế này | Không nói |
|---|---|
| Gửi duyệt | trình ký, submit |
| Trả về | trả lại hồ sơ, reject |
| Từ chối | huỷ, cancel |
| Rút phiếu | thu hồi, rollback |
| Ban hành | phát hành, publish |
| Bãi bỏ | xoá, huỷ văn bản |
| Phiên bản mới / bản 2.0 | sửa lại, cập nhật |
| Phạm vi áp dụng | người nhận, danh sách phân phối |
| Bản riêng (clone) | bản sao, copy |
| Mức mật | độ bảo mật, security level |

---

## 9. Ranh giới của trợ lý ở phân hệ này

- **Chỉ trả lời trong phạm vi người hỏi được xem.** Không suy ra sự tồn tại của văn
  bản mà họ không có quyền đọc.
- **Không bịa số hiệu.** Số do hệ cấp trong cùng giao dịch ghi bản ghi; màn tạo chỉ
  có *xem trước*, và con số xem trước có thể lệch nếu có người được cấp số xen vào.
- **Không hướng dẫn cách đi vòng qua luồng duyệt**, kể cả khi người dùng nói gấp.
  Việc gấp thì hướng họ dùng **độ khẩn** và liên hệ người duyệt, không phải né bước ký.
- Chưa đủ căn cứ thì nói rõ là chưa đủ căn cứ. **Không có trong tài liệu thì nói không
  có**, đừng đoán.
- Cần các bước thao tác chi tiết (bấm nút nào, ở đâu) thì tra HDSD bằng `search_docs`
  và trích nguồn.
