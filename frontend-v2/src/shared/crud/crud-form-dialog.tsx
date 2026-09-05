import { Loader2 } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { confirm } from '@/shared/ui/confirm-dialog'
import { CrudField } from './crud-field'
import { buildFormDefaults, toApiPayload } from './field-values'
import type { CrudConfig, CrudRecord } from './types'
import { useCrudSave } from './use-crud'

interface CrudFormDialogProps<T> {
  open: boolean
  onOpenChange: (open: boolean) => void
  config: CrudConfig<T>
  item?: T | null
}

export function CrudFormDialog<T extends CrudRecord>({
  open,
  onOpenChange,
  config,
  item,
}: CrudFormDialogProps<T>) {
  const saveMutation = useCrudSave<T>(config.apiPath, config.title)
  const isEditing = Boolean(item)

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<Record<string, unknown>>({
    defaultValues: buildFormDefaults(config.formFields, item),
  })

  const pending = isSubmitting || saveMutation.isPending

  /** Đóng theo case C-01: chỉ Hủy/X; form đã sửa thì hỏi xác nhận, tránh mất dữ liệu. */
  const attemptClose = async () => {
    if (pending) return
    if (isDirty && !(await confirm({ message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ các thay đổi này?' }))) return
    onOpenChange(false)
  }

  // Nạp lại giá trị mỗi lần MỞ hộp thoại: cùng một component được dùng lại cho
  // cả "Thêm" lẫn "Sửa", không reset thì lần mở sau còn nguyên số của lần trước.
  useEffect(() => {
    if (open) {
      reset(buildFormDefaults(config.formFields, item))
    }
  }, [open, item, config.formFields, reset])

  const onSubmit = async (values: Record<string, unknown>) => {
    const idKey = (config.idKey as string) || 'id'
    const id = item ? (item[idKey] as string | number) : undefined

    await saveMutation.mutateAsync({ id, values: toApiPayload(config.formFields, values) })
    onOpenChange(false)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        // Đóng (next=false) phải qua chốt chống mất dữ liệu; mở thì để nguyên.
        if (next) onOpenChange(true)
        else attemptClose()
      }}
    >
      <DialogContent
        className={config.dialogMaxWidth || 'sm:max-w-lg'}
        // C-01: KHÔNG đóng bằng Esc hay click ra ngoài — chỉ Hủy/X (qua onOpenChange).
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>
            {isEditing ? `Sửa ${config.unitLabel}` : `Thêm ${config.unitLabel}`}
          </DialogTitle>
        </DialogHeader>

        <form
          onSubmit={handleSubmit(onSubmit)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.target as HTMLElement).tagName !== 'TEXTAREA') {
              e.preventDefault()
            }
          }}
          className="space-y-4 pt-2"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {config.formFields.map((field) => (
              <CrudField
                key={field.name}
                field={field}
                register={register}
                control={control}
                errors={errors}
                isReadonly={isEditing && field.readonlyOnEdit}
              />
            ))}
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={attemptClose}
              disabled={pending}
            >
              Hủy
            </Button>
            <Button type="submit" disabled={pending}>
              {pending && <Loader2 className="mr-2 size-4 animate-spin" />}
              {isEditing ? 'Lưu thay đổi' : 'Tạo mới'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
