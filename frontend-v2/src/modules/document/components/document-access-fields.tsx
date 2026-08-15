import { ChevronDown, Pencil, ShieldCheck, UserPlus } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { EFFECT, type DocumentAccessDraft } from '../types/document-access'
import { SubjectChips } from './access-subject-chips'
import { DocumentAccessDialog } from './document-access-dialog'
import { AccessGroupEditDialog } from './document-access-group-dialog'

/** Một dòng quyền đang xếp hàng chờ — xem `DocumentAccessDraft`. */
export type PendingAccess = DocumentAccessDraft

interface DocumentAccessFieldsProps {
  rows: PendingAccess[]
  onChange: (rows: PendingAccess[]) => void
  /** Tên sổ đang chọn ở ô "Vào sổ" phía trên — trống nghĩa là không vào sổ nào. */
  bookName?: string
}

/**
 * PHÂN QUYỀN TRUY CẬP, nằm ở CUỐI thẻ thông tin chính của form tạo văn bản.
 *
 * Mặc định chỉ là MỘT DÒNG tóm tắt: phần lớn văn bản dùng đúng quyền mặc định
 * (phạm vi vai trò + thành viên sổ), bày sẵn cả bảng ra chỉ làm form dài thêm
 * mà chín trên mười lần không ai đụng tới. Ai cần mới bấm "Phân quyền nâng
 * cao".
 *
 * Khai ngay lúc tạo chứ không để tạo xong rồi vào tab Thông tin sửa: khoảng
 * giữa hai việc đó là lúc văn bản đã tồn tại mà chưa ai chặn — với văn bản mật
 * thì đó đúng là khoảng hở. Các dòng khai ở đây **xếp hàng chờ**, gửi lên máy
 * chủ ngay sau khi văn bản được tạo.
 */
export function DocumentAccessFields({ rows, onChange, bookName }: DocumentAccessFieldsProps) {
  const [open, setOpen] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  //  Đang sửa quyền của cụm nào (`EFFECT.allow` / `EFFECT.deny`), `null` = đóng.
  const [editing, setEditing] = useState<number | null>(null)

  const allowRows = rows.filter((row) => row.values.effect === EFFECT.allow)
  const denyRows = rows.filter((row) => row.values.effect === EFFECT.deny)

  function add(added: PendingAccess[]) {
    //  Khai lại đúng đối tượng nào thì THAY dòng cũ của nó, không xếp hai dòng
    //  chọi nhau cho cùng một người.
    const key = (row: PendingAccess) => `${row.values.subject_kind}-${row.values.subject_id}`
    const replaced = new Set(added.map(key))
    onChange([...rows.filter((row) => !replaced.has(key(row))), ...added])
    setDialogOpen(false)
  }

  return (
    <div className="mt-1 border-t border-dashed pt-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-sm font-medium">
            <ShieldCheck className="size-4 text-muted-foreground" />
            Quyền truy cập
            {rows.length > 0 && (
              <span className="text-xs font-normal text-muted-foreground tabular-nums">
                · {rows.length} dòng khai thêm
              </span>
            )}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Mặc định: người có phạm vi vai trò bao trùm văn bản
            {bookName ? (
              <>
                {' '}
                và mọi thành viên của sổ <span className="font-medium">{bookName}</span>
              </>
            ) : (
              <> — chọn ô Vào sổ ở trên thì cả sổ đó đọc được</>
            )}
            .
          </p>
        </div>

        <Button type="button" variant="outline" size="sm" onClick={() => setOpen(!open)}>
          <ShieldCheck className="size-4" />
          Phân quyền nâng cao
          <ChevronDown className={cn('size-4 transition-transform', open && 'rotate-180')} />
        </Button>
      </div>

      {open && (
        <div className="mt-3 space-y-3 rounded-lg border bg-muted/30 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-muted-foreground">
              Mở thêm cho người ngoài phạm vi, hoặc chặn đích danh.{' '}
              <span className="font-medium text-foreground">Cấm</span> thắng tất cả — kể cả người
              trong sổ và người có phạm vi vai trò.
            </p>
            {/* MỘT nút: chiều tác động (cho phép / cấm) chọn ngay trong hộp,
                cùng lượt với danh sách đối tượng. Tách hai nút ở đây là hỏi
                cùng một câu ở hai chỗ. */}
            <Button type="button" variant="outline" size="sm" onClick={() => setDialogOpen(true)}>
              <UserPlus className="size-4" />
              Thêm quyền
            </Button>
          </div>

          {rows.length === 0 ? (
            <p className="rounded-md border border-dashed bg-background px-3 py-4 text-center text-xs text-muted-foreground">
              Chưa khai dòng nào — văn bản chạy đúng quyền mặc định ở trên.
            </p>
          ) : (
            <div className="space-y-4 rounded-md border bg-background p-3">
              <AccessGroup
                title="Cho phép"
                rows={allowRows}
                onEdit={() => setEditing(EFFECT.allow)}
                onRemove={(row) => onChange(rows.filter((item) => item !== row))}
              />
              <AccessGroup
                title="Không cho phép"
                rows={denyRows}
                onEdit={() => setEditing(EFFECT.deny)}
                onRemove={(row) => onChange(rows.filter((item) => item !== row))}
              />
            </div>
          )}
        </div>
      )}

      <DocumentAccessDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        existing={rows}
        onSubmit={add}
      />

      <AccessGroupEditDialog
        open={editing !== null}
        onOpenChange={(isOpen) => !isOpen && setEditing(null)}
        deny={editing === EFFECT.deny}
        count={(editing === EFFECT.deny ? denyRows : allowRows).length}
        onApply={(patch) => {
          //  Áp bộ quyền mới cho MỌI dòng trong cụm — sửa từng dòng một thì
          //  cụm mười người là mười lần khai lại y hệt nhau.
          onChange(
            rows.map((row) =>
              row.values.effect === editing ? { ...row, values: { ...row.values, ...patch } } : row,
            ),
          )
          setEditing(null)
        }}
      />
    </div>
  )
}

interface AccessGroupProps {
  title: string
  rows: PendingAccess[]
  onEdit: () => void
  onRemove: (row: PendingAccess) => void
}

/**
 * Một CỤM quyền — dải badge, mỗi đối tượng một chip xóa được.
 *
 * Giống hệt dải chip trong hộp chia quyền (dùng chung `SubjectChips`): khai ở
 * hộp thấy chip, đóng hộp ra ngoài vẫn thấy đúng những chip đó, không phải học
 * hai cách đọc cho cùng một dữ liệu. Bộ quyền dùng chung của cụm nằm ở dòng
 * tiêu đề, sửa cho cả cụm bằng nút bên phải.
 */
function AccessGroup({ title, rows, onEdit, onRemove }: AccessGroupProps) {
  if (rows.length === 0) return null

  //  Cả cụm dùng chung một bộ quyền nên đọc ở dòng đầu là đủ.
  const sample = rows[0].values
  const abilities = ['xem', sample.can_write && 'sửa', sample.can_delete && 'xóa']
    .filter(Boolean)
    .join(' · ')

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium">
          {title}
          <span className="ml-2 font-normal text-muted-foreground">
            {rows.length} đối tượng · {abilities}
            {sample.valid_to && ` · hết hạn ${formatDate(sample.valid_to)}`}
            {sample.reason && ` · ${sample.reason}`}
          </span>
        </p>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-6 shrink-0 px-2 text-xs text-muted-foreground hover:text-foreground"
          onClick={onEdit}
        >
          <Pencil className="size-3.5" />
          Sửa
        </Button>
      </div>

      <SubjectChips
        items={rows.map((row) => ({
          key: `${row.values.subject_kind}-${row.values.subject_id}`,
          label: row.subjectLabel || '(chưa rõ tên)',
        }))}
        onRemove={(key) => {
          const row = rows.find(
            (item) => `${item.values.subject_kind}-${item.values.subject_id}` === key,
          )
          if (row) onRemove(row)
        }}
      />
    </div>
  )
}
