import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { laborContractTemplateApi } from '../api/labor-contract-template-api'
import type {
  LaborContractTemplateContent,
  LaborContractTemplateFormValues,
  LaborContractTemplateUpdatePayload,
} from '../types/labor-contract'

/** Danh sách mẫu. `hr.all` bị quét sau mỗi lệnh ghi nên bảng và ô chọn mẫu ở hồ sơ cùng mới. */
export function useLaborContractTemplates(params: ListParams, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractTemplates(params),
    queryFn: () => laborContractTemplateApi.list(params),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

/** Danh mục biến — chỉ nạp khi hộp hướng dẫn mở (`enabled`). */
export function useLaborContractPlaceholders(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractPlaceholders(),
    queryFn: () => laborContractTemplateApi.placeholders(),
    enabled,
    staleTime: 10 * 60_000,
  })
}

/** MỘT mẫu — tên / pháp nhân cho tiêu đề trang soạn. */
export function useLaborContractTemplate(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractTemplate(id),
    queryFn: () => laborContractTemplateApi.get(id),
    enabled: id > 0,
  })
}

/**
 * Nội dung HTML để soạn. `staleTime: Infinity` + không tự nạp lại khi quay lại tab: trình soạn thảo
 * chỉ đọc `defaultContent` MỘT lần, nạp lại giữa chừng là đè mất chữ người dùng đang gõ.
 */
export function useLaborContractTemplateContent(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractTemplateContent(id),
    queryFn: () => laborContractTemplateApi.content(id),
    enabled: id > 0,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    retry: false,
  })
}

function useInvalidateHr() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
}

export function useCreateLaborContractTemplate() {
  const invalidate = useInvalidateHr()
  return useMutation({
    mutationFn: ({ values, file }: { values: LaborContractTemplateFormValues; file: File }) =>
      laborContractTemplateApi.create(values, file),
    onSuccess: () => {
      toast.success('Đã tải mẫu hợp đồng lên')
      void invalidate()
    },
  })
}

export function useReplaceLaborContractTemplateFile() {
  const invalidate = useInvalidateHr()
  return useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) =>
      laborContractTemplateApi.replaceFile(id, file),
    onSuccess: () => {
      toast.success('Đã thay tệp mẫu')
      void invalidate()
    },
  })
}

export function useSaveLaborContractTemplateContent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: LaborContractTemplateContent }) =>
      laborContractTemplateApi.saveContent(id, payload),
    onSuccess: (_data, { id }) => {
      toast.success('Đã lưu nội dung mẫu')
      //  Chỉ quét danh sách + thông tin mẫu; KHÔNG quét khóa nội dung đang mở (đè chữ đang soạn).
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.laborContractTemplates().slice(0, 2) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.laborContractTemplate(id), exact: true })
    },
  })
}

export function useUpdateLaborContractTemplate() {
  const invalidate = useInvalidateHr()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: LaborContractTemplateUpdatePayload }) =>
      laborContractTemplateApi.update(id, payload),
    onSuccess: (_data, { payload }) => {
      if (payload.is_active !== undefined) {
        toast.success(payload.is_active ? 'Đã bật dùng mẫu' : 'Đã ngừng dùng mẫu')
      } else {
        toast.success('Đã cập nhật mẫu')
      }
      void invalidate()
    },
  })
}

export function useDeleteLaborContractTemplate() {
  const invalidate = useInvalidateHr()
  return useMutation({
    mutationFn: (id: number) => laborContractTemplateApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa mẫu')
      void invalidate()
    },
  })
}
