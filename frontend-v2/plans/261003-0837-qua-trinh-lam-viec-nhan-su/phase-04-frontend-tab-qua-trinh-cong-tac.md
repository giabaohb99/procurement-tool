# Phase 04 — Frontend: tab «Quá trình công tác» ở hồ sơ nhân sự

**Ưu tiên:** P2 · **Effort:** 5.5h · **Trạng thái:** pending · **Phụ thuộc:** 01 (`statuses.ts` có `WORK_EVENT_TYPE`); code theo hợp đồng API ở phase 02 (chạy thật cần 02 xong)

## Bối cảnh
- `src/modules/hr/pages/employee-detail-page.tsx` (5 tab, `?tab=`, MỘT `<form>` bọc mọi tab).
- Khuôn tệp riêng tư: `hr/components/leave-attachments-card.tsx` + `hr/api/leave-attachment-api.ts` + `hr/hooks/use-leave-attachments.ts` (`AttachmentPreviewDialog`, `downloadFile`, `FileDropzone`).
- `docs/ui/table.md` (DataTable trong `Card`, `columns` bọc `useMemo`, ô hành động `stopPropagation`).
- `.claude/rules/frontend-v2-ui-conventions.md` — bốn bẫy biểu mẫu.
- `shared/ui/confirm-dialog.tsx` (`confirm()` dạng promise) cho câu hỏi áp hồ sơ.

## Thiết kế màn
- Tab thứ 6 **«Quá trình công tác»** (icon lucide `History`), `value="work-history"`, đặt sau «Chung». Trigger luôn hiện (ai đọc được hồ sơ thì đọc được tab).
- `Card` + `SectionHeading` + `DataTable` (không phân trang — trần 200 dòng), `storageKey="hr.employee-work-history"`, xếp mới nhất trên cùng.
- Cột: Từ ngày (hiệu lực) · Đến ngày (trống → huy hiệu «Đang hiệu lực») · Loại (`labelOf(WORK_EVENT_TYPE, String(row.event_type))`) · Pháp nhân · Phòng ban · Chức vụ (`position_label`) · Số QĐ · Ngày ký QĐ · Tệp · Ghi chú (`wrap`, `defaultHidden`) · Đã áp (ngày, `defaultHidden`) · Thao tác (chỉ khi `can_edit`: Sửa · Áp vào hồ sơ khi `can_apply` · Xóa).
- **Cột Tệp (Q4):** `can_open_files` → kẹp giấy + số, bấm mở hộp tệp. Không có → chữ tĩnh «Có N tệp đính kèm» + tooltip «Cần quyền xem thông tin nhạy cảm để mở tệp», KHÔNG nút xem/tải, KHÔNG gọi `/api/attachments` (gọi là 403). `file_count = 0` → «—».
- **Được sửa / được mở tệp lấy từ cờ backend** `can_edit`, `can_open_files` (A9) — không tự ghép `can()` + so `employee_id` + đoán quản trị ở TS. `can_edit=false` trên hồ sơ của chính mình → chỉ đọc + câu «Quá trình công tác của chính bạn do người khác cập nhật».
- Rỗng: phân biệt «chưa có dòng nào» + nút **«Tạo dòng đầu từ hồ sơ»** (mở hộp Thêm điền sẵn: Tuyển dụng, `from_date = hire_date`, pháp nhân/phòng/chức vụ hiện tại) — thay cho migration dữ liệu.

## Hộp thêm/sửa (`employee-work-history-form-dialog.tsx`)
- RHF + zod (`hr/schemas/employee-work-history-schema.ts`): bắt buộc loại + từ ngày; `to_date ≥ from_date`; `decision_no` ≤50; `note` ≤500 (khớp backend).
- Ô: Loại · Từ ngày (hiệu lực) · Đến ngày · Pháp nhân · Phòng ban (lọc theo pháp nhân) · Chức vụ (`useJobPositions`, `sort_by=name`) · Số QĐ · Ngày ký QĐ · Ghi chú · Tệp QĐ (thêm mới: hàng đợi tệp, tải lên SAU khi tạo xong; sửa: danh sách + vùng thả).
- Mở Thêm: điền sẵn pháp nhân/phòng/chức vụ từ hồ sơ hiện tại. Loại nhóm chính + đang có dòng chính mở → ô tick «Đóng dòng đang hiệu lực «…» vào ngày trước đó» (mặc định tick) → `close_open_main`.
- **Câu hỏi áp hồ sơ** — hàm thuần `planApplyPrompt(values, employee, extraDeptIds, today)` ở `hr/utils/employee-work-history-apply.ts`, trả `null | {kind:'profile', changes[]} | {kind:'resign', resignDate}`. Chỉ hỏi khi `from_date ≤ hôm nay` (Q1: từ ngày = ngày hiệu lực) và:
  - loại 1,2,3,5: dòng chưa kết thúc VÀ có ô khác hồ sơ → `confirm({title:'Cập nhật hồ sơ hiện tại?', description: danh sách thay đổi})`;
  - loại 4: trạng thái phòng trong danh sách kiêm nhiệm khác với dòng → cùng hộp trên («Thêm/Gỡ kiêm nhiệm phòng X»);
  - **loại 6 Thôi việc (Q2):** hồ sơ chưa ở «Nghỉ việc» hoặc `resign_date` khác → **hộp xác nhận RIÊNG** `employee-work-history-resign-confirm-dialog.tsx` (AlertDialog, tông `destructive`): tiêu đề «Chuyển hồ sơ sang nghỉ việc?»; nội dung nói rõ «Ngày nghỉ việc ghi vào hồ sơ: dd/mm/yyyy (lấy từ dòng)», «Mọi tài khoản đăng nhập của người này sẽ bị KHÓA và bị ĐĂNG XUẤT khỏi mọi thiết bị ngay lập tức», «Mở lại tài khoản phải làm tay ở tab Tài khoản»; hai nút **«Chỉ lưu dòng»** và **«Lưu và chuyển sang nghỉ việc»** (nút đỏ, chữ nói đúng việc — không dùng «Đồng ý» chung chung). Ngày tương lai → không hỏi, ghi dưới ô ngày «Tới ngày này quay lại bấm Áp vào hồ sơ để chuyển nghỉ việc».
  Câu trả lời → `apply_to_profile` — **một request**. Nút «Áp vào hồ sơ» ở dòng dùng đúng các hộp này rồi gọi `/apply`.
- Sau áp Thôi việc: dọn cả nhánh `hr.all` (thẻ tiêu đề đổi chip tình trạng, thẻ Tài khoản hiện «đã khóa»).
- `warnings` từ API → `toast.warning` từng câu; `applied_changes` → toast thành công kèm tóm tắt.
- Hôm nay: `toDateInputValue(new Date())` (giờ máy; test cố định `Asia/Ho_Chi_Minh`).

## Bẫy bắt buộc xử lý
1. ⚠️ **Hộp thoại nằm trong `<form>` của trang** (tab render trong form). Radix portal tách DOM nhưng **sự kiện React vẫn nổi bọt theo cây React** → submit form con kích luôn `onSubmit` của form hồ sơ. Form con phải `event.preventDefault(); event.stopPropagation()` trước `handleSubmit`. Đây là hộp có `<form>` đầu tiên trong màn này — viết test bắt.
2. Mọi `<Button>` trong tab: `type="button"`.
3. Chặn bấm đúp bằng `useRef` (lưu, áp, xóa) — `disabled={isPending}` không đủ.
4. Enter trong ô của hộp thoại không được rơi vào form cha (đi kèm bẫy 1).
5. Ô hành động trong bảng: `onClick={(e) => e.stopPropagation()}`.

## Tệp (sở hữu riêng phase này)

| Tạo | Sửa |
|---|---|
| `hr/types/employee-work-history.ts` | `hr/pages/employee-detail-page.tsx` (+1 trigger, +1 content, +import ≈ 12 dòng) |
| `hr/api/employee-work-history-api.ts` (list/create/update/remove/apply/listMine + files) | `shared/constants/query-keys.ts` (+3 khóa dưới `hr`) |
| `hr/hooks/use-employee-work-history.ts` | |
| `hr/hooks/use-employee-work-history-files.ts` | |
| `hr/utils/employee-work-history-apply.ts` + `.test.ts` | |
| `hr/schemas/employee-work-history-schema.ts` | |
| `hr/config/employee-work-history-columns.tsx` (dựng cột, tham số `actions?` — dùng lại ở /me) | |
| `hr/components/employee-tab-work-history.tsx` + `.test.tsx` | |
| `hr/components/employee-work-history-form-dialog.tsx` + `.test.tsx` | |
| `hr/components/employee-work-history-files-dialog.tsx` (prop `editable`) | |
| `hr/components/employee-work-history-resign-confirm-dialog.tsx` + `.test.tsx` | |

Mỗi tệp < 200 dòng. Không import ruột phân hệ khác (chỉ `@/shared/**`, `@/core/**`, trong `hr`).

**Query keys** (`hr`): `employeeWorkHistory: (id) => ['hr','employees',id,'work-history']` · `myWorkHistory: () => ['hr','employees','me','work-history']` · `workHistoryFiles: (hid) => ['hr','work-history',hid,'files']`.
Sau lưu/xóa: dọn `employeeWorkHistory(id)`. Sau áp: thêm `employee(id)`, `employeeDepartments(id)`, `employees()` (prefix), `myEmployee()`.

## Test (hành vi người dùng thấy; mock ở `@/core/api`)
- `employee-work-history-apply.test.ts`: tương lai → `null`; đúng hôm nay → hỏi; dòng đã kết thúc → không; khớp hồ sơ → không; Khác → không; kiêm nhiệm đang hiệu lực mà phòng chưa có → hỏi, đã có → không; kiêm nhiệm đã kết thúc mà phòng còn → hỏi gỡ; id 0 ở ô → không coi là thay đổi; ngày rỗng/không hợp lệ → không hỏi. Thôi việc: hôm nay / quá khứ → `kind:'resign'` với `resignDate` = ngày của DÒNG; tương lai → `null`; hồ sơ đã nghỉ việc cùng ngày → `null`; đã nghỉ khác ngày → hỏi.
- `employee-work-history-resign-confirm-dialog.test.tsx`: hiện ngày nghỉ việc + câu «khóa» + «đăng xuất khỏi mọi thiết bị»; «Chỉ lưu dòng» → `apply_to_profile:false`; «Lưu và chuyển sang nghỉ việc» → `true`; Esc/đóng hộp → không gửi gì.
- `employee-work-history-form-dialog.test.tsx`: `to < from` hiện lỗi, không gọi API; bấm Lưu 2 lần liền → 1 request; submit hộp KHÔNG gọi `onSubmit` của form cha bọc ngoài (bẫy 1); từ chối câu hỏi → gửi `apply_to_profile:false`; loại Thôi việc mở hộp xác nhận riêng, không mở `confirm()` chung.
- `employee-tab-work-history.test.tsx`: `can_edit=false` → không nút Thêm/Sửa/Xóa/Áp; nhãn loại lấy từ `WORK_EVENT_TYPE`; `to_date` rỗng → «Đang hiệu lực»; rỗng → có nút «Tạo dòng đầu từ hồ sơ»; `can_open_files=false` + `file_count=2` → hiện «Có 2 tệp đính kèm», không có nút xem/tải và không gọi `/api/attachments`.

```bash
docker compose exec -T erp npm run typecheck
docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run employee-work-history employee-tab-work-history
```

## Todo
- [x] types/api/hooks/query-keys
- [x] util + test
- [x] cột, tab, hộp thêm/sửa, hộp tệp
- [x] gắn tab vào trang chi tiết
- [x] hộp xác nhận thôi việc riêng
- [x] 4 test xanh; typecheck + lint 0 lỗi
- [ ] bấm tay ở 390px (emulate, không resize — xem bộ nhớ) và màn rộng — CHƯA LÀM: đã đối chiếu mã backend thật (phase 02/03 xong) khớp hợp đồng, nhưng chưa bấm qua trình duyệt; xem Concerns trong report.

## Thành công khi
HR thêm dòng Bổ nhiệm hôm nay → hỏi → đồng ý → chip chức vụ trên thẻ tiêu đề đổi ngay; từ chối → hồ sơ giữ nguyên, dòng vẫn lưu. Thôi việc hôm nay → hộp riêng → «Lưu và chuyển sang nghỉ việc» → chip «Nghỉ việc», tab Tài khoản báo đã khóa. HR thiếu sensitive thấy «Có N tệp đính kèm» nhưng không mở được. Xem/tải tệp QĐ chạy qua `/view`.

## Rủi ro
| Rủi ro | K × A | Giảm thiểu |
|---|---|---|
| Submit hộp thoại lưu luôn hồ sơ (portal bubbling) | Cao × Cao | Bẫy 1 + test |
| `employee-detail-page.tsx` đã 400 dòng | — | Chỉ thêm ~12 dòng; tách trang là việc riêng, không làm ở đây |
| Lệch luật hỏi FE/BE | TB × Thấp | BE vẫn chặn cuối; FE chỉ quyết có HỎI hay không; `can_apply`, `can_edit`, `can_open_files` từ API |
| HR bấm nhầm chuyển nghỉ việc | Thấp × Cao | Hộp riêng, nút đỏ nói đúng hệ quả; không gộp vào `confirm()` chung |

## Rollback
Gỡ trigger + content ở trang chi tiết (1 commit revert). Các tệp mới không ai khác import.
