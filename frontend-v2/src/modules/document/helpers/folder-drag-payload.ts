/**
 * HỢP ĐỒNG KÉO THẢ giữa khung TRÁI (cây, phase 10A) và khung PHẢI (nội dung
 * thư mục, phase 10B) — cả hai bên đọc/ghi qua ĐÚNG một hằng số + hai hàm ở
 * đây, không tự chế `dataTransfer.setData(...)` rải rác (xem
 * `phase-10-giao-dien-kieu-drive-va-vscode.md` §"Hợp đồng kéo thả").
 *
 * `sourceFolderId = null` khi kéo từ một nơi KHÔNG gắn với một thư mục cụ thể
 * (vd kết quả tìm toàn văn gộp nhiều thư mục) — bên nhận khi đó chỉ THÊM vào
 * thư mục đích, không có "thư mục nguồn" nào để gỡ khỏi lúc giữ Alt/Option.
 */
export const FOLDER_DRAG_MIME = 'application/x-doc-folder-items'

export interface FolderDragPayload {
  documentIds: number[]
  folderIds: number[]
  sourceFolderId: number | null
}

/** Mảng số nguyên DƯƠNG — chặn `NaN`/số thực/chuỗi lẫn vào lúc đọc lại JSON không kiểm soát được nguồn. */
function isPositiveIntArray(value: unknown): value is number[] {
  return (
    Array.isArray(value) &&
    value.every((item) => typeof item === 'number' && Number.isInteger(item) && item > 0)
  )
}

/** `sourceFolderId` — số nguyên dương, hoặc `null` (không gắn thư mục nguồn). Không nhận `undefined`/số 0. */
function isValidSourceFolderId(value: unknown): value is number | null {
  return value === null || (typeof value === 'number' && Number.isInteger(value) && value > 0)
}

function isFolderDragPayload(value: unknown): value is FolderDragPayload {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Record<string, unknown>
  return (
    isPositiveIntArray(candidate.documentIds) &&
    isPositiveIntArray(candidate.folderIds) &&
    isValidSourceFolderId(candidate.sourceFolderId)
  )
}

/**
 * Ghi payload lúc BẮT ĐẦU kéo (`onDragStart`). Dùng `'move'`/`'copy'` tùy nơi
 * gọi qua `dataTransfer.effectAllowed` riêng — hàm này chỉ lo phần dữ liệu.
 */
export function writeFolderDragPayload(dataTransfer: DataTransfer, payload: FolderDragPayload): void {
  dataTransfer.setData(FOLDER_DRAG_MIME, JSON.stringify(payload))
}

/**
 * Đọc payload lúc THẢ (`onDrop`) — `null` nếu thiếu, hỏng JSON, hoặc sai hình
 * dạng (khóa lạ trộn vào, số không phải số nguyên dương…). Bên nhận PHẢI kiểm
 * `null` trước khi dùng, không giả định payload luôn hợp lệ chỉ vì đúng MIME.
 *
 * ⚠️ Hầu hết trình duyệt chỉ trả dữ liệu THẬT ở sự kiện `drop` — lúc
 * `dragover` gọi `getData` thường ra chuỗi rỗng (giới hạn bảo mật của
 * `dataTransfer`, khác Firefox). Muốn biết CÓ payload hay không trong lúc kéo
 * qua (để tô trạng thái hợp lệ/không hợp lệ) thì dùng {@link hasFolderDragPayload}.
 */
export function readFolderDragPayload(dataTransfer: DataTransfer): FolderDragPayload | null {
  const raw = dataTransfer.getData(FOLDER_DRAG_MIME)
  if (!raw) return null
  try {
    const parsed: unknown = JSON.parse(raw)
    return isFolderDragPayload(parsed) ? parsed : null
  } catch {
    return null
  }
}

/**
 * Đang kéo một payload thư mục/văn bản hay không — dùng ở `onDragEnter`/
 * `onDragOver` để quyết định có tô "vùng nhận thả" hay không, KHÔNG đọc được
 * nội dung thật (xem ghi chú ở {@link readFolderDragPayload}). Đọc
 * `dataTransfer.types`, luôn có sẵn ở mọi nhịp của một lượt kéo native.
 */
export function hasFolderDragPayload(dataTransfer: DataTransfer): boolean {
  return Array.from(dataTransfer.types).includes(FOLDER_DRAG_MIME)
}
