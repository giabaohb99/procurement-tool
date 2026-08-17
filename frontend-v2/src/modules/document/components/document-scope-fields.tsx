import { AlertTriangle, Building2, MinusCircle, PlusCircle, User, Users, X } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { SCOPE_DIM, SCOPE_MODE, type DocumentScopeInput } from '../types/document-scope'
import { DocumentScopeAddForm } from './document-scope-add-form'

/** Một dòng phạm vi đang xếp hàng chờ — gửi lên ngay sau khi văn bản được tạo. */
export interface PendingScope {
  values: DocumentScopeInput
  /** Tên đọc được, do form thêm dòng dựng sẵn — xem `scopeLabel`. */
  label: string
}

interface DocumentScopeFieldsProps {
  rows: PendingScope[]
  onChange: (rows: PendingScope[]) => void
}

/**
 * PHẠM VI ÁP DỤNG khai ngay ở form TẠO văn bản (F01–F04).
 *
 * Khai ở đây thay vì đợi tạo xong rồi vào tab riêng, vì quy tắc của hệ là
 * *không khai gì = không ai thuộc phạm vi* — ngược hẳn trực giác. Ai chưa biết
 * luật đó sẽ tạo xong rồi đi làm việc khác, và văn bản ban hành ra không tới ai
 * mà không có gì báo. Hỏi ngay lúc lập là lúc duy nhất chắc chắn người ta còn
 * đang nghĩ về văn bản này.
 *
 * Các dòng khai ở đây **xếp hàng chờ** trong bộ nhớ, gửi lên máy chủ ngay sau
 * khi văn bản được tạo — giống hệt cách khối quyền truy cập làm.
 */
export function DocumentScopeFields({ rows, onChange }: DocumentScopeFieldsProps) {
  return (
    <div className="space-y-4">
      {/*  Băng cảnh báo là phần quan trọng nhất của khối này, và nó phải hiện
           NGAY khi chưa khai dòng nào chứ không đợi bấm gửi. */}
      {rows.length === 0 && (
        <div className="flex gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
          <div className="text-sm text-amber-900">
            <p className="font-medium">Chưa khai dòng nào — văn bản này sẽ không tới ai.</p>
            <p className="text-amber-800">
              Để trống KHÔNG có nghĩa là áp cho mọi người. Khai ít nhất một dòng bao
              gồm thì văn bản mới hiện trong mục «Văn bản áp dụng cho tôi» của người
              thuộc phạm vi. Bỏ qua bước này cũng được — khai lại sau ở tab Phạm vi.
            </p>
          </div>
        </div>
      )}

      {rows.length > 0 && (
        <ul className="divide-y rounded-md border px-3">
          {rows.map((row, index) => (
            <PendingScopeRow
              key={`${row.values.dim}-${row.values.mode}-${row.label}-${index}`}
              row={row}
              onRemove={() => onChange(rows.filter((item) => item !== row))}
            />
          ))}
        </ul>
      )}

      <DocumentScopeAddForm
        onAdd={(values, label) => {
          //  Khai trùng y hệt một dòng đã có thì bỏ qua: backend trả lỗi "Dòng
          //  phạm vi này đã khai rồi", mà lỗi đó chỉ nổ ra sau khi văn bản đã
          //  được tạo — lúc người dùng không còn ở đây để sửa.
          const trung = rows.some(
            (item) =>
              item.values.dim === values.dim &&
              item.values.mode === values.mode &&
              item.values.company_id === values.company_id &&
              item.values.department_id === values.department_id &&
              item.values.employee_id === values.employee_id,
          )
          if (!trung) onChange([...rows, { values, label }])
        }}
      />
    </div>
  )
}

/** Cùng cách đọc với `DocumentScopeRow` ở trang chi tiết, chỉ khác là chưa lưu. */
function PendingScopeRow({ row, onRemove }: { row: PendingScope; onRemove: () => void }) {
  const isExclude = row.values.mode === SCOPE_MODE.exclude
  const Icon =
    row.values.dim === SCOPE_DIM.company
      ? Building2
      : row.values.dim === SCOPE_DIM.department
        ? Users
        : User

  return (
    <li className="flex items-center gap-3 py-2">
      {isExclude ? (
        <MinusCircle className="size-4 shrink-0 text-destructive" />
      ) : (
        <PlusCircle className="size-4 shrink-0 text-muted-foreground" />
      )}

      <Icon className="size-4 shrink-0 text-muted-foreground" />

      <div className="min-w-0 flex-1">
        <p className="text-sm">{row.label || '(chưa rõ tên)'}</p>
        {row.values.include_children && (
          <p className="text-xs text-muted-foreground">
            Gồm cả đơn vị con — kể cả công ty mở sau này
          </p>
        )}
      </div>

      {isExclude && <Badge variant="destructive">Loại trừ</Badge>}

      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-7 text-muted-foreground hover:text-destructive"
        title="Bỏ dòng này"
        aria-label="Bỏ dòng này"
        onClick={onRemove}
      >
        <X className="size-4" />
      </Button>
    </li>
  )
}
