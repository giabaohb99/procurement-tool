/**
 * Số đo bố cục của khung nhìn Gantt — dùng chung cho lưới trái, hàng tiêu đề,
 * từng hàng thanh và lớp mũi tên phụ thuộc. Để riêng một tệp vì bốn component
 * đều cần: hằng số đặt trong tệp component sẽ bị `react-refresh` cảnh báo.
 *
 * Lệch một con số ở đây là lưới trái và trục phải trượt khỏi nhau theo hàng —
 * nhìn vẫn "có vẻ đúng" cho tới khi đối chiếu tên việc với thanh của nó.
 */

/** Chiều cao MỘT hàng — lưới trái và trục phải phải dùng đúng số này. */
export const ROW_HEIGHT = 36

/** Hai hàng tiêu đề (nhóm tháng/năm + ô ngày/tuần) — hai nửa cao bằng nhau. */
export const HEADER_HEIGHT = ROW_HEIGHT * 2

/** Khoảng hở trên/dưới của thanh trong lòng hàng. */
export const BAR_PAD = 7

export const BAR_HEIGHT = ROW_HEIGHT - BAR_PAD * 2

/**
 * Thanh hẹp hơn ngưỡng này thì ĐẶT TÊN RA NGOÀI, bên phải thanh — đúng lối Lark.
 * Phần lớn việc thật chỉ có hạn mà không có ngày bắt đầu nên thanh rộng đúng một
 * ngày: nhét chữ vào trong là mọi thẻ đều còn mỗi "C…".
 */
export const MIN_LABEL_WIDTH = 96

/** Bề rộng vùng bắt chuột của mép kéo (px). */
export const HANDLE_WIDTH = 7

/**
 * Đường kính chấm NỐI PHỤ THUỘC ở hai đầu thanh.
 *
 * 12px là mức nhỏ nhất còn trỏ trúng được bằng chuột mà không nuốt mất mép kéo
 * nằm ngay cạnh; chấm nằm HẲN NGOÀI thanh nên thanh một ngày (38px ở mức Ngày)
 * vẫn còn chỗ cho cả hai mép kéo.
 */
export const LINK_DOT = 12

/** Nửa đường chéo hình thoi của CỘT MỐC (B-14). */
export const MILESTONE_SIZE = 15

/**
 * Bề rộng tối thiểu của lưới trái — hẹp hơn thì cột tên cụt còn dăm ba chữ.
 * Bề rộng THẬT do người dùng kéo giãn từng cột quyết định.
 */
export const GRID_MIN_WIDTH = 260

/** Lề trái của một dòng ở lưới trái — chừa chỗ cho mũi tên thu/mở nhóm. */
export const GRID_PAD_LEFT = 10

/** `gap-1.5` giữa các ô của lưới trái, tính bằng px — phải khớp lớp Tailwind. */
export const COLUMN_GAP = 6

/** Thụt lề của dòng VIỆC so với dòng NHÓM chứa nó. */
export const GRID_INDENT = 18
