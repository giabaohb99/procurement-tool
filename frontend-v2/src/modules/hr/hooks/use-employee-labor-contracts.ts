import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { laborContractApi } from '../api/labor-contract-api'
import type {
  LaborContractPayload,
  LaborContractSaveResult,
  LaborContractTransitionPayload,
  LaborContractUpdatePayload,
} from '../types/labor-contract'

/** Hợp đồng của MỘT nhân sự. Chỉ nạp khi `enabled` (có quyền đọc) — tránh toast 403 lúc mount. */
export function useEmployeeLaborContracts(employeeId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.employeeLaborContracts(employeeId),
    queryFn: () => laborContractApi.listByEmployee(employeeId),
    enabled: enabled && employeeId > 0,
  })
}

/** Mẫu chọn được cho nhân sự này (`contractType` 0 = mọi loại). */
export function useEmployeeLaborContractTemplates(
  employeeId: number,
  contractType: number,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.hr.employeeLaborContractTemplates(employeeId, contractType),
    queryFn: () => laborContractApi.listTemplateOptions(employeeId, contractType || undefined),
    enabled: enabled && employeeId > 0,
  })
}

/** Mẫu chọn được để sinh tệp cho MỘT hợp đồng (theo pháp nhân + loại của HĐ, không theo nhân sự hiện tại). */
export function useLaborContractTemplateOptions(employeeId: number, contractId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractTemplateOptions(employeeId, contractId),
    queryFn: () => laborContractApi.listTemplateOptionsForContract(contractId),
    enabled: enabled && contractId > 0,
  })
}

/** `warnings` không chặn (vd HĐ xác định thời hạn > 36 tháng): hiện toast cảnh báo, KHÔNG phải lỗi. */
export function notifySaveWarnings(result: LaborContractSaveResult, message: string) {
  toast.success(message)
  for (const warning of result.warnings ?? []) toast.warning(warning)
}

/** Mọi lệnh ghi quét cả nhánh hồ sơ của người này — danh sách + ô chọn mẫu cùng mới. */
function useInvalidateContracts(employeeId: number) {
  const queryClient = useQueryClient()
  return () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.employeeLaborContracts(employeeId) })
}

export function useSaveLaborContract(employeeId: number) {
  const invalidate = useInvalidateContracts(employeeId)
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id?: number
      payload: LaborContractPayload | LaborContractUpdatePayload
    }) =>
      id
        ? laborContractApi.update(id, payload)
        : laborContractApi.create(employeeId, payload as LaborContractPayload),
    onSuccess: (result, { id }) => {
      notifySaveWarnings(result, id ? 'Đã cập nhật hợp đồng' : 'Đã lập hợp đồng')
      void invalidate()
    },
  })
}

export function useDeleteLaborContract(employeeId: number) {
  const invalidate = useInvalidateContracts(employeeId)
  return useMutation({
    mutationFn: (id: number) => laborContractApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa hợp đồng')
      void invalidate()
    },
  })
}

export function useGenerateLaborContract(employeeId: number) {
  const invalidate = useInvalidateContracts(employeeId)
  return useMutation({
    mutationFn: ({ id, templateId }: { id: number; templateId: number }) =>
      laborContractApi.generate(id, { template_id: templateId }),
    onSuccess: () => {
      toast.success('Đã sinh tệp hợp đồng')
      void invalidate()
    },
  })
}

export function useTransitionLaborContract(employeeId: number) {
  const invalidate = useInvalidateContracts(employeeId)
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: LaborContractTransitionPayload }) =>
      laborContractApi.transition(id, payload),
    onSuccess: () => {
      toast.success('Đã đổi trạng thái hợp đồng')
      void invalidate()
    },
  })
}

export function useUploadSignedLaborContract(employeeId: number) {
  const invalidate = useInvalidateContracts(employeeId)
  return useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) =>
      laborContractApi.uploadSignedFile(id, file),
    onSuccess: () => {
      toast.success('Đã tải lên bản ký')
      void invalidate()
    },
  })
}
