import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Briefcase, Hash, Save, Stamp, Trash2, UserCheck } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { companyApi } from '@/modules/hr/api/company-api'
import { useEmployee } from '@/modules/hr/hooks/use-employees'
import { DocumentComments } from '@/modules/procurement/components/document-comments'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { queryKeys } from '@/shared/constants/query-keys'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { RecordIdentityCard, type IdentityChip } from '@/shared/ui/record-identity-card'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { toastDeletedWithUndo } from '@/shared/utils/toast-undo'
import { sealClerkApi } from '../api/seal-clerk-api'
import { CompanyRow } from '../components/company-row'
import { ClerkStatusBadge } from '../components/status-pill'
import { useSealClerk, useSealClerkByEmployee, useSyncSealClerks } from '../hooks/use-seal-clerks'
import { CLERK_STATUS, CLERK_STATUS_LABELS } from '../types/seal-clerk'

/** Chữ viết tắt từ họ tên (2 từ cuối) để làm ảnh đại diện tạm. */
function initialsOf(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  const picked = words.slice(-2).map((w) => w[0])
  return picked.join('').toUpperCase() || '?'
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-muted-foreground">{label}</label>
      <ReadOnlyValue>{value || '—'}</ReadOnlyValue>
    </div>
  )
}

export function SealClerkDetailPage() {
  const { id } = useParams()
  const clerkId = Number(id) || 0
  const navigate = useNavigate()
  const { can } = usePermission()
  const canManage = can('seal_type', 'write')

  const qc = useQueryClient()
  const { data: row, isLoading, isError } = useSealClerk(clerkId)
  const employeeId = row?.employee_id ?? 0
  const { data: employee } = useEmployee(employeeId)
  const { data: assign } = useSealClerkByEmployee(employeeId)
  const sync = useSyncSealClerks()
  //  Xóa dùng nhánh "im lặng" — tự lo toast ĐỎ có Hoàn tác, không để hook nhả toast xanh.
  const remove = useSyncSealClerks({ silent: true })

  const { data: companies } = useQuery({
    queryKey: queryKeys.hr.companies({ page_size: 500, is_active: true }),
    queryFn: () => companyApi.list({ page_size: 500, is_active: true }),
    enabled: canManage,
  })
  //  Ô chọn công ty GIỐNG phiếu Duyệt dấu: logo trước tên, MST sau tên, tìm theo
  //  tên/MST — dùng chung `MultiPicker` với option {label, hint, avatar}.
  const companyOptions = useMemo(
    () => (companies?.items ?? []).map((c) => ({
      id: c.id, label: c.name, hint: c.tax_code, avatar: c.logo,
    })),
    [companies],
  )

  //  Override giá trị người dùng vừa đổi; nếu chưa đổi thì lấy từ server. Tránh
  //  setState-trong-effect (đồng bộ khi data về) — không xóa mất chỉnh sửa dở.
  const [companyOverride, setCompanyOverride] = useState<number[] | null>(null)
  const [headOverride, setHeadOverride] = useState<boolean | null>(null)
  const [statusOverride, setStatusOverride] = useState<number | null>(null)
  const companyIds = useMemo(
    () => companyOverride ?? assign?.company_ids ?? [],
    [companyOverride, assign],
  )
  const isHead = headOverride ?? assign?.is_head ?? false
  const status = statusOverride ?? assign?.status ?? CLERK_STATUS.active

  //  Công ty ĐÃ CHỌN (theo thứ tự chọn) để hiện thành danh sách thẻ logo + tên + MST.
  const selectedCompanies = useMemo(() => {
    const byId = new Map((companies?.items ?? []).map((c) => [c.id, c]))
    return companyIds.map((id) => byId.get(id)).filter((c): c is NonNullable<typeof c> => Boolean(c))
  }, [companyIds, companies])

  const back = () => navigate(appRoutes.approvalSeal.clerks)

  //  Lưu: KHÔNG thoát trang. Nhả về server rồi bỏ override để hiển thị đúng bản đã lưu.
  const handleSave = () => {
    sync.mutate(
      { employee_id: employeeId, company_ids: companyIds, is_head: isHead, status, anchor_id: clerkId },
      {
        onSuccess: () => {
          setCompanyOverride(null)
          setHeadOverride(null)
          setStatusOverride(null)
        },
      },
    )
  }

  //  Khôi phục lại phân công vừa xóa. Gọi API thẳng + tự invalidate vì lúc bấm Hoàn
  //  tác trang chi tiết đã unmount (đã back về danh sách) — không dựa mutation của trang.
  const restoreAssignment = async (companyIdsToRestore: number[], head: boolean) => {
    try {
      await sealClerkApi.sync({ employee_id: employeeId, company_ids: companyIdsToRestore, is_head: head })
      await qc.invalidateQueries({ queryKey: queryKeys.sealClerk.all })
      toast.success('Đã phục hồi phân công văn thư')
    } catch {
      toast.error('Không phục hồi được phân công')
    }
  }

  //  Xóa = gỡ TOÀN BỘ phân công của văn thư này (đặt lại danh sách rỗng).
  const handleDelete = async () => {
    const ok = await confirm({
      title: 'Xóa phân công văn thư?',
      message:
        `Gỡ toàn bộ công ty phụ trách của ${employee?.full_name || row?.employee_name || 'văn thư này'}. ` +
        'Sau khi xóa, người này KHÔNG còn nhận phiếu đóng dấu của công ty nào cho tới khi được phân công lại.',
      confirmLabel: 'Xóa',
    })
    if (!ok) return

    //  Chụp lại trạng thái đã lưu TRƯỚC khi xóa để nút Hoàn tác dựng lại đúng.
    const prevCompanyIds = assign?.company_ids ?? []
    const prevIsHead = assign?.is_head ?? false

    remove.mutate(
      { employee_id: employeeId, company_ids: [], is_head: false, anchor_id: clerkId },
      {
        onSuccess: () => {
          back()
          toastDeletedWithUndo('Đã xóa phân công văn thư', () =>
            void restoreAssignment(prevCompanyIds, prevIsHead),
          )
        },
      },
    )
  }

  //  Không còn chip "Chính thức" (trạng thái nhân sự) ở đây — thay bằng badge TRẠNG
  //  THÁI PHÂN CÔNG (Đang hoạt động / Nghỉ phép / Ngưng sử dụng) ở góc phải thẻ.
  const chips = useMemo<IdentityChip[]>(() => {
    const out: IdentityChip[] = []
    if (employee?.code) out.push({ icon: Hash, text: employee.code, tone: 'code' })
    if (employee?.position) out.push({ icon: Briefcase, text: employee.position, tone: 'muted' })
    return out
  }, [employee])

  return (
    <PageContainer>
      {/*  Thanh thao tác: Quay lại bên trái, Lưu / Xóa bên phải (khuôn trang chi
          tiết Nhân sự). */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" onClick={back}>
          <ArrowLeft />
          Danh sách
        </Button>
        {row && canManage && (
          <div className="flex items-center gap-2">
            <Button onClick={handleSave} disabled={sync.isPending || remove.isPending}>
              <Save />
              {sync.isPending ? 'Đang lưu…' : 'Lưu'}
            </Button>
            <Button
              variant="outline"
              onClick={handleDelete}
              disabled={sync.isPending || remove.isPending}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 />
              Xóa
            </Button>
          </div>
        )}
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Đang tải…</p>}
      {isError && <p className="text-sm text-destructive">Không tải được phân công.</p>}

      {row && (
        <>
          <RecordIdentityCard
            media={
              <span className="grid size-16 shrink-0 place-items-center overflow-hidden rounded-full border bg-accent">
                <span className="text-xl font-semibold text-primary">
                  {initialsOf(employee?.full_name || row.employee_name || '')}
                </span>
              </span>
            }
            title={employee?.full_name || row.employee_name || `#${row.employee_id}`}
            chips={chips}
            chipsSuffix={<ClerkStatusBadge status={status} />}
          />

          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
            <div className="flex min-w-0 flex-col gap-5">
              <Card className="flex flex-col gap-4 p-5 pb-4">
                {/*  C-03: tiêu đề block = icon + nhãn, gạch dưới KÉO HẾT bề ngang thẻ
                    (`-mx-5 px-5 border-b` bù `p-5`); `-mt-1` + `pb-4` cho padding 16px. */}
                <h3 className="-mx-5 -mt-1 flex items-center gap-2 border-b px-5 pb-3 text-sm font-medium">
                  <UserCheck className="size-4 text-primary" />
                  Thông tin nhân sự
                </h3>
                <div className="grid gap-4 sm:grid-cols-2">
                  <InfoRow label="Email" value={employee?.email} />
                  <InfoRow label="Số điện thoại" value={employee?.phone} />
                  <InfoRow label="Phòng ban" value={employee?.department_name} />
                  <InfoRow label="Chức vụ" value={employee?.position} />
                </div>
              </Card>

              <Card className="flex flex-col gap-4 p-5 pb-4">
                <h3 className="-mx-5 -mt-1 flex items-center gap-2 border-b px-5 pb-3 text-sm font-medium">
                  <Stamp className="size-4 text-primary" />
                  Công ty phụ trách đóng dấu
                </h3>

                {/*  Trạng thái phân công: Tạm dừng thì văn thư ngừng nhận phiếu (badge
                    cùng khuôn với cột trạng thái tài xế ở /vehicle-booking/drivers). */}
                <div className="flex items-center justify-between gap-4 rounded-lg border p-4">
                  <div className="min-w-0">
                    <div className="text-sm font-medium">Trạng thái phân công</div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      Tạm dừng thì văn thư GIỮ danh sách công ty nhưng NGỪNG nhận phiếu đóng dấu.
                    </p>
                  </div>
                  <Select
                    value={String(status)}
                    onValueChange={(v) => setStatusOverride(Number(v))}
                    disabled={!canManage}
                  >
                    <SelectTrigger className="w-44 shrink-0">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(CLERK_STATUS_LABELS).map(([value, label]) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground">Danh sách công ty</label>
                  <MultiPicker<number>
                    options={companyOptions}
                    value={companyIds}
                    onChange={setCompanyOverride}
                    placeholder="Chọn công ty phụ trách"
                    searchPlaceholder="Tìm theo tên hoặc mã số thuế…"
                    emptyMessage="Không tìm thấy công ty nào."
                    contentClassName="w-[min(34rem,92vw)]"
                    clearInTrigger
                    hideChips
                    disabled={!canManage}
                  />

                  {/*  Sau khi chọn, hiện danh sách công ty dạng thẻ: logo + tên + MST. */}
                  {selectedCompanies.length > 0 && (
                    <div className="flex flex-col gap-2 pt-1">
                      {selectedCompanies.map((c) => (
                        <CompanyRow key={c.id} name={c.name} logo={c.logo} taxCode={c.tax_code} />
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-start justify-between gap-4 rounded-lg border p-4">
                  <div>
                    <div className="text-sm font-medium">Đa pháp nhân (văn thư tổng)</div>
                    <p className="text-xs text-muted-foreground">
                      Phụ trách các phiếu cần dấu của NHIỀU công ty (nhiều pháp nhân).
                    </p>
                  </div>
                  <Switch checked={isHead} onCheckedChange={setHeadOverride} disabled={!canManage} />
                </div>
              </Card>
            </div>

            <div className="flex flex-col gap-5">
              <DocumentComments entity="seal_clerk" entityId={row.id} />
              <AuditTimeline entity="seal_clerk" entityId={row.id} showMessage dense />
            </div>
          </div>
        </>
      )}
    </PageContainer>
  )
}
