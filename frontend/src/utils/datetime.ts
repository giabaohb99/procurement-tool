// Backend lưu thời gian theo UTC (naive, không kèm 'Z'). Khi hiển thị phải quy về giờ VN (+7),
// nếu không JS sẽ hiểu nhầm là giờ local → lệch 7 tiếng.
const VN_TZ = 'Asia/Ho_Chi_Minh'

function toDate(v: any): Date | null {
  if (!v) return null
  let s = String(v)
  // Không có thông tin timezone (Z hoặc ±HH:MM) → coi là UTC
  if (!/[zZ]$|[+-]\d{2}:?\d{2}$/.test(s)) s += 'Z'
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

/** Ngày + giờ theo giờ VN, vd "09:46:41 09/07/2026". */
export function fmtDateTime(v: any): string {
  const d = toDate(v)
  return d ? d.toLocaleString('vi-VN', { timeZone: VN_TZ }) : ''
}

/** Chỉ ngày theo giờ VN. */
export function fmtDate(v: any): string {
  const d = toDate(v)
  return d ? d.toLocaleDateString('vi-VN', { timeZone: VN_TZ }) : ''
}

/**
 * Khoảng cách tới hiện tại, kiểu "5 phút trước" / "2 ngày trước" — dùng cho dòng trao đổi,
 * nơi "cách đây bao lâu" đáng quan tâm hơn mốc giờ chính xác.
 *
 * Quá `cutoffDays` (mặc định 60 ngày) thì trả về NGÀY THÁNG: đọc "14 tháng trước" không giúp
 * hình dung được gì, còn "12/03/2026" thì tra lại được ngay.
 */
export function fmtRelative(v: any, cutoffDays = 60): string {
  const d = toDate(v)
  if (!d) return ''
  const phut = Math.floor((Date.now() - d.getTime()) / 60000)
  // Lệch vài phút là chuyện thường (đồng hồ máy trạm so với máy chủ) — vẫn coi là vừa xong.
  // Lệch xa hẳn về tương lai thì dữ liệu có vấn đề, hiện thẳng mốc giờ cho dễ truy.
  if (phut < -5) return fmtDateTime(v)
  if (phut < 1) return 'Vừa xong'
  if (phut < 60) return `${phut} phút trước`
  const gio = Math.floor(phut / 60)
  if (gio < 24) return `${gio} giờ trước`
  const ngay = Math.floor(gio / 24)
  if (ngay < 7) return `${ngay} ngày trước`
  if (ngay < 30) return `${Math.floor(ngay / 7)} tuần trước`
  if (ngay < cutoffDays) return `${Math.floor(ngay / 30)} tháng trước`
  return fmtDate(v)
}
