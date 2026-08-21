import type { BookKind } from './document-book'

export type NumberingDirection = BookKind
export type ScopeMode = 1 | 2
export type BookScopeMode = 1 | 2 | 3

export interface DocumentNumberingRule {
  id: number
  direction: NumberingDirection
  direction_label: string
  pattern: string
  start_no: number
  reset_yearly: boolean
  allow_manual: boolean
  doc_type_mode: ScopeMode
  book_mode: BookScopeMode
  priority: number
  is_active: boolean
  doc_type_ids: number[]
  book_ids: number[]
  doc_type_names: string[]
  book_names: string[]
  has_issued_numbers: boolean
}

export type DocumentNumberingRuleInput = Omit<
  DocumentNumberingRule,
  'id' | 'direction_label' | 'doc_type_names' | 'book_names' | 'has_issued_numbers'
>

export const NUMBERING_DIRECTIONS: Array<{ value: NumberingDirection; label: string }> = [
  { value: 1, label: 'Văn bản đến' },
  { value: 2, label: 'Văn bản đi' },
  { value: 3, label: 'Văn bản nội bộ' },
]

export const NUMBERING_TOKENS = [
  { token: '{STT}', label: 'Số thứ tự' },
  { token: '{Ngay}', label: 'Ngày phát hành' },
  { token: '{Thang}', label: 'Tháng phát hành' },
  { token: '{Nam}', label: 'Năm phát hành' },
  { token: '{LoaiVB}', label: 'Mã loại văn bản' },
  { token: '{PhongBan}', label: 'Mã phòng ban' },
  { token: '{PhapNhan}', label: 'Mã pháp nhân' },
  { token: '{SoVB}', label: 'Mã sổ văn bản' },
] as const

/** Các dấu thường dùng để ghép những phần của số hiệu. */
export const NUMBERING_SEPARATORS = [
  { token: '/', label: '/' },
  { token: '-', label: '-' },
  { token: '.', label: '.' },
  { token: '(', label: '(' },
  { token: ')', label: ')' },
] as const
