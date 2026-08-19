/**
 * Hình của DÒNG CHƯA LƯU trên phiếu Yêu cầu báo giá.
 *
 * Dòng chưa lưu thì chưa có id để gắn tệp vào, nên trang giữ hộ tệp trong bộ nhớ
 * và gom theo **chỉ số dòng**, lưu xong mới tải lên. Hệ quả: xóa hay nhân bản một
 * dòng là mọi dòng phía sau đổi chỉ số — không dời khóa theo thì hình của dòng
 * này nhảy sang dòng khác, mà tới lúc phát hiện thì đã tải nhầm lên server rồi.
 */
export type PendingLineFiles = Record<number, File[]>

/** Xóa dòng thứ `removed`: bỏ giỏ của nó, mọi khóa lớn hơn lùi một bậc. */
export function shiftPendingAfterRemove(
  files: PendingLineFiles,
  removed: number,
): PendingLineFiles {
  const next: PendingLineFiles = {}
  for (const [key, value] of Object.entries(files)) {
    const index = Number(key)
    if (index === removed) continue
    next[index > removed ? index - 1 : index] = value
  }
  return next
}

/**
 * Nhân bản dòng thứ `inserted`: bản sao chèn ngay SAU bản gốc nên mọi khóa lớn
 * hơn tiến một bậc. Bản sao KHÔNG thừa hưởng hình của bản gốc — đúng như bảng
 * dòng đã bỏ `id`/`assignee` khi nhân bản, tệp cũng phải chọn lại.
 */
export function shiftPendingAfterInsert(
  files: PendingLineFiles,
  inserted: number,
): PendingLineFiles {
  const next: PendingLineFiles = {}
  for (const [key, value] of Object.entries(files)) {
    const index = Number(key)
    next[index > inserted ? index + 1 : index] = value
  }
  return next
}
