/** duoc-CR-784 — chữ cố định + nhịp của các bản in cụm Giá bao bì (tách khỏi tệp component để react-refresh không cảnh báo). */

/** Chờ một nhịp sau khi dữ liệu + font về để bảng / biểu đồ kịp dựng rồi mới mở hộp thoại in. */
export const PACKAGING_PRINT_DELAY_MS = 500
/** Chờ font Montserrat tối đa bấy nhiêu — mạng chậm thì in bằng font dự phòng chứ không treo. */
export const PACKAGING_PRINT_FONT_WAIT_MS = 2500
export const PACKAGING_PRINT_REPORT_TITLE = 'BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT'
export const PACKAGING_PRINT_CRUMB = 'Dego Holding › Phòng Thu mua › Báo cáo giá'
/** Font của bản mẫu (Google Fonts, có tiếng Việt). Không tải được thì rơi về `Segoe UI`, `Arial` như bản mẫu. */
export const PACKAGING_PRINT_FONT_URL =
  'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap&subset=vietnamese,latin-ext'
