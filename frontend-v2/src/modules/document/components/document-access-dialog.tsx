import { useState } from 'react'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useRoles } from '@/modules/hr/hooks/use-roles'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import {
  EFFECT,
  SUBJECT_KIND,
  SUBJECT_KIND_LABELS,
  type DocumentAccessInput,
} from '../types/document-access'

interface DocumentAccessDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Chiều tác động lúc mở hộp — trang tạo văn bản mở sẵn đúng cụm người bấm. */
  defaultEffect?: number
  pending?: boolean
  /**
   * Nhận dòng vừa khai. Trang chi tiết gửi thẳng lên máy chủ; trang TẠO văn bản
   * xếp hàng chờ vì lúc đó văn bản còn chưa có id.
   *
   * `subjectLabel` để nơi gọi hiện tên đối tượng mà không phải tra lại danh mục.
   */
  onSubmit: (values: DocumentAccessInput, subjectLabel: string) => void
}

/**
 * CHIA QUYỀN (hoặc CẤM) trên một văn bản.
 *
 * Cấp cho **bốn loại đối tượng**, không chỉ cá nhân: người · phòng ban · pháp
 * nhân · vai trò. Chia cho cả phòng mà phải chọn từng người thì người mới vào
 * phòng không có quyền còn người chuyển đi vẫn còn — hai hành vi sai mà người
 * chia không hề chọn.
 *
 * Ô **hạn** không bắt buộc nhưng nên đặt: hết ngày là tự mất quyền, không phải
 * trông vào việc có ai nhớ đi thu hồi hay không.
 */
export function DocumentAccessDialog({
  open,
  onOpenChange,
  defaultEffect = EFFECT.allow,
  pending = false,
  onSubmit,
}: DocumentAccessDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Chia quyền truy cập</DialogTitle>
          <DialogDescription>
            Mở thêm cho người ngoài phạm vi vai trò, hoặc chặn đích danh một người vốn đang xem
            được.
          </DialogDescription>
        </DialogHeader>

        {/* Ô nhập nằm trong component con nên đóng hộp là chữ đã khai tự mất —
            mở lại là một lần khai MỚI, khỏi phải tự dọn. */}
        <AccessForm
          defaultEffect={defaultEffect}
          pending={pending}
          onCancel={() => onOpenChange(false)}
          onSubmit={onSubmit}
        />
      </DialogContent>
    </Dialog>
  )
}

interface AccessFormProps {
  defaultEffect: number
  pending: boolean
  onCancel: () => void
  onSubmit: (values: DocumentAccessInput, subjectLabel: string) => void
}

function AccessForm({ defaultEffect, pending, onCancel, onSubmit }: AccessFormProps) {
  const [subjectKind, setSubjectKind] = useState(String(SUBJECT_KIND.employee))
  const [subjectId, setSubjectId] = useState('')
  const [effect, setEffect] = useState(String(defaultEffect))
  const [canWrite, setCanWrite] = useState(false)
  const [canDelete, setCanDelete] = useState(false)
  const [validTo, setValidTo] = useState('')
  const [reason, setReason] = useState('')

  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })
  const { data: companies } = useCompanies({ page_size: 200, is_active: true })
  const { data: roles } = useRoles()

  const options = (() => {
    switch (Number(subjectKind)) {
      case SUBJECT_KIND.department:
        return (departments?.items ?? [])
          .filter((item) => item.is_active)
          .map((item) => ({ id: item.id, label: item.name }))
      case SUBJECT_KIND.company:
        return (companies?.items ?? []).map((item) => ({ id: item.id, label: item.name }))
      case SUBJECT_KIND.role:
        return (roles ?? []).map((item) => ({ id: item.id, label: item.name }))
      default:
        return (employees?.items ?? []).map((item) => ({
          id: item.id,
          label: item.full_name,
        }))
    }
  })()

  function handleSubmit() {
    onSubmit(
      {
        subject_kind: Number(subjectKind),
        subject_id: Number(subjectId),
        effect: Number(effect),
        //  Cho phép mà không cho đọc là vô nghĩa; cấm mà không chặn đọc thì
        //  cũng chẳng cấm được gì. Nên `can_read` luôn bật.
        can_read: true,
        can_write: canWrite,
        can_delete: canDelete,
        valid_from: null,
        valid_to: validTo || null,
        reason: reason.trim(),
      },
      options.find((option) => String(option.id) === subjectId)?.label ?? '',
    )
  }

  const isDeny = Number(effect) === EFFECT.deny

  return (
    <>
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Loại đối tượng</Label>
            <Select
              value={subjectKind}
              onValueChange={(value) => {
                setSubjectKind(value)
                setSubjectId('')
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(SUBJECT_KIND_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>
              Chọn {SUBJECT_KIND_LABELS[Number(subjectKind)].toLowerCase()}
              <span className="text-destructive"> *</span>
            </Label>
            <Select value={subjectId} onValueChange={setSubjectId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chưa chọn" />
              </SelectTrigger>
              <SelectContent>
                {options.map((option) => (
                  <SelectItem key={option.id} value={String(option.id)}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Chiều tác động</Label>
          <RadioGroup value={effect} onValueChange={setEffect} className="sm:flex sm:gap-4">
            <label className="flex items-center gap-2 text-sm">
              <RadioGroupItem value={String(EFFECT.allow)} />
              Cho phép
            </label>
            <label className="flex items-center gap-2 text-sm">
              <RadioGroupItem value={String(EFFECT.deny)} />
              Cấm
            </label>
          </RadioGroup>
          <p className="text-xs text-muted-foreground">
            {isDeny
              ? 'Cấm thắng mọi dòng cho phép và thắng cả phạm vi vai trò — người bị cấm không còn thấy văn bản này trong danh sách.'
              : 'Người được chia sẽ thấy và mở được văn bản này kể cả khi nó nằm ngoài phạm vi vai trò của họ.'}
          </p>
        </div>

        <div className="space-y-2">
          <Label>Được làm gì</Label>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox checked disabled />
              Xem {isDeny && '(chặn cả việc nhìn thấy)'}
            </label>
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={canWrite}
                onCheckedChange={(value) => setCanWrite(value === true)}
              />
              Sửa
            </label>
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={canDelete}
                onCheckedChange={(value) => setCanDelete(value === true)}
              />
              Xóa
            </label>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Hết hạn</Label>
            <DatePicker value={validTo} onChange={setValidTo} />
            <p className="text-xs text-muted-foreground">Trống = không đặt hạn.</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="access-reason">Lý do</Label>
            <Input
              id="access-reason"
              placeholder="VD: Phối hợp rà soát quy chế"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </div>
        </div>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Hủy
        </Button>
        <Button type="button" onClick={handleSubmit} disabled={!subjectId || pending}>
          {isDeny ? 'Cấm truy cập' : 'Chia quyền'}
        </Button>
      </DialogFooter>
    </>
  )
}
