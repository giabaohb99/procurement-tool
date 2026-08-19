import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  surveyApi,
  type SurveyLineApproveItem,
  type SurveyPayload,
} from '../api/survey-api'
import type { SurveyLine, SurveyTable } from '../types/survey-detail'

/** Một phiếu khảo sát. `id <= 0` (màn tạo mới) thì không gọi API. */
export function useSurvey(id: number) {
  return useQuery({
    queryKey: queryKeys.procurement.survey(id),
    queryFn: () => surveyApi.getById(id),
    enabled: id > 0,
  })
}

/** Tạo mới HOẶC cập nhật — một form dùng cho cả hai màn. */
export function useSaveSurvey() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id?: number; payload: SurveyPayload }) =>
      id ? surveyApi.update(id, payload) : surveyApi.create(payload),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu phiếu' : 'Đã tạo phiếu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Tên thao tác chuyển trạng thái + câu báo thành công tương ứng. */
const ACTION_LABELS = {
  submit: 'Đã gửi duyệt',
  approve: 'Đã duyệt phiếu',
  reject: 'Đã trả lại phiếu',
  cancel: 'Đã từ chối phiếu',
  clone: 'Đã nhân bản phiếu',
} as const

export type SurveyAction = keyof typeof ACTION_LABELS

/**
 * Mọi thao tác chuyển trạng thái gom vào MỘT mutation — chúng chỉ khác đường dẫn
 * và câu thông báo. `reason` bắt buộc với reject / cancel (backend cũng chặn).
 */
export function useSurveyAction(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ action, reason }: { action: SurveyAction; reason?: string }) => {
      switch (action) {
        case 'submit':
          return surveyApi.submit(id)
        case 'approve':
          return surveyApi.approve(id)
        case 'reject':
          return surveyApi.reject(id, reason ?? '')
        case 'cancel':
          return surveyApi.cancel(id, reason ?? '')
        case 'clone':
          return surveyApi.clone(id)
      }
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_LABELS[variables.action])
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

export function useDeleteSurvey() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => surveyApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa phiếu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** TP/QL chốt duyệt từng dòng của cả hai bảng trong một lượt. */
export function useSurveyLineApprove(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      supplierLines,
      productLines,
    }: {
      supplierLines: SurveyLineApproveItem[]
      productLines: SurveyLineApproveItem[]
    }) => surveyApi.lineApprove(id, supplierLines, productLines),
    onSuccess: () => {
      toast.success('Đã lưu duyệt dòng')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}

/** Bổ sung thông tin một dòng khi phiếu đã gửi và TP/QL báo "Thiếu thông tin". */
export function useFillSurveyLine(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      table,
      lineId,
      changes,
    }: {
      table: SurveyTable
      lineId: number
      changes: SurveyLine
    }) => surveyApi.fillLine(id, table, lineId, changes),
    onSuccess: () => {
      toast.success('Đã lưu bổ sung')
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
    },
  })
}
