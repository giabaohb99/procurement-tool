import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { aiPlanApi } from '../api/ai-plan-api'
import type { AiPlanDocument } from '../types/ai-plan'

export function useAiPlans(params: { status?: number; page: number; page_size: number }) {
  return useQuery({
    queryKey: queryKeys.work.aiPlans(params),
    queryFn: () => aiPlanApi.list(params),
  })
}

export function useAiPlan(id: number) {
  return useQuery({
    queryKey: queryKeys.work.aiPlan(id),
    queryFn: () => aiPlanApi.get(id),
    enabled: id > 0,
    //  Màn chi tiết dựng lại bộ sửa mỗi khi dữ liệu đổi (`dataUpdatedAt`) — tự tải lại lúc
    //  quay về tab là XÓA SẠCH bản người duyệt đang sửa dở. Dữ liệu chỉ đổi khi chính
    //  người này lưu / duyệt / từ chối, và các lần đó đã ghi thẳng vào đệm.
    staleTime: Number.POSITIVE_INFINITY,
    refetchOnWindowFocus: false,
  })
}

/**
 * Ba thao tác ghi của một đề xuất. Xong thì làm mới cả nhánh `ai-plans` (danh sách đổi
 * trạng thái, đếm việc); duyệt xong thì làm mới luôn cây dự án bên trái vì vừa có bảng mới.
 *
 * Lỗi 422 `PLAN_INVALID` để màn tự đọc `details.problems` và ghim vào dòng — `http-client`
 * đã toast câu chung sẵn rồi.
 */
export function useAiPlanActions(id: number) {
  const queryClient = useQueryClient()
  const refresh = () => queryClient.invalidateQueries({ queryKey: queryKeys.work.aiPlans() })

  const save = useMutation({
    mutationFn: (plan: AiPlanDocument) => aiPlanApi.save(id, plan),
    onSuccess: (detail) => {
      queryClient.setQueryData(queryKeys.work.aiPlan(id), detail)
      void refresh()
      toast.success('Đã lưu bản sửa')
    },
  })

  const approve = useMutation({
    mutationFn: (plan: AiPlanDocument) => aiPlanApi.approve(id, plan),
    onSuccess: () => {
      //  Cả phân hệ: vừa có bảng Dự án mới (cây bên trái, tổng quan) và đề xuất đổi trạng thái.
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
      toast.success('Đã duyệt — kế hoạch đã tạo trong Dự án')
    },
  })

  const reject = useMutation({
    mutationFn: (reason: string) => aiPlanApi.reject(id, reason),
    onSuccess: (detail) => {
      queryClient.setQueryData(queryKeys.work.aiPlan(id), detail)
      void refresh()
      toast.success('Đã từ chối đề xuất')
    },
  })

  return { save, approve, reject }
}
