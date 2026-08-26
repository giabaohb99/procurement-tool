import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'

import {
  importApi,
  type ImportListParams,
  type ImportLogParams,
  type UploadImportPayload,
} from '../api/import-api'
import { isImportRunning } from '../config/import-meta'

/** Danh sách batch import — tự làm mới mỗi 4s khi còn batch đang chạy. */
export function useImports(params: ImportListParams) {
  return useQuery({
    queryKey: queryKeys.system.imports(params as Record<string, unknown>),
    queryFn: () => importApi.list(params),
    refetchInterval: (query) => {
      const running = query.state.data?.items?.some((b) => isImportRunning(b.status))
      return running ? 4000 : false
    },
  })
}

/** Chi tiết một batch — auto-poll khi batch còn Chờ/Đang chạy. */
export function useImportBatch(id: number) {
  return useQuery({
    queryKey: queryKeys.system.importDetail(id),
    queryFn: () => importApi.get(id),
    enabled: Number.isFinite(id) && id > 0,
    refetchInterval: (query) => (query.state.data && isImportRunning(query.state.data.status) ? 4000 : false),
  })
}

export function useImportLogs(id: number, params: ImportLogParams) {
  return useQuery({
    queryKey: queryKeys.system.importLogs(id, params as Record<string, unknown>),
    queryFn: () => importApi.logs(id, params),
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function useUploadImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: UploadImportPayload) => importApi.upload(payload),
    onSuccess: () => {
      toast.success('Đã nhận file — đang import nền, hệ thống sẽ báo khi xong')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
    // Lỗi (vd sai file cho bảng) hiển thị NGAY trong hộp thoại upload — không toast
    // để tránh lặp; hộp thoại vẫn mở nên người dùng thấy và sửa tại chỗ.
  })
}

export function useRevertImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => importApi.revert(id),
    onSuccess: (batch) => {
      toast.success('Đã hoàn tác lần import')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.importDetail(batch.id) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  })
}

/** Ghi thật từ bản chạy thử — trả batch APPLY mới (chỗ gọi điều hướng sang nó). */
export function useCommitImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => importApi.commit(id),
    onSuccess: () => {
      toast.success('Đang ghi thật dữ liệu — hệ thống sẽ báo khi xong')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  })
}

export function useDownloadImportFile() {
  return useMutation({
    mutationFn: ({ id, filename }: { id: number; filename: string }) =>
      importApi.downloadFile(id, filename),
    onError: (err) => toast.error(extractErrorMessage(err)),
  })
}
