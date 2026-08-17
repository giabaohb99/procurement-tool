import { AlertTriangle } from 'lucide-react'
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
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import { useCreateClones } from '../hooks/use-document-clones'
import type { PendingCompany } from '../types/document-clone'

interface DocumentCloneDialogProps {
  documentId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Chỉ pháp nhân CHƯA nhận bản clone nào — mỗi nơi nhận đúng một bản. */
  companies: PendingCompany[]
}

/**
 * CLONE XUỐNG PHÁP NHÂN CON (F06, F09).
 *
 * Nói thẳng ba việc sẽ xảy ra thay vì để người dùng đoán: mỗi nơi được một bản
 * nháp riêng, mỗi bản mang số hiệu của chính pháp nhân đó, và người phụ trách
 * nhận thông báo kèm hạn xử lý.
 *
 * Ba dòng đó không phải trang trí — chúng là ba trong bốn điều kiện bắt buộc để
 * clone không biến thành 12 bản lệch nhau sau hai năm.
 */
export function DocumentCloneDialog({
  documentId,
  open,
  onOpenChange,
  companies,
}: DocumentCloneDialogProps) {
  const createClones = useCreateClones(documentId)
  const [picked, setPicked] = useState<number[]>([])
  const [dueDate, setDueDate] = useState('')
  const [note, setNote] = useState('')

  function toggle(companyId: number) {
    setPicked((truoc) =>
      truoc.includes(companyId)
        ? truoc.filter((id) => id !== companyId)
        : [...truoc, companyId],
    )
  }

  function handleCreate() {
    createClones.mutate(
      { company_ids: picked, due_date: dueDate || null, note: note.trim() },
      {
        onSuccess: () => {
          onOpenChange(false)
          setPicked([])
          setDueDate('')
          setNote('')
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Clone xuống pháp nhân con</DialogTitle>
          <DialogDescription>
            Mỗi pháp nhân được một bản nháp riêng, chép sẵn nội dung và tệp đính kèm.
            Họ để nguyên nếu dùng được, hoặc soạn lại cho đúng pháp nhân mình.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>
              Pháp nhân nhận<span className="text-destructive"> *</span>
            </Label>
            {companies.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Mọi pháp nhân đều đã có bản clone của văn bản này.
              </p>
            ) : (
              <ul className="max-h-56 space-y-2 overflow-y-auto rounded-md border p-3">
                {companies.map((company) => (
                  <li key={company.company_id} className="flex items-center gap-3">
                    <Checkbox
                      id={`clone-company-${company.company_id}`}
                      checked={picked.includes(company.company_id)}
                      onCheckedChange={() => toggle(company.company_id)}
                    />
                    <Label
                      htmlFor={`clone-company-${company.company_id}`}
                      className="font-normal"
                    >
                      {company.company_name}
                    </Label>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="space-y-2">
            <Label>Hạn xử lý</Label>
            <DatePicker value={dueDate} onChange={setDueDate} />
            <p className="text-xs text-muted-foreground">
              Hiện trong thư báo và trên bảng theo dõi.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="clone-note">Ghi chú cho pháp nhân nhận</Label>
            <Textarea
              id="clone-note"
              rows={2}
              placeholder="VD: Giữ nguyên Điều 1–4, chỉ sửa hạn mức ở Điều 5 cho đúng quy mô công ty."
              value={note}
              onChange={(event) => setNote(event.target.value)}
            />
          </div>

          <ul className="space-y-1 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <li className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
              <span>Mỗi bản clone mang <b>số hiệu riêng của pháp nhân con</b>, không dùng lại số của Tập đoàn.</span>
            </li>
            <li className="pl-6">
              Liên kết ngược về bản gốc <b>không xóa được</b> — để sau này còn truy ra bản nào từ đâu.
            </li>
            <li className="pl-6">
              Bản gốc lên phiên bản mới thì mọi bản clone <b>tự động bị đánh dấu cần rà lại</b>.
            </li>
          </ul>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={picked.length === 0 || createClones.isPending}
            onClick={handleCreate}
          >
            Tạo {picked.length > 0 ? `${picked.length} ` : ''}bản nháp
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
