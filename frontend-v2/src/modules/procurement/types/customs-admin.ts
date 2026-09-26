/**
 * Hai danh mục cấu hình của màn Tra cứu giá hải quan — bao-CR-494 / bao-CR-495.
 * Tách khỏi `customs.ts` để không đụng tệp bao-CR-493 đang sửa.
 */

/** Nhãn Thành phẩm / Nguyên liệu của dòng hàng — khớp `ProductKind` backend (luật R2, lưu số). */
export const PRODUCT_KIND = {
  UNTAGGED: 0,
  FINISHED: 1,
  TECHNICAL: 2,
} as const

export type ProductKind = (typeof PRODUCT_KIND)[keyof typeof PRODUCT_KIND]

export const PRODUCT_KIND_OPTIONS = [
  { value: PRODUCT_KIND.TECHNICAL, label: 'Nguyên liệu (TC/TECH/TG)' },
  { value: PRODUCT_KIND.FINISHED, label: 'Thành phẩm' },
] as const

export function formatProductKindLabel(kind: number | null | undefined): string {
  if (kind === PRODUCT_KIND.TECHNICAL) return 'Nguyên liệu'
  if (kind === PRODUCT_KIND.FINISHED) return 'Thành phẩm'
  return ''
}

/** Một từ khóa nhận diện nhãn — `tab_customs_kind_keyword`. */
export type CustomsKindKeyword = {
  id: number
  keyword: string
  kind: number
  note: string
  is_active: boolean
}

/** Một nhóm từ đồng nghĩa cho ô tìm tên hàng — `tab_customs_search_synonym`. */
export type CustomsSearchSynonym = {
  id: number
  term: string
  /** Các cách viết tương đương, ngăn bằng «;». */
  synonyms: string
  note: string
  is_active: boolean
}

/** Kết quả `POST /api/customs/kinds/retag`. */
export interface CustomsRetagResult {
  total: number
  tagged: number
  technical: number
}
