import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { useEmployeeLaborContractTemplates, useSaveLaborContract } from '../hooks/use-employee-labor-contracts'
import {
  buildContractFormDefaults,
  laborContractSchema,
  toLaborContractPayload,
  type LaborContractFormValues,
} from '../schemas/labor-contract-schema'
import type { EmployeeDetail } from '../types/employee'
import type { LaborContract } from '../types/labor-contract'
import { LaborContractFormDialogFields } from './labor-contract-form-dialog-fields'

interface LaborContractFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  employee: EmployeeDetail
  /** Có = đang SỬA (chỉ DRAFT); không = lập mới. */
  row?: LaborContract | null
}

/** Hộp lập / sửa hợp đồng nháp. Chọn mẫu và sinh tệp là bước RIÊNG (hộp «Sinh tệp»). */
export function LaborContractFormDialog({ open, onOpenChange, employee, row }: LaborContractFormDialogProps) {
  const { can } = usePermission()
  const saveMutation = useSaveLaborContract(employee.id)
  //  Chặn bấm đúp bằng ref (disabled theo state React chỉ đúng ở lần render sau).
  const submitting = useRef(false)

  const form = useForm<LaborContractFormValues>({
    resolver: zodResolver(laborContractSchema),
    defaultValues: buildContractFormDefaults(employee, row),
  })

  useEffect(() => {
    if (open) form.reset(buildContractFormDefaults(employee, row))
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ reset lúc MỞ / đổi dòng.
  }, [open, row])

  const contractType = form.watch('contract_type')
  const { data: templates, isSuccess } = useEmployeeLaborContractTemplates(
    employee.id,
    contractType,
    open && contractType > 0,
  )
  const companyName = row?.company_name ?? employee.company_name ?? ''

  function onSubmit(values: LaborContractFormValues) {
    if (submitting.current) return
    submitting.current = true
    saveMutation.mutate(
      { id: row?.id, payload: toLaborContractPayload(values, row ? 'edit' : 'create') },
      {
        onSuccess: () => onOpenChange(false),
        onSettled: () => {
          submitting.current = false
        },
      },
    )
  }

  const templateHint =
    contractType > 0 && isSuccess && (templates?.length ?? 0) === 0 ? (
      <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">
        Pháp nhân {companyName || 'này'} chưa có mẫu cho loại này.
        {can('labor_contract_template', 'read') && (
          <>
            {' '}
            <Link to={appRoutes.hr.laborContractTemplates} className="font-medium underline">
              Mở màn Mẫu hợp đồng
            </Link>
          </>
        )}
      </p>
    ) : null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{row ? 'Sửa hợp đồng' : 'Lập hợp đồng lao động'}</DialogTitle>
        </DialogHeader>
        <LaborContractFormDialogFields
          form={form}
          onSubmit={onSubmit}
          companyName={companyName}
          templateHint={templateHint}
          footer={
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Hủy</Button>
              <Button type="submit" disabled={saveMutation.isPending}>
                {saveMutation.isPending && <Loader2 className="size-4 animate-spin" />}
                Lưu
              </Button>
            </DialogFooter>
          }
        />
      </DialogContent>
    </Dialog>
  )
}
