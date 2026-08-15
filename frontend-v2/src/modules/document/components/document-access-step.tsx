import { Ban, ShieldCheck, UserMinus, UserPlus, X } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'
import { EFFECT, SUBJECT_KIND_LABELS, type DocumentAccessInput } from '../types/document-access'
import { DocumentAccessDialog } from './document-access-dialog'

/** Một dòng quyền đang xếp hàng chờ, kèm tên đối tượng để hiện ra cho người khai. */
export interface PendingAccess {
  values: DocumentAccessInput
  subjectLabel: string
}

interface DocumentAccessStepProps {
  rows: PendingAccess[]
  onChange: (rows: PendingAccess[]) => void
  /** Tên sổ đang chọn ở ô "Vào sổ" phía trên — trống nghĩa là không vào sổ nào. */
  bookName?: string
}

/**
 * Khối PHÂN QUYỀN TRUY CẬP, nằm ngay dưới thông tin chính của form tạo văn bản.
 *
 * Khai ngay lúc tạo chứ không để tạo xong rồi vào tab Thông tin sửa: khoảng
 * giữa hai việc đó là lúc văn bản đã tồn tại mà chưa ai chặn — với văn bản mật
 * thì đó đúng là khoảng hở. Các dòng khai ở đây **xếp hàng chờ**, gửi lên máy
 * chủ ngay sau khi văn bản được tạo.
 *
 * Ba nguồn quyền, nói rõ trên màn hình để người khai biết mình đang thêm gì vào
 * cái gì (chi tiết ở `access_service.py`):
 *  1. phạm vi vai trò — có sẵn, không khai ở đây;
 *  2. **thành viên sổ** — chọn sổ ở ô "Vào sổ" là cả sổ đọc được, khỏi khai tay;
 *  3. hai cụm dưới đây — mở thêm cho người ngoài, hoặc chặn đích danh.
 */
export function DocumentAccessStep({ rows, onChange, bookName }: DocumentAccessStepProps) {
  //  `null` = đóng; số = đang mở hộp khai cho chiều tác động đó.
  const [dialogEffect, setDialogEffect] = useState<number | null>(null)

  const allowRows = rows.filter((row) => row.values.effect === EFFECT.allow)
  const denyRows = rows.filter((row) => row.values.effect === EFFECT.deny)

  function add(values: DocumentAccessInput, subjectLabel: string) {
    //  Khai lại đúng đối tượng đó thì thay dòng cũ, không xếp hai dòng chọi nhau.
    const rest = rows.filter(
      (row) =>
        !(
          row.values.subject_kind === values.subject_kind &&
          row.values.subject_id === values.subject_id
        ),
    )
    onChange([...rest, { values, subjectLabel }])
    setDialogEffect(null)
  }

  return (
    <div className="space-y-5">
      <div className="rounded-md border bg-muted/40 px-4 py-3 text-sm">
        <p className="flex items-center gap-2 font-medium">
          <ShieldCheck className="size-4 text-primary" />
          Ai thấy văn bản này
        </p>
        <ul className="mt-2 space-y-1 text-muted-foreground">
          <li>· Người có phạm vi vai trò bao trùm văn bản (mặc định, không cần khai).</li>
          <li>
            ·{' '}
            {bookName ? (
              <>
                Mọi thành viên của sổ <span className="font-medium">{bookName}</span> — do ô{' '}
                <span className="font-medium">Vào sổ</span> ở trên đã chọn sổ này.
              </>
            ) : (
              <>
                Thành viên của sổ, nếu ô <span className="font-medium">Vào sổ</span> ở trên có chọn.
              </>
            )}
          </li>
          <li>· Người được chỉ định thêm bên dưới.</li>
        </ul>
        <p className="mt-2 text-xs text-muted-foreground">
          Dòng <span className="font-medium">Loại trừ</span> thắng tất cả những dòng trên — kể cả
          người trong sổ và người có phạm vi vai trò.
        </p>
      </div>

      <AccessGroup
        title="Chỉ định thêm người xem"
        hint="Mở cho người vốn không thuộc phạm vi vai trò hay sổ nào của văn bản này."
        icon={UserPlus}
        rows={allowRows}
        emptyText="Chưa chỉ định thêm ai."
        onAdd={() => setDialogEffect(EFFECT.allow)}
        onRemove={(row) => onChange(rows.filter((item) => item !== row))}
      />

      <AccessGroup
        title="Loại trừ người"
        hint="Chặn đích danh một người vốn đang xem được — họ không còn thấy văn bản trong danh sách."
        icon={UserMinus}
        destructive
        rows={denyRows}
        emptyText="Chưa loại trừ ai."
        onAdd={() => setDialogEffect(EFFECT.deny)}
        onRemove={(row) => onChange(rows.filter((item) => item !== row))}
      />

      <DocumentAccessDialog
        open={dialogEffect !== null}
        onOpenChange={(open) => !open && setDialogEffect(null)}
        defaultEffect={dialogEffect ?? EFFECT.allow}
        onSubmit={add}
      />
    </div>
  )
}

interface AccessGroupProps {
  title: string
  hint: string
  icon: typeof UserPlus
  destructive?: boolean
  rows: PendingAccess[]
  emptyText: string
  onAdd: () => void
  onRemove: (row: PendingAccess) => void
}

/** Một cụm (chỉ định thêm / loại trừ) — cùng bố cục, chỉ khác màu và chữ. */
function AccessGroup({
  title,
  hint,
  icon: Icon,
  destructive = false,
  rows,
  emptyText,
  onAdd,
  onRemove,
}: AccessGroupProps) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="flex items-center gap-2 text-sm font-medium">
            <Icon className={destructive ? 'size-4 text-destructive' : 'size-4 text-primary'} />
            {title}
            {rows.length > 0 && <Badge variant="secondary">{rows.length}</Badge>}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={onAdd}>
          <Icon className="size-4" />
          Thêm
        </Button>
      </div>

      {rows.length === 0 ? (
        <p className="rounded-md border border-dashed px-3 py-3 text-xs text-muted-foreground">
          {emptyText}
        </p>
      ) : (
        <ul className="divide-y rounded-md border">
          {rows.map((row) => (
            <li
              key={`${row.values.subject_kind}-${row.values.subject_id}`}
              className="flex flex-wrap items-center gap-2 px-3 py-2 text-sm"
            >
              {destructive && <Ban className="size-3.5 shrink-0 text-destructive" />}
              <span className="font-medium">{row.subjectLabel || '(chưa rõ tên)'}</span>
              <Badge variant="outline">{SUBJECT_KIND_LABELS[row.values.subject_kind]}</Badge>
              <span className="text-xs text-muted-foreground">
                {['xem', row.values.can_write && 'sửa', row.values.can_delete && 'xóa']
                  .filter(Boolean)
                  .join(' · ')}
                {row.values.valid_to && ` · hết hạn ${formatDate(row.values.valid_to)}`}
                {row.values.reason && ` · ${row.values.reason}`}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="ml-auto size-7"
                title={`Bỏ ${row.subjectLabel}`}
                aria-label={`Bỏ ${row.subjectLabel}`}
                onClick={() => onRemove(row)}
              >
                <X className="size-4" />
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
