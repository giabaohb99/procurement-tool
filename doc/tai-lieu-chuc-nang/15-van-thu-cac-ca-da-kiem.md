# Văn thư — Các ca đã kiểm

Bản kê **hành vi nào của phân hệ Văn thư đang được bài kiểm tự động khoá lại**.

Tài liệu chức năng ([14-van-thu-van-ban.md](14-van-thu-van-ban.md)) trả lời *"hệ làm
gì"*. Tài liệu này trả lời câu khác: *"cái gì đã được chứng minh là đúng, và bằng
bài kiểm nào"* — thứ cần khi sắp sửa một chỗ nhạy cảm và muốn biết mình đang được
lưới nào đỡ.

> **Cách đọc.** Mỗi mục dưới đây là một **cam kết hành vi**, kèm tên tệp bài kiểm
> giữ nó. Muốn xem chi tiết thì mở `test/backend/<tệp>.py` — tên hàm và phần mô tả
> ở đầu tệp viết bằng tiếng Việt, đọc thẳng được.

> ⚠️ **Con số trong tài liệu này cũ rất nhanh.** Đếm lại bằng:
> ```bash
> docker compose exec -T api python -m pytest test/backend -q
> ```

**Tính tới 27/08/2026: 624 ca kiểm / 55 tệp** riêng cho phân hệ Văn thư.

---

## 0. Bản đồ nhanh

| Nhóm | Ca | Câu hỏi nó trả lời |
|---|---|---|
| [1. Phê duyệt](#1-phê-duyệt) | ~130 | Phiếu đi qua ai, ai ký được, ký hỏng thì sao |
| [2. Phân quyền & phạm vi](#2-phân-quyền--phạm-vi) | ~120 | Ai thấy, ai đọc, ai sửa, ai xoá |
| [3. Bảo mật](#3-bảo-mật) | ~40 | Chống XSS, rò tệp, chiếm chữ ký, nhật ký truy cập |
| [4. Ban hành & pháp nhân con](#4-ban-hành--pháp-nhân-con) | ~90 | Cấp số, khoá bản, clone xuống công ty con |
| [5. Hộp thư gửi](#5-hộp-thư-gửi) | ~43 | Gửi thông báo danh nghĩa địa chỉ khác |
| [6. Vòng đời & phiên bản](#6-vòng-đời--phiên-bản) | ~60 | Nháp → duyệt → hiệu lực → bãi bỏ |
| [7. Stress test & hiệu năng](#7-stress-test--hiệu-năng) | 22 | Chạy trọn một lượt như người thật, và văn bản lớn |
| [8. Chỗ CHƯA có lưới](#8-chỗ-chưa-có-lưới) | — | Rủi ro đã biết, chưa được bài kiểm nào giữ |

---

## 1. Phê duyệt

### 1.1 Nối vào bộ máy duyệt dùng chung
`test_van_ban_qua_bo_may_duyet.py` · 13 ca

Ba điều kiện của cam kết *"không ảnh hưởng thứ đang chạy"*, theo đúng thứ tự:

- **Cờ TẮT thì không có gì đổi** — gửi duyệt và duyệt chạy y như trước.
- **Cờ BẬT mà chưa khai luồng cũng không đổi gì** — không có khe nào để văn bản
  rơi vào khoảng không giữa hai bộ máy.
- Cờ BẬT và có luồng → phiếu chạy nhiều bước, và **duyệt xong là văn bản được ban
  hành THẬT** (cấp số, khoá phiên bản), không chỉ đổi một con số trạng thái.

Kèm: bản gốc và bản clone mở **hai luồng riêng theo pháp nhân**; trả lại / từ chối
qua bộ máy đều **ghi nhật ký đúng người bấm** (không phải người nộp).

### 1.2 Chọn luồng, chọn người duyệt
`test_bo_may_phe_duyet.py` · 21 ca

- Luồng khai **đúng pháp nhân thắng luồng dùng chung**, bất kể độ ưu tiên thấp hơn.
- Trùng người thì tự bỏ qua và **ghi rõ lý do**; chỉ bỏ bước liền trước, không bỏ bước xa.
- Người duyệt nghỉ việc → chuyển người dự phòng. **Không ai duyệt và không có dự
  phòng thì phiếu KẸT, chứ không tự duyệt qua** — đây là chỗ cố ý không có tuỳ chọn
  "tự động duyệt".
- **Người nộp không tự duyệt phiếu của mình.**
- Sửa luồng không làm hỏng phiếu đang chạy; phiếu mới đi theo luồng đã sửa.
- Rẽ nhánh: không khớp nhánh nào thì vào nhánh mặc định; **thiếu nhánh mặc định thì
  phiếu KẾT chứ không biến mất**.

### 1.3 Hành động trên phiếu
`test_bo_may_phe_duyet_hanh_dong.py` · 24 ca

- **Từ chối / trả lại / rút lại đều bắt ghi lý do**; lý do quá dài bị chặn ở cửa
  (`test_bo_may_duyet_chiu_tranh_chap.py` đo trần khớp bề rộng cột).
- Trả về **một bước phía trước** thì các bước sau phải ký lại; **không trả về bước
  phía sau**.
- Rút lại chỉ khi **chưa ai duyệt**; đã có chữ ký thì phải dùng Trả lại / Từ chối.
- Bốn cách gom nhiều người trong một bước: **một người là đủ · tất cả · lần lượt ·
  đủ tỷ lệ**. Bước *nhận bản sao* không chặn luồng.
- Uỷ quyền: hết hạn thì không bấm thay được · khác loại chứng từ thì không dùng
  được · **cấm uỷ quyền dây chuyền** · không uỷ quyền cho chính mình · ngày bắt đầu
  phải trước ngày kết thúc.

### 1.4 Các ca hiểm
`test_bo_may_duyet_ca_hiem.py` · 15 ca — *"thứ không ai làm nhưng vẫn xảy ra"*

- Trả về một bước **không làm phình mẫu số của biểu quyết theo tỷ lệ**.
- Người duyệt **không tự đặt bối cảnh** để chọn người duyệt bước kế tiếp.
- **Phiếu không ghi người trình thì không ai rút được** (cột để trống không được
  biến thành "ai cũng rút").
- Một người giữ hai việc trong cùng một bước thì **phải bấm đủ hai lần**.
- Bấm duyệt lần hai khi phiếu đã xong → báo *đã kết thúc*, không âm thầm chạy lại.

### 1.5 Chịu tải & tranh chấp
`test_bo_may_duyet_chiu_tranh_chap.py` · 14 ca — bốn lỗi bắt được ở vòng kiểm 24/08/2026

- **Không thể có hai phiếu đang chạy cho một chứng từ**; phiếu KẸT vẫn tính là đang mở.
- Kẹt khoá DB → **409, không phải 500**, và **TUYỆT ĐỐI không chạy lại** (chạy lại
  là ký hai lần).
- Chiếm việc lần hai bị chặn; không chiếm được việc đã huỷ.

### 1.6 Không có đường tắt
`test_van_ban_dang_duyet_khong_di_tat.py` · 8 ca · `test_khoa_sua_khi_dang_duyet.py` · 7 ca

- Đang ở chặng 1 thì **không ban hành thẳng được** bằng nút cũ.
- Gửi duyệt rồi thì **không sửa được nội dung, lề trang, tiêu đề, mức mật** (409).
- Bị trả lại → sửa tiếp được. **Bị từ chối → khoá hẳn**, muốn làm lại thì *Sao chép*.
- Duyệt xong mà không ban hành được thì **ghi lý do vào phiên**, không im lặng.

### 1.7 Ba nhịp kết thúc phiếu
`test_van_ban_tra_ve_va_tu_choi.py` · 14 ca

Ba nhịp **khác nhau** và không được gộp:

| Nhịp | Trạng thái văn bản | Còn đường đi tiếp |
|---|---|---|
| Trả về | *Trả về* | có — sửa rồi gửi duyệt lại |
| Từ chối | *Đã từ chối* | không — phải *Sao chép* |
| Rút phiếu | *Nháp* | có — không ai trả gì cho ai |

Từ **bản thứ hai trở đi**, cả ba nhịp **không đụng trạng thái văn bản** — bản 1.0
vẫn có hiệu lực suốt lúc bản 2.0 chờ duyệt. Xoá văn bản thì **dọn luôn phiếu duyệt
và quan hệ**.

---

## 2. Phân quyền & phạm vi

### 2.1 Quyền trên từng văn bản
`test_document_access.py` · 24 ca

- **Không đọc được thì báo 404, không phải 403** — 403 tự nó đã tiết lộ "có văn bản đó".
- Chia đích danh: cho người ngoài phạm vi · cho cả phòng ban · theo vai trò · chia
  quyền sửa/xoá riêng.
- **Dòng CẤM thắng tuyệt đối** — thắng cả dòng cho phép, thắng cả phạm vi vai trò,
  thắng cả quyền theo sổ.
- Có hạn: quá hạn tự mất quyền · chưa tới ngày bắt đầu thì chưa có quyền · hạn ngược
  đầu bị chặn.
- Thu hồi là **đánh dấu, không xoá dòng** (giữ dấu vết); thu hồi hai lần bị chặn.
- Đọc được bản clone thì **xem lại được bản gốc** — nhưng dòng cấm đích danh ở bản
  gốc vẫn thắng.

### 2.2 Phạm vi áp dụng
`test_pham_vi_ap_dung.py` · 23 ca · `test_ban_hanh_ai_thay_van_ban.py` · 15 ca

Bốn luật, và **bốn đầu ra phải cho cùng một tập người** (thuộc phạm vi · danh sách
"áp dụng cho tôi" · mở được chi tiết · nhận chuông + email). Lệch nhau là ra đúng
hai lỗi tệ nhất: nhận mail rồi bấm vào thì 404, hoặc người bị loại trừ vẫn mở được.

- Chưa khai dòng nào → áp cho **cả pháp nhân ban hành**.
- Khai một dòng là **tắt mặc định** đó đi.
- **Loại trừ thắng bao gồm** cùng chiều; loại trừ cá nhân thắng bao gồm cả pháp nhân.
- *Gồm đơn vị con* chỉ có nghĩa với chiều pháp nhân; **Tập đoàn không kèm cờ đó thì
  không lan xuống công ty con**.
- Người bị loại trừ **gõ thẳng URL vẫn không vào được**.

> ⚠️ `test_chi_khai_loai_tru_thi_khong_ai_thay` ghi lại một **cái bẫy CÓ THẬT đang
> tồn tại**, không phải hành vi mong muốn — đọc ghi chú tại chỗ.

### 2.3 Phạm vi dữ liệu ở tầng hạ tầng
`test_pham_vi_khai_du_b07.py` · 14 ca

- **Mọi entity trong `ENTITIES` phải được khai trong `SCOPE_FIELDS`** — hiện **44/44**.
  Thêm entity mà quên khai là suite đỏ ngay.
- Thiếu khai, hoặc phạm vi không dựng nổi điều kiện → **chặn hết (`false()`)**, không
  còn rơi về "thấy tất".
- `get_scoped` **chặn gõ thẳng id vào URL** — bộ lọc danh sách không bị đi vòng.
- Không grant nào thì không thấy gì.

### 2.4 Văn bản cá nhân (đơn nghỉ phép)
`test_van_ban_ca_nhan_ai_thay_duoc.py` · 15 ca

Loại bật `is_personal` thì **thoát khỏi phạm vi vai trò**:

- Đồng nghiệp cùng phòng **không thấy** đơn nghỉ phép, nhưng **vẫn thấy văn bản
  thường** cùng pháp nhân.
- **Ô tìm kiếm không được lộ tiêu đề đơn.**
- Thành viên sổ và phạm vi áp dụng **không mở được** đơn.
- Đổi loại sang cá nhân thì **lập tức bị giấu**.
- Lập hộ thì cả người lập lẫn người nghỉ đều thấy.
- **Danh sách và chi tiết không bao giờ lệch nhau** — hai đường tính quyền khác nhau
  nhưng phải ra cùng kết quả.

### 2.5 Người duyệt đọc được thứ mình ký
`test_nguoi_duyet_doc_duoc_van_ban.py` · 8 ca

Người duyệt thường **không có vai trò nào** trên phân hệ Văn bản. Thiếu ngoại lệ này
thì họ bấm từ «Việc của tôi» sang là gặp 404 và phải **ký mù**.

Ngoại lệ **chỉ mở quyền ĐỌC** — sửa, xoá, ban hành vẫn theo phân quyền như cũ.

---

## 3. Bảo mật

### 3.1 Chống XSS lưu trữ
`test_van_ban_chong_xss.py` · 4 ca

Nội dung văn bản là HTML người dùng gõ. Lọc **hai lớp**, cố ý không chỉ một:

- **Cửa ghi** (`content_sanitize`) — dữ liệu nằm trong DB đã sạch.
- **Cửa đọc** (`shared/utils/sanitize-html`) — lọc lại lúc hiện ra, cho cả dữ liệu
  cũ đã nằm sẵn trong DB từ trước bản vá.

Kèm chốt ngược: **giữ nguyên định dạng lành** (không lọc quá tay), và
`content_html = None` **không xoá trắng** nội dung đang có.

### 3.2 Tệp đính kèm
`test_dinh_kem_van_ban_rieng_tu.py` · 6 ca · `test_pham_vi_dinh_kem_b08.py` · 22 ca

- Đính kèm văn bản **không trả link công khai** — chỉ trả đường tải có kiểm quyền.
  Đính kèm thu mua giữ link như cũ (không đổi thứ đang chạy).
- **Mã băm toàn vẹn** vẫn trả về cả khi giấu link; băm đúng nội dung tệp; tệp rỗng
  vẫn có mã băm.
- Đính kèm **lọc theo phạm vi dữ liệu** của chứng từ cha, không chỉ theo quyền vai trò.
- Ngoài phạm vi → **404 chứ không 403**.

> ⚠️ **Nửa việc còn lại, đã ghi trong mã**: bản thân object trên kho lưu trữ vẫn đọc
> được nếu ai đó đã có URL từ trước. Bịt hẳn thì phải chuyển bucket sang private —
> việc hạ tầng, chưa làm. **Cho tới lúc đó: không đưa văn bản Tuyệt mật thật vào hệ.**

### 3.3 Hạn xem và nhật ký truy cập
`test_han_xem_tep_dinh_kem.py` · 8 ca · `test_nhat_ky_mo_tep_van_ban.py` · 6 ca

- Hạn xem: đúng ngày hạn **vẫn xem được**, quá một ngày là hết, hết hạn thì **403
  kèm ngày**.
- Mỗi lượt mở/tải ghi **một dòng trên chính văn bản**.
- Cảnh báo bất thường theo **ngưỡng × cửa sổ thời gian**; ngưỡng `0` = tắt cảnh báo
  nhưng **vẫn ghi nhật ký**. Dấu "đã báo" treo theo **NGƯỜI**, không theo văn bản.

### 3.4 Chiếm chữ ký của người khác
`test_bo_may_duyet_chiem_quyen.py` · 17 ca

Bộ máy hỏi *"anh có quyền vai trò không"* nhưng không hỏi *"anh có tư cách gì với
CON NGƯỜI này"*. Ai có sẵn `approval_flow.write/create` — thứ hay cấp cho trợ lý,
admin phân hệ — đều ký thay giám đốc được qua **ba đường**:

1. **Uỷ quyền** — lập tờ uỷ quyền TỪ giám đốc SANG mình. Nhật ký ghi *"B duyệt thay
   A theo uỷ quyền số 12"*, nhìn hoàn toàn hợp lệ.
2. **Chuyển việc** — đổi người xử lý sang chính mình rồi tự ký.
3. **Bàn giao hàng loạt** — một cú gọi chuyển sạch việc đang chờ của giám đốc sang
   mình. **Nặng nhất**: uỷ quyền còn để lại chữ "ký thay", còn bàn giao thì việc đổi
   hẳn chủ — bản in dấu vết không còn chỗ nào nói người ký không phải người được giao.

Cả ba đã bịt, và **mỗi ca bịt cửa đều kèm một cặp đối chứng** để không làm chết thao
tác thật (trợ lý lập uỷ quyền hộ sếp, hành chính bàn giao khi có người nghỉ).

---

## 4. Ban hành & pháp nhân con

### 4.1 Ban hành
`test_ban_hanh_van_ban.py` · 10 ca · `test_document_revoke_keeps_number.py` · 4 ca

- Màn xem trước nói đủ bốn thứ sắp xảy ra, **tách CHẶN khỏi CẢNH BÁO**.
- Loại khai *"phải kèm Quyết định"* mà thiếu thì **chặn ở tầng dịch vụ**, không chỉ
  ẩn nút.
- **Bãi bỏ không trả số về cho văn bản sau dùng** — số đã vào sổ là vĩnh viễn.

### 4.2 Clone xuống pháp nhân con
`test_clone_phap_nhan_con.py` · 17 ca · `test_clone_tu_sinh_khi_ban_hanh.py` · 15 ca ·
`test_ke_hoach_clone.py` · 10 ca · `test_cay_tai_lieu_ban_clone.py` · 6 ca

- Ban hành xong thì **mỗi pháp nhân trong phạm vi có ngay một bản nháp**, chép đúng
  nội dung gốc.
- **Không clone** về: chính pháp nhân ban hành · dòng loại trừ · dòng phòng ban.
- Bản gốc lên bản 2.0 **không đẻ thêm bản thứ hai** cho cùng pháp nhân; bản con bị
  đánh dấu *cần rà lại* **và người phụ trách được báo**.
- Bản clone mang **số hiệu của pháp nhân con**, kể cả loại cấp số lúc nháp.
- Cột theo dõi ở bản gốc đổi theo vòng đời thật của bản con (Đã gửi → Đang duyệt →
  Đã ban hành / Từ chối áp dụng); rà xong thì **hết lệch bản**, không kẹt vĩnh viễn.

### 4.3 Quan hệ giữa văn bản
`test_document_quan_he_cha_con.py` · 33 ca · `test_ban_trich_noi_bo.py` · 17 ca

- Tác động dây chuyền lúc ban hành: *thay thế* → cái cũ sang **Đã thay thế**; *bãi
  bỏ* → sang **Bãi bỏ**; *sửa đổi* **KHÔNG đụng trạng thái** (phần không bị sửa vẫn
  còn hiệu lực — và chính vì thế cái nhãn cảnh báo là bắt buộc).
- Chỉ chạy khi văn bản mới **thật sự có hiệu lực** — ban hành hôm nay mà áp dụng
  tháng sau thì văn bản cũ còn nguyên hiệu lực.
- Bản trích **không cấp số hiệu riêng** (C19) — gọi theo số bản gốc.

---

## 5. Hộp thư gửi
`test_chon_hop_thu_khi_ban_hanh.py` · 21 ca · `test_api_hop_thu_gui.py` · 11 ca ·
`test_stress_gui_thu_theo_hop_thu.py` · 11 ca

Chi tiết nghiệp vụ ở [14-van-thu-van-ban.md §14.3](14-van-thu-van-ban.md). Phần được
bài kiểm khoá lại:

- **Loại giữ mặc định thì duyệt xong ban hành luôn** — điều kiện số một của cam kết
  không đổi thứ đang chạy.
- Loại bật cờ thì dừng ở *Chờ ban hành*: **chưa cấp số, khoá sửa, không gửi duyệt
  chồng được**, và **chỉ người soạn thảo** bấm được.
- Mật khẩu ứng dụng **không bao giờ trả ngược qua API**; **sửa tên không làm mất mật
  khẩu** (ô trống = giữ nguyên); xoá phải là thao tác riêng.
- Đường gửi SMTP: **đăng nhập bằng chính hộp thư**, không phải tài khoản hệ thống —
  chỉ đổi tiêu đề `From` thì Gmail ghi đè và **hỏng im lặng**.
- Ba nhánh lùi an toàn: hộp thư **bị xoá · ngừng dùng · mất mật khẩu** → gửi bằng
  địa chỉ hệ thống, **không để thư nằm chết trong hàng đợi**.
- Công tắc `email_enabled` tắt thì hộp thư riêng **không đi vòng qua** hàng rào vận hành.

---

## 6. Vòng đời & phiên bản

| Cam kết | Tệp |
|---|---|
| Bất biến hoá bản đã duyệt; **một bản đang mở** tại một thời điểm | `test_document_version.py` (11) |
| Chia sổ văn bản — người được cho xem phải **thấy quyển sổ đó** | `test_chia_so_van_ban.py` (14) + `_bien.py` (13) |
| Quy tắc đánh số, ba lớp chống trùng số | `test_document_numbering_rule.py` (4) |
| Chữ ký trên văn bản (J02, J03) | `test_chu_ky_van_ban.py` (9) |
| Lề trang theo Nghị định 30/2020 điều 8 | `test_le_trang_van_ban.py` (8) |
| Thư viện mẫu — chép nội dung, **không giữ liên kết sống** | `test_document_template.py` (4) |
| Sao chép văn bản ra bản nháp độc lập | `test_sao_chep_van_ban.py` (3) |
| Mức mật / độ khẩn là **danh mục dưới DB**, không phải hằng số trong mã | `test_danh_muc_muc_mat.py` (22) |
| Nhập tệp (docx/pdf/md) + ba lớp chặn kích thước | `test_document_import.py` (6) |
| Xuất Excel danh sách | `test_xuat_excel_van_ban.py` (9) |
| Ma trận ưu tiên + bộ lọc trang Tổng quan | `test_document_dashboard_matran.py` (8) |
| Thư báo «có việc chờ bạn duyệt» | `test_thu_bao_viec_can_duyet.py` (5) |
| Email ban hành dùng đúng phạm vi, dẫn vào màn chỉ đọc | `test_email_khi_ban_hanh_van_ban.py` (6) |
| Thứ tự đăng ký route dưới `/api/documents` | `test_thu_tu_route_van_ban.py` (2) |

---

## 7. Stress test & hiệu năng

### 7.1 Chuỗi đầu–cuối
`test_stress_luong_van_ban_dau_cuoi.py` · 11 ca

Dựng một tổ chức thật — Tập đoàn + hai pháp nhân con, mỗi nơi một luồng ký riêng,
**tài khoản gắn hồ sơ nhân sự** — rồi chạy trọn:

```
soạn → gửi duyệt → ký bước 1 → ký bước 2 → BAN HÀNH
     → hai pháp nhân con tự nhận bản nháp riêng
     → mỗi nơi gửi duyệt qua LUỒNG CỦA CHÍNH NƠI ĐÓ → ký → ban hành
```

Mỗi nhịp kiểm **lại toàn bộ** trạng thái, không chỉ cái vừa đổi. Kèm 10 nhánh gãy:
ban hành thẳng khi phiếu đang chạy · sửa lúc đang duyệt · clone thiếu luồng riêng
(chặn **trước** khi đổi trạng thái) · pháp nhân con từ chối · trả lại rồi gửi lại ·
rút phiếu · bản gốc lên 2.0 · bấm Gửi duyệt hai lần · ngày hiệu lực tương lai ·
quyền đọc chéo pháp nhân.

> Vì sao cần tệp này: các bài kiểm khác **mỗi bài soi một mảnh**, mà chỗ nối giữa các
> mảnh mới là chỗ lọt lỗi.

### 7.2 Số đo hiệu năng (27/08/2026)

Đo trên **bản production** (bản dev đắt gấp 2–4 lần vì `jsxDEV`/`createTask` của
React development — **đừng lấy số đo trên `localhost:8083` làm chuẩn**).

| Thao tác | Văn bản 100 trang (900 node) |
|---|---|
| Gõ phím | 4,8 ms · **0 tác vụ dài** |
| Mỗi lượt sửa xong | **0 ms** |
| Từ danh sách vào chi tiết | **292 ms** → **222 ms** sau khi nạp trước (CR sau) |
| Nhập tệp 100 trang | 132 ms |
| Nhập tệp 800 trang (mức nặng nhất còn lọt) | 782 ms |

Backend chuyển đổi tệp Word **không phải nút thắt**: 100 trang = 15 ms, 800 trang =
100 ms; 1 200 trang bị ba lớp chặn từ chối.

### 7.3 ⚠️ LỖI ĐÃ BIẾT, CHƯA SỬA — phân trang chạy loạn

**Bất kỳ khối nào cao hơn vùng in một trang đều đẩy `PaginationPlus` vào vòng lặp vô
hạn.** Nó chèn ngắt trang để nhét vừa một khối không bao giờ nhét vừa được.

Ngưỡng đo được (vùng in một trang ≈ **971 px**):

| Bảng | Chiều cao | Kết quả |
|---|---|---|
| 26 hàng | 897 px | ổn định, 2 trang |
| **30 hàng** | **1 035 px** | **chạy loạn** |

Ca tối giản: một tài liệu **3 KB, đúng 3 node**, chỉ chứa **một bảng 30 hàng** →
1 249 trang A4, 1 195 ngắt trang **và vẫn tăng +108 mỗi 2,5 giây**, 338 MB bộ nhớ.
Chỉ dừng khi chạm trần bố cục 2²⁴ px của Chrome.

**Mức độ phơi nhiễm cao**: một bảng 30 dòng là văn bản hoàn toàn bình thường (bảng
giá, danh sách nhân sự, phụ lục hợp đồng). **Không lớp chặn nào bắt được** vì tài
liệu chỉ 3 KB.

Dữ liệu **an toàn** — đã kiểm: rác phân trang không bị ghi ngược vào CSDL.

> **Chưa có bài kiểm tự động nào giữ chỗ này** — nó là lỗi trình duyệt/bố cục, không
> tái hiện được bằng `pytest`. Muốn khoá lại thì phải dựng bài kiểm chạy trên trình
> duyệt thật.

### 7.4 Hướng đã thử và **loại bỏ**

Ghi lại để người sau không thử lại:

| Hướng | Kết quả đo |
|---|---|
| **Web Worker** cho việc chuỗi hoá/lưu | **Không giúp.** `getHTML()` 4 ms · transaction 5–17 ms · layout cả tài liệu 8,2 ms · chuỗi hoá DOM 1,3 ms. Không có khối tính toán nào đáng đẩy sang worker; phần đắt còn lại (dựng cây React, ProseMirror cập nhật DOM) worker **không đụng được** vì không có DOM. |
| **`content-visibility: auto`** (ảo hoá của trình duyệt) | **Hỏng.** Chiều cao 67 972 → 90 848 px; sau khi cuộn hết còn tệ hơn: **+53 619 px (+79%)**, không hội tụ. Pagination đo DOM → số đo sai → chèn sai → vòng lặp phản hồi. |
| **Ảo hoá cột mục lục** | **Không đáng.** A/B cùng 1 600 node: tài liệu **800 mục lục lại NHANH HƠN** (224 ms) tài liệu **5 mục lục** (306 ms). Mục lục không phải nút thắt, và các mục đều cao đúng 36 px nên cũng không phải "variable height". |

---

## 8. Chỗ CHƯA có lưới

Nói thẳng ra để không ai tưởng đã được che:

- **Phân trang chạy loạn** (§7.3) — biết rõ, chưa sửa, chưa có bài kiểm.
- **Giao diện `frontend-v2/`** — hầu hết bài kiểm ở đây là **backend**. Phía giao
  diện chỉ có vài tệp `.test.tsx` lẻ; các lỗi bố cục (mục lục tràn khung, chữ bị
  cắt) đều **phát hiện bằng đo tay trên trình duyệt**, không có bài kiểm giữ.
- **Kho lưu trữ tệp vẫn là bucket public** (§3.2) — bài kiểm chỉ khoá được phần API
  không phát link, không khoá được chính object.
- `line_approve` trên hai bảng dòng khảo sát và `STATE_*` trong `survey_request/
  line_state.py` **vẫn là tiếng Việt** — ngoài phạm vi đợt chuyển mã, xem `CLAUDE.md`.

---

## Chạy bài kiểm

```bash
# toàn bộ backend
docker compose exec -T api python -m pytest test/backend -q

# riêng một nhóm
docker compose exec -T api python -m pytest test/backend/test_stress_luong_van_ban_dau_cuoi.py -q

# giao diện
docker compose exec erp npm run check      # typecheck + lint + test
```

---

## Liên quan

- [14-van-thu-van-ban.md](14-van-thu-van-ban.md) — tài liệu chức năng phân hệ Văn thư
- [`doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`](../phan-quyen/Thiet_Ke_Phan_Quyen.md) — thiết kế hai trục phân quyền
- [`doc/tai-lieu-ky-thuat/change-log.md`](../tai-lieu-ky-thuat/change-log.md) — CR-182…CR-188 là các đợt gần nhất chạm vào phân hệ này
