/**
 * Phiếu giao của LẦN GIAO CHƯA LƯU trên Đơn mua hàng.
 *
 * Lần giao mới chưa có id nên chưa gắn tệp vào đâu được: trang giữ hộ tệp trong
 * bộ nhớ, bấm "Lưu đơn" xong mới tải lên đúng lần giao server vừa trả về. Cùng ý
 * tưởng với `pending-line-files.ts` của phiếu khảo sát, khác ở chỗ mỗi DÒNG HÀNG
 * có một bảng lần giao riêng nên khóa phải gồm cả hai chỉ số.
 *
 * Hệ quả: xóa dòng hàng hay xóa lần giao là mọi thứ phía sau đổi chỉ số — không
 * dời khóa theo thì tệp nhảy sang lần giao khác, mà lúc phát hiện thì đã tải
 * nhầm lên server rồi.
 */
export type PendingDeliveryFiles = Record<string, File[]>

const SEPARATOR = ':'

export function deliveryFileKey(lineIndex: number, deliveryIndex: number): string {
  return `${lineIndex}${SEPARATOR}${deliveryIndex}`
}

export function parseDeliveryFileKey(key: string): {
  lineIndex: number
  deliveryIndex: number
} {
  const [line, delivery] = key.split(SEPARATOR)
  return { lineIndex: Number(line), deliveryIndex: Number(delivery) }
}

/** Giỏ tệp của MỘT dòng hàng, đổi về khóa theo chỉ số lần giao. */
export function pendingFilesOfLine(
  files: PendingDeliveryFiles,
  lineIndex: number,
): Record<number, File[]> {
  const result: Record<number, File[]> = {}
  for (const [key, value] of Object.entries(files)) {
    const parsed = parseDeliveryFileKey(key)
    if (parsed.lineIndex === lineIndex) result[parsed.deliveryIndex] = value
  }
  return result
}

/** Đặt giỏ tệp cho một lần giao; giỏ rỗng thì bỏ hẳn khóa cho gọn. */
export function setPendingDeliveryFiles(
  files: PendingDeliveryFiles,
  lineIndex: number,
  deliveryIndex: number,
  next: File[],
): PendingDeliveryFiles {
  const result = { ...files }
  const key = deliveryFileKey(lineIndex, deliveryIndex)
  if (next.length) result[key] = next
  else delete result[key]
  return result
}

/** Xóa lần giao thứ `removed` của dòng `lineIndex`: các lần giao sau lùi một bậc. */
export function shiftPendingAfterDeliveryRemove(
  files: PendingDeliveryFiles,
  lineIndex: number,
  removed: number,
): PendingDeliveryFiles {
  const result: PendingDeliveryFiles = {}
  for (const [key, value] of Object.entries(files)) {
    const parsed = parseDeliveryFileKey(key)
    if (parsed.lineIndex !== lineIndex) {
      result[key] = value
      continue
    }
    if (parsed.deliveryIndex === removed) continue
    const next =
      parsed.deliveryIndex > removed ? parsed.deliveryIndex - 1 : parsed.deliveryIndex
    result[deliveryFileKey(lineIndex, next)] = value
  }
  return result
}

/** Xóa dòng hàng thứ `removed`: giỏ của nó mất, các dòng sau lùi một bậc. */
export function shiftPendingAfterLineRemove(
  files: PendingDeliveryFiles,
  removed: number,
): PendingDeliveryFiles {
  const result: PendingDeliveryFiles = {}
  for (const [key, value] of Object.entries(files)) {
    const { lineIndex, deliveryIndex } = parseDeliveryFileKey(key)
    if (lineIndex === removed) continue
    result[deliveryFileKey(lineIndex > removed ? lineIndex - 1 : lineIndex, deliveryIndex)] =
      value
  }
  return result
}

/**
 * Nhân bản dòng hàng thứ `inserted`: bản sao chèn ngay SAU bản gốc nên mọi dòng
 * phía sau tiến một bậc. Bản sao KHÔNG thừa hưởng tệp của bản gốc — nó cũng đã
 * bỏ sạch các lần giao rồi.
 */
export function shiftPendingAfterLineInsert(
  files: PendingDeliveryFiles,
  inserted: number,
): PendingDeliveryFiles {
  const result: PendingDeliveryFiles = {}
  for (const [key, value] of Object.entries(files)) {
    const { lineIndex, deliveryIndex } = parseDeliveryFileKey(key)
    result[deliveryFileKey(lineIndex > inserted ? lineIndex + 1 : lineIndex, deliveryIndex)] =
      value
  }
  return result
}
