import { ArrowLeft, CircleCheck, CircleX, Hash, Loader2, Save } from 'lucide-react'
import { useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DatePicker } from '@/shared/ui/date-picker'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { ErrorState } from '@/shared/ui/error-state'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { RecordIdentityCard, type IdentityChip } from '@/shared/ui/record-identity-card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Switch } from '@/shared/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { Textarea } from '@/shared/ui/textarea'
import type { CrudConfig, CrudFormField } from './types'
import { useCrudDelete, useCrudDetail, useCrudSave, useCrudSourceOptions } from './use-crud'

interface CrudDetailPageProps<T> {
  config: CrudConfig<T>
}

export function CrudDetailPage<T extends Record<string, any>>({
  config,
}: CrudDetailPageProps<T>) {
  const { id } = useParams()
  const navigate = useNavigate()
  const { can } = usePermission()
  const canWrite = can(config.entity, 'write')
  const idKey = (config.idKey as string) || 'id'

  const { data: item, isLoading, isError } = useCrudDetail<T>(config.apiPath, id)
  const saveMutation = useCrudSave<T>(config.apiPath, config.title)
  const deleteMutation = useCrudDelete(config.apiPath, config.title)

  const listUrl = config.listRoute || '/'

  const buildDefaultValues = (sourceItem?: T | null) => {
    const values: Record<string, any> = {}
    for (const field of config.formFields) {
      if (sourceItem && sourceItem[field.name] !== undefined) {
        values[field.name] = sourceItem[field.name]
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
    formState: { errors },
  } = useForm<Record<string, any>>({
    defaultValues: buildDefaultValues(item),
  })

  useEffect(() => {
    if (item) {
      reset(buildDefaultValues(item))
    }
  }, [item])

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-5 h-20 w-full" />
        <Skeleton className="h-80 w-full" />
      </PageContainer>
    )
  }

  if (isError || !item) {
    return (
      <ErrorState
        title={`Không tìm thấy ${config.unitLabel}`}
        description={`${config.title} có thể đã bị xóa hoặc bạn không có quyền xem.`}
      >
        <Button variant="outline" onClick={() => navigate(listUrl)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  const itemName = config.getItemName
    ? config.getItemName(item)
    : String(item.name || item.code || item[idKey] || config.title)

  const onSubmit = async (values: Record<string, any>) => {
    const payload: Record<string, any> = { ...values }
    for (const field of config.formFields) {
      if (field.type === 'number' && payload[field.name] !== undefined && payload[field.name] !== '') {
        payload[field.name] = Number(payload[field.name])
      }
    }

    const itemId = item[idKey]
    await saveMutation.mutateAsync({ id: itemId, values: payload })
  }

  const handleDelete = async () => {
    const itemId = item[idKey]
    await deleteMutation.mutateAsync(itemId)
    navigate(listUrl)
  }

  // Danh sách chip danh tính mặc định nếu config không tự khai
  const chips: IdentityChip[] = config.chips
    ? config.chips(item)
    : [
        ...(item.code
          ? [{ icon: Hash, text: String(item.code), tone: 'code' as const }]
          : []),
        ...(item.is_active !== undefined
          ? [
              {
                icon: item.is_active ? CircleCheck : CircleX,
                text: item.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
                tone: item.is_active ? ('ok' as const) : ('muted' as const),
              },
            ]
          : []),
      ]

  return (
    <PageContainer>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to={listUrl}>
            <ArrowLeft />
            Danh sách {config.unitLabel}
          </Link>
        </Button>

        <div className="flex items-center gap-2">
          <PermissionGate entity={config.entity} action="write">
            <Button
              type="submit"
              form="crud-detail-form"
              disabled={saveMutation.isPending || !canWrite}
            >
              {saveMutation.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              Lưu
            </Button>
          </PermissionGate>

          <PermissionGate entity={config.entity} action="delete">
            <DeleteConfirmButton
              recordName={itemName}
              pending={deleteMutation.isPending}
              onConfirm={handleDelete}
              warning={config.deleteWarning}
            />
          </PermissionGate>
        </div>
      </div>

      <div className="space-y-6">
        <RecordIdentityCard title={itemName} chips={chips} />

        {config.tabs && config.tabs.length > 0 ? (
          <Tabs defaultValue="info" className="space-y-4">
            <TabsList className="mb-2">
              <TabsTrigger value="info">Thông tin</TabsTrigger>
              {config.tabs.map((tab) => (
                <TabsTrigger key={tab.key} value={tab.key}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value="info" className="space-y-6">
              <form
                id="crud-detail-form"
                onSubmit={handleSubmit(onSubmit)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.target as HTMLElement).tagName !== 'TEXTAREA') {
                    e.preventDefault()
                  }
                }}
              >
                <Card className="gap-4 p-5">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {config.formFields.map((field) => (
                      <DetailFormFieldItem
                        key={field.name}
                        field={field}
                        register={register}
                        control={control}
                        errors={errors}
                        canWrite={canWrite}
                      />
                    ))}
                  </div>
                </Card>
              </form>

              {config.renderExtra && (
                <div>{config.renderExtra(item)}</div>
              )}

              {item[idKey] && (
                <div>
                  <AuditTimeline entity={config.entity} entityId={Number(item[idKey])} />
                </div>
              )}
            </TabsContent>

            {config.tabs.map((tab) => (
              <TabsContent key={tab.key} value={tab.key} className="space-y-4">
                {tab.render(item)}
              </TabsContent>
            ))}
          </Tabs>
        ) : (
          <div className="space-y-6">
            <form
              id="crud-detail-form"
              onSubmit={handleSubmit(onSubmit)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.target as HTMLElement).tagName !== 'TEXTAREA') {
                  e.preventDefault()
                }
              }}
            >
              <Card className="gap-4 p-5">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {config.formFields.map((field) => (
                    <DetailFormFieldItem
                      key={field.name}
                      field={field}
                      register={register}
                      control={control}
                      errors={errors}
                      canWrite={canWrite}
                    />
                  ))}
                </div>
              </Card>
            </form>

            {config.renderExtra && (
              <div>{config.renderExtra(item)}</div>
            )}

            {item[idKey] && (
              <div>
                <AuditTimeline entity={config.entity} entityId={Number(item[idKey])} />
              </div>
            )}
          </div>
        )}
      </div>
    </PageContainer>
  )
}

function DetailFormFieldItem({
  field,
  register,
  control,
  errors,
  canWrite,
}: {
  field: CrudFormField
  register: any
  control: any
  errors: any
  canWrite: boolean
}) {
  const isFullWidth = field.fullWidth || field.type === 'textarea'
  const isReadonly = !canWrite || field.readonlyOnEdit
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
        <DetailSelectField field={field} control={control} isReadonly={isReadonly} />
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

function DetailSelectField({
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
