/**
 * id CỦA CÁC DÒNG LÁ chèn thêm vào cây thư mục khi mở một thư mục — văn bản
 * trực tiếp, dòng «(trống)», dòng «đang tải…», dòng «Xem thêm n văn bản…»
 * (yêu cầu giao diện kiểu VS Code, 23/09/2026, §4). Thư mục THẬT luôn mang id
 * SỐ (khóa `tab_doc_folder.id`) — bốn loại dòng lá này cố ý dùng id CHUỖI để
 * không bao giờ trùng, và để `folder-tree-panel.tsx` phân biệt "dòng thư mục
 * thật" khỏi "dòng lá chèn thêm" chỉ bằng `typeof id`.
 *
 * Mã hóa CẢ folderId vào id lá tài liệu (`doc:<folderId>:<documentId>`) thay
 * vì tra một map riêng: cùng một văn bản có thể hiện dưới HAI thư mục khác
 * nhau nếu cả hai đang mở cùng lúc (văn bản gắn nhiều thư mục) — không mã hóa
 * folderId thì hai dòng đó trùng id, React cảnh báo key trùng và tree chỉ vẽ
 * một trong hai (giống bài học "dedupe theo link_id" của `/attachments/chain`).
 */
const DOC_PREFIX = 'doc:'
const EMPTY_PREFIX = 'empty:'
const LOADING_PREFIX = 'loading:'
const MORE_PREFIX = 'more:'

export function makeDocumentLeafId(folderId: number, documentId: number): string {
  return `${DOC_PREFIX}${folderId}:${documentId}`
}

export function makeEmptyLeafId(folderId: number): string {
  return `${EMPTY_PREFIX}${folderId}`
}

export function makeLoadingLeafId(folderId: number): string {
  return `${LOADING_PREFIX}${folderId}`
}

export function makeMoreLeafId(folderId: number): string {
  return `${MORE_PREFIX}${folderId}`
}

/** Tách lại `(folderId, documentId)` từ id lá văn bản — `null` nếu không đúng khuôn. */
export function parseDocumentLeafId(id: string | number): { folderId: number; documentId: number } | null {
  if (typeof id !== 'string' || !id.startsWith(DOC_PREFIX)) return null
  const [folderPart, documentPart] = id.slice(DOC_PREFIX.length).split(':')
  const folderId = Number(folderPart)
  const documentId = Number(documentPart)
  if (!Number.isInteger(folderId) || !Number.isInteger(documentId) || folderId <= 0 || documentId <= 0) {
    return null
  }
  return { folderId, documentId }
}
