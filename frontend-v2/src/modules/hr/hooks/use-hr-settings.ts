import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { hrSettingApi } from '../api/hr-setting-api'
import type { SettingsPayloadForHr } from '../types/hr-setting'
import { pickHrSettingFields } from '../utils/hr-setting-values'

/**
 * Đọc Cài đặt nhân sự. Dùng CHUNG khóa đệm với màn Cấu hình hệ thống (`system.settings`) vì cùng một nguồn —
 * lưu ở trang này thì màn kia mở ra thấy ngay, không lệch nhau. `staleTime: Infinity` cùng lý do màn kia: trang một
 * người sửa, tự nạp lại giữa chừng sẽ đè lên ô đang gạt dở.
 */
export function useHrSettings(options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.system.settings(),
    queryFn: () => hrSettingApi.get(),
    staleTime: Infinity,
    enabled: options.enabled ?? true,
    select: (payload: SettingsPayloadForHr) => pickHrSettingFields(payload),
  })
}

export function useSaveHrSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: Record<string, unknown>) => hrSettingApi.save(values),
    onSuccess: (payload) => {
      queryClient.setQueryData(queryKeys.system.settings(), payload)
      //  Lần lưu đẻ một dòng nhật ký ở thẻ «Lịch sử thay đổi» của màn Cấu hình hệ thống.
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.settingHistory() })
    },
  })
}
