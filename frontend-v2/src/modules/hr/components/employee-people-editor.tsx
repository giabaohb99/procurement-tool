import { Loader2, Plus, Save, Trash2 } from 'lucide-react'
import { useId, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { EMPLOYEE_GENDER_OPTIONS } from '../types/employee'
import { MAX_PEOPLE_ROWS, RELATION_OPTIONS } from '../types/employee-codes'

/**
 * Bảng NGƯỜI GẮN VỚI HỒ SƠ — dùng chung cho *Người báo tin* và *Thành viên hộ
 * gia đình* (duoc-CR-314 Đợt 2).
 *
 * Một component cho hai bảng vì chúng khác nhau đúng ở DANH SÁCH CỘT; dựng hai
 * bản chép tay thì hai bản trôi khỏi nhau ngay ở cái nút Thêm dòng.
 *
 * ⚠️ **Đặt lại CẢ BẢNG một lượt** (`PUT`), không sửa từng dòng. Đây là bảng
 * ba–bốn dòng nằm trong một tab; nút Lưu của riêng nó, tách khỏi nút Lưu của hồ
 * sơ, vì hai thứ đi hai cửa API khác nhau và một cửa hỏng thì cửa kia vẫn phải
 * lưu được.
 *
 * ⚠️ Dòng để TRỐNG HỌ TÊN bị backend bỏ qua — cố ý, vì bảng luôn dựng sẵn một
 * dòng trống cho người dùng gõ vào. Ghi chú đó nói thành lời ở chân bảng, đừng
 * để người dùng gõ nửa dòng rồi thắc mắc sao lưu xong mất.
 */

export type PeopleFieldKind = 'text' | 'phone' | 'date' | 'gender' | 'relation'

export interface PeopleColumn<T> {
  key: keyof T & string
  label: string
  kind: PeopleFieldKind
  placeholder?: string
  /** Bề rộng tương đối trong lưới; mặc định 1. */
  span?: number
}

interface EmployeePeopleEditorProps<T extends { id: number }> {
  title: string
  description: string
  columns: PeopleColumn<T>[]
  rows: T[] | undefined
  isLoading: boolean
  /** Hàng rỗng để thêm mới — khai ở nơi gọi vì mỗi bảng một bộ cột. */
  emptyRow: () => T
  canWrite: boolean
  isSaving: boolean
  onSave: (rows: T[]) => void
  className?: string
}

export function EmployeePeopleEditor<T extends { id: number }>({
  title,
  description,
  columns,
  rows,
  isLoading,
  emptyRow,
  canWrite,
  isSaving,
  onSave,
  className,
}: EmployeePeopleEditorProps<T>) {
  const [draft, setDraft] = useState<T[]>(rows ?? [])

  //  Nạp lại nháp mỗi khi server trả bộ MỚI — khuôn "điều chỉnh state khi prop
  //  đổi" của React, cố ý KHÔNG dùng `useEffect`.
  //
  //  Với effect thì mỗi lần dữ liệu về là một lượt render thừa: React vẽ bảng
  //  bằng nháp CŨ, chạy effect, rồi vẽ lại — người dùng thấy dữ liệu cũ nhấp
  //  nháy một khung hình. So sánh ngay trong lúc render thì React bỏ luôn kết
  //  quả dở dang, không có khung hình nào bị vẽ sai.
  //
  //  So bằng THAM CHIẾU là đủ và là chủ ý: TanStack Query giữ nguyên tham chiếu
  //  của `data` giữa các lần render, chỉ đổi khi thực sự nạp lại — nên không có
  //  vòng lặp vô hạn. So sâu ở đây còn nguy hiểm hơn: nó sẽ nuốt mất lần nạp
  //  lại sau khi lưu, và mọi sửa đổi dở dang của người dùng lại được giữ lại
  //  dù server đã trả bộ khác.
  const [lastRows, setLastRows] = useState(rows)
  if (rows !== lastRows) {
    setLastRows(rows)
    setDraft(rows ?? [])
  }

  function updateCell(index: number, key: keyof T & string, value: unknown) {
    setDraft((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [key]: value } : row)),
    )
  }

  if (isLoading) {
    return (
      <Card className={cn('gap-4 p-5', className)}>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-24 w-full" />
      </Card>
    )
  }

  return (
    <Card className={cn('gap-4 p-5', className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <SectionHeading>{title}</SectionHeading>
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        </div>

        {canWrite && (
          <Button type="button" size="sm" onClick={() => onSave(draft)} disabled={isSaving}>
            {isSaving ? <Loader2 className="animate-spin" /> : <Save />}
            Lưu danh sách
          </Button>
        )}
      </div>

      {draft.length === 0 && (
        <p className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
          Chưa khai ai.
        </p>
      )}

      {/*  ⚠️ CHẶN «gửi biểu mẫu ngầm» của trình duyệt.

           Bảng này nằm BÊN TRONG `<form>` của màn hồ sơ. Gõ tên người báo tin
           rồi quen tay nhấn Enter là trình duyệt tự bấm nút submit đầu tiên —
           tức **lưu HỒ SƠ**, trong khi dòng đang gõ dở thì KHÔNG được lưu (nó
           đi một cửa API khác). Đã dựng lại được trên trình duyệt thật
           08/09/2026: một `PATCH /api/employees/{id}` chạy, toast báo «Đã cập
           nhật nhân sự», và người dùng tin rằng dòng vừa gõ đã lưu xong.

           Đó là kiểu lỗi tệ nhất: thao tác sai nhưng **báo thành công**.

           Enter ở đây cố ý KHÔNG làm gì — không lưu bảng, không thêm dòng.
           Đoán ý người dùng ở một phím bấm nhầm là đổi một lỗi im lặng lấy một
           lỗi khác. Muốn lưu thì có nút «Lưu danh sách» ngay trên đầu.

           Không chặn cho `<textarea>`: ở đó Enter là xuống dòng, trình duyệt
           vốn không submit. Bảng này chưa có ô nào như vậy, nhưng khai sẵn để
           lần sau thêm cột không phải nhớ lại. */}
      <div
        className="flex flex-col gap-3"
        onKeyDown={(event) => {
          if (event.key !== 'Enter') return
          if (event.target instanceof HTMLTextAreaElement) return
          event.preventDefault()
        }}
      >
        {draft.map((row, index) => (
          <div
            key={row.id || `moi-${index}`}
            className="grid items-end gap-3 rounded-md border p-3 md:grid-cols-12"
          >
            {columns.map((col) => (
              <PeopleField
                key={col.key}
                column={col}
                value={row[col.key]}
                disabled={!canWrite}
                onChange={(v) => updateCell(index, col.key, v)}
              />
            ))}

            {canWrite && (
              <div className="md:col-span-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={`Xóa dòng ${index + 1}`}
                  onClick={() => setDraft((prev) => prev.filter((_, i) => i !== index))}
                >
                  <Trash2 className="text-destructive" />
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>

      {canWrite && (
        <div className="flex flex-wrap items-center gap-3">
          {/*  ⚠️ Chặn NGAY Ở NÚT, không đợi backend.

               Backend có trần `MAX_PEOPLE_ROWS`, nhưng nó chỉ nói ra lúc bấm
               Lưu — và nói bằng tiếng Anh (`List should have at most 30 items
               after validation, not 35`). Dựng lại được 08/09/2026: thêm 35
               dòng, gõ hết, bấm Lưu, mất trắng công gõ. Trần phải nhìn thấy
               TRƯỚC khi gõ, không phải sau. */}
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={draft.length >= MAX_PEOPLE_ROWS}
            onClick={() => setDraft((prev) => [...prev, emptyRow()])}
          >
            <Plus />
            Thêm dòng
          </Button>
          <p className="text-xs text-muted-foreground">
            {draft.length >= MAX_PEOPLE_ROWS
              ? `Đã đủ ${MAX_PEOPLE_ROWS} dòng, không thêm được nữa.`
              : `Dòng chưa có họ tên sẽ không được lưu. Tối đa ${MAX_PEOPLE_ROWS} dòng.`}
          </p>
        </div>
      )}
    </Card>
  )
}

interface PeopleFieldProps<T> {
  column: PeopleColumn<T>
  value: unknown
  disabled: boolean
  onChange: (value: unknown) => void
}

/**
 * Một ô kèm NHÃN NỐI ĐÚNG vào ô nhập.
 *
 * ⚠️ `<label>` trần không nối với gì cả — nhãn hiện ra bằng mắt nhưng trình đọc
 * màn hình đọc ô đó là "textbox" không tên, và bấm vào chữ không nhảy được vào
 * ô. Bảng này có 5 cột × N dòng nên lỗi nhân lên rất nhanh. `useId` cho mỗi ô
 * một id thật, kể cả khi cùng một cột xuất hiện ở nhiều dòng.
 */
function PeopleField<T>({ column, value, disabled, onChange }: PeopleFieldProps<T>) {
  const id = useId()

  return (
    <div className="flex flex-col gap-1.5" style={{ gridColumn: `span ${column.span ?? 3}` }}>
      <label htmlFor={id} className="text-xs font-medium text-muted-foreground">
        {column.label}
      </label>
      <PeopleCell
        id={id}
        kind={column.kind}
        value={value}
        placeholder={column.placeholder}
        disabled={disabled}
        onChange={onChange}
      />
    </div>
  )
}

interface PeopleCellProps {
  id: string
  kind: PeopleFieldKind
  value: unknown
  placeholder?: string
  disabled: boolean
  onChange: (value: unknown) => void
}

function PeopleCell({ id, kind, value, placeholder, disabled, onChange }: PeopleCellProps) {
  //  Hai kiểu ô CHỌN dùng chung một khối: khác nhau đúng ở bộ mục.
  //
  //  ⚠️ «Quan hệ» từng là ô gõ tay. Khách chốt thành ô chọn 08/09/2026 vì chữ
  //  tự do làm mỗi người gõ một kiểu — «vợ» · «Vợ» · «v/c» · «vo» — nên không
  //  lọc được, không đếm được, và bản in ra không đều. Cột cũng đổi sang
  //  SMALLINT theo R2/QĐ-11.
  if (kind === 'gender' || kind === 'relation') {
    const options = kind === 'gender' ? EMPLOYEE_GENDER_OPTIONS : RELATION_OPTIONS
    return (
      <Select
        value={String((value as number) ?? 0)}
        onValueChange={(v) => onChange(Number(v))}
        disabled={disabled}
      >
        <SelectTrigger id={id} className="w-full">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map((item) => (
            <SelectItem key={item.value} value={String(item.value)}>
              {/*  Mục `0` là «chưa khai» — nhãn của nó rỗng, nên phải mượn
                   `placeholder` của cột, không thì ô chọn có một dòng trắng
                   không ai biết bấm vào để làm gì. */}
              {item.value === 0 ? (placeholder ?? '— Chưa khai —') : item.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    )
  }

  if (kind === 'date') {
    return (
      <DatePicker
        id={id}
        //  Cột ngày là `DATE NULL` nên API trả `null` cho ô chưa khai; ô ngày
        //  nhận `null` là hiện lỗi ngay khi mở ra, chưa gõ gì.
        value={(value as string | null) ?? ''}
        onChange={(v) => onChange(v || null)}
        disabled={disabled}
      />
    )
  }

  return (
    <Input
      id={id}
      type={kind === 'phone' ? 'tel' : 'text'}
      value={(value as string) ?? ''}
      placeholder={placeholder}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}
