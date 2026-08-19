import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { settingApi } from '../api/setting-api'
import type { SettingPayload } from '../types/setting'

/**
 * Đọc cấu hình hệ thống.
 *
 * `staleTime: Infinity` vì đây là màn một người sửa: dữ liệu chỉ đổi khi chính
 * người đang mở bấm Lưu. Tự nạp lại giữa chừng sẽ đè lên những ô họ vừa gõ dở.
 */
export function useSettings() {
  return useQuery({
    queryKey: queryKeys.system.settings(),
    queryFn: () => settingApi.get(),
    staleTime: Infinity,
  })
}

export function useSaveSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (values: Record<string, unknown>) => settingApi.save(values),
    // Backend trả lại nguyên trạng thái sau khi lưu — ghi thẳng vào cache thay
    // vì invalidate rồi gọi lại một vòng nữa.
    onSuccess: (data: SettingPayload) => {
      queryClient.setQueryData(queryKeys.system.settings(), data)
    },
  })
}
