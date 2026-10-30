import { Plus, Trash2 } from 'lucide-react'
import { useId } from 'react'
import { useFormContext, useWatch } from 'react-hook-form'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import {
  duplicatePhoneIndexes,
  MAX_EXTRA_PHONES,
  PHONE_LABEL_SUGGESTIONS,
  phoneNumberError,
  swapWithMain,
  type ExtraPhone,
} from '../schemas/extra-phones-schema'

/** Hình dạng tối thiểu của form chứa danh sách số — form hồ sơ và form tự sửa liên hệ đều có đúng hai ô này. */
interface PhoneFormShape {
  phone: string
  phone_label: string
  extra_phones: ExtraPhone[]
}

interface PhoneListEditorProps {
  disabled?: boolean
}

//  Cột nhãn cố định, ô số chiếm phần còn lại; khổ hẹp thì nút xuống hàng dưới (flex-wrap) chứ không tràn ngang.
const LABEL_CLASS = 'w-32 shrink-0'
const NUMBER_CLASS = 'min-w-[10rem] flex-1'
const ACTIONS_CLASS = 'sm:w-36 sm:shrink-0'

/**
 * Ô nhập NHIỀU SỐ ĐIỆN THOẠI (duoc-CR-694) — MỘT danh sách "Số điện thoại" cùng bề rộng các ô khác.
 *
 * Mỗi dòng: [nhãn] [số] [nút/huy hiệu]. Dòng đầu là SỐ CHÍNH (cột `phone` + `phone_label`, huy hiệu "Số chính"
 * ở cuối dòng); các dòng sau là số phụ (`extra_phones`, tối đa `MAX_EXTRA_PHONES`) có
 * ô nhãn gõ tự do kèm gợi ý, nút "Đặt làm chính" và thùng rác. "Đặt làm chính" chỉ hoán đổi trên form — bấm Lưu
 * mới ghi, và hoán đổi CẢ số lẫn nhãn.
 *
 * Đọc/ghi qua `useFormContext` nên dùng được trong cả hai form; nơi gọi chỉ cần nằm trong `<Form>`.
 * Báo lỗi từng dòng tại chỗ (định dạng, trùng) để người dùng thấy ngay, kể cả khi chưa bấm Lưu.
 */
export function PhoneListEditor({ disabled = false }: PhoneListEditorProps) {
  const form = useFormContext<PhoneFormShape>()
  const listId = useId()
  const main = useWatch({ control: form.control, name: 'phone' }) ?? ''
  const mainLabel = useWatch({ control: form.control, name: 'phone_label' }) ?? ''
  const extras = useWatch({ control: form.control, name: 'extra_phones' }) ?? []
  const duplicates = duplicatePhoneIndexes(main, extras)
  const mainError = form.formState.errors.phone?.message
  const listError =
    form.formState.errors.extra_phones?.message ?? form.formState.errors.extra_phones?.root?.message

  const setExtras = (next: ExtraPhone[]) =>
    form.setValue('extra_phones', next, { shouldDirty: true, shouldValidate: true })

  function updateRow(index: number, patch: Partial<ExtraPhone>) {
    setExtras(extras.map((p, i) => (i === index ? { ...p, ...patch } : p)))
  }

  function makeMain(index: number) {
    const swapped = swapWithMain({ number: main, label: mainLabel }, extras, index)
    form.setValue('phone', swapped.main.number, { shouldDirty: true, shouldValidate: true })
    form.setValue('phone_label', swapped.main.label, { shouldDirty: true, shouldValidate: true })
    setExtras(swapped.extras)
  }

  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm font-medium leading-none">Số điện thoại</p>

      <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <Input
            aria-label="Nhãn số chính"
            placeholder="Nhãn"
            list={listId}
            maxLength={50}
            disabled={disabled}
            className={LABEL_CLASS}
            {...form.register('phone_label')}
          />
          <Input
            type="tel"
            autoComplete="tel"
            aria-label="Số điện thoại"
            placeholder="Số điện thoại"
            disabled={disabled}
            className={NUMBER_CLASS}
            {...form.register('phone')}
          />
          {/*  Cột nút cùng bề rộng với các số phụ để mọi ô số thẳng hàng (khổ rộng). */}
          <div className={`flex h-9 items-center px-2 ${ACTIONS_CLASS}`}>
            <Badge variant="secondary">Số chính</Badge>
          </div>
        </div>
        {mainError && <p className="text-xs text-destructive">{mainError}</p>}
      </div>

      {extras.map((phone, index) => {
        const error =
          phoneNumberError(phone.number) ?? (duplicates.has(index) ? 'Số này đã nhập ở trên' : null)
        return (
          <div key={index} className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <Input
                aria-label={`Nhãn số điện thoại khác ${index + 1}`}
                placeholder="Nhãn"
                list={listId}
                maxLength={50}
                disabled={disabled}
                value={phone.label}
                onChange={(e) => updateRow(index, { label: e.target.value })}
                className={LABEL_CLASS}
              />
              <Input
                type="tel"
                aria-label={`Số điện thoại khác ${index + 1}`}
                placeholder="Số điện thoại"
                disabled={disabled}
                aria-invalid={error ? true : undefined}
                value={phone.number}
                onChange={(e) => updateRow(index, { number: e.target.value })}
                className={NUMBER_CLASS}
              />
              {!disabled && (
                <div className={`flex items-center gap-1 ${ACTIONS_CLASS}`}>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-xs"
                    aria-label={`Đặt số khác ${index + 1} làm số chính`}
                    disabled={!phone.number.trim()}
                    onClick={() => makeMain(index)}
                  >
                    Đặt làm chính
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-8"
                    title="Xóa số này"
                    aria-label={`Xóa số điện thoại khác ${index + 1}`}
                    onClick={() => setExtras(extras.filter((_, i) => i !== index))}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              )}
            </div>
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
        )
      })}

      <datalist id={listId}>
        {PHONE_LABEL_SUGGESTIONS.map((label) => (
          <option key={label} value={label} />
        ))}
      </datalist>

      {listError && <p className="text-xs text-destructive">{listError}</p>}

      {!disabled && extras.length < MAX_EXTRA_PHONES && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 self-start px-2 text-xs"
          onClick={() => setExtras([...extras, { number: '', label: '' }])}
        >
          <Plus className="size-3.5" />
          Thêm số
        </Button>
      )}
    </div>
  )
}
