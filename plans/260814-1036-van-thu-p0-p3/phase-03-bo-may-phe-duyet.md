# PHASE 3 · BỘ MÁY PHÊ DUYỆT DÙNG CHUNG

> [← plan.md](./plan.md) · Nguồn: **`03` toàn bộ (82 mục Lark)**, `01` nhóm I, `02` mục 7, `04` mục 6
> Ra được: khai luồng duyệt **bằng giao diện, không sửa mã, không deploy lại**.

## Tổng quan

| | |
|---|---|
| Ưu tiên | Cao — chặn P4 |
| Trạng thái | ☐ Chưa bắt đầu |
| Mã `01` | I01–I12, I15–I18, I20, I21, I23, I26 (20 tính năng bản 1) |
| Migration | M8 (6 bảng) |
| Song song được với | Phase 5 (quyền + tra cứu) — hai mảng gần như không đụng nhau |

Phase **nặng nhất và rủi ro nhất**: đây là chỗ dễ làm hỏng Thu mua nhất. Bộ máy mới **chạy song song**, mã duyệt hiện tại của Thu mua **giữ nguyên, không đụng vào**.

## Điểm cần biết trước

1. **Không lấy bộ kéo thả biểu mẫu của Lark** (`03` nhóm A). Mỗi loại phiếu đã là một bảng dữ liệu thật. Thứ cần lấy là **phần đường đi của phiếu**, không phải phần biểu mẫu.
2. **`on_no_approver` cố ý KHÔNG có giá trị "tự động duyệt qua".** Không khai giá trị thì sau này không ai bật nhầm được. Thứ tự xử lý khi không tìm ra người duyệt: người thay thế khai sẵn → trưởng phòng của người đó **tại pháp nhân đó** → quản trị văn thư kèm cảnh báo đỏ → **hết, phiếu đứng lại**.
3. **`flow_snapshot` là cột giải quyết bài toán sửa luồng khi có phiếu đang chạy.** Phiếu chạy theo **bản chụp của chính nó**, không tham chiếu bản luồng đang sống (chỗ dễ sai số 5).
4. **`is_default_branch` là cột chống mất phiếu.** Không có nó thì phiếu rơi vào trạng thái không nhánh nào nhận, **biến mất khỏi mọi danh sách**.
5. **Trạng thái task số 5 "tự động qua vì trùng người" phải là trạng thái riêng** — không để trống, không ghi thành "đã duyệt". Bản in dấu vết cần phân biệt *người này ký* với *bước này tự qua vì người này đã ký ở bước trước*.
6. **Cây tổ chức không phải một cây.** Trưởng phòng theo **cặp (phòng ban × pháp nhân)** — dùng `tab_department_company` của P1-T01. Bỏ qua là phiếu của nhân viên Kế toán công ty A bay sang trưởng phòng Kế toán công ty B.
7. **Bốn việc Lark không có, phải nằm TRONG cùng transaction với hành động duyệt:** cấp số văn bản · đóng băng phiên bản + khóa sửa · tôn trọng mức mật · clone xuống pháp nhân con (P4). Đây là lý do không dùng thẳng Lark.
8. **Chỉ mục quan trọng nhất cả hệ thống:** `tab_approval_task(assignee_employee_id, status)` — truy vấn của màn "việc của tôi", chạy mỗi lần ai mở trang chủ.

## Danh sách task

### Chuẩn bị và nền dữ liệu

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T01** | — | **Khai thử 8 luồng ra giấy** | **Làm trước khi viết dòng mã đầu tiên.** 5 luồng thật của Thu mua (PYC, khảo sát, yêu cầu khảo sát, ĐMH, yêu cầu thanh toán) + 3 luồng văn thư (duyệt yêu cầu văn bản, duyệt nội dung, duyệt bản clone) — khai bằng đúng mô hình `tab_approval_flow` + `tab_approval_node`. **Chỗ nào khai không nổi thì mô hình còn thiếu.** Ra một tệp `plans/.../8-luong-thu-nghiem.md` |
| **P3-T02** | DB | **Migration M8** | 6 bảng: `tab_approval_flow` (13 cột) · `tab_approval_node` (17 cột) · `tab_approval_instance` (11 cột, có `flow_snapshot JSON`) · `tab_approval_task` (10 cột) · `tab_approval_action` (13 cột) · `tab_delegation` (10 cột). Index: **`tab_approval_task(assignee_employee_id, status)`**, `(instance_id, node_id)`, `tab_approval_instance(entity, entity_id)` + `(status, company_id)`, `tab_approval_action(instance_id, created_at)`. Grant MySQL append-only cho `tab_approval_action` |

### Bộ máy chạy phiên (backend)

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T03** | BE | **Chọn luồng** | `flow_resolver.py`: khớp theo `entity` + `doc_type_id` + `company_id` + `department_id` + `condition_json`, nhiều luồng cùng khớp thì lấy `priority` nhỏ hơn. Không luồng nào khớp → lỗi rõ ràng, **không tự duyệt qua** |
| **P3-T04** | BE | **Khởi tạo phiên + snapshot** | `POST /approvals/submit`: chép **toàn bộ** định nghĩa luồng + node vào `flow_snapshot`, ghi `flow_version_no`. Từ đó engine **chỉ đọc snapshot**, không đọc bảng luồng sống (I21, J2) |
| **P3-T05** | BE | **Sáu cách chọn người duyệt** | `approver_kind`: 1 người cụ thể · 2 vai trò · 3 **trưởng phòng của người nộp tại pháp nhân của phiếu** (qua `tab_department_company`) · 4 lên n cấp · 5 người đại diện pháp nhân (`tab_company.legal_representative_id`) · 6 lấy từ ô trên phiếu · 7 cả phòng ban. Kiểu 6 phải kiểm người được chọn nằm trong danh sách cho phép |
| **P3-T06** | BE | **Nhiều người trong một bước** | `multi_mode`: 1 một người là đủ · 2 tất cả phải duyệt · 3 lần lượt (`seq` trong node) · 4 đủ tỷ lệ (`quorum`, bản sau). **Mặc định: một người từ chối là hỏng cả bước** (D5) |
| **P3-T07** | BE | **Rẽ nhánh + nhánh mặc định** | Đánh giá `condition_json` theo số tiền / loại văn bản / phòng ban / pháp nhân / mức mật. **Mỗi chỗ rẽ phải có đúng một `is_default_branch`** — validate lúc lưu luồng, không phải lúc chạy phiếu. Nhánh song song (B4): nhiều node cùng `seq` |
| **P3-T08** | BE | **Trùng thao tác thì bỏ qua** | `duplicate_mode` 1 trùng liền kề · 2 trùng bất kỳ chỗ nào phía trước · 3 không bỏ qua. Khai **theo từng luồng**, không phải cấu hình chung. Bỏ qua thì ghi `task.status = 5` + `action = 9` kèm câu **"bước 3 tự động qua vì ông X đã duyệt ở bước 2"** |
| **P3-T09** | BE | **Người duyệt nghỉ việc** | Theo thứ tự: `fallback_employee_id` của node → trưởng phòng tại pháp nhân đó → quản trị văn thư (`on_no_approver = 1`) kèm cảnh báo đỏ trên phiếu → **hết**. Ghi `task.assign_reason` 3 hoặc 4. **Không có nhánh tự duyệt qua** |
| **P3-T10** | BE | **Chặn tự duyệt** | Người nộp không duyệt phiếu của chính mình. Nếu luồng bắt buộc trùng thì **chuyển lên cấp trên**, không tự qua (I08, C8/E4 của `03`) |
| **P3-T11** | BE | **Hành động của người duyệt** | Duyệt · từ chối (**bắt lý do**, kết thúc phiếu) · trả lại (**bắt lý do**, về người nộp hoặc **về một bước cụ thể** `return_to_node_id`) · nộp lại (cấu hình đi lại từ bước bị trả hay từ đầu) · rút lại (chỉ khi chưa ai duyệt). Mỗi hành động ghi một dòng `tab_approval_action` |
| **P3-T12** | BE | **Ủy quyền có thời hạn** | `tab_delegation`: bắt buộc `from_date`/`to_date`, quản trị đặt hộ được (`created_by_admin`). **Cấm ủy quyền dây chuyền** — A ủy cho B thì B không ủy tiếp phần việc nhận từ A, kiểm lúc lưu, báo lỗi rõ. Ghi cả hai danh tính: `actor_employee_id` + `on_behalf_of_id` + `delegation_id` |
| **P3-T13** | BE | **Hạn và nhắc** | `sla_hours` mỗi node → `task.due_at`. Job định kỳ: sắp quá hạn nhắc, quá hạn nhắc tiếp, tăng `reminded_count`, ghi `action = 11`. Thông báo qua chuông (`app = 'vanthu'`) + thư. Leo cấp trên để bản sau (I6) |
| **P3-T14** | BE | **Bàn giao hàng loạt + cảnh báo trước khi tắt tài khoản** | Chọn nhiều task của người nghỉ → chuyển sang người khác trong một lần (I23/F5). Khi HR bấm tắt nhân sự: **cảnh báo "người này đang giữ 12 phiếu"** trước khi cho tắt (F6) |
| **P3-T15** | BE | **Cờ bật tắt theo loại chứng từ** | `setting` key `approval_engine.{entity}` mặc định `false`. Bật cho `document_request` và `document` trước; 5 luồng Thu mua **giữ nguyên mã cũ**, tắt cờ là quay về đường cũ ngay, không deploy (I26) |

### Giao diện (frontend-v2 — module `approval` mới)

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P3-T16** | FE | **Trình khai luồng duyệt** | Màn nặng nhất. Danh sách luồng + trình soạn: danh sách bước dọc (kéo đổi thứ tự), mỗi bước một panel cấu hình (`node_kind`, `flow_role`, `approver_kind` + `approver_ref`, `multi_mode`, `fallback_employee_id`, `sla_hours`, `min_secrecy_required`), khối điều kiện rẽ nhánh, **ép khai nhánh mặc định**. Ô `on_no_approver` **không có lựa chọn tự duyệt qua**. Nút "xem trước đường đi" (B8). Không dùng thư viện flow-chart — danh sách dọc đủ và rẻ hơn nhiều |
| **P3-T17** | FE | **Panel duyệt trên phiếu + chuyển luồng yêu cầu văn bản** | Component dùng chung `<ApprovalPanel entity entityId />`: các nút duyệt/từ chối/trả lại/rút, ô ý kiến + đính kèm (tái dùng `procurement/document-comments` + `mention-input`), dòng thời gian dấu vết, hiện phiên bản luồng đang chạy. Gắn vào trang chi tiết yêu cầu văn bản (thay luồng một bước tạm của P2) và trang chi tiết văn bản |
| **P3-T18** | FE | **Việc của tôi + phiếu kẹt + in dấu vết + ủy quyền** | `pages/my-tasks-page.tsx` gom việc chờ của **cả văn thư và thu mua** (I17), 3 tab: chờ tôi · tôi đã nộp · tôi đã duyệt. `pages/stuck-instances-page.tsx` liệt kê phiếu không ai xử lý (F7). `pages/approval-trace-print-page.tsx` — bản in dấu vết, ghi rõ "B duyệt thay A theo ủy quyền số 12" và "bước 3 tự qua vì …" (I20/H4/E). `pages/delegation-page.tsx` khai ủy quyền |

## Tệp đụng tới

**Tạo BE:** `modules/approval/{__init__,model,schema,controller}.py` · `modules/approval/{flow_resolver,engine,assignee_resolver,duplicate_rule,delegation_service,reminder_job}.py` · `migrations/versions/<M8>.py` · `test/backend/test_approval_engine.py` · `test_approval_snapshot.py` · `test_approval_duplicate_skip.py` · `test_approval_no_approver.py` · `test_delegation_chain.py`
**Tạo FE:** `modules/approval/routes.tsx` · `pages/flow-{list,detail}-page.tsx` · `pages/my-tasks-page.tsx` · `pages/stuck-instances-page.tsx` · `pages/delegation-page.tsx` · `pages/approval-trace-print-page.tsx` · `components/flow-node-editor.tsx` · `approver-picker.tsx` · `branch-condition-editor.tsx` · `approval-panel.tsx` · `approval-trace-timeline.tsx` · `api/approval-api.ts` · `hooks/use-approval-{flows,tasks,instance}.ts` · `types/approval.ts`
**Sửa:** `app/main.py` · `core/permissions.py` (entity `approval_flow`, `approval_task`) · `core/all_models.py` · `modules/employee/service.py` (cảnh báo trước khi tắt) · `frontend-v2/src/app/router/module-registry.ts` · `modules/document/pages/document-request-detail-page.tsx`

## Todo

- [ ] P3-T01 · **Khai thử 8 luồng ra giấy** (trước khi viết mã)
- [ ] P3-T02 · M8: 6 bảng + index + grant append-only
- [ ] P3-T03 · Chọn luồng theo điều kiện + `priority`
- [ ] P3-T04 · Khởi tạo phiên + `flow_snapshot`
- [ ] P3-T05 · Sáu cách chọn người duyệt (trưởng phòng theo cặp phòng×pháp nhân)
- [ ] P3-T06 · Nhiều người trong một bước, 3 chế độ
- [ ] P3-T07 · Rẽ nhánh + ép nhánh mặc định + nhánh song song
- [ ] P3-T08 · Trùng thao tác thì bỏ qua, 3 mức, ghi nhật ký lý do
- [ ] P3-T09 · Người duyệt nghỉ việc — 4 bước, **không có bước tự duyệt qua**
- [ ] P3-T10 · Chặn tự duyệt
- [ ] P3-T11 · Duyệt / từ chối / trả lại đúng bước / nộp lại / rút lại
- [ ] P3-T12 · Ủy quyền có hạn, cấm dây chuyền, ghi hai danh tính
- [ ] P3-T13 · Hạn duyệt + nhắc + thông báo
- [ ] P3-T14 · Bàn giao hàng loạt + cảnh báo trước khi tắt tài khoản
- [ ] P3-T15 · Cờ bật tắt theo loại chứng từ
- [ ] P3-T16 · FE trình khai luồng duyệt
- [ ] P3-T17 · FE panel duyệt + chuyển luồng yêu cầu văn bản sang bộ máy mới
- [ ] P3-T18 · FE việc của tôi, phiếu kẹt, in dấu vết, ủy quyền
- [ ] **Chạy lại 5 kiểm thử Thu mua ở P0-T01 → vẫn xanh**

## Nghiệm thu

| Bài kiểm | Kết quả phải là |
|---|---|
| Khai một luồng 4 bước bằng giao diện | Phiếu chạy đúng qua 4 người, **không sửa dòng mã nào, không deploy lại** |
| Người bước 1 cũng là người bước 3 | Bước 3 tự bỏ qua, **nhật ký ghi rõ lý do bỏ qua** |
| Tắt trạng thái một nhân sự đang giữ 3 phiếu | 3 phiếu chuyển sang người thay thế, **không phiếu nào tự động duyệt qua** |
| Sửa luồng khi có 5 phiếu đang chạy | 5 phiếu vẫn đi theo luồng cũ tới khi kết thúc |
| Tạo phiếu không khớp điều kiện nhánh nào | Rơi vào nhánh mặc định, **không biến mất khỏi mọi danh sách** |
| **Chạy lại 5 kiểm thử Thu mua (P0-T01)** | **Vẫn xanh** — bộ máy mới chưa bật cho Thu mua nên không được ảnh hưởng gì |
| A ủy quyền cho B, B thử ủy tiếp cho C | Bị chặn, báo lỗi rõ |
| In dấu vết một phiếu có bước tự qua và bước duyệt thay | Tờ in ghi đúng cả hai: "tự qua vì …" và "B duyệt thay A theo ủy quyền số 12" |
| Tắt cờ `approval_engine.document_request` | Quay về đường duyệt cũ ngay, không cần deploy |

## Rủi ro

| Rủi ro | Mức | Giảm bằng |
|---|---|---|
| Mô hình luồng không đủ mềm, vẫn phải sửa mã cho từng loại | Trung bình | **P3-T01** — khai thử 8 luồng ra giấy. Sửa trên giấy rẻ hơn sửa khi đã có 200 phiếu chạy |
| Đụng vào 5 luồng đang chạy của Thu mua | Cao nếu bất cẩn | Bộ máy mới **đứng cạnh**, cờ mặc định tắt, không sửa một dòng nào trong 5 module cũ ở phase này |
| Phiếu kẹt không ai biết | Trung bình | `is_default_branch` bắt buộc + màn "phiếu đang kẹt" (P3-T18) + cảnh báo đỏ khi rơi về quản trị |
| Trình khai luồng phình to thành công cụ vạn năng | **Cao** | Chỉ làm đúng phần bản 1 của `03`. Không kéo thả biểu mẫu (A1–A3), không luồng con (B7), không chuyển tiếp/thêm người duyệt (G6–G8), không mô phỏng (J5) — tất cả để bản sau |
| Truy vấn "việc của tôi" chậm khi nhiều phiếu | Trung bình | Index `(assignee_employee_id, status)` bắt buộc có từ M8, không thêm sau |

## Bảo mật

- `min_secrecy_required` trên node: người duyệt không đủ mức mật thì **không được nhìn thấy nội dung**, kể cả khi họ là người duyệt. Ràng buộc này chỉ thực thi được đầy đủ sau P5 — trong lúc đó cột vẫn khai và lưu.
- `tab_approval_action` **chỉ ghi thêm**, grant MySQL không cấp `UPDATE`/`DELETE`. Nhật ký mà sửa được thì không còn là nhật ký.
- Duyệt hàng loạt (I19) để bản sau và khi làm thì **cấm với văn bản mật** (`03` G11).
- Entity phân quyền riêng cho việc **thiết kế luồng** (`approval_flow`) — khác với quyền duyệt phiếu (J6). Ai sửa luồng, sửa gì đều vào nhật ký (J7).

## Tiếp theo

Phase 4 (ban hành, phạm vi, clone) — **cần trả lời câu B5 và B6 trước**. Phase 5 (quyền truy cập + tra cứu) làm song song được với phase này nếu có người thứ hai.
