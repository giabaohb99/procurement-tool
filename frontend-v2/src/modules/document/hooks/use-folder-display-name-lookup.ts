import { useCallback, useMemo } from 'react'

import { useDocFolderTree } from './use-document-folders'

/**
 * Tra CHỮ NGẮN (`display_name`) của một thư mục theo id — vài nơi CHỈ nhận
 * được tên PHÁP LÝ (`FolderBreadcrumbItem`/`DocumentFolderRef`, cả hai chỉ có
 * `name`, backend chưa gộp `display_name` vào hai kiểu đó) nhưng vẫn cần hiện
 * chữ ngắn cho khớp phần còn lại của giao diện (chốt dọn gọn lead 24/09/2026
 * tối: breadcrumb + «Thư mục chứa» từng hiện tên HOA đầy đủ của pháp nhân,
 * lệch với tiêu đề/thẻ/dòng đã đổi sang `display_name` từ trước).
 *
 * Tra qua CÂY đã nạp sẵn (`useDocFolderTree`, cùng cache với khung trái —
 * không tốn thêm lượt gọi API nào); không thấy (thư mục ngoài phạm vi cây,
 * hoặc chưa nạp xong) thì RƠI VỀ đúng tên đã có, không hiện rỗng.
 */
export function useFolderDisplayNameLookup(): (id: number, fallbackName: string) => string {
  const { data: allFolders } = useDocFolderTree()
  const displayNameById = useMemo(
    () => new Map((allFolders ?? []).map((folder) => [folder.id, folder.display_name ?? folder.name])),
    [allFolders],
  )
  return useCallback(
    (id: number, fallbackName: string) => displayNameById.get(id) ?? fallbackName,
    [displayNameById],
  )
}
