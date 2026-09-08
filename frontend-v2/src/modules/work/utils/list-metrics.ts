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

/**
 * Khe giữa các ô trong MỘT dòng — hàng tiêu đề, dòng việc và dòng nháp đều phải
 * lấy đúng con số này, và phải lấy qua `style={{ gap: COLUMN_GAP }}` chứ KHÔNG
 * gõ lớp `gap-*`.
 *
 * ⚠️ Đây từng là ba con số khác nhau nằm ở ba tệp: hàng tiêu đề `gap-1.5` (6px),
 * dòng việc `gap-2` (8px), dòng nháp `gap-1.5`. Lệch 2px mỗi cột thì cột đầu
 * nhìn còn khớp, tới cột thứ tám nhãn đã trôi khỏi cột của nó 22px — đo thật:
 * nhãn «Trạng thái» ở x=868 trong khi ô trạng thái ở x=882. Bề rộng nội dung
 * của lưới cũng tính bằng hằng này, nên sai nó là cột cuối bị cắt cụt.
 */
export const COLUMN_GAP = 8
