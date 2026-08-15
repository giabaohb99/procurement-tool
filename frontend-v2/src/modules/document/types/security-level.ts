/**
 * MỨC MẬT / KHẨN — hai thang đo song song, cùng một danh mục:
 *  - `confidential` (độ mật): ai được đọc.
 *  - `urgent` (độ khẩn): phải xử lý nhanh tới đâu.
 *
 * Một văn bản chọn tối đa một mức ở mỗi thang, nên `kind` phải có để lọc đúng
 * nhóm khi chọn.
 */
export type SecurityLevelKind = 'confidential' | 'urgent'

export const SECURITY_LEVEL_KIND_LABELS: Record<SecurityLevelKind, string> = {
  confidential: 'Độ mật',
  urgent: 'Độ khẩn',
}

export interface SecurityLevel {
  id: number
  code: string
  name: string
  kind: SecurityLevelKind
  /** Càng lớn càng nghiêm/gấp — dùng để xếp thứ tự và tô đậm nhạt. */
  rank: number
  description: string
  is_active: boolean
}

/** Thang mật / khẩn theo lối hành chính Việt Nam. */
export const DEFAULT_SECURITY_LEVELS: SecurityLevel[] = [
  { id: 1, code: 'THUONG', name: 'Thường', kind: 'confidential', rank: 0, description: 'Không hạn chế người đọc.', is_active: true },
  { id: 2, code: 'MAT', name: 'Mật', kind: 'confidential', rank: 1, description: 'Chỉ người được phân quyền mới xem.', is_active: true },
  { id: 3, code: 'TOIMAT', name: 'Tối mật', kind: 'confidential', rank: 2, description: 'Hạn chế nghiêm ngặt, có sổ theo dõi người đọc.', is_active: true },
  { id: 4, code: 'TUYETMAT', name: 'Tuyệt mật', kind: 'confidential', rank: 3, description: 'Mức cao nhất, do lãnh đạo chỉ định người đọc.', is_active: true },
  { id: 5, code: 'BINHTHUONG', name: 'Bình thường', kind: 'urgent', rank: 0, description: 'Xử lý theo thứ tự thông thường.', is_active: true },
  { id: 6, code: 'KHAN', name: 'Khẩn', kind: 'urgent', rank: 1, description: 'Xử lý trong ngày.', is_active: true },
  { id: 7, code: 'THUONGKHAN', name: 'Thượng khẩn', kind: 'urgent', rank: 2, description: 'Xử lý ngay khi nhận.', is_active: true },
  { id: 8, code: 'HOATOC', name: 'Hỏa tốc', kind: 'urgent', rank: 3, description: 'Chuyển và xử lý tức thì.', is_active: true },
]
