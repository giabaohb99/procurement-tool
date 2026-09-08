# Dự án — quản lý công việc

Phân hệ **Dự án** (`/project`): giao việc, theo dõi tiến độ và trao đổi quanh từng
công việc. Dựng theo Lark Tasks — bốn khung nhìn trên cùng một bộ dữ liệu.

> **Chỉ có trên `frontend-v2/` (ERP v2, cổng 8083).** `frontend/` đã đóng băng nên
> không có bản tương ứng.
>
> Thiết kế chi tiết: `doc/erp/cong-viec/` (01 danh sách tính năng · 02 bảng dữ liệu ·
> 04 phân quyền · 05 giao diện). Tài liệu này mô tả **thứ người dùng nhìn thấy**.

---

## 1. Các khái niệm — đọc trước, đừng đoán theo tên

Bốn tầng, mỗi tầng một nghĩa riêng. Gọi sai tầng là tìm không ra nút.

| Tên trên màn hình | Là gì | Ghi chú quan trọng |
|---|---|---|
| **Nhóm** | Thư mục chứa dự án, tối đa **2 cấp** | Chỉ để xếp gọn cây bên trái. Thành viên nhóm được **kế thừa** xuống mọi dự án trong nhóm |
| **Dự án** | Một danh sách công việc | **Đây là đơn vị phân quyền chính.** Mọi câu hỏi "ai thấy được gì" đều quy về dự án |
| **Cột** | Một cột kanban (`Cần làm`, `Đang làm`…) | Là **nhãn người dùng tự đặt**, KHÔNG phải trạng thái hệ thống — xem §2 |
| **Công việc** | Một việc | Nằm trong đúng một cột |
| **Việc con** | Việc nhỏ bên trong một công việc | Chỉ sống trong panel chi tiết: **không** thành thẻ kanban, **không** thành dòng ở khung Danh sách |
| **Cột mốc** | Một công việc đặc biệt, chỉ có MỘT ngày | Gantt vẽ thành hình thoi thay vì thanh |

⚠️ **«Dự án» và «danh sách công việc» là MỘT thứ**, không phải hai tầng chồng nhau.
Thư mục mã nguồn vẫn tên `work`, API vẫn `/api/work/...`, bảng vẫn `tab_work_*` — chỉ
tên hiển thị cho người dùng là «Dự án».

---

## 2. Cột kanban KHÁC trạng thái công việc

Đây là chỗ nhầm nhiều nhất.

| | Cột kanban | Trạng thái |
|---|---|---|
| Ai đặt tên | Từng dự án tự đặt | Hệ thống, cố định |
| Giá trị | Bất kỳ (`Chờ duyệt nội dung`, `Đã chạy`…) | **Đang mở · Hoàn thành · Đã hủy** |
| Đổi bằng cách | Kéo thẻ sang cột khác | Tick ô tròn, hoặc chọn ở panel |
| Dùng để | Xếp việc theo quy trình riêng của đội | Đếm việc chưa xong, nhắc hạn, báo cáo |

Hệ quả: kéo một việc vào cột tên «Xong» **không** làm nó thành «Hoàn thành». Muốn đánh
dấu xong thì **tick ô tròn** trên thẻ / trên dòng, hoặc đổi trạng thái trong panel.

---

## 3. Bốn khung nhìn

Chọn bằng hàng tab ngay dưới tên dự án. Khung nhìn đang mở, cách sắp xếp, các trường
hiện trên thẻ và mức phóng Gantt đều **nhớ theo từng dự án** (lưu tại trình duyệt).

### 3.1 Bảng (Kanban)

Mỗi cột một dải thẻ. Kéo thả được **thẻ trong cột** (đổi thứ tự), **thẻ sang cột khác**,
và **kéo ngang để đổi thứ tự cột**.

Trên thẻ: **ô tick xong việc**, tên việc, rồi các trường bật ở nút «Tùy chỉnh»
(phụ trách · trạng thái · ngày bắt đầu · hạn chót · việc con `n/m` · số bình luận · nhãn
tùy biến). Trường nào không có giá trị thì **bỏ hẳn dòng**, không vẽ gạch ngang.

⚠️ Đang sắp xếp theo tiêu chí khác «Tay (kéo thả)» thì **khóa kéo** — thả xong danh sách
tự xếp lại chỗ cũ, nhìn như thao tác bị nuốt.

### 3.2 Danh sách

Bảng phẳng, gom theo cột (thu/mở được). Sửa được ngay trên dòng: tên, người phụ trách,
ngày, trạng thái, nhãn tùy biến. Bung mũi tên để xem việc con.

Cột hiện những gì là do nút «Tùy chỉnh» — **cùng một bộ cột** với thẻ kanban và với lưới
trái của Gantt.

### 3.3 Gantt

Lưới trái **chính là khung nhìn Danh sách** (cùng cột, cùng ô sửa tại chỗ, cùng kéo thả),
bên phải là trục thời gian.

- Mức phóng **Ngày · Tuần · Tháng**; nút **Hôm nay** và ‹ › nhảy từng trang.
- Kéo cả thanh để **dời lịch**, kéo hai mép để **đổi ngày**.
- Việc chưa có ngày: kéo ngay trên hàng trống của nó để **đặt lịch**.
- **Mũi tên phụ thuộc** giữa hai việc: kéo từ chấm ở đầu thanh này sang thanh kia; bấm
  mũi tên để đổi kiểu hoặc xóa.
- Hàng **nhóm** có một thanh tổng gom con, tô phần trăm việc đã xong. Thanh này **không
  kéo được** — ngày của nó là ngày tính ra.
- Trục luôn sẵn **hai năm** (đầu năm nay → hết năm sau) kể cả dự án trống, để đặt lịch
  cho quãng chưa có việc nào.
- Nút ẩn/hiện lưới trái nằm ở góc trên, cạnh nhãn tháng.

### 3.4 Hoạt động

Nhật ký gộp của **cả dự án**, mới nhất trên cùng, cuộn để lấy thêm. Gom ba nguồn:

- việc trong dự án (kể cả **việc đã xóa** — đó là dòng người ta cần nhất),
- thành viên vào / ra,
- sửa chính dự án và các cột.

Lọc nhanh theo **loại sự kiện** và theo **người**. Dòng nào gắn với một việc thì bấm mở
được panel chi tiết việc đó.

⚠️ **Bình luận KHÔNG nằm trong dòng hoạt động** (nó không ghi nhật ký thao tác), và
**chưa lọc được theo một việc cụ thể**.

---

## 4. Thanh công cụ

| Nút | Làm gì |
|---|---|
| **Việc mới ▾** | Tạo nhanh một việc. Mũi tên: **Cột mốc mới**, **Cột mới** |
| **Bộ lọc** | Lọc điều kiện nhiều tầng — trạng thái, người phụ trách, người tạo, mọi trường tùy biến |
| **Sắp xếp** | Tay (kéo thả) · ngày bắt đầu · hạn chót · ngày tạo · sửa gần nhất · ngày hoàn thành · tiêu đề · **hoặc một trường tùy biến bất kỳ** |
| **Tùy chỉnh** | Bật/tắt và **đổi thứ tự** các trường hiện trên thẻ / cột bảng / lưới Gantt |
| **Tìm** (kính lúp) | Lọc theo từ khóa trong tên việc |

Thanh này **không hiện ở tab Hoạt động** — không nút nào trong đó có nghĩa với một cuốn
nhật ký.

⚠️ Các «lát cắt nhanh» kiểu *Việc của tôi / Đã hoàn thành* **đã bỏ**; mọi lát cắt đó nay
khai bằng Bộ lọc.

---

## 5. Panel chi tiết công việc

Trượt ra từ phải khi bấm vào một việc. Mọi ô **lưu ngay khi rời ô**, không có nút Lưu.

Thứ tự từ trên xuống:

1. **Thanh trên cùng** — trạng thái, nút bật/tắt **Cột mốc**, nút xóa, nút đóng.
2. **Tiêu đề** (sửa tại chỗ).
3. **Người phụ trách** — cụm avatar chồng nhau + `N người phụ trách`; một người thì hiện
   thẳng tên. Bấm cả cụm để mở danh sách chọn; gỡ ai thì bỏ tick trong đó.
4. **Thời gian** — ngày bắt đầu và hạn chót.
5. **Cột** — đổi cột ngay tại đây.
6. **Các trường tùy biến** của dự án (Tag, Độ ưu tiên, Kênh…) — mỗi trường một ô chọn.
7. **Mô tả**.
8. **Việc con** — thanh tiến độ `n/m` + danh sách tick + «Thêm việc con».
9. **Đính kèm** — «Thêm đính kèm», danh sách tệp có nút tải về / gỡ.
10. **Bình luận** — xem §6.

⚠️ Panel **không có** khối «Lịch sử thao tác». Nhật ký đọc ở tab **Hoạt động** (§3.4).

### Trường tùy biến

Mỗi dự án tự khai bộ trường riêng ở **Quản lý dự án → Thiết lập**. Sáu kiểu: chọn một ·
**chọn nhiều** · người · số · ngày · chữ.

**Độ ưu tiên** cũng chỉ là một trường tùy biến được nạp sẵn — bậc và màu do từng dự án
tự đặt, xóa được. Vì thế không có "thang ưu tiên chung của cả hệ".

---

## 6. Bình luận và đính kèm

### 6.1 Bình luận

Danh sách phẳng theo thời gian, ô soạn **ghim ở đáy panel**.

- **@nhắc tên**: gõ `@` hoặc bấm nút `@`. Người được nhắc **nhận chuông**; bấm chuông
  mở thẳng đúng việc đó.
- **Kèm tệp**: bấm kẹp giấy, bấm nút ảnh, **dán ảnh thẳng vào ô**, hoặc **kéo thả tệp**
  vào ô. Tối đa **5 tệp** mỗi bình luận. Ảnh hiện thẳng trong bình luận.
- Gửi bằng nút **Gửi** hoặc **Ctrl/Cmd + Enter**. Có tệp mà không gõ chữ vẫn gửi được.
- Tự xóa được bình luận của mình.
- Số bình luận hiện thành huy hiệu trên thẻ kanban và dòng danh sách.

⚠️ **Chưa có định dạng chữ** (đậm/nghiêng/danh sách) — ô soạn nhận chữ thuần + chip nhắc
tên.

### 6.2 Đính kèm ở cấp công việc

Tách hẳn với tệp kèm trong bình luận. Nhận tài liệu và ảnh, **tối đa 50MB/tệp**.

⚠️ **Tải tệp bắt buộc qua nút trong hệ thống.** Không có đường dẫn công khai — dán link
ra ngoài trình duyệt sẽ bị từ chối.

---

## 7. Ai thấy được gì — hai lớp

Quyền của phân hệ này **không giống các phân hệ chứng từ**. Có **hai lớp, phải qua cả hai**:

**Lớp 1 — vai trò hệ thống.** Cần khóa `work_task` trong ma trận phân quyền. Đây chỉ là
cửa vào phân hệ.

**Lớp 2 — tư cách thành viên.** Quyết định thật sự nằm ở đây: **bạn thấy dự án nào là do
bạn được mời vào dự án đó** (trực tiếp, hoặc kế thừa từ nhóm chứa nó).

⚠️ Không có chuyện "phạm vi phòng ban / pháp nhân" như ở chứng từ thu mua. Có
`work_task.read` toàn hệ vẫn **không** đọc được dự án mình không tham gia.

### Bốn vai trò trong một dự án

| Vai trò | Làm được gì |
|---|---|
| **Khách xem** | Đọc mọi thứ, kể cả bình luận. **Không** sửa, **không** gửi bình luận, **không** thêm/gỡ tệp |
| **Thành viên** | Tạo/sửa việc, kéo thả, tick xong, bình luận, đính kèm |
| **Quản trị** | Thêm mọi thứ trên, cộng: sửa cột, khai trường tùy biến, mời/gỡ thành viên |
| **Chủ sở hữu** | Thêm: đổi tên dự án, lưu trữ, chuyển quyền sở hữu |

Vai trò hiệu lực = **cao nhất** trong các nguồn. Được mời làm Khách xem ở dự án nhưng là
Quản trị ở nhóm chứa nó → hiệu lực là **Quản trị**.

Mỗi dự án luôn có **đúng một** chủ sở hữu. Chủ muốn rời thì phải **chuyển quyền trước**.

⚠️ Tài khoản **chưa gắn hồ sơ nhân sự** không tham gia dự án được — hệ thống báo rõ và
việc phải làm là nhờ quản trị gắn nhân sự cho tài khoản.

---

## 8. Thông báo

| Việc xảy ra | Ai nhận chuông |
|---|---|
| Được **@nhắc tên** trong bình luận | Người bị nhắc |
| Có **bình luận mới** | Người tạo việc + những ai đã bình luận (trừ người vừa bị nhắc, để khỏi kêu hai lần) |

Bấm chuông của bình luận sẽ mở đúng việc đó (qua `/project/tasks/{id}`, hệ tự tìm dự án
chứa việc rồi bung panel).

⚠️ **Được giao việc chưa bắn chuông** — thuộc đợt sau (F-01), cùng đợt với nhắc hạn và
tab «Việc cần làm».

---

## 9. Những thứ CHƯA có

Ghi ra để khỏi ai đi tìm:

| Chưa có | Ghi chú |
|---|---|
| Tab **Dashboard** thống kê dự án | Cố ý chưa render — không để tab chết trên thanh |
| **Nhắc hạn** đến hạn / quá hạn | Đợt sau (F-03) |
| Việc của dự án trong tab **Việc cần làm** | Đợt sau (F-02) |
| Màn **«Việc của tôi»** gom việc từ mọi dự án | Đợt sau (G-03) |
| **Thùng rác** khôi phục việc đã xóa | Đợt sau (B-09) — xóa hiện là xóa mềm, dữ liệu còn |
| **Chuyển việc sang dự án khác** | Đợt sau (B-10) |
| **Sửa** bình luận đã gửi | Xóa thì được |
| **Định dạng chữ** trong bình luận | Xem §6.1 |
| Gom nhóm kanban theo người / ưu tiên / hạn | Hiện chỉ gom theo cột |

---

## 10. Tra cứu nhanh

| Câu hỏi | Trả lời |
|---|---|
| Kéo việc vào cột «Xong» rồi mà báo cáo vẫn tính chưa xong? | Cột kanban ≠ trạng thái. Phải **tick ô tròn** — xem §2 |
| Không thấy dự án của đồng nghiệp? | Phải được **mời vào dự án** hoặc vào nhóm chứa nó — §7 |
| Kéo thả không ăn? | Đang sắp xếp khác «Tay (kéo thả)» — đổi lại ở nút Sắp xếp |
| Việc con đâu mất trên kanban? | Việc con **chỉ** sống trong panel chi tiết — §1 |
| Xem lịch sử một việc ở đâu? | Tab **Hoạt động** của dự án. Chưa lọc được theo từng việc — §3.4 |
| Cột mốc khác việc thường chỗ nào? | Chỉ có **một** ngày (hạn), Gantt vẽ hình thoi — §1 |
| Bấm nút xóa dự án mà nó vẫn còn? | «Xóa» dự án/nhóm là **lưu trữ**, không xóa hẳn |
