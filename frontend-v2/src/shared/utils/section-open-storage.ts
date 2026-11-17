/**
 * Nhớ trạng thái GẬP / MỞ của một khối trong `localStorage` — dùng chung cho `CollapsibleSection` và thẻ gập
 * được (`useCardCollapse`), để hai kiểu khối cùng một khuôn khóa `erp.section.<khóa>`.
 */
const STORAGE_PREFIX = 'erp.section.'

/** Bản lưu của người dùng; `null` = **chưa từng** bấm gập/mở khối này (hoặc không có khóa). */
export function readSectionOpen(storageKey: string | undefined): boolean | null {
  if (!storageKey) return null
  try {
    const saved = localStorage.getItem(STORAGE_PREFIX + storageKey)
    return saved === null ? null : saved === '1'
  } catch {
    //  Chế độ riêng tư / bộ nhớ đầy thì `localStorage` NÉM. Nuốt và coi như chưa có bản lưu: nhớ trạng thái
    //  gập là tiện nghi, không đáng làm trắng cả trang.
    return null
  }
}

/** Ghi trạng thái; không ghi được thì thôi — trạng thái vẫn đúng trong phiên này. */
export function writeSectionOpen(storageKey: string | undefined, open: boolean): void {
  if (!storageKey) return
  try {
    localStorage.setItem(STORAGE_PREFIX + storageKey, open ? '1' : '0')
  } catch {
    //  Xem ghi chú ở `readSectionOpen`.
  }
}
