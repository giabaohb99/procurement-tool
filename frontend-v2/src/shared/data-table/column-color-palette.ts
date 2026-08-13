import type { CSSProperties } from 'react'

export interface ColumnColor {
  id: string
  label: string
  /** Màu gốc — chỉ dùng để pha, không bao giờ tô nguyên độ đậm này lên ô. */
  value: string
}

/**
 * Bảng màu cho phép tô cột.
 *
 * Dùng mã màu cứng chứ không dùng token ngữ nghĩa (`--warning`, `--success`…):
 * đây là màu người dùng tự chọn để ĐÁNH DẤU cột cho dễ dò, không mang nghĩa
 * "cảnh báo" hay "thành công" nào cả. Tám tông lấy đúng bảng màu đang dùng cho
 * huy hiệu tiến độ để cả hệ nhìn cùng một gam.
 */
export const COLUMN_COLORS: ColumnColor[] = [
  { id: 'blue', label: 'Xanh dương', value: '#2563eb' },
  { id: 'cyan', label: 'Xanh ngọc', value: '#0891b2' },
  { id: 'green', label: 'Xanh lá', value: '#16a34a' },
  { id: 'amber', label: 'Vàng', value: '#d97706' },
  { id: 'orange', label: 'Cam', value: '#ea580c' },
  { id: 'red', label: 'Đỏ', value: '#dc2626' },
  { id: 'pink', label: 'Hồng', value: '#db2777' },
  { id: 'violet', label: 'Tím', value: '#7c3aed' },
]

const BY_ID = new Map(COLUMN_COLORS.map((color) => [color.id, color]))

/** Màu tự chọn được lưu thẳng dưới dạng mã hex (`#1a2b3c`), không có trong bảng trên. */
export function isCustomColor(id?: string): boolean {
  return /^#[0-9a-f]{6}$/i.test(id || '')
}

export function findColumnColor(id?: string): ColumnColor | undefined {
  if (isCustomColor(id)) return { id: id as string, label: 'Màu tùy chỉnh', value: id as string }
  return id ? BY_ID.get(id) : undefined
}

/**
 * Nền của ô thuộc cột đã tô màu.
 *
 * Pha bằng `color-mix` với nền nguyên bản để ra màu ĐỤC: ô của cột ghim đè lên
 * phần bảng đang cuộn ngang phía dưới, dùng màu có alpha là lộ nội dung xuyên
 * qua. Pha với biến nền nên tự đúng cả ở giao diện tối.
 */
export function columnColorStyle(
  colorId: string | undefined,
  part: 'head' | 'cell',
): CSSProperties | undefined {
  const color = findColumnColor(colorId)
  if (!color) return undefined

  const [ratio, base] = part === 'head' ? ['20%', 'var(--muted)'] : ['10%', 'var(--card)']
  return { backgroundColor: `color-mix(in oklab, ${color.value} ${ratio}, ${base})` }
}
