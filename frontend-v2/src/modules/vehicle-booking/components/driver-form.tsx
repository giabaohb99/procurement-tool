import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { DocumentComments } from '@/modules/procurement/components/document-comments'
import type { UserAccount } from '@/modules/hr/types/user-account'
import { useCrudDelete, useCrudSave } from '@/shared/crud'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { Input } from '@/shared/ui/input'
import { SectionHeading } from '@/shared/ui/section-heading'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { BookingPageHeader } from './booking-page-header'
import { CatalogFormField } from './catalog-form-field'
import { CatalogRecordTitle } from './catalog-record-title'
import { CatalogSourceSection } from './catalog-source-section'
import { DriverAccountPicker } from './driver-account-picker'
import { AvailabilityBadge, SourceBadge } from './status-pill'
import { DRIVER_STATUS_LABELS, SUPPLIER_TYPE, type Driver } from '../types/driver'

const API_PATH = '/api/drivers'
const TITLE = 'Danh mục Tài xế'
const DELETE_WARNING = 'Tài xế này có thể đang được phân cho phiếu đặt xe.'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'on_leave', label: 'Nghỉ phép' },
  { value: 'inactive', label: 'Ngưng sử dụng' },
]

interface FormState {
  name: string
  phone: string
  email: string
  license_number: string
  license_class: string
  status: string
  external_company: string
  supplier_type: number
  tax_code: string
  tax_address: string
  id_number: string
  user_id: number | null
}

function initialState(item?: Driver | null): FormState {
  return {
    name: item?.name ?? '',
    phone: item?.phone ?? '',
    email: item?.email ?? '',
    license_number: item?.license_number ?? '',
    license_class: item?.license_class ?? '',
    status: item?.status ?? 'available',
    external_company: item?.external_company ?? '',
    supplier_type: item?.supplier_type || SUPPLIER_TYPE.enterprise,
    tax_code: item?.tax_code ?? '',
    tax_address: item?.tax_address ?? '',
    id_number: item?.id_number ?? '',
    user_id: item?.user_id ?? null,
  }
}

interface DriverFormProps {
  item?: Driver | null
  /** Tiêu đề trang (vd "Chỉnh sửa thông tin tài xế"). */
  title: string
  onDone: () => void
}

/**
 * Biểu mẫu TÀI XẾ dùng trên TRANG (tạo mới `/drivers/new` và sửa `/drivers/:id`).
 *
 * Nội bộ: tìm tài khoản nhân sự theo số điện thoại rồi tự điền tên · điện thoại
 * · email. Thuê ngoài: khai tay, kèm giấy tờ của bên cung cấp.
 *
 * ⚠️ Đầu trang hiện TÊN TÀI XẾ chứ không phải chữ "Chỉnh sửa thông tin tài xế":
 * mở một trang sửa mà không biết đang sửa bản ghi nào là lỗi nặng hơn mọi lỗi
 * bố cục.
 *
 * ⚠️ Thứ tự khối ĐỔI theo việc đang tạo hay đang sửa. Lúc TẠO, *Nguồn* đứng
 * đầu vì nó quyết định cả phần còn lại của biểu mẫu (nội bộ thì chọn tài khoản,
 * thuê ngoài thì gõ tay) — hỏi sau là bắt người ta khai lại từ đầu. Lúc SỬA,
 * nguồn đã chốt nên nó chỉ còn là thông tin tham khảo và lùi xuống cuối, nhường
 * chỗ đầu trang cho thứ sửa được.
 */
export function DriverForm({ item, title, onDone }: DriverFormProps) {
  const save = useCrudSave<Driver>(API_PATH, TITLE)
  const del = useCrudDelete(API_PATH, TITLE)
  const isEdit = Boolean(item)

  const [isExternal, setIsExternal] = useState(Boolean(item?.is_external))
  const [form, setForm] = useState<FormState>(() => initialState(item))
  //  ⚠️ `disabled={pending}` KHÔNG chặn được bấm đúp: `isPending` là state React
  //  nên chỉ bật ở lượt render SAU. Danh mục Tài xế **không có cột duy nhất**
  //  (xem `catalog_controller.py`: `unique_field=None`), nên hai cú bấm liền
  //  tay lúc tạo mới ra HAI tài xế giống hệt nhau, không gì chặn lại.
  const runOnce = useSingleFlight()

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const pending = save.isPending || del.isPending
  const linked = !isExternal && form.user_id != null

  function selectAccount(account: UserAccount) {
    setForm((prev) => ({
      ...prev,
      name: account.full_name || '',
      phone: account.phone || '',
      email: account.contact_email || '',
      user_id: account.id,
    }))
  }

  function clearAccount() {
    setForm((prev) => ({ ...prev, name: '', phone: '', email: '', user_id: null }))
  }

  function validate(): string {
    if (!form.name.trim())
      return isExternal
        ? 'Thiếu tên tài xế.'
        : 'Vui lòng chọn tài khoản nhân sự (tìm theo số điện thoại).'
    if (!form.phone.trim()) return 'Thiếu số điện thoại.'
    if (!form.license_number.trim()) return 'Thiếu số giấy phép lái xe.'
    if (isExternal && form.supplier_type === SUPPLIER_TYPE.enterprise) {
      if (!form.external_company.trim()) return 'Thiếu tên doanh nghiệp.'
      if (!form.tax_code.trim()) return 'Thiếu mã số thuế.'
      if (!form.tax_address.trim()) return 'Thiếu địa chỉ thuế.'
    }
    return ''
  }

  async function submit() {
    const msg = validate()
    if (msg) {
      toast.error(msg)
      return
    }
    const isEnterprise = isExternal && form.supplier_type === SUPPLIER_TYPE.enterprise
    const isIndividual = isExternal && form.supplier_type === SUPPLIER_TYPE.individual
    await save.mutateAsync({
      id: item?.id,
      values: {
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
        license_number: form.license_number.trim(),
        license_class: form.license_class.trim(),
        status: form.status,
        is_external: isExternal,
        supplier_type: isExternal ? form.supplier_type : SUPPLIER_TYPE.none,
        external_company: isEnterprise ? form.external_company.trim() : '',
        tax_code: isEnterprise ? form.tax_code.trim() : '',
        tax_address: isEnterprise ? form.tax_address.trim() : '',
        id_number: isIndividual ? form.id_number.trim() : '',
        user_id: isExternal ? null : form.user_id,
      },
    })
    onDone()
  }

  async function handleDelete() {
    if (!item) return
    await del.mutateAsync(item.id)
    onDone()
  }

  const sourceSection = (
    <CatalogSourceSection
      unitLabel="tài xế"
      idNumberHint="Căn cước của chính tài xế."
      isEdit={isEdit}
      isExternal={isExternal}
      onExternalChange={setIsExternal}
      supplierType={form.supplier_type}
      onSupplierTypeChange={(v) => set('supplier_type', v)}
      values={form}
      onChange={(key, value) => set(key, value)}
    />
  )

  const profileSection = (
    <section className="flex flex-col gap-4">
      <SectionHeading>Thông tin tài xế</SectionHeading>

      {isExternal ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <CatalogFormField label="Tên tài xế" required>
            <Input
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              placeholder="VD: Lê Minh Thông"
            />
          </CatalogFormField>
          <CatalogFormField label="Số điện thoại" required>
            <Input
              value={form.phone}
              onChange={(e) => set('phone', e.target.value)}
              placeholder="VD: 0907507103"
            />
          </CatalogFormField>
          <CatalogFormField label="Email" fullWidth>
            <Input
              value={form.email}
              onChange={(e) => set('email', e.target.value)}
              placeholder="VD: taixe@ncc.com"
            />
          </CatalogFormField>
        </div>
      ) : (
        <DriverAccountPicker
          linked={linked}
          name={form.name}
          phone={form.phone}
          email={form.email}
          onSelect={selectAccount}
          onClear={clearAccount}
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <CatalogFormField
          label="Trạng thái"
          fullWidth
          hint="Tài xế «Nghỉ phép» / «Ngưng sử dụng» vẫn nằm trong danh mục nhưng không nên phân chuyến."
        >
          <Select value={form.status} onValueChange={(v) => set('status', v)}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CatalogFormField>
      </div>
    </section>
  )

  const licenseSection = (
    <section className="flex flex-col gap-4">
      <SectionHeading>Giấy phép lái xe</SectionHeading>
      <div className="grid gap-4 sm:grid-cols-2">
        <CatalogFormField label="Số giấy phép lái xe" required>
          <Input
            value={form.license_number}
            onChange={(e) => set('license_number', e.target.value)}
            placeholder="VD: 790112345678"
          />
        </CatalogFormField>
        <CatalogFormField
          label="Hạng GPLX"
          hint="Hạng quyết định tài xế được cầm loại xe nào — B2 không chạy được xe tải hạng C."
        >
          <Input
            value={form.license_class}
            onChange={(e) => set('license_class', e.target.value)}
            placeholder="VD: B2, C, D"
          />
        </CatalogFormField>
      </div>
    </section>
  )

  return (
    <div className="flex w-full flex-col">
      <BookingPageHeader
        //  Khi SỬA: đầu trang là TÊN TÀI XẾ + một dòng tóm tắt đọc theo giá trị
        //  ĐANG NHẬP (không phải giá trị đã lưu), nên sửa số điện thoại hay hạng
        //  bằng là dòng đó đổi theo ngay.
        title={
          isEdit ? (
            <CatalogRecordTitle
              title={form.name.trim() || 'Tài xế chưa đặt tên'}
              summary={
                [form.phone, [form.license_class, form.license_number].filter(Boolean).join(' · ')]
                  .filter(Boolean)
                  .join(' — ') || title
              }
            />
          ) : (
            title
          )
        }
        badge={
          isEdit ? (
            <div className="flex items-center gap-2">
              <SourceBadge isExternal={isExternal} />
              <AvailabilityBadge
                status={form.status}
                label={DRIVER_STATUS_LABELS[form.status] ?? form.status}
              />
            </div>
          ) : undefined
        }
        onBack={onDone}
        actions={
          <>
            {isEdit && (
              <DeleteConfirmButton
                recordName={form.name || 'tài xế này'}
                pending={del.isPending}
                onConfirm={handleDelete}
                warning={DELETE_WARNING}
              />
            )}
            <Button variant="outline" onClick={onDone} disabled={pending}>
              Hủy
            </Button>
            <Button onClick={() => void runOnce(submit)} disabled={pending}>
              {pending && <Loader2 className="size-4 animate-spin" />}
              {isEdit ? 'Lưu thay đổi' : 'Tạo mới'}
            </Button>
          </>
        }
      />
      {/*  Khi SỬA: 2 cột như trang chi tiết phiếu (C-03) — biểu mẫu trái, Trao đổi
          + Lịch sử thao tác dồn cột phải. Khi THÊM mới: một cột, và phải tự chặn
          bề ngang vì không có cột phải bó lại (xem ghi chú ở `vehicle-form`). */}
      <div
        className={cn(
          'grid gap-5',
          isEdit && item ? 'lg:grid-cols-[minmax(0,1fr)_360px]' : 'max-w-3xl',
        )}
      >
        <div className="flex min-w-0 flex-col gap-5">
          <Card className="flex flex-col gap-6 p-5">
            {isEdit ? (
              <>
                {profileSection}
                {licenseSection}
                {sourceSection}
              </>
            ) : (
              <>
                {sourceSection}
                {profileSection}
                {licenseSection}
              </>
            )}
          </Card>
        </div>

        {/*  Cột phải chỉ khi SỬA: Trao đổi trên bản ghi + Lịch sử thao tác (như phiếu). */}
        {isEdit && item && (
          <div className="flex flex-col gap-5">
            <DocumentComments entity="driver" entityId={item.id} />
            <AuditTimeline entity="driver" entityId={item.id} dense showMessage />
          </div>
        )}
      </div>
    </div>
  )
}
