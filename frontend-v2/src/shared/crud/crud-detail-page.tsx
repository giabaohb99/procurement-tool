import { ArrowLeft, CircleCheck, CircleX, Hash, Loader2, Save } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { RecordIdentityCard, type IdentityChip } from '@/shared/ui/record-identity-card'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { CrudField } from './crud-field'
import { buildFormDefaults, toApiPayload } from './field-values'
import type { CrudConfig, CrudRecord } from './types'
import { useCrudDelete, useCrudDetail, useCrudSave } from './use-crud'

interface CrudDetailPageProps<T> {
  config: CrudConfig<T>
}

export function CrudDetailPage<T extends CrudRecord>({
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

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<Record<string, unknown>>({
    defaultValues: buildFormDefaults(config.formFields, item),
  })

  // Bản ghi về sau khi gọi API (hoặc sau khi lưu) thì nạp lại vào form.
  useEffect(() => {
    if (item) {
      reset(buildFormDefaults(config.formFields, item))
    }
  }, [item, config.formFields, reset])

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

  const onSubmit = async (values: Record<string, unknown>) => {
    await saveMutation.mutateAsync({
      id: item[idKey] as string | number,
      values: toApiPayload(config.formFields, values),
    })
  }

  const handleDelete = async () => {
    await deleteMutation.mutateAsync(item[idKey] as string | number)
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

  const infoPanel = (
    <>
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
              <CrudField
                key={field.name}
                field={field}
                register={register}
                control={control}
                errors={errors}
                isReadonly={!canWrite || field.readonlyOnEdit}
              />
            ))}
          </div>
        </Card>
      </form>

      {config.renderExtra && <div>{config.renderExtra(item)}</div>}

      {item[idKey] && (
        <div>
          <AuditTimeline entity={config.entity} entityId={Number(item[idKey])} />
        </div>
      )}
    </>
  )

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
              {infoPanel}
            </TabsContent>

            {config.tabs.map((tab) => (
              <TabsContent key={tab.key} value={tab.key} className="space-y-4">
                {tab.render(item)}
              </TabsContent>
            ))}
          </Tabs>
        ) : (
          <div className="space-y-6">{infoPanel}</div>
        )}
      </div>
    </PageContainer>
  )
}
