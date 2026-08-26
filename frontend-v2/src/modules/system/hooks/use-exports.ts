import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'

import { exportApi, type ExportListParams } from '../api/export-api'
import type { ExportFormat } from '../config/export-meta'

export function useExports(params: ExportListParams) {
  return useQuery({
    queryKey: queryKeys.system.exports(params as Record<string, unknown>),
    queryFn: () => exportApi.list(params),
  })
}

/** Các bảng người dùng được phép xuất (đổ vào ô chọn hộp thoại). */
export function useExportEntities() {
  return useQuery({
    queryKey: queryKeys.system.exportEntities(),
    queryFn: () => exportApi.entities(),
  })
}

export function useExportDetail(id: number) {
  return useQuery({
    queryKey: queryKeys.system.exportDetail(id),
    queryFn: () => exportApi.get(id),
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function useDownloadExportFile() {
  return useMutation({
    mutationFn: ({ id, filename }: { id: number; filename: string }) =>
      exportApi.downloadFile(id, filename),
    onError: (err) => toast.error(extractErrorMessage(err)),
  })
}

export function useRunExport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ entity, format, filename }: { entity: string; format: ExportFormat; filename: string }) =>
      exportApi.run(entity, format, filename),
    onSuccess: () => {
      toast.success('Đã xuất dữ liệu')
      // Nhật ký vừa có thêm dòng mới → làm mới danh sách.
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.exports() })
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  })
}
