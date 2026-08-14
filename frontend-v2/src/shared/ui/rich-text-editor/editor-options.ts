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

/**
 * BẢNG MÀU dùng chung cho màu chữ, tô nền chữ và nền ô bảng.
 *
 * Xếp như Word: hàng đầu là dải xám từ trắng tới đen, mười hàng dưới là mười
 * sắc màu đi từ nhạt tới đậm — cùng một cột là cùng một màu, càng xuống càng
 * đậm, nên mắt dò theo cột chứ không phải quét cả bảng. Ai cần đúng màu nhận
 * diện của đơn vị thì bấm "Màu khác" chọn tay.
 */
export const COLOR_PALETTE_ROWS = [
  [
    '#ffffff',
    '#f1f5f9',
    '#e2e8f0',
    '#cbd5e1',
    '#94a3b8',
    '#64748b',
    '#475569',
    '#334155',
    '#1e293b',
    '#000000',
  ],
  [
    '#fee2e2',
    '#ffedd5',
    '#fef3c7',
    '#dcfce7',
    '#ccfbf1',
    '#cffafe',
    '#dbeafe',
    '#e0e7ff',
    '#ede9fe',
    '#fce7f3',
  ],
  [
    '#fca5a5',
    '#fdba74',
    '#fcd34d',
    '#86efac',
    '#5eead4',
    '#67e8f9',
    '#93c5fd',
    '#a5b4fc',
    '#c4b5fd',
    '#f9a8d4',
  ],
  [
    '#ef4444',
    '#f97316',
    '#eab308',
    '#22c55e',
    '#14b8a6',
    '#06b6d4',
    '#3b82f6',
    '#6366f1',
    '#8b5cf6',
    '#ec4899',
  ],
  [
    '#b91c1c',
    '#c2410c',
    '#a16207',
    '#15803d',
    '#0f766e',
    '#0e7490',
    '#1d4ed8',
    '#4338ca',
    '#6d28d9',
    '#be185d',
  ],
  [
    '#7f1d1d',
    '#7c2d12',
    '#713f12',
    '#14532d',
    '#134e4a',
    '#164e63',
    '#1e3a8a',
    '#312e81',
    '#4c1d95',
    '#831843',
  ],
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

