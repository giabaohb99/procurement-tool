import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiPut } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { fetchMyPreferences, type UserPreferences } from '@/shared/theme/theme-api'
import {
  PINNED_LISTS_PREF_KEY,
  parsePinnedLists,
  serializePinnedLists,
  togglePinned,
} from '../utils/pinned-lists'

/**
 * Danh sách dự án đã ghim của người đang đăng nhập (A-05).
 *
 * Dùng chung khóa `auth.preferences` với `ThemeSync` nên hai bên đọc cùng một bản
 * đệm, không gọi `/api/me/preferences` hai lần. Ghim LẠC QUAN: đổi trên màn ngay,
 * máy chủ trả lại toàn bộ tùy chọn thì ghi đè; lỗi thì quay về bản cũ.
 */
export function usePinnedLists() {
  const queryClient = useQueryClient()
  const key = queryKeys.auth.preferences()

  const { data } = useQuery({ queryKey: key, queryFn: fetchMyPreferences, staleTime: 60_000 })
  const pinned = parsePinnedLists(data?.[PINNED_LISTS_PREF_KEY])

  const save = useMutation({
    //  Bấm ghim/bỏ ghim liên tiếp: chạy NỐI ĐUÔI, để lượt trả lời cũ về sau không
    //  ghi đè bản mới vào bộ đệm (mỗi lượt gửi TOÀN BỘ danh sách ghim).
    scope: { id: 'work-pinned-lists' },
    mutationFn: (ids: number[]) =>
      apiPut<UserPreferences>('/api/me/preferences', {
        values: { [PINNED_LISTS_PREF_KEY]: serializePinnedLists(ids) },
      }),
    onMutate: async (ids) => {
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<UserPreferences>(key)
      queryClient.setQueryData<UserPreferences>(key, {
        ...(previous ?? {}),
        [PINNED_LISTS_PREF_KEY]: serializePinnedLists(ids),
      })
      return { previous }
    },
    onError: (_error, _ids, context) => {
      if (context?.previous) queryClient.setQueryData(key, context.previous)
    },
    onSuccess: (prefs) => queryClient.setQueryData(key, prefs),
  })

  return {
    pinned,
    isPinned: (listId: number) => pinned.includes(listId),
    toggle: (listId: number) => save.mutate(togglePinned(pinned, listId)),
  }
}
