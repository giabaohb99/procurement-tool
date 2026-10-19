import { appConfig } from '@/core/config/app-config'

/**
 * Ô «Số ký tự kết quả» của Nhật ký lượt gọi (ai-CR-228). Máy chủ trả 0 cho lượt không phải tools/call (khởi tạo,
 * liệt kê, thông báo) và cho dòng cũ trước ai-CR-228 — 0 ở đây nghĩa "không đo", nên in gạch chứ không in «0» kẻo
 * người đọc tưởng công cụ trả về rỗng. Máy chủ chưa có trường (bản trước ai-CR-228) hay số hỏng cũng in gạch.
 * Lưu ý: trong `DataTable` ô chuỗi «—» được đổi thành ô trống (luật CR-132), giống mọi cột trống khác của màn.
 */
export function formatResultChars(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return '—'
  return Math.round(value).toLocaleString(appConfig.locale, { maximumFractionDigits: 0 })
}
