import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { useGenerateLaborContract, useLaborContractTemplateOptions } from '../hooks/use-employee-labor-contracts'
import type { LaborContract } from '../types/labor-contract'

interface LaborContractGenerateDialogProps {
  /** `null` = đóng. */
  row: LaborContract | null
  employeeId: number
  onClose: () => void
}

/**
 * Chọn mẫu rồi sinh (hoặc sinh lại) tệp .docx. Chỉ liệt kê mẫu `is_active` của pháp nhân và loại của
 * CHÍNH hợp đồng (snapshot lúc lập — nhân sự chuyển pháp nhân sau đó vẫn ra đúng mẫu cũ); backend
 * lọc, FE chỉ hiển thị.
 * Dựng thân hộp chỉ khi mở nên state chọn mẫu tự sạch mỗi lần mở.
 */
export function LaborContractGenerateDialog({ row, employeeId, onClose }: LaborContractGenerateDialogProps) {
  return (
    <Dialog open={row !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        {row && <GenerateBody row={row} employeeId={employeeId} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  )
}

function GenerateBody({ row, employeeId, onClose }: { row: LaborContract; employeeId: number; onClose: () => void }) {
  const { can } = usePermission()
  const { data: templates, isLoading, isError } = useLaborContractTemplateOptions(employeeId, row.id, true)
  const generateMutation = useGenerateLaborContract(employeeId)
  const [picked, setPicked] = useState<number | null>(null)

  const options = templates ?? []
  //  Ưu tiên lựa chọn của người dùng; chưa chọn thì mẫu đã dùng lần trước (nếu còn trong danh sách);
  //  chỉ có đúng một mẫu thì lấy luôn.
  const templateId =
    picked ?? options.find((t) => t.id === row.template_id)?.id ?? (options.length === 1 ? options[0].id : null)

  function handleGenerate() {
    if (templateId === null || generateMutation.isPending) return
    generateMutation.mutate({ id: row.id, templateId }, { onSuccess: onClose })
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>{row.has_generated_file ? 'Sinh lại tệp hợp đồng' : 'Sinh tệp hợp đồng'}</DialogTitle>
      </DialogHeader>
      <div className="space-y-3">
        {isLoading && <Skeleton className="h-9 w-full" />}
        {isError && <p className="text-sm text-destructive">Không tải được danh sách mẫu.</p>}
        {!isLoading && !isError && options.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Pháp nhân {row.company_name || 'này'} chưa có mẫu cho loại hợp đồng này.
            {can('labor_contract_template', 'read') && (
              <>
                {' '}
                <Link to={appRoutes.hr.laborContractTemplates} className="font-medium underline">
                  Mở màn Mẫu hợp đồng
                </Link>
              </>
            )}
          </p>
        )}
        {options.length > 0 && (
          <div className="space-y-1.5">
            <Label htmlFor="labor-contract-template">Mẫu hợp đồng *</Label>
            <Select value={templateId === null ? '' : String(templateId)} onValueChange={(v) => setPicked(Number(v))}>
              <SelectTrigger id="labor-contract-template" className="w-full">
                <SelectValue placeholder="Chọn mẫu" />
              </SelectTrigger>
              <SelectContent>
                {options.map((t) => (
                  <SelectItem key={t.id} value={String(t.id)}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {row.has_generated_file && (
              <p className="text-xs text-muted-foreground">Tệp đã sinh trước đó sẽ được thay bằng tệp mới.</p>
            )}
          </div>
        )}
      </div>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>Hủy</Button>
        <Button type="button" disabled={templateId === null || generateMutation.isPending} onClick={handleGenerate}>
          {generateMutation.isPending && <Loader2 className="size-4 animate-spin" />}
          Sinh tệp
        </Button>
      </DialogFooter>
    </>
  )
}
