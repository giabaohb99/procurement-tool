# LỘ TRÌNH: CỦNG CỐ HẠ TẦNG, RỒI HRM

| | |
|---|---|
| Bản | **2.2 — 12/08/2026** (rà lại tầng middleware và tầng dùng chung, thêm **H17** và **H18** từ bốn lỗ hổng tìm ra khi đọc lại mã nguồn) |
| Trả lời câu gì | Nền hiện tại thiếu gì để gánh nhiều phân hệ, và làm HRM theo thứ tự nào |
| Căn cứ | Đọc trực tiếp mã nguồn `procurement-tool` ngày 11 và 12/08/2026, số liệu là đếm được. Bản 2.1 đã đếm lại toàn bộ, chỗ nào lệch so với bản 2.0 đều ghi rõ |
| Ai đọc | Đội phần mềm đọc hết. Người chủ trì đọc mục 1, 4, 6 |
| Trạng thái | **Đề xuất — chưa được duyệt** |
| Liên quan | [`01` Ngắn hạn](./01-ngan-han-2026.md) · [`02` Dài hạn](./02-dai-han.md) · [`04` Danh mục chờ](./04-danh-muc-cho.md) · **[`08` Danh sách task củng cố](./08-danh-sach-task-cung-co.md)** · [`tham-khao-hrm/`](./tham-khao-hrm/README.md) |
| Bắt tay vào làm thì mở tệp nào | **[`08`](./08-danh-sach-task-cung-co.md)** — tệp này nói *cần gì và vì sao*, `08` nói *làm gì, thứ tự nào, căn cứ vào đâu nói là xong* |

**Ba câu tóm tắt cả tài liệu:**

1. Nền hiện tại **không phải viết lại**. Chia module, phân quyền hành động, tác vụ nền, nhật ký thao tác đều đủ tốt để xây tiếp.
2. Thiếu tập trung ở năm chỗ: **phạm vi dữ liệu chưa chặn khi quên khai · không có gì tích hợp ra ngoài · chưa sẵn sàng đa pháp nhân · không nhìn thấy hệ thống khi hỏng · cái gì lặp thì chưa gom.**
3. Hạng mục lớn nhất và đáng giá nhất là **bộ máy duyệt dùng chung**, và nó **không phải việc của HRM** — phải làm trước.

> **Sửa quan trọng ở bản 2.1.** Bản 2.0 xếp lỗ hổng phạm vi dữ liệu (R5) vào loại rủi ro *tiềm ẩn*, "hôm nay chưa vỡ". Đếm lại thì **nó đang hở thật, ngay trên `tab_employee`** — đúng bảng mà HRM sắp mở rộng. Chi tiết ở cuối mục 1 và ở H4. Đây là việc phải làm trước mọi việc khác trong tài liệu này.

> **Thêm ở bản 2.2.** Rà lại tầng middleware và tầng dùng chung theo yêu cầu ngày 12/08/2026, ra thêm **bốn lỗ hổng đang hở** mà bản 2.1 chưa có: cấu hình loại trừ phòng ban trên dữ liệu nhân sự **không có hiệu lực** (vào H4a), tệp đính kèm **tải được không cần đăng nhập** (thành **H17**), nhật ký thao tác **đọc tự do** (thành **H18**), và bộ sinh router chung **chưa có phạm vi** nên không được kế thừa trước khi vá (vào H3). Cộng một cấu hình chết ở tầng giới hạn tần suất (vào H5). Danh sách task thực thi ở [`08`](./08-danh-sach-task-cung-co.md).

**Không có ước lượng người-ngày trong tài liệu này.** Có thứ tự, điều kiện vào ra, và cỡ tương đối. Ước lượng sớm sẽ bị nhớ như cam kết.

---

## 1. Bảy ràng buộc bắt buộc

Không kiểm được tự động thì ràng buộc chỉ là lời khuyên, mà lời khuyên thì sáu tháng nữa không ai nhớ. Nên mỗi ràng buộc phải có cột cuối.

| # | Nội dung | Hiện trạng đo được | Kiểm bằng gì |
|---|---|---|---|
| **R1** | Tên bảng, cột, biến, hàm, endpoint bằng **tiếng Anh**. Cấm tiếng Việt không dấu (`phan_loai`, `so_luong`). Tiếng Việt chỉ ở nhãn giao diện, nội dung dữ liệu, chú thích | **Đã là quy ước** ở [`NAMING_CONVENTIONS.md`](../../procurement-tool/doc/chung/NAMING_CONVENTIONS.md) và mã nguồn đang tuân thủ — quét 31 tệp model không thấy vi phạm | Bài kiểm duyệt metadata SQLAlchemy, so tên bảng/cột với danh sách từ tiếng Việt hay gặp. Chạy trong CI |
| **R2** | Cột mang nghĩa trạng thái, loại, mức, cấp lưu **giá trị thuộc một bộ mã cố định khai trong mã nguồn**, có **validator ở `schema.py` chặn giá trị ngoài bộ**. Cấm chữ tự do, cấm tiếng Việt có dấu. **Mặc định cho MỌI thứ làm mới: số** — `SMALLINT` + `IntEnum`, khuôn `import_tool` / `document/` / `approval/` *(**QĐ-11**, 22/08/2026)*. **Ngoại lệ ĐÓNG:** đúng 12 cột Thu mua ở [`15` §2.2](./15-do-be-tong-nen-v2.md) dùng **mã chuỗi tiếng Anh** *(khuôn CR-118)*, vì `status` cấp phiếu của tám chứng từ Thu mua đã là mã chuỗi — **QĐ-9**, lý do ở [`15` §2.4](./15-do-be-tong-nen-v2.md). Danh sách đó không mở rộng | **30 cột** đang lưu chuỗi, trong đó **12 cột lưu tiếng Việt có dấu** *(`15` §2.2 đếm lại ngày 22/08; bản cũ ghi 11, sót `tab_po_item.status_before_pause`)*. Khoảng **350 chỗ** so chuỗi. Khung khai chung đã dựng ở `app/core/status_catalog.py` **(B-01)** | Cột tên khớp `status/type/kind/level/state` mà **giá trị không thuộc bộ mã đã đăng ký** thì hỏng bài kiểm. **Không** kiểm theo kiểu dữ liệu — hai khuôn dùng hai kiểu khác nhau. Trừ danh sách miễn trừ có ghi lý do |
| **R3** | Enum khai **một chỗ** ở máy chủ, **một chỗ** ở giao diện. Mỗi bảng đúng một model. Đổi cấu trúc đi qua migration | 9 tệp giao diện cùng chép lại danh sách trạng thái | Sinh tệp enum của giao diện từ máy chủ, CI chạy lại và so — khác một ký tự là hỏng. Xem H2 |
| **R4** | Bảng nghiệp vụ có `company_id` **ngay từ migration đầu tiên**, kể cả khi bản 1 chạy một pháp nhân | **15 trên 57 bảng** có. *(Bản 2.0 ghi 14/31 — đó là đếm theo **tệp model**, mà một tệp thường khai nhiều bảng. Phân quyền chạy theo bảng, nên phải đếm theo bảng: thiếu **42 bảng**, không phải 17)* | Bài kiểm có danh sách bảng nghiệp vụ; thiếu cột là hỏng |
| **R5** | Thiếu khai phạm vi dữ liệu thì **báo lỗi**, không lặng lẽ trả hết | Khai **9 trên 28** loại. Thiếu thì `_role_scope_cond` trả "không giới hạn". **Và ngay cả loại đã khai vẫn hở nếu endpoint quên gọi `apply_scope`** — xem khung dưới bảng | Đổi mặc định thành chặn, cộng bài kiểm duyệt đủ 28 loại **và** bài kiểm mọi endpoint đọc đều đi qua phạm vi |
| **R6** | Một mã nguồn, một cơ sở dữ liệu, một cơ chế đăng nhập, một cơ chế phân quyền. Giao diện tách theo phân hệ thì được | Đang đúng — Trung tâm HDSD và Project-M là giao diện riêng nhưng chung máy chủ, chung tài khoản | Quy tắc quản trị, không kiểm tự động. Đưa vào điều kiện duyệt khi mở phân hệ mới |
| **R7** | Dữ liệu đang chạy: **chỉ thêm, không sửa**. Chuẩn hóa theo kiểu thêm cột, chạy song song, rồi mới bỏ cột cũ | Đang đúng | Rà tay khi duyệt migration |

**Vì sao R2 gắt:** chuỗi tiếng Việt làm giá trị trạng thái gây bốn lỗi cùng lúc — `"Chờ TT"` và `"Chờ TT "` là hai trạng thái khác nhau với cơ sở dữ liệu nhưng nhìn màn hình y hệt; đổi nhãn hiển thị là phải sửa dữ liệu đang chạy vì **nhãn chính là dữ liệu**; sắp thứ tự phải viết `CASE WHEN` khắp nơi; và so sánh chuỗi rải 145 chỗ, sửa một luồng phải nhớ đủ chỗ.

**Vì sao R5 là lỗ hổng nguy hiểm nhất — và nó đang hở thật, không phải rủi ro tương lai.**

Lỗ hổng có **hai tầng**, bản 2.0 chỉ mô tả tầng thứ nhất:

*Tầng 1 — quên khai loại dữ liệu.* 19 loại chưa khai trong `SCOPE_FIELDS`, gặp loại chưa khai thì `_role_scope_cond` trả về "không giới hạn". Phần lớn 19 loại đó là danh mục dùng chung nên chưa gây hậu quả.

*Tầng 2 — đã khai nhưng endpoint quên gọi.* Phạm vi đang được áp **bằng tay ở 38 chỗ**. Loại `employee` **đã khai đủ** trong `SCOPE_FIELDS`, nhưng chỉ endpoint danh sách gọi `apply_scope`. Rà hết module nhân sự ngày 12/08/2026:

| Endpoint | Có `apply_scope` | Hậu quả |
|---|---|---|
| `GET /api/employees` (danh sách) | Có | Đúng |
| `GET /api/employees/{id}` (chi tiết) | **Không** | Ai có quyền đọc nhân sự là **xem được hồ sơ bất kỳ**, chỉ cần đoán số id |
| `GET /api/employees/export/csv` | **Không** | **Tải về toàn bộ nhân sự của mọi pháp nhân** trong một lần bấm |

Rộng ra ngoài module nhân sự: **cả 11 endpoint xuất và nhập tệp** (pháp nhân, phòng ban, nhân sự, sản phẩm, nhà cung cấp, báo cáo) **đều không gọi `apply_scope`**. Thêm nữa, hành động `export` **đã có sẵn** trong danh sách hành động của hệ phân quyền, nhưng chỉ **1 trên 11** endpoint đó thực sự kiểm nó — 10 endpoint còn lại chỉ cần quyền `read`.

Nghĩa là câu "một lần quên khai là lộ bảng lương" không còn là giả định. Cùng một kiểu quên **đã xảy ra rồi** trên chính bảng nhân sự, ở thời điểm bảng đó mới chỉ chứa họ tên và phòng ban. N1 sẽ thêm căn cước vào bảng này, N2 sẽ thêm lương. **H4 phải xong trước khi thêm bất kỳ trường nhạy cảm nào.**

---

## 2. Hạ tầng hiện có gì — chấm điểm

Cột bằng chứng là thứ đọc được trong mã nguồn, không phải ấn tượng chung.

| # | Hạng mục | Hiện có gì | Thiếu gì | Mức |
|---|---|---|---|---|
| 1 | Kiến trúc module | 35 module, mỗi module bốn tệp `model`/`schema`/`service`/`controller`; hạ tầng chung ở `core/` | Không thiếu gì đáng kể. Điểm mạnh nhất | Đủ |
| 2 | Phân quyền hành động | Ma trận (đối tượng × hành động) theo vai trò, chặn ở endpoint bằng `require(entity, action)`. Danh sách hành động **đã có sẵn `export`** | `export` khai rồi nhưng chỉ **1/11** endpoint xuất tệp thực sự kiểm; **`import` chưa có**; thiếu **phân quyền mức trường** (lương, căn cước) — xem H15 | Tạm |
| 3 | Phạm vi dữ liệu | Cấp theo từng lượt vai trò, có bao gồm và loại trừ theo pháp nhân / phòng ban / nhân sự. Mềm hơn HRM thương mại đã khảo sát | Khai 9/28, **thiếu khai thì không lọc**, và **áp bằng tay ở 38 chỗ trong khi có 97 endpoint đọc — quên chỗ nào là hở chỗ đó**, đang hở thật ở 3 endpoint nhân sự. Phạm vi phòng ban còn **so bằng tên tiếng Việt** chứ không theo id, xem H16. **Thêm ở bản 2.2:** phần bao gồm / loại trừ theo phòng ban và theo nhân sự **đặt trên dữ liệu nhân sự thì không có hiệu lực** — hàm dựng điều kiện tra khóa `dept_name` và `owner`, còn bảng nhân sự khai `dept_id` và `self`, tra không thấy thì bỏ qua im lặng. Cấu hình lưu được nhưng không sinh mệnh đề nào. Xem H4(a) | Thiếu |
| 4 | Middleware | **Đúng một cái: CORS** (danh sách địa chỉ khai trong `.env`, không dùng `*` — chỗ này đúng). Cộng 2 bộ xử lý lỗi và một mount tệp tĩnh | Không có mã định danh request; không có nhật ký truy cập; **không có bộ xử lý cho lỗi chưa bắt** nên lỗi 500 trả `{"detail": ...}`, **sai vỏ envelope mà giao diện đang dựa vào**; không header bảo mật; không giới hạn kích thước ở tầng chung. **Và một cấu hình chết:** `default_limits=["300/minute"]` khai trong `limiter.py` nhưng `SlowAPIMiddleware` **không được add vào app** → thực tế **4/265 route** có giới hạn tần suất, người đọc mã lại tưởng cả hệ được bảo vệ | Thiếu |
| 5 | Bảo mật đăng nhập | JWT access + refresh, bcrypt, token đặt lại mật khẩu hạn 24 giờ, giới hạn tần suất ở 4 endpoint | Token **không có mã định danh nên không thu hồi được** — khóa tài khoản không có hiệu lực thật tới khi hết hạn. Không có nhật ký phiên | Tạm |
| 6 | Bộ nhớ đệm | Hồ sơ quyền đệm trong bộ nhớ tiến trình, hạn 60 giây | **Bản chạy thật có 2 tiến trình**, xóa đệm chỉ tác dụng ở một tiến trình. Redis sẵn sàng nhưng chưa dùng | Thiếu |
| 7 | Tác vụ nền | Celery + Redis + hẹn giờ, chạy thật: sao lưu 01:00 và 13:00, dọn thông báo 02:30, gom nhật ký ngày 1 | Một hàng đợi chung, việc nặng chạy chung việc nhẹ. Không theo dõi tác vụ hỏng | Tạm |
| 8 | Webhook, API ra ngoài | **Không có dòng mã nào** | Toàn bộ. Phải viết mới | Thiếu |
| 9 | Đa pháp nhân | Có bảng pháp nhân, có phân cấp cha con, có đại diện pháp luật, mã số thuế | **42/57 bảng** chưa có cột pháp nhân (bản 2.0 ghi 17/31 vì đếm theo tệp model). Chưa có đánh số chứng từ theo pháp nhân, chưa có báo cáo hợp nhất | Thiếu |
| 10 | Chuẩn hóa trạng thái | Tiền lệ đúng ở `import_tool` (SmallInt + enum) | 30 cột lưu chuỗi, 11 cột lưu tiếng Việt và **trả nguyên chuỗi đó ra giao diện** | Thiếu |
| 11 | Migration | 75 tệp, chạy tự động khi khởi động | Khi cơ sở dữ liệu trống, kịch bản khởi động **tạo bảng thẳng từ model rồi đánh dấu đã chạy hết migration** — chuỗi migration không bao giờ được chạy lại từ đầu, hỏng lúc nào không biết | Thiếu |
| 12 | Kiểm thử | 27 tệp kiểm thử máy chủ, cộng kiểm thử giao diện tự động | Chưa có bài kiểm cho chính phần nền: phân quyền, phạm vi, quy ước. Chưa có CI chặn | Tạm |
| 13 | Nhật ký, giám sát | Nhật ký thao tác ghi mọi thay đổi dữ liệu, có gom theo tháng | Không có nhật ký ứng dụng tập trung, không cảnh báo, không chỉ số. Hỏng thì biết qua người dùng gọi điện. **Chưa có nhật ký truy cập** — chỉ ghi ai *sửa* gì, không ghi ai *đọc* gì và ai *xuất* gì. **Và endpoint đọc nhật ký thao tác chỉ kiểm đã đăng nhập, không kiểm quyền, không áp phạm vi** — mà nhật ký chứa giá trị trước và sau, nên đây là đường vòng đọc được dữ liệu phạm vi đang che. Xem **H18** | Thiếu |
| 14 | Tệp đính kèm | Kho đối tượng, tách môi trường bằng tiền tố. Có hàm sinh liên kết ký hạn 10 phút | **Bản 2.1 mô tả hạng mục này quá lạc quan.** Rà lại: hàm ký hạn giờ **chỉ dùng đúng 1 chỗ** (tải bản sao lưu). Mọi tệp còn lại — hợp đồng, đính kèm chứng từ, ảnh nhân sự, chữ ký, tệp nhập — lưu và trả về **liên kết công khai vĩnh viễn**, và mount tệp tĩnh `/api/uploads` **không có kiểm quyền nào**. Khóa tệp đoán được theo cấu trúc `{môi trường}/{loại}/{năm}/{tháng}/{id}-{tên}`. Xem **H17** | **Thiếu** |
| 15 | Tái sử dụng mã nguồn | Bảy tệp hạ tầng chung ở `core/`; controller mỏng, nghiệp vụ ở `service.py` (6.654 dòng controller / 6.368 dòng service — tỷ lệ lành) | Lớp dùng chung dừng ở mức **hàm rời rạc**, mỗi module vẫn tự lắp lại đủ bảy bước. Xem H3 | Tạm |

**Không có hạng mục nào ở mức phải viết lại từ đầu.** Giữ mã nguồn Thu mua làm nền là lựa chọn đúng.

---

## 3. H3 — Gom phần lặp thành lớp dùng chung

Đặt lên đầu mục 3 vì đây là hạng mục **quyết định giá của mọi thứ viết sau nó**. HRM sẽ sinh hơn mười module mới: gom trước thì mười module đó được lợi, gom sau thì phải đi dọn lại chính cái vừa viết.

### Mức lặp đo được ngày 12/08/2026

| Đo cái gì | Con số | Hậu quả |
|---|---|---|
| **Ném lỗi bằng `HTTPException` thô** | **259 chỗ** *(2.0 ghi 247 — chênh do CR-060, CR-061 vào sau)* | Xem mục dưới. Đây là chỗ tệ nhất |
| Bộ sinh router chung `make_crud_router` | dùng ở **1 trên 36** module (chỉ `catalog`) | 35 module tự viết lại năm endpoint giống hệt |
| Endpoint danh sách tự viết cùng khuôn | **25 chỗ** | Sửa cách phân trang là sửa 25 chỗ |
| Ghi nhật ký thao tác bằng tay | **92 chỗ** | Quên một chỗ là mất dấu vết, không ai biết |
| **Áp phạm vi dữ liệu bằng tay** | **38 chỗ** | Quên một chỗ là lộ dữ liệu. Đây là R5 nhìn từ góc khác, và **đã quên 3 chỗ rồi** |
| Module tự viết luồng duyệt riêng | **5 module** | Xem H6 |
| Xuất và nhập tệp tự viết | **11 endpoint** trên 6 module | Mỗi màn hình xuất một kiểu; **không endpoint nào áp phạm vi**, chỉ 1 kiểm quyền `export` |

### 3.1. Hàm trả lỗi dùng chung

**Hiện trạng.** `core/response.py` **đã có** hàm `error(message, code, status_code, details)` đúng chuẩn. Nhưng đếm lại ngày 12/08/2026: trong 36 module, hàm này được gọi **0 lần** — hai chỗ dùng nó đều nằm ở bộ xử lý lỗi trong `main.py`, không phải trong module *(bản 2.1 ghi "đúng 2 lần trong 36 module", đếm gộp nhầm hai chỗ ở `main.py`)*. Toàn bộ **259 chỗ** trong module đều ném `HTTPException(400, "câu tiếng Việt")`, rồi bộ xử lý lỗi tập trung ở `main.py` chuyển thành envelope với `code = str(exc.status_code)`.

Nghĩa là **mã lỗi trả ra chỉ là con số HTTP** — `"400"`, `"404"`. Giao diện không phân biệt được "trùng mã" với "sai định dạng ngày" với "ngoài phạm vi", vì cả ba đều là `400`. Muốn xử lý khác nhau thì chỉ còn cách **so chuỗi tiếng Việt** — đúng lỗi mà R2 đang cấm, chỉ là ở tầng khác.

Câu lỗi cũng chép tay: `"Ngoài phạm vi được phép xem"` xuất hiện 10 chỗ, `"Không có ID hợp lệ"` 9 chỗ, `"Không tìm thấy tài khoản"` 4 chỗ.

**Đề xuất.** Một tệp `core/errors.py`, mọi chỗ ném lỗi đi qua đó:

```python
class ErrorCode(StrEnum):
    NOT_FOUND       = "not_found"
    DUPLICATE       = "duplicate"
    OUT_OF_SCOPE    = "out_of_scope"
    INVALID_STATE   = "invalid_state"      # thao tác sai trạng thái chứng từ
    MISSING_FIELD   = "missing_field"
    ...

MESSAGES = {
    ErrorCode.NOT_FOUND:    "Không tìm thấy {entity}",
    ErrorCode.DUPLICATE:    "{field} đã tồn tại",
    ErrorCode.OUT_OF_SCOPE: "Ngoài phạm vi được phép xem",
    ...
}

class AppError(Exception):
    def __init__(self, code: ErrorCode, status: int = 400, **ctx): ...
```

Chỗ gọi:

```python
raise AppError(ErrorCode.NOT_FOUND, status=404, entity="nhà cung cấp", id=sid)
```

Bộ xử lý tập trung dựng ra:

```json
{ "success": false,
  "error": { "code": "not_found",
             "message": "Không tìm thấy nhà cung cấp",
             "details": { "entity": "supplier", "id": 42 },
             "request_id": "..." } }
```

**Được gì:**

| | |
|---|---|
| Giao diện rẽ nhánh theo `code`, không theo chữ tiếng Việt | Đổi câu chữ không làm gãy giao diện |
| Câu chữ khai một chỗ | Sửa `"Ngoài phạm vi được phép xem"` là sửa 1 dòng, không phải 10 |
| `details` có ngữ cảnh máy đọc được | Giao diện tô đỏ đúng ô sai, thay vì hiện một dòng chữ chung |
| `request_id` đi kèm | Người dùng đọc mã đó qua điện thoại là tra được đúng dòng nhật ký. Ăn khớp với H11 |
| Dịch được về sau | Khi cần song ngữ thì chỉ đổi bảng `MESSAGES` |

**Chuyển dần được:** giữ nguyên bộ xử lý `HTTPException` cũ, thêm bộ xử lý `AppError` chạy song song. Module mới bắt buộc dùng `AppError`; 259 chỗ cũ chuyển theo từng module, không cần chuyển hết một lần.

### 3.2. Bốn lớp dùng chung còn lại

| Việc | Thay cho | Nội dung | Điểm quan trọng nhất |
|---|---|---|---|
| **Hàm danh sách chuẩn** | 25 endpoint chép khuôn | Gộp sáu bước đang lắp tay: lọc → **áp phạm vi** → sắp xếp → đếm → phân trang → chuyển schema. Module gọi một dòng thay vì bảy | **Áp phạm vi thành mặc định**, muốn bỏ phải ghi rõ. Đây chính là fail-closed của R5 áp ở tầng controller |
| **Lớp dịch vụ nền** | 92 chỗ ghi nhật ký tay, 53 chỗ ném lỗi "không tìm thấy" tay | `get_or_404`, tạo, sửa, xóa; **tự ghi nhật ký**, tự gán người tạo và người sửa. Module kế thừa rồi chỉ viết phần riêng | Quên gắn nhật ký trở thành chuyện không thể xảy ra |
| **Mở rộng bộ sinh router** | 35 module tự viết | **Vá trước đã:** bộ sinh router hiện tại **không gọi `apply_scope` ở bất kỳ đâu**, endpoint xuất tệp nó sinh ra chỉ kiểm quyền `read` chứ không kiểm `export`, nhánh nhập tệp gọi một hàm **chưa được nhập khẩu ở phạm vi đó nên chạy tới là lỗi tên**, và nhập tệp **không ghi nhật ký, không giới hạn số dòng**. Sau khi vá mới nhận thêm phạm vi dữ liệu, xuất tệp, đính kèm, bình luận, rồi chuyển các module danh mục thuần sang dùng | Khoảng một nửa số module hiện tại là danh mục thuần. **Thứ tự bắt buộc: vá bộ sinh router trước, cho module kế thừa sau** — làm ngược lại là nhân một lỗ hổng ở 1 chỗ thành lỗ hổng ở 36 chỗ |
| **Xuất tệp dùng chung** | 11 endpoint xuất và nhập | Khai cột theo dữ liệu thay vì viết mã từng màn hình. Gắn sẵn ba thứ: **kiểm quyền `export` / `import`**, **áp phạm vi dữ liệu**, và **ghi một dòng nhật ký cho mỗi lần xuất** (ai, lúc nào, bảng nào, bao nhiêu dòng, bộ lọc gì) | Xuất tệp thống nhất một kiểu; không xuất được dữ liệu ngoài phạm vi; và mọi lần xuất đều tra lại được về sau |
| **Bộ khung module mới** | — | Thư mục mẫu tạo module mới đúng chuẩn ngay từ đầu | HRM sinh hơn mười module; không có khung mẫu thì mười module đó lặp lại đúng phần vừa dọn |

**Xong là thế nào:** viết một module danh mục mới từ đầu tới lúc chạy được **dưới 50 dòng mã**, và module đó tự động có phân quyền, phạm vi dữ liệu, nhật ký thao tác, phân trang, sắp xếp, xuất tệp, mã lỗi chuẩn — không phải nhớ gắn thứ nào.

**Nguyên tắc gom, để không gom quá tay:** chỉ gom cái đã lặp **từ ba lần trở lên** và lặp **giống hệt nhau**. Gom hai cái hơi giống nhau thành một lớp cha có năm tham số điều kiện thì khó đọc hơn là để nguyên.

**Nguyên tắc thứ hai, quan trọng hơn — thêm ở bản 2.2:** *đừng viết hàm tiện ích để người ta nhớ mà gọi; hãy làm cho **đường đi lấy dữ liệu duy nhất** đã có sẵn phạm vi bên trong, ai muốn không lọc thì phải ghi rõ `public=True`.* Căn cứ: hiện có **97 endpoint đọc** nhưng chỉ **38 chỗ** gọi `apply_scope`. `apply_scope` đã là một hàm dùng chung viết đúng — vấn đề không phải thiếu hàm, mà là **hàm đó có thể quên gọi**. Thêm một hàm tiện ích nữa cũng có thể quên gọi y như vậy.

**Thứ tự bắt buộc khi làm H3:** `errors.py` → `deps.py` (gói ngữ cảnh yêu cầu: phiên, hồ sơ quyền, `db`) → tầng truy vấn có sẵn phạm vi → lớp dịch vụ nền → **vá rồi viết lại bộ sinh router** → cuối cùng mới chuyển từng module. Mỗi bước đứng trên bước trước; đảo thứ tự là phải viết lại.

**Cỡ:** vừa. Làm dần được — viết lớp dùng chung trước, module cũ chuyển lúc nào cũng được.

Danh sách task chi tiết của H3, kèm điều kiện cần và điều kiện đủ của từng bước, ở [`08` mục 4 và đợt 3](./08-danh-sach-task-cung-co.md).

---

## 4. H1 — Bỏ tiếng Việt khỏi cơ sở dữ liệu

Quy định đã có (R2), giờ là kế hoạch thi hành. Đây là hạng mục **lớn nhất về số chỗ phải sờ vào**, nhưng chia nhỏ được theo module và có đường lui ở mọi bước.

> **Bản thực thi của mục này nay ở [`15` Đổ bê tông nền ERP v2](./15-do-be-tong-nen-v2.md)** — đo lại
> bằng dữ liệu thật ngày 22/08/2026, chia thành chín đợt B-01…B-09. **Chỗ nào số liệu lệch thì lấy
> `15`**, vì mục này đo từ 12/08/2026. Ba đính chính đã biết: bảng dưới thiếu **cột thứ 12**
> `tab_po_item.status_before_pause`; `tab_contract.contract_type` đã được CR-118 chuẩn hóa nên
> không còn trong danh sách; và **R2 ở mục 1 đã được viết lại trong đợt B-01** — **QĐ-9 chốt ngày
> 22/08/2026 đi khuôn mã chuỗi tiếng Anh cho Thu mua**, không phải `SMALLINT` *(lý do đầy đủ ở
> `15` §2.4)*.
>
> Thêm **QĐ-10** *(`15` §4.2)*: chín đợt này làm **thẳng trên nhánh `erp-v2`**, `main`/prod đứng
> yên với chuỗi tiếng Việt cho tới ngày cắt sang bản mới. Nên `frontend/` **ngoài phạm vi** —
> con số "67 chỗ giao diện" ở mục 1 chỉ còn tính phần `frontend-v2/`.

### Mười một cột đang lưu tiếng Việt

| Bảng | Cột | Giá trị đang lưu | Độ liên đới |
|---|---|---|---|
| `tab_contract` | `party_type` | Nhà cung cấp / Khách hàng / Khác | Thấp |
| `tab_contract` | `status` | Hiệu lực / Hết hạn / Thanh lý | Thấp |
| `tab_employee` | `status` | Chính thức / … | Thấp |
| `tab_supplier` | `legal_type` | Công ty / Cá nhân / Hợp danh / Hộ kinh doanh | Thấp |
| `tab_survey` | `approve_status` | Duyệt / Không duyệt | Vừa |
| `tab_payable` | `status` | Chờ TT / Trả một phần / Đã TT | Vừa — dính công nợ |
| `tab_purchase_request` (dòng) | `line_status` | Chưa đặt hàng / … | **Cao** |
| `tab_purchase_order` | `document_status` | chưa có chứng từ / … | **Cao** |
| `tab_purchase_order` (dòng) | `line_status` | Chưa giao / Đang giao / Đủ | **Cao** |
| `tab_purchase_order` (dòng) | `progress_status` | Chưa đặt hàng / … — máy trạng thái của màn Tiến độ | **Cao** |
| `tab_purchase_order` (giao) | `status` | trạng thái giao | **Cao** |

Ngoài ra khoảng 20 cột lưu chuỗi tiếng Anh viết thường (`draft`, `submitted`, `pending`) — đỡ nguy hiểm hơn vì nhãn không phải là dữ liệu, nhưng vẫn là chuỗi tự do, vẫn gõ sai được, nên cũng chuyển, chỉ là xếp sau.

### Sáu bước, làm cho từng cột một

| Bước | Làm gì | Đường lui |
|---|---|---|
| 1 | **Liệt kê giá trị thật đang có trong dữ liệu** (`SELECT DISTINCT`), không tin vào chú thích trong mã nguồn. Khai `IntEnum` ở `core/enums.py` kèm nhãn tiếng Việt, và bảng ánh xạ chuỗi cũ sang số | Chưa đụng dữ liệu |
| 2 | Migration **thêm cột mới** `<tên>_code SMALLINT`, điền cho dòng cũ theo bảng ánh xạ. **Giá trị lạ không ánh xạ được thì để rỗng và ghi ra một bảng lỗi — không đoán** | Cột cũ nguyên vẹn |
| 3 | Trong model, cột chuỗi cũ thành **thuộc tính suy ra từ cột số**. Ghi vào một chỗ, đọc được cả hai. Hai cột luôn khớp | Bỏ thuộc tính là quay lại như cũ |
| 4 | Chuyển phần **đọc, lọc, báo cáo** sang cột số. API trả `status` là số và `status_label` là chữ | Giao diện chưa sửa vẫn chạy nhờ `status_label` |
| 5 | Giao diện: sinh `enums.ts` từ `core/enums.py`, CI so sánh; gom 9 tệp đang chép chuỗi về đúng tệp này | |
| 6 | Sau khi chạy song song **ít nhất một tháng** không có sự cố: migration bỏ cột chuỗi cũ và bỏ `status_label` | Bước duy nhất không lui được — nên đặt cuối và có mốc thời gian |

**Thứ tự module:** làm từ độ liên đới thấp lên cao — hợp đồng, nhân sự, nhà cung cấp trước (tập dượt, ít rủi ro), rồi khảo sát và công nợ, **cuối cùng mới tới yêu cầu mua hàng và đơn mua hàng** vì đó là nơi máy trạng thái phức tạp nhất và đang chạy thật hằng ngày.

**Bảng và module mới:** dùng cột số ngay từ đầu, **không có giai đoạn chuyển tiếp**. Kể cả toàn bộ HRM.

**Xong là thế nào:** bài kiểm tự động pass; không còn chỗ nào ở máy chủ so sánh trực tiếp với chuỗi trạng thái; đổi nhãn hiển thị của một trạng thái chỉ sửa một dòng và không đụng dữ liệu.

**Chặn cái gì:** chặn mọi báo cáo xuyên phân hệ. Chừng nào trạng thái còn là chuỗi tự do thì không gộp số liệu giữa hai phân hệ được.

**Cỡ:** lớn, nhưng chia nhỏ được và làm dần được.

---

## 5. Mười sáu hạng mục còn lại

| # | Hạng mục | Vấn đề | Làm gì | Xong là thế nào | Cỡ |
|---|---|---|---|---|---|
| **H2** | Enum một chỗ, giao diện không chép | 9 tệp giao diện cùng chép danh sách trạng thái. **Không dựng API lấy động** — trạng thái đổi vài lần một năm, mà mỗi lần đổi đằng nào cũng phải sửa giao diện | Kịch bản sinh `frontend/src/config/enums.ts` từ `core/enums.py`; tệp sinh ra lưu vào mã nguồn nên có kiểm tra kiểu đầy đủ; CI chạy lại và so sánh | Khác một ký tự giữa hai đầu là CI hỏng. Người viết mã quên chạy lại thì CI nhắc | Nhỏ |
| **H4** | Phạm vi dữ liệu: khai đủ, chặn khi thiếu, và **vá bốn chỗ đang hở** | R5 cả hai tầng. Khai 9/28; thiếu thì không lọc; 3 endpoint đã khai vẫn không gọi `apply_scope`; **và bản 2.2 tìm thêm chỗ thứ tư: cấu hình bao gồm / loại trừ theo phòng ban và theo nhân sự đặt trên dữ liệu nhân sự là *không có hiệu lực*** — hàm dựng điều kiện tra khóa `dept_name` và `owner`, còn khai báo phạm vi của bảng nhân sự chỉ có `company`, `dept_id`, `self`, tra không thấy thì **bỏ qua im lặng**. Nghĩa là màn hình cấp quyền cho phép chọn "trừ phòng Nhân sự" và lưu được, nhưng câu truy vấn không có mệnh đề nào tương ứng | **(a) Vá trước, trong ngày:** thêm `apply_scope` vào `GET /api/employees/{id}` và cả 11 endpoint xuất/nhập tệp; **và sửa hàm dựng điều kiện để nó tra đúng khóa đã khai, tra không thấy thì báo lỗi chứ không bỏ qua**. **(b)** Bắt buộc kiểm quyền `export` ở cả 11 endpoint đó, thêm hành động `import` — **chỉ bật chặn sau khi đã có nhật ký truy cập của H18 và đã thu thập đủ hai tuần**, xem ghi chú dưới bảng. **(c)** Mỗi lần xuất ghi một dòng nhật ký: ai, lúc nào, bảng nào, bao nhiêu dòng, bộ lọc gì. **(d)** Khai đủ 28 loại (loại cố ý công khai thì khai rõ là công khai, không để trống), đổi mặc định thành **báo lỗi**. **(e)** Bài kiểm duyệt đủ 28 loại **và** duyệt mọi endpoint đọc đều đi qua phạm vi | Thêm loại dữ liệu mới mà quên khai thì bài kiểm hỏng ngay; thêm endpoint đọc mà quên áp phạm vi cũng hỏng ngay; **cấu hình loại trừ phòng ban đặt trên dữ liệu nhân sự có tác dụng thật, kiểm lại được bằng cách đếm số dòng trước và sau khi loại trừ**; và mọi lần xuất dữ liệu đều tra lại được | Vừa — nhưng phần (a) là **việc trong ngày**, tách ra làm ngay, không đợi cả hạng mục |
| **H5** | Middleware và bảo mật | **Đúng một middleware: CORS.** Token không thu hồi được. Không có bộ xử lý cho lỗi chưa bắt nên lỗi 500 trả `{"detail": ...}`, **sai vỏ envelope mà giao diện đang dựa vào**. Và một **cấu hình chết**: `default_limits=["300/minute"]` khai trong `limiter.py` nhưng `SlowAPIMiddleware` **không được nạp vào app**, nên thực tế chỉ **4/265 route** có giới hạn tần suất — người đọc mã lại tưởng cả hệ được bảo vệ | Mã định danh request xuyên suốt; **bộ xử lý lỗi chưa bắt, trả đúng vỏ envelope, kèm mã định danh request**; **nạp `SlowAPIMiddleware` để `default_limits` có hiệu lực thật, hoặc bỏ hẳn dòng khai đó — không để cấu hình chết**; header bảo mật; giới hạn kích thước tệp ở tầng chung; **thêm mã định danh vào token và bảng token đã thu hồi**; nhật ký phiên đăng nhập | Khóa một tài khoản là người đó mất quyền **ngay**, không phải đợi token hết hạn. Ném một lỗi cố ý ở máy chủ thì giao diện vẫn nhận đúng vỏ `{success, message, data}` và hiện được thông báo. Gọi quá ngưỡng ở một route bất kỳ thì bị chặn | Vừa |
| **H6** | **Bộ máy duyệt dùng chung** | 5 module tự viết luồng duyệt riêng. HRM sẽ thêm ít nhất 5 loại nữa | Một bộ máy: khai người duyệt theo **vai trò tương đối** (trưởng bộ phận của người nộp), không khai theo tên; nhiều bậc; ủy quyền khi vắng; xem được đang tắc ở ai. Chuyển **một** loại chứng từ Thu mua đang chạy sang làm mẫu, có đường lui | Thêm một loại chứng từ mới chỉ là khai cấu hình, không viết mã | **Lớn** |
| **H7** | Sẵn sàng đa pháp nhân | **42/57 bảng** thiếu `company_id` — gấp gần hai lần rưỡi con số ở bản 2.0. Trong đó có bảng lớn: khảo sát, nhà cung cấp, sản phẩm, dòng đơn mua hàng, dòng yêu cầu mua hàng, kho, đơn vị tính, nhóm hàng, thương hiệu, tài khoản, vai trò | Thêm cột cho các bảng còn thiếu, **điền theo dữ liệu suy được, chỗ nào không suy được thì để rỗng và ghi lại, không gán bừa**; đánh số chứng từ theo pháp nhân; quy tắc dùng chung danh mục giữa các pháp nhân. **Phải chia thành nhiều đợt theo module**, một đợt một nhóm bảng | Tạo chứng từ ở pháp nhân B không nhìn thấy dữ liệu pháp nhân A trừ chỗ cố ý dùng chung | **Lớn** *(bản 2.0 xếp "Vừa" — sai vì đếm thiếu)* |
| **H8** | Bộ đệm dùng chung | Đệm quyền nằm trong bộ nhớ từng tiến trình, bản chạy thật có 2 tiến trình | Chuyển đệm quyền sang Redis; xóa đệm là xóa cho mọi tiến trình | Rút quyền một người xong, mọi tiến trình đều thấy ngay | Nhỏ |
| **H9** | Tác vụ nền | Một hàng đợi chung, việc nặng chạy chung việc nhẹ; tác vụ hỏng không ai biết | Tách hàng đợi nặng / nhẹ; ghi kết quả từng tác vụ; cảnh báo khi hỏng | Tác vụ hỏng là có người biết trong vòng vài phút | Nhỏ |
| **H10** | Webhook và API ra ngoài | Không có dòng mã nào | Khai sự kiện một chỗ; đăng ký địa chỉ nhận; ký nội dung; gửi lại khi hỏng; nhật ký gửi; khóa API cho hệ thống ngoài | Một hệ thống ngoài đăng ký nhận sự kiện và nhận đủ, có bằng chứng ở nhật ký | Vừa |
| **H11** | Nhật ký, giám sát, cảnh báo | Hỏng thì biết qua người dùng gọi điện | Nhật ký ứng dụng có cấu trúc, gắn mã định danh request của H5; cảnh báo khi tỷ lệ lỗi vọt; vài chỉ số cơ bản | Người dùng đọc mã lỗi qua điện thoại là tra ra đúng dòng nhật ký | Vừa |
| **H12** | Migration | Cơ sở dữ liệu trống thì tạo bảng thẳng từ model rồi đánh dấu đã chạy hết migration — chuỗi migration **không bao giờ được chạy lại từ đầu** | Bỏ nhánh tạo thẳng; CI dựng cơ sở dữ liệu trống rồi chạy đủ 75 migration từ đầu mỗi lần | Dựng môi trường mới là chạy migration, và biết chắc nó chạy được | Nhỏ |
| **H13** | Kiểm thử phần nền và CI | 27 tệp kiểm thử nhưng không tệp nào kiểm chính phần nền | Bài kiểm cho: quy ước đặt tên (R1), enum (R2), lệch enum giữa hai đầu (R3), cột pháp nhân (R4), đủ 28 phạm vi (R5), **mọi endpoint đọc đều đi qua `apply_scope`** (R5 tầng 2), chuỗi migration (H12). CI chặn khi hỏng | Vi phạm bất kỳ ràng buộc nào ở mục 1 là CI chặn, không phải chờ người rà | Vừa |
| **H14** | Khung giao diện nhiều phân hệ | Giao diện dựng cho một phân hệ | Lưới biểu tượng phân hệ hiện theo quyền; điều hướng hai cấp; khai danh sách phân hệ một chỗ dùng chung với máy chủ; **giữ nguyên đường dẫn cũ của Thu mua** | Người dùng Thu mua đăng nhập vẫn vào thẳng việc của mình; người có quyền HRM thấy thêm một biểu tượng | Vừa |
| **H15** | **Phân quyền mức trường** | Hệ hiện tại chỉ biết "được đọc loại dữ liệu này" hay "không". Không có mức "được đọc hồ sơ nhân sự **nhưng không thấy cột lương**". Bản 2.0 có nhắc thiếu ở mục 2 nhưng **không có hạng mục nào làm** | Khai danh sách trường nhạy cảm theo loại dữ liệu (lương, căn cước, tài khoản ngân hàng, ngày sinh); cấp quyền đọc và sửa riêng cho từng nhóm trường; **lọc ngay ở lớp schema đầu ra**, không lọc ở giao diện; trường bị che thì không có mặt trong JSON chứ không phải trả rỗng; xuất tệp và webhook dùng chung bộ lọc đó | Trưởng phòng mở hồ sơ nhân viên phòng mình thì **không có** cột lương trong dữ liệu trả về, kể cả khi mở bằng công cụ lập trình | Vừa — **chặn N2** |
| **H16** | **Phạm vi phòng ban khóa theo id** | `apply_scope` đang lọc phòng ban bằng **so bằng chuỗi tiếng Việt**: chứng từ lưu cột `department` kiểu `String(255)`, đem so đúng bằng với `dept_name` trong hồ sơ quyền. Đổi tên phòng là **chứng từ cũ rơi khỏi phạm vi, im lặng**; thừa dấu cách là thành phòng khác; hai phòng trùng tên ở hai pháp nhân thì lẫn dữ liệu | Thêm cột `dept_id` vào các bảng chứng từ đang dùng tên (yêu cầu mua hàng, yêu cầu khảo sát, đơn mua hàng); điền theo tên hiện có, **tên nào không khớp phòng nào thì để rỗng và ghi ra bảng lỗi, không đoán**; chuyển `apply_scope` sang so theo id; giữ cột tên chạy song song rồi mới bỏ, theo đúng sáu bước của H1 | Đổi tên một phòng ban không làm ai mất dữ liệu đang thấy | Vừa — làm cùng đợt với H1 |
| **H17** | **Tệp đính kèm phải đi qua kiểm quyền** | Bản 2.1 chấm hạng mục này "Tạm" và mô tả là "liên kết ký hạn 10 phút". Đọc lại mã nguồn: hàm ký hạn **chỉ dùng ở một chỗ duy nhất** là tải bản sao lưu. Mọi tệp còn lại — hợp đồng, đính kèm chứng từ, ảnh nhân sự, chữ ký, tệp nhập — được lưu và trả về **liên kết công khai vĩnh viễn**; ở môi trường không dùng kho đối tượng thì phục vụ qua mount tệp tĩnh `/api/uploads`, **không gắn phụ thuộc kiểm quyền nào**. Khóa tệp lại đoán được: `{môi trường}/{loại}/{năm}/{tháng}/{id}-{tên gốc}`. Ai có liên kết là tải được, không cần đăng nhập, và liên kết không hết hạn. HRM sẽ đính kèm căn cước, hợp đồng lao động, quyết định lương vào chính đường này | Đưa mọi tệp về **một đường tải duy nhất** `GET /api/files/{id}`: kiểm đăng nhập, kiểm quyền đọc **của chứng từ chủ quản**, áp phạm vi của chứng từ đó, rồi mới chuyển hướng sang liên kết ký hạn ngắn; bỏ mount tệp tĩnh không kiểm quyền, hoặc gắn phụ thuộc kiểm quyền vào nó; **ngừng lưu liên kết công khai vào cơ sở dữ liệu — lưu khóa tệp, sinh liên kết lúc trả về**; ghi nhật ký mỗi lượt tải; đổi khóa tệp sang phần ngẫu nhiên để không đoán được | Dán liên kết tệp hợp đồng vào cửa sổ trình duyệt ẩn danh thì **bị chặn**, không tải được. Người không có quyền đọc chứng từ chủ quản cũng bị chặn dù có liên kết | Vừa — **chặn N1 và N2** |
| **H18** | **Nhật ký thao tác phải có quyền và có phạm vi** | Endpoint đọc nhật ký thao tác chỉ kiểm **đã đăng nhập**, không kiểm quyền, không áp phạm vi. Tham số mã bản ghi để trống thì trả **nhật ký của mọi bản ghi thuộc loại đó** — chính tài liệu API viết như vậy. Nhật ký chứa giá trị trước và sau của từng lần sửa, nên đây là **đường vòng đọc được dữ liệu mà phạm vi đang che**: một người không được xem hồ sơ nhân sự phòng khác vẫn đọc được nội dung thay đổi của hồ sơ đó qua nhật ký. Đồng thời **chưa có nhật ký truy cập** (ai đọc gì, ai xuất gì) — mới chỉ có nhật ký thay đổi | Thêm `require("audit", "read")` vào endpoint đọc nhật ký; áp phạm vi **theo chứng từ chủ quản**, không phải theo bản thân dòng nhật ký; che trường nhạy cảm trong nội dung trước/sau bằng đúng bộ lọc của H15; **thêm nhật ký truy cập** cho các endpoint đọc và xuất, giữ đủ lâu để trả lời được câu "ai đã xuất bảng lương tháng trước" | Người không có quyền đọc một chứng từ thì gọi thẳng endpoint nhật ký của chứng từ đó cũng không ra dòng nào. Hỏi "hai tuần qua ai xuất dữ liệu nhân sự" là tra ra danh sách | Nhỏ phần chặn quyền, **Vừa** phần nhật ký truy cập — **phần nhật ký truy cập chặn H4(b)** |

> **Ghi chú về thứ tự giữa H4(b) và H18.** Hiện chỉ **1/11** endpoint xuất tệp kiểm quyền `export`, nghĩa là mười endpoint còn lại đang có người dùng thật, hằng ngày, mà **không ai biết là ai**. Bật chặn trước sẽ cắt việc của những người đó mà không báo trước, và không có cách nào biết trước là cắt vào ai. Thứ tự bắt buộc: **thêm nhật ký truy cập (H18) → thu thập hai tuần → đọc danh sách và cấp quyền `export` cho đúng những người đang xuất → mới bật chặn (H4b)**. Đây là lý do H18 tách thành hạng mục riêng chứ không gộp vào H4.

### Hạng mục nào chặn hạng mục nào

| Làm được ngay, không phụ thuộc gì | Cần cái trước | Chặn gì |
|---|---|---|
| **H4a** vá bốn chỗ đang hở · **H17** tệp đính kèm · **H18** phần chặn quyền của nhật ký thao tác | — | **Làm trước tất cả.** Đều là lỗ hổng đang hở thật, việc trong ngày hoặc trong tuần, không phải chờ duyệt lộ trình |
| **H4** phạm vi (phần còn lại) · **H5** bảo mật · **H13** kiểm thử nền · **H8** bộ đệm · **H12** migration | H4 phần (b) cần **phần nhật ký truy cập của H18** | H4 và H5 **chặn toàn bộ HRM** |
| **H15** phân quyền mức trường | H4 | **Chặn N2.** Vá sau là phải sửa lại cả API lẫn giao diện, nên phải chốt **trước khi thiết kế bảng hợp đồng lao động** |
| **H3** lớp dùng chung · **H2** enum | H4 (để phạm vi thành mặc định) | Không chặn cứng, nhưng làm sau HRM là mất trắng phần lợi |
| **H1** bỏ tiếng Việt · **H16** phòng ban theo id · **H7** đa pháp nhân · **H14** khung giao diện | H13, H12 | Báo cáo xuyên phân hệ · hồ sơ, hợp đồng, kế toán. **H16 làm chung đợt với H1** vì cùng một kiểu migration sáu bước |
| **H6** bộ máy duyệt | H4, H7 | Đơn từ và mọi quyết định nhân sự |
| **H9** tác vụ nền · **H10** webhook · **H11** giám sát | H13 với riêng H10 | Không chặn HRM, chen vào chỗ trống |

---

## 6. HRM làm gì trước

Nguyên tắc: **làm từ cái cơ bản nhất, cái mà mọi thứ khác đứng lên trên.** Cách kiểm tra một bậc có cơ bản không: bỏ nó đi thì bậc sau có làm được không.

Chi tiết trường và cấu trúc từng màn hình ở [`tham-khao-hrm/`](./tham-khao-hrm/README.md) — **trỏ sang để đối chiếu, không phải để chép.** Nghiệp vụ thật vẫn phải ra từ buổi phỏng vấn phòng Nhân sự.

| Bậc | Gồm gì | Vì sao ở đây | Cố tình chưa làm |
|---|---|---|---|
| **N1** | Danh mục cơ cấu: pháp nhân → phòng ban **một cấp phẳng** → chức danh → chức vụ. Hồ sơ nhân viên **tối thiểu** (12 trường). Phạm vi phòng ban khóa theo `dept_id` (H16) | Không có phòng ban và chức danh thì không gắn được người duyệt, không phân được phạm vi dữ liệu, không làm được gì tiếp | **Cây phòng ban nhiều cấp — đã chốt bỏ, xem Q1 ở mục 9.** Hợp đồng, bảo hiểm, lộ trình sự nghiệp, người phụ thuộc, sơ đồ tổ chức vẽ tự động |
| **N2** | Hợp đồng lao động (loại, hạn, ký lại, cảnh báo sắp hết hạn). Quyết định: điều chuyển, tăng lương, thôi việc | Hợp đồng là chỗ duy nhất trả lời "người này đang thuộc pháp nhân nào, chức danh gì, từ ngày nào" | Bảo hiểm, thuế thu nhập cá nhân |
| **N3** | Đơn từ, bắt đầu bằng **nghỉ phép**. Loại đơn và quy tắc phép khai bằng **bảng cấu hình**, không viết cứng | Đây là chức năng người dùng thật chạm vào hằng ngày — nơi HRM chứng minh được giá trị | Các loại đơn hiếm dùng |
| **N4** | Chấm công: nhập dữ liệu máy, đối chiếu với đơn từ, **màn hình xử lý dữ liệu lỗi** | Nặng, dính thiết bị, và chặn lương. Có làm hay không còn chờ chốt ([`04` C2](./04-danh-muc-cho.md)) | — |
| **N5** | Đánh giá, tuyển dụng | Chạy tạm bằng Excel không chết ai | — |

**Hai điều rút ra từ khảo sát, quan trọng hơn danh sách màn hình:**

- Hồ sơ nhân viên bên ngoài có khoảng **90 trường nhưng lúc tạo chỉ hỏi 12**. Bắt điền đủ ngay thì không ai nhập, dữ liệu thành rác. N1 làm đúng 12 trường đó.
- **Luật nghỉ phép là dữ liệu, không phải mã nguồn** — họ khai 15 loại nghỉ trong một bảng cấu hình khoảng 50 cột, vì luật đổi theo năm và theo pháp nhân. Viết cứng vào mã nguồn là mỗi năm sửa mã một lần.

**Không làm lương trong bản 1.** Lý do có bằng chứng: hệ thống đã khảo sát **không viết cứng công thức lương**, họ làm một bộ máy công thức có `IIF`, `isnull`, `round`, khách tự khai cột và tự viết công thức ([`tham-khao-hrm/04`](./tham-khao-hrm/04-tien-luong.md)). Làm lương không phải làm một màn hình mà là làm **một ngôn ngữ kịch bản thu nhỏ** cộng ba màn hình phụ trợ. Đưa vào bản 1 thì HRM trượt lịch **và** bản lương đầu tiên sai — mà lương sai một lần là mất niềm tin của cả công ty vào toàn hệ thống.

---

## 7. Thứ tự tổng

| Vòng | Nội dung | Vì sao ở đây |
|---|---|---|
| **V0-0** | **H4a — vá bốn chỗ đang hở** (chi tiết nhân sự · 11 endpoint xuất/nhập thêm phạm vi · sửa hàm dựng điều kiện tra sai khóa nên loại trừ phòng ban trên dữ liệu nhân sự vô hiệu) · **H17 tệp đính kèm đi qua kiểm quyền** · **H18 phần chặn quyền của nhật ký thao tác** | Bốn lỗ hổng, **đang hở thật trên hệ chạy thật**. Cỡ vài ngày công. **Không chờ duyệt lộ trình.** Riêng phần bật chặn quyền `export` tách sang V0-a vì phải có nhật ký truy cập trước |
| **V0-a** | H4 phạm vi (phần còn lại) · H5 bảo mật · **H18 phần nhật ký truy cập** · H13 kiểm thử nền · H8 bộ đệm · H12 migration | Không phụ thuộc gì, làm được ngay. H4 và H5 chặn toàn bộ HRM. Trong vòng này, **H18 phải xong trước H4(b)**: chưa biết ai đang xuất dữ liệu thì bật chặn là cắt việc người ta mà không báo trước |
| **V0-b** | **H3 lớp dùng chung** · H2 enum · H1 bỏ tiếng Việt · **H16 phòng ban theo id** · H7 đa pháp nhân · H14 khung giao diện | H3 phải xong **trước module HRM đầu tiên** — hơn mười module HRM sẽ viết trên lớp này. H16 đi kèm H1, cùng kiểu migration |
| **V0-c** | H6 bộ máy duyệt dùng chung · **H15 phân quyền mức trường** | H6 cần H4 và H7. H15 phải xong trước khi thiết kế bảng của N2 |
| **V1** | N1 cơ cấu tổ chức và hồ sơ nhân viên | Bậc cơ bản nhất |
| **V2** | N2 hợp đồng và quyết định · N3 đơn từ | Cả hai đứng trên N1 và H6 |
| **V3** | N4 chấm công (nếu chốt làm) · N5 đánh giá, tuyển dụng | Phần nặng và phần hoãn được |
| **Song song** | H9 tác vụ nền · H10 webhook · H11 giám sát | Không chặn HRM, chen vào chỗ trống |

Ba thứ **không** nằm trong lộ trình này: tiền lương, E-Learning, mọi thứ thuộc MFM. Thứ tự phân hệ về sau ở [`02`](./02-dai-han.md).

---

## 8. Rủi ro

| Rủi ro | Dấu hiệu sớm | Chặn bằng gì |
|---|---|---|
| **Lộ dữ liệu lương, căn cước** | Không có dấu hiệu sớm. Loại rủi ro chỉ biết khi đã xảy ra. **Và kiểu quên gây ra nó đã xảy ra rồi** — rà ngày 12/08/2026 ra **bốn đường rò cùng lúc**: 3 endpoint nhân sự bỏ qua phạm vi; cấu hình loại trừ phòng ban trên dữ liệu nhân sự không có hiệu lực; **tệp đính kèm tải được bằng liên kết công khai vĩnh viễn, không cần đăng nhập**; **nhật ký thao tác đọc tự do, mà nhật ký chứa giá trị trước và sau của mọi lần sửa**. Ba trong bốn đường này sẽ dẫn thẳng vào dữ liệu HRM khi N1/N2 lên | H4a + **H17** + **H18** làm ngay; H4 + H5 + **H15** phải xong trước N1 và N2. Không ngoại lệ. Riêng H17 đáng chú ý vì hợp đồng lao động và căn cước là **tệp**, không phải cột trong bảng — vá phạm vi ở tầng truy vấn không che được đường này |
| **Cấu hình bảo mật có màn hình nhưng không có tác dụng** | Không có dấu hiệu nào cả — đó chính là điểm nguy. Đã có hai ca: cấu hình loại trừ phòng ban lưu được nhưng không sinh mệnh đề truy vấn; `default_limits` khai trong bộ giới hạn tần suất nhưng middleware không được nạp | Mọi cấu hình bảo mật phải có **một bài kiểm chứng minh nó có tác dụng**, không phải chứng minh nó lưu được. Vào H13. Nguyên tắc: tra khóa không thấy thì **báo lỗi**, không bỏ qua im lặng |
| **Lịch trượt vì đội vẫn đang gánh Thu mua chạy thật** | Yêu cầu thay đổi của Thu mua vẫn vào đều mà không ai bị rút khỏi lộ trình. Đo được: CR-034 đến CR-061 rơi gọn trong khoảng năm ngày làm việc, tức **xấp xỉ một yêu cầu mỗi ngày** | Lộ trình này **chưa trừ phần công đó ra**. Trước khi chốt lịch, phải có người chuyên trách tách hẳn khỏi luồng xử lý yêu cầu thay đổi, hoặc chấp nhận kéo dài mốc. Ghi thành câu hỏi C15 ở [`04`](./04-danh-muc-cho.md) |
| Bộ máy duyệt bị coi là việc kỹ thuật để sau | Có người đề nghị "làm HRM trước, duyệt tính sau" | H6 nằm ở V0-c với lý do viết sẵn: nó là nền dùng chung của mọi phân hệ, không phải việc của HRM |
| Gom mã nguồn bị hoãn tới sau HRM | Module HRM đầu tiên viết xong mà chưa có lớp dùng chung | H3 ở V0-b. Sau HRM thì phần lợi mất trắng và phải đi dọn lại |
| Chuẩn hóa trạng thái làm vỡ hệ thống đang chạy | Người dùng báo phiếu mất trạng thái | Hai cột chạy song song, không xóa cột cũ trước một tháng. Đường lui ở mọi bước trừ bước 6 |
| Đa pháp nhân bị bỏ tới lúc cần mới làm | Có yêu cầu tách báo cáo theo công ty con | H7 ở V0-b. Thêm cột pháp nhân sau khi có dữ liệu là **không sửa lại được** |
| HRM phình phạm vi | Xuất hiện yêu cầu "tiện thể làm luôn" | Cột "cố tình chưa làm" ở mục 6. Yêu cầu mới vào [`04`](./04-danh-muc-cho.md), không chen ngang |

---

## 9. Việc phải quyết, và quan hệ với `01`

### Quyết định đã chốt — 12/08/2026

| # | Câu hỏi | Đã chốt | Kéo theo gì |
|---|---|---|---|
| **Q1** | Phòng ban có làm **cây nhiều cấp** không | **Không làm.** Phòng ban giữ **một cấp phẳng** | Bảng `tab_department` **đã có sẵn** cột `parent` và `manager_id` từ trước, nhưng **để nguyên không khai thác**. Quan trọng hơn: phạm vi phòng ban vẫn có nghĩa là **đúng một phòng**, không lan xuống phòng con — nên **người dùng Thu mua đang chạy thật không bị đổi tầm nhìn dữ liệu**. Đây chính là lý do nên bỏ: làm cây thì "phạm vi phòng ban" buộc phải đổi nghĩa thành "phòng mình và các phòng con", và mọi trưởng phòng cấp trên **đột nhiên thấy nhiều chứng từ hơn hôm trước** — một thay đổi hành vi trên hệ chạy thật, sinh ra từ một việc của HRM |
| **Q2** | Phạm vi phòng ban so theo **tên** hay theo **id** | **Theo `dept_id`** | Thành hạng mục **H16**. Làm cùng đợt với H1 |
| **Q3** | Endpoint xuất dữ liệu xử lý thế nào | **Kiểm quyền `export` bắt buộc, và ghi nhật ký mỗi lần xuất** | Vào H4 phần (b) và (c), và vào lớp xuất tệp dùng chung ở H3 |
| **Q4** | Phân quyền mức trường có làm không | **Có** | Thành hạng mục **H15**, đặt ở V0-c, chặn N2 |

### Ba câu hỏi còn chờ, đã ghi vào [`04` Danh mục chờ quyết](./04-danh-muc-cho.md)

| # | Câu hỏi | Ai quyết | Mặc định nếu quá hạn |
|---|---|---|---|
| C12 | Chuẩn hóa trạng thái áp cả bảng cũ hay chỉ bảng mới | Đội phần mềm | Chỉ áp bảng mới, bảng cũ chuyển dần theo module |
| **C13** | Một người làm nhiều pháp nhân thì **một hồ sơ hay nhiều hồ sơ** | Nhân sự + Ban điều hành | Một hồ sơ gắn nhiều pháp nhân, vì gộp dễ hơn tách |
| **C14** | Bản 1 chạy thật cho **mấy pháp nhân** | Ban điều hành | Khai đủ cấu trúc nhiều pháp nhân, bản 1 chạy một |

**C13 và C14 không sửa lại được sau khi đã nhập dữ liệu.** Đây là hai câu đáng hỏi sớm nhất.

**Quan hệ với [`01`](./01-ngan-han-2026.md):** `01` chia việc theo lịch nửa tháng và mã việc; tài liệu này mở chi tiết hai bước trong đó. Chỗ nào lệch thì lấy tài liệu này vì nó viết sau và có đọc mã nguồn. Bốn chỗ lệch đã sửa sang `01` bản 1.1 (11/08/2026); H2 và H3 đã thành mã việc trong `01` bản **1.2** (12/08/2026). Ghi đầy đủ ở [`05` Lịch sử thay đổi](../05-lich-su-thay-doi.md).

**`01` đã cập nhật xong theo bản 2.1 này** — [`01` bản 1.4](./01-ngan-han-2026.md), cùng ngày 12/08/2026: H4a thành **PQ11** (có hàng riêng "ngay bây giờ" đứng trước cả bảng lịch), H15 thành **PQ12** (chặn HR1 và HR3), H16 thành **DB15** (chặn DUY2 và HR6); DB10 sửa lên 42 bảng và chia thành nhiều đợt; cây phòng ban bỏ khỏi HR1, HR6 và điều kiện vào của bước 3b, kèm một dòng ở mục "Không làm trong năm nay"; thêm hai rủi ro **R8** (lịch chưa trừ phần bảo trì Thu mua — C15) và **R9** (ước lượng dựa trên số đếm sai đơn vị).

**`01` cũng đã cập nhật xong theo bản 2.2 này** — [`01` bản 1.5](./01-ngan-han-2026.md), cùng ngày 12/08/2026: PQ11 thêm phần (d) là lỗi tra sai khóa trong cấu hình phạm vi; H17 thành **PQ13** và H18 thành **PQ14**, cả hai xếp vào hàng "ngay bây giờ"; thêm **LC6** (gói ngữ cảnh yêu cầu ở `core/deps.py`) vào mục 4.2 và **HT13** (middleware vòng đời yêu cầu và nhật ký truy cập, **đứng trước PQ11 phần bật chặn `export`**); "Sáu việc chặn HRM" thành **tám**; thêm rủi ro **R10** (cấu hình bảo mật có màn hình nhưng không có tác dụng); sửa số đếm sai ở LC1 (`error()` gọi **0** lần trong module, không phải 2).

**Còn lại, chưa làm:** tính lại lịch mục 10 của `01` sau khi C15 có câu trả lời. Đây là việc của người chủ trì, không phải của đội phần mềm.

**Ánh xạ mã việc** — `06` nói bằng H và N, `01` nói bằng mã việc:

| `06` | `01` bản 1.5 |
|---|---|
| H1 bỏ tiếng Việt | DB3 |
| H2 enum một chỗ | DB14 |
| **H3 lớp dùng chung** | LC1–LC6 (mục 4.2) |
| H4 phạm vi dữ liệu | PQ4, PQ5, PQ6, **PQ11** |
| H5 middleware và bảo mật | PQ9, HT10, **HT13** |
| H6 bộ máy duyệt | DUY1–DUY6 (bước 3b) |
| H7 đa pháp nhân | DB4, DB5, DB10–DB13 |
| H8 bộ đệm | PQ10 |
| H9 tác vụ nền | HT4 |
| H10 webhook | WH1–WH11 |
| H11 giám sát | HT1, HT3 |
| H12 migration | HT9 |
| H13 kiểm thử nền | HT2, PQ6 |
| H14 khung giao diện | FE1–FE12 |
| **H15 phân quyền mức trường** | **PQ12** |
| **H16 phòng ban theo id** | **DB15** |
| **H17 tệp đính kèm qua kiểm quyền** | **PQ13** — hạng mục mới ở bản 2.2 |
| **H18 nhật ký thao tác có quyền và có phạm vi** | **PQ14** (phần chặn quyền) + **HT13** (phần nhật ký truy cập) — hạng mục mới ở bản 2.2 |
| N1 cơ cấu tổ chức và hồ sơ | HR1, HR5, HR12 |
| N2 hợp đồng và quyết định | HR2, HR3, HR4 |
| N3 đơn từ | HR8, HR9 |
| N4 chấm công | HR10 |
| N5 đánh giá, tuyển dụng | Chưa có mã |

**Không đụng tới:** [`02` Dài hạn](./02-dai-han.md) giữ nguyên — tài liệu này nằm gọn trong vòng 1 của nó. [`03` Câu hỏi khảo sát](./03-cau-hoi-khao-sat-hrm.md) chỉ nên thêm hai câu về đa pháp nhân (C13, C14).
