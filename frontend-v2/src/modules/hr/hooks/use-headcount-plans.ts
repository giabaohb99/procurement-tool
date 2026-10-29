import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { getCrudRootKey } from '@/shared/crud'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { HEADCOUNT_PLAN_API_PATH, headcountPlanApi } from '../api/headcount-plan-api'
import type {
  HeadcountPlanCreatePayload,
  HeadcountPlanCreateResult,
  HeadcountPlanDraftPayload,
  HeadcountPlanPayload,
} from '../types/headcount-plan'

/** Chờ người dùng dừng tay 400ms rồi mới hỏi bộ tính — cùng nhịp với ô tìm toàn văn. */
const COMPUTE_DEBOUNCE_MS = 400

export function useHeadcountPlan(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.headcountPlan(id),
    queryFn: () => headcountPlanApi.get(id),
    enabled: id > 0,
  })
}

/**
 * XEM TRƯỚC bảng tự tính. Gọi `POST /compute` theo bản nháp ĐÃ HOÃN — `useQuery` (không phải
 * mutation) vì đây là phép đọc thuần, cùng bản nháp thì cùng kết quả, và TanStack tự bỏ câu trả lời
 * của bản nháp cũ khi người dùng gõ tiếp. Chưa chọn pháp nhân thì không hỏi (backend 422 vô ích).
 */
export function useHeadcountPlanCompute(payload: HeadcountPlanDraftPayload, enabled: boolean) {
  const debounced = useDebouncedValue(payload, COMPUTE_DEBOUNCE_MS)
  return useQuery({
    queryKey: queryKeys.hr.headcountPlanCompute(debounced),
    queryFn: () => headcountPlanApi.compute(debounced),
    enabled: enabled && debounced.company_id > 0,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

/** «Đang có» + lương bình quân theo vị trí. Pháp nhân chưa chọn thì không hỏi. */
export function useHeadcountPlanPositionStats(companyId: number, departmentId: number) {
  return useQuery({
    queryKey: queryKeys.hr.headcountPlanPositionStats(companyId, departmentId),
    queryFn: () => headcountPlanApi.positionStats(companyId, departmentId),
    enabled: companyId > 0,
    staleTime: 60_000,
  })
}

function useInvalidatePlans() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: getCrudRootKey(HEADCOUNT_PLAN_API_PATH) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.hr.headcountPlansRoot() })
  }
}

/**
 * LƯU kế hoạch: tạo = `POST` (một lượt, kèm dòng + văn bản; khoản chép từ mẫu ở backend trừ khi người
 * dùng đã sửa bảng khoản), sửa = `PUT` thay nguyên. Không có PATCH.
 */
export function useSaveHeadcountPlan() {
  const invalidate = useInvalidatePlans()
  return useMutation({
    mutationFn: ({
      id,
      create,
      payload,
    }: {
      id: number
      create: HeadcountPlanCreatePayload
      payload: HeadcountPlanPayload
    }): Promise<HeadcountPlanCreateResult> =>
      id > 0 ? headcountPlanApi.update(id, payload) : headcountPlanApi.create(create),
    onSuccess: (data, { id }) => {
      toast.success(id > 0 ? 'Đã lưu kế hoạch nhân sự' : 'Đã tạo kế hoạch nhân sự')
      //  Backend bỏ khoản của mẫu rơi ngoài kỳ khi chép (thưởng T12 trong kế hoạch Q1) — nói ra, kẻo
      //  người lập tưởng mẫu thiếu khoản.
      if (data.skipped_items?.length) {
        toast.info(`Không chép các khoản ngoài kỳ: ${data.skipped_items.join(', ')}`)
      }
      invalidate()
    },
  })
}

export function useDeleteHeadcountPlan() {
  const invalidate = useInvalidatePlans()
  return useMutation({
    mutationFn: headcountPlanApi.remove,
    onSuccess: () => {
      toast.success('Đã xóa kế hoạch nhân sự')
      invalidate()
    },
  })
}

export function useImportHeadcountPlanLines(id: number) {
  const invalidate = useInvalidatePlans()
  return useMutation({
    mutationFn: (file: File) => headcountPlanApi.importLinesCsv(id, file),
    onSuccess: invalidate,
  })
}
