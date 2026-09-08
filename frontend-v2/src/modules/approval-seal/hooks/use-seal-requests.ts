import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
// Phân hệ Duyệt dấu dùng chung tầng đính kèm của Mua hàng (DocumentAttachmentsCard,
// hook đính kèm ở trang chi tiết cũng lấy từ đây) — nên tải tệp đã ký cũng đi qua
// đúng api đó thay vì dựng lối riêng.
import { purchaseRequestSupportApi } from '@/modules/procurement/api/purchase-request-support-api'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { sealRequestApi } from '../api/seal-request-api'
import type { SealRequestPayload } from '../types/seal-request'

/** Loại chứng từ mặc định cho tệp đã ký đính kèm lúc tạo phiếu. */
const SIGNED_DOC_TYPE = 'signed_doc'

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

/**
 * TBP đủ điều kiện duyệt + id người duyệt mặc định.
 *
 * Key cục bộ, chỉ một hook dùng và không ai làm mới từ bên ngoài (theo ngoại lệ
 * ở `naming.md`). `enabled` để màn tự tắt khi thiếu quyền tạo phiếu.
 */
export function useSealApprovers(enabled = true) {
  return useQuery({
    queryKey: ['seal-request', 'approvers'] as const,
    queryFn: () => sealRequestApi.listApprovers(),
    enabled,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Tạo phiếu KÈM chứng từ đã ký chọn sẵn trên form tạo mới.
 *
 * Backend đòi ≥1 tệp đính kèm trước khi gửi duyệt, mà tệp chỉ gắn được sau khi
 * phiếu đã có id — nên luôn tạo NHÁP trước để lấy id, tải các tệp đã buffer lên,
 * rồi mới gửi duyệt nếu người dùng bấm "Gửi duyệt". Một toast duy nhất ở cuối.
 */
export function useCreateSealRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({
      payload,
      files,
      submit,
    }: {
      payload: SealRequestPayload
      files: File[]
      submit: boolean
    }) => {
      const created = await sealRequestApi.create(payload, false)
      if (files.length) {
        await purchaseRequestSupportApi.uploadAttachments(
          'seal_request',
          created.id,
          files,
          SIGNED_DOC_TYPE,
        )
      }
      return submit ? sealRequestApi.submit(created.id) : created
    },
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
    ({ id, note }: { id: number; note: string }) => sealRequestApi.complete(id, { note }),
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
