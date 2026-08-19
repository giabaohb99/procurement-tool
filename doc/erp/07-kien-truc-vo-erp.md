# KIẾN TRÚC VỎ ERP — BỌC THU MUA THÀNH MỘT PHÂN HỆ

| | |
|---|---|
| Bản | **1.0 — 12/08/2026** |
| Đối tượng đọc | Đội phần mềm · Gia Bảo · Được · người làm giao diện |
| Trả lời câu hỏi | Biến Thu mua thành một phân hệ của ERP bằng cách nào, mà Thu mua không gián đoạn một phút nào, và hai người làm song song được |
| Chưa có trong bản này | Số người-ngày, ngày giao cam kết, thiết kế màn hình lưới |
| Liên quan | [`01` Ngắn hạn](./01-ngan-han-2026.md) bước 2 · [`06` Lộ trình nền tảng](./06-lo-trinh-nen-tang-va-hrm.md) · [`04` Danh mục chờ quyết](./04-danh-muc-cho.md) |

**Ba câu tóm tắt.** Vỏ ERP là **một lớp thêm vào phía trên**, không phải viết lại phía dưới: 35 module backend và 35 trang giao diện giữ nguyên, không sửa một dòng. Backend thêm ba tệp mới và một endpoint; giao diện thêm ba tệp mới và một trường vào mảng menu đã có sẵn. Toàn bộ nằm sau một cờ tính năng tắt ở bản chạy thật, nên Thu mua không biết có việc gì đang xảy ra cho tới ngày bật cờ.

Tài liệu này là bản chi tiết của **bước 2 trong [`01`](./01-ngan-han-2026.md)**. Chỗ nào lệch với `01` thì lấy `07`, vì `07` viết sau khi đọc lại mã nguồn — danh sách chỗ lệch ở mục 12.

---

## 1. Quyết định: bọc, không tách kho mã

Đã cân nhắc phương án tách mã nguồn Thu mua thành một sản phẩm mới tên ERP rồi sửa song song. **Không chọn.** Ghi lại cả hai để về sau không phải bàn lại.

| | Bọc (chọn) | Tách kho mã (loại) |
|---|---|---|
| Số kho mã, số backend, số cơ sở dữ liệu | 1 · 1 · 1 | 2 · 2 · 1 hoặc 2 |
| Vá lỗi cho Thu mua trong lúc làm | Một lần | **Hai lần**, và số lần tăng dần theo thời gian |
| Đóng băng tính năng Thu mua | Không cần | **Bắt buộc**, mà điều kiện này giữ không nổi |
| Dự án Quản lý dự án đang dùng chung backend | Không ảnh hưởng | Treo ở giữa hai bản |
| Đường lui khi hỏng | Tắt một cờ | Không có |
| Ngày chuyển đổi | Không có ngày chuyển đổi | Một ngày cắt, có di trú dữ liệu |

Lý do quyết định, ngắn gọn: cái cần đạt — lưới biểu tượng, phân hệ theo quyền, thương hiệu ERP — **là một lớp vỏ, không cần thay ruột mới có được**. Tách kho mã trả giá bằng chi phí gộp mã tăng dần, đổi lại một thứ không mua thêm được gì.

---

## 2. Nguyên tắc: chỉ thêm, không sửa

Một câu để kiểm tra mọi thiết kế trong tài liệu này:

> Nếu một việc nào đó **bắt buộc phải sửa vào trang cũ hoặc endpoint cũ** thì vỏ mới mới chạy được, thì việc đó đang thiết kế sai.

Ba hệ quả:

| Được làm | Không được làm |
|---|---|
| Thêm tệp mới ở `core/`, thêm module mới | Sửa nghiệp vụ trong 35 module đang có |
| Thêm endpoint mới | Đổi dạng trả về của endpoint đang có |
| Thêm một trường vào mảng menu khai báo sẵn | Viết lại `AppLayout.tsx` hay `cruds.tsx` |
| Thêm tệp giao diện mới | Đổi đường dẫn URL mà Thu mua đang dùng (mục 7) |

---

## 3. Ba tầng

```
        Lưới biểu tượng phân hệ          <- tầng MỚI (vỏ)
                  |
   +--------------+--------------+
   |              |              |
Thu mua      Nhân sự       Danh mục      <- tầng phân hệ: chỉ là bộ lọc menu
   |              |              |
   +--------------+--------------+
                  |
   35 module backend, 35 trang giao diện  <- tầng CŨ, không đụng
                  |
        Một cơ sở dữ liệu duy nhất
```

Điểm mấu chốt: **tầng phân hệ không phải một lớp mã đứng chen giữa.** Nó là một bộ lọc trên dữ liệu khai báo. Yêu cầu từ trình duyệt đi thẳng từ vỏ xuống endpoint cũ, không qua trung gian nào.

---

## 4. Backend thêm gì

Đúng ba thứ, đều là tệp mới:

| Mã | Tệp | Nội dung | Ước lượng |
|---|---|---|---|
| **FE1** | `app/core/modules.py` | Khai báo phân hệ: mã, tên, biểu tượng, thứ tự, loại, trang chủ, **danh sách entity thuộc phân hệ** | ~70 dòng |
| **PQ1** | `app/modules/module/controller.py` | `GET /api/me/modules` | ~40 dòng |
| **FE8** | `app/main.py` | Thêm một dòng vào 38 dòng gắn router đang có | 1 dòng |

### 4.1 Khung khai báo

```python
class ModuleKind(StrEnum):
    INTERNAL = "internal"      # màn hình nằm trong chính ứng dụng này
    EXTERNAL = "external"      # ứng dụng riêng, tên miền riêng, chung tài khoản

@dataclass(frozen=True)
class Module:
    code: str
    name: str
    icon: str
    order: int
    kind: ModuleKind
    home: str                  # đường dẫn nội bộ, hoặc URL đầy đủ nếu external
    entities: tuple[str, ...]  # entity THUỘC VỀ phân hệ này

MODULES: tuple[Module, ...] = (...)
```

**Kiểm tra lúc khởi động, bắt buộc:** mọi entity trong `ENTITIES` phải thuộc **đúng một** phân hệ. Thiếu hoặc trùng thì ứng dụng không lên. Đây là cùng một triết lý với PQ4 — khai thiếu thì báo lỗi ngay, không im lặng.

### 4.2 Ai thấy phân hệ nào

**Không cần mô hình quyền mới.** Lấy hồ sơ quyền sẵn có; phân hệ nào người dùng có `read` trên **ít nhất một** entity của nó thì hiện.

```python
def visible_modules(profile):
    return [m for m in MODULES if any(can_read(profile, e) for e in m.entities)]
```

Ngày đầu chạy: không ai phải cấp lại quyền, không bảng mới, không migration.

Khi nào cần chặt hơn — ví dụ có `read` nhà cung cấp nhưng không được vào phân hệ Kế toán — lúc đó thêm entity `module` vào `ENTITIES`. **Đó là việc sau, không phải điều kiện để bắt đầu.** Ghi ra đây để khi cần thì biết đường đi, chứ không làm sớm.

### 4.3 Hợp đồng dữ liệu — chốt trước khi ai viết dòng nào

`GET /api/me/modules`, theo đúng vỏ trả về hiện có của hệ thống:

```json
{
  "success": true,
  "message": "OK",
  "data": [
    {
      "code": "thu_mua",
      "name": "Thu mua",
      "icon": "ti-shopping-cart",
      "order": 10,
      "kind": "internal",
      "home": "/"
    },
    {
      "code": "hdsd",
      "name": "Hướng dẫn sử dụng",
      "icon": "ti-help",
      "order": 90,
      "kind": "external",
      "home": "https://help.degoholding.vn"
    }
  ]
}
```

Ba điều đã cân nhắc và cố ý:

| Quyết định | Vì sao |
|---|---|
| Không trả danh sách `entities` xuống giao diện | Giao diện không cần biết; trả ra chỉ tạo thêm một chỗ suy luận quyền ở phía không được tin |
| Không nhét vào phản hồi đăng nhập ở bản 1 | Để endpoint riêng thì thử và làm mới độc lập được. Gộp vào sau vẫn kịp, gộp trước thì mỗi lần sửa phải đụng luồng đăng nhập |
| Chưa có số đếm thông báo trên ô | Thêm được lúc nào cũng được, nhưng nó kéo theo một truy vấn cho mỗi phân hệ ở mỗi lần vào web. Để sau, đo rồi hãy làm |

---

## 5. Chia entity vào phân hệ

Đếm ở `core/permissions.py` ngày 12/08/2026: **28 entity**. (`01` và `06` ghi 29 — lệch một, rà lại khi làm FE1.)

**Một entity thuộc đúng một phân hệ**, nhưng **một phân hệ được hiện màn hình của entity thuộc phân hệ khác**. Quyền sở hữu chỉ quyết định ô nào hiện trên lưới; menu bên trong vẫn khai riêng như hiện nay. Không có quy tắc này thì `inventory` và `supplier` sẽ kẹt vì nhiều phân hệ cùng cần.

| Phân hệ | Mã | Entity thuộc về | Có ô trên lưới ở bản 1 |
|---|---|---|---|
| **Thu mua** | `thu_mua` | purchase_request · survey_request · survey · purchase_order · goods_receipt · payable · payment · payment_request · category_assignee · supplier · contract · report | Có |
| **Danh mục dùng chung** | `danh_muc` | product · unit · item_group · brand · warehouse | Có |
| **Kho** | `kho` | inventory | Có |
| **Nhân sự** | `nhan_su` | employee · department | Có, nhưng bên trong mới có danh sách nhân sự cho tới khi HRM xong |
| **Quản trị hệ thống** | `quan_tri` | company · user · role · setting · backup · import | Có |
| **Hỗ trợ** | `ho_tro` | ticket | Theo cờ tính năng hiện có |
| **Hướng dẫn sử dụng** | `hdsd` | help_article | Có — ứng dụng ngoài |
| **Dự án** | `du_an` | (chưa có entity trong danh sách chung) | Có — ứng dụng ngoài |

Bốn chỗ phải giải thích, vì đọc lướt sẽ thấy lạ:

| Chỗ | Vì sao xếp vậy |
|---|---|
| `supplier`, `contract` thuộc Thu mua | Thu mua là nơi tạo và quản. Kế toán và Sản xuất về sau **đọc** qua menu của họ, không cần đổi chủ sở hữu |
| Danh mục dùng chung tách khỏi Thu mua | Đúng việc **DB8** trong [`01`](./01-ngan-han-2026.md). Đơn vị tính và phân loại là của cả tập đoàn, không phải của Thu mua |
| `warehouse` nằm ở Danh mục, `inventory` nằm ở Kho | Kho là danh mục, tồn kho là số dư biến động. Khi MFM tới, phân hệ Kho là chỗ nó đổ vào |
| `report` thuộc Thu mua | Hiện chỉ có báo cáo mua hàng. Khi có báo cáo liên phân hệ thì tách entity mới, không đổi entity này |

**Đây là bảng phải chốt trước khi hai người bắt đầu.** Đổi sau thì đổi cả lưới, cả menu, cả phân quyền.

---

## 6. Giao diện thêm gì

**Tin tốt:** `NAV_GROUPS` trong `frontend/src/layouts/AppLayout.tsx` dòng 54 đã là mảng khai báo, mỗi mục đã có `entity` và đã tự ẩn theo quyền. Cấu trúc cần cho lưới phân hệ **đã tồn tại sẵn**.

| Mã | Việc | Loại |
|---|---|---|
| **FE2** | `pages/ModuleHub.tsx` — lưới biểu tượng, đọc từ `/api/me/modules` | Tệp mới |
| **FE4** | `layouts/ShellLayout.tsx` — khung ngoài, nút quay về lưới, tên phân hệ đang đứng | Tệp mới |
| **FE15** | `config/modules.mock.json` — bản mô phỏng hợp đồng dữ liệu để làm trước khi có backend | Tệp mới, xóa khi xong |
| **FE4** | Thêm trường `module` vào từng nhóm trong `NAV_GROUPS`; lọc thêm một điều kiện | Sửa mảng khai báo, **không sửa logic** |
| **FE3** | Trang chủ hiện tại thành trang chủ của Thu mua | Đổi tuyến, không sửa nội dung trang |
| **FE13** | Cờ `VITE_ERP_SHELL` trong `config/features.ts` | Thêm một dòng |
| **FE14** | Có đúng một phân hệ thì vào thẳng; nhiều thì hiện lưới; nhớ phân hệ dùng lần trước | Trong FE2 |

**Không viết lại trang nào. Không đụng `config/cruds.tsx` 765 dòng.**

FE7 trong `01` (tách `cruds.tsx` theo phân hệ) **không phải điều kiện của vỏ** — làm khi thêm phân hệ thứ hai thì hợp lý hơn, vì lúc đó mới biết cắt theo đường nào.

### 6.1 FE14 không phải việc phụ

Người chỉ có mỗi Thu mua mà phải bấm thêm một cú mỗi lần vào web, mỗi ngày, mãi mãi — đó là cái giá vỏ ERP bắt người dùng trả mà họ không nhận lại gì. Quy tắc: **một phân hệ thì không hiện lưới.** Nhiều phân hệ thì vào thẳng cái dùng lần trước, có nút đổi.

---

## 7. Đường dẫn URL — không đổi

**Giữ nguyên `/purchase-requests`. Không đổi thành `/thu-mua/purchase-requests`.** Phân hệ là trạng thái giao diện, không phải tiền tố URL.

Lý do đo được: `notification.link` là cột `String(500)` trong cơ sở dữ liệu, đang chứa hàng nghìn đường dẫn thật của thông báo đã gửi. Thông báo đẩy cũng mang đường dẫn. Đổi tiền tố là làm chết toàn bộ thông báo cũ, cộng mọi dấu trang và mọi link trong email đã gửi. Đổi lại được đúng một thứ: URL nhìn cho gọn.

| Trường hợp | Cách làm |
|---|---|
| Màn hình Thu mua đang có | Giữ nguyên đường dẫn, vĩnh viễn |
| **Phân hệ mới (HRM)** | **Có tiền tố ngay từ đầu**: `/nhan-su/ho-so`, `/nhan-su/hop-dong`. Chưa có link cũ nào nên không mất gì |
| Đụng tên entity giữa hai phân hệ | Đây là lý do phân hệ mới phải có tiền tố. Hợp đồng lao động và hợp đồng nhà cung cấp cùng tên `contract` — tiền tố ở phân hệ mới giải quyết xong, không cần đổi bên cũ |

Hệ quả: **FE6 (chuyển hướng đường dẫn cũ) không còn cần trong giai đoạn này.** Không đổi thì không phải chuyển hướng. Đổi lại, FE6 thành một việc nhỏ hơn: kiểm tra một mẫu link cũ lấy từ `notification.link` vẫn mở đúng sau khi bật vỏ.

---

## 8. Cơ chế chạy song song

Không phát minh gì mới — **kho mã này đã làm đúng cách đó một lần rồi**, với phiếu hỗ trợ:

```
export const TICKET_ENABLED = import.meta.env.VITE_FEATURE_TICKET !== 'off'
```

Bản chạy thật đặt `off`, dev bật. Tính năng nằm cùng một nhánh, cùng một bản dựng, người dùng thật không thấy gì. Làm lại đúng khuôn đó với `VITE_ERP_SHELL`.

| Việc | Cách làm |
|---|---|
| Nhánh | **Một nhánh `bao` như hiện tại.** Không có nhánh dài hạn thứ hai. Gộp mã mỗi ngày |
| Bản chạy thật | `main` vẫn nhận vá lỗi và yêu cầu mới bình thường, vì mã vỏ nằm sau cờ tắt |
| Môi trường thử | Bật cờ ở `devthumua.degoholding.vn`, chạy song song hàng tuần trước khi bật thật |
| Tên miền | `erp.degoholding.vn` trỏ về **cùng backend**. `thumua.degoholding.vn` vẫn sống — đó là đường lui |
| Hạn bỏ cờ | Chốt sẵn: bật thật xong **một tháng** thì xóa cờ và xóa nhánh mã cũ. Cờ để lâu thành hai bản mã trong một tệp |

Tiền lệ đã có trong nhà: **Quản lý dự án dùng chung backend và cơ sở dữ liệu với Thu mua**, chạy container giao diện riêng, tên miền riêng. Vỏ ERP còn đơn giản hơn — cùng backend, cùng giao diện, chỉ thêm một tên miền.

### 8.1 Mặt tiếp giáp giữa hai người: đúng hai tệp

Đây là chỗ quyết định song song có trôi hay không.

| Tệp | Ai định nghĩa | Chốt khi nào |
|---|---|---|
| Dạng trả về của `/api/me/modules` (mục 4.3) | Backend | **Ngày đầu**, trước khi ai viết dòng nào |
| `frontend/src/config/enums.ts` sinh từ `core/enums.py` (DB14) | Backend | Trước khi giao diện đụng vào chỗ hiển thị trạng thái |

Chốt xong dạng dữ liệu, người làm giao diện **mô phỏng bằng `config/modules.mock.json`** (FE15) và làm trọn lưới phân hệ mà không chờ backend. Khi endpoint thật lên, đổi một dòng gọi API. Đó là lý do hai người không chặn nhau.

Ngược lại: cho làm giao diện trước khi chốt hai tệp này thì người đó viết dựa trên định dạng lỗi cũ và chuỗi trạng thái tiếng Việt — **cả hai đều nằm trong danh sách sắp sửa** (LC1 và DB14 ở [`01`](./01-ngan-han-2026.md)). Viết xong rồi sửa lại toàn bộ.

### 8.2 Chia việc

| Backend (Gia Bảo) | Giao diện (đồng nghiệp) |
|---|---|
| LC1 hàm trả lỗi chung | FE2 lưới phân hệ, FE4 khung vỏ |
| `core/enums.py` + sinh `enums.ts` (DB3, DB14) | FE14 luồng vào: một phân hệ thì vào thẳng |
| FE1 `core/modules.py` + PQ1 endpoint | FE4 thêm trường `module` vào `NAV_GROUPS` |
| **PQ4, PQ5 vá lỗ hổng phạm vi dữ liệu** | Dọn 9 tệp chép cứng chuỗi trạng thái, sau khi có `enums.ts` |

Việc cuối cột trái là việc gấp nhất trong bảng, và **nó không liên quan gì tới ERP** — đó là lỗ hổng đang có trên bản chạy thật ngay lúc này. Xem [`06`](./06-lo-trinh-nen-tang-va-hrm.md) R5.

### 8.3 Thứ tự

| Nhịp | Backend | Giao diện |
|---|---|---|
| Ngày đầu | Chốt mục 4.3 và mục 5 | Chốt cùng, rồi viết FE15 mô phỏng |
| Nửa đầu T9 | FE1, PQ1, FE8. LC1. DB3, DB14 | FE13 cờ, FE2, FE3 |
| Nửa sau T9 | PQ2 ẩn ô theo quyền | FE4, FE14, FE10a–FE10e |
| Nửa đầu T10 | PQ3 màn phân quyền gom theo phân hệ | FE11 tài liệu, FE12 báo trước người dùng |

Khớp với lịch ở [`01` mục 10](./01-ngan-han-2026.md), không thêm nhịp mới.

---

## 9. Đường lui

Ba mức, tính bằng phút:

| Hỏng gì | Làm gì | Mất bao lâu |
|---|---|---|
| Vỏ mới hiển thị sai | Đặt `VITE_ERP_SHELL=off`, dựng lại giao diện | Vài phút. Menu cũ trở lại y nguyên |
| `/api/me/modules` lỗi | Không nằm trong luồng nghiệp vụ nào. Lưới không hiện, các trang vẫn vào được bằng đường dẫn trực tiếp | Không cần làm gì gấp |
| Tên miền mới có vấn đề | Người dùng quay về `thumua.degoholding.vn` | Ngay |

Phương án tách kho mã không có mức nào trong ba mức này.

---

## 10. Xong là thế nào

Toàn bước coi là đạt khi đủ sáu điều, kiểm được chứ không phải nhận xét:

1. Tài khoản chỉ có quyền Thu mua: đăng nhập vào **thẳng** Thu mua, không thấy lưới, màn hình y hệt hôm nay.
2. Tài khoản có nhiều phân hệ: thấy lưới, chỉ thấy ô mình có quyền, bấm vào đúng chỗ, quay về lưới được.
3. Mở một link cũ lấy từ `notification.link` trong cơ sở dữ liệu thật: vẫn vào đúng màn hình.
4. Tắt cờ `VITE_ERP_SHELL`: mọi thứ trở lại hệt trước, không sót dấu vết.
5. Thêm một entity mới vào `ENTITIES` mà quên xếp vào phân hệ: **ứng dụng không khởi động được**.
6. Suốt thời gian làm, Thu mua trên bản chạy thật **không có một lần gián đoạn nào** — kiểm bằng nhật ký triển khai, không bằng trí nhớ.

---

## 11. Sáu rủi ro

| # | Rủi ro | Xử lý |
|---|---|---|
| V1 | **Giao diện bắt đầu trước khi chốt hai tệp ở mục 8.1** — viết xong phải sửa lại toàn bộ chỗ đọc lỗi và chỗ so trạng thái | Chốt mục 4.3 và mục 5 ngay ngày đầu. Đây là việc của một buổi, không phải một tuần |
| V2 | **Lưới thành cú nhấp thừa mỗi ngày** cho người chỉ dùng Thu mua | FE14 là bắt buộc, không phải tính năng thêm |
| V3 | **Ô phân hệ hiện ra nhưng bên trong trống** — người có `read` đúng một entity lẻ | Ô chỉ hiện khi có **ít nhất một màn hình vào được**, không phải khi có ít nhất một entity đọc được. Kiểm ở tiêu chí 2 |
| V4 | **Chuyển tiếp đăng nhập giữa ba ứng dụng** — sang Hướng dẫn sử dụng hoặc Dự án bị bắt đăng nhập lại | FE10d. Phải thử trước khi bật, vì đây là thứ người dùng gặp ngay lần đầu |
| V5 | **Cờ tính năng để quá lâu** thành hai bản mã trong một tệp, rồi không ai dám xóa | Chốt hạn bỏ cờ ngay từ đầu: một tháng sau khi bật thật |
| V6 | **Vỏ xong rồi bên trong vẫn là Thu mua, lãnh đạo hỏi "thế ERP đâu"** | Nói trước ngay từ đầu: bước này đổi **cửa vào**, không thêm nghiệp vụ. Nghiệp vụ mới là HRM ở bước 4. Không hứa nhầm |

---

## 12. `07` sửa gì so với `01`

**Đã gộp hết vào [`01` bản 1.3](./01-ngan-han-2026.md) ngày 12/08/2026.** Bảng dưới giữ lại để ai đọc `01` bản 1.2 thì tra được.

| Chỗ | `01` bản 1.2 | `07`, nay là `01` bản 1.3 |
|---|---|---|
| **FE5** đường dẫn có tiền tố phân hệ | Đổi hết sang `/thu-mua/...`, tuyến bắt-tất-cả thành `:module/:entity` | **Chỉ phân hệ mới có tiền tố.** Thu mua giữ nguyên đường dẫn vĩnh viễn. Lý do ở mục 7 |
| **FE6** chuyển hướng đường dẫn cũ | Một việc riêng, phải làm | **Không còn cần** — không đổi thì không phải chuyển hướng. Thu lại thành một phép thử ở tiêu chí 3 |
| **FE7** tách `cruds.tsx` | Nằm trong bước 2 | Không phải điều kiện của vỏ. Để tới khi thêm phân hệ thứ hai |
| Số entity | 29 | Đếm được **28**. Rà lại khi làm FE1 |
| Ba mã mới | — | **FE13** cờ tính năng · **FE14** một phân hệ vào thẳng · **FE15** tệp mô phỏng hợp đồng dữ liệu |

Kéo theo ở `01` bản 1.3: PQ3 thành ma trận 28 × 8, PQ5 còn 19 entity thiếu khai báo phạm vi thay vì 20, rủi ro R2 viết lại vì phần lớn rủi ro đã rút ngay từ thiết kế. **[`06`](./06-lo-trinh-nen-tang-va-hrm.md) vẫn còn ghi 29 entity — chưa sửa.**

---

## 13. Cái này không làm

| Không làm | Vì sao |
|---|---|
| Tách kho mã, tách backend, tách cơ sở dữ liệu | Mục 1 |
| Viết lại trang giao diện nào | Giao diện giống như cũ mà viết lại thì người dùng thấy giá trị bằng không, còn sai sót thì chịu đủ |
| Đổi đường dẫn URL của Thu mua | Mục 7 |
| Dựng hệ quyền thứ hai cho phân hệ | Dùng lại hồ sơ quyền sẵn có. Entity `module` chỉ thêm khi thật sự cần chặn, mục 4.2 |
| Bảng cơ sở dữ liệu cho danh sách phân hệ | Khai trong mã nguồn, đúng quy tắc 3 của bộ tài liệu. Cấu hình được trên giao diện là việc của năm sau, nếu có ai hỏi |
| Số đếm thông báo trên ô phân hệ | Một truy vấn cho mỗi phân hệ ở mỗi lần vào web. Đo rồi hãy làm |
