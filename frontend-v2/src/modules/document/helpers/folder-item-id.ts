/**
 * KHÓA CHỌN dùng chung cho `useItemSelection` trong khung nội dung thư mục —
 * một dòng chọn được có thể là THƯ MỤC hay VĂN BẢN, hai bảng id độc lập
 * (thư mục #5 và văn bản #5 là hai thứ khác nhau), nên gộp lại thành MỘT
 * chuỗi có tiền tố thay vì hai `Set<number>` song song phải đồng bộ tay.
 */
export type FolderItemKind = 'folder' | 'document'

export interface FolderItemId {
  kind: FolderItemKind
  id: number
}

export function folderItemKey(kind: FolderItemKind, id: number): string {
  return `${kind}:${id}`
}

/**
 * `id` DOM của một dòng/thẻ (thư mục hoặc văn bản) trong khung nội dung —
 * dùng để `document.getElementById(...)?.scrollIntoView(...)` cuộn tới đúng
 * dòng khi văn bản được CÂY bên trái chỉ tới (đặc tả §3, duoc-CR-476). Cùng
 * tiền tố `folder-item-` cho cả chế độ Lưới (`folder-grid-document-card.tsx`)
 * lẫn Danh sách (`folder-list-view.tsx`) — một văn bản chỉ có MỘT id DOM dù
 * đang xem ở chế độ nào.
 */
export function folderItemDomId(kind: FolderItemKind, id: number): string {
  return `folder-item-${kind}-${id}`
}

/** `null` nếu chuỗi không đúng khuôn `folder:<n>`/`document:<n>` — không đoán, không nổ. */
export function parseFolderItemKey(key: string): FolderItemId | null {
  const [kind, rawId] = key.split(':', 2)
  if (kind !== 'folder' && kind !== 'document') return null
  const id = Number(rawId)
  if (!Number.isInteger(id) || id <= 0) return null
  return { kind, id }
}

/** Tách một tập khóa hỗn hợp thành hai mảng id THUẦN SỐ — nơi gọi API cần đúng dạng này. */
export function splitFolderItemKeys(keys: Iterable<string>): { folderIds: number[]; documentIds: number[] } {
  const folderIds: number[] = []
  const documentIds: number[] = []
  for (const key of keys) {
    const parsed = parseFolderItemKey(key)
    if (!parsed) continue
    if (parsed.kind === 'folder') folderIds.push(parsed.id)
    else documentIds.push(parsed.id)
  }
  return { folderIds, documentIds }
}
