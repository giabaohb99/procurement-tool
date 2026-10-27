import { formatDate, parseLocalDate } from '@/shared/utils/format-date'

import type { ReportDrilldownColumnKind, ReportDrilldownRow } from '../types/report-drilldown'
import { formatReportMetricValue } from './format-report-metric'

const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/

/** Số từ JSON — backend có thể trả `Decimal` thành chuỗi ("1500000.00"). Không phải số → `null`. */
function toFiniteNumber(value: unknown): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  if (typeof value === 'string' && value.trim() !== '') {
    const n = Number(value)
    return Number.isFinite(n) ? n : null
  }
  return null
}

/**
 * Định dạng MỘT ô của ngăn «Danh sách người» theo `kind` backend khai (duoc-CR-686):
 * `date` → dd/MM/yyyy · `int` → 1.234 · `days` → "2,5 ngày" · `money` → "1.500.000 đ".
 *
 * Giá trị trống (`null`, `""`, thiếu khóa) hoặc không đọc được → `""` (ô trống), KHÔNG
 * phải "0" hay "—": số 0 là giá trị thật (vd "Còn 0 ngày"), ô trống là "không có".
 */
export function formatDrilldownCell(value: unknown, kind: ReportDrilldownColumnKind): string {
  if (value === null || value === undefined || value === '') return ''
  switch (kind) {
    case 'date': {
      if (typeof value !== 'string') return ''
      //  Ngày trần dựng theo giờ ĐỊA PHƯƠNG — `new Date('2026-10-27')` là mốc UTC, ở múi
      //  giờ âm nó lùi về hôm trước.
      return formatDate(DATE_ONLY.test(value) ? (parseLocalDate(value) ?? null) : value)
    }
    case 'int':
    case 'days':
    case 'money': {
      const n = toFiniteNumber(value)
      return n === null ? '' : formatReportMetricValue(n, kind)
    }
    default:
      return typeof value === 'object' ? '' : String(value)
  }
}

/**
 * Đường của dòng nếu là đường NỘI BỘ giao diện v2 (`/hr/...`) — đường tuyệt đối ra ngoài
 * (`https://…`, `//host`) hay `javascript:` bị bỏ: dữ liệu hàng không phải chỗ để mở cửa ra
 * trang lạ.
 */
export function resolveDrilldownLink(row: ReportDrilldownRow): string | null {
  const link = row.link
  if (typeof link !== 'string') return null
  if (!link.startsWith('/') || link.startsWith('//') || link.startsWith('/\\')) return null
  return link
}
