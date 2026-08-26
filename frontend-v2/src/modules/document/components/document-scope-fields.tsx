import { Building2, MinusCircle, PlusCircle, User, Users, X } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { onlyExcludeRows } from '../helpers/scope-only-exclude'
import { SCOPE_DIM, SCOPE_MODE, type PendingScope } from '../types/document-scope'
import { DocumentScopeAddForm } from './document-scope-add-form'
import { DocumentScopeOnlyExcludeNotice } from './document-scope-only-exclude-notice'

export type { PendingScope }

/** Khóa nhận diện một dòng phạm vi — hai dòng cùng khóa là khai trùng. */
function duplicateKey({ values }: PendingScope): string {
  return [
    values.dim,
    values.mode,
    values.company_id ?? '',
    values.department_id ?? '',
    values.employee_id ?? '',
  ].join('|')
}

interface DocumentScopeFieldsProps {
  rows: PendingScope[]
  onChange: (rows: PendingScope[]) => void
}

/**
 * PHẠM VI ÁP DỤNG khai ngay ở form TẠO văn bản (F01–F04).
 *
 * **Bỏ trống là xong việc** với phần lớn văn bản: không khai dòng nào thì văn
 * bản áp cho toàn bộ pháp nhân ban hành — mọi phòng ban, mọi nhân sự ở đó. Khối
 * này chỉ cần đụng tới khi muốn đi XA HƠN (pháp nhân khác) hoặc HẸP LẠI (một
 * phòng ban, một người, hoặc trừ ai đó ra).
 *
 * Các dòng khai ở đây **xếp hàng chờ** trong bộ nhớ, gửi lên máy chủ ngay sau
 * khi văn bản được tạo — giống hệt cách khối quyền truy cập làm.
 */
export function DocumentScopeFields({ rows, onChange }: DocumentScopeFieldsProps) {
  return (
    <div className="space-y-4">
      {/*  Nói rõ cái sẽ xảy ra khi bỏ trống — người dùng bước qua bước này nhiều
           hơn hẳn số lần dừng lại khai, nên câu này phải đọc là yên tâm đi tiếp. */}
      {rows.length === 0 && (
        <div className="flex gap-3 rounded-md border bg-muted/40 px-4 py-3">
          <Building2 className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div className="text-sm">
            <p className="font-medium">
              Bỏ trống được — mặc định áp cho toàn bộ pháp nhân ban hành.
            </p>
            <p className="text-muted-foreground">
              Mọi phòng ban, mọi nhân sự của pháp nhân đứng tên văn bản đều thấy nó
              trong mục «Văn bản áp dụng cho tôi». Chỉ khai thêm dòng khi cần đi xa
              hơn (pháp nhân khác) hoặc hẹp lại (một phòng ban, một người).
            </p>
          </div>
        </div>
      )}

      {/*  Ghi chú "bỏ trống được" ở trên biến mất ngay khi có dòng đầu tiên. Nếu
           dòng đó lại là loại trừ thì màn hình không còn nói gì cả, trong khi
           người dùng vừa vô tình khai ra một văn bản không tới ai. */}
      {onlyExcludeRows(rows.map((row) => row.values.mode)) && (
        <DocumentScopeOnlyExcludeNotice />
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
        onAdd={(them) => {
          //  Khai trùng y hệt một dòng đã có thì bỏ qua: backend trả lỗi "Dòng
          //  phạm vi này đã khai rồi", mà lỗi đó chỉ nổ ra sau khi văn bản đã
          //  được tạo — lúc người dùng không còn ở đây để sửa.
          //
          //  Lọc trùng bằng `Set` khóa chuỗi, và cho khóa của các dòng MỚI vào
          //  luôn: một mẻ có thể chứa hai dòng y hệt nhau, so với `rows` không
          //  thôi thì cả hai cùng lọt.
          const existing = new Set(rows.map((item) => duplicateKey(item)))
          const canAdd: PendingScope[] = []
          for (const item of them) {
            const khoa = duplicateKey(item)
            if (existing.has(khoa)) continue
            existing.add(khoa)
            canAdd.push(item)
          }

          //  Ghi state ĐÚNG MỘT LẦN cho cả mẻ. Gọi `onChange` trong vòng lặp là
          //  lỗi cũ: `rows` đọc qua closure không đổi giữa các lượt nên lượt
          //  cuối ghi đè hết — chọn 13 pháp nhân chỉ còn 1 dòng.
          if (canAdd.length > 0) onChange([...rows, ...canAdd])
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
