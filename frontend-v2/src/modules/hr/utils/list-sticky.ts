/**
 * Các dải GHIM ĐẦU TRANG của những màn danh sách BA TAB trong phân hệ Nhân sự ở
 * khổ điện thoại — Đơn nghỉ phép và Phiếu đặt phòng họp dùng chung.
 *
 * ⚠️ **Đừng chép mấy chuỗi này sang màn mới, hãy import.** Chúng là một hệ mốc
 * `top` CỘNG DỒN (xem ghi chú ngay dưới): một bản chép sẽ chỉ sai vào ngày ai đó
 * sửa chiều cao dải tab ở một chỗ, và sai kiểu chỉ lộ ra khi cuộn.
 *
 * Ở khổ hẹp trang bỏ chế độ `fill` (xem ghi chú trong `leave-request-list-page`)
 * nên CẢ TRANG cuộn — danh sách 20 thẻ dài hơn 3000px. Không ghim thì hai thứ
 * người ta cần nhất trong lúc đọc đều trôi mất ngay nhịp vuốt đầu tiên: **thanh
 * ba tab** (đang xem hàng đợi hay phiếu của mình) và **ô tìm + bộ lọc**. Muốn lọc
 * lại thì phải vuốt ngược lên đầu, lọc xong lại vuốt xuống.
 *
 * ⚠️ **Hai mốc `top` phải cộng dồn, và đó là lý do chúng khai chung một chỗ.**
 * Dải tab cao 36px (`TabsList` = `h-9`) cộng 8px đệm dưới = **44px**, nên thanh
 * công cụ ghim ở `top-11`. Sửa cỡ dải tab mà quên sửa mốc kia thì hai dải chồng
 * lên nhau (mốc nhỏ hơn) hoặc hở một khe cho nội dung chạy qua giữa (mốc lớn
 * hơn) — cả hai đều chỉ lộ ra khi cuộn, không lộ lúc dựng màn.
 *
 * ⚠️ **Nền phải ĐỤC và phải trải hết bề ngang.** Dải ghim là một khối nổi trên
 * nội dung đang chạy bên dưới nó; nền trong suốt (hoặc có alpha) thì chữ của thẻ
 * hiện xuyên qua chữ của ô tìm. Cặp lề âm + đệm bù (`-mx-4 px-4`) để nền phủ hết
 * phần đệm của khung cha, nếu không thì hai mép trái/phải chừa hai khe hở cho
 * nội dung trôi qua — cùng bài học với `PIN_*` của `DataTable`.
 *
 * ⚠️ **BÓNG ĐỔ chỉ hiện khi đã cuộn**, và chỉ ở dải DƯỚI CÙNG.
 *
 * Điều kiện `group-data-[scrolled]` đọc thuộc tính `data-scrolled` mà trang gắn
 * lên `<Tabs className="group">` từ `useScrolled` — bóng mờ dần trong 200ms nên
 * lúc ghim vào không bị "khựng" một nhát. Đổ sẵn từ đầu thì dải trông như đang
 * nổi giữa một trang đứng yên: bóng là câu nói *"có nội dung đang trôi bên
 * dưới"*, nói lúc chưa có gì trôi là nói sai.
 *
 * Chỉ dải THANH CÔNG CỤ đổ bóng, không phải dải tab: hai dải chồng lên nhau
 * (`z-30` trên `z-20`) nên bóng của dải tab sẽ vẽ ĐÈ lên mặt thanh công cụ,
 * thành một vệt xám ngang giữa hai dải chứ không ra chiều sâu.
 *
 * ⚠️ **Khoảng hở dưới dải ghim phải là ĐỆM, không được là LỀ.** `DataTable` đặt
 * sẵn `mb-4` cho thanh công cụ; lề nằm NGOÀI hộp được tô nền, nên thẻ cuộn qua
 * hiện nguyên một vạch chữ cụt trong dải 16px ngay dưới ô tìm — trông đúng như
 * lỗi vẽ. Đổi thành `mb-0` + `pb-3` thì khoảng hở đó nằm trong phần được tô.
 * `border-b` để dải có ranh giới rõ, không thì thẻ trượt vào như bị cắt ngang.
 */

/**
 * Dải BA TAB — ghim sát đỉnh khung cuộn. Bọc ngoài `<TabsList>`.
 *
 * Dùng ở: Đơn nghỉ phép · Phiếu đặt phòng họp.
 */
export const LIST_TABS_STICKY =
  'max-md:sticky max-md:top-0 max-md:z-30 max-md:-mx-4 max-md:bg-canvas max-md:px-4 max-md:pb-2'

/**
 * Dải TAB CHUYỂN MÀN của một cụm màn (`LeaveSectionTabs sticky` ·
 * `RoomSectionTabs sticky`) — ghim sát đỉnh khung cuộn.
 *
 * Dùng ở màn **không có hàng tab thứ hai** (Quỹ phép năm · Danh mục phòng họp):
 * ở đó dải này là hàng điều hướng duy nhất nên nó phải là thứ ở lại. Màn Đơn
 * nghỉ phép và Phiếu đặt phòng thì ngược lại — hàng BA TAB bên trong mới ghim
 * (`LIST_TABS_STICKY`), còn dải chuyển màn cuộn đi; ghim cả hai là hai dải chồng
 * nhau ăn 84px trên một màn 852px.
 *
 * Cao **40px**: `pt-1` 4 + nhãn `py-1.5 text-xs` 28 + `pb-2` 8 — đó là mốc
 * `top-10` của `LIST_SECTION_TOOLBAR_STICKY`, sửa cái này thì sửa luôn cái kia.
 *
 * ⚠️ `max-md:pb-2` ở đây **đè lên `pb-3`** mà cả hai component tự đặt (khác
 * variant nên tailwind-merge giữ cả hai, media query quyết). Nhờ vậy hai dải
 * khác cấu trúc — một cái `<div space-y-2>`, một cái `<nav>` — vẫn ra đúng cùng
 * 40px, tức dùng chung được một mốc `top`.
 */
export const LIST_SECTION_TABS_STICKY =
  'max-md:sticky max-md:top-0 max-md:z-30 max-md:-mx-4 max-md:bg-canvas max-md:px-4 max-md:pt-1 max-md:pb-2'

/**
 * Phần chung của dải THANH CÔNG CỤ ghim — chỉ khác nhau ở mốc `top`, mà mốc đó
 * bằng đúng chiều cao của dải nằm TRÊN nó.
 *
 * Lề âm tính theo đệm `p-3` của `Card` ở khổ hẹp, không phải `p-4` của trang.
 */
const TOOLBAR_STICKY_BASE =
  'max-md:sticky max-md:z-20 max-md:-mx-3 max-md:-mt-3 max-md:mb-0 max-md:border-b max-md:bg-card max-md:px-3 max-md:pt-3 max-md:pb-3 max-md:transition-shadow max-md:duration-200 max-md:group-data-[scrolled]:shadow-[0_6px_12px_-8px_rgb(0_0_0/0.35)]'

/**
 * Dải THANH CÔNG CỤ ghim dưới dải BA TAB (cao 44px). Truyền vào
 * `DataTableProps.toolbarClassName`.
 *
 * Dùng ở: Đơn nghỉ phép · Phiếu đặt phòng họp.
 */
export const LIST_TOOLBAR_STICKY = `${TOOLBAR_STICKY_BASE} max-md:top-11`

/**
 * Dải THANH CÔNG CỤ ghim dưới dải TAB CHUYỂN MÀN (cao 40px).
 *
 * Dùng ở: Quỹ phép năm · Danh mục phòng họp.
 */
export const LIST_SECTION_TOOLBAR_STICKY = `${TOOLBAR_STICKY_BASE} max-md:top-10`

/**
 * Dải THANH CÔNG CỤ của hai màn **Thiết lập** (Loại nghỉ · Lịch ngày lễ), nơi
 * dải điều hướng có HAI hàng nên cao **78px**: `pt-1` 4 + tab chuyển màn 28 +
 * khe `space-y-2` 8 + hàng tab con 30 (chữ 20 + `pb-2` 8 + gạch chân 2) +
 * `pb-2` 8.
 *
 * ⚠️ Mốc lẻ nên phải khai giá trị tùy ý (`top-[78px]`), không làm tròn về
 * `top-19` (76px): thiếu 2px thì thanh công cụ **đè lên đúng gạch chân** của tab
 * con đang mở — dấu hiệu duy nhất nói đang ở Loại nghỉ hay Lịch ngày lễ. Đo lại
 * bằng `getBoundingClientRect` mỗi khi sửa hai hàng đó, đừng nhẩm.
 *
 * ⚠️ 78px điều hướng + 61px thanh công cụ = **139px bị che thường trực** trên
 * màn 852px. Chấp nhận được vì hai danh mục này chỉ hơn chục dòng (khách chốt
 * 09/09/2026); danh mục nào dài hàng trăm dòng thì cân nhắc lại trước khi chép
 * mốc này sang.
 */
export const LEAVE_SETTINGS_TOOLBAR_STICKY = `${TOOLBAR_STICKY_BASE} max-md:top-[78px]`

/**
 * Dải THANH CÔNG CỤ của màn danh mục **đứng một mình** — không có dải tab nào
 * phía trên nên ghim thẳng lên đỉnh khung cuộn.
 *
 * Dùng ở: Danh mục chức vụ.
 *
 * Mốc `top-0` KHÔNG có nghĩa là "sát mép màn hình": khung cuộn ở khổ hẹp là
 * vùng nội dung nằm dưới thanh trên cùng của app, nên dải này ghim ngay dưới
 * thanh đó. Tiêu đề trang và nút *Thêm…* cuộn đi bên trên nó — cố ý: cả hai
 * chỉ cần một lần lúc mở màn, còn ô tìm thì cần suốt lúc đọc danh sách.
 */
export const LIST_TOOLBAR_STICKY_TOP = `${TOOLBAR_STICKY_BASE} max-md:top-0`

/**
 * Dải THANH CÔNG CỤ của một bảng nằm trong TAB của trang chi tiết CRUD.
 *
 * Dùng ở: tab *«Người đang giữ»* của Chức vụ.
 *
 * ⚠️ Mốc `61px` là chiều cao **hàng nút Lưu/Xóa** mà `CrudDetailPage` đã ghim
 * sẵn ở `top-0`: đệm `py-3` (12+12) + nút `h-9` (36) + `border-b` (1). Sửa cỡ
 * nút hay đệm của hàng đó thì **phải đo lại bằng `getBoundingClientRect` và sửa
 * luôn số này** — nhỏ hơn thì thanh công cụ chui lên dưới hàng nút, lớn hơn thì
 * hở một khe cho thẻ nhân sự trôi qua giữa hai dải. Cả hai chỉ lộ ra khi cuộn.
 *
 * ⚠️ **Chỉ ghim thanh công cụ, KHÔNG ghim dải tab.** Ghim cả hai thì
 * 61 (hàng nút) + 44 (dải tab) + 61 (thanh công cụ) = **166px trên 788px nhìn
 * thấy được**, tức hơn một phần năm màn hình đứng yên vĩnh viễn. Dải tab đổi
 * lấy chỗ đó không đáng: nó trả lời câu *«đang ở tab nào»*, mà giữa một danh
 * sách gương mặt thì câu đó không ai phải hỏi.
 *
 * ⚠️ Bóng đổ đòi tổ tiên mang `group` + `data-scrolled` — `CrudDetailPage` dựng
 * sẵn (xem `stickyRef` ở đó). Thiếu nó thì dải vẫn ghim, chỉ là không bao giờ
 * đổ bóng, và lỗi đó im lặng.
 */
export const DETAIL_TOOLBAR_STICKY = `${TOOLBAR_STICKY_BASE} max-md:top-[61px]`
