import { FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'

/**
 * Câu «để trống thì vào đâu» ở ô «Lưu vào thư mục» (phase 06, duoc-CR-476).
 *
 * Người dùng không chọn thư mục nào KHÔNG có nghĩa văn bản mất tích — nó tự
 * vào thư mục MẶC ĐỊNH của loại văn bản (nếu loại có khai, còn thuộc đúng
 * pháp nhân đang chọn, và còn đang dùng), nếu không thì vào thư mục MANG TÊN
 * PHÁP NHÂN của văn bản. Đây là chính luật `folder_link_service.resolve_default`
 * ở backend — hàm này chỉ DỰNG CÂU, không tự suy luật khác đi.
 *
 * `folders` truyền vào là danh sách PHẲNG từ `GET /api/doc-folders/tree` —
 * hàm không tự lọc theo `my_level`: tên thư mục mặc định vẫn cần hiện ra dù
 * người soạn không đủ mức Đóng góp để TỰ CHỌN nó trong ô tìm (khác lỗi, đây
 * là văn bản vẫn nằm đúng chỗ, chỉ là người này không được liệt kê nó ra để bấm).
 */
export function defaultFolderHint(
  folders: readonly DocFolderTreeNode[],
  companyId: number,
  docTypeDefaultFolderId: number | null | undefined,
): string | null {
  if (!companyId) return null

  const byId = new Map(folders.map((folder) => [folder.id, folder] as const))
  const declared = docTypeDefaultFolderId ? byId.get(docTypeDefaultFolderId) : undefined
  const declaredValid =
    declared &&
    declared.company_id === companyId &&
    declared.status === FOLDER_STATUS.active
      ? declared
      : undefined

  const companyRoot = folders.find(
    (folder) => folder.kind === FOLDER_KIND.company && folder.company_id === companyId,
  )
  const target = declaredValid ?? companyRoot
  if (!target) return null

  return `Không chọn → văn bản sẽ vào thư mục "${target.name}".`
}
