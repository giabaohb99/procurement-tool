import { keepPreviousData, useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  chatGroupApi,
  type ChatGroupListParams,
  type ChatGroupMessageParams,
} from '../api/chat-group-api'

const MESSAGE_PAGE = 100

/** Danh mục loại / kênh + quyền của người đang xem — gần như bất biến trong phiên. */
export function useChatGroupMeta() {
  return useQuery({
    queryKey: queryKeys.assistant.chatGroupMeta(),
    queryFn: chatGroupApi.meta,
    staleTime: 5 * 60 * 1000,
  })
}

export function useChatGroups(params: ChatGroupListParams) {
  return useQuery({
    queryKey: queryKeys.assistant.chatGroups(params as Record<string, unknown>),
    queryFn: () => chatGroupApi.list(params),
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
  })
}

export function useChatGroup(id: number) {
  return useQuery({
    queryKey: queryKeys.assistant.chatGroup(id),
    queryFn: () => chatGroupApi.detail(id),
    enabled: id > 0,
  })
}

/** Tin nhóm, mới nhất trước; «Xem tin cũ hơn» kéo thêm trang bằng `before_id`. */
export function useChatGroupMessages(id: number, params: Omit<ChatGroupMessageParams, 'before_id'>) {
  return useInfiniteQuery({
    queryKey: queryKeys.assistant.chatGroupMessages(id, params as Record<string, unknown>),
    queryFn: ({ pageParam }) => chatGroupApi.messages(id, { ...params, limit: MESSAGE_PAGE, before_id: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (last) => (last.has_more && last.next_before_id ? last.next_before_id : undefined),
    enabled: id > 0,
  })
}

export function useChatGroupSummaries(id: number) {
  return useQuery({
    queryKey: queryKeys.assistant.chatGroupSummaries(id),
    queryFn: () => chatGroupApi.summaries(id),
    enabled: id > 0,
  })
}

export function useChatGroupViews(id: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.assistant.chatGroupViews(id),
    queryFn: () => chatGroupApi.views(id),
    enabled: id > 0 && enabled,
  })
}

export function useSummarizeChatGroup(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (hours: number) => chatGroupApi.summarize(id, hours),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.assistant.chatGroupSummaries(id) }),
  })
}

export function useUpdateChatGroup(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { category?: number; paused?: boolean }) => chatGroupApi.update(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.assistant.chatGroupsAll() }),
  })
}

/** Tình trạng Zalo công ty. Đang chờ quét QR thì hỏi lại mỗi 3 giây để ảnh mã mới / kết quả quét hiện ngay. */
export function useZaloStatus(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.assistant.zaloStatus(),
    queryFn: chatGroupApi.zaloStatus,
    enabled,
    refetchInterval: (query) => (query.state.data?.state === 'qr' ? 3000 : 30 * 1000),
  })
}

export function useZaloLogin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: chatGroupApi.zaloLogin,
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.assistant.zaloStatus() }),
  })
}

/** ai-CR-129: đăng xuất / đổi tài khoản Zalo công ty. */
export function useZaloLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: chatGroupApi.zaloLogout,
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.assistant.zaloStatus() }),
  })
}

export function useZaloRefreshGroups() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: chatGroupApi.zaloRefreshGroups,
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.assistant.chatGroupsAll() }),
  })
}
