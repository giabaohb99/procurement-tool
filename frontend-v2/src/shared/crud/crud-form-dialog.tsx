import { Loader2 } from 'lucide-react'
import { useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import type { CrudConfig, CrudFormField } from './types'
import { useCrudSave, useCrudSourceOptions } from './use-crud'

interface CrudFormDialogProps<T> {
  open: boolean
  onOpenChange: (open: boolean) => void
  config: CrudConfig<T>
  item?: T | null
}

export function CrudFormDialog<T extends Record<string, any>>({
  open,
  onOpenChange,
  config,
  item,
}: CrudFormDialogProps<T>) {
  const saveMutation = useCrudSave<T>(config.apiPath, config.title)
  const isEditing = Boolean(item)

  // Xây dựng giá trị mặc định từ formFields
  const buildDefaultValues = () => {
    const values: Record<string, any> = {}
    for (const field of config.formFields) {
      if (item && item[field.name] !== undefined) {
        values[field.name] = item[field.name]
      } else if (field.defaultValue !== undefined) {
        values[field.name] = field.defaultValue
      } else if (field.type === 'switch') {
        values[field.name] = true
      } else if (field.type === 'number') {
        values[field.name] = 0
      } else {
        values[field.name] = ''
      }
    }
    return values
  }

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<Record<string, any>>({
    defaultValues: buildDefaultValues(),
  })

  useEffect(() => {
    if (open) {
      reset(buildDefaultValues())
    }
  }, [open, item])

  const onSubmit = async (values: Record<string, any>) => {
    // Chuyển đổi các trường number hoặc switch nếu cần
    const payload: Record<string, any> = { ...values }
    for (const field of config.formFields) {
      if (field.type === 'number' && payload[field.name] !== undefined && payload[field.name] !== '') {
        payload[field.name] = Number(payload[field.name])
      }
    }

    const idKey = (config.idKey as string) || 'id'
    const id = item ? item[idKey] : undefined

    await saveMutation.mutateAsync({ id, values: payload })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={config.dialogMaxWidth || 'sm:max-w-lg'}>
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
              <FormFieldItem
                key={field.name}
                field={field}
                register={register}
                control={control}
                errors={errors}
                isEditing={isEditing}
              />
            ))}
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting || saveMutation.isPending}
            >
              Hủy
            </Button>
            <Button type="submit" disabled={isSubmitting || saveMutation.isPending}>
              {(isSubmitting || saveMutation.isPending) && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              {isEditing ? 'Lưu thay đổi' : 'Tạo mới'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function FormFieldItem({
  field,
  register,
  control,
  errors,
  isEditing,
}: {
  field: CrudFormField
  register: any
  control: any
  errors: any
  isEditing: boolean
}) {
  const isFullWidth = field.fullWidth || field.type === 'textarea'
  const isReadonly = isEditing && field.readonlyOnEdit
  const errorMessage = errors[field.name]?.message as string | undefined

  return (
    <div className={`space-y-1.5 ${isFullWidth ? 'sm:col-span-2' : ''}`}>
      <Label htmlFor={field.name} className="flex items-center gap-1">
        {field.label}
        {field.required && <span className="text-destructive">*</span>}
      </Label>

      {field.type === 'textarea' ? (
        <Textarea
          id={field.name}
          placeholder={field.placeholder}
          disabled={isReadonly}
          rows={3}
          {...register(field.name, {
            required: field.required ? `${field.label} là bắt buộc` : false,
          })}
        />
      ) : field.type === 'switch' ? (
        <Controller
          control={control}
          name={field.name}
          render={({ field: controllerField }) => (
            <div className="flex items-center gap-3 pt-1">
              <Switch
                id={field.name}
                checked={Boolean(controllerField.value)}
                onCheckedChange={controllerField.onChange}
                disabled={isReadonly}
              />
              <span className="text-sm font-normal text-muted-foreground">
                {controllerField.value ? 'Đang dùng / Hoạt động' : 'Ngừng / Ẩn'}
              </span>
            </div>
          )}
        />
      ) : field.type === 'select' ? (
        <SelectField field={field} control={control} isReadonly={isReadonly} />
      ) : field.type === 'date' ? (
        <Controller
          control={control}
          name={field.name}
          rules={{ required: field.required ? `${field.label} là bắt buộc` : false }}
          render={({ field: controllerField }) => (
            <DatePicker
              value={controllerField.value || ''}
              onChange={controllerField.onChange}
              disabled={isReadonly}
            />
          )}
        />
      ) : (
        <Input
          id={field.name}
          type={field.type === 'number' ? 'number' : 'text'}
          placeholder={field.placeholder}
          disabled={isReadonly}
          {...register(field.name, {
            required: field.required ? `${field.label} là bắt buộc` : false,
          })}
        />
      )}

      {field.hint && <p className="text-xs text-muted-foreground">{field.hint}</p>}
      {errorMessage && <p className="text-xs text-destructive">{errorMessage}</p>}
    </div>
  )
}

function SelectField({
  field,
  control,
  isReadonly,
}: {
  field: CrudFormField
  control: any
  isReadonly?: boolean
}) {
  const { data: remoteOptions, isLoading } = useCrudSourceOptions(field.source)
  const options = field.options ?? remoteOptions ?? []

  return (
    <Controller
      control={control}
      name={field.name}
      rules={{ required: field.required ? `${field.label} là bắt buộc` : false }}
      render={({ field: controllerField }) => (
        <Select
          value={String(controllerField.value ?? '')}
          onValueChange={(val) => {
            // Nếu options có kiểu boolean, parse lại
            if (val === 'true') controllerField.onChange(true)
            else if (val === 'false') controllerField.onChange(false)
            else controllerField.onChange(val)
          }}
          disabled={isReadonly || isLoading}
        >
          <SelectTrigger id={field.name}>
            <SelectValue placeholder={field.placeholder || `Chọn ${field.label.toLowerCase()}`} />
          </SelectTrigger>
          <SelectContent>
            {options.map((opt) => (
              <SelectItem key={String(opt.value)} value={String(opt.value)}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    />
  )
}
