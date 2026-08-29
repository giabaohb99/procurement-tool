/**
 * Số đo bố cục của khung nhìn Danh sách — khai MỘT chỗ.
 *
 * Bốn thứ phải khớp nhau từng pixel, mà chúng nằm ở ba tệp khác nhau: lề trái
 * của dòng, ô giữ chỗ dẫn đầu, trục của nét nối việc con, và lề trái của ô tiêu
 * đề «Tên công việc». Gõ số thẳng vào từng nơi thì thêm một cái tay cầm kéo là
 * lệch hàng ba chỗ mà không ai nhớ hết.
 */

/** Lề trái của dòng — rộng hơn `px-2` thường để chừa chỗ cho tay cầm kéo. */
export const ROW_PAD_LEFT = 24

/** Mũi tên bung việc con + ô tick: phần dẫn đầu trước TÊN việc. */
export const LEAD_WIDTH = 46

/** Trục nét nối việc con — trùng tâm ô tick của việc CHA. */
export const GUIDE_LEFT = ROW_PAD_LEFT + 22

/** Lề trái của ô tiêu đề «Tên công việc», để nó thẳng hàng với tên việc. */
export const HEADER_TITLE_PAD = ROW_PAD_LEFT + LEAD_WIDTH
