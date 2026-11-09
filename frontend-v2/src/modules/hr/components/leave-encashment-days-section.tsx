import { FormSection } from '@/shared/ui/form-section'
import { Input } from '@/shared/ui/input'
import type { LeaveEncashmentPreview } from '../types/leave-encashment'
import { EncashFieldLabel } from './leave-encashment-flat-field'
import { LeaveEncashmentPreviewBox } from './leave-encashment-preview-box'

interface LeaveEncashmentDaysSectionProps {
  preview?: LeaveEncashmentPreview
  previewLoading: boolean
  previewError?: string
  /** Chuỗi người dùng gõ (giữ dấu phẩy thập phân) — form tự đổi sang số lúc lưu. */
  days: string
  error?: string
  /** Lúc SỬA ô trống là mơ hồ (PATCH null = giữ số cũ) nên bắt nhập; lúc LẬP ô trống = dùng hết. */
  required: boolean
  placeholder: string
  onDaysChange: (days: string) => void
}

/**
 * Nhóm "SỐ NGÀY" của form phiếu thanh toán nghỉ phép (duoc-CR-719): dải số ngày được thanh toán (đọc `/preview`) rồi ô
 * số ngày nửa bề ngang. Câu "phiếu chỉ ghi số ngày" thu vào (i) của ô số ngày thay vì một dòng chữ riêng dưới form.
 */
export function LeaveEncashmentDaysSection({
  preview,
  previewLoading,
  previewError,
  days,
  error,
  required,
  placeholder,
  onDaysChange,
}: LeaveEncashmentDaysSectionProps) {
  return (
    //  `forceOpen` khi ô sai: câu lỗi nằm trong nhóm đang gập thì bấm Lưu là không thấy gì (duoc-CR-317).
    <FormSection title="Số ngày" forceOpen={Boolean(error)}>
      <div className="col-span-full">
        <LeaveEncashmentPreviewBox
          preview={preview}
          isLoading={previewLoading}
          errorMessage={previewError}
          onUseAll={(d) => onDaysChange(String(d))}
        />
      </div>

      <div className="space-y-1.5">
        <EncashFieldLabel
          label="Số ngày thanh toán"
          htmlFor="encash-days"
          required={required}
          hintId="encash-days-hint"
          hint={
            <>
              Theo bước nửa ngày (0,5), không vượt số được thanh toán. Phiếu chỉ ghi số ngày: duyệt xong, số ngày bị trừ
              khỏi quỹ phép và kế toán nhận một yêu cầu thanh toán để nhập số tiền và chi.
            </>
          }
        />
        <Input
          id="encash-days"
          inputMode="decimal"
          autoComplete="off"
          aria-describedby="encash-days-hint"
          placeholder={placeholder}
          value={days}
          onChange={(e) => onDaysChange(e.target.value)}
          onKeyDown={(e) => {
            //  Form không có `<form>` bao ngoài, nhưng chặn sẵn Enter để ai bọc lại cũng không submit ngầm.
            if (e.key === 'Enter') e.preventDefault()
          }}
        />
        {error && (
          <p role="alert" className="text-xs text-destructive">
            {error}
          </p>
        )}
      </div>
    </FormSection>
  )
}
