import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { documentFolderApi } from '../api/document-folder-api'
import type {
  FolderAccessBulkGrantInput,
  FolderAccessGrantInput,
  FolderAccessLevelPatchInput,
} from '../types/document-folder'

/**
 * QUYỀN TRÊN THƯ MỤC — `GET/POST /api/doc-folders/{id}/access`,
 * `DELETE .../access/{access_id}` (phase 04, duoc-CR-475). Cần mức Quản lý
 * trên thư mục để gọi cả ba route — backend đã gác, ở đây chỉ ẩn/hiện nút bằng
 * `my_level` đọc từ `useDocFolder`.
 *
 * Cả grant/revoke đều dọn `folderAccess` (danh sách trực tiếp) LẪN
 * `folderDetail` (vì `effective_access` lồng trong chi tiết cũng đổi theo).
 */

/** Chỉ dòng ACL TRỰC TIẾP trên thư mục này — không kèm kế thừa từ tổ tiên. */
export function useFolderAccessList(folderId?: number) {
  return useQuery({
    queryKey: queryKeys.document.folderAccess(folderId ?? 0),
    queryFn: () => documentFolderApi.listAccess(folderId as number),
    enabled: typeof folderId === 'number' && folderId > 0,
  })
}

export function useGrantFolderAccess(folderId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: FolderAccessGrantInput) => documentFolderApi.grantAccess(folderId, payload),
    onSuccess: () => {
      toast.success('Đã cấp quyền')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderAccess(folderId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderDetail(folderId) })
    },
  })
}

/**
 * Hộp «Chia sẻ» kiểu Drive — cấp CÙNG một mức cho CẢ danh sách chủ thể trong
 * một lượt (phase 10B). Kết quả `{created, updated, skipped}`: báo `skipped`
 * qua toast riêng vì đó là phần backend ÂM THẦM bỏ qua (chủ thể không tồn
 * tại) — im lặng thì người chia tưởng đã cấp cho cả danh sách.
 */
export function useGrantFolderAccessBulk(folderId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: FolderAccessBulkGrantInput) =>
      documentFolderApi.grantAccessBulk(folderId, payload),
    onSuccess: (result) => {
      if (result.skipped.length > 0) {
        toast.warning(
          `Đã cấp quyền cho ${result.created + result.updated}, bỏ qua ${result.skipped.length} ` +
            'đối tượng không tìm thấy',
        )
      } else {
        toast.success(`Đã cấp quyền cho ${result.created + result.updated} đối tượng`)
      }
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderAccess(folderId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderDetail(folderId) })
    },
  })
}

/** Đổi MỨC tại chỗ — menu thả xuống trên dòng «Người có quyền» của hộp «Chia sẻ». */
export function useUpdateFolderAccessLevel(folderId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ accessId, level }: { accessId: number; level: number }) =>
      documentFolderApi.updateAccessLevel(folderId, accessId, { level } as FolderAccessLevelPatchInput),
    onSuccess: () => {
      toast.success('Đã đổi mức quyền')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderAccess(folderId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderDetail(folderId) })
    },
  })
}

/** Thu hồi = đánh dấu; dòng vẫn ở lại kèm mốc + lý do, không xóa hẳn. */
export function useRevokeFolderAccess(folderId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ accessId, reason }: { accessId: number; reason: string }) =>
      documentFolderApi.revokeAccess(folderId, accessId, reason),
    onSuccess: () => {
      toast.success('Đã thu hồi quyền')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderAccess(folderId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderDetail(folderId) })
    },
  })
}
