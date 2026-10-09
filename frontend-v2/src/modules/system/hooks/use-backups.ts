import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { backupApi } from '../api/backup-api'
import type { BackupTarget } from '../types/backup'

export function useBackups(params: ListParams, target: BackupTarget = 'erp') {
  return useQuery({
    queryKey: queryKeys.system.backups({ ...params, target } as Record<string, unknown>),
    queryFn: () => backupApi.list(params, target),
    refetchInterval: (query) => {
      const items = query.state.data?.items
      const isRunning = items?.some((r) => r.status === 'running')
      return isRunning ? 3000 : false
    },
  })
}

export function useRunBackup(target: BackupTarget = 'erp') {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => backupApi.runNow(target),
    onSuccess: () => {
      toast.success(target === 'agent' ? 'Đã bắt đầu sao lưu DB bot. Đang xử lý...' : 'Đã bắt đầu sao lưu CSDL. Đang xử lý...')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
  })
}

/** ai-CR-139: khôi phục THỬ DB bot (nạp vào DB tạm, kiểm, xóa) — không đụng DB đang chạy. */
export function useRestoreTest() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => backupApi.restoreTest(),
    onSuccess: () => {
      toast.success('Đã bắt đầu khôi phục thử. Kết quả hiện trong danh sách sau ít phút.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
  })
}

export function useDownloadBackup(target: BackupTarget = 'erp') {
  return useMutation({
    mutationFn: (id: number) => backupApi.download(id, target),
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
