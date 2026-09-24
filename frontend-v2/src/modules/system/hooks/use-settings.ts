import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { auditLogApi } from '../api/audit-log-api'
import { settingApi } from '../api/setting-api'
import type { SettingPayload } from '../types/setting'

/** Số lần cập nhật gần nhất bày ở thẻ «Lịch sử thay đổi» của màn Cấu hình. */
export const SETTING_HISTORY_LIMIT = 30

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
      //  Lần lưu vừa rồi đẻ ra một dòng nhật ký — thẻ «Lịch sử thay đổi» ngay
      //  trong màn này phải thấy nó, không thì người dùng bấm Lưu xong mở tab
      //  lịch sử ra và tưởng thao tác của mình không được ghi lại.
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.settingHistory() })
    },
  })
}

/**
 * Nhật ký thay đổi của chính màn Cấu hình (bao-CR-462).
 *
 * Đọc `tab_audit_log` qua `entity=setting` chứ KHÔNG đọc `tab_change_log`: quyển
 * sổ trước/sau ở mức cột kia chưa có đường API nào để đọc, nó dành cho người đi
 * tra sự cố. Dòng ở đây là thứ backend đã viết sẵn thành câu cho người vừa bấm Lưu.
 */
export function useSettingHistory() {
  return useQuery({
    queryKey: queryKeys.system.settingHistory(),
    queryFn: () => auditLogApi.listRecent('setting', SETTING_HISTORY_LIMIT),
  })
}

/**
 * Số bài HDSD + FAQ đã vào kho vector của Trợ lý AI (bao-CR-451).
 *
 * `enabled` do người gọi truyền vào: thẻ này chỉ dựng cho người có `help_article.write`,
 * mà backend cũng đòi đúng quyền đó — gọi khi chưa đủ quyền thì người dùng ăn toast 403
 * ngay lúc mở tab.
 *
 * KHÔNG tự nạp lại theo chu kỳ: mỗi lần gọi là một lượt quét kho vector, mà con số chỉ
 * đổi khi có người seed bài hoặc bấm nạp. Bấm xong thì `invalidate` là đủ — nhưng nhớ là
 * worker chạy nền, bấm xong hỏi ngay vẫn ra số cũ.
 */
export function useRagIndexStatus(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.system.ragIndexStatus(),
    queryFn: () => settingApi.ragIndexStatus(),
    enabled,
    staleTime: 60_000,
  })
}
