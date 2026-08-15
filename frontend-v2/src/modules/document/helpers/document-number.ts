import type { DocumentDirection, DocumentRecord } from '../types/document-record'

/**
 * TỰ SINH SỐ HIỆU + VÀO SỔ.
 *
 * Sổ tính riêng theo (luồng × năm): văn bản đến, đi và nội bộ mỗi loại một sổ,
 * và sang năm mới thì đánh số lại từ 1 — đúng lệ hành chính.
 *
 * Số hiệu ghép từ tiền tố của LOẠI văn bản: `CV-2026-001`.
 */

/** Số vào sổ kế tiếp của một luồng trong năm. */
export function nextBookNo(
  records: DocumentRecord[],
  direction: DocumentDirection,
  year: number,
): number {
  const used = records.filter(
    (record) => record.direction === direction && record.book_year === year,
  )
  // Lấy MAX chứ không đếm số bản ghi: xóa một văn bản giữa sổ mà đếm thì số kế
  // tiếp sẽ đụng vào số đã cấp.
  return used.reduce((max, record) => Math.max(max, record.book_no), 0) + 1
}

/** `CV` + 2026 + 1 → `CV-2026-001`. */
export function buildDocumentCode(prefix: string, year: number, bookNo: number): string {
  return `${prefix || 'VB'}-${year}-${String(bookNo).padStart(3, '0')}`
}

/** Năm dùng để vào sổ: theo NGÀY BAN HÀNH, không phải ngày ngồi nhập. */
export function bookYearOf(issuedDate: string): number {
  const parsed = issuedDate ? new Date(issuedDate) : new Date()
  return Number.isNaN(parsed.getTime()) ? new Date().getFullYear() : parsed.getFullYear()
}
