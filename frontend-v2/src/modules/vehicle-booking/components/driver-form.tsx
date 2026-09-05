import { Loader2, Search, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { useCrudDelete, useCrudSave } from '@/shared/crud'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { BookingPageHeader } from './booking-page-header'
import { employeeInitials } from '@/modules/hr/types/employee'
import type { UserAccount } from '@/modules/hr/types/user-account'
import { MIN_PHONE_DIGITS, useDriverAccountSearch } from '../hooks/use-driver-account-search'
import { SUPPLIER_TYPE, type Driver } from '../types/driver'

const API_PATH = '/api/drivers'
const TITLE = 'Danh mục Tài xế'
const DELETE_WARNING = 'Tài xế này có thể đang được phân cho phiếu đặt xe.'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'on_leave', label: 'Nghỉ phép' },
  { value: 'inactive', label: 'Ngưng sử dụng' },
]

type Mode = 'internal' | 'external'

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
 * Nội bộ: tìm tài khoản nhân sự theo SĐT (thẻ avatar + tên), tự điền, khóa xám.
 * Thuê ngoài: Doanh nghiệp / Cá nhân + MST · địa chỉ thuế · CCCD. Trang sửa có
 * khối Lịch sử thao tác; khóa nguồn + loại NCC khi sửa.
 */
export function DriverForm({ item, title, onDone }: DriverFormProps) {
  const save = useCrudSave<Driver>(API_PATH, TITLE)
  const del = useCrudDelete(API_PATH, TITLE)
  const isEdit = Boolean(item)

  const [mode, setMode] = useState<Mode>(item?.is_external ? 'external' : 'internal')
  const [form, setForm] = useState<FormState>(() => initialState(item))
  const [phoneSearch, setPhoneSearch] = useState('')
  const [selectedAcc, setSelectedAcc] = useState<UserAccount | null>(null)

  const searchResult = useDriverAccountSearch(phoneSearch)
  const results = searchResult.data?.items ?? []

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const pending = save.isPending || del.isPending
  const linked = mode === 'internal' && form.user_id != null

  function selectAccount(acc: UserAccount) {
    setForm((prev) => ({
      ...prev,
      name: acc.full_name || '',
      phone: acc.phone || '',
      email: acc.contact_email || '',
      user_id: acc.id,
    }))
    setSelectedAcc(acc)
  }

  function clearSelection() {
    setSelectedAcc(null)
    setPhoneSearch('')
    setForm((prev) => ({ ...prev, name: '', phone: '', email: '', user_id: null }))
  }

  function validate(): string {
    if (!form.name.trim())
      return mode === 'internal'
        ? 'Vui lòng chọn tài khoản nhân sự (tìm theo số điện thoại).'
        : 'Thiếu tên tài xế.'
    if (!form.phone.trim()) return 'Thiếu số điện thoại.'
    if (!form.license_number.trim()) return 'Thiếu số giấy phép lái xe.'
    if (mode === 'external' && form.supplier_type === SUPPLIER_TYPE.enterprise) {
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
    const isEnterprise = mode === 'external' && form.supplier_type === SUPPLIER_TYPE.enterprise
    const isIndividual = mode === 'external' && form.supplier_type === SUPPLIER_TYPE.individual
    await save.mutateAsync({
      id: item?.id,
      values: {
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
        license_number: form.license_number.trim(),
        license_class: form.license_class.trim(),
        status: form.status,
        is_external: mode === 'external',
        supplier_type: mode === 'external' ? form.supplier_type : SUPPLIER_TYPE.none,
        external_company: isEnterprise ? form.external_company.trim() : '',
        tax_code: isEnterprise ? form.tax_code.trim() : '',
        tax_address: isEnterprise ? form.tax_address.trim() : '',
        id_number: isIndividual ? form.id_number.trim() : '',
        user_id: mode === 'internal' ? form.user_id : null,
      },
    })
    onDone()
  }

  async function handleDelete() {
    if (!item) return
    await del.mutateAsync(item.id)
    onDone()
  }

  return (
    <div className="flex w-full flex-col">
      <BookingPageHeader
        title={title}
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
            <Button onClick={submit} disabled={pending}>
              {pending && <Loader2 className="size-4 animate-spin" />}
              {isEdit ? 'Lưu thay đổi' : 'Tạo mới'}
            </Button>
          </>
        }
      />
      <div className="flex flex-col gap-5">
      <Card className="flex flex-col gap-4 p-5">
        {/* Nút chọn nguồn: Nội bộ (xanh) | Thuê ngoài (hổ phách) — khóa khi SỬA. */}
        <div className="grid grid-cols-2 gap-2 sm:max-w-md">
          <ModeButton active={mode === 'internal'} tone="blue" disabled={isEdit} onClick={() => setMode('internal')}>
            Nội bộ
          </ModeButton>
          <ModeButton active={mode === 'external'} tone="amber" disabled={isEdit} onClick={() => setMode('external')}>
            Thuê ngoài
          </ModeButton>
        </div>
        {isEdit && (
          <p className="-mt-2 text-xs text-muted-foreground">
            Không đổi được nguồn (nội bộ / thuê ngoài) của tài xế đã tạo.
          </p>
        )}

        {mode === 'internal' ? (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>
                Tài khoản nhân sự
                <RequiredMark hint="Tìm và chọn theo số điện thoại" />
              </Label>
              {linked ? (
                <div className="flex items-center gap-3 rounded-lg border bg-muted/40 px-3 py-2 transition-colors">
                  <Avatar className="size-8">
                    <AvatarImage src={selectedAcc?.avatar} alt={form.name} />
                    <AvatarFallback className="text-xs">{employeeInitials(form.name)}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{form.name}</div>
                    <div className="truncate text-xs text-muted-foreground">
                      {[form.phone, selectedAcc?.code].filter(Boolean).join(' · ')}
                    </div>
                  </div>
                  <Button type="button" variant="ghost" size="icon" className="size-7 shrink-0" onClick={clearSelection} aria-label="Đổi tài khoản">
                    <X className="size-4" />
                  </Button>
                </div>
              ) : (
                <>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input className="pl-9" inputMode="numeric" placeholder="Nhập đủ số điện thoại để tìm…" value={phoneSearch} onChange={(e) => setPhoneSearch(e.target.value)} />
                  </div>
                  {searchResult.enabled ? (
                    <div className="flex max-h-52 flex-col gap-1 overflow-y-auto rounded-lg border p-1">
                      {searchResult.isLoading && (
                        <p className="px-2 py-3 text-center text-sm text-muted-foreground">Đang tìm…</p>
                      )}
                      {!searchResult.isLoading && results.length === 0 && (
                        <p className="px-2 py-3 text-center text-sm text-muted-foreground">
                          Không tìm thấy nhân sự nào khớp số điện thoại này.
                        </p>
                      )}
                      {results.map((acc) => (
                        <button key={acc.id} type="button" onClick={() => selectAccount(acc)} className="flex items-center gap-3 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-accent">
                          <Avatar className="size-8">
                            <AvatarImage src={acc.avatar} alt={acc.full_name} />
                            <AvatarFallback className="text-xs">{employeeInitials(acc.full_name)}</AvatarFallback>
                          </Avatar>
                          <div className="min-w-0">
                            <div className="truncate text-sm font-medium">{acc.full_name}</div>
                            <div className="truncate text-xs text-muted-foreground">
                              {[acc.phone, acc.code].filter(Boolean).join(' · ') || acc.email}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Gõ đủ số điện thoại ({MIN_PHONE_DIGITS} chữ số trở lên) để hiện danh sách.
                    </p>
                  )}
                </>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Họ tên">
                <LockedInput value={form.name} placeholder="Tự điền khi chọn tài khoản" />
              </Field>
              <Field label="Số điện thoại">
                <LockedInput value={form.phone} placeholder="Tự điền khi chọn tài khoản" />
              </Field>
              <Field label="Email" fullWidth>
                <LockedInput value={form.email} placeholder="Tự điền khi chọn tài khoản" />
              </Field>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Số giấy phép lái xe" required>
                <Input value={form.license_number} onChange={(e) => set('license_number', e.target.value)} placeholder="VD: 790112345678" />
              </Field>
              <Field label="Hạng GPLX">
                <Input value={form.license_class} onChange={(e) => set('license_class', e.target.value)} placeholder="VD: B2, C, D" />
              </Field>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Loại nhà cung cấp</Label>
              <div className="grid grid-cols-2 gap-2 sm:max-w-md">
                <ModeButton active={form.supplier_type === SUPPLIER_TYPE.enterprise} tone="blue" disabled={isEdit} onClick={() => set('supplier_type', SUPPLIER_TYPE.enterprise)}>
                  Doanh nghiệp
                </ModeButton>
                <ModeButton active={form.supplier_type === SUPPLIER_TYPE.individual} tone="amber" disabled={isEdit} onClick={() => set('supplier_type', SUPPLIER_TYPE.individual)}>
                  Cá nhân
                </ModeButton>
              </div>
              {isEdit && (
                <p className="text-xs text-muted-foreground">
                  Không đổi được loại nhà cung cấp của tài xế đã tạo.
                </p>
              )}
            </div>

            {form.supplier_type === SUPPLIER_TYPE.individual ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Tên tài xế" required>
                  <Input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="VD: Lê Minh Thông" />
                </Field>
                <Field label="CCCD">
                  <Input value={form.id_number} onChange={(e) => set('id_number', e.target.value)} placeholder="Số căn cước công dân" />
                </Field>
                <Field label="Số giấy phép lái xe" required>
                  <Input value={form.license_number} onChange={(e) => set('license_number', e.target.value)} placeholder="VD: 790112345678" />
                </Field>
                <Field label="Hạng GPLX">
                  <Input value={form.license_class} onChange={(e) => set('license_class', e.target.value)} placeholder="VD: B2, C, D" />
                </Field>
                <Field label="Email">
                  <Input value={form.email} onChange={(e) => set('email', e.target.value)} placeholder="VD: taixe@ncc.com" />
                </Field>
                <Field label="Số điện thoại" required>
                  <Input value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="VD: 0907507103" />
                </Field>
              </div>
            ) : (
              <>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Tên doanh nghiệp" required>
                    <Input value={form.external_company} onChange={(e) => set('external_company', e.target.value)} placeholder="VD: Công ty Vận tải ABC" />
                  </Field>
                  <Field label="Mã số thuế" required>
                    <Input value={form.tax_code} onChange={(e) => set('tax_code', e.target.value)} placeholder="VD: 0312345678" />
                  </Field>
                  <Field label="Địa chỉ thuế" required fullWidth>
                    <Input value={form.tax_address} onChange={(e) => set('tax_address', e.target.value)} placeholder="Địa chỉ đăng ký thuế" />
                  </Field>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Tên tài xế" required>
                    <Input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="VD: Lê Minh Thông" />
                  </Field>
                  <Field label="Số điện thoại" required>
                    <Input value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="VD: 0907507103" />
                  </Field>
                  <Field label="Số giấy phép lái xe" required>
                    <Input value={form.license_number} onChange={(e) => set('license_number', e.target.value)} placeholder="VD: 790112345678" />
                  </Field>
                  <Field label="Hạng GPLX">
                    <Input value={form.license_class} onChange={(e) => set('license_class', e.target.value)} placeholder="VD: B2, C, D" />
                  </Field>
                  <Field label="Email" fullWidth>
                    <Input value={form.email} onChange={(e) => set('email', e.target.value)} placeholder="VD: taixe@ncc.com" />
                  </Field>
                </div>
              </>
            )}
          </div>
        )}

        <Field label="Trạng thái">
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
        </Field>

      </Card>

      {isEdit && item && <AuditTimeline entity="driver" entityId={item.id} dense showMessage />}
      </div>
    </div>
  )
}

function ModeButton({
  active,
  tone,
  disabled,
  onClick,
  children,
}: {
  active: boolean
  tone: 'blue' | 'amber'
  disabled?: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'flex h-10 items-center justify-center rounded-lg text-sm font-semibold transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-60',
        !active && 'border border-input bg-background text-muted-foreground hover:bg-accent',
        active && tone === 'blue' && 'border-2 border-blue-500 bg-blue-50 text-blue-600 dark:bg-blue-950/40',
        active && tone === 'amber' && 'border-2 border-amber-500 bg-amber-50 text-amber-600 dark:bg-amber-950/40',
      )}
    >
      {children}
    </button>
  )
}

function LockedInput({ value, placeholder }: { value: string; placeholder?: string }) {
  return (
    <Input
      readOnly
      tabIndex={-1}
      value={value}
      placeholder={placeholder}
      className="cursor-default bg-muted text-muted-foreground focus-visible:ring-0"
    />
  )
}

function Field({
  label,
  required,
  fullWidth,
  children,
}: {
  label: string
  required?: boolean
  fullWidth?: boolean
  children: React.ReactNode
}) {
  return (
    <div className={cn('flex flex-col gap-1.5', fullWidth && 'sm:col-span-2')}>
      <Label>
        {label}
        {required && <RequiredMark />}
      </Label>
      {children}
    </div>
  )
}
