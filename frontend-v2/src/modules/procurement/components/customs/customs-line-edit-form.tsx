// bao-CR-608 — biểu mẫu SỬA một dòng hàng, hiện ngay trong hộp chi tiết dòng (đại ca 07/10/2026).
//
// Chỉ gửi ô ĐÃ ĐỔI (`buildCustomsLinePatch`). Bốn ô suy ra / tự tính để trống = hệ thống tự làm;
// gõ vào = giá trị do người nhập, «Gắn lại nhãn» không ghi đè. Bản trước khi sửa được backend chụp
// lại (`tab_customs_line_change`) và ghi nhật ký thao tác.
//
// Bẫy biểu mẫu (duoc-CR-317): chặn bấm đúp bằng `useRef`; Enter trong ô một dòng không lưu;
// nút Hủy khai `type="button"`.
import { Info } from 'lucide-react'
import { useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { DialogFooter } from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import { useUpdateCustomsLine } from '../../hooks/use-customs'
import type { CustomsLine } from '../../types/customs'
import {
  buildCustomsLinePatch,
  CUSTOMS_LINE_FORM_GROUPS,
  CUSTOMS_TRANSPORT_OPTIONS,
  derivedPlaceholder,
  toCustomsLineForm,
  type CustomsLineEditKey,
  type CustomsLineField,
} from '../../utils/customs-line-form'
import { CustomsNotice } from './customs-controls'

const FORM_ID = 'customs-line-edit-form'
/** Ô chọn phương tiện: Radix Select không cho giá trị rỗng — dùng mốc riêng cho «chưa khai». */
const NO_TRANSPORT = 'none'

function blockEnter(event: KeyboardEvent<HTMLInputElement>) {
  if (event.key === 'Enter') event.preventDefault()
}

interface CustomsLineEditFormProps {
  line: CustomsLine
  onCancel: () => void
  onSaved: () => void
}

export function CustomsLineEditForm({ line, onCancel, onSaved }: CustomsLineEditFormProps) {
  const initial = useMemo(() => toCustomsLineForm(line), [line])
  const [form, setForm] = useState(initial)
  const [error, setError] = useState<string | null>(null)
  const busy = useRef(false)
  const update = useUpdateCustomsLine()
  const pending = update.isPending

  function setField(key: CustomsLineEditKey, value: string) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (busy.current) return
    const { patch, error: problem } = buildCustomsLinePatch(initial, form)
    setError(problem)
    if (problem) return
    if (!Object.keys(patch).length) {
      toast.info('Chưa có ô nào thay đổi')
      onCancel()
      return
    }
    busy.current = true
    try {
      await update.mutateAsync({ id: line.id, patch })
      toast.success('Đã lưu dòng hàng')
      onSaved()
    } catch {
      //  `httpClient` đã báo lỗi (422 quá dài, 403…) bằng toast — giữ biểu mẫu để sửa tiếp.
    } finally {
      busy.current = false
    }
  }

  function renderInput(field: CustomsLineField) {
    const id = `customs-line-${field.key}`
    if (field.kind === 'date') {
      return (
        <DatePicker
          id={id}
          value={form[field.key]}
          clearable={!field.required}
          disabled={pending}
          onChange={(value) => setField(field.key, value)}
        />
      )
    }
    if (field.kind === 'transport') {
      return (
        <Select
          value={form[field.key] || NO_TRANSPORT}
          onValueChange={(value) => setField(field.key, value === NO_TRANSPORT ? '' : value)}
          disabled={pending}
        >
          <SelectTrigger id={id} className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NO_TRANSPORT}>Không khai</SelectItem>
            {CUSTOMS_TRANSPORT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
    }
    return (
      <Input
        id={id}
        value={form[field.key]}
        maxLength={field.maxLength}
        inputMode={field.kind === 'text' ? undefined : 'decimal'}
        placeholder={field.derived ? derivedPlaceholder(line, field.key) : undefined}
        disabled={pending}
        onKeyDown={blockEnter}
        onChange={(event) => setField(field.key, event.target.value)}
      />
    )
  }

  return (
    <>
      <form id={FORM_ID} className="space-y-3 p-5" onSubmit={(event) => void submit(event)} noValidate>
        <CustomsNotice icon={<Info className="size-4" />}>
          Ô <b>Hoạt chất</b>, <b>Hàm lượng / dạng</b> và hai ô <b>giá VND</b> để trống thì hệ thống
          tự suy ra / tự tính (giá trị hiện ở chữ mờ); gõ vào thì giữ đúng giá trị đó. Số dùng dấu
          chấm hoặc phẩy cho phần thập phân, không gõ dấu ngăn nghìn. Bản trước khi sửa được lưu lại
          trong nhật ký.
        </CustomsNotice>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="grid gap-3 md:grid-cols-2">
          {CUSTOMS_LINE_FORM_GROUPS.map((group) => (
            <section key={group.title} className="min-w-0 rounded-lg border p-3">
              <h3 className="mb-2 text-sm font-semibold text-navy dark:text-foreground">{group.title}</h3>
              <div className="space-y-2">
                {group.fields.map((field) => (
                  <div key={field.key} className="grid grid-cols-[minmax(0,11rem)_minmax(0,1fr)] items-center gap-2">
                    <Label htmlFor={`customs-line-${field.key}`} className="text-muted-foreground">
                      {field.label}
                      {field.required && <RequiredMark hint="Bắt buộc" />}
                    </Label>
                    {renderInput(field)}
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      </form>
      <DialogFooter className="border-t p-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={pending}>
          Hủy
        </Button>
        <Button type="submit" form={FORM_ID} disabled={pending}>
          {pending ? 'Đang lưu…' : 'Lưu'}
        </Button>
      </DialogFooter>
    </>
  )
}
