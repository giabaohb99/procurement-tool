import { useFormContext } from 'react-hook-form'

import { Button } from '@/shared/ui/button'

/** Hình dạng tối thiểu của form có hai ô địa chỉ — form hồ sơ và form tự sửa liên hệ đều có. */
interface AddressFormShape {
  permanent_address: string
  current_address: string
}

/**
 * Nút nhỏ "Giống địa chỉ thường trú" đặt dưới ô địa chỉ hiện nay (đại ca chốt 29/10/2026): chép địa chỉ
 * thường trú sang ô tạm trú ngay trên form — bấm Lưu mới ghi. Tắt khi ô thường trú còn trống.
 */
export function CopyAddressButton({ disabled = false }: { disabled?: boolean }) {
  const form = useFormContext<AddressFormShape>()
  const permanent = form.watch('permanent_address')

  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className="h-7 self-start px-2 text-xs"
      disabled={disabled || !(permanent ?? '').trim()}
      onClick={() =>
        form.setValue('current_address', permanent, { shouldDirty: true, shouldValidate: true })
      }
    >
      Giống địa chỉ thường trú
    </Button>
  )
}
