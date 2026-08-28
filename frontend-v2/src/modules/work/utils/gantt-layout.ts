/**
 * Số đo bố cục của khung nhìn Gantt — dùng chung cho lưới trái, hàng tiêu đề và
 * từng hàng thanh. Để riêng một tệp vì cả `gantt-view.tsx` lẫn `gantt-row.tsx`
 * đều cần: hằng số đặt trong tệp component sẽ bị `react-refresh` cảnh báo.
 *
 * Lệch một con số ở đây là lưới trái và trục phải trượt khỏi nhau theo hàng —
 * nhìn vẫn "có vẻ đúng" cho tới khi đối chiếu tên việc với thanh của nó.
 */

/** Lưới trái — bố cục DHTMLX: cột tên việc rộng, rồi hai cột ngày hẹp. */
export const GRID_COLUMNS = [
  { key: 'title', label: 'Công việc', width: 220 },
  { key: 'start', label: 'Bắt đầu', width: 82 },
  { key: 'due', label: 'Hạn', width: 82 },
] as const

export const GRID_WIDTH = GRID_COLUMNS.reduce((sum, c) => sum + c.width, 0)

export const ROW_HEIGHT = 34

/** Hai hàng tiêu đề (nhóm tháng/năm + ô ngày) — hai nửa phải cao bằng nhau. */
export const HEADER_HEIGHT = ROW_HEIGHT * 2

/**
 * Thanh hẹp hơn ngưỡng này thì ĐẶT TÊN RA NGOÀI, bên phải thanh — đúng lối
 * DHTMLX. Phần lớn việc thật chỉ có hạn mà không có ngày bắt đầu nên thanh rộng
 * đúng một ngày: nhét chữ vào trong là mọi thẻ đều còn mỗi "C…".
 */
export const MIN_LABEL_WIDTH = 96

/** Bề rộng vùng bắt chuột của mép kéo (px). */
export const HANDLE_WIDTH = 7
