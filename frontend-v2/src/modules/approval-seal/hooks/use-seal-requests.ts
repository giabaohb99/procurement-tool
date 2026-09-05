import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { sealRequestApi } from '../api/seal-request-api'
import type { SealRequestPayload } from '../types/seal-request'

/** Danh sách phiếu đóng dấu trong phạm vi người xem. Server phân trang. */
export function useSealRequests(params: ListParams = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }
  return useQuery({
    queryKey: queryKeys.sealRequest.list(query),
    queryFn: () => sealRequestApi.list(query),
    placeholderData: keepPreviousData,
  })
}

export function useSealRequest(id: number | null) {
  return useQuery({
    queryKey: queryKeys.sealRequest.detail(id ?? 0),
    queryFn: () => sealRequestApi.get(id as number),
    enabled: id !== null && id > 0,
  })
}

/** Tạo phiếu — `submit` quyết định lưu nháp hay gửi duyệt. */
export function useCreateSealRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ payload, submit }: { payload: SealRequestPayload; submit: boolean }) =>
      sealRequestApi.create(payload, submit),
    onSuccess: (_data, { submit }) => {
      qc.invalidateQueries({ queryKey: queryKeys.sealRequest.all })
      toast.success(submit ? 'Đã gửi duyệt yêu cầu đóng dấu' : 'Đã lưu nháp yêu cầu đóng dấu')
    },
  })
}

/** Sửa phiếu (chỉ khi còn nháp / bị trả về) — `submit` để gửi duyệt sau khi lưu. */
export function useUpdateSealRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      payload,
      submit,
    }: {
      id: number
      payload: Partial<SealRequestPayload>
      submit: boolean
    }) => sealRequestApi.update(id, payload, submit),
    onSuccess: (_data, { id, submit }) => {
      qc.invalidateQueries({ queryKey: queryKeys.sealRequest.all })
      qc.invalidateQueries({ queryKey: queryKeys.sealRequest.detail(id) })
      toast.success(submit ? 'Đã gửi duyệt yêu cầu đóng dấu' : 'Đã lưu thay đổi')
    },
  })
}

export function useDeleteSealRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => sealRequestApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.sealRequest.all })
      toast.success('Đã xóa yêu cầu đóng dấu')
    },
  })
}

/**
 * Các nút chuyển trạng thái theo vai trò. Mọi mutation làm mới danh sách + chi
 * tiết rồi bắn toast — dùng chung một khung để khỏi lặp bảy hook.
 */
function useSealTransition<TVars extends { id: number }>(
  mutationFn: (vars: TVars) => Promise<unknown>,
  successMsg: string,
) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: queryKeys.sealRequest.all })
      qc.invalidateQueries({ queryKey: queryKeys.sealRequest.detail(id) })
      toast.success(successMsg)
    },
  })
}

/** Gửi duyệt từ trang chi tiết (khác nút Gửi duyệt trên form — không lưu lại nội dung). */
export function useSubmitSealRequest() {
  return useSealTransition(({ id }: { id: number }) => sealRequestApi.submit(id), 'Đã gửi duyệt yêu cầu')
}

// --- Trưởng bộ phận ---
export function useApproveSealRequest() {
  return useSealTransition(({ id }: { id: number }) => sealRequestApi.approve(id), 'Đã duyệt yêu cầu')
}
export function useReturnSealRequest() {
  return useSealTransition(
    ({ id, reason }: { id: number; reason: string }) => sealRequestApi.returnForEdit(id, reason),
    'Đã trả lại để chỉnh sửa',
  )
}
export function useRejectSealRequest() {
  return useSealTransition(
    ({ id, reason }: { id: number; reason: string }) => sealRequestApi.reject(id, reason),
    'Đã từ chối yêu cầu',
  )
}

// --- Văn thư ---
export function useCompleteSealRequest() {
  return useSealTransition(
    ({ id, copies_done, note }: { id: number; copies_done?: number; note: string }) =>
      sealRequestApi.complete(id, { copies_done, note }),
    'Đã hoàn thành đóng dấu',
  )
}
export function useReturnClerkSealRequest() {
  return useSealTransition(
    ({ id, reason }: { id: number; reason: string }) => sealRequestApi.returnClerk(id, reason),
    'Đã trả lại để chỉnh sửa',
  )
}
export function useRejectClerkSealRequest() {
  return useSealTransition(
    ({ id, reason }: { id: number; reason: string }) => sealRequestApi.rejectClerk(id, reason),
    'Đã từ chối yêu cầu',
  )
}
