import { formatQuantity } from '@/shared/utils/format-money'

/**
 * Điểm hiển thị là SỐ NGUYÊN có phân tách nghìn, nhãn đơn vị là "điểm" — dù đề
 * nghị N1 là 1 điểm = 1 đồng, nhãn phải là điểm để sau đổi tỷ lệ không sửa chữ.
 */
export function formatPoints(value: number | null | undefined): string {
  return formatQuantity(value ?? 0)
}

/** Dòng sổ: dấu +/− tường minh để cột đọc lướt được chiều tăng giảm. */
export function formatSignedPoints(value: number): string {
  const text = formatPoints(Math.abs(value))
  return value < 0 ? `−${text}` : `+${text}`
}
