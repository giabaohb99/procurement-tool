import { Plus, UserX, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'
import { SearchSelect } from '@/shared/ui/search-select'
import { cn } from '@/shared/utils/cn'

import {
  useAddEmailExclusion,
  useEmailExclusions,
  useRemoveEmailExclusion,
} from '../hooks/use-email-exclusions'
import { useEmailTemplates } from '../hooks/use-email-templates'
import type { ExclusionScope } from '../types/email-exclusion'

const SCOPES: { value: ExclusionScope; label: string }[] = [
  { value: 'employee', label: 'Cá nhân' },
  { value: 'department', label: 'Phòng ban' },
  { value: 'company', label: 'Công ty' },
]

//  SearchSelect coi value "" là "chưa chọn" (hiện placeholder), nên "mọi mẫu" phải
//  dùng một giá trị khác rỗng rồi quy về "" khi gửi backend.
const ALL_EVENTS = 'ALL'

/**
 * Loại trừ email — chọn cá nhân / phòng ban / công ty để KHÔNG gửi email thông báo
 * (backend lọc theo hồ sơ nhân sự). Chuông trong ứng dụng vẫn gửi. Nằm trong Cấu
 * hình hệ thống, gác `setting.write` như cả trang.
 */
export function EmailExclusionPanel({ canWrite }: { canWrite: boolean }) {
  const { data: exclusions } = useEmailExclusions()
  const add = useAddEmailExclusion()
  const remove = useRemoveEmailExclusion()

  const { data: templates } = useEmailTemplates()

  const [scope, setScope] = useState<ExclusionScope>('employee')
  const [refId, setRefId] = useState('')
  const [event, setEvent] = useState(ALL_EVENTS)

  //  Chỉ nạp danh bạ của mức đang chọn (và khi có quyền sửa) — tránh gọi thừa.
  const employees = useEmployees({ page_size: 500 }, { enabled: canWrite && scope === 'employee' })
  const departments = useDepartments({ page_size: 500 })
  const companies = useCompanies({ page_size: 500 }, { enabled: canWrite && scope === 'company' })

  //  "Áp cho mẫu": Tất cả mẫu + từng mẫu email (kèm người nhận để phân biệt 2 dòng cùng bước).
  const eventOptions = useMemo(
    () => [
      { value: ALL_EVENTS, label: 'Tất cả mẫu' },
      ...(templates ?? []).map((t) => ({ value: t.event, label: `${t.label} → ${t.recipient}` })),
    ],
    [templates],
  )

  const options = useMemo(() => {
    if (scope === 'employee') {
      return (employees.data?.items ?? []).map((e) => ({
        value: String(e.id),
        label: e.code ? `${e.full_name} (${e.code})` : e.full_name,
      }))
    }
    if (scope === 'department') {
      return (departments.data?.items ?? []).map((d) => ({ value: String(d.id), label: d.name }))
    }
    return (companies.data?.items ?? []).map((c) => ({ value: String(c.id), label: c.name }))
  }, [scope, employees.data, departments.data, companies.data])

  function onAdd() {
    const opt = options.find((o) => o.value === refId)
    if (!opt) {
      toast.error('Hãy chọn đối tượng cần loại trừ')
      return
    }
    add.mutate(
      { scope, ref_id: Number(refId), label: opt.label, event: event === ALL_EVENTS ? '' : event },
      {
        onSuccess: () => {
          toast.success('Đã thêm loại trừ email')
          setRefId('')
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    )
  }

  return (
    <FormCard title="Loại trừ email" icon={UserX} iconClassName="text-muted-foreground">
      <p className="mb-3 text-xs text-muted-foreground">
        Không gửi <strong>email</strong> thông báo cho các đối tượng dưới đây (theo hồ sơ nhân
        sự) — áp cho <strong>tất cả mẫu</strong> hoặc <strong>từng mẫu email</strong>. Chuông
        trong ứng dụng vẫn gửi bình thường.
      </p>

      {/* Danh sách đang loại trừ */}
      {(exclusions ?? []).length === 0 ? (
        <p className="rounded-md bg-accent px-3 py-2 text-[13px] text-muted-foreground">
          Chưa loại trừ ai — mọi người liên quan đều nhận email.
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {(exclusions ?? []).map((ex) => (
            <span
              key={ex.id}
              className="inline-flex items-center gap-1.5 rounded-full border bg-card py-1 pl-2.5 pr-1.5 text-sm"
            >
              <Badge variant="outline" className="px-1.5 py-0 text-[11px]">
                {ex.scope_label}
              </Badge>
              {ex.label || `#${ex.ref_id}`}
              <span className="text-xs text-muted-foreground">· {ex.event_label}</span>
              {canWrite && (
                <button
                  type="button"
                  aria-label="Bỏ loại trừ"
                  onClick={() => remove.mutate(ex.id)}
                  className="rounded-full p-0.5 text-muted-foreground hover:bg-accent hover:text-destructive"
                >
                  <X className="size-3.5" />
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      {/* Thêm mới */}
      {canWrite && (
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-dashed pt-3">
          <div className="flex rounded-md border p-0.5">
            {SCOPES.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => {
                  setScope(s.value)
                  setRefId('')
                }}
                className={cn(
                  'rounded px-3 py-1 text-sm',
                  scope === s.value
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {s.label}
              </button>
            ))}
          </div>
          <div className="min-w-56 flex-1">
            <SearchSelect
              value={refId}
              onChange={setRefId}
              options={options}
              placeholder={`Chọn ${SCOPES.find((s) => s.value === scope)?.label.toLowerCase()}…`}
            />
          </div>
          <div className="flex min-w-56 items-center gap-1.5">
            <span className="shrink-0 text-xs text-muted-foreground">Áp cho</span>
            <div className="min-w-0 flex-1">
              <SearchSelect
                value={event}
                onChange={setEvent}
                options={eventOptions}
                placeholder="Tất cả mẫu"
              />
            </div>
          </div>
          <Button onClick={onAdd} disabled={!refId || add.isPending}>
            <Plus className="size-4" />
            Thêm loại trừ
          </Button>
        </div>
      )}
    </FormCard>
  )
}
