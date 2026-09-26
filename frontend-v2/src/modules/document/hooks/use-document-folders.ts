import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { documentFolderApi } from '../api/document-folder-api'
import { FOLDER_STATUS } from '../types/document-folder'
import type {
  DocumentFolderSetInput,
  FolderCreateInput,
  FolderLinkDocumentsInput,
  FolderReorderItem,
  FolderUnlinkDocumentsInput,
  FolderUpdateInput,
} from '../types/document-folder'

/**
 * CÂY THƯ MỤC VĂN BẢN — đọc/ghi qua `/api/doc-folders` (phase 03/04, duoc-CR-475).
 *
 * Mọi mutation ở đây dọn `folderTreeAll` (cả hai biến thể `include_archived`)
 * và `document.all` — đổi thư mục kéo theo đổi `folders[]`/`primary_folder_path`
 * hiển thị trên bảng/chi tiết văn bản, cùng luật invalidate rộng mà
 * `use-documents.ts` đang dùng cho mọi thao tác ghi khác của phân hệ.
 */

function useInvalidateFolders() {
  const queryClient = useQueryClient()
  return (folderId?: number) => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderTreeAll })
    if (folderId) {
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderDetail(folderId) })
    }
    //  `folders[]`/`primary_folder_path` của văn bản đổi theo thư mục — cùng
    //  phạm vi invalidate rộng mà mọi mutation khác của `document` đang dùng.
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
  }
}

/**
 * `enabled` (phase 06, duoc-CR-476): `document-main-info-fields.tsx` cần danh
 * sách đầy đủ để khớp thư mục mặc định của loại + gỡ thư mục sai pháp nhân,
 * nhưng CHỈ ở màn tạo văn bản (`folderPicker` được truyền) — mặc định `true`
 * để mọi nơi gọi cũ (không truyền tham số này) giữ nguyên hành vi.
 */
export function useDocFolderTree(includeArchived = false, enabled = true) {
  return useQuery({
    queryKey: queryKeys.document.folderTree(includeArchived),
    queryFn: () => documentFolderApi.tree(includeArchived),
    enabled,
  })
}

/**
 * Tìm thư mục theo tên — chỉ hỏi backend khi đã gõ ít nhất 1 ký tự (đã trim).
 *
 * `enabled` (rà soát 23/09/2026, mục H4): mặc định `true` để mọi nơi gọi cũ
 * (không truyền tham số này) giữ nguyên hành vi — nơi nào thiếu
 * `doc_folder.read` thì truyền `false` để tắt hẳn cuộc gọi `/api/doc-folders/search`
 * thay vì chỉ ẩn kết quả trên giao diện.
 */
export function useDocFolderSearch(q: string, enabled = true) {
  //  Hoãn 250ms (26/09/2026): trước đây mỗi ký tự là một request, mà mỗi
  //  request backend tính lại quyền trên TOÀN BỘ cây — gõ «hợp đồng» = 8 lượt.
  const keyword = useDebouncedValue(q.trim(), 250)
  return useQuery({
    queryKey: queryKeys.document.folderSearch(keyword),
    queryFn: () => documentFolderApi.search(keyword),
    enabled: enabled && keyword.length >= 1,
    //  Gõ lùi về từ khóa cũ thì lấy lại từ bộ nhớ, không hỏi lại backend.
    staleTime: 30_000,
  })
}

export function useDocFolder(id?: number) {
  return useQuery({
    queryKey: queryKeys.document.folderDetail(id ?? 0),
    queryFn: () => documentFolderApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useCreateDocFolder() {
  const invalidate = useInvalidateFolders()
  return useMutation({
    mutationFn: (payload: FolderCreateInput) => documentFolderApi.create(payload),
    onSuccess: (folder) => {
      toast.success('Đã tạo thư mục')
      //  Cha vừa nhận thêm một con — dọn luôn chi tiết của cha để số đếm/breadcrumb đúng.
      invalidate(folder.parent_id || folder.id)
    },
  })
}

export function useUpdateDocFolder() {
  const invalidate = useInvalidateFolders()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: FolderUpdateInput }) =>
      documentFolderApi.update(id, payload),
    onSuccess: (folder) => {
      toast.success('Đã cập nhật thư mục')
      invalidate(folder.id)
    },
  })
}

/**
 * Ngừng dùng một thư mục (kéo cả nhánh con). Khôi phục dùng lại
 * `useUpdateDocFolder` với `status: FOLDER_STATUS.active` — khôi phục chỉ đúng
 * thư mục đó, không tự bật lại con (đúng luật backend), nên không cần một mutation riêng.
 */
export function useArchiveDocFolder() {
  const invalidate = useInvalidateFolders()
  return useMutation({
    mutationFn: (id: number) => documentFolderApi.update(id, { status: FOLDER_STATUS.archived }),
    onSuccess: (folder) => {
      toast.success('Đã ngừng dùng thư mục')
      invalidate(folder.id)
    },
  })
}

export function useMoveDocFolder() {
  const invalidate = useInvalidateFolders()
  return useMutation({
    mutationFn: ({ id, newParentId }: { id: number; newParentId: number }) =>
      documentFolderApi.move(id, newParentId),
    onSuccess: (folder) => {
      toast.success('Đã chuyển thư mục')
      invalidate(folder.id)
    },
  })
}

export function useReorderDocFolders() {
  const invalidate = useInvalidateFolders()
  return useMutation({
    mutationFn: (items: FolderReorderItem[]) => documentFolderApi.reorder(items),
    onSuccess: () => {
      invalidate()
    },
  })
}

/** Số văn bản sẽ bị ảnh hưởng nếu xóa thư mục — chỉ gọi khi hộp xác nhận đang mở. */
export function useFolderDeletePreview(folderId: number | null) {
  return useQuery({
    queryKey: queryKeys.document.folderDeletePreview(folderId ?? 0),
    queryFn: () => documentFolderApi.deletePreview(folderId as number),
    enabled: folderId != null && folderId > 0,
    //  Số đếm phải đúng TẠI LÚC mở hộp — không dùng lại số của lần mở trước.
    staleTime: 0,
  })
}

export function useDeleteDocFolder() {
  const invalidate = useInvalidateFolders()
  return useMutation({
    mutationFn: (input: number | { id: number; moveTo?: number }) =>
      typeof input === 'number'
        ? documentFolderApi.remove(input)
        : documentFolderApi.remove(input.id, input.moveTo),
    onSuccess: () => {
      toast.success('Đã xóa thư mục')
      invalidate()
    },
  })
}

/** Gắn HÀNG LOẠT văn bản vào một thư mục (màn Quản lý cây thư mục). */
export function useLinkDocumentsToFolder() {
  const invalidate = useInvalidateFolders()
  return useMutation({
    mutationFn: (payload: FolderLinkDocumentsInput) => documentFolderApi.linkDocuments(payload),
    onSuccess: (result, variables) => {
      if (result.denied.length > 0) {
        toast.warning(`Đã gắn ${result.moved.length} văn bản, ${result.denied.length} văn bản bị từ chối`)
      } else {
        toast.success('Đã gắn văn bản vào thư mục')
      }
      invalidate(variables.folder_id)
    },
  })
}

export function useUnlinkDocumentsFromFolder() {
  const invalidate = useInvalidateFolders()
  return useMutation({
    mutationFn: (payload: FolderUnlinkDocumentsInput) => documentFolderApi.unlinkDocuments(payload),
    onSuccess: (result, variables) => {
      if (result.denied.length > 0) {
        toast.warning(`Đã gỡ ${result.moved.length} văn bản, ${result.denied.length} văn bản bị từ chối`)
      } else {
        toast.success('Đã gỡ văn bản khỏi thư mục')
      }
      invalidate(variables.folder_id)
    },
  })
}

/** Đặt lại TOÀN BỘ thư mục của MỘT văn bản — màn tạo/sửa văn bản dùng cửa này. */
export function useSetDocumentFolders(documentId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: DocumentFolderSetInput) =>
      documentFolderApi.setDocumentFolders(documentId, payload),
    onSuccess: () => {
      toast.success('Đã cập nhật thư mục')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.folderTreeAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}
