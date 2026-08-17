# VĂN THƯ — PHASE 0→3 · KẾ HOẠCH TRIỂN KHAI

> Full-stack (backend `backend/app` + frontend `frontend-v2`) · nguồn: `van-thu/00`–`05`
> Phạm vi: **P0 vá nền · P1 danh mục+số hiệu · P2 soạn thảo+phiên bản · P3 bộ máy phê duyệt**
> Ngoài phạm vi: P4 ban hành/clone, P5 quyền+tra cứu (chờ câu B3/B5/B6) — sẽ lên plan riêng.

## 👉 Bắt đầu từ đâu

**[`thu-tu-thuc-hien.md`](./thu-tu-thuc-hien.md) — đọc tệp này trước khi làm.** Bốn tệp phase bên dưới nói *cái gì phải làm*; tệp thứ tự nói *ai làm gì, theo thứ tự nào*.

Chốt 14/08/2026: **hai người làm song song trên hai nhánh việc.**

| | Nhánh | Người | Nội dung |
|---|---|---|---|
| **A** | Nền tổ chức + bộ máy phê duyệt | chủ dự án | `phase-03` nhóm A → B → C → E → F. Người dùng đầu tiên là **văn thư** (quyết định 10, 17/08/2026). Nhóm D (chuyển 5 luồng Thu mua) **tách ra làm sau** |
| **B** | Văn thư | người thứ hai | Bước 1 → 2 → 3 của `thu-tu-thuc-hien.md`: nắn nền module đang có → danh mục → soạn thảo và phiên bản |

Nền chung còn **P0-T10** và **P0-T11**. Nhánh A **không chờ nhánh B ở bất kỳ đâu**; ngược lại, từ 17/08/2026 nhánh B là **nơi cắm đầu tiên** của bộ máy — chỗ cắm đã sẵn (`tab_doc_type.needs_approval` + `default_flow_id`), nên luồng duyệt một bước viết tay tạm của bước 3b chỉ sống tới khi nhóm C xong.

## Tiến độ

| Phase | Tệp | Task | Trạng thái |
|---|---|---|---|
| 0 · Vá nền | [phase-00-va-nen.md](./phase-00-va-nen.md) | 13 | ☐ 3 task ở nền chung (T01, T10, T11) · 4 task vào nhánh B khi làm đính kèm (T02–T04, T12) · 6 task còn lại chạy bất kỳ lúc nào, **chặn việc lên prod** |
| 1 · Danh mục và số hiệu | [phase-01-danh-muc-va-so-hieu.md](./phase-01-danh-muc-va-so-hieu.md) | 14 | ☐ nhánh B (P1-T01 ở nền chung) |
| 2 · Soạn thảo và phiên bản | [phase-02-soan-thao-va-phien-ban.md](./phase-02-soan-thao-va-phien-ban.md) | 18 | ☐ nhánh B |
| 3 · Bộ máy phê duyệt dùng chung | [phase-03-bo-may-phe-duyet.md](./phase-03-bo-may-phe-duyet.md) | **37** | ☐ nhánh A — viết lại 14/08/2026, **đảo người dùng đầu tiên 17/08/2026**. Người dùng đầu tiên là **văn thư**; Thu mua giữ nguyên, vào sổ nợ. Nhóm A (nền tổ chức) vẫn chặn tất cả |
| — · Sổ nợ kỹ thuật | [no-can-don.md](./no-can-don.md) | — | ● Mở 17/08/2026 · 7 món nợ (N-01…N-07). **Không phải danh sách việc** — là chỗ ghi những gì đang cố tình nợ và điều kiện trả |

**82 task** (45 của văn thư + P0, 37 của P3) — **trừ 2 task trùng còn 80 việc thật**: `P0-T01` nay làm ở `P3-T11`, phần `tab_department_company` của `P1-T01` nay làm ở `P3-T04`. Hai dòng cũ giữ nguyên trong tệp phase để không đứt tham chiếu, nhưng **đừng làm hai lần**. Mã task: `P{phase}-T{nn}`. Cột **L** trong từng phase: `BE` backend · `FE` frontend-v2 · `DB` migration · `DATA` nạp/làm sạch dữ liệu · `∞` nhiều tầng.

> **P3 viết lại (14/08/2026).** Hủy bản 18 task cũ. Hai thay đổi gốc: **(1)** bộ máy không còn "đứng cạnh" Thu mua mà **gom hẳn** — thay đúng đoạn kiểm tra phân quyền, hoặc thêm một nhánh `if` trong hàm đó để đổi đường, chuyển dần từng luồng, có **sổ nợ** để dọn sau; **(2)** rà DB thì **dữ liệu tổ chức không đủ để làm điều kiện duyệt** — chức vụ là chữ tự do, 18/18 phòng ban không gắn pháp nhân, 235/244 nhân sự không gắn pháp nhân, 16/18 phòng không có trưởng. Nên **11 task nền tổ chức đứng trước và chặn cứng**. Số đo đầy đủ ở Phần 1 của `phase-03`. Điều này **thay quyết định 5** trong change-log.

## Phụ thuộc

```
        ┌──▶ NHÁNH A: P3 nhóm A (nền tổ chức, 11 task) ──▶ B ──▶ C ──▶ E ──▶ F
        │        chức vụ · pháp nhân · trưởng phòng · cây tổ chức        │
NỀN CHUNG                                                    P3-T37 đấu nối VĂN THƯ
P0-T10  └──▶ NHÁNH B: P1 ──▶ P2  (văn thư — là NGƯỜI DÙNG ĐẦU TIÊN của bộ máy)
P0-T11

NHÓM D (chuyển 5 luồng Thu mua) ── TÁCH RA, làm sau, ghi sổ nợ trước
6 task P0 còn lại ─────────── chạy bất kỳ lúc nào, chặn cứng việc lên prod
(P5 quyền+tra cứu: song song được với nhánh A, chưa có plan)
```

- Sơ đồ **cũ** `P0 ▶ P1 ▶ P2 ▶ P3 ▶ P4` là **phụ thuộc của tính năng người dùng thấy**, không phải phụ thuộc của mã và cũng không phải thứ tự chạy. Thứ tự chạy ở [`thu-tu-thuc-hien.md`](./thu-tu-thuc-hien.md).
- **P3 phụ thuộc P2 ở đúng một chỗ: `P3-T37` đấu nối văn thư.** Người dùng đầu tiên của bộ máy là **văn thư** (quyết định 10) — bước duyệt văn bản hiện là **một bước cứng** (`require("document","approve")` → `service.approve`), thay bằng bộ máy là việc sạch, không kéo theo nghiệp vụ phụ. Nhóm A → B → C của P3 **vẫn không chờ P2**; chỉ riêng T37 chờ P2 xong.
- **P1-T01 không còn là nền chung.** Việc gắn phòng ban vào pháp nhân đã thành **P3-T04** trong nhóm A, vì nhánh A cần nó gấp hơn nhánh B nhiều. Nền chung rút còn **P0-T10** và **P0-T11**.
- **Nhóm A của P3 chặn cứng phần còn lại của P3.** Không có chức vụ, pháp nhân, trưởng phòng thì 5 trong 7 cách chọn người duyệt **không có dữ liệu để chạy**. Số đo ở Phần 1 của `phase-03`.
- P0 **tách làm ba**: P0-T10/T11 vào nền chung · kho tệp riêng tư (T02/T03/T04/T12) vào nhánh B khi làm đính kèm · **6 task còn lại** (T05–T09, T13) chạy bất kỳ lúc nào và **chặn cứng việc lên prod**. **P0-T01 chuyển hẳn thành P3-T11** vì nó là lưới an toàn của riêng nhánh A.
- **P3-T11** (kiểm thử 5 luồng duyệt Thu mua) **làm sớm nhất có thể**, không chờ trả lời câu hỏi nào — phase này sẽ sửa thật vào 5 luồng đó.
- P2 duyệt **nội dung văn bản** bằng luồng một bước viết tay tạm thời, tự dựng, **đừng chờ nhánh A**. Chuyển sang bộ máy chung là việc sau khi P3 xong.
- P1–P3 **không bị chặn** bởi 17 câu hỏi ở `00` mục 8 (chỉ chặn P4 trở đi).

### Luật khi hai người chạy song song

| Chỗ va chạm | Luật |
|---|---|
| **Chuỗi Alembic** | Alembic một head duy nhất (hiện 80 tệp). Hai nhánh cùng đẻ migration là gãy `upgrade head`. Nhánh A giờ **cũng đẻ nhiều migration** (nhóm A nền tổ chức + M-B 6 bảng), không còn chuyện một người giữ chuỗi. Luật: **`fetch` trước khi sinh revision**, và kiểm `alembic heads` chỉ ra **một** dòng trước khi đẩy; ra hai head thì dựng `merge revision` ngay, đừng để dồn |
| `core/permissions.py` | **P0-T10 làm một lần ở nền chung**, khai luôn cả entity văn thư (`document`, `doc_type`, `document_acl`) lẫn entity phê duyệt (`approval_flow`, `approval_task`). Không ai sửa tệp này lần hai |
| `core/all_models.py` · `app/main.py` | Mỗi bên thêm vài dòng ở cuối, xung đột dễ gỡ. Cứ `fetch` trước khi sửa |
| `frontend-v2/src/app/router/module-registry.ts` | Mỗi nhánh thêm đúng một dòng (`document` / `approval`) |
| Thư mục mã | Nhánh A ở `modules/approval` + `modules/position` (BE + FE), nhánh B ở `modules/doc_catalog` + `modules/document`. **Nhánh A còn đụng thêm:** `modules/{company,department,employee}`, `core/scoping.py`, `frontend-v2/src/modules/hr/**` — nhánh B không đụng tới những chỗ đó. **5 controller Thu mua: KHÔNG ai đụng trong phase này** (quyết định 10) |
| `modules/document/{controller,service}.py` | **Chỗ va chạm mới từ 17/08/2026.** P3-T37 sửa đúng hai endpoint `submit` / `approve` của văn bản, mà nhánh B đang dựng luồng tạm ngay tại đó. Luật: nhánh B **cứ làm luồng tạm bình thường**, đừng né; T37 làm sau và thay hẳn, không làm song song. Nhánh A **báo trước** cho nhánh B ít nhất một ngày trước khi vào T37 |

## Điều kiện chuyển phase

Hai nhánh chạy song song nên không còn một dãy cổng nối đuôi nhau. Cổng của từng nhánh:

| Nhánh | Từ | Sang | Điều kiện |
|---|---|---|---|
| chung | nền chung | tách nhánh | Entity mới đã khai đủ trong `core/permissions.py` (P0-T10) · chuông lọc theo app (P0-T11) |
| B | P1 | P2 | **Bài kiểm 100 kết nối cấp số** ra đúng 100 số liên tiếp · hủy văn bản không trả số về · sang năm mới sổ theo năm reset, sổ mã bất biến không reset |
| B | P2 | xong | Một người đi hết đường tạo → soạn → gửi duyệt → phiên bản 2 trên dev · 5 phép thử ở `02` mục 6 đạt · ≥3 người ngoài đội phần mềm bấm thử |
| A | nhóm A | nhóm B | 4 quyết định đã chốt · 244 nhân sự có chức vụ và pháp nhân · 18 phòng ban có pháp nhân và trưởng phòng · **5 kiểm thử Thu mua xanh** (lưới an toàn chứng minh **không** đụng vào Thu mua) |
| A | nhóm B | nhóm C | 5 luồng Thu mua **và** luồng văn thư đều khai được trên giấy bằng mô hình T13 · quyết định 11 (a)(b)(c) đã áp vào M-B |
| A | nhóm C+E | P3-T37 | Khai được một luồng 4 bước bằng giao diện, phiếu chạy đúng, không sửa mã · việc chạy kèm cùng transaction (T26) đã có |
| A | P3-T37 | xong | Một văn bản đi hết đường tạo → gửi duyệt → duyệt **qua bộ máy** trên dev · loại có `needs_approval = false` vẫn chạy đường một bước cũ · **5 kiểm thử Thu mua vẫn xanh y nguyên** |
| A | — | nhóm D (làm sau) | Chỉ mở khi bộ máy đã chạy thật ổn với văn thư ở prod. Điều kiện cũ của T28/T29/T31 giữ nguyên trong `phase-03` |
| cả hai | dev | **prod** | 6 task P0 còn lại đã xong và chạy prod ổn định. Xem ràng buộc ở [`thu-tu-thuc-hien.md`](./thu-tu-thuc-hien.md) |

## Quyết định đã chốt trong plan này

| # | Quyết định | Vì sao |
|---|---|---|
| 1 | `tab_file_access_log` tạo **sớm ở M1 (phase 0)** thay vì M10 | H03 "ghi nhật ký mọi lượt xem/tải" thuộc phase 0; không có bảng thì không ghi được |
| 2 | Backend đặt ở **3 module mới**: `doc_catalog`, `document`, `approval` | Theo `module pattern` của `CLAUDE.md`; không nhét vào module có sẵn |
| 3 | FE dựng trong `frontend-v2/src/modules/document` (đã có) + module mới `approval` | Tái dùng 3 danh mục (loại · mức mật/khẩn · đối tác) + data-table + conditional-filter + rich-text-editor đã có |
| 4 | `store/local-collection.ts` **gỡ dần theo từng task**, không gỡ một lần | Mỗi màn nối API xong thì bỏ collection tương ứng; tránh một PR khổng lồ |
| ~~5~~ | ~~Bộ máy duyệt **đứng cạnh** 5 luồng viết tay của Thu mua~~ | **Thay ngày 14/08/2026 bằng quyết định 8** |
| 8 | **Gom hẳn 5 luồng Thu mua vào bộ máy duyệt**, không để đứng cạnh. Cách làm: thay **đúng đoạn kiểm tra phân quyền**, hoặc thêm một nhánh `if` **ngay trong hàm đó** để đổi đường; chuyển **dần từng luồng một**; mọi chỗ chèn vào **sổ nợ `no-can-don.md`** và dọn ở P3-T36. Cờ `approval_engine.{entity}` và đường lui giữ nguyên | Chốt 14/08/2026. Để đứng cạnh thì thành **ba cơ chế cùng trả lời một câu hỏi**: phân quyền vai trò, `_in_approve_scope` (một bước duyệt bị nhét vào cột phạm vi dữ liệu), và bộ máy mới. Dữ liệu phân quyền đã có sẵn nên chỉ cần thay chỗ kiểm tra, không phải viết lại nghiệp vụ. **Vẫn giữ nguyên là đích đến — 17/08/2026 chỉ hoãn *thời điểm*, xem quyết định 10** |
| 10 | **Người dùng đầu tiên của bộ máy là VĂN THƯ, không phải Thu mua. Thu mua giữ nguyên, không đụng.** Nhóm D của `phase-03` (T28 gate · T29 cờ đổi đường · T31 chuyển 5 luồng) **tách khỏi phase, làm sau**; riêng T30 (hợp đồng dữ liệu `approval` cho giao diện) ở lại vì văn thư cần. Thêm **P3-T37** đấu nối văn thư. **Sổ nợ `no-can-don.md` mở NGAY** thay vì mở cùng T28 | Chốt 17/08/2026. Ba lý do: **(1) Chỗ cắm đã sẵn** — `tab_doc_type` đã có `needs_approval`, `needs_signature` và `default_flow_id`, đồng nghiệp khai sẵn đúng để "khỏi ALTER". **(2) Rẻ hơn nhiều.** Duyệt văn bản hiện là **một bước cứng** (`POST /{id}/approve` → `require("document","approve")` → `service.approve`), duyệt xong chỉ cấp số + đổi trạng thái phiên bản. Còn duyệt YCMH kéo theo đổi trạng thái, điều phối, chuông, thư — **phải xong T26 (việc chạy kèm cùng transaction) mới chuyển nổi**. **(3) Sai thì không ai chết.** Văn thư chưa có người dùng thật trên prod; 5 luồng Thu mua thì ~300 tài khoản đang chạy. Đổi lại, mô hình luồng ở T12/T13 **vẫn phải khai thử được cả 5 luồng Thu mua trên giấy** — thiết kế chỉ vừa văn thư thì mai mốt Thu mua vào không lọt, nhất là YCMH có **hai lần duyệt** |
| 11 | **Bộ máy duyệt làm theo kiểu "nhiều pháp nhân trong một tập đoàn", và không chặn đường sang kiểu "nhiều khách hàng".** Ba thứ chốt cứng **trước** khi gõ migration M-B (T13): **(a)** `tab_approval_flow.company_id`, `0` = dùng chung cả tập đoàn, và chọn luồng ở T14 **leo lên `tab_company.parent`** — con không khai thì lấy của mẹ; **(b)** mọi khóa tổ chức trong `condition_json` lưu bằng **ID**, cấm lưu chuỗi tên; **(c)** **không** thêm cột `tenant_id` | Chốt 17/08/2026 sau câu hỏi của khách về hướng nhiều tenant. **(a)** Không có thừa kế thì 13 pháp nhân × 5 loại phiếu = **65 luồng khai tay**, sửa một quy định phải sửa 13 chỗ; và chính cơ chế này là phần "clone xuống pháp nhân con" của P4 văn thư — làm một lần dùng cả hai. Đổi ngữ nghĩa sau khi `flow_snapshot` đã có phiếu chạy thì rất đắt, nên phải chốt trước T13. **(b)** Bài học đang trả giá: `SCOPE_FIELDS` khớp phòng ban bằng **tên** và `purchase_order` khớp người phụ trách bằng **tên** — hai pháp nhân trùng tên phòng / trùng tên người là **lộ dữ liệu xuyên pháp nhân**, xem P0-T06 + P0-T07 + P3-T09. Đừng lặp lại trong bảng mới. **(c)** Gốc cây pháp nhân (`level = 1`, `parent = 0`) đã đóng vai `tenant_id` rồi. Muốn sang kiểu nhiều khách hàng thì việc phải làm là **chặn `scope='all'` vượt gốc cây** trong `core/scoping.py` — một thay đổi ở tầng lọc, làm lúc nào cũng được, không cần cột mới |
| 9 | **Nền tổ chức làm trước bộ máy** — chức vụ thành danh mục có cấp bậc, phòng ban và nhân sự gắn pháp nhân, khai trưởng phòng, dựng cây tổ chức (P3 nhóm A, 11 task) | Chốt 14/08/2026 sau khi đo DB: chức vụ là **chữ tự do** (216/244 người ghi `"Nhân sự"` — tên phòng ban), **18/18** phòng ban `company_id = 0`, **235/244** nhân sự `company_id = 0`, **16/18** phòng không có trưởng, không có cây phòng ban lẫn cây pháp nhân. Với dữ liệu đó thì **5 trong 7 cách chọn người duyệt không chạy được** |
| 6 | **Soạn thảo = gõ thẳng trên web.** Bỏ cả `C02` tệp mẫu Word lẫn bộ trường nhập động | Chốt 14/08/2026: việc cơ bản nhất là người dùng **nhập văn bản bằng tay**. Không làm bảng `tab_doc_template`, không có cột `template_id`; gỡ danh mục "Trường thông tin động" đang có trong `frontend-v2`. Nội dung nằm ở `tab_document_version.content_html`, soạn bằng `rich-text-editor` (tiptap) đã có. Vẫn **giữ đính kèm tệp** — chỉ bỏ phần khai form |
| 7 | **Bỏ hẳn bước xin phép (nhóm B *Yêu cầu văn bản*).** Ai có quyền `document.create` thì tạo văn bản trực tiếp | Chốt 14/08/2026. Mất đi chốt chặn mà `00` mục 4.1 coi là quan trọng nhất — ngăn ai cũng đẻ ra quy trình rồi không ai biết cái nào đang hiệu lực; bù lại bằng **B05** (form hiện luôn văn bản cùng loại cùng phòng đang hiệu lực) và bằng chính bước duyệt nội dung ở P3. Để thêm lại sau mà không phải `ALTER` bảng nóng: **vẫn tạo bảng `tab_document_request` rỗng** ở M6, **vẫn khai** `tab_document.document_request_id` + `tab_document_version.created_from_request_id` (luôn `NULL`) và cột `doc_type.needs_request` (mặc định `FALSE`, ẩn khỏi form) |

## Rủi ro chặn cả plan

| Rủi ro | Giảm bằng |
|---|---|
| P0 và P3 làm gián đoạn Thu mua (~300 tài khoản) | **Quyết định 10: không đụng vào Thu mua trong phase này** · **P3-T11 trước tiên** (kiểm thử 5 luồng duyệt hiện tại, nay là **bằng chứng không đụng vào**) · mỗi task một lần deploy · dev trước prod ít nhất 1 tuần · khi nào mở nhóm D thì cờ bật tắt + chuyển **từng luồng một** |
| **Hoãn Thu mua rồi quên luôn, bộ máy chỉ vừa văn thư** | T12 **bắt buộc khai thử cả 5 luồng Thu mua ra giấy** dù chưa chuyển — chỗ nào khai không nổi là mô hình còn thiếu. Sổ nợ `no-can-don.md` mở **ngay từ đầu phase**, không chờ T28, và ghi rõ điều kiện dọn |
| **Lộ dữ liệu xuyên pháp nhân** — phòng ban và người phụ trách đang khớp bằng **chuỗi tên** | P0-T06 + P0-T07 + P3-T09. Quyết định 11(b): bảng mới **cấm** lưu khóa tổ chức bằng tên |
| **Nền tổ chức rỗng, làm bộ máy xong không chạy được** | P3 nhóm A (11 task) **chặn cứng** phần còn lại của P3. Số đo hiện trạng ở Phần 1 của `phase-03` để không ai nghĩ "chắc dữ liệu ổn" |
| Chèn `if` đổi đường khắp nơi rồi quên, thành mã hai đường vĩnh viễn | [`no-can-don.md`](./no-can-don.md) mở **ngay từ đầu P3** (sửa 17/08/2026 — bản cũ ghi "cùng lúc với P3-T28", mà T28 đã hoãn thì chờ nó là chờ vô hạn), ghi **ngay lúc chèn**. P3-T36 là task bắt buộc |
| Cấp số trùng | 3 lớp: khóa dòng · UNIQUE tầng DB · cùng transaction. Bài kiểm 100 kết nối là điều kiện chuyển phase |
| Quên lọc `origin = 1` | Bộ lọc nằm ở hàm dựng truy vấn dùng chung + bài kiểm tự động (P2-T04) |
| Quên khai `SCOPE_FIELDS` cho bảng mới | Guard lúc khởi động (P0-T13): bảng có `company_id` mà chưa khai → chết ngay lúc chạy |
| Mô hình luồng duyệt không đủ mềm | **Khai thử 5 luồng thật ra giấy trước khi viết mã** (P3-T12) |
| Bỏ bước xin phép (quyết định 7) mà bước duyệt nội dung chưa có → ai cũng đẻ văn bản, không ai biết cái nào đang hiệu lực | Trong bước 3b nhánh B **bắt buộc dựng luồng duyệt một bước viết tay tạm**, không được để văn bản tạo xong là hiệu lực ngay. Cấm mở tài khoản văn thư trên prod trước khi luồng tạm đó được thay bằng bộ máy chung |
| Hai nhánh song song đẻ hai head Alembic | Luật ở mục "Luật khi hai người chạy song song" — `fetch` trước khi sinh revision, kiểm `alembic heads` chỉ ra một dòng trước khi đẩy |

## Câu hỏi chưa trả lời (không chặn P0–P3)

1. ~~**B1** — form chuẩn là mẫu Word hay form web?~~ **Đã chốt 14/08/2026: không cả hai.** Người soạn gõ thẳng nội dung trên web bằng trình soạn thảo + bộ trường chung cố định `C01`. `C02` tệp mẫu Word và `C09` form web sinh thể thức đều **bỏ khỏi bản 1** — muốn làm thì đưa vào P9.
2. **B3** — 4 mức mật chốt tên gì? Plan dùng `1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật` theo `04` mục 5.2. FE hiện đang là Thường/Mật/Tối mật/Tuyệt mật → P1-T13 nắn lại.
3. **B12** — có làm loại thứ 33 *Trích lục* (C20) không? Plan chỉ làm bản trích nội bộ C19.
4. **B6** — 32 mã loại + 13 mã pháp nhân đã ai duyệt chưa? Cấp số rồi thì **không đổi mã được** (P1-T05 khóa cột).
5. ~~`frontend-v2` đã chốt thay `frontend/` chưa?~~ **Đã chốt: `frontend-v2` là FE chính thức, `frontend/` đóng băng chỉ sửa lỗi.** Ghi ở **D-026** (13/08/2026) trong `doc/tai-lieu-ky-thuat/change-log.md`, kèm **D-027** (14/08/2026) về ba cổng kiểm tra của `frontend-v2`; `CLAUDE.md` mục "Frontend architecture" cũng đã cập nhật. Cả bộ `van-thu` viết trước quyết định này nên không nhắc tới `frontend-v2` chỗ nào — đọc `01` thấy nói "màn hình của Thu mua" thì hiểu là `frontend-v2`.

## Mức tái dùng của module `document` đang có trong `frontend-v2`

Module này dựng theo **trục sổ đến/đi** (`direction` · `book_no` · `partner_id` · `processing_status`) — thuộc nhóm S, van-thu xếp **phase 9**. Nói "đập đi làm lại" thì quá, nói "dùng lại được nhiều" cũng sai. Phân ra cho rõ:

| Phần | Số phận |
|---|---|
| 3 danh mục: loại văn bản · mức mật/khẩn · đối tác | **Giữ**, sửa trường (P1-T10, T11, T13) |
| Vỏ trang: list · detail · create · settings, breadcrumb, layout | **Giữ**, thay nội dung |
| Hạ tầng dùng chung: `data-table`, `conditional-filter`, `rich-text-editor`, `use-document-autosave`, `audit-timeline`, `notification-bell` | **Giữ nguyên**, không đụng |
| Bộ trường trên form văn bản (`DocumentRecord` ~40 trường) | **Đổi trục** (P2-T14) — phần viết lại thật sự nằm ở đây |
| Trường nhập động | **Xóa** (P2-T14b) |
| Sổ văn bản đến/đi + `direction`/`book_no`/`partner_id`/`processing_*` | **Tạm ẩn khỏi menu**, giữ mã, chờ câu A1 |
| `store/local-collection.ts` + 3 store | **Xóa dần** khi từng màn nối API |
