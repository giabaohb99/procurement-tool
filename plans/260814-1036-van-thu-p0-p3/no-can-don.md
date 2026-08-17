# Sổ nợ cần dọn — bộ máy phê duyệt (P3-T35)

> **Mở ngày 17/08/2026.** Tệp này là **sổ nợ kỹ thuật của phase 3**, không phải danh sách việc.
>
> **Luật ghi sổ:** ghi **ngay lúc chèn**, không ghi sau. Mỗi món nợ phải có đủ **năm cột**:
> *(1)* nợ cái gì · *(2)* nằm ở đâu (tệp + dòng) · *(3)* vì sao chấp nhận nợ · *(4)* **điều kiện nào thì xóa được** · *(5)* xóa bằng cách nào.
>
> Món nợ nào không viết nổi cột (4) thì **không phải nợ, mà là thiết kế** — đừng ghi vào đây, hãy sửa thiết kế.
>
> Liên quan: [`plan.md`](./plan.md) quyết định 10 · [`phase-03-bo-may-phe-duyet.md`](./phase-03-bo-may-phe-duyet.md) T35, T36.

## Bảng tổng

| # | Nợ | Mức | Điều kiện xóa | Trạng thái |
|---|---|---|---|---|
| **N-01** | **5 luồng duyệt Thu mua chưa chuyển sang bộ máy mới** | **Rất cao** | Bộ máy chạy thật ổn định với văn thư ở prod | Đang nợ |
| N-02 | Mã kiểm tra quyền duyệt cũ nằm rải ở 5 controller Thu mua | Cao | Cùng N-01 (là hệ quả của N-01) | Đang nợ |
| N-03 | 12 tên cờ `can_*` rời rạc backend phát ra cho `frontend/` | Trung bình | 5 luồng đã chuyển xong **và** `frontend/` không còn đọc cờ đó | Đang nợ |
| N-04 | Giao diện tự suy luận quyền duyệt ở trang YCMH | Trung bình | YCMH chuyển sang `<ApprovalPanel>` | Đang nợ |
| N-05 | Bốn vai trò cùng nghĩa "quản lý" | Trung bình | Bước duyệt khai bằng luồng, không còn dựa vào vai trò | Đang nợ |
| N-06 | `tab_user_scope` với `dim='department'` lưu **tên phòng** | **Cao (rò dữ liệu)** | P0-T06 xong: đổi sang lưu `department_id` | Đang nợ |
| N-07 | Nhánh `if` đổi đường ở văn thư | Thấp | Mọi loại văn bản đã bật `needs_approval`, không ai dùng đường một bước nữa | Chưa phát sinh (sẽ có ở T37) |

---

## N-01 · Năm luồng duyệt Thu mua chưa chuyển sang bộ máy mới

**Nợ cái gì.** Phase 3 dựng xong một bộ máy phê duyệt khai được bằng giao diện, nhưng **chỉ văn thư dùng nó**. Năm luồng duyệt của Thu mua vẫn chạy bằng mã viết tay như trước ngày 17/08/2026:

| Luồng | Chỗ quyết định ai được duyệt | Ghi chú |
|---|---|---|
| Yêu cầu mua hàng (YCMH) | `modules/purchase_request/controller.py` — hai lần duyệt (trưởng phòng, rồi thu mua) + `_in_approve_scope` ở dòng **45** | Khó nhất. Có cả điều phối chạy kèm |
| Đơn mua hàng (ĐMH) | `modules/purchase_order/controller.py` — `submit_po` / `approve_po` / `reject_po` / `cancel_po` | Xem thêm **CR-073**: các hàm này hiện **không có bất kỳ luật chuyển trạng thái nào** |
| Yêu cầu thanh toán | `modules/payment_request/controller.py` | Đơn giản nhất — khi mở lại nhóm D thì chuyển luồng này trước |
| Khảo sát | `modules/survey/controller.py` | |
| Yêu cầu khảo sát | `modules/survey_request/controller.py` | |

**Vì sao chấp nhận nợ.** Khách chốt (17/08/2026) Thu mua **đang chạy thật ở prod, giữ nguyên**. Đổi đường duyệt của một hệ đang có người dùng thật, ngay trong lúc bộ máy mới còn chưa ai dùng bao giờ, là đặt rủi ro vào chỗ đắt nhất. Văn thư chưa có người dùng thật nên hỏng cũng không ai chết — đó là chỗ đúng để bộ máy chạy vòng đầu.

**Điều kiện xóa.** Đủ **cả ba**:

1. Bộ máy đã chạy thật với văn thư **ở prod**, qua ít nhất một chu kỳ ban hành văn bản đầy đủ, không có sự cố cấp số / phiếu kẹt / duyệt nhầm người.
2. Trình khai luồng (T32) đã được người dùng nghiệp vụ tự khai được ít nhất một luồng mà **không cần lập trình viên**.
3. Năm luồng Thu mua ở **P3-T12** đã khai được hết trên mô hình **mà không phải mở rộng bảng** — nếu phải `ALTER` thì mô hình chưa đủ, quay lại T13.

**Xóa bằng cách nào.** Mở lại **nhóm D** của phase 3, giữ nguyên nội dung đã viết sẵn: T28 (dựng `gate.py`, bê mã cũ nguyên xi, kiểm thử T11 làm chứng) → T29 (nhánh `if` + cờ `approval_engine.{entity}`) → T31 (chuyển **từng luồng một**, thứ tự: yêu cầu thanh toán → khảo sát → yêu cầu khảo sát → YCMH → ĐMH) → T36 (dọn).

**Cảnh báo.** Đây là món nợ dễ quên nhất, vì quên nó thì **không có gì hỏng cả** — hệ vẫn chạy, chỉ là mãi mãi có hai bộ máy duyệt song song. Chống bằng cách: T12 vẫn bắt buộc khai đủ 5 luồng Thu mua ra giấy ngay trong phase này, để mô hình không bị đẽo vừa vặn cho mỗi văn thư.

---

## N-02 · Mã kiểm tra quyền duyệt cũ nằm rải ở 5 controller

**Nợ cái gì.** Câu hỏi *"người này có được duyệt phiếu này không"* hiện được trả lời **năm chỗ khác nhau, mỗi chỗ một kiểu**. Nặng nhất là `_in_approve_scope` (`modules/purchase_request/controller.py:45`) — hàm này lọc `scope in ("proc","all")`, tức là **một bước duyệt bị nhét vào cột phạm vi dữ liệu**. Phạm vi dữ liệu trả lời "được *nhìn thấy* những phiếu nào", không phải "được *duyệt* phiếu nào"; dùng nó làm bước duyệt là mượn sai công cụ.

**Vì sao chấp nhận nợ.** Là hệ quả trực tiếp của N-01 — không chuyển luồng thì không gom mã được.

**Điều kiện xóa.** Cùng N-01.

**Xóa bằng cách nào.** T28 bê **nguyên xi** vào `gate.py` trước (kể cả chỗ trông có vẻ sai — **chống chỉ định: nhân tiện sửa luôn**), T31 chuyển từng luồng, T36 xóa hẳn.

---

## N-03 · Mười hai tên cờ `can_*` rời rạc

**Nợ cái gì.** Backend phát ra 12 tên cờ khác nhau cho cùng một ý "người này làm được gì với phiếu này": `can_approve`, `can_dispatch`, `can_process`, `can_khao_sat_lai`, … Bộ máy mới phát ra **một khối `approval` duy nhất** (T30). Hai thứ chạy song song.

**Vì sao chấp nhận nợ.** `frontend/` đang chạy thật ở prod và đang đọc đúng 12 cờ đó. Xóa là vỡ ngay.

**Điều kiện xóa.** 5 luồng Thu mua đã chuyển xong (N-01) **và** `grep` trong `frontend/` không còn chỗ nào đọc các cờ đó.

**Xóa bằng cách nào.** T36.

---

## N-04 · Giao diện tự suy luận quyền duyệt ở trang YCMH

**Nợ cái gì.** `frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx`, dòng **513** và **520**: điều kiện hiện nút duyệt là `(data.can_approve || canManage)`, trong đó `canManage = can('purchase_request','cancel')`.

Nghĩa là giao diện đang **tự đoán**: *"người này có quyền hủy, chắc là quản lý, chắc là được duyệt"*. Suy đoán này **không tồn tại ở backend** — backend không bao giờ nói thế. Kết quả: nút duyệt hiện ra cho người bấm vào sẽ bị từ chối, hoặc tệ hơn là hiện đúng nhưng vì lý do sai.

**Vì sao chấp nhận nợ.** Gỡ nó là đụng vào đường duyệt YCMH — thuộc phạm vi đã hoãn.

**Điều kiện xóa.** YCMH chuyển sang `<ApprovalPanel>` (T31 + T33).

**Xóa bằng cách nào.** Bỏ hẳn `|| canManage`, chỉ đọc khối `approval` từ backend. Luật chung: **giao diện không được suy luận quyền duyệt, chỉ được hiển thị cái backend nói.**

---

## N-05 · Bốn vai trò cùng nghĩa "quản lý"

**Nợ cái gì.** `MANAGER` (id 2) · `dept_head` (id 11) · `manager_purchase` (id 8, vai trò demo) · `pur_manager` (id 14) — bốn vai trò, cùng một ý. Khi bước duyệt chuyển sang khai bằng luồng thì một phần quyền `approve` trên các vai trò này **không còn ai đọc tới**, nhưng vẫn nằm trong bảng phân quyền và vẫn cấp quyền thật.

**Vì sao chấp nhận nợ.** Quyền thừa không tự gây lỗi, nhưng dọn sớm thì rủi ro cắt nhầm quyền của người đang dùng thật.

**Điều kiện xóa.** Bước duyệt đã khai bằng luồng cho luồng tương ứng, **và** đã đối chiếu từng vai trò xem còn ai được gán không (`tab_user_role`).

**Xóa bằng cách nào.** T36. **Sao lưu bảng phân quyền trước khi xóa** — đã có tiền lệ ở CR-068.

---

## N-06 · `tab_user_scope` với `dim='department'` lưu tên phòng

**Nợ cái gì.** Phạm vi dữ liệu theo phòng ban đang so bằng **chuỗi tên phòng**, không phải ID. Ba hệ quả **đang xảy ra thật**:

1. Hai pháp nhân có phòng trùng tên (kiểu "Phòng Kế toán") → người của pháp nhân A **nhìn thấy phiếu của pháp nhân B**. Đây là rò dữ liệu xuyên pháp nhân, không phải chuyện thẩm mỹ.
2. Đổi tên phòng là phạm vi **im lặng đứt**, không báo lỗi gì.
3. `_explicit_cond` và `_dept_include_cond` trong `core/scoping.py` lấy cột theo `dept_name`, nên với entity khóa theo `dept_id` (gồm `document` mới) thì **luật loại trừ phòng ban chết hoàn toàn** — khai loại trừ mà không loại trừ gì cả.

Cùng họ với nó: `core/scoping.py:84` so `model.nspt == profile["emp_name"]` — cũng là so bằng **tên nhân sự**.

**Vì sao chấp nhận nợ.** Không phải nợ tự nguyện — là nợ có sẵn từ trước, phát hiện khi rà phase 0.

**Điều kiện xóa.** Không có điều kiện chờ. **Đây là món phải trả sớm nhất trong cả sổ**, vì bộ máy duyệt sắp giao việc xuyên pháp nhân — giao việc trên nền phạm vi đang rò thì nhân đôi hậu quả.

**Xóa bằng cách nào.** **P0-T06** (đổi sang lưu ID) + **P0-T07** (vá loại trừ chết) + **P3-T09** (khóa hóa phòng ban trên chứng từ). Kèm nguyên tắc từ quyết định 11: **mọi khóa tổ chức trong `condition_json` lưu bằng ID, cấm lưu chuỗi tên.**

---

## N-07 · Nhánh `if` đổi đường ở văn thư

**Nợ cái gì.** *(Chưa phát sinh — sẽ có khi làm T37.)* Trong `modules/document/controller.py` sẽ có một nhánh: `doc_type.needs_approval = true` → chạy bộ máy mới; `false` → chạy đường duyệt một bước cũ.

**Vì sao chấp nhận nợ.** Là chốt an toàn để lùi được mà không cần deploy.

**Điều kiện xóa.** Mọi loại văn bản trong danh mục đã bật `needs_approval`, và đường một bước cũ không còn văn bản nào đi qua trong một khoảng đủ dài.

**Xóa bằng cách nào.** Xóa nhánh `if`, xóa đường cũ, xóa cột cờ nếu không còn ý nghĩa nào khác.

---

## N-08 · CR-074 / CR-075 làm ở `frontend/`, nợ lại bản `frontend-v2`

**Nợ cái gì.** Hai việc khách yêu cầu ngày 17/08 được dựng giao diện ở `frontend/` — bản đang
chạy thật — chứ không phải `frontend-v2`:

- **CR-074** trạng thái dòng YCMH "Chưa tạo đơn mua hàng" (`frontend/src/pages/PurchaseRequestDetail.tsx`);
- **CR-075** màn "Tiến độ báo giá" (màn MỚI hoàn toàn).

CR-074 là sửa lỗi nhãn trên màn đang chạy nên vẫn nằm trong luật D-026. CR-075 thì **là tính
năng mới, đúng luật phải làm ở `frontend-v2`** — đây là ngoại lệ có ý thức, khách chốt.

**Vì sao chấp nhận nợ.** `frontend-v2` chưa có màn Yêu cầu báo giá lẫn màn Tiến độ mua hàng để
lấy làm khuôn; dựng ở đó trước nghĩa là khách phải chờ thêm hai màn nữa mới dùng được. Backend
thì dùng chung — `survey_progress/` gọi được từ cả hai giao diện, nên phần nợ chỉ là lớp màn hình.

**Điều kiện xóa.** Khi `frontend-v2` làm tới phân hệ thu mua (đang thiếu 6 màn: Yêu cầu báo giá,
Công nợ, Yêu cầu thanh toán, Tiến độ mua hàng, Báo cáo, Phân quyền).

**Xóa bằng cách nào.** Dựng lại hai màn trên `frontend-v2` bằng `DataTable` + `conditional-filter`
dùng chung, gọi thẳng API cũ; xong thì tắt màn tương ứng ở `frontend/`.

---

## Nhật ký sổ

| Ngày | Ai | Việc |
|---|---|---|
| 17/08/2026 | — | Mở sổ. Ghi N-01…N-06 (nợ có sẵn). N-07 ghi trước ở dạng dự kiến |
| 17/08/2026 | — | Ghi N-08: giao diện CR-074/CR-075 làm ở `frontend/`, nợ lại bản `frontend-v2` |
