---
paths:
  - "frontend-v2/src/**"
---
# Luật giao diện dùng chung của frontend-v2: bảng dòng, ô chỉ xem, trường bắt buộc, bẫy biểu mẫu, bẫy bảng có bộ lọc

> Chuyển nguyên văn từ CLAUDE.md gốc ngày 01/10/2026 — chỉ nạp khi làm việc với các đường dẫn ở trên.

**Bảng DÒNG CHỨNG TỪ dùng chung `LinesTable`** (`shared/data-table/lines-table.tsx`, CR-101 + CR-102):
bốn bảng dòng (YCMH · YCBG · ĐMH · Giao hàng nhiều lần trong popup chi tiết dòng ĐMH) đều chạy trên
nó — ghim cột, kéo thả đổi thứ tự, co giãn + auto-fit, tô màu, nhớ `localStorage`, nút _Bảng rút gọn
/ Bảng đầy đủ_ (cột phụ khai `compactHidden`, bảng nhiều cột bật `defaultCompact`). Bảng dòng mới
**phải dùng `LinesTable`**, đừng chép khung. ⚠️ **Không đặt bề rộng cứng cho `<table>`** —
`table-fixed` + `w-full` là đủ; gắn `style={{ width: totalWidth }}` thì ẩn cột xong bảng co lại,
chừa một lỗ trắng bên phải trong khung viền (đúng lỗi CR-102 phải vá). Xem `doc/erp/13-...md` §6.
⚠️ **Ô CHỈ XEM: cấm `<Input disabled>` / `<Textarea disabled>`** — `disabled` gỡ luôn khả năng
nhận con trỏ nên người dùng KHÔNG bôi đen, KHÔNG copy được giá trị, lại còn bị làm mờ 50% nhìn
như chữ gợi ý. Dùng `shared/ui/read-only-value.tsx` (chữ trong thẻ thường, khung viền nền mờ).
Giá trị nằm trong **ô CHỌN** thì bản chất là một `<button>` — bôi đen không được bằng cách nào cả,
phải gắn `shared/ui/copy-button.tsx` bên cạnh (xem CR-105).
⚠️ **TRƯỜNG BẮT BUỘC của YCMH · YCBG · ĐMH khai MỘT CHỖ:**
`modules/procurement/utils/required-fields.ts` (CR-107) — vừa là nguồn vẽ dấu sao đỏ, vừa là
nguồn câu chặn lúc **gửi duyệt** (không chặn lúc lưu nháp). Bộ trường của ĐMH phải khớp
`REQUIRED_LINE_FIELDS` ở `backend/app/modules/purchase_order/service.py` (cổng CR-095); YCMH và
YCBG thì backend **không kiểm**, luật chỉ nằm ở giao diện. Đừng gõ `*` thẳng vào chuỗi nhãn —
ô nhập dùng `shared/ui/required-mark.tsx`, tiêu đề cột dùng đuôi `" *"`
(`shared/data-table/required-header.ts`, xem `docs/ui/table.md` §1). **VAT cố ý KHÔNG bắt buộc**:
`0` vừa nghĩa "chưa nhập" vừa nghĩa "hàng không chịu thuế".
Đụng vào **bảng dòng của phiếu khảo sát** (cả hai bản) thì đọc **hợp đồng hiển thị** ở dòng
**CR-090** trong `doc/tai-lieu-ky-thuat/change-log.md` trước — 5 điều kiện về xuống dòng /
ô chỉ xem / ô chọn NCC / phím Enter / bề rộng cột, làm hụt là lủng đúng chỗ vừa sửa lỗi.

⚠️ **BỐN BẪY CỦA BIỂU MẪU, tìm ra bằng cách bấm tay trên trình duyệt** (duoc-CR-317
— áp cho MỌI màn, không riêng nhân sự). Cả bốn im lặng, không test đơn vị nào bắt
được, và ba trong số đó là lỗi có sẵn của khuôn chung:

- **Ô sai ở TAB ĐANG ẨN → bấm Lưu không có gì xảy ra.** Radix hủy mount tab ẩn
  nên `FormMessage` không có chỗ hiện; react-hook-form chặn submit trong im lặng
  tuyệt đối — không toast, không lỗi, không request. Biểu mẫu chia tab **bắt
  buộc** có nhánh `onInvalid` nhảy tới tab chứa ô sai. Mẫu:
  `hr/utils/profile-field-tab.ts` + `form.handleSubmit(onSubmit, onInvalid)`.
- **Nhấn Enter trong ô con nằm trong `<form>` → submit form CHA.** Bảng con có
  nút Lưu riêng thì Enter phải bị `preventDefault`, không thì người dùng gõ dở
  một dòng, nhấn Enter, và hệ thống lưu thứ khác rồi **báo thành công**.
- **Nút mở hộp thoại trong `<form>` phải khai `type="button"`.** Thiếu thì HTML
  mặc định `submit`: bấm «Xóa» là form LƯU bản ghi trước, hộp xác nhận mở sau —
  bấm Hủy thì đã lưu rồi. `shared/ui/delete-confirm-button.tsx` từng thiếu, ảnh
  hưởng ~11 màn chi tiết.
- **`disabled={mutation.isPending}` KHÔNG chặn được bấm đúp.** Nó là state React
  nên chỉ đúng ở lần render sau; bấm 5 lần liền tay ra 5 request và 5 dòng nhật
  ký cho một lần lưu. Chặn bằng `useRef` đổi ngay trong tick, `disabled` chỉ để
  báo hiệu. Khuôn chung còn lỗ này ở nhiều màn.

⚠️ **BA BẪY CỦA BẢNG CÓ BỘ LỌC** (duoc-CR-322 — áp cho MỌI màn danh sách):

- **`id = 0` là một GIÁ TRỊ THẬT, đừng lấy làm mốc «tất cả».** Cột tham chiếu
  bỏ trống (`department_id`, `company_id`, `manager_id`…) lưu `0`, và
  `apply_filters` so khớp CHÍNH XÁC nên `department_id=0` lọc ra đúng nhóm *chưa
  gắn*. Lấy `0` làm sentinel thì nhóm đó thành thứ **duy nhất không lọc ra
  được**, mà nó lại chính là nhóm người ta cần tìm để đi gắn cho đủ. Dùng `-1`.
- **Đổi bộ lọc phải kéo trang về 1** — dùng `usePageResetOnFilterChange`, KHÔNG
  `useEffect(() => setPage(1), [...])`: effect chạy sau khi commit nên lượt
  render đầu vẫn gọi API với số trang cũ (một request thừa vào trang không còn
  tồn tại), và ESLint chặn `setState` trong effect. Theo dõi giá trị tìm kiếm
  **đã hoãn** chứ không theo ô nhập thô, kẻo mỗi ký tự một lần đặt lại trang.
- **Câu «bảng rỗng» phải phân biệt _rỗng vì bộ lọc_ với _rỗng vì chưa có gì_.**
  Một câu chung cho cả hai thì người vừa gõ nhầm một chữ đọc ra "chưa có dữ
  liệu" và tin là vậy.

Bẫy thứ tư nằm ở `frontend-v2/docs/ui/table.md` §4: **`defaultHidden` chỉ áp cho
người chưa từng đụng menu «Cột»** — bảng nhớ bố cục trong `localStorage` và bản
lưu thắng toàn bộ, nên sửa `defaultHidden` xong mà màn hình không đổi thì không
phải mã sai.
