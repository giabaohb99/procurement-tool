import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '@/core/auth/use-auth'
import { queryKeys } from '@/shared/constants/query-keys'
import { fetchMyPreferences } from '@/shared/theme/theme-api'

import {
  fetchReleaseNotes,
  fetchReleaseVersion,
  RELEASE_SEEN_PREFERENCE_KEY,
  saveReleaseSeen,
} from './release-api'

/** Phiên bản đang chạy — một lần mỗi phiên là đủ, image không đổi giữa chừng. */
export function useReleaseVersion() {
  const { user } = useAuth()
  return useQuery({
    queryKey: queryKeys.release.version(),
    queryFn: fetchReleaseVersion,
    enabled: !!user,
    staleTime: Infinity,
  })
}

export function useReleaseNotes() {
  return useQuery({
    queryKey: queryKeys.release.notes(),
    queryFn: () => fetchReleaseNotes(),
    staleTime: Infinity,
  })
}

/**
 * Có đợt mới chưa xem? So phiên bản đang chạy với khóa `release_seen_version` trong tùy chọn cá nhân.
 *
 * Lần đầu đọc từ hồ sơ `/api/auth/me` (đã kèm `preferences`) để không gọi thêm; sau khi đánh dấu thì bộ đệm
 * `auth.preferences` được cập nhật nên chấm đỏ tắt ngay, không chờ nạp lại.
 */
export function useReleaseUnseen() {
  const { user } = useAuth()
  const version = useReleaseVersion()
  const prefs = useQuery({
    queryKey: queryKeys.auth.preferences(),
    queryFn: fetchMyPreferences,
    enabled: !!user,
    staleTime: Infinity,
    initialData: user?.preferences,
  })
  const seen = prefs.data?.[RELEASE_SEEN_PREFERENCE_KEY] ?? ''
  const current = version.data?.version ?? ''
  return { unseen: !!current && seen !== current, version: version.data }
}

export function useMarkReleaseSeen() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (version: string) => saveReleaseSeen(version),
    onSuccess: (prefs) => {
      queryClient.setQueryData(queryKeys.auth.preferences(), prefs)
    },
  })
}
