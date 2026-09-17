import { ArrowRightLeft, CornerUpLeft, Loader2 } from 'lucide-react'
import { useState } from 'react'

import type { Department } from '@/modules/hr/types/department'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'

export type TransferDeptMode = 'transfer' | 'return'

interface TransferDeptDialogProps {
  open: boolean
  mode: TransferDeptMode
  /** "yêu cầu mua hàng" / "yêu cầu báo giá" — ghép vào câu mô tả. */
  docLabel: string
  /** Mọi phòng ban đang có; hộp tự lọc phòng hoạt động và bỏ phòng đang xử lý. */
  departments: Department[]
  /** Phòng ĐANG xử lý (phòng được nhờ; 0 = phòng lập tự xử lý). */
  currentDeptId: number
  /** Phòng lập phiếu. */
  requestingDeptId: number
  pending?: boolean
  onOpenChange: (open: boolean) => void
  /** `handlerDeptId` = 0 khi trả về phòng lập. Lý do đã cắt khoảng trắng. */
  onConfirm: (handlerDeptId: number, reason: string) => void | Promise<void>
}

/**
 * bao-CR-414 GĐ5 — hộp CHUYỂN PHÒNG XỬ LÝ / TRẢ VỀ PHÒNG LẬP dùng chung cho YCMH và YCBG.
 *
 * `mode = 'transfer'`: chọn phòng đích (bỏ phòng đang xử lý) + lý do bắt buộc.
 * `mode = 'return'`: chỉ hỏi lý do, đích là phòng lập phiếu (backend đặt `handler_dept_id` = 0).
 * Không có lựa chọn chuyển MỘT PHẦN dòng — cả phiếu đi cùng nhau (luật đã chốt ở HDSD).
 */
export function TransferDeptDialog({
  open,
  mode,
  docLabel,
  departments,
  currentDeptId,
  requestingDeptId,
  pending,
  onOpenChange,
  onConfirm,
}: TransferDeptDialogProps) {
  const [deptId, setDeptId] = useState('')
  const [reason, setReason] = useState('')

  // Mở lại hộp cho thao tác khác thì phải sạch ô, không mang phòng/lý do cũ theo.
  if (useHasChanged(open)) {
    setDeptId('')
    setReason('')
  }

  const isTransfer = mode === 'transfer'
  const effectiveCurrent = currentDeptId || requestingDeptId
  const options = departments
    .filter((department) => department.is_active && department.id !== effectiveCurrent)
    .map((department) => ({ value: String(department.id), label: department.name }))
  const canSubmit = reason.trim().length > 0 && (!isTransfer || deptId !== '')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isTransfer ? 'Chuyển phòng xử lý' : 'Trả về phòng lập'}</DialogTitle>
          <DialogDescription>
            {isTransfer
              ? `Đẩy cả ${docLabel} này sang phòng khác xử lý. Người phụ trách hiện tại ở mọi dòng sẽ được gỡ để phòng nhận phân công lại. Không chuyển một phần dòng.`
              : `Trả cả ${docLabel} này về phòng lập phiếu tự xử lý. Người phụ trách hiện tại ở mọi dòng sẽ được gỡ.`}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          {isTransfer && (
            <div className="grid gap-2">
              <Label>
                Phòng nhận xử lý
                <RequiredMark hint="Phải chọn phòng nhận" />
              </Label>
              <SearchSelect
                value={deptId}
                onChange={setDeptId}
                options={options}
                placeholder="Chọn phòng ban"
                searchPlaceholder="Tìm phòng ban..."
                emptyMessage="Không có phòng nào khác"
                className="w-full"
              />
            </div>
          )}
          <div className="grid gap-2">
            <Label htmlFor="transfer-dept-reason">
              Lý do
              <RequiredMark hint="Phải nêu lý do" />
            </Label>
            <Textarea
              id="transfer-dept-reason"
              rows={3}
              value={reason}
              placeholder="Ghi vào nhật ký phiếu, người lập và người phụ trách cũ đều đọc được"
              onChange={(event) => setReason(event.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
          <Button
            type="button"
            disabled={!canSubmit || pending}
            onClick={() => void onConfirm(isTransfer ? Number(deptId) : 0, reason.trim())}
          >
            {pending ? <Loader2 className="animate-spin" /> : isTransfer ? <ArrowRightLeft /> : <CornerUpLeft />}
            {isTransfer ? 'Chuyển phòng' : 'Trả về'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
