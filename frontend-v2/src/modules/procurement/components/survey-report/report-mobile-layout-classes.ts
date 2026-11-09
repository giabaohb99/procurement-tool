/**
 * Lớp Tailwind cho khổ ĐIỆN THOẠI (< md, 768px) của hai khối anh em "Báo cáo thực hiện"
 * và "Hồ sơ cần hoàn thành" (duoc-CR-737). Khai một chỗ để hai khối không lệch nhau.
 *
 * Luật chung: mọi lớp riêng điện thoại đều đi với tiền tố `max-md:`, còn lớp khổ rộng giữ
 * NGUYÊN chuỗi cũ — nên từ md trở lên màn hình y hệt trước. Nhóm con dùng `contents` ở khổ
 * rộng (vỏ bọc biến mất, con tham gia thẳng hàng flex của cha như cũ) và `max-md:flex` ở
 * khổ hẹp (vỏ bọc thành một hàng riêng, chiếm trọn bề ngang).
 */

/** Thanh công cụ: khổ rộng canh phải tự xuống dòng như cũ; điện thoại thành một cột trái. */
export const REPORT_TOOLBAR_CLASS =
  'flex flex-wrap items-center justify-end gap-2 max-md:w-full max-md:justify-start'

/** Một hàng con của thanh công cụ (ô tìm + lọc · cụm nút) — điện thoại chiếm trọn hàng. */
export const REPORT_TOOLBAR_ROW_CLASS =
  'contents max-md:flex max-md:w-full max-md:items-center max-md:gap-2'

/** Công tắc dạng xem: điện thoại kéo hết bề ngang, các nửa chia đều. */
export const REPORT_VIEW_TOGGLE_CLASS = 'flex items-center rounded-md border p-0.5 max-md:w-full'
export const REPORT_VIEW_MODE_BUTTON_MOBILE_CLASS = 'max-md:flex-1 max-md:justify-center'

/** Ô tìm: khổ rộng 12rem cố định; điện thoại giãn hết phần còn lại cạnh ô lọc trạng thái. */
export const REPORT_SEARCH_CLASS = 'h-8 w-48 flex-none max-md:w-auto max-md:flex-1'

/** Nút chữ ở hàng nút của điện thoại giãn theo chữ để cả hàng phủ kín, không lởm chởm. */
export const REPORT_TOOLBAR_BUTTON_MOBILE_CLASS = 'max-md:flex-auto'

/**
 * Lưới bốn ô tổng: điện thoại 2 x 2 (trước là 4 hàng một cột, nửa màn hình là ô trống).
 * Không cho ô tiến độ chiếm 2 cột: 3 ô còn lại sẽ để hở một lỗ ở hàng cuối.
 */
export const REPORT_SUMMARY_GRID_CLASS = 'grid grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4'
export const REPORT_SUMMARY_TILE_CLASS =
  'min-w-0 rounded-lg border bg-muted/20 px-2.5 py-2 sm:px-3 sm:py-2.5'
export const REPORT_SUMMARY_VALUE_CLASS = 'text-base font-semibold tabular-nums sm:text-lg'

/** Hàng tiêu đề giai đoạn / nhóm: điện thoại cho xuống dòng, tên giữ trọn hàng đầu. */
export const REPORT_GROUP_HEADER_CLASS = 'flex items-center gap-2.5 max-md:flex-wrap max-md:gap-y-1'
export const REPORT_GROUP_TITLE_CLASS = 'text-sm font-semibold max-md:min-w-0 max-md:flex-1'

/**
 * Cụm nút nhỏ (thêm · tạo mẫu · xóa cụm · sửa) trên tiêu đề giai đoạn: khổ rộng `contents`
 * nên khoảng cách giữa nút vẫn là `gap-2.5` của hàng cha; điện thoại khít lại (tiết kiệm
 * ~30px) để tên giai đoạn dài như "Đặt hàng & Hợp đồng" vẫn nằm một dòng.
 */
export const REPORT_GROUP_ACTIONS_CLASS = 'contents max-md:flex max-md:shrink-0 max-md:items-center'

/**
 * Vỏ bọc ghi chú giai đoạn + thanh tiến độ: điện thoại đẩy xuống hàng thứ hai (sau cả cụm
 * nút), thụt vào thẳng cột tên. Người gọi cộng `max-md:pl-*` theo bề rộng phần đứng trước tên.
 */
export const REPORT_GROUP_META_CLASS =
  'md:contents max-md:order-last max-md:flex max-md:basis-full max-md:items-center max-md:gap-2.5'

/** Thụt hàng thứ hai khi trước tên có nút gập + ô số thứ tự (16 + 10 + 24 + 10 = 60px). */
export const REPORT_GROUP_META_INDENT_WITH_TOGGLE = 'max-md:pl-[3.75rem]'
/** Thụt hàng thứ hai khi trước tên chỉ có ô số thứ tự (24 + 10 = 34px). */
export const REPORT_GROUP_META_INDENT_NUMBER_ONLY = 'max-md:pl-[2.125rem]'
