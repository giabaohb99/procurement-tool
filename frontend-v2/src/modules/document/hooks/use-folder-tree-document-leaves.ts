import { useQueries } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { documentApi } from '../api/document-api'
import type { DocumentRecord } from '../types/document-record'

/** Trần dòng lá văn bản NẠP MỘT LƯỢT dưới một thư mục — vượt trần thì dòng lá
 * cuối «Xem thêm n văn bản…» chọn thư mục đó ở khung nội dung thay vì tải
 * thêm ngay trong cây (yêu cầu giao diện kiểu VS Code, §4). */
export const FOLDER_LEAF_DOCUMENT_PAGE_SIZE = 100

export interface FolderDocumentLeavesState {
  documents: DocumentRecord[]
  total: number
  isLoading: boolean
}

/**
 * Nạp LƯỜI văn bản TRỰC TIẾP (không gồm nhánh con) của TỪNG thư mục ĐANG MỞ
 * trên cây — mỗi thư mục mở là một truy vấn riêng qua `useQueries` (số lượng
 * đổi ĐỘNG theo tập mở, khác `useQuery` không gọi được trong vòng lặp).
 *
 * Không tự lọc trùng `expandedFolderIds` — nơi gọi (`folder-tree-panel.tsx`)
 * đã đi qua `Set` nên không trùng; hàm này chỉ lo phần nạp dữ liệu.
 */
export function useFolderTreeDocumentLeaves(
  expandedFolderIds: number[],
): Map<number, FolderDocumentLeavesState> {
  const results = useQueries({
    queries: expandedFolderIds.map((folderId) => {
      const params = {
        folder_id: folderId,
        include_subfolders: false,
        page: 1,
        page_size: FOLDER_LEAF_DOCUMENT_PAGE_SIZE,
        sort: 'title',
      }
      return {
        queryKey: queryKeys.document.records(params),
        queryFn: () => documentApi.list(params),
      }
    }),
  })

  const map = new Map<number, FolderDocumentLeavesState>()
  expandedFolderIds.forEach((folderId, index) => {
    const result = results[index]
    map.set(folderId, {
      documents: result?.data?.items ?? [],
      total: result?.data?.total ?? 0,
      isLoading: result?.isLoading ?? false,
    })
  })
  return map
}
