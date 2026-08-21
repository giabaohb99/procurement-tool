import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { backupApi } from '../api/backup-api'

export function useBackups(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.system.backups(params as Record<string, unknown>),
    queryFn: () => backupApi.list(params),
    refetchInterval: (query) => {
      const items = query.state.data?.items
      const isRunning = items?.some((r) => r.status === 'running')
      return isRunning ? 3000 : false
    },
  })
}

export function useRunBackup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => backupApi.runNow(),
    onSuccess: () => {
      toast.success('Đã bắt đầu sao lưu CSDL. Đang xử lý...')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
  })
}

export function useDownloadBackup() {
  return useMutation({
    mutationFn: (id: number) => backupApi.download(id),
    onSuccess: (res) => {
      if (res?.url) {
        window.open(res.url, '_blank')
      } else {
        toast.error('Không thể tạo liên kết tải bản sao lưu')
      }
    },
  })
}

export function useDeleteBackup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => backupApi.deleteBackup(id),
    onSuccess: () => {
      toast.success('Đã xóa bản sao lưu CSDL')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
  })
}
