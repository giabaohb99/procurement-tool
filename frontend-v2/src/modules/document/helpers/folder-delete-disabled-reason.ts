import { FOLDER_ACCESS_LEVEL, FOLDER_KIND } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'

/**
 * Vì sao mục «Xóa» của MỘT THƯ MỤC bị khóa — `null` = xóa được (chưa tính
 * điều kiện "phải RỖNG", backend tự chặn và trả lỗi rõ nếu còn thư mục
 * con/văn bản — lỗi đó tự nổi thành toast qua `http-client.ts`, không cần
 * đoán trước ở đây).
 *
 * ⚠️ Thư mục PHÁP NHÂN và thư mục nhóm «Công ty» KHÔNG xóa được (đại ca chốt
 * 24/09/2026, ĐẢO quyết định cho xóa gốc pháp nhân trước đó cùng ngày) —
 * backend cũng chặn (`folder_service.delete_folder`). Mục «Xóa» vẫn HIỆN, chỉ
 * KHÓA kèm lý do đọc được — giấu hẳn thì người dùng tưởng tính năng biến mất.
 */
export function folderDeleteDisabledReason(
  folder: Pick<DocFolderTreeNode, 'my_level'> & Partial<Pick<DocFolderTreeNode, 'kind'>>,
): string | null {
  if (folder.kind === FOLDER_KIND.company || folder.kind === FOLDER_KIND.companyGroup) {
    return 'Thư mục công ty do hệ thống quản lý, không xóa được'
  }
  if (folder.my_level < FOLDER_ACCESS_LEVEL.manage) return 'Cần quyền Quản lý'
  return null
}
