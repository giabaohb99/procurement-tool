import type { CellGetters } from '@/shared/utils/sort-rows-by-cell'
import { DOCUMENT_STATUS, type DocumentRecord } from '../types/document-record'

/** Hạng vòng đời của trạng thái — KHỚP `_STATUS_RANK` ở `backend/app/modules/document/sort_expressions.py`. */
const STATUS_RANK: Record<number, number> = {
  [DOCUMENT_STATUS.draft]: 1,
  [DOCUMENT_STATUS.returned]: 2,
  [DOCUMENT_STATUS.submitted]: 3,
  [DOCUMENT_STATUS.pendingIssue]: 4,
  [DOCUMENT_STATUS.approved]: 5,
  [DOCUMENT_STATUS.effective]: 7,
  [DOCUMENT_STATUS.expired]: 8,
  [DOCUMENT_STATUS.replaced]: 9,
  [DOCUMENT_STATUS.revoked]: 10,
  [DOCUMENT_STATUS.archived]: 11,
  [DOCUMENT_STATUS.rejected]: 12,
}
const RANK_NOT_YET_EFFECTIVE = 6
const RANK_EXPIRED = 8
const RANK_UNKNOWN = 99

/** `yyyy-mm-dd` -> mốc đầu ngày; rỗng / sai định dạng -> null. */
function dayStart(value: string | null): number | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
}

/**
 * Hạng của trạng thái đúng như chữ ô hiện: "Hết hiệu lực" / "Chưa hiệu lực" suy ra từ ngày (xem
 * `effectiveLabel`) chứ không phải mã số thô. `today` truyền vào để bài kiểm không phụ thuộc "hôm nay".
 */
export function documentStatusRank(
  row: Pick<DocumentRecord, 'status' | 'effective_date' | 'expire_date'>,
  today: Date = new Date(),
): number {
  if (row.status === DOCUMENT_STATUS.effective) {
    const now = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime()
    const to = dayStart(row.expire_date)
    const from = dayStart(row.effective_date)
    if (to !== null && to < now) return RANK_EXPIRED
    if (from !== null && from > now) return RANK_NOT_YET_EFFECTIVE
  }
  return STATUS_RANK[row.status] ?? RANK_UNKNOWN
}

/**
 * Giá trị ô đang hiện của từng cột xếp được của tab Văn bản đến (duoc-CR-744). Tab này tải TRỌN danh sách
 * một lần (`/applies-to-me` không phân trang, không nhận `sort_by`) nên xếp tại chỗ trên cả tập.
 */
export function buildIncomingSortGetters(today: Date = new Date()): CellGetters<DocumentRecord> {
  return {
    id: (r) => r.id,
    display_code: (r) => r.display_code,
    title: (r) => r.title,
    doc_type_name: (r) => r.doc_type_name,
    status: (r) => documentStatusRank(r, today),
    effective_date: (r) => r.effective_date,
    company_name: (r) => r.company_name,
    department_name: (r) => r.department_name,
    secrecy_level: (r) => r.secrecy_level,
    owner_name: (r) => r.owner_name,
  }
}
