import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { aiUsageApi } from '../api/ai-skill-api'
import type { KeyIssueInput, KeyRevokeInput, McpCallFilters, McpSettings, McpSettingsPatch } from '../types/ai-skill'

/** Khóa kết nối AI của nhân sự (K4) + nhật ký lượt gọi (K3) — qua cổng dịch vụ AI. */

export function useKeyAdminMeta() {
  return useQuery({ queryKey: queryKeys.aiSkill.keyAdminMeta(), queryFn: () => aiUsageApi.keyAdminMeta() })
}

export function useKeyAdminKeys(
  params: { department_id?: number; state?: number; user_id?: number; page: number; size: number },
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.aiSkill.keyAdminKeys(params),
    queryFn: () => aiUsageApi.keyAdminKeys(params),
    placeholderData: keepPreviousData,
    enabled,
  })
}

export function useIssueKeys() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: KeyIssueInput) => aiUsageApi.issueKeys(body),
    onSuccess: (result) => {
      //  Câu chốt doc 21 §6.3 — có người bị bỏ qua (đã đủ khóa còn hiệu lực…) thì nói thêm, đừng để quản trị tưởng
      //  ai cũng có khóa mới.
      const skipped = result.skipped.length > 0 ? ` Bỏ qua ${result.skipped.length} người: ${result.skipped
        .slice(0, 3)
        .map((s) => `${s.label} (${s.reason})`)
        .join('; ')}${result.skipped.length > 3 ? '…' : ''}.` : ''
      toast.success(`Đã phát ${result.issued.length} khóa, mỗi người sẽ nhận thông báo để lấy khóa.${skipped}`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.keyAdminKeysAll() })
    },
  })
}

export function useRevokeKeys() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: KeyRevokeInput) => aiUsageApi.revokeKeys(body),
    onSuccess: (result) => {
      toast.success(result.revoked > 0 ? `Đã thu hồi ${result.revoked} khóa.` : 'Không có khóa nào đang hiệu lực để thu hồi.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.keyAdminKeysAll() })
    },
  })
}

export function useMcpCalls(filters: McpCallFilters) {
  return useQuery({
    queryKey: queryKeys.aiSkill.calls({ ...filters }),
    queryFn: () => aiUsageApi.listCalls(filters),
    placeholderData: keepPreviousData,
  })
}

export function useMcpSettings(enabled: boolean) {
  return useQuery({ queryKey: queryKeys.aiSkill.mcpSettings(), queryFn: () => aiUsageApi.settings(), enabled })
}

export function useSaveMcpSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: McpSettingsPatch) => aiUsageApi.saveSettings(body),
    onSuccess: (saved) => {
      //  PUT không trả `can_write` — giữ lại của bản GET, kẻo màn tự chuyển sang chỉ xem ngay sau khi lưu.
      queryClient.setQueryData<McpSettings>(queryKeys.aiSkill.mcpSettings(), (old) => ({
        ...saved,
        can_write: old?.can_write,
      }))
      toast.success('Đã lưu cấu hình. Cổng MCP áp dụng trong vòng 1 phút.')
    },
  })
}

/** bao-CR-635 — ứng dụng AI tự đăng ký OAuth; `enabled` = có `agent_group.read`, thiếu thì không gọi để khỏi ăn 403. */
export function useOAuthClients(enabled: boolean) {
  return useQuery({ queryKey: queryKeys.aiSkill.oauthClients(), queryFn: () => aiUsageApi.oauthClients(), enabled })
}

export function useDeleteOAuthClient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => aiUsageApi.deleteOAuthClient(id),
    onSuccess: (result) => {
      toast.success(
        result.revoked_grants > 0
          ? `Đã xóa ứng dụng, cắt ${result.revoked_grants} kết nối.`
          : 'Đã xóa ứng dụng (không có kết nối nào đang sống).',
      )
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.oauthClients() })
      //  Kết nối OAuth cũng là một dòng khóa ở màn Khóa nhân sự (ai-CR-218) — làm tươi để trạng thái "Đã thu hồi" hiện ngay.
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.keyAdminKeysAll() })
    },
  })
}
