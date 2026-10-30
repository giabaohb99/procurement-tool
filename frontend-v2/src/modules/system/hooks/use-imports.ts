import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
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

/**
 * Chi tiết một batch — auto-poll khi batch còn Chờ/Đang chạy. Khi batch CHUYỂN từ Chờ/Đang chạy sang
 * trạng thái cuối (Xong/Lỗi) thì làm mới luôn nhật ký của nó: worker ghi log lúc kết thúc, trang đã mở
 * từ trước chỉ có danh sách log rỗng cho tới khi người dùng F5.
 */
export function useImportBatch(id: number) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: queryKeys.system.importDetail(id),
    queryFn: () => importApi.get(id),
    enabled: Number.isFinite(id) && id > 0,
    refetchInterval: (q) => (q.state.data && isImportRunning(q.state.data.status) ? 4000 : false),
  })

  const status = query.data?.status
  const prevRunning = useRef<boolean | null>(null)
  //  Đổi sang lô khác: quên trạng thái của lô trước, kẻo "đang chạy → xong" bị suy từ hai lô khác nhau.
  useEffect(() => {
    prevRunning.current = null
  }, [id])
  useEffect(() => {
    if (status === undefined) return
    const running = isImportRunning(status)
    if (prevRunning.current === true && !running) {
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.importLogs(id) })
    }
    prevRunning.current = running
  }, [status, id, queryClient])

  return query
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
    //  Lỗi KHÔNG toast ở đây: `httpClient` đã toast mọi lỗi của POST/PATCH/DELETE — thêm lần nữa là hiện hai lần.
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
    //  Lỗi đã được `httpClient` toast sẵn (POST) — không toast lần hai.
  })
}

export function useDownloadImportFile() {
  return useMutation({
    mutationFn: ({ id, filename }: { id: number; filename: string }) =>
      importApi.downloadFile(id, filename),
    onError: (err) => toast.error(extractErrorMessage(err)),
  })
}
