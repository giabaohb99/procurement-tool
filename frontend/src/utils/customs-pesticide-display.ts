// Các hàm HIỂN THỊ của trang chi tiết thuốc BVTV (01/10/2026 — làm lại thẻ «Thông tin đăng ký»).
// BẢN SAO của `frontend-v2/src/modules/procurement/utils/customs-pesticide-display.ts` (hai app không
// dùng chung mã) — bài kiểm nằm bên v2; sửa luật ở đây thì sửa cả bên đó.
// Chỉ đổi cách bày, KHÔNG đổi giá trị lưu: chuỗi gốc của trang nguồn vẫn là thứ được lưu và xuất.

export type ToxicitySeverity = 'high' | 'medium' | 'low' | 'unknown'

export interface ToxicityItem {
  /** "GHS 5", "WHO 2" — rỗng khi đoạn đó không theo khuôn của nguồn. */
  code: string
  /** "Rất ít độc/Không độc" — hoặc NGUYÊN đoạn gốc khi không tách được. */
  label: string
  severity: ToxicitySeverity
}

//  Khuôn của nguồn: "GHS 5 (GHS - Nhóm 5: Rất ít độc/Không độc)", nhiều nhóm nối bằng ";".
const TOXICITY_PATTERN = /^(GHS|WHO)\s*([0-9A-Za-z]+)\s*\((?:[^:]*:\s*)?(.+)\)$/

function severityOf(label: string): ToxicitySeverity {
  const text = label.toLocaleLowerCase('vi')
  if (text.includes('rất độc') || text.includes('độc cao')) return 'high'
  if (text.includes('trung bình')) return 'medium'
  if (text.includes('ít độc') || text.includes('không độc')) return 'low'
  return 'unknown'
}

/**
 * Tách chuỗi «Nhóm độc» thành từng nhóm để bày thành thẻ nhỏ thay cho một dòng chữ dài.
 * Đoạn không khớp khuôn KHÔNG bị bỏ — trả nguyên văn (`code` rỗng) để không mất thông tin.
 */
export function parsePesticideToxicity(raw: string | null | undefined): ToxicityItem[] {
  if (!raw) return []
  return raw
    .split(';')
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const match = TOXICITY_PATTERN.exec(part)
      if (!match) return { code: '', label: part, severity: 'unknown' as const }
      const label = match[3].trim()
      return { code: `${match[1]} ${match[2]}`, label, severity: severityOf(label) }
    })
}

/**
 * Chuỗi VIẾT HOA toàn bộ của nguồn ("THUỐC SỬ DỤNG TRONG NÔNG NGHIỆP") → viết hoa chữ đầu.
 * Chuỗi đã có chữ thường thì để nguyên — có thể chứa tên riêng, viết tắt người nhập cố ý.
 */
export function toSentenceCaseIfShouting(value: string): string {
  const upper = value.toLocaleUpperCase('vi')
  if (value !== upper || value === value.toLocaleLowerCase('vi')) return value
  const lower = value.toLocaleLowerCase('vi')
  return lower.charAt(0).toLocaleUpperCase('vi') + lower.slice(1)
}

function parseIsoDate(value: string): { y: number; m: number; d: number } | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
  if (!match) return null
  return { y: Number(match[1]), m: Number(match[2]), d: Number(match[3]) }
}

/**
 * Thời hạn đăng ký còn lại tính tới `today` (truyền vào, không tự đọc đồng hồ): "còn 2 năm 11
 * tháng" · "còn 20 ngày" · "Đã hết hạn". Tính theo LỊCH (tháng/năm), không chia 30/365.
 * `null` khi không có ngày hết hạn đọc được.
 */
export function describeRemainingTerm(expiresOn: string | null, today: Date): string | null {
  const end = expiresOn ? parseIsoDate(expiresOn) : null
  if (!end) return null
  const t = { y: today.getFullYear(), m: today.getMonth() + 1, d: today.getDate() }
  const endKey = end.y * 10000 + end.m * 100 + end.d
  const todayKey = t.y * 10000 + t.m * 100 + t.d
  if (endKey < todayKey) return 'Đã hết hạn'

  let months = (end.y - t.y) * 12 + (end.m - t.m)
  if (end.d < t.d) months -= 1
  if (months <= 0) {
    const days = Math.round(
      (Date.UTC(end.y, end.m - 1, end.d) - Date.UTC(t.y, t.m - 1, t.d)) / 86_400_000,
    )
    return days === 0 ? 'Hết hạn hôm nay' : `còn ${days} ngày`
  }
  const years = Math.floor(months / 12)
  const rest = months % 12
  if (years === 0) return `còn ${rest} tháng`
  return rest === 0 ? `còn ${years} năm` : `còn ${years} năm ${rest} tháng`
}
