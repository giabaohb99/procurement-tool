# 12 — KẾ HOẠCH ERP V2: SỬA LOGIC VÀ RÀNG BUỘC THEO PHẠM VI

**Bản 2.0 — 16/09/2026 (viết gọn).** Tên tệp giữ nguyên
(`12-ke-hoach-erp-v2-da-phap-nhan.md`) để không gãy liên kết từ các tệp khác, nhưng nội dung
đã đổi hẳn:

> **Kế hoạch hôm nay KHÔNG còn là dựng tầng đa pháp nhân.** Nó rút lại thành một việc:
> **sửa logic và siết ràng buộc theo PHẠM VI, trục chia là PHÒNG BAN.** Toàn bộ phần đang làm
> nằm ở **mục 5.1** (chốt 16/09/2026, mã CR `bao-CR-414`).

Mục 1 → 5 giữ lại **chỉ để tra cứu**: đã chốt gì, đã bỏ gì, vì sao — mỗi mục rút còn một bảng.
Đừng lấy việc từ đó; việc lấy ở **mục 5.1** và ở
[`19` mục 7](./19-viec-con-lai-tong-hop.md).

**Ba lần đổi hướng, theo thứ tự:**

| Mốc | Chốt | Nằm ở mục nào |
|---|---|---|
| 18/08/2026 | Chốt tám câu Q1–Q8, dựng kế hoạch mười giai đoạn P0–P9 | 1 · 2 · 3 · 4 |
| 18/08/2026 (cuối ngày) | Rút gọn lần một: **hoãn P5** (danh mục theo đơn vị) | 5 |
| **16/09/2026** | Rút gọn lần hai: **bỏ hẳn vế pháp nhân**, chia việc và chia tầm nhìn bằng **phòng ban + phạm vi** | **5.1 — phần đang làm** |

Tệp [`11`](./11-da-phap-nhan-va-erp-v2.md) trả lời "vì sao"; tệp này trả lời "làm gì, theo thứ
tự nào, xong thì đo bằng gì".

---

## 1. Tám câu Q1–Q8 (chốt 18/08/2026) — còn hiệu lực tới đâu

Chi tiết và lý do ở [`11` mục 4.1–4.2](./11-da-phap-nhan-va-erp-v2.md).

| | Chốt cũ | Hôm nay |
|---|---|---|
| **Q1 · Q2** | Sản phẩm một dòng gốc + **bản đè theo pháp nhân**, con sửa được tên/quy cách/phân loại, khóa mã | **Không làm** — bỏ cùng P5 |
| **Q3** | Danh mục tách theo "đơn vị"; phân loại và đơn vị tính dùng chung | **Không làm.** Danh mục sản phẩm và NCC chốt **giữ công khai** (5.1.4) |
| **Q4** | Gộp Yêu cầu báo giá + Yêu cầu mua hàng thành một chứng từ | **KHAI TỬ 07/09/2026** — thay bằng `bao-CR-310` (khối phương án NCC trên dòng YCMH), YCBG giữ nguyên |
| **Q5** | Dego Organic là **phòng ban dùng chung nhiều công ty** | **Còn đúng, đổi cách làm**: không cần cặp *(pháp nhân, phòng ban)* nữa, chỉ cần **cột phòng xử lý** (5.1.1) |
| **Q6** | Mã chứng từ giữ nguyên, một dãy số chung | **Còn** — không đụng tới |
| **Q7** | Tiền treo không đối chiếu kế toán | **Còn**, và thêm một ràng buộc mới: cấn trừ tiền treo **cấp NCC** phải giới hạn theo phòng (5.1.4) |
| **Q8** | Dữ liệu cũ về DEGO hết | **Còn, đổi nghĩa**: migration điền lùi **toàn bộ = phòng Thu mua chung** |

Mẩu dữ liệu từng chặn P7-4 — *danh sách phân loại nào được coi là nguyên liệu* — **không cần
nữa**: mục 5.1 chốt **không định tuyến theo phân loại hàng**, chỉ theo phòng ban của người lập
phiếu.

---

## 2. Trạng thái các màn ở v2

Bảng tính năng đầy đủ của bản 1.2 (năm bảng, hơn bốn mươi dòng) **hết hiệu lực quá nửa** vì
phần lớn gắn vào P5 và P6 — cả hai đã bỏ. Rút lại còn phần đúng:

| Phân hệ | Đã có ở v2 | Còn phải làm |
|---|---|---|
| **Thu mua** | Tổng quan · YCMH · YCBG (kể cả màn xử lý và Tiến độ báo giá) · Đơn mua hàng và nhận hàng · Tiến độ mua hàng · Phiếu khảo sát · Báo cáo | Khối phương án trên dòng YCMH (`bao-CR-310`) · các sửa đổi ở 5.1 |
| **Tài chính** | Công nợ · Yêu cầu thanh toán và bản in | Màn Công nợ hai con số · cột phòng ẩn trên công nợ và YCTT (5.1.8 A3) |
| **Kho** | Tồn kho · danh mục Kho | Chốt **để mở, không lọc** (5.1.4) |
| **Danh mục** | Sản phẩm · NCC · Hợp đồng · Kho · Phân loại · Đơn vị tính | Bảng phân công thêm cột phòng (5.1.1) · phạm vi hợp đồng (5.1.8 C — đợt sau) |
| **Quyền** | Công ty · Phòng ban · Nhân sự · Phân quyền vai trò và theo người | Hai vai trò mới + bậc phạm vi "Thu mua trong phòng mình" (5.1.2) · ô tick "Phòng tự mua hàng" |
| **Màn còn lại** | — | Kế hoạch riêng ở [`13`](./13-ke-hoach-man-con-lai-v2.md), mã **MC-1 … MC-7** (Cấu hình hệ thống · Import · Sao lưu CSDL · Phiếu hỗ trợ · Thông báo · Trang cá nhân · Đặt lại mật khẩu) |

**Bỏ khỏi bảng cũ:** mọi dòng gắn **P5** (bản đè sản phẩm và NCC theo pháp nhân, đơn vị sở hữu
danh mục, khối "Đơn vị được dùng") · mọi dòng gắn **P6** (chứng từ hợp nhất) · các bậc phạm vi
theo pháp nhân · ô chọn "Pháp nhân đang làm việc" · báo cáo tổng hợp nhiều pháp nhân.

### 2.7 Hai màn từng bị bỏ — đã sống lại

Kế hoạch cũ bỏ **Tiến độ báo giá** và **màn xử lý Yêu cầu báo giá** (798 dòng ở bản cũ) vì tính
gộp hai loại yêu cầu làm một. **Cả hai đã dựng lại ở v2 ngày 29/08/2026** — CR-227
`survey-progress-page.tsx` (`/procurement/survey-progress`) và CR-222
`survey-request-process-page.tsx` (`/procurement/survey-requests/:id/process`) — rồi hướng gộp
khai tử hẳn ngày 07/09, nên quyết định bỏ coi như **đảo trọn vẹn, không còn gì phải xem lại**.

Kéo theo: **Yêu cầu mua hàng bản cũ không bị đóng băng chỉ đọc.** `tab_purchase_request` vẫn là
chứng từ chính đang chạy hằng ngày.

---

## 3. Mười giai đoạn P0–P9 — còn lại gì

Kế hoạch cũ chia mười giai đoạn, tổng **73–104 ngày công**. Sau hai lần rút gọn:

| GĐ | Nội dung cũ | Tình trạng hôm nay |
|---|---|---|
| **P0** | Chốt quyết định | **Xong** (Q1–Q8, 18/08) |
| **P1** | Vá lỗ hổng phạm vi | **XONG 24/08.** P1-1 bậc `proc` AND thêm pháp nhân (CR-164 — chỉ siết khi người xem có `company_id > 0`, nên prod không đổi hành vi); P1-2 khớp phòng ban theo **ID** (CR-086); P1-3 test rò rỉ đã có (`test_proc_loc_cong_ty_p1.py`, `test_pham_vi_khai_du_b07.py`) |
| **P2** | Nền pháp nhân: cây công ty, pháp nhân đang làm việc, bậc phạm vi theo pháp nhân | **BỎ** — mục 5.1 thay bằng trục phòng ban |
| **P3** | Port Công nợ · YCTT · Tồn kho · Báo cáo mua hàng sang v2 | **Xong**, hai phân hệ Tài chính và Kho đã bật |
| **P4** | Lớp CRUD khai báo + các danh mục | **Đang có, làm theo nhu cầu.** P4-3 khai phạm vi: **hợp đồng xong** (CR-117) nhưng chưa đủ chiều phòng (5.1.8 C); còn **nhận hàng** và **lịch sử mua hàng** → gộp vào nhóm "đợt sau" ở 5.1.3 |
| **P5** | Danh mục theo đơn vị, bản đè sản phẩm và NCC | **BỎ** (hoãn 18/08, bỏ hẳn 16/09) |
| **P6** | Gộp YCBG + YCMH | **KHAI TỬ 07/09/2026.** Code đóng băng ở nhánh `p6-hop-nhat-chung-tu` (`42bc0290`, cụm CR-277..291 + 5 migration chưa từng áp) — **chỉ giữ tham khảo, không merge lại**. Thay bằng `bao-CR-310` |
| **P7** | Định tuyến phân loại về đơn vị xử lý | **Đổi hẳn** — 5.1 định tuyến theo **phòng ban người lập phiếu**, không theo phân loại hàng. Phần còn đúng: `tab_category_assignee` phải thêm cột phòng (5.1.1) |
| **P8** | Công nợ theo pháp nhân + tiền treo | **Còn một phần**: chặn trộn phòng trong một YCTT và giới hạn cấn trừ tiền treo cấp NCC theo phòng (5.1.4, 5.1.8 A3). Sổ tiền treo · cấn trừ · hoàn tiền đầy đủ **chưa xếp lịch** |
| **P9** | Báo cáo tổng + hoàn thiện quyền | **Chưa xếp lịch.** Phần báo cáo chưa lọc phạm vi nằm ở nhóm "đợt sau" (5.1.3) |

Ba quy tắc chung của mọi giai đoạn vẫn giữ nguyên và vẫn áp cho 5.1: **cơ sở dữ liệu cũ chỉ
thêm không sửa · Thu mua không được gián đoạn · mỗi thay đổi phạm vi phải có bài test "người
phòng A không thấy chứng từ phòng B"**.

---

## 4. Thứ tự làm và đường găng

Sơ đồ hai luồng của bản cũ (nền `P0 → P1 → P6 → P7 → P9`, giao diện `P3 → P4`) **hết hiệu
lực**: P2 · P5 · P6 bỏ, P3 xong, P1 xong. Thứ tự đang chạy là **năm giai đoạn ở mục 5.1.6**,
làm tuần tự vì mỗi bước đứng trên cột dữ liệu bước trước vừa dựng.

Còn đúng một dây chuyền cứng của bản cũ: **vá lỗ hổng phạm vi trước mọi việc nới quyền** — và
việc đó (P1) đã xong 24/08.

---

## 5. Hai lần rút gọn

**Lần một — 18/08/2026: hoãn P5.** Đo lại thì bỏ tầng đa pháp nhân chỉ bỏ trọn được P5 (9–13
ngày công), **đường găng không đổi** vì P5 nằm ở luồng giao diện chạy song song. Cái mất là
**tên gọi riêng theo pháp nhân** — giá và tồn kho vẫn riêng được, giá nằm ở chứng từ và
`tab_inventory` đã có `company_id`. Mất thêm một thứ không ai nêu lúc đó: danh mục dùng chung
nghĩa là **ai đọc được nhà cung cấp thì thấy toàn bộ NCC, điều khoản và lịch sử giá của cả tập
đoàn**. P5 chỉ **thêm bảng mới**, không sửa bảng cũ, nên hoãn không phát sinh phí.

**Lần hai — 16/09/2026: bỏ hẳn vế pháp nhân.** Nội dung ở mục 5.1 ngay dưới. Lý do đo được:
**17/17 phòng ban chưa gắn pháp nhân và 234/236 nhân sự chưa gắn công ty** — dựng xong tầng
pháp nhân cũng không có dữ liệu để chạy, trong khi việc thật khách cần (phòng tự đi mua) chỉ
cần trục phòng ban.

⚠️ **Ba nợ kỹ thuật của bản cũ nhảy hạng thành lỗ hổng cấp một khi phòng ban thành trục phân
quyền chính.** Hai cái đầu đã vá:

1. `department` là **chuỗi tên** chứ không phải id (N-006) → **đã vá** (CR-086, khớp theo ID;
   tên chuỗi chỉ còn là đường lùi cho phiếu cũ `department_id = 0`).
2. Bậc `proc` **không lọc công ty** → **đã vá** (CR-164).
3. **Không có cây phòng ban** → **chưa có**, và 5.1 không cần: phòng tự mua là quan hệ phẳng,
   không có phòng con.

---

## 5.1 Chốt 16/09/2026 — rút gọn lần hai: bỏ hẳn pháp nhân, định tuyến theo PHÒNG BAN

Khách hỏi lại tình trạng "phân quyền cho nhà máy riêng và thu mua riêng", rồi chốt luôn:
**không chia theo pháp nhân nữa, chỉ chia bằng phòng ban và phạm vi của tài khoản.**
Đây là bước rút gọn thứ hai, đứng sau bản 18/08 ở mục 5 — lần đó bỏ P5, lần này bỏ nốt vế
pháp nhân trong P2 và P7.

**Bài toán thật không phải "nhà máy".** Nhà máy chỉ là ca đầu tiên của một luật chung:
**có những phòng ban tự đi mua, không qua phòng Thu mua.** Khách nêu ba ví dụ cùng loại —
nhà máy (Dego Organic) mua nguyên liệu vì sản xuất theo công thức, sợ lộ công thức ra
ngoài; phòng Nhân sự mua văn phòng phẩm; phòng Kinh doanh mua hàng tặng kèm khách. Làm
đúng một lần thì thêm phòng sau này chỉ là bật một ô cấu hình, không phải sửa mã nữa.
Vì lẽ đó **đừng đặt tên bất cứ thứ gì theo "nhà máy"** — tên phải là "phòng tự mua hàng".

**Ba câu chốt của khách:**

| Câu | Chốt | Hệ quả |
|---|---|---|
| Phiếu nhà máy lập nhưng hàng là **vật tư**, ai mua? | **Nhà máy tự mua HẾT** | Không chia theo phân loại hàng. Định tuyến chỉ nhìn **phòng ban người lập phiếu** |
| Người thu mua của nhà máy lấy đâu ra? | **Người đang ở phòng Dego Organic** | Cấp thêm vai trò thu mua cho vài người trong 27 người sẵn có, chờ khách cho danh sách tên |
| Phòng Thu mua chung có thấy phiếu nhà máy không? | **Giấu hẳn** | Không có ngoại lệ "xem để báo cáo". Báo cáo tổng chi tiêu phải đi đường khác nếu sau này cần |

⚠️ **Vì sao KHÔNG chia theo phân loại hàng, dù khách mô tả nghiệp vụ theo phân loại.**
`item_group` nằm ở **DÒNG** (`tab_purchase_request_item.item_group`), không ở đầu phiếu, và
là chuỗi tự do. Một phiếu trộn cả nguyên liệu lẫn vật tư là chuyện bình thường, nên chia
theo phân loại nghĩa là **một phiếu hai người xử lý hai phần** — kéo theo hàng chờ, phân
bổ, tiến độ và bản in đều phải hiểu khái niệm "nửa phiếu". Khách chốt bỏ, nhà máy tự mua
trọn phiếu của mình.

**Hiện trạng đo trên prod ngày 16/09/2026** (đo trực tiếp trên DB, không phải suy từ tài liệu):

- 17 nhân viên thu mua (`pur_staff`) **tất cả thuộc phòng id 20 "Sản xuất -Thu mua"**;
  quản lý và admin thu mua mỗi vai trò 2 người, chia giữa phòng 20 và phòng 12 "IDA Global".
- Phòng id 5 **"Dego Organic" 27 người, chưa ai giữ vai trò thu mua nào** — nghĩa là bộ tài
  khoản thu mua của nhà máy **chưa tồn tại**, phải lập mới chứ không phải chỉnh cái có sẵn.
- Phạm vi các vai trò thu mua phần lớn đang là **`all`**.
- 17/17 phòng ban chưa gắn pháp nhân và 234/236 nhân sự chưa gắn công ty — không còn là vấn
  đề sau khi bỏ vế pháp nhân, nhưng ghi lại để khỏi đi đo lại.

**Ba việc phải làm:**

1. **Bậc phạm vi mới "Thu mua trong phòng mình"** — cần sửa mã. Người mang bậc này thấy
   phiếu **đã duyệt của chính phòng ban mình**, thay vì mọi phiếu đã duyệt như bậc `proc`.
   Đây chính là bậc **"đơn vị mình xử lý" (P2-2b)** bỏ vế pháp nhân, chỉ còn vế phòng ban.
   ⚠️ **Không dùng lại được ô "Phòng ban được xem"** để làm việc này: ô đó đi qua
   `_dept_include_cond` và được **OR** vào phạm vi vai trò (`core/scoping.py`, `scope_condition`),
   tức là **cộng thêm chứ không giới hạn**. Đặt nó cho thu mua nhà máy thì phạm vi nở ra chứ
   không hẹp lại.
2. **Ô tick "Phòng tự mua hàng" trên danh mục Phòng ban** — cần sửa mã. Tick vào thì phiếu
   của phòng đó không chảy vào hàng chờ chung nữa. ⚠️ Không dùng danh sách **loại trừ** khai
   tay cho phòng Thu mua chung: loại trừ chạy đúng về mặt kỹ thuật (`_explicit_cond` AND vào
   phạm vi vai trò) nhưng phải bảo trì bằng tay, và **thêm một phòng tự mua mà quên khai là
   lủng im lặng** — đúng loại lỗi B-07 đã dọn một lần.
3. **Khai dữ liệu**: cấp vai trò thu mua cho người của Dego Organic, tick "phòng tự mua"
   cho Dego Organic, hạ phạm vi vai trò thu mua chung từ `all` xuống đúng bậc.

**Việc 1 và 2 là mã dùng chung cho mọi phòng tự mua**, không có một dòng nào nói riêng về
nhà máy. Việc 3 lặp lại cho từng phòng khi khách mở thêm.

**Ba chốt bổ sung 16/09/2026** (trả lời ba câu chặn trước khi khởi công):

| Câu | Chốt |
| --- | --- |
| Làm giao diện ở bản nào trước | **`frontend/` (v1) trước**, chạy thật trên prod rồi mới port sang `frontend-v2` — đúng nếp đã chốt 08/09/2026. |
| Máy nhận ra "phòng Thu mua chung" bằng gì | **Mặc định phòng "Sản xuất -Thu mua"**, id để trong một dòng Cấu hình hệ thống (sửa được, không phải sửa mã). Migration điền lùi `handler_dept_id` của mọi phiếu cũ về id đó. |
| Người thu mua ngồi ở phòng khác thì sao | **Không đụng hồ sơ nhân sự.** Cấp thêm cho họ ô **"Phòng ban được xem"** = phòng Thu mua chung (và phòng nào họ phụ trách). Ô này đã có sẵn, là điều kiện **CỘNG THÊM (OR)** vào phạm vi vai trò (`_dept_include_cond` trong `core/scoping.py`) — khai bằng tay trên màn Phân quyền, không cần mã mới. |

⚠️ **Hệ quả kỹ thuật của chốt thứ ba**: `_dept_include_cond` và nhánh `dept` của
`_role_scope_cond` đều so phòng qua `SCOPE_FIELDS[entity]["dept_id"]`, hiện là `department_id`
(**phòng yêu cầu**). CR-414 phải sửa **một chỗ duy nhất** là hàm so phòng để nó khớp **HỢP
(OR) hai cột**: `department_id` (phòng yêu cầu) **hoặc** `handler_dept_id` (phòng xử lý). Sửa
đúng chỗ đó thì mọi màn đang lọc theo phòng tự hiểu khái niệm "phòng được điều chuyển tới",
không phải đi vá từng màn.

⚠️ **Nhưng vẫn cần bậc phạm vi mới, không dùng lại bậc `dept` có sẵn.** Nhân viên thu mua
hiện ở bậc `proc` = "thấy mọi phiếu ĐÃ DUYỆT của toàn hệ". Hạ thẳng xuống `dept` thì họ thấy
**cả phiếu còn nháp, chưa ai duyệt** của các phòng khác gửi sang — rộng hơn hiện tại ở đúng
chỗ nhạy cảm. Bậc mới = `proc` **AND** thêm chiều phòng, đúng khuôn CR-164 đã ghép chiều công
ty vào `_proc_status_cond`. Là một điều kiện, không phải màn mới hay bảng mới.

### 5.1.1 Nhờ ngược lại phòng Thu mua chung — cột "phòng xử lý"

Khách hỏi tiếp ngay trong cùng buổi: phòng tự mua gặp món **không tự mua nổi** (ví dụ mua
thùng, chưa tìm được nguồn) thì có **đẩy sang phòng Thu mua chung khảo sát và mua giúp**
được không, và hệ thống **phân công** khi đó chạy thế nào.

Được, và phải thiết kế ngay từ đầu — nếu chỉ định tuyến cứng theo phòng của người lập
phiếu thì phòng tự mua bị **nhốt**, không có đường ra.

**Cơ chế: tách "phòng yêu cầu" khỏi "phòng xử lý".**

| Cột | Nghĩa | Ai sửa |
|---|---|---|
| `department_id` (đã có) | **Phòng yêu cầu** — ai xin, tiền tính vào ngân sách phòng nào | Không ai sửa sau khi lập. Mọi báo cáo chi tiêu bám cột này |
| `handler_dept_id` (**MỚI**) | **Phòng xử lý** — ai đi mua, hàng chờ của ai, phạm vi xem bám cột này | Đổi được bằng một nút bấm |

Lúc lập phiếu hệ thống tự điền `handler_dept_id`: phòng người lập có tick **"Phòng tự mua
hàng"** thì điền chính phòng đó, không thì điền **phòng Thu mua chung**. Nhờ ngược lại =
**đổi đúng một cột**, không đụng một dòng dữ liệu nghiệp vụ nào; nhận lại cũng vậy.

⚠️ **Tuyệt đối không định tuyến bằng `department_id`.** Sửa cột đó để chuyển việc là làm
hỏng số chi tiêu của cả hai phòng và không có đường lần ngược.

**Bậc phạm vi mới ở việc 1 đọc `handler_dept_id`, không đọc `department_id`** — nếu đọc
nhầm thì phiếu đã nhờ sang thu mua chung vẫn nằm trong tầm nhìn nhà máy mà thu mua chung
không thấy, tức là nhờ xong không ai làm.

**Trọn phiếu, không nửa phiếu.** Kỹ thuật thì chuyển từng dòng làm được (nhánh `proc` đã
có sẵn truy vấn con "thấy phiếu vì có dòng gán cho tôi"), nhưng **cho thu mua chung thấy
phiếu là thấy TOÀN BỘ dòng của phiếu đó** — đúng cái công thức mà cả thiết kế này sinh ra
để giấu. Nên phòng tự mua muốn nhờ món nào thì **lập phiếu riêng cho món đó**.

**Phân công (`dispatch_pr`) sau khi chuyển.** Thuật toán không đổi: phiếu vẫn phải ở trạng
thái "Đã duyệt", vẫn Quản lý/Admin thu mua bấm điều phối, vẫn tự gán NSTM theo phân loại
rồi chuyển "Đã điều phối". Chỉ khác **ai nhìn thấy và ai bấm được** — người của phòng đang
giữ `handler_dept_id`.

⚠️ **Chỗ thật sự phải sửa nằm ở bảng phân công, không nằm ở thuật toán.**
`tab_category_assignee` hiện là **bảng dùng chung toàn hệ**: mỗi phân loại đúng **một**
người chính + một dự phòng (`item_group_id` là khóa **duy nhất**). Hai phòng cùng tự mua
thì tranh nhau một ô — nhà máy khai người của mình vào phân loại "Nguyên liệu" là đè luôn
cấu hình của thu mua chung. Phải thêm **cột phòng** vào bảng này và đổi khóa duy nhất
thành **(phòng xử lý, phân loại)**; `auto_assign_by_category` tra bảng theo
`handler_dept_id` của phiếu, không tra bảng phẳng như bây giờ.

**Chuyển lúc nào.** Sạch nhất là khi phiếu **chưa điều phối**. Đã điều phối rồi mà vẫn
muốn nhờ thì phải **xóa NSTM đã gán** trên các dòng trước khi đổi phòng xử lý, kẻo phiếu
sang phòng mới nhưng người phụ trách vẫn là người phòng cũ.

**Hai câu đã chốt (16/09):**

- **Ai được bấm nút nhờ:** **người có quyền yêu cầu** là đủ — không cần vai trò thu mua.
  Đổi lại, việc nhờ **đi qua bước trưởng phòng duyệt** như mọi nội dung khác của phiếu,
  nên trưởng phòng vẫn nắm thông tin.

  Việc này **tự nhiên đúng, gần như không phải làm gì thêm**: ô tick nằm trên **form
  phiếu**, mà phiếu chỉ sửa được ở trạng thái Nháp / Bị trả lại (`service` chặn sẵn:
  *"Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại"*). Người yêu cầu tick lúc
  lập, trưởng phòng bấm duyệt là chốt luôn — không cần thêm một bước duyệt riêng cho
  việc nhờ.
- **Phòng nhận có nút trả về.** Nhận rồi vẫn đẩy lại được, kèm lý do vào nhật ký.

**Còn một tình huống phải tính riêng:** đúng ca khách nêu lúc đầu — phiếu **đã duyệt, đã
điều phối**, người của phòng đi mua **không nổi** mới muốn nhờ. Lúc đó phiếu không còn sửa
được nên ô tick trên form vô dụng, phải có **nút chuyển rời** ở màn chi tiết. Đề xuất: nút
đó dành cho **người phụ trách hoặc quản lý thu mua của phòng**, và khi bấm thì **gỡ luôn
người phụ trách đã gán** trên các dòng rồi mới đổi phòng xử lý.

**Chốt thêm trong cùng buổi 16/09:**

- **Giao diện**: một ô tick "Nhờ phòng khác xử lý", tick rồi mới bung ô chọn phòng. Danh
  sách chọn **chỉ gồm phòng Thu mua chung và các phòng đã tick "Phòng tự mua hàng"** —
  nhờ sang phòng không có nhân sự thu mua là phiếu rơi vào chỗ không ai điều phối được.
- **Chuyển giao CHỈ có ở Yêu cầu báo giá và Yêu cầu mua hàng.** Đơn mua hàng không có nút
  này và không hiện cho phòng người yêu cầu — giữ đúng hiện trạng. (Đo lại mã nguồn: vai
  trò `requester` và `dept_head` **không có quyền `purchase_order` nào cả**, nên "giữ
  nguyên" ở đây là không phải làm gì.)
- **Phòng chưa khai bảng phân công cho phân loại đó** → để trống, quản lý phòng chọn tay.
  Không rơi về bộ mặc định của Thu mua chung, vì như vậy là tự động gán người ngoài vào
  phiếu của phòng tự mua.
- **Đơn mua hàng vẫn phải mang "phòng xử lý"**, dù không có nút chuyển: lúc tạo đơn thì
  **chép ô phòng xử lý từ phiếu gốc** rồi đông cứng. ⚠️ Nếu để phạm vi Đơn mua hàng lọc
  theo `department_id` (phòng yêu cầu) thì đơn **thu mua chung làm hộ phòng tự mua** sẽ
  mang phòng ban của phòng yêu cầu — chính người làm ra đơn lại không thấy đơn của mình.

### 5.1.2 Vai trò: CỘNG vai trò, nhưng phải là vai trò MỚI

Khách chốt: vai trò phía người yêu cầu **giữ nguyên hết**; trưởng phòng của phòng tự mua
chỉ **được cấp thêm** vai trò thu mua của phòng mình.

⚠️ **Không cấp được vai trò `pur_manager` / `pur_staff` đang có.** Một người nhiều vai trò
thì phạm vi **HỢP** lại (`scope_condition` OR các grant), và **chỉ cần một grant đặt
`all` là hàm trả `None` — thấy tất, mọi grant hẹp còn lại vô nghĩa**. Vai trò Quản lý thu
mua hiện đang full phạm vi, cấp thêm cho trưởng phòng tự mua là họ nhìn thấy toàn công ty,
đúng cái đang muốn tránh.

Nên phải **lập vai trò mới** dùng chung cho mọi phòng tự mua, phạm vi đặt ở bậc "Thu mua
trong phòng mình":

| Vai trò mới | Thay cho | Ghi chú |
|---|---|---|
| Quản lý thu mua phòng | `pur_manager` | Có quyền duyệt điều phối |
| Nhân viên thu mua phòng | `pur_staff` | Không duyệt điều phối |

Tên đặt theo "phòng", **không đặt theo "nhà máy"** — xem đoạn đầu mục 5.1.

Hệ quả cần khách xác nhận: trưởng phòng tự mua sẽ **vừa duyệt phiếu của phòng vừa bấm điều
phối** phiếu đó. Đây chính là nghĩa của "phòng tự xử", nhưng nó bỏ mất một cửa kiểm soát so
với luồng chung, nên ghi ra đây cho rõ chứ không để lẫn.

### 5.1.3 Ba chỗ hở mà phân quyền phiếu KHÔNG che được

Chia phạm vi trên phiếu chỉ đóng **một** đường nhìn. Rà ngày 16/09 thấy còn ba đường khác
vẫn dẫn thẳng tới "mua nguyên liệu gì, bao nhiêu, giá nào, của ai" — tức là đúng thứ mà cả
thiết kế này sinh ra để giấu:

| Chỗ hở | Tình trạng | Cần làm |
|---|---|---|
| **Lịch sử giá mua** (`modules/purchase_history`) | Chỉ gác bằng `require("product", "read")` / `require("supplier", "read")`, **không gọi `apply_scope` lần nào** | Nặng nhất. Phải lọc theo phòng xử lý của chứng từ nguồn |
| **Báo cáo tổng hợp** (`modules/report/service.compute`) | Hàm tính theo NCC / phân loại / NSPT **không nhận `user`**, không lọc phạm vi | Truyền `user` vào và lọc, hoặc chặn bằng quyền `report.read` |
| **Phương án khảo sát** (`survey`) | `SCOPE_FIELDS["survey"]` chỉ có `owner`; `pur_staff` đang để phạm vi `all` | Thêm chiều phòng, hoặc neo phương án theo phiếu gốc |

Hai chỗ nữa **cố ý không lọc được**, phải chấp nhận hoặc xử bằng quyền chứ không bằng phạm vi:

- **Danh mục sản phẩm và nhà cung cấp** khai `PUBLIC` có chủ đích (các phân hệ nối nhau
  bằng `product_code`). Mã nguyên liệu vẫn hiện trong danh mục chung — giấu được *phiếu*
  chứ không giấu được *mặt hàng tồn tại*.
- **Công nợ và nhập kho** lọc theo `company_id`, mà 234/236 nhân sự đang để trống công ty
  nên bộ lọc đó **không chạy**. Muốn giấu thật thì phải khai công ty cho nhân sự, hoặc
  thêm chiều phòng.

Các màn **Tiến độ mua hàng** và **Tiến độ khảo sát** đã gọi `apply_scope` đúng, tự động
theo bậc phạm vi mới, không phải sửa.

### 5.1.4 Chốt của khách về ba chỗ hở và hai chỗ công khai (16/09)

| Hạng mục | Chốt |
|---|---|
| Lịch sử giá mua · Báo cáo tổng hợp · Phương án khảo sát | **Ghi vào kế hoạch, làm ĐỢT SAU** — không chặn đợt 1 |
| Danh mục sản phẩm và nhà cung cấp | **Giữ công khai**, cho xem cũng không sao |
| Nhập kho và tồn kho | **Cho xem hết**, giữ nguyên. Lý do của khách: không thấy tồn thì không biết thiếu gì mà đi mua; xem tồn kho vốn đã phải có quyền, và khách **đã trình bày trước với nhà máy, phía nhà máy chấp nhận** |
| Công nợ | **Lọc THEO ĐƠN** — ai thao tác đơn nào thì thấy và trả nợ của đơn đó |

**Công nợ theo đơn — mô hình đã sẵn sàng.** `tab_payable` mỗi dòng đã neo `po_id`/`po_code`,
nên đây là việc **lọc**, không phải đập lại mô hình. Khách mô tả: NCC A có 10 đơn, thu mua
chung làm 5 thì thấy 5, phòng tự mua làm 5 thì thấy 5, người quyền tổng thấy đủ 10; trong 5
đơn của thu mua chung có thể có 1 đơn phòng tự mua nhờ mua giúp — không sao, vì đúng người
làm đơn mới thấy đơn đó.

**Đo prod 16/09/2026:** 221/221 dòng công nợ (182 hàng · 24 vận chuyển · 15 chi phí nhập
khẩu) **đều có mã đơn**, không có dòng mồ côi — lọc theo đơn chạy được ngay, không phải dọn
dữ liệu trước. 58/58 dòng thanh toán cũng đều gắn đơn, tổng đối trừ đang bằng 0.

Hai điều phải xử khi làm:

1. **Màn Công nợ đang gom theo NHÀ CUNG CẤP.** Khách chốt cách xử: **số TỔNG của NCC vẫn
   hiện cho mọi người, nhưng lọc/mở chi tiết ra thì chỉ thấy đơn của mình.** Ví dụ của
   khách: nợ NCC 100tr, phần của tôi 50tr — tôi trả xong 50tr của tôi, 50tr còn lại của
   phòng khác thì phòng đó tự đề xuất trả với kế toán.

   Cụ thể trong mã: `payable/controller.summary` hiện đang đi qua `_filtered` (đã lọc
   phạm vi) — phải tách ra, trả **hai con số cạnh nhau: "Tổng nợ NCC" (không lọc) và
   "Phần của tôi" (đã lọc)**. Danh sách dòng nợ và **tập nợ được chọn khi lập Yêu cầu
   thanh toán** thì lọc như cũ.

   Hệ quả chấp nhận: thấy tổng 100tr mà phần mình 50tr thì suy ra được "có phòng khác cũng
   mua của NCC này, khoảng 50tr". Với NCC chuyên nguyên liệu thì đó là một đường suy ra
   nữa — nằm trong mức kỳ vọng "khó thấy hơn, không phải không thể thấy" ghi bên dưới.
2. ⚠️ **Tiền treo CẤP NCC** (`payment_request.service.offset_supplier_hanging`): kế toán bấm
   tay cấn trừ tiền trả trước không gắn đơn vào **một khoản nợ bất kỳ** của NCC đó — tiền
   phòng này có thể đi vào nợ phòng kia. Phải giới hạn tập nợ được cấn theo phòng xử lý.
   Treo **gắn đơn** (`apply_prepay_offsets`) đã an toàn sẵn vì lọc theo `po_code`.

### 5.1.5 Luật nền: PHẠM VI là công tắc, không có cờ tính năng

Khách chốt nguyên tắc bao trùm cả mục 5.1:

> Giữ phạm vi như hiện tại thì **mọi thứ chạy y như cũ**. Chỉ khi có bộ tài khoản mang
> **phạm vi mới** thì mới chạy theo kiểu mới. Bản chất là làm gọn và làm đúng trong phạm
> vi của vai trò đó thôi.

Nghĩa là **không thêm cờ bật/tắt tính năng** — bậc phạm vi chính là công tắc, không gán
cho ai thì không ai thấy gì khác. Đây cũng là tiêu chí nghiệm thu: **chưa gán bậc mới mà
màn hình đổi hành vi là làm sai.**

Bốn phần tự nhiên thỏa luật này: hai vai trò mới (không gán thì không tồn tại), ô tick
"Phòng tự mua hàng" (mặc định không tick), cột `handler_dept_id` (bậc phạm vi **cũ** không
được phép đọc cột này), và nút nhờ (chưa phòng nào tick tự mua thì danh sách chọn rỗng →
**ẩn hẳn nút**, không hiện ra rồi bấm không được).

⚠️ **Hai phần KHÔNG tự nhiên thỏa, phải chăm tay:**

1. **Bảng phân công theo phân loại thêm cột phòng.** Dữ liệu cũ không có phòng. Migration
   phải **điền toàn bộ dòng cũ = phòng Thu mua chung**; phiếu nào có phòng xử lý là Thu
   mua chung thì tra đúng bộ đó và gán y như trước. Quên bước điền lùi này là **mọi phiếu
   đang chạy mất người phụ trách tự động** ngay sau khi deploy.
2. **Màn Công nợ hai con số.** Cột "Phần của tôi" đổi giao diện cho cả người chưa dùng
   phạm vi mới. Chỉ **hiện cột đó khi nó khác số tổng**, còn bằng nhau thì giữ nguyên màn
   như cũ.

Đi kèm: viết test "**chưa gán bậc phạm vi mới thì mọi màn hành xử y như trước**" — kiểu
bài kiểm B-07 đã dùng, để lần deploy sau không ai phá luật này mà không biết.

### 5.1.6 Thứ tự làm

Khách chốt: nút chuyển ở màn chi tiết (đường 2) **để giai đoạn cuối**.

| GĐ | Nội dung | Ghi chú |
|---|---|---|
| 1 | Cột `handler_dept_id` cho YCMH + YCBG, ĐMH chép sẵn lúc tạo · ô tick "Phòng tự mua hàng" trên Phòng ban · hai vai trò mới (**Quản lý thu mua phòng cấp `purchase_order` approve + cancel**, xem 5.1.8 A1) · bậc phạm vi "Thu mua trong phòng mình" | Migration điền lùi toàn bộ = phòng Thu mua chung. Chưa gán ai thì **không đổi hành vi**. Chuông **giữ nguyên**, không sửa (5.1.8 A2) |
| 2 | Bảng phân công thêm cột phòng, khóa duy nhất (phòng, phân loại); tra theo phòng xử lý | ⚠️ Chạm **cả YCMH và YCBG** vì hai bên dùng chung `category_assignee.resolve_for_group` |
| 3 | Ô tick "Nhờ phòng khác xử lý" trên **form** phiếu (đường 1) | Chưa phòng nào tick tự mua → danh sách rỗng → ẩn nút |
| 4 | Công nợ hai con số (Tổng nợ NCC / Phần của tôi) · **cột ẩn `department_id` chép sẵn trên CẢ `tab_payable` lẫn `tab_payment_request`, lọc đọc thẳng cột đó — mục 5.1.8 A3** · chặn cấn trừ tiền treo cấp NCC theo phòng · **rà bộ tool Trợ lý AI cho khớp phạm vi mới (5.1.8 D)** | Chỉ hiện cột "Phần của tôi" khi khác số tổng. Bản in YCTT **không** hiện phòng ban. Migration điền lùi 221 dòng nợ + toàn bộ YCTT cũ = Thu mua chung |
| **5 (cuối)** | **Nút chuyển phòng xử lý ở màn chi tiết (đường 2)** + nút Trả về + ô lý do vào nhật ký | Khách chốt để sau cùng. Điều kiện bật nút ở mục **5.1.7** |
| Đợt sau, ngoài CR này | Lịch sử giá mua · Báo cáo tổng hợp · Phương án khảo sát (mục 5.1.3) | |

**Đường 1 và đường 2 áp cho CẢ Yêu cầu báo giá lẫn Yêu cầu mua hàng**, nhưng hai phiếu
khác nhau một chỗ: **YCBG không có bước điều phối riêng** — trưởng phòng duyệt là
`survey_request.service.auto_assign` gán người ngay, không có trạng thái trung gian "đã
duyệt, chưa điều phối" để lùi về. Nên ở YCBG, đường 2 chỉ làm hai việc: gỡ người khỏi các
dòng rồi đổi phòng xử lý; bên nhận gán lại (tự động theo bảng phân công của phòng họ, hoặc
gán tay qua endpoint gán NSTM theo dòng sẵn có).

**Ghi nhận mức kỳ vọng.** Với danh mục sản phẩm/NCC công khai và tồn kho mở, thiết kế này
đạt mức **"khó thấy hơn"** chứ không phải **"không thể thấy"**: nhìn tồn kho và nhập xuất
theo thời gian vẫn suy ra được tỉ lệ nguyên liệu. Giá trị thật của mục 5.1 là **tách việc
và tách hàng chờ giữa các phòng**; phần giấu công thức là hệ quả kèm theo. Muốn kín thật
thì phải tách riêng cả danh mục nguyên liệu — đắt hơn nhiều bậc và không nằm trong đợt này.
Ghi ra đây để sau này không ai hiểu nhầm là đã kín.

### 5.1.7 Điều kiện bật nút chuyển ở màn chi tiết (đường 2)

Một câu luật chung cho cả hai loại phiếu: **chỉ chuyển được khi việc mua chưa thật sự bắt
đầu ngoài đời.** Đã có đơn sống, đã chốt nhà cung cấp, đã nhận hàng hay đã sinh công nợ thì
nút phải tắt — chuyển lúc đó là ném cho phòng mới một hồ sơ dở dang mà họ không sửa được.

**Yêu cầu mua hàng**

| # | Điều kiện bật nút | Vì sao |
|---|---|---|
| 1 | Phiếu đang ở **Đã duyệt** hoặc **Đã điều phối** | Nháp / Bị trả lại đã có ô tick trên form (đường 1) rồi; Hủy / Hoàn thành thì hết việc |
| 2 | **MỌI dòng hàng còn ở mức "Chưa tạo đơn mua hàng"** — dòng bị hủy tay trên phiếu thì bỏ qua, không tính | Đây là ô duy nhất phải soi, xem giải thích ngay dưới |
| 3 | Người bấm là quản lý thu mua của **phòng đang giữ phiếu** (hoặc người có phạm vi tổng) | Phòng khác không được giành việc của nhau |

Điều kiện 2 **đã bao trọn** yêu cầu "chưa có đơn mua hàng nào sống", nên không cần kiểm
thêm lần nữa: trạng thái dòng YCMH do máy suy ngược từ các đơn mua hàng — đơn đã **Hủy**
thì coi như chưa ai lập, còn đơn **Nháp / Chờ duyệt / Bị trả lại** vẫn tính là đã có người
lập. Hệ quả cố ý: một cái đơn nháp bỏ quên cũng chặn nút, người đang giữ phiếu phải vào xóa
hoặc hủy đơn đó trước. Hệ thống **không** tự hủy đơn giúp — đơn đã nhận hàng thì bản thân
chức năng hủy cũng từ chối, nên không có đường tự động nào an toàn.

Khi bấm: gỡ người phụ trách khỏi mọi dòng, đổi phòng xử lý, đưa phiếu về **Đã duyệt (chưa
điều phối)**, bắt nhập lý do và ghi vào nhật ký.

**Yêu cầu báo giá**

| # | Điều kiện bật nút | Vì sao |
|---|---|---|
| 1 | Phiếu ở **Đã duyệt** hoặc **Đang khảo sát**, không phải **Khảo sát xong** | Khảo sát xong là đã ra kết quả, không còn gì để chuyển |
| 2 | **Chưa dòng nào Hoàn thành** | Dòng đang ở **Khảo sát lại** thì VẪN cho chuyển — đó đúng là ca "phòng tôi tìm không ra, nhờ thu mua chung" |
| 3 | **Chưa chốt phương án nào** trên phiếu | Chốt phương án là đã chọn nhà cung cấp và giá |
| 4 | **Chưa sinh yêu cầu mua hàng nào từ phiếu này** | Tương đương điều kiện "chưa có đơn" bên YCMH |

Phương án đã nhập nhưng **chưa chốt** thì không chặn: giữ nguyên các phương án cũ, phòng
nhận khảo sát tiếp cho đủ. Khi bấm: gỡ người phụ trách và ngày nhận việc trên các dòng, đổi
phòng xử lý, ghi lý do; phòng nhận gán lại — tự động theo bảng phân công của phòng họ, hoặc
gán tay qua màn gán NSTM theo dòng sẵn có.

**Chuyển một phần: không có.** Mua được nửa phiếu rồi mới muốn nhờ thì tách các dòng chưa
mua sang một phiếu mới rồi chuyển phiếu mới đó. Phải ghi rõ trong HDSD kẻo người dùng tưởng
hệ thống hỏng.

**Nút Trả về của phòng nhận dùng đúng bộ điều kiện này**, chỉ khác một chỗ: phòng xử lý
quay về phòng đã nhờ, và lý do trả về là bắt buộc.

Tham chiếu kỹ thuật: dòng YCMH `no_po` trong `PR_LINE_STATUS`, suy ra ở
`purchase_request.service.sync_from_purchase_orders` (bỏ đơn `cancelled`, tính cả `draft`);
YCBG dùng `SurveyRequestLine.is_completed` / `line_status = completed`,
`SurveyRequestOption.is_chosen`, và bảng `tab_survey_request_pr`; trạng thái phiếu YCBG
`approved` / `processing` / `survey_done`.

### 5.1.8 Rà vòng hai sau khi chốt điều kiện — còn những gì

Mục 5.1.3 rà đường NHÌN (ai đọc được dữ liệu của ai). Vòng này rà đường CHẠY (phiếu có đi
hết luồng được không) và lòi ra ba chỗ **không hoãn sang đợt sau được**, vì thiếu chúng thì
phòng tự mua hoặc tắc giữa đường, hoặc rò ngay lần đầu chạy.

**A. Ba chỗ — đại ca đã chốt cách xử 16/09**

| # | Chỗ | Chốt |
|---|---|---|
| A1 | **Ai duyệt Đơn mua hàng của phòng tự mua** | **Không đặt luật riêng: ai có quyền duyệt TRÊN PHÒNG ĐÓ thì duyệt được** — tức vẫn là quyền `purchase_order.approve` cũ, chỉ khác phạm vi. Thực tế chạy: **quản lý thu mua của phòng tự duyệt đơn của phòng mình**; người phạm vi toàn hệ (Quản lý thu mua chung, admin) vẫn duyệt được mọi phòng như trước. Việc phải làm rút còn một dòng: vai trò **Quản lý thu mua phòng** cấp `purchase_order` **approve + cancel** ở bậc phạm vi mới — phần còn lại phạm vi tự lo |
| A2 | **Chuông thông báo không biết phạm vi** | **Giữ nguyên, không sửa gì** — đại ca chốt *"ai có quyền thì cứ gửi thôi không sao"*. Hệ quả chấp nhận: người nhận chuông mà không có phạm vi phòng đó thì bấm vào ăn **403**; chuông chỉ mang mã phiếu nên không lộ nguyên liệu. **Ghi vào HDSD** để người dùng khỏi báo lỗi. Nếu sau này ồn quá mới lọc — lúc đó là CR riêng |
| A3 | **Yêu cầu thanh toán lọc theo phòng** | **Thêm một trường ẩn `department_id` trên đầu phiếu YCTT rồi lọc theo nó** (đại ca chốt), **bản in KHÔNG hiện phòng ban**. Phải dùng trường riêng chứ không suy từ đơn, vì YCTT cho phép **dòng gõ tay không gắn đơn** (`payable_id = 0`, `po_code` trống) — suy từ đơn là những dòng đó rơi ra ngoài mọi bộ lọc |

**Chi tiết trường ẩn của A3.** Cột `department_id` trên `tab_payment_request`, mang nghĩa
**phòng ĐỨNG RA CHI** (phòng xử lý), điền một lần lúc tạo phiếu rồi đông cứng:

- Phiếu có dòng gắn đơn → lấy **phòng xử lý của đơn**; phiếu toàn dòng gõ tay → lấy **phòng
  của người lập**.
- ⚠️ **Chặn trộn hai phòng trong một YCTT**: các dòng gắn đơn phải cùng một phòng xử lý.
  Lọc bằng một trường mà phiếu ôm đơn của hai phòng thì một phòng mất dấu tiền của mình.
  Ràng buộc này **không phiền ai**: YCTT vốn đã chỉ cho **1 NCC/phiếu**, mà hai phòng cùng
  mua một NCC trong cùng một phiếu chi là chuyện gần như không xảy ra.
- Migration **điền lùi toàn bộ phiếu cũ = phòng Thu mua chung** (cùng nhịp với `handler_dept_id`),
  và thêm `dept_id` vào `SCOPE_FIELDS["payment_request"]` — trước giờ chỉ có `company` + `owner`.
- **Bản in YCTT không thêm dòng phòng ban nào**, mẫu in giữ y nguyên.
**Công nợ làm ĐÚNG KHUÔN NÀY — đại ca chốt 16/09.** Không lọc vòng qua đơn nữa: thêm cột
`department_id` vào `tab_payable`, **chép sẵn phòng xử lý của đơn ngay lúc sinh dòng nợ** (cả
ba nguồn `goods` · `shipping` · `import_cost`), rồi lọc đọc thẳng cột đó.

| | Lọc vòng qua đơn (đã BỎ) | Chép sẵn cột ẩn (đã CHỌN) |
|---|---|---|
| Mỗi lần mở màn Công nợ | Cầm từng dòng nợ, lấy mã đơn, nối sang bảng ĐMH hỏi phòng xử lý rồi mới lọc | Đọc cột ngay tại dòng nợ |
| Dòng nợ không gắn đơn | **Rơi khỏi mọi bộ lọc** — đúng cái bẫy đã gặp ở YCTT | Vẫn có phòng, không rơi |
| Giá phải trả | Không thêm cột, nhưng nối bảng ở màn vốn đã chậm | Một migration điền lùi **221 dòng** (đo prod 16/09, tất cả đều có mã đơn) |
| Về sau đọc mã | Hai màn dính nhau mà hai kiểu lọc | Một khuôn dùng chung với YCTT |

⚠️ **Vì sao số chép ra không bao giờ lệch:** điều kiện ở mục 5.1.7 đã cấm chuyển phòng khi
đơn đã nhận hàng — mà đã nhận hàng mới sinh công nợ. Đơn nào đẻ ra dòng nợ là đơn đó đứng
yên vĩnh viễn, nên phòng chép vào dòng nợ không có đường cũ đi. Ghi ra đây để lần sau ai đọc
khỏi tưởng là dữ liệu chép hớ.

Kèm theo: thêm `dept_id` vào `SCOPE_FIELDS["payable"]` (trước giờ chỉ `company` + `owner`),
và migration điền lùi toàn bộ dòng nợ cũ = **phòng Thu mua chung** — cùng nhịp với
`handler_dept_id` và `tab_payment_request`, một lượt cho cả ba.

**B. Bốn luật cần chốt, gần như không tốn công**

| # | Tình huống | Đề xuất |
|---|---|---|
| B1 | **Bỏ tick "Phòng tự mua hàng" giữa chừng** | Phiếu đang chạy **giữ nguyên phòng xử lý** — tự đẩy về thu mua chung là mất dấu hàng loạt. Chỉ phiếu mới đổi. Và **chặn bỏ tick khi phòng còn phiếu chưa hoàn thành**, kèm câu báo "còn N phiếu đang xử lý" |
| B2 | **Người thu mua của phòng nghỉ / chuyển phòng** | Phiếu bám PHÒNG chứ không bám người nên không mất; người phụ trách trên dòng vẫn là người cũ, quản lý phòng gán lại tay bằng chức năng sẵn có. **Không đẻ thêm gì** |
| B3 | **Cụm NCC đề xuất trên dòng YCMH** (hai cụm req/pur) khi chuyển phòng | **Giữ nguyên**, không xóa: đó là thông tin có ích cho phòng nhận ("chỗ này tôi hỏi rồi"), và điều kiện bật nút ở 5.1.7 đã bảo đảm chưa ai chốt giá hay lập đơn |
| B4 | **Bản in ghi phòng nào** | In **phòng yêu cầu** (`department_id`) — đúng nghĩa ai xin, ngân sách phòng nào. Phòng xử lý chỉ để lọc trong hệ, **không đưa lên bản in** |

**C. Thêm một chỗ vào nhóm "đợt sau" của mục 5.1.3:** **hợp đồng nhà cung cấp** —
`SCOPE_FIELDS["contract"]` cũng chỉ `company` + `owner`, vai trò thu mua giữ `contract` ở
phạm vi `company` nên **không chạy** y hệt ba chỗ kia. Hợp đồng có giá và điều khoản, cùng
loại rò với lịch sử giá mua. Gom chung một đợt dọn sau.

**D. Đã rà, không có lỗ mới:** **Trợ lý AI** — 9/14 nhóm tool đã đi qua `apply_scope` (công
nợ, YCTT, chứng từ thu mua, danh mục, hợp đồng, nhân sự, nghỉ phép, xuất dữ liệu, tra cứu
chung); 5 nhóm còn lại (việc chờ duyệt của chính mình, nháp của mình, tài liệu HDSD, tra cứu
HDSD, phiếu hỗ trợ) không đụng dữ liệu mua hàng. Hai màn **Tiến độ mua hàng** và **Tiến độ
khảo sát** đã gọi `apply_scope` đúng, tự theo bậc phạm vi mới. **Nhập kho** không nằm ở vai
trò nhân viên thu mua nên không phải tính, mà kho vốn đã chốt để mở.

⚠️ **Nhưng phải ghi thành việc, đại ca dặn:** **sửa phạm vi thì PHẢI rà lại bộ tool của Trợ
lý AI cho khớp.** Đi chung `apply_scope` nghĩa là **tự theo bậc phạm vi mới**, nhưng chỗ nào
tool tự dựng câu lọc riêng hoặc tự cộng số tổng thì **không tự theo**. Ba việc cụ thể trong
đợt này:

1. **Tool công nợ** phải trả **hai con số** y như màn Công nợ (Tổng nợ NCC / Phần của tôi) —
   để nguyên thì hỏi trợ lý sẽ ra con số khác với màn hình, người dùng tưởng số sai.
2. **Tool yêu cầu thanh toán** phải lọc theo cột `department_id` mới của A3.
3. **Tool chứng từ thu mua** phải đọc `handler_dept_id` — nếu có chỗ nào đang tự lọc theo
   `department_id` (phòng yêu cầu) thì sửa cho khớp bậc phạm vi mới.

Và ghi thành **luật thường trực**: mỗi lần thêm bậc phạm vi hoặc thêm trường lọc mới thì rà
`modules/assistant/tools/` trong cùng đợt, không để lệch một nhịp — trợ lý là cửa **hỏi một
câu lục cả hệ**, lệch phạm vi ở đây là lệch to nhất.

---

## 6. Rủi ro

Bảng rủi ro của tầng đa pháp nhân ở [`11` mục 6](./11-da-phap-nhan-va-erp-v2.md) nay chỉ còn
giá trị lịch sử. Bốn rủi ro thật của kế hoạch đang chạy:

| Rủi ro | Dấu hiệu sớm | Đường lui |
|---|---|---|
| **Migration quên điền lùi cột phòng** — `handler_dept_id`, `tab_category_assignee`, `tab_payable`, `tab_payment_request` | Ngay sau deploy: phiếu đang chạy mất người phụ trách tự động, hoặc biến khỏi danh sách của chính người đang làm nó | Điền lùi **toàn bộ dòng cũ = phòng Thu mua chung**; trước khi bật, chạy bài đếm "số dòng phòng rỗng = 0" |
| **Đổi hành vi khi chưa gán bậc phạm vi mới** — phá luật nền ở 5.1.5 | Người dùng cũ thấy màn hình khác đi mà không ai được cấp quyền gì thêm | Bài test "chưa gán bậc mới thì mọi màn y như trước", kiểu B-07 đã dùng |
| **Lọc theo phòng nhưng để lọt đường vòng** — lịch sử giá mua, báo cáo tổng hợp, phương án khảo sát, hợp đồng, bộ tool Trợ lý AI | Hỏi trợ lý ra số khác màn hình; mở lịch sử giá thấy mã hàng của phòng khác | Bốn chỗ đầu **đã chốt làm đợt sau** (5.1.3, 5.1.8 C); bộ tool Trợ lý AI **phải rà trong cùng đợt** (5.1.8 D) |
| **Bỏ tick "Phòng tự mua hàng" giữa chừng** | Phiếu đang chạy của phòng đó mất dấu hàng loạt | Chặn bỏ tick khi phòng còn phiếu chưa hoàn thành (5.1.8 B1) |

---

## 7. Không nằm trong kế hoạch này

- **Tầng đa pháp nhân** — cây công ty, pháp nhân đang làm việc, bản đè danh mục theo pháp
  nhân. Bỏ, xem mục 5. Quay lại khi nào HRM khai đủ công ty cho nhân sự.
- **Giấu KÍN công thức nguyên liệu.** Với danh mục sản phẩm/NCC công khai và tồn kho mở, thiết
  kế này chỉ đạt **"khó thấy hơn"**, không phải "không thể thấy" — xem đoạn cuối 5.1.6.
- **Tắt `frontend/`.** Chỉ bàn khi các màn ở [`13`](./13-ke-hoach-man-con-lai-v2.md) xong.
- **Triển khai v2 lên prod.** Hạ tầng đã sẵn (service `erp` có trong
  `docker-compose.production.yml` từ 11/09/2026), nhưng ngày bật cho người dùng prod chưa chốt.
- **HRM, Văn thư, các phân hệ còn lại** — xem `02`, `06`, `10` và `van-thu/`.
- **685 sản phẩm dùng tên phân loại thô** (CR-083) — việc dữ liệu, độc lập với kế hoạch này.

---

## 8. Liên quan

- [`19` Việc còn lại tổng hợp](./19-viec-con-lai-tong-hop.md) mục 7 — **chỗ lấy việc**, bảng
  giai đoạn rút gọn của mục 5.1.
- [`11` Đa pháp nhân và chuyển chức năng sang ERP v2](./11-da-phap-nhan-va-erp-v2.md) — đánh
  giá và số đo hiện trạng của hướng cũ; **không cập nhật nữa**.
- [`13` Kế hoạch các màn còn lại ở v2](./13-ke-hoach-man-con-lai-v2.md) — MC-1 … MC-7.
- [`08` Danh sách task củng cố](./08-danh-sach-task-cung-co.md) — **DB15** trùng với P1-2 (đã
  xong); **PQ11/PQ13/PQ14** thuộc cùng nhóm phạm vi.
- [`07` Kiến trúc vỏ ERP](./07-kien-truc-vo-erp.md) — bảng chia entity vào phân hệ.
- `doc/tai-lieu-ky-thuat/change-log-bao.md` — dòng **bao-CR-414-phong-tu-mua-hang**.
