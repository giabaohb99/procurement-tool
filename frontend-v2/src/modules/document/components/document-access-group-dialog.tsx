import { useState } from 'react'

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
import { SubjectChips } from './access-subject-chips'
import type { DocumentAccessDraft, DocumentAccessInput } from '../types/document-access'

/** Phần khai lại được cho cả cụm — đối tượng và chiều tác động thì không. */
type GroupPatch = Pick<DocumentAccessInput, 'can_write' | 'can_delete' | 'valid_to' | 'reason'>

interface AccessGroupEditDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Cụm đang sửa là cụm KHÔNG CHO PHÉP — đổi chữ cho khỏi nhầm với cụm cho phép. */
  deny: boolean
  /**
   * CÁC DÒNG ĐANG CÓ trong cụm. Hộp mở ra phải hiện đúng thứ đã khai — cả bộ
   * quyền lẫn danh sách đối tượng.
   *
   * ⚠️ Trước 24/08/2026 hộp này chỉ nhận mỗi `count` và mở ra với form TRẮNG:
   * người dùng bấm «Sửa» để xem lại mình đã cho những ai, được làm gì, hạn tới
   * bao giờ — và thấy một form rỗng y như khai mới. Bấm «Áp cho cả cụm» là ghi
   * đè hết bằng giá trị trắng đó.
   */
  rows: DocumentAccessDraft[]
  onApply: (patch: GroupPatch) => void
}

/**
 * Sửa BỘ QUYỀN của cả một cụm (cho phép / không cho phép).
 *
 * Chỉ sửa được phần dùng chung: được làm gì, hết hạn, lý do. Muốn đổi đối tượng
 * thì bỏ badge rồi khai lại; muốn đổi chiều tác động thì đó là cụm khác — hai
 * việc đó nằm ngoài đây cho khỏi biến hộp này thành form khai mới thứ hai.
 */
export function AccessGroupEditDialog({
  open,
  onOpenChange,
  deny,
  rows,
  onApply,
}: AccessGroupEditDialogProps) {
  //  Cả cụm dùng chung một bộ quyền nên đọc ở dòng đầu là đủ — cùng cách đọc
  //  với dòng tóm tắt bên ngoài (`AccessGroup`).
  const hienTai = rows[0]?.values

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Sửa quyền cụm {deny ? 'không cho phép' : 'cho phép'}</DialogTitle>
          <DialogDescription>
            Áp cho cả {rows.length} đối tượng trong cụm. Muốn khác nhau thì tách thành cụm riêng.
          </DialogDescription>
        </DialogHeader>

        {/*  Hiện luôn ĐANG ÁP CHO AI. Con số "3 đối tượng" không đủ để rà lại
             trước khi ghi đè — người ta bấm Sửa chính là để xem lại danh sách. */}
        {rows.length > 0 && (
          <div className="space-y-1.5">
            <Label>Đang áp cho</Label>
            <SubjectChips
              items={rows.map((row) => ({
                key: `${row.values.subject_kind}-${row.values.subject_id}`,
                label: row.subjectLabel || '(chưa rõ tên)',
              }))}
            />
          </div>
        )}

        {/* Ô nhập nằm trong component con nên đóng hộp là chữ đã gõ tự mất.
            `key` đổi theo cụm để mở cụm khác là nạp lại đúng giá trị của cụm đó. */}
        <GroupForm
          key={deny ? 'deny' : 'allow'}
          deny={deny}
          hienTai={hienTai}
          onCancel={() => onOpenChange(false)}
          onApply={onApply}
        />
      </DialogContent>
    </Dialog>
  )
}

interface GroupFormProps {
  deny: boolean
  /** Bộ quyền đang áp cho cụm — mở hộp ra là thấy đúng nó, không phải form trắng. */
  hienTai?: DocumentAccessInput
  onCancel: () => void
  onApply: (patch: GroupPatch) => void
}

function GroupForm({ deny, hienTai, onCancel, onApply }: GroupFormProps) {
  const [canWrite, setCanWrite] = useState(hienTai?.can_write ?? false)
  const [canDelete, setCanDelete] = useState(hienTai?.can_delete ?? false)
  const [validTo, setValidTo] = useState(hienTai?.valid_to ?? '')
  const [reason, setReason] = useState(hienTai?.reason ?? '')

  return (
    <>
      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Được làm gì</Label>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox checked disabled />
              Xem {deny && '(chặn cả việc nhìn thấy)'}
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

        <div className="space-y-2">
          <Label>Hết hạn</Label>
          <DatePicker value={validTo} onChange={setValidTo} />
          <p className="text-xs text-muted-foreground">Trống = không đặt hạn.</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="group-reason">Lý do</Label>
          <Input
            id="group-reason"
            placeholder="VD: Phối hợp rà soát quy chế"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </div>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Hủy
        </Button>
        <Button
          type="button"
          onClick={() =>
            onApply({
              can_write: canWrite,
              can_delete: canDelete,
              valid_to: validTo || null,
              reason: reason.trim(),
            })
          }
        >
          Áp cho cả cụm
        </Button>
      </DialogFooter>
    </>
  )
}
