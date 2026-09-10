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
import { PageHeader } from '@/shared/ui/page-header'
import { RecordIdentityCard, type IdentityChip } from '@/shared/ui/record-identity-card'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { cn } from '@/shared/utils/cn'
import { CrudFormFields } from './crud-form-fields'
import { buildFormDefaults, toApiPayload } from './field-values'
import type { CrudConfig, CrudRecord } from './types'
import { useCrudDelete, useCrudDetail, useCrudSave } from './use-crud'

interface CrudDetailPageProps<T> {
  config: CrudConfig<T>
}

/**
 * Trang CHI TIẾT của lớp CRUD khai báo — và cũng là trang THÊM MỚI.
 *
 * Một component cho cả hai vì hai màn ấy chỉ khác nhau ở chỗ *đã có bản ghi hay
 * chưa*: cùng bộ ô nhập, cùng luật quyền, cùng chỗ hiện lỗi. Tách đôi là hai
 * bản chép, và mọi ô thêm về sau phải nhớ thêm ở cả hai chỗ.
 *
 * Chế độ THÊM MỚI bật khi route KHÔNG có `:id` (vd `/hr/leave-types/new` — xem
 * `CrudConfig.createRoute`). Khi đó: không gọi API chi tiết, không có thẻ danh
 * tính / dấu vết / nút Xóa (chưa có gì để kể), ô khai `readonlyOnEdit` mở ra cho
 * nhập, và lưu xong thì nhảy thẳng sang trang chi tiết của bản ghi vừa tạo.
 */
export function CrudDetailPage<T extends CrudRecord>({
  config,
}: CrudDetailPageProps<T>) {
  const { id } = useParams()
  const navigate = useNavigate()
  const { can } = usePermission()
  const idKey = (config.idKey as string) || 'id'

  //  Route tĩnh (`/hr/leave-types/new`) không có tham số `:id`.
  const isCreate = !id
  const canSave = can(config.entity, isCreate ? 'create' : 'write')

  const { data: item, isLoading, isError } = useCrudDetail<T>(config.apiPath, id)
  //  Chặn bấm trùng trong cùng một nhịp — xem `useSingleFlight`.
  const once = useSingleFlight()
  const saveMutation = useCrudSave<T>(config.apiPath, config.title)
  const deleteMutation = useCrudDelete(config.apiPath, config.title)

  const listUrl = config.listRoute || '/'

  //  ⚠️ MỘT CỘT cho CẢ TRANG — xem `CrudConfig.detailMaxWidth`. Chặn riêng biểu
  //  mẫu thì nó ngắn cụt nằm dưới thẻ danh tính rộng hết màn hình, trông như một
  //  khối bị lỗi chứ không phải một cột cố ý.
  const pageWidth = cn('mx-auto w-full', config.detailMaxWidth ?? 'max-w-5xl')

  const {
    register,
    handleSubmit,
    control,
    reset,
    watch,
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

  if (!isCreate && isLoading) {
    return (
      <PageContainer className={pageWidth}>
        <Skeleton className="mb-5 h-20 w-full" />
        <Skeleton className="h-80 w-full" />
      </PageContainer>
    )
  }

  if (!isCreate && (isError || !item)) {
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

  const itemName =
    item &&
    (config.getItemName
      ? config.getItemName(item)
      : String(item.name || item.code || item[idKey] || config.title))

  //  ⚠️ THẺ DANH TÍNH dùng tên TRẦN, không dùng `getItemName`. Hai chỗ hỏi hai
  //  câu khác nhau, và `getItemName` khai ra để trả lời câu thứ hai: *«Xóa bản
  //  ghi nào?»* — ở đó cái mã đính kèm là thứ phân biệt tuyệt đối, đáng có.
  //  Thẻ danh tính thì đã bày chính cái mã ấy thành một huy hiệu ngay bên dưới
  //  tiêu đề, nên in lần nữa trong ngoặc là nói hai lần cùng một điều. Trên màn
  //  390px điều đó thành lỗi thấy được: tiêu đề bị cắt giữa chừng — «Trưởng
  //  phòng Thu mua (Demo) (tru…» — tức phần bị hy sinh lại chính là phần trùng.
  //  Thẻ ở khổ điện thoại (`mobileCard` của các config) vốn đã dùng tên trần;
  //  đây là chỗ duy nhất còn lệch.
  const cardTitle = item && String(item.name || item.title || itemName)

  const onSubmit = (values: Record<string, unknown>) =>
    once(async () => {
    const saved = await saveMutation.mutateAsync({
      id: item ? (item[idKey] as string | number) : undefined,
      values: toApiPayload(config.formFields, values),
    })

    //  Tạo xong thì đi tiếp sang chính bản ghi vừa tạo, KHÔNG ở lại form rỗng:
    //  đứng yên thì bấm Lưu lần nữa là tạo thêm một bản trùng. `replace` để nút
    //  Lùi đưa về danh sách chứ không quay lại form đã gửi.
    if (isCreate) {
      const newId = (saved as CrudRecord | undefined)?.[idKey] as string | number | undefined
      navigate(newId && config.detailRoute ? config.detailRoute(newId) : listUrl, {
        replace: true,
      })
    }
    })

  const handleDelete = async () => {
    if (!item) return
    await deleteMutation.mutateAsync(item[idKey] as string | number)
    navigate(listUrl)
  }

  // Danh sách chip danh tính mặc định nếu config không tự khai
  const chips: IdentityChip[] = !item
    ? []
    : config.chips
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
        {/*  Lớp khung NGOÀI CÙNG của ba lớp lồng nhau — xem ghi chú ở
             `crud-form-fields.tsx`. */}
        <Card className="gap-4 p-3 sm:p-5">
          <CrudFormFields
            fields={config.formFields}
            register={register}
            control={control}
            errors={errors}
            watch={watch}
            sectionHints={config.formSections}
            //  `readonlyOnEdit` chỉ khóa lúc SỬA — ô «Mã loại nghỉ» phải nhập
            //  được đúng một lần, chính là lần tạo này.
            isReadonly={(field) => !canSave || (!isCreate && Boolean(field.readonlyOnEdit))}
          />
        </Card>
      </form>

      {item && config.renderExtra && <div>{config.renderExtra(item)}</div>}

      {Boolean(item?.[idKey]) && item && (
        <div>
          <AuditTimeline entity={config.entity} entityId={Number(item[idKey])} />
        </div>
      )}
    </div>
  )

  return (
    <PageContainer className={pageWidth}>
      {/*  ⚠️ Hàng nút DÍNH khi cuộn. Form danh mục dài hơn một màn — riêng
           *Loại nghỉ* đo được 1943px ở khổ 390px — nên nút Lưu đứng yên ở đầu
           trang nghĩa là gõ xong ô cuối phải cuộn ngược hết chiều dài trang mới
           lưu được, rồi cuộn xuống lại để kiểm. Cùng luật với `PageHeader.sticky`
           mà hai màn chi tiết Nghỉ phép đang dùng; đây là màn duy nhất còn thiếu.

           Lề âm để dải chạy hết bề ngang khung thay vì thụt vào theo phần đệm
           của `PageContainer` — dính mà còn hai mép hở thì nhìn ra ngay là vá. */}
      <div className="sticky top-0 z-20 -mx-4 -mt-4 mb-4 flex flex-wrap items-center justify-between gap-3 border-b bg-canvas px-4 py-3 lg:-mx-6 lg:-mt-6 lg:px-6">
        {/*  `-ml-2` kéo chữ về sát mép: nút `ghost` có phần đệm ngang riêng nên
             không có nó thì dòng «Danh sách …» thụt vào so với mọi thẻ bên dưới.

             ⚠️ Tên danh mục THÔI HIỆN ở khổ điện thoại. «Danh sách phòng họp»
             đo được **186px trên 390px** — gần một nửa hàng — trong khi hàng này
             còn phải chứa nút Lưu và nút Xóa; ba thứ chen nhau còn 24px khe.
             Giấu đi không mất nghĩa: mũi tên đã nói đây là đường lùi, và dòng
             chỉ mục ngay phía trên vẫn ghi đủ tên danh mục.

             ⚠️ `sr-only` chứ KHÔNG `hidden`: `hidden` là `display:none`, tức
             trình đọc màn hình cũng mất luôn và người mù chỉ nghe được "Danh
             sách" — trong khi họ không có mũi tên lẫn dòng chỉ mục để suy ra
             danh sách nào. `sr-only` giấu khỏi mắt mà vẫn đọc được, và nó
             `position:absolute` nên cũng không chiếm chỗ trong hàng. */}
        <Button variant="ghost" size="sm" className="-ml-2 min-w-0" asChild>
          <Link to={listUrl}>
            <ArrowLeft />
            <span className="truncate">
              Danh sách<span className="max-sm:sr-only"> {config.unitLabel}</span>
            </span>
          </Link>
        </Button>

        <div className="flex shrink-0 items-center gap-2">
          <PermissionGate entity={config.entity} action={isCreate ? 'create' : 'write'}>
            <Button
              type="submit"
              form="crud-detail-form"
              disabled={saveMutation.isPending || !canSave}
            >
              {saveMutation.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              {isCreate ? `Tạo ${config.unitLabel}` : 'Lưu'}
            </Button>
          </PermissionGate>

          {item && (
            <PermissionGate entity={config.entity} action="delete">
              <DeleteConfirmButton
                recordName={itemName as string}
                pending={deleteMutation.isPending}
                onConfirm={handleDelete}
                warning={config.deleteWarning}
              />
            </PermissionGate>
          )}
        </div>
      </div>

      <div className="space-y-6">
        {/*  Chưa có bản ghi thì không dựng thẻ danh tính: nó sinh ra để trưng mã
             / trạng thái của MỘT bản ghi, để rỗng chỉ còn một cái khung. */}
        {item ? (
          <RecordIdentityCard title={cardTitle as string} chips={chips} />
        ) : (
          <PageHeader
            title={`Thêm ${config.unitLabel}`}
            description={config.description ?? `Điền thông tin rồi bấm «Tạo ${config.unitLabel}».`}
          />
        )}

        {item && config.tabs && config.tabs.length > 0 ? (
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
