import type { ExpiringLaborContract } from '../types/labor-contract'

/**
 * Câu ngắn nói HĐLĐ còn bao lâu (duoc-CR-620). Cùng cách nói với chuông cảnh báo ở backend
 * (`ExpiringContract.alert_title`) để hai chỗ không nói hai kiểu về cùng một hợp đồng.
 */
export function describeDaysLeft(daysLeft: number): string {
  if (daysLeft < 0) return `Quá hạn ${-daysLeft} ngày`
  if (daysLeft === 0) return 'Hết hạn hôm nay'
  return `Còn ${daysLeft} ngày`
}

/** Đếm theo mức để viết dòng mô tả của thẻ — mức do backend chấm, giao diện không tự tính lại. */
export function countByLevel(items: ExpiringLaborContract[]) {
  const overdue = items.filter((item) => item.days_left < 0).length
  const danger = items.filter((item) => item.level === 'danger').length
  return { total: items.length, overdue, danger, warn: items.length - danger }
}
