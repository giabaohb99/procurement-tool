# DANH SÁCH TASK CỦNG CỐ CODE BASE

Bản **1.1** — 12/08/2026 (bản 1.0 cùng ngày). Đọc mã nguồn nhánh `bao` ngày 12/08/2026.

Bản 1.1 điền mã việc thật vào cột **Mã cũ** sau khi các phát hiện ở mục 2 đã được gộp về [`06` bản 2.2](./06-lo-trinh-nen-tang-va-hrm.md) và [`01` bản 1.5](./01-ngan-han-2026.md), và **đính chính hai chỗ** ở mục 2.2 và 2.5 — xem chi tiết tại chỗ.

Tài liệu này là **bản thực thi** của phần gia cố nền trong [`06`](./06-lo-trinh-nen-tang-va-hrm.md). `06` nói *cần gì và vì sao*; tài liệu này nói *làm gì, theo thứ tự nào, và căn cứ vào đâu để nói là xong*.

Mỗi task có **điều kiện cần** (chưa có thì không bắt đầu được) và **điều kiện đủ** (bằng chứng kiểm chứng lại được — không nhận "đã code xong" làm bằng chứng).

Cột **Mã cũ** để tra ngược sang [`06`](./06-lo-trinh-nen-tang-va-hrm.md) (mã H) và [`01`](./01-ngan-han-2026.md) (mã PQ/DB/LC/HT). Từ bản 1.1, **không còn ô nào ghi "mới"** — mọi task đều đã có mã ở hai tài liệu gốc, tức là đều nằm trong lịch của một ai đó.

---

## 1. Số đo hiện trạng — 12/08/2026

Đếm trên `backend/app`, nhánh `bao`.

| Chỉ số | Giá trị | Ý nghĩa |
|---|---|---|
| Dòng Python backend | 20.674 | |
| Module | 36 · 34 controller · 29 service | |
| Endpoint | **265** | đếm decorator route trong `app/modules` |
| Endpoint có `require(...)` | 203 | 62 endpoint còn lại **đều có** `get_current_user`, không có endpoint nào công khai ngoài đăng nhập |
| Endpoint đọc (GET) | 97 | |
| Chỗ gọi `apply_scope` | **38** | khoảng cách 97 với 38 là lỗ hổng phạm vi tầng hai |
| Entity khai `SCOPE_FIELDS` | **9/28** | 19 entity còn lại không lọc phạm vi theo chiều nào |
| Chỗ gọi `get_perm_profile` thủ công | 42 | |
| `raise HTTPException` | **259** | đều sập về một mã lỗi duy nhất |
| Module `import error` từ `core.response` | **0** | hàm lỗi dùng chung chỉ được dùng ở 2 handler trong `main.py` |
| `success(...)` | 267 | vỏ trả về thì thống nhất tốt |
| Module dùng `make_crud_router` | **1/36** (`catalog`) | |
| Tự khai phân trang · tự `offset/limit` | 25 · 23 | |
| Tự `.count()` · tự `raise 404` · tự ghi nhật ký | 50 · 53 · 92 | |
| Middleware | **1** (CORS) | |
| Route có giới hạn tần suất | **4/265** | `default_limits` khai nhưng không có hiệu lực |

---

## 2. Phát hiện mới ngày 12/08/2026 — chưa có trong `06` bản 2.1

Sáu mục dưới đây tìm ra khi đọc lại mã nguồn. Bốn mục đầu **đang hở trên hệ chạy thật**.

> **Đã gộp về `06` và `01`, cùng ngày.** Mục 2.1 vào **H4(a)** / **PQ11(d)**; mục 2.2 thành **H17** / **PQ13**; mục 2.3 thành **H18** / **PQ14**; mục 2.4 vào **H3** / **LC4 phần vá**; mục 2.5 sửa số đếm ở `06` mục 3.1 và `01` LC1. `06` lên bản **2.2**, `01` lên bản **1.5**. Mục này giữ nguyên làm bản ghi phát hiện gốc, có mã nguồn cụ thể để tra lại.

### 2.1. Loại trừ phòng ban và nhân sự trên entity nhân sự bị bỏ qua im lặng

`_explicit_cond` và `_dept_include_cond` (`core/scoping.py`) tra tên cột qua khóa **`dept_name`**. `SCOPE_FIELDS["employee"]` chỉ khai `dept_id`, không khai `dept_name`. Vòng lặp gặp `col = None` thì `continue`.

Hậu quả: cấu hình **"phòng ban không được xem"** và **"phòng ban được xem"** trên màn hình phân quyền **không có tác dụng gì** với dữ liệu nhân sự. Chiều `employee` cũng vậy — nó tra `f.get("owner")`, mà entity nhân sự khai `self` chứ không khai `owner`.

Người quản trị bấm cấu hình, hệ thống báo lưu thành công, và người ta tin là đã cấm. Đây là kiểu lỗi tệ nhất: **cấu hình bảo mật có giao diện nhưng không có hiệu lực.**

### 2.2. Tệp đính kèm tải được mà không cần quyền

`main.py` mount `StaticFiles` tại `/api/uploads` **không có dependency nào**. Khóa tệp có cấu trúc đoán được: `prod/attachment/2026/07/123-hop_dong.pdf` (`core/storage.py`, hàm `dated_key`). Bản chạy thật dùng R2 với địa chỉ công khai nên cùng tính chất.

Hậu quả: hợp đồng, hóa đơn, giấy tờ tùy thân — ai có đường dẫn là tải được, **không cần đăng nhập**, kể cả người đã nghỉ việc còn giữ link cũ. Không có dấu vết nào ghi lại việc tải.

*Đính chính về mức mới, ghi cùng ngày:* thư mục tệp tĩnh này **không phải phát hiện hoàn toàn mới** — `06` bản 2.1 hàng 14 của bảng chấm điểm đã ghi "còn một thư mục tệp tĩnh phục vụ trực tiếp không kiểm quyền", nhưng chấm mức **Tạm** và không có hạng mục nào làm. Phần thật sự mới, và là phần khiến mức bị hạ xuống **Thiếu**: `upload_fileobj` trả về **URL công khai vĩnh viễn** và URL đó **lưu thẳng vào cơ sở dữ liệu**, còn `presigned_url` — cái mà hàng 14 mô tả là "liên kết ký hạn 10 phút" — **chỉ được dùng ở một chỗ duy nhất** là tải bản sao lưu (`modules/backup/controller.py`). Nghĩa là mô tả ở bản 2.1 nói về một cơ chế theo thứ nó *có thể* làm được, không phải theo thứ nó *đang* làm.

### 2.3. Nhật ký thao tác đọc tự do

`modules/audit/controller.py` chỉ đặt `get_current_user`, không `require`, không phạm vi. Tham số `entity_id` bỏ trống thì lấy log của **mọi bản ghi** thuộc entity đó. Bất kỳ tài khoản nào đăng nhập cũng đọc được toàn bộ dấu vết thao tác của mọi phòng ban.

### 2.4. `make_crud_router` chưa có phạm vi, chưa đúng quyền, và có một lỗi thật

`core/crud.py`:
- `list`, `get/{id}`, `export/csv` **không gọi `apply_scope`** ở bất kỳ đâu.
- `export/csv` đòi quyền `read`, không đòi `export`.
- `import/csv` đòi quyền `write` vì hành động `import` chưa tồn tại.
- Nhập CSV **không ghi nhật ký**, **không giới hạn số dòng**, chạy trọn một transaction.
- **Lỗi thật:** nhánh nhập CSV gọi `generate_code` nhưng hàm này chỉ được import trong phạm vi `create_item`. Nhập tệp thiếu mã mà entity có `code_prefix` sẽ `NameError`.

Đây là điểm nguy hiểm nhất cho hướng "viết lớp chung rồi kế thừa": **lớp chung đang thủng, kế thừa nó là nhân lỗ hổng ra 36 module thay vì 1.** Bắt buộc sửa factory trước, chuyển module sau.

### 2.5. 259 chỗ báo lỗi đều sập về một mã

Handler trong `main.py` đặt `code=str(status_code)`. Mọi lỗi nghiệp vụ khác nhau đến tay frontend đều là `code: "400"` kèm một chuỗi tiếng Việt. Frontend muốn xử lý riêng một tình huống thì phải so khớp chuỗi tiếng Việt — đổi chữ trong thông báo là frontend hỏng.

Đây là lý do thật sự phải gom hàm lỗi dùng chung. *(Đính chính, ghi cùng ngày: bản 1.0 của tệp này viết rằng `06` mục 3.1 đang nêu lý do yếu là "đỡ lặp code". Đọc lại thì **không phải** — mục 3.1 của `06` đã nêu đúng lý do này rồi. Chỗ thật sự sai ở `06` và `01` chỉ là con số: cả hai ghi `error()` "gọi đúng **2 lần** trong 36 module", đếm lại là **0** — hai chỗ dùng nó nằm ở `main.py`, tức ở bộ xử lý lỗi chứ không phải ở module. Đã sửa ở `06` bản 2.2 và `01` bản 1.5.)*

### 2.6. Hồ sơ quyền đã có sẵn `dept_id`

`get_perm_profile` (`core/auth.py`) đã trả cả `dept_id` lẫn `dept_name`. Nên việc chuyển phạm vi phòng ban sang id (H16/DB15) **nhỏ hơn ước lượng cũ**: chỉ còn thêm cột vào 3 bảng chứng từ và đổi thứ tự ưu tiên trong `_role_scope_cond` — hiện `dept_name` nằm ở nhánh `if` nên luôn thắng `dept_id` ở nhánh `elif`.

---

## 3. Đánh giá tầng middleware

Toàn bộ tầng middleware là **một cái**: CORS. Ngoài ra có 2 handler lỗi và 1 mount tệp tĩnh.

Điểm đáng chú ý nhất là thứ **trông như có mà không chạy**: `core/limiter.py` khai `default_limits=["300/minute"]` nhưng `SlowAPIMiddleware` **không được add vào app**. Không có middleware đó thì `default_limits` là dòng cấu hình chết — thực tế chỉ 4 route đăng nhập/quên mật khẩu có giới hạn, 261 route còn lại không có.

| Thành phần | Có | Ghi chú |
|---|---|---|
| CORS | Có | Danh sách địa chỉ khai trong `.env`, không dùng `*`. Đúng |
| Vỏ trả về thống nhất | Có | 267 chỗ dùng `success(...)`. Điểm mạnh của code base này |
| Handler `HTTPException`, lỗi validate | Có | |
| Handler **lỗi chưa bắt** | **Không** | Lỗi 500 trả `{"detail": ...}`, **sai vỏ** mà frontend đang dựa vào |
| Mã định danh request | **Không** | Người dùng đọc lỗi qua điện thoại thì không tra ngược được |
| Nhật ký truy cập | **Không** | Không biết ai đang gọi endpoint nào → **không khảo sát được trước khi siết quyền** |
| Giới hạn tần suất toàn cục | **Không** | 4/265 route |
| Giới hạn kích thước body/tệp ở tầng chung | **Không** | Mỗi endpoint tự lo, tức là có chỗ không lo |
| Header bảo mật | **Không** | |
| Nén phản hồi | **Không** | Danh sách 5.000 dòng cho dropdown gửi thô |
| Thu hồi token | **Không** | Khóa tài khoản xong, token cũ còn dùng được tới 60 phút |

---

## 4. Thiết kế lớp dùng chung

Yêu cầu: gom hàm kiểm quyền và hàm dựng truy vấn về một chỗ, rồi cho module kế thừa.

**Nguyên tắc quyết định toàn bộ thiết kế:** không làm hàm tiện ích để người ta *gọi cho gọn* — vì gọi hay không vẫn tùy người viết, mà quên là lỗ hổng. Phải làm cho **con đường lấy dữ liệu duy nhất đã bao gồm phạm vi**; muốn bỏ qua thì phải khai rõ ràng `public=True`. Khi đó "quên" không còn là một khả năng, và bài kiểm ở CC-19 chỉ cần tìm những chỗ khai `public=True` mà không có lý do.

### Bốn tệp mới trong `app/core/`

| Tệp | Nội dung | Thay cho |
|---|---|---|
| `errors.py` | `AppError(code, message, status)` + bảng mã lỗi. Mã ổn định, không đổi theo câu chữ tiếng Việt | 259 chỗ `raise HTTPException` |
| `deps.py` | Một dependency `ctx(entity, action)` trả về `Ctx(user, db, profile, entity)` — kiểm quyền **và** mang sẵn hồ sơ quyền | `require(...)` + 42 chỗ tự gọi `get_perm_profile` |
| `repository.py` | `list_query(ctx, Model, request, filterable=..., ranges=..., public=False)` → **tự áp `apply_scope`**, tự lọc, tự sắp xếp, tự phân trang, trả `(total, items)` | 25+23+50+38 chỗ rời rạc |
| `base_service.py` | `get_or_404`, `create`, `update`, `delete` — **tự ghi nhật ký**, tự kiểm phạm vi trước khi cho sửa | 53 chỗ `raise 404` + 92 chỗ tự ghi nhật ký |

### Hình dạng trước và sau

Trước — mẫu đang lặp ở 25 controller:

```
@router.get("")
def list_items(request, pg=Depends(pagination), db=Depends(get_db),
               user=Depends(require("purchase_order", "read"))):
    q = db.query(PO)
    q = apply_filters(q, PO, request, FILTERABLE)
    q = apply_scope(q, PO, "purchase_order", user, get_perm_profile(db, user))   # quên dòng này là hở
    total = q.count()
    q = apply_sort_from_request(q, PO, request)
    items = q.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [out(i) for i in items]})
```

Sau:

```
@router.get("")
def list_items(request, c: Ctx = Depends(ctx("purchase_order", "read"))):
    total, items = list_query(c, PO, request, filterable=FILTERABLE, ranges=["order_date"])
    return success({"total": total, "items": [out(i) for i in items]})
```

Phạm vi không còn là một dòng có thể quên. Nó nằm bên trong `list_query`, và `list_query` là đường duy nhất để lấy danh sách.

### Thứ tự bắt buộc

`errors.py` → `deps.py` → `repository.py` → `base_service.py` → **viết lại `make_crud_router` trên bốn lớp đó** → mới chuyển module theo đợt.

Không được đảo: chuyển module trước khi vá factory là nhân lỗ hổng ra 36 chỗ.

---

## 5. Danh sách task

### Đợt 0 — đang hở, làm ngay, không chờ duyệt lộ trình

| Mã | Việc | Điều kiện cần | Điều kiện đủ | Cỡ | Mã cũ |
|---|---|---|---|---|---|
| **CC-01** | Thêm `apply_scope` vào các endpoint đọc nhân sự còn thiếu: `GET /api/employees/{id}`, `GET /api/employees/export/csv` | — | Tài khoản phòng A gọi id của người phòng B nhận 404; xuất CSV không còn dòng nào của phòng B; test khóa lại cả hai | Nhỏ | H4a · PQ11a |
| **CC-02** | Sửa `_explicit_cond` và `_dept_include_cond` tra cột theo **chiều** chứ không theo khóa `dept_name`; khai `dept_id` cho các chiều còn thiếu | — | Đặt loại trừ "phòng Kế toán" cho một tài khoản → tài khoản đó **thật sự** không thấy nhân sự phòng Kế toán; test cho cả 4 tổ hợp include/exclude × phòng ban/nhân sự | Nhỏ | H4a · **PQ11d** |
| **CC-03** | Tệp đính kèm phải qua kiểm quyền: bỏ mount tĩnh công khai, tải tệp đi qua endpoint có `require` + `apply_scope` theo chứng từ gắn tệp; R2 chuyển sang địa chỉ ký có hạn giờ | — | Dán đường dẫn tệp vào trình duyệt ẩn danh → bị từ chối; người không có quyền đọc chứng từ gốc cũng không tải được tệp của nó; mỗi lượt tải ghi một dòng nhật ký | Vừa | **H17 · PQ13** |
| **CC-04** | `/api/audit-logs`: thêm `require("audit","read")`, áp phạm vi, và **cấm bỏ trống `entity_id`** trừ khi có phạm vi toàn hệ | — | Tài khoản thường gọi endpoint nhận 403; tài khoản có quyền nhưng phạm vi phòng ban chỉ thấy log của chứng từ trong phạm vi mình | Nhỏ | **H18 · PQ14** |
| **CC-05** | Bắt buộc quyền `export` ở 11 endpoint xuất/nhập; thêm hành động `import`; mỗi lần xuất ghi một dòng nhật ký (ai, lúc nào, bảng nào, bao nhiêu dòng, bộ lọc gì) | CC-01 | Không có quyền `export` thì mọi đường xuất trả 403; xuất một lần rồi truy ra được đúng dòng nhật ký tương ứng | Nhỏ | H4b/c · PQ11b/c |
| **CC-06** | Chuyển bộ đệm quyền sang Redis, xóa đệm là xóa cho mọi tiến trình | — | Rút quyền một người → **cả hai tiến trình** đều mất quyền trong vài giây, kiểm bằng gọi lặp | Nhỏ | H8 |

> **Trước khi bật CC-05, phải khảo sát ai đang xuất dữ liệu.** Hiện không có nhật ký truy cập nên chưa khảo sát được. Cách làm: triển khai CC-13 trước, chạy thu thập 2 tuần, đọc xem ai đang gọi các endpoint xuất, cấp phạm vi đúng người, rồi mới siết. Siết trước khi khảo sát là cắt việc của người đang làm thật mà không ai biết vì sao.

### Đợt 1 — trục dùng chung

| Mã | Việc | Điều kiện cần | Điều kiện đủ | Cỡ | Mã cũ |
|---|---|---|---|---|---|
| **CC-07** | `core/errors.py`: lớp `AppError` + bảng mã lỗi ổn định; handler trả đúng mã thay vì `str(status_code)` | — | Frontend bắt được một tình huống nghiệp vụ **bằng mã**, không so khớp chuỗi tiếng Việt; đổi câu chữ thông báo không làm frontend hỏng | Nhỏ | H3 · LC1 |
| **CC-08** | `core/deps.py`: dependency `ctx(entity, action)` trả `Ctx(user, db, profile, entity)` | CC-07 | Một endpoint mẫu dùng `Ctx` không còn gọi `get_perm_profile` thủ công; hồ sơ quyền lấy đúng một lần mỗi request | Nhỏ | H3 · **LC6** |
| **CC-09** | `core/repository.py`: `list_query` **tự áp `apply_scope`**, có tham số `public=True` để khai ngoại lệ | CC-08 | Viết một endpoint danh sách mới mà **không viết dòng phạm vi nào** thì dữ liệu vẫn bị lọc đúng; khai `public=True` thì bài kiểm ở CC-19 bắt được và đòi lý do | Vừa | H3 · LC2 |
| **CC-10** | `core/base_service.py`: `get_or_404`, `create/update/delete` tự ghi nhật ký và tự kiểm phạm vi trước khi cho sửa | CC-09 | Sửa một bản ghi ngoài phạm vi của mình bị chặn **ở tầng service**, không phụ thuộc controller nhớ kiểm; nhật ký sinh ra tự động, không phải gọi tay | Vừa | H3 · LC3 |
| **CC-11** | Viết lại `make_crud_router` trên 4 lớp trên: có phạm vi, `export/csv` đòi quyền `export`, `import/csv` đòi `import`, ghi nhật ký khi nhập, giới hạn số dòng, **và vá lỗi `generate_code`** | CC-10 | Kiểm nhập một tệp CSV thiếu mã cho entity có `code_prefix` → chạy được (hiện `NameError`); nhập tệp vượt hạn mức dòng bị từ chối có thông báo rõ; xuất từ factory bị lọc phạm vi | Vừa | H3 · LC4 |
| **CC-12** | Chuyển module sang lớp chung, **mỗi đợt 3–5 module**, mỗi đợt tự bấm lại màn hình liên quan | CC-11 | Sau mỗi đợt: số chỗ tự phân trang / tự `.count()` / tự ghi nhật ký giảm đúng bằng số module đã chuyển; bộ kiểm cũ vẫn xanh | **Lớn** | H3 |

### Đợt 2 — middleware và vòng đời request

| Mã | Việc | Điều kiện cần | Điều kiện đủ | Cỡ | Mã cũ |
|---|---|---|---|---|---|
| **CC-13** | Middleware mã định danh request + nhật ký truy cập có cấu trúc (ai, endpoint, mã trạng thái, thời gian chạy) | — | Người dùng đọc mã lỗi qua điện thoại là tra ra **đúng một dòng** nhật ký; thống kê được endpoint nào đang được ai gọi — đây là đầu vào của CC-05 | Nhỏ | H5 · H11 · **HT13a/c** |
| **CC-14** | Handler cho lỗi chưa bắt: trả đúng vỏ envelope, kèm mã định danh request, **không lộ traceback** ra ngoài | CC-13 | Gây một lỗi 500 cố ý → frontend hiện thông báo có mã tra cứu chứ không phải màn hình trắng; phản hồi không chứa đường dẫn tệp hay tên hàm | Nhỏ | **H5 · HT13b** |
| **CC-15** | Add `SlowAPIMiddleware` cho `default_limits` có hiệu lực; đặt giới hạn riêng cho endpoint nặng (xuất tệp, báo cáo) | — | Gọi vượt ngưỡng một endpoint bất kỳ → bị chặn (hiện chỉ 4 route bị chặn) | Nhỏ | H5 · **HT13d** |
| **CC-16** | Header bảo mật + giới hạn kích thước body và tệp tải lên ở tầng chung | — | Tải tệp vượt hạn mức bị từ chối **trước khi** đọc hết vào bộ nhớ | Nhỏ | H5 |
| **CC-17** | Thu hồi token: thêm định danh vào token, bảng token đã thu hồi, xoay vòng refresh token, nhật ký phiên đăng nhập | CC-06 | Khóa một tài khoản → token cũ **mất hiệu lực ngay**, không đợi 60 phút; dùng lại một refresh token đã xoay bị từ chối | Vừa | H5 |

### Đợt 3 — ràng buộc và kiểm chứng

| Mã | Việc | Điều kiện cần | Điều kiện đủ | Cỡ | Mã cũ |
|---|---|---|---|---|---|
| **CC-18** | Khai đủ phạm vi cho 28 entity; entity cố ý công khai phải khai rõ là công khai; đổi mặc định của `_role_scope_cond` từ "bỏ qua" thành **báo lỗi** | CC-09 | Thêm một entity mới mà quên khai → hệ thống báo lỗi ngay lúc chạy, không im lặng trả hết dữ liệu | Vừa | H4d · PQ11 |
| **CC-19** | Bộ kiểm ràng buộc nền + CI: đặt tên, enum, cột pháp nhân, đủ 28 phạm vi, **mọi endpoint đọc đi qua `apply_scope`**, chuỗi migration | CC-18, CC-20 | **Cố tình vi phạm từng ràng buộc trong một nhánh nháp thì CI phải đỏ đúng ràng buộc đó** — viết test rồi thấy nó xanh chưa chứng minh được gì | Vừa | H13 |
| **CC-20** | Bỏ nhánh tạo bảng thẳng từ model; CI dựng cơ sở dữ liệu trống rồi chạy đủ chuỗi migration từ đầu | — | Lược đồ sinh ra từ chuỗi migration **so khớp** với lược đồ bản chạy thật, không lệch cột nào | Nhỏ | H12 |
| **CC-21** | Enum khai một chỗ, sinh sang frontend, CI so lại | CC-19 | Sửa một trạng thái ở máy chủ mà quên chạy lại kịch bản sinh → CI hỏng | Nhỏ | H2 |

### Đợt 4 — dữ liệu

| Mã | Việc | Điều kiện cần | Điều kiện đủ | Cỡ | Mã cũ |
|---|---|---|---|---|---|
| **CC-22** | Phạm vi phòng ban theo `dept_id`: thêm cột vào 3 bảng chứng từ, nạp ngược theo tên, tên không khớp thì để rỗng và ghi bảng lỗi, đổi thứ tự ưu tiên trong `_role_scope_cond` | CC-19, CC-20 | **Đối chiếu số dòng thấy được theo cột cũ và cột mới bằng nhau** trên toàn bộ dữ liệu thật; bảng lỗi nạp ngược được người phòng Thu mua xác nhận từng dòng; đổi tên một phòng trên dev thì chứng từ cũ vẫn trong phạm vi | Nhỏ *(nhỏ hơn ước cũ — hồ sơ quyền đã có `dept_id`)* | H16 · DB15 |
| **CC-23** | Bỏ tiếng Việt khỏi cơ sở dữ liệu — 11 cột, mỗi cột đủ sáu bước | CC-19, CC-20 | Chạy song song hai cột rồi mới bỏ cột cũ; không có bước nào đọc cột cũ còn sót | **Lớn** | H1 |
| **CC-24** | Thêm `company_id` cho 42/57 bảng còn thiếu, **chia đợt theo module** | CC-19, CC-20 | Mỗi đợt: tạo chứng từ ở pháp nhân B không thấy dữ liệu pháp nhân A, trừ chỗ cố ý dùng chung; chỗ không suy được pháp nhân thì để rỗng và ghi lại, **không gán bừa** | **Lớn** | H7 |

### Đợt 5 — chỉ cần khi thành ERP

| Mã | Việc | Điều kiện cần | Điều kiện đủ | Cỡ | Mã cũ |
|---|---|---|---|---|---|
| **CC-25** | Bộ máy duyệt dùng chung | CC-18, CC-24 | Chuyển **một** loại chứng từ Thu mua đang chạy sang làm mẫu, có đường lui; thêm loại mới chỉ là khai cấu hình | **Lớn** | H6 |
| **CC-26** | Phân quyền mức trường, lọc ở lớp schema đầu ra | CC-09, CC-18 | Trường bị che **không có mặt trong JSON**; kiểm cả đường xuất tệp và webhook, không chỉ đường JSON | Vừa | H15 · PQ12 |
| **CC-27** | Khung giao diện nhiều phân hệ | CC-19, CC-20 | Người dùng Thu mua đăng nhập vẫn vào thẳng việc cũ, đường dẫn cũ không đổi | Vừa | H14 |
| **CC-28** | Webhook và API ra ngoài | CC-19 | Một hệ thống ngoài đăng ký nhận sự kiện và nhận đủ, có bằng chứng ở nhật ký | Vừa | H10 |
| **CC-29** | Tách hàng đợi tác vụ nặng/nhẹ, cảnh báo khi hỏng | — | Tác vụ hỏng là có người biết trong vòng vài phút | Nhỏ | H9 |
| **CC-30** | Giám sát và cảnh báo khi tỷ lệ lỗi vọt | CC-13 | Có chỉ số cơ bản và một ngưỡng cảnh báo chạy thật | Vừa | H11 |

---

## 6. Nếu hướng ERP không được duyệt

Ranh giới này nên nói ra trước khi trình, để người duyệt có thể chọn "chưa làm ERP nhưng cứ củng cố đi" mà không phải bác cả bộ.

| | Task |
|---|---|
| **Vẫn nên làm dù không có ERP** — sửa code base Thu mua đang chạy | CC-01 → CC-23 (trừ CC-24) |
| **Chỉ có nghĩa khi thành ERP** | CC-24 đa pháp nhân · CC-25 bộ máy duyệt · CC-27 khung phân hệ · CC-28 webhook |

---

## 7. Quan hệ với các tài liệu khác

| Tài liệu | Quan hệ |
|---|---|
| [`06` Lộ trình nền tảng và HRM](./06-lo-trinh-nen-tang-va-hrm.md) | Nguồn của các hạng mục H. Tài liệu này là bản thực thi. Mục 2 ở trên là phần bổ sung cho `06` bản 2.1, và **đã được gộp về `06` bản 2.2** thành **H17**, **H18**, cùng các phần thêm vào H3, H4, H5 |
| [`01` Ngắn hạn 2026](./01-ngan-han-2026.md) | Mã PQ/DB/LC/HT và lịch theo nửa tháng. **`01` bản 1.5** đã nhận về: CC-01, CC-02, CC-05 nằm trong **PQ11** (CC-02 là phần (d) mới); CC-03 thành **PQ13**; CC-04 thành **PQ14**; CC-13, CC-14, CC-15 gộp thành **HT13**; CC-08 thành **LC6** |
| [`04` Danh mục chờ quyết](./04-danh-muc-cho.md) | C15 nhân lực — chưa trả lời thì không đặt được lịch cho đợt 1 trở đi |

---

## 8. Việc cần quyết trước khi bắt đầu

| Câu hỏi | Chặn task nào | Ai quyết |
|---|---|---|
| Ai làm, và người đó có được rút khỏi hàng chờ thay đổi của Thu mua không (C15) | Từ đợt 1 trở đi | Người chủ trì |
| Đợt 0 có được làm ngay không, hay chờ duyệt cả lộ trình | CC-01 → CC-06 | Người chủ trì — **khuyến nghị: làm ngay**, vì đây là thứ đang hở, không phải kế hoạch |
| Tệp đính kèm đang có ai dùng đường dẫn trực tiếp không (dán vào chat, gửi mail) | CC-03 | Phòng Thu mua |
