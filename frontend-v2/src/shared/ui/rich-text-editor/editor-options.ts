/**
 * Các lựa chọn cố định của thanh công cụ soạn thảo.
 *
 * Tách khỏi component để chỗ nào cần đọc danh sách (vd trang in) cũng dùng
 * chung một bảng, không chép lại.
 */

/** Giá trị của ô select khi đoạn đang chọn không có định dạng nào. */
export const INHERIT = 'inherit'

/** Phông chữ hành chính — Times New Roman đứng đầu theo Nghị định 30/2020. */
export const FONT_FAMILIES = [
  { label: 'Times New Roman', value: '"Times New Roman", serif' },
  { label: 'Arial', value: 'Arial, sans-serif' },
  { label: 'Cambria', value: 'Cambria, serif' },
  { label: 'Calibri', value: 'Calibri, sans-serif' },
  { label: 'Tahoma', value: 'Tahoma, sans-serif' },
  { label: 'Verdana', value: 'Verdana, sans-serif' },
]

/** Cỡ chữ tính bằng `pt` như Word — văn bản hành chính chuẩn là 13–14pt. */
export const FONT_SIZES = ['10pt', '11pt', '12pt', '13pt', '14pt', '16pt', '18pt', '24pt', '32pt']

/** Kiểu đoạn: đoạn thường + ba mức tiêu đề. */
export const BLOCK_STYLES = [
  { label: 'Đoạn văn', value: 'paragraph' },
  { label: 'Tiêu đề 1', value: '1' },
  { label: 'Tiêu đề 2', value: '2' },
  { label: 'Tiêu đề 3', value: '3' },
]

/** Bảng màu chữ / màu nền — đủ dùng cho văn bản, không cần bảng đầy đủ. */
export const TEXT_COLORS = [
  '#111827',
  '#dc2626',
  '#ea580c',
  '#ca8a04',
  '#16a34a',
  '#0891b2',
  '#2563eb',
  '#7c3aed',
  '#be185d',
  '#6b7280',
]

/**
 * Mức phóng to / thu nhỏ trang giấy, theo đúng các nấc của Google Docs.
 *
 * Giá trị là chuỗi vì ô select chỉ nhận chuỗi; đổi sang số lúc áp vào `zoom`.
 */
export const ZOOM_LEVELS = ['0.5', '0.75', '0.9', '1', '1.25', '1.5', '2'] as const

/** Giãn dòng theo nấc quen thuộc của Word — công văn thường quy định 1,5. */
export const LINE_HEIGHTS = [
  { label: 'Đơn (1,0)', value: '1' },
  { label: '1,15', value: '1.15' },
  { label: '1,5', value: '1.5' },
  { label: 'Đôi (2,0)', value: '2' },
] as const

export const HIGHLIGHT_COLORS = [
  '#fef08a',
  '#bbf7d0',
  '#bfdbfe',
  '#fbcfe8',
  '#e9d5ff',
  '#fed7aa',
]
