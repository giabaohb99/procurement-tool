import type { ReactNode } from 'react'

import { FormDescriptionHint } from '@/shared/ui/form-description-hint'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { cn } from '@/shared/utils/cn'

/**
 * Lớp cho ô CHỈ XEM trên mặt phẳng trắng kiểu ERPNext: bỏ viền, nền xám nhạt hơn ô nhập (`bg-muted`) một bậc —
 * chữ đậm navy + con trỏ cấm của `ReadOnlyValue` vẫn là thứ phân biệt nó với ô gõ được.
 */
const READONLY_BOX = 'border-transparent bg-muted/60'

interface EncashFieldLabelProps {
  label: string
  /** `id` của ô nhập — vắng thì nhãn chỉ là chữ (ô chỉ xem, nhóm nút chọn có `aria-labelledby` riêng). */
  htmlFor?: string
  /** `id` của chính nhãn, cho nhóm nút chọn (`RadioGroup aria-labelledby`). */
  id?: string
  required?: boolean
  /** Chú thích thu vào (i) cạnh nhãn; chữ vẫn nằm trong DOM (`sr-only`) dưới `hintId`. */
  hint?: ReactNode
  hintId?: string
}

/**
 * HÀNG NHÃN của một ô trên form / bản xem phiếu thanh toán nghỉ phép (duoc-CR-719, bố cục phẳng) — chép đúng khuôn
 * `CrudField`: cao tối thiểu `min-h-5` (= nút (i) 20px) để ô có (i) và ô không có nằm cạnh nhau không so le; (i) nằm
 * NGOÀI `<label>` vì trong nhãn thì bấm (i) là con trỏ nhảy vào ô nhập.
 */
export function EncashFieldLabel({ label, htmlFor, id, required, hint, hintId }: EncashFieldLabelProps) {
  return (
    <div className="flex min-h-5 items-center gap-1">
      <Label id={id} htmlFor={htmlFor} className="flex items-center gap-1">
        {label}
        {required && <RequiredMark />}
      </Label>
      {hint && hintId && (
        <FormDescriptionHint id={hintId} className="static inline-flex">
          {hint}
        </FormDescriptionHint>
      )}
    </div>
  )
}

interface EncashReadOnlyFieldProps {
  label: string
  children?: ReactNode
  /** Trải hết hai cột (ghi chú, câu dài). */
  full?: boolean
  multiline?: boolean
}

/** Một ô CHỈ XEM: hàng nhãn + hộp giá trị xám (bôi đen / copy được — không dùng `<Input disabled>`). */
export function EncashReadOnlyField({ label, children, full = false, multiline = false }: EncashReadOnlyFieldProps) {
  return (
    <div className={cn('space-y-1.5', full && 'col-span-full')}>
      <EncashFieldLabel label={label} />
      <ReadOnlyValue multiline={multiline} className={READONLY_BOX}>
        {children}
      </ReadOnlyValue>
    </div>
  )
}
