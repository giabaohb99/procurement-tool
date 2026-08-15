# PHASE 3 · BỘ MÁY PHÊ DUYỆT DÙNG CHUNG

> [← plan.md](./plan.md) · Nguồn: `03-lark-approver.md` (phần đường đi của phiếu), `01` nhóm I
> Ra được: khai luồng duyệt **bằng giao diện, không sửa mã, không deploy lại** — cho **Thu mua trước**, văn thư dùng ké sau.

**Viết lại toàn bộ ngày 14/08/2026.** Bản cũ (18 task) bị hủy vì hai lý do: (1) nó coi bộ máy là thứ *đứng cạnh* Thu mua, nay chốt là **gom hẳn về một luồng**; (2) nó giả định dữ liệu tổ chức đã đủ để làm điều kiện duyệt — **rà DB thì không đủ, thiếu rất nặng**. Phần văn thư tách khỏi phase này, không nhắc tới nữa.

## Tổng quan

| | |
|---|---|
| Ưu tiên | Cao |
| Trạng thái | ☐ Chưa bắt đầu |
| Task | **36** — nhóm A (11) nền tổ chức · B (2) mô hình · C (14) bộ máy · D (4) gom cổng · E (3) giao diện · F (2) sổ nợ |
| Migration | M-A (nền tổ chức, nhóm A) · M-B (6 bảng phê duyệt, T13) |
| Phụ thuộc | **Nhóm A chặn tất cả.** Không có chức vụ và pháp nhân thì không có điều kiện duyệt để mà khai |
| Người dùng đầu tiên | **Thu mua** — 5 luồng đang chạy thật, không phải văn bản |

---

## Phần 1 · Hiện trạng dữ liệu tổ chức — ĐO THẬT, không phải phỏng đoán

Đo trên DB local ngày 14/08/2026 (244 nhân sự, 15 pháp nhân, 18 phòng ban — dữ liệu thật đã đồng bộ):

| Thứ điều kiện duyệt cần | Hiện trạng đo được | Dùng được không |
|---|---|---|
| **Chức vụ** | `tab_employee.position` là `varchar(100)` **chữ tự do**. Không có bảng danh mục nào. 216/244 người ghi `"Nhân sự"` (đó là **tên phòng ban**, không phải chức vụ), 16 ghi `"Trưởng bộ phận"`, còn lại lẫn chuỗi demo `"Trưởng phòng Thu mua (Demo)"` | **Không** |
| **Cấp bậc chức vụ** (để "duyệt lên n cấp") | Không tồn tại. Không có cột số nào xếp hạng chức vụ | **Không** |
| **Phòng ban thuộc pháp nhân nào** | `tab_department.company_id = 0` cho **18/18** phòng ban | **Không** |
| **Nhân sự thuộc pháp nhân nào** | `tab_employee.company_id <> 0` chỉ **9/244** người (96% bỏ trống) | **Không** |
| **Trưởng phòng là ai** | `tab_department.manager_id = 0` cho **16/18** phòng | **Gần như không** |
| **Cây phòng ban** (leo cấp) | `tab_department.parent = 0` cho **18/18** | **Không** |
| **Cây pháp nhân** (mẹ/con) | `tab_company.parent = 0` cho **15/15**, dù cột có sẵn | **Không** |
| **Cấp trên trực tiếp của một người** | `tab_employee` **không có cột `manager_id`**. Chỉ suy gián tiếp qua `department.manager_id` | **Không** |
| **Người đại diện pháp nhân** | `legal_representative_id` NULL ở **3/15** công ty; `legal_rep_title` rỗng ở **14/15** | Một phần |
| **Phòng ban của phiếu** | `tab_purchase_request.department` là **`varchar(255)` tên phòng**, không phải khóa. Cùng kiểu ở `tab_purchase_order`, `tab_survey_request`. Dữ liệu thật có `'Phòng Marketing'` — **không tồn tại** trong `tab_department` | **Không** |
| **Số tiền của phiếu** (điều kiện hay dùng nhất) | `tab_payment_request.total` có. `tab_purchase_request` và `tab_purchase_order` **không có cột tổng ở header** — phải cộng từ dòng | Phải tính |
| **Vai trò** | Có, nhưng lẫn: `MANAGER` (id 2) và `dept_head` (id 11) và `manager_purchase` (id 8, demo) và `pur_manager` (id 14) cùng nghĩa "quản lý" | Cần dọn |

**Kết luận:** trong 7 cách chọn người duyệt của `03`, với dữ liệu hôm nay chỉ **2 cách chạy được** (chỉ định đích danh, và lấy từ ô trên phiếu). Năm cách còn lại — theo vai trò, theo trưởng phòng, lên n cấp, người đại diện pháp nhân, cả phòng ban — **không có dữ liệu để chạy**. Đó là lý do nhóm A đứng trước và chặn tất cả.

---

## Phần 2 · Danh sách task

Cột **L**: `BE` backend · `FE` frontend-v2 · `DB` migration · `DATA` nạp/làm sạch dữ liệu · `∞` nhiều tầng.

### Nhóm A · Nền tổ chức — LÀM TRƯỚC, chặn mọi thứ

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T01** | — | **Chốt 4 quyết định về tổ chức** | Trên bảng hiện trạng ở Phần 1. Bốn câu phải có câu trả lời trước khi gõ dòng mã đầu: **(a)** một phòng ban thuộc **một** pháp nhân hay **chạy cho nhiều** pháp nhân · **(b)** danh mục chức vụ gồm những chức vụ nào, chia mấy cấp · **(c)** "duyệt lên n cấp" leo theo **cây phòng ban** hay theo **cấp bậc chức vụ** · **(d)** `'Phòng Marketing'` trên phiếu là phòng thật chưa khai hay gõ nhầm. Ra một mục trong `plan.md`, không đẻ tệp mới |
| **P3-T02** | DB·BE | **Danh mục chức vụ** | Bảng `tab_position`: `code` · `name` · **`level` (số, nhỏ = cao)** · `company_id` (0 = dùng chung) · `is_active`. `level` là thứ làm cho "lên n cấp" và "từ cấp trưởng phòng trở lên" chạy được — không có nó thì chức vụ chỉ là nhãn |
| **P3-T03** | ∞·DATA | **Gắn chức vụ cho nhân sự** | Thêm `tab_employee.position_id`. **Giữ nguyên cột `position` chữ** làm dữ liệu cũ, không xóa. Màn Nhân sự đổi ô chức vụ từ gõ tay sang chọn danh mục. Nạp lại cho **244 người** — 216 người đang ghi `"Nhân sự"` phải rà thật, đó là tên phòng ban lọt vào ô chức vụ |
| **P3-T04** | ∞·DATA | **Gắn phòng ban vào pháp nhân** | **18/18 phòng đang `company_id = 0`.** Hình dạng theo quyết định (a) của T01: một-một thì điền `tab_department.company_id`; một-nhiều thì dựng `tab_department_company` (phòng × pháp nhân, kèm trưởng phòng riêng cho từng pháp nhân) |
| **P3-T05** | ∞·DATA | **Gắn nhân sự vào pháp nhân** | **235/244 người đang `company_id = 0`.** Suy từ phòng ban sau khi có T04, rồi **rà tay** phần không suy được. Không có bước này thì mọi điều kiện "theo pháp nhân của người nộp" đều rơi vào nhánh mặc định |
| **P3-T06** | ∞·DATA | **Khai trưởng phòng** | **16/18 phòng đang `manager_id = 0`.** Không khai thì cách chọn "trưởng phòng của người nộp" rơi thẳng vào đường dự phòng ngay ngày đầu, và người dùng sẽ kết luận là bộ máy hỏng |
| **P3-T07** | ∞·DATA | **Cây tổ chức + cấp trên trực tiếp** | `tab_department.parent` (18/18 đang 0) · `tab_company.parent` (15/15 đang 0) · thêm **`tab_employee.manager_id`** cho cấp trên trực tiếp — hiện **không có cột này**, cấp trên chỉ suy gián tiếp qua trưởng phòng. Hình dạng theo quyết định (c) của T01. **Nếu chốt là leo theo cấp bậc chức vụ thì T07 rút xuống chỉ còn `company.parent`** |
| **P3-T08** | DATA | **Người đại diện pháp nhân** | Điền `legal_representative_id` cho **3 công ty đang NULL**, `legal_rep_title` cho **14 công ty đang rỗng**. Rẻ, làm một buổi, mở khóa được một cách chọn người duyệt |
| **P3-T09** | ∞·DATA | **Khóa hóa phòng ban trên chứng từ** | YCMH · ĐMH · Yêu cầu khảo sát đang nối phòng ban bằng **chuỗi tên** (`department varchar(255)`). Thêm `department_id` **song song**, backfill bằng khớp tên, **giữ cột chữ** để không vỡ màn hình cũ. Chốt cách xử lý `'Phòng Marketing'` theo quyết định (d). Ghi vào sổ nợ F: `tab_user_scope` với `dim='department'` cũng đang lưu **tên phòng** làm giá trị — cùng một món nợ, dọn cùng lúc |
| **P3-T10** | BE | **Hàm lấy giá trị phiếu** | `doc_amount(db, entity, entity_id) -> Decimal` — chuẩn hóa "số tiền của phiếu" cho cả 5 loại. YCMH và ĐMH **không có cột tổng ở header**, phải cộng từ dòng; YCTT có `total` sẵn. Không có hàm này thì mỗi chỗ rẽ nhánh theo tiền tự cộng một kiểu, và số trên phiếu sẽ khác số bộ máy dùng để quyết định |
| **P3-T11** | BE | **Lưới an toàn: kiểm thử 5 luồng duyệt Thu mua hiện tại** | YCMH · khảo sát · yêu cầu khảo sát · ĐMH · yêu cầu thanh toán. **Viết trước khi đụng vào bất cứ thứ gì**, vì phase này sẽ sửa vào chúng thật. Đây là điều kiện nghiệm thu của cả phase, chạy lại ở mọi cổng |

**Cổng nhóm A:** 4 quyết định đã chốt · 244 nhân sự có chức vụ và pháp nhân · 18 phòng ban có pháp nhân và trưởng phòng · 5 kiểm thử Thu mua xanh. Chưa đạt thì **không sang nhóm B** — làm bộ máy trên nền dữ liệu rỗng là làm xong không chạy được.

### Nhóm B · Mô hình luồng

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T12** | — | **Khai thử 5 luồng thật ra giấy** | Đúng 5 luồng Thu mua đang chạy, khai bằng mô hình `tab_approval_flow` + `tab_approval_node` **có dùng chức vụ và cấp bậc của nhóm A**. **Chỗ nào khai không nổi là mô hình còn thiếu** — sửa trên giấy rẻ hơn sửa khi đã có 200 phiếu chạy. Chú ý luồng YCMH: nó có **hai lần duyệt** (trưởng phòng duyệt, rồi thu mua điều phối), khai không ra hai bước là mô hình sai |
| **P3-T13** | DB | **Migration M-B: 6 bảng phê duyệt** | `tab_approval_flow` · `tab_approval_node` · `tab_approval_instance` (có `flow_snapshot JSON`) · `tab_approval_task` · `tab_approval_action` · `tab_delegation`. Điều kiện trong `condition_json` phải khai được: **số tiền · pháp nhân · phòng ban · chức vụ · cấp bậc chức vụ · loại phiếu · gấp/không gấp**. Chỉ mục bắt buộc có ngay: **`tab_approval_task(assignee_employee_id, status)`** — truy vấn "việc của tôi" chạy mỗi lần ai mở trang chủ. `tab_approval_action` chỉ ghi thêm, grant MySQL không cấp `UPDATE`/`DELETE` |

### Nhóm C · Bộ máy chạy phiên (backend, tự kiểm bằng pytest)

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T14** | BE | **Chọn luồng** | Khớp theo `entity` + `company_id` + `department_id` + `condition_json`, nhiều luồng khớp thì `priority` nhỏ hơn thắng. Không luồng nào khớp → **lỗi rõ ràng, không tự duyệt qua** |
| **P3-T15** | BE | **Khởi tạo phiên + bản chụp luồng** | Chép **toàn bộ** định nghĩa luồng + node vào `flow_snapshot`, ghi `flow_version_no`. Từ đó engine **chỉ đọc bản chụp**. Đây là cột giải bài toán sửa luồng khi đang có phiếu chạy |
| **P3-T16** | BE | **Bảy cách chọn người duyệt** | 1 đích danh · 2 **theo vai trò** · 3 **theo chức vụ** (dùng `tab_position` của T02) · 4 **trưởng phòng của người nộp tại pháp nhân của phiếu** · 5 **lên n cấp** (theo quyết định (c): cây phòng ban hoặc `position.level`) · 6 người đại diện pháp nhân · 7 lấy từ một ô trên phiếu (phải kiểm người được chọn nằm trong danh sách cho phép). Cách 2·3·4·5·6 **chỉ chạy được sau nhóm A** |
| **P3-T17** | BE | **Nhiều người trong một bước** | Một người đủ · tất cả phải duyệt · lần lượt theo `seq` · đủ tỷ lệ (để bản sau). **Mặc định: một người từ chối là hỏng cả bước** |
| **P3-T18** | BE | **Rẽ nhánh + nhánh mặc định** | Đánh giá `condition_json`, số tiền lấy từ `doc_amount` của T10. **Mỗi chỗ rẽ phải có đúng một nhánh mặc định** — kiểm **lúc lưu luồng**, không phải lúc chạy phiếu. Không có nó thì phiếu rơi vào chỗ không nhánh nào nhận và **biến mất khỏi mọi danh sách** |
| **P3-T19** | BE | **Trùng người thì bỏ qua bước** | 3 mức: trùng liền kề · trùng bất kỳ chỗ nào phía trước · không bỏ qua. Khai **theo từng luồng**. Bỏ qua thì ghi **trạng thái riêng** kèm câu "bước 3 tự động qua vì ông X đã duyệt ở bước 2" — **không ghi thành 'đã duyệt'**, bản in dấu vết cần phân biệt được |
| **P3-T20** | BE | **Không tìm ra người duyệt** | Thứ tự: người thay thế khai sẵn ở node → trưởng phòng tại pháp nhân đó → quản trị kèm cảnh báo đỏ trên phiếu → **hết, phiếu đứng lại**. **Cố ý không có nhánh "tự động duyệt qua"** — không khai giá trị đó thì sau này không ai bật nhầm được |
| **P3-T21** | BE | **Chặn tự duyệt** | Người nộp không duyệt phiếu của chính mình. Luồng bắt buộc trùng thì **đẩy lên cấp trên**, không tự qua |
| **P3-T22** | BE | **Hành động của người duyệt** | Duyệt · từ chối (bắt lý do, kết thúc) · trả lại (bắt lý do, về người nộp **hoặc về một bước cụ thể**) · nộp lại (khai đi lại từ bước bị trả hay từ đầu) · rút lại (chỉ khi chưa ai duyệt). Mỗi hành động một dòng `tab_approval_action` |
| **P3-T23** | BE | **Ủy quyền có thời hạn** | Bắt buộc có ngày bắt đầu/kết thúc, quản trị đặt hộ được. **Cấm ủy quyền dây chuyền** — A ủy cho B thì B không ủy tiếp phần việc nhận từ A, kiểm lúc lưu. Ghi **cả hai danh tính**: người bấm và người được thay |
| **P3-T24** | BE | **Hạn duyệt + nhắc** | `sla_hours` mỗi bước → hạn của việc. Job định kỳ: sắp quá hạn nhắc, quá hạn nhắc tiếp, đếm số lần nhắc. Đi qua chuông + thư. Leo cấp để bản sau |
| **P3-T25** | BE | **Bàn giao hàng loạt + cảnh báo trước khi tắt tài khoản** | Chọn nhiều việc của người nghỉ, chuyển sang người khác một lần. Khi HR bấm tắt một nhân sự: **cảnh báo "người này đang giữ 12 phiếu"** trước khi cho tắt |
| **P3-T26** | BE | **Sổ đăng ký việc chạy kèm, cùng transaction** | `on_approved / on_rejected / on_returned(db, entity, entity_id, instance)`. Duyệt YCMH hiện kéo theo đổi trạng thái, điều phối, chuông, thư — **không có chỗ cắm này thì chuyển sang bộ máy là mất sạch tác dụng phụ**. Việc chạy kèm ném lỗi → **rollback cả hành động duyệt**, không để phiếu "đã duyệt nhưng chưa làm gì" |
| **P3-T27** | BE | **Quyền đọc phiếu cho người được giao duyệt** | `approval_task` là entity mới, mà phạm vi `assigned` đang **viết tay cho từng entity** ở `core/scoping.py:37–66` nên **không được lọc tự động**. Nặng hơn: người được giao duyệt một phiếu **ngoài phạm vi dữ liệu thường ngày của họ** sẽ không mở nổi phiếu mình phải duyệt. Luật: **được giao duyệt phiếu nào thì đọc được đúng phiếu đó**, hết phiên là hết, **không nới phạm vi chung**. Kiểm thử: người pháp nhân B duyệt phiếu pháp nhân A → mở được đúng phiếu đó, **không** thấy thêm phiếu nào khác của A |

### Nhóm D · Gom về một cổng và chuyển Thu mua sang

> Cách làm đã chốt: **thay đúng đoạn kiểm tra phân quyền**, hoặc **thêm một nhánh `if` ngay trong hàm đó** để đổi đường. Không viết lại nghiệp vụ. Mỗi chỗ chèn **phải vào sổ nợ ở nhóm F ngay lúc chèn**.

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T28** | BE | **Một cổng duy nhất — bê nguyên xi, chưa đổi hành vi** | `modules/approval/gate.py`, đúng một hàm `approval_state(db, user, entity, entity_id)` trả về `{instance_id, status, step, waiting_on[], can_approve, can_reject, can_return, can_withdraw, block_reason}`. **Bê nguyên logic duyệt của 5 module Thu mua vào, không sửa một dòng nghiệp vụ** — kể cả `_in_approve_scope` ở `purchase_request/controller.py:45`, kể cả chỗ trông có vẻ sai. Controller bỏ tính tay, gọi cổng. Giao diện **không sửa**. Không đụng DB. **Chống chỉ định: nhân tiện sửa luôn cái thấy sai.** Nghiệm thu: 5 kiểm thử T11 xanh y nguyên, `git diff` chỉ có mã bị **dời chỗ** |
| **P3-T29** | BE | **Nhánh `if` đổi đường + cờ theo từng loại phiếu** | `setting` key `approval_engine.{entity}` mặc định `false`. Nhánh `if` nằm **bên trong cổng**, đúng một chỗ: bật → trả lời bằng `tab_approval_task`, tắt → trả lời bằng đoạn mã cũ đã dời vào. Tắt cờ là về đường cũ **ngay, không deploy**. Vào sổ nợ F |
| **P3-T30** | BE·FE | **Hợp đồng dữ liệu cho giao diện** | Mọi phiếu duyệt được trả về **cùng một khối `approval`** như trên. Hiện backend phát ra **12 tên cờ rời rạc** (`can_approve`, `can_dispatch`, `can_process`, `can_khao_sat_lai`…) — **giữ song song** tới khi dọn ở T36, đừng xóa ngay kẻo vỡ `frontend/` đang chạy thật. Thêm `?waiting_for_me=1` trên endpoint danh sách và `GET /approvals/my-tasks`, chạy trên chỉ mục của T13. **Giao diện tuyệt đối không tự suy luận quyền duyệt** |
| **P3-T31** | BE·DATA | **Chuyển 5 luồng Thu mua, mỗi luồng một lần** | Thứ tự: **yêu cầu thanh toán** (đơn giản nhất) → khảo sát → yêu cầu khảo sát → **YCMH** (khó nhất: hai lần duyệt + `_in_approve_scope` + điều phối) → **ĐMH**. Mỗi luồng đi đúng bốn nhịp: khai luồng bằng giao diện T32 → chạy kiểm thử của luồng đó **ở cả hai chế độ cờ, phải ra cùng kết quả** → bật ở dev, theo dõi → mới sang luồng kế. **Không bật hai luồng cùng lúc** |

### Nhóm E · Giao diện

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T32** | FE | **Trình khai luồng duyệt** | Màn nặng nhất. Danh sách luồng + trình soạn: danh sách bước dọc kéo đổi thứ tự, mỗi bước một panel (cách chọn người duyệt, nhiều người, người thay thế, hạn), khối điều kiện rẽ nhánh **có đủ: số tiền · pháp nhân · phòng ban · chức vụ · cấp bậc · loại phiếu · gấp**, **ép khai nhánh mặc định**. Ô "không tìm ra người duyệt" **không có lựa chọn tự duyệt qua**. Nút xem trước đường đi. **Không dùng thư viện flow-chart** — danh sách dọc đủ và rẻ hơn nhiều |
| **P3-T33** | FE | **Panel duyệt dùng chung** | `<ApprovalPanel entity entityId />` đọc **đúng khối `approval` của T30**, không tự suy luận: nút duyệt/từ chối/trả lại/rút, ô ý kiến + đính kèm (tái dùng `procurement/document-comments` + `mention-input`), dòng thời gian dấu vết, hiện phiên bản luồng đang chạy, hiện lý do khi không được duyệt. **Dựng và nghiệm thu trên trang chi tiết YCMH** (`purchase-request-detail-page.tsx`). Gỡ luôn chỗ rò `(data.can_approve \|\| canManage)` ở dòng **513** và **520** — `canManage = can('purchase_request','cancel')`, tức giao diện đang **tự đoán** "có quyền hủy nghĩa là quản lý nên chắc được trả về", suy đoán này không tồn tại ở backend |
| **P3-T34** | FE | **Việc của tôi · phiếu kẹt · in dấu vết · ủy quyền** | `my-tasks-page.tsx` 3 tab: chờ tôi · tôi đã nộp · tôi đã duyệt — lấy từ `GET /approvals/my-tasks`, **không gọi cổng cho từng dòng** (N+1 sẽ giết trang chủ). `stuck-instances-page.tsx` liệt kê phiếu không ai xử lý. `approval-trace-print-page.tsx` bản in dấu vết, ghi rõ "B duyệt thay A theo ủy quyền số 12" và "bước 3 tự qua vì …". `delegation-page.tsx` khai ủy quyền |

### Nhóm F · Sổ nợ và dọn dẹp

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T35** | — | **Mở sổ nợ, ghi ngay lúc chèn** | Tệp `plans/260814-1036-van-thu-p0-p3/no-can-don.md`, mở **cùng lúc với T28**, ghi **ngay khi chèn chứ không ghi sau**. Mỗi dòng: tệp · dòng · chèn cái gì · điều kiện xóa được. Bốn nhóm nợ đã biết trước: **(1)** mọi nhánh `if` đổi đường ở T29 · **(2)** đoạn mã duyệt cũ bê nguyên vào cổng ở T28, gồm `_in_approve_scope` · **(3)** 12 tên cờ `can_*` giữ song song ở T30 · **(4)** **phân quyền vai trò thành thừa** — `MANAGER` (id 2) và `dept_head` (id 11) và `manager_purchase` (id 8, demo) và `pur_manager` (id 14) cùng nghĩa "quản lý"; khi bước duyệt chuyển sang khai bằng luồng thì một số quyền `approve` không còn dùng, cộng `tab_user_scope` với `dim='department'` đang lưu **tên phòng** làm giá trị |
| **P3-T36** | ∞ | **Dọn** | Chỉ làm khi luồng đó đã chạy thật ổn **ở prod**. Xóa nhánh `if`, xóa mã cũ trong cổng, xóa `_in_approve_scope`, xóa cờ `can_*` hết người dùng, dọn vai trò/quyền thành thừa. **Task cuối cùng, không gộp vào T31.** Không làm là còn ba cơ chế cùng trả lời một câu hỏi — đúng cái mà việc gom này sinh ra để dẹp |

---

## Phần 3 · Điểm cần biết trước

1. **Hai câu hỏi khác nhau, đừng trộn.** (a) *"Chức danh này về nguyên tắc được duyệt loại phiếu này không?"* — bảng phân quyền vai trò, ít khi đổi. (b) *"Phiếu số 88 ở bước 2 có đang chờ chính người này không?"* — `tab_approval_task`, đổi từng phiếu từng bước. Phải qua **cả hai**. Hiện câu (b) đang được viết tay bằng cách bẻ cong câu (a): `_in_approve_scope` lọc `scope in ("proc","all")` chính là **một bước duyệt bị nhét vào cột phạm vi dữ liệu**.
2. **Điều kiện duyệt chỉ mạnh bằng dữ liệu tổ chức đứng sau nó.** Toàn bộ Phần 1 nói đúng một điều: hôm nay khai luồng "trưởng phòng duyệt" thì 16/18 phòng không có trưởng, và 235/244 người không biết thuộc pháp nhân nào.
3. **Chức vụ phải là danh mục có cấp bậc, không phải nhãn.** Có `level` thì mới khai được "từ cấp trưởng phòng trở lên" và "lên 2 cấp". Không có thì chức vụ chỉ dùng để so bằng đúng một chuỗi, và sẽ hỏng ngay lần đầu ai đó đổi tên chức vụ.
4. **Bản chụp luồng là cột giải bài toán sửa luồng khi đang có phiếu chạy.** Phiếu chạy theo **bản chụp của chính nó**.
5. **Nhánh mặc định là cột chống mất phiếu.** Không có là phiếu rơi vào trạng thái không nhánh nào nhận.
6. **Không có chỗ cắm việc chạy kèm cùng transaction thì không chuyển được Thu mua.** Xem T26.
7. **`apply_scope` sẽ giấu việc của chính người được giao duyệt.** Xem T27.
8. **Chỉ mục quan trọng nhất cả hệ thống:** `tab_approval_task(assignee_employee_id, status)`.
9. **Nhật ký mà sửa được thì không còn là nhật ký.** `tab_approval_action` chỉ ghi thêm, grant MySQL không cấp `UPDATE`/`DELETE`.

## Phần 4 · Tệp đụng tới

**Tạo BE:** `modules/position/{model,schema,service,controller}.py` (T02) · `modules/approval/{__init__,model,schema,controller}.py` · `modules/approval/{gate,hooks,flow_resolver,engine,assignee_resolver,duplicate_rule,delegation_service,reminder_job,doc_amount}.py` · `migrations/versions/<M-A>.py` · `<M-B>.py`
**Tạo test:** `test_approval_gate.py` · `test_approval_engine.py` · `test_approval_snapshot.py` · `test_approval_assignee_by_position.py` · `test_approval_duplicate_skip.py` · `test_approval_no_approver.py` · `test_approval_hooks_transaction.py` · `test_approval_reader_scope.py` · `test_delegation_chain.py` · 5 tệp kiểm thử luồng Thu mua (T11)
**Tạo FE:** `modules/approval/routes.tsx` · `pages/flow-{list,detail}-page.tsx` · `my-tasks-page.tsx` · `stuck-instances-page.tsx` · `delegation-page.tsx` · `approval-trace-print-page.tsx` · `components/{flow-node-editor,approver-picker,branch-condition-editor,approval-panel,approval-trace-timeline}.tsx` · `api/approval-api.ts` · `hooks/use-approval-{flows,tasks,instance}.ts` · `types/approval.ts` · màn danh mục chức vụ trong `modules/hr`
**Sửa nền tổ chức (nhóm A):** `modules/company/model.py` · `modules/department/model.py` · `modules/employee/{model,schema,service}.py` · `modules/purchase_request/model.py` · `modules/purchase_order/model.py` · `modules/survey_request/model.py` (thêm `department_id`) · `frontend-v2/src/modules/hr/**`
**Sửa để gom cổng (nhóm D — chỉ đoạn kiểm tra phân quyền):** `modules/purchase_request/controller.py` · `modules/purchase_order/controller.py` · `modules/payment_request/controller.py` · `modules/survey/controller.py` · `modules/survey_request/controller.py`
**Sửa chung:** `app/main.py` · `core/permissions.py` (entity `approval_flow`, `approval_task`, `position`) · `core/all_models.py` · `core/scoping.py` (T27) · `frontend-v2/src/app/router/module-registry.ts` · `frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx`

## Phần 5 · Todo

Nhóm A — nền tổ chức (chặn mọi thứ):

- [ ] P3-T01 · Chốt 4 quyết định về tổ chức
- [ ] P3-T02 · Danh mục chức vụ + cấp bậc
- [ ] P3-T03 · Gắn chức vụ cho 244 nhân sự
- [ ] P3-T04 · Gắn 18 phòng ban vào pháp nhân
- [ ] P3-T05 · Gắn 235 nhân sự vào pháp nhân
- [ ] P3-T06 · Khai trưởng phòng cho 16 phòng
- [ ] P3-T07 · Cây tổ chức + cấp trên trực tiếp
- [ ] P3-T08 · Người đại diện pháp nhân (3 NULL, 14 rỗng chức danh)
- [ ] P3-T09 · Khóa hóa phòng ban trên chứng từ
- [ ] P3-T10 · Hàm lấy giá trị phiếu
- [ ] P3-T11 · **Kiểm thử 5 luồng duyệt Thu mua hiện tại** (lưới an toàn)

Nhóm B — mô hình:

- [ ] P3-T12 · Khai thử 5 luồng thật ra giấy
- [ ] P3-T13 · M-B: 6 bảng + chỉ mục + grant append-only

Nhóm C — bộ máy:

- [ ] P3-T14 · Chọn luồng
- [ ] P3-T15 · Khởi tạo phiên + bản chụp
- [ ] P3-T16 · Bảy cách chọn người duyệt (có chức vụ, có cấp bậc)
- [ ] P3-T17 · Nhiều người trong một bước
- [ ] P3-T18 · Rẽ nhánh + ép nhánh mặc định
- [ ] P3-T19 · Trùng người thì bỏ qua, ghi trạng thái riêng
- [ ] P3-T20 · Không tìm ra người duyệt — **không có bước tự duyệt qua**
- [ ] P3-T21 · Chặn tự duyệt
- [ ] P3-T22 · Duyệt / từ chối / trả lại đúng bước / nộp lại / rút lại
- [ ] P3-T23 · Ủy quyền có hạn, cấm dây chuyền
- [ ] P3-T24 · Hạn duyệt + nhắc
- [ ] P3-T25 · Bàn giao hàng loạt + cảnh báo trước khi tắt tài khoản
- [ ] P3-T26 · Việc chạy kèm cùng transaction
- [ ] P3-T27 · Quyền đọc phiếu cho người được giao duyệt

Nhóm D — gom cổng:

- [ ] P3-T28 · `gate.py` — một hàm, bê nguyên xi
- [ ] P3-T29 · Nhánh `if` đổi đường + cờ theo loại phiếu
- [ ] P3-T30 · Hợp đồng dữ liệu `approval` cho giao diện
- [ ] P3-T31 · Chuyển 5 luồng Thu mua, mỗi luồng một lần

Nhóm E — giao diện:

- [ ] P3-T32 · Trình khai luồng duyệt
- [ ] P3-T33 · `<ApprovalPanel>` trên YCMH + gỡ rò `canManage`
- [ ] P3-T34 · Việc của tôi · phiếu kẹt · in dấu vết · ủy quyền

Nhóm F — sổ nợ:

- [ ] P3-T35 · Mở `no-can-don.md` **cùng lúc với T28**
- [ ] P3-T36 · Dọn sau khi prod chạy ổn

## Phần 6 · Nghiệm thu

| Bài kiểm | Kết quả phải là |
|---|---|
| Mở màn Nhân sự, chọn chức vụ | Là **danh mục có cấp bậc**, không phải ô gõ tay. 244 người đều có chức vụ và pháp nhân |
| Khai một luồng "từ cấp trưởng phòng trở lên duyệt" | Chạy đúng — nghĩa là dữ liệu chức vụ và cấp bậc đã đủ |
| Khai một luồng 4 bước bằng giao diện | Phiếu chạy đúng qua 4 người, **không sửa dòng mã nào, không deploy lại** |
| Sau T28: chạy lại 5 kiểm thử Thu mua | **Vẫn xanh**, `git diff` chỉ có mã **dời chỗ**, không có thay đổi nghiệp vụ |
| Sau mỗi luồng ở T31: chạy kiểm thử ở **cả hai chế độ cờ** | Cờ tắt và cờ bật cho **cùng một kết quả** |
| Tắt cờ `approval_engine.purchase_request` | Quay về đường duyệt cũ **ngay, không cần deploy** |
| Người bước 1 cũng là người bước 3 | Bước 3 tự bỏ qua, nhật ký ghi rõ lý do, **không ghi thành "đã duyệt"** |
| Sửa luồng khi có 5 phiếu đang chạy | 5 phiếu vẫn đi theo luồng cũ tới khi kết thúc |
| Tạo phiếu không khớp điều kiện nhánh nào | Rơi vào nhánh mặc định, **không biến mất khỏi mọi danh sách** |
| Tắt trạng thái một nhân sự đang giữ 3 phiếu | Cảnh báo trước, 3 phiếu chuyển người, **không phiếu nào tự động duyệt qua** |
| A ủy quyền cho B, B thử ủy tiếp cho C | Bị chặn, báo lỗi rõ |
| Người pháp nhân B được giao duyệt một phiếu của pháp nhân A | Mở được **đúng phiếu đó**, **không** thấy thêm phiếu nào khác của A |
| Việc chạy kèm (cấp số / điều phối) ném lỗi giữa chừng | **Rollback cả hành động duyệt** |
| Grep `frontend-v2` tìm chỗ tự suy luận quyền duyệt | **Không còn** `can_approve \|\| canManage` hay tương tự |
| Mở `no-can-don.md` | Có **đủ** mọi chỗ đã chèn `if`, mọi hàm đã thay, mọi vai trò/quyền thành thừa |

## Phần 7 · Rủi ro

| Rủi ro | Mức | Giảm bằng |
|---|---|---|
| **Làm bộ máy trước, phát hiện dữ liệu tổ chức rỗng sau** | **Cao** | Nhóm A đứng trước và **chặn cứng**. Phần 1 đã đo sẵn con số để không ai nghĩ "chắc dữ liệu ổn" |
| Nạp lại chức vụ cho 244 người bị làm ẩu | Cao | 216 người đang ghi `"Nhân sự"` — đó là tên **phòng ban**, không phải chức vụ. Phải rà thật, không map máy móc |
| Sửa vào 5 luồng Thu mua đang chạy thật | **Cao** | T11 viết **trước** · T28 chỉ dời mã, kiểm thử làm chứng · T31 chuyển **từng luồng một**, mỗi luồng xanh ở cả hai chế độ mới sang luồng kế · cờ tắt là về đường cũ không cần deploy |
| Chèn `if` khắp nơi rồi quên, thành mã hai đường vĩnh viễn | **Cao** | T35 mở sổ nợ **cùng lúc với T28**, ghi ngay lúc chèn. T36 là task bắt buộc, không bỏ |
| Mô hình luồng không đủ mềm, vẫn phải sửa mã cho từng loại | Trung bình | T12 khai thử 5 luồng ra giấy. Sửa trên giấy rẻ hơn sửa khi đã có 200 phiếu chạy |
| Phiếu kẹt không ai biết | Trung bình | Ép nhánh mặc định (T18) + màn phiếu kẹt (T34) + cảnh báo đỏ khi rơi về quản trị |
| Trình khai luồng phình thành công cụ vạn năng | Cao | Chỉ làm phần bản 1: không kéo thả biểu mẫu, không luồng con, không chuyển tiếp/thêm người duyệt giữa chừng, không mô phỏng |
| "Việc của tôi" chậm khi nhiều phiếu | Trung bình | Chỉ mục `(assignee_employee_id, status)` có ngay từ T13, không thêm sau |
| Xóa cờ `can_*` cũ làm vỡ `frontend/` đang chạy thật | Trung bình | T30 **giữ song song**; chỉ xóa ở T36 |

## Phần 8 · Bốn quyết định đang chặn (T01)

| | Câu hỏi | Chặn task nào | Không trả lời thì |
|---|---|---|---|
| **a** | Một phòng ban thuộc **một** pháp nhân hay **chạy cho nhiều** pháp nhân? | T04, T06, T16 | Không biết `tab_department.company_id` là đủ hay phải dựng bảng phòng × pháp nhân |
| **b** | Danh mục chức vụ gồm những chức vụ nào, chia mấy cấp? | T02, T03, T16 | Không nạp được dữ liệu, và "từ cấp trưởng phòng trở lên" không khai được |
| **c** | "Lên n cấp" leo theo **cây phòng ban** hay theo **cấp bậc chức vụ**? | T07, T16 | Nếu chọn cấp bậc thì T07 rút gọn còn mỗi `company.parent` — chênh nhau khá nhiều công |
| **d** | `'Phòng Marketing'` trên phiếu: phòng thật chưa khai, hay gõ nhầm? | T09 | Không backfill được `department_id`, phiếu đó thành không có phòng ban |
