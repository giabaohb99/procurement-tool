import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { loginSessionApi, type LoginSessionListParams } from '../api/login-session-api'

/** Số ngày lịch sử mặc định — khớp `HISTORY_DAYS_DEFAULT` của backend. */
export const LOGIN_HISTORY_DAYS = 90

/**
 * Phiên đăng nhập toàn hệ (màn Quản trị) hoặc của một người (thẻ hồ sơ nhân sự).
 *
 * `enabled` để thẻ ở hồ sơ nhân sự tự tắt khi thiếu `login_session.read` hoặc
 * nhân sự chưa có tài khoản — mount là gọi thì người dùng ăn toast 403.
 */
export function useLoginSessions(
  params: LoginSessionListParams,
  options: { enabled?: boolean } = {},
) {
  return useQuery({
    queryKey: queryKeys.system.loginSessions(params as Record<string, unknown>),
    queryFn: () => loginSessionApi.list(params),
    placeholderData: keepPreviousData,
    staleTime: 10 * 1000,
    enabled: options.enabled ?? true,
  })
}

export function useLoginHistory(
  userId: number,
  days: number = LOGIN_HISTORY_DAYS,
  options: { enabled?: boolean } = {},
) {
  return useQuery({
    queryKey: queryKeys.system.loginHistory(userId, days),
    queryFn: () => loginSessionApi.history(userId, days),
    enabled: (options.enabled ?? true) && userId > 0,
  })
}

/** Đá MỘT phiên của người khác — cần `login_session.delete`. */
export function useRevokeLoginSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: number) => loginSessionApi.revoke(sessionId),
    onSuccess: () => {
      toast.success('Đã đá phiên khỏi thiết bị. Có hiệu lực trong vòng 1 phút.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
  })
}

/** Bắt một người đăng nhập lại ở mọi thiết bị — cần `login_session.delete`. */
export function useLogoutAllSessions() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: number) => loginSessionApi.logoutAll(userId),
    onSuccess: (data) => {
      toast.success(`Đã đăng xuất ${data?.revoked ?? 0} thiết bị. Có hiệu lực ngay.`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.all })
    },
  })
}

// ── Thiết bị của tôi (/me) — chỉ đòi đăng nhập ─────────────────────────────

export function useMySessions(activeOnly = true) {
  return useQuery({
    queryKey: queryKeys.auth.mySessions(activeOnly),
    queryFn: () => loginSessionApi.mySessions(activeOnly),
    staleTime: 10 * 1000,
  })
}

/** Lịch sử đăng nhập của chính mình — tab «Lịch sử đăng nhập» ở /me (bao-CR-400). */
export function useMyLoginHistory(days: number = LOGIN_HISTORY_DAYS) {
  return useQuery({
    queryKey: queryKeys.auth.myLoginHistory(days),
    queryFn: () => loginSessionApi.myHistory(days),
    staleTime: 30 * 1000,
  })
}

export function useRevokeMySession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: number) => loginSessionApi.revokeMine(sessionId),
    onSuccess: () => {
      toast.success('Đã đăng xuất thiết bị đó. Có hiệu lực trong vòng 1 phút.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.auth.all })
    },
  })
}

export function useRevokeMyOtherSessions() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => loginSessionApi.revokeMyOthers(),
    onSuccess: (data) => {
      toast.success(`Đã đăng xuất ${data?.revoked ?? 0} thiết bị khác.`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.auth.all })
    },
  })
}
