import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  Briefcase,
  Building,
  Building2,
  ExternalLink,
  Hash,
  Mail,
  Phone,
  Save,
  ShieldCheck,
  Stamp,
  Trash2,
  UserCheck,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { companyApi } from '@/modules/hr/api/company-api'
import { useEmployee } from '@/modules/hr/hooks/use-employees'
import { DocumentComments } from '@/modules/procurement/components/document-comments'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { queryKeys } from '@/shared/constants/query-keys'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { PageContainer } from '@/shared/ui/page-container'
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
import { SealClerkDetailHeader } from '../components/seal-clerk-detail-header'
import { useSealClerk, useSealClerkByEmployee, useSyncSealClerks } from '../hooks/use-seal-clerks'
import { CLERK_STATUS, CLERK_STATUS_LABELS } from '../types/seal-clerk'

function InfoItem({
  icon: Icon,
  label,
  value,
  href,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value?: string | null
  href?: string
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border/50 bg-muted/15 p-3">
      <div className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-md bg-muted text-muted-foreground">
        <Icon className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        {href && value ? (
          <a
            href={href}
            className="mt-0.5 inline-block truncate text-sm font-medium text-primary hover:underline"
          >
            {value}
          </a>
        ) : (
          <p className="mt-0.5 truncate text-sm font-medium text-foreground">
            {value || '—'}
          </p>
        )}
      </div>
    </div>
  )
}

/**
 * Trang CHI TIẾT phân công văn thư đóng dấu (`/approval-seal/clerks/:id`).
 *
 * Bố cục cải tiến:
 * - Header dính đỉnh màn hình (`sticky top-0`) hiển thị tên văn thư, ảnh đại diện,
 *   trạng thái, dải metadata và cụm nút thao tác (Lưu thay đổi, Xóa phân công).
 * - Thân trang chia 2 cột:
 *   + Cột trái: Thông tin nhân sự (hồ sơ HR) & Cấu hình phân công đóng dấu
 *     (Trạng thái, Văn thư tổng, Danh sách công ty có thể gỡ nhanh).
 *   + Cột phải (Sticky scroll): Ghim cố định và cuộn độc lập cho Thẻ tổng quan
 *     phân công, Trao đổi bình luận (`DocumentComments`) & Lịch sử thao tác (`AuditTimeline`).
 */
export function SealClerkDetailPage() {
  const { id } = useParams()
  const clerkId = Number(id) || 0
  const navigate = useNavigate()
  const { can } = usePermission()
  const canManage = can('seal_type', 'write')
  const canViewEmployee = can('employee', 'read')

  const qc = useQueryClient()
  const { data: row, isLoading, isError } = useSealClerk(clerkId)
  const employeeId = row?.employee_id ?? 0
  const { data: employee } = useEmployee(employeeId)
  const { data: assign } = useSealClerkByEmployee(employeeId)
  const sync = useSyncSealClerks()
  // Xóa dùng nhánh "im lặng" — tự lo toast ĐỎ có Hoàn tác, không để hook nhả toast xanh.
  const remove = useSyncSealClerks({ silent: true })

  const { data: companies } = useQuery({
    queryKey: queryKeys.hr.companies({ page_size: 500, is_active: true }),
    queryFn: () => companyApi.list({ page_size: 500, is_active: true }),
  })

  // Ô chọn công ty: logo trước tên, MST sau tên, tìm theo tên/MST
  const companyOptions = useMemo(
    () =>
      (companies?.items ?? []).map((c) => ({
        id: c.id,
        label: c.name,
        hint: c.tax_code,
        avatar: c.logo,
      })),
    [companies],
  )

  // Override giá trị người dùng vừa đổi; nếu chưa đổi thì lấy từ server
  const [companyOverride, setCompanyOverride] = useState<number[] | null>(null)
  const [headOverride, setHeadOverride] = useState<boolean | null>(null)
  const [statusOverride, setStatusOverride] = useState<number | null>(null)

  const companyIds = useMemo(
    () => companyOverride ?? assign?.company_ids ?? [],
    [companyOverride, assign],
  )
  const isHead = headOverride ?? assign?.is_head ?? false
  const status = statusOverride ?? assign?.status ?? CLERK_STATUS.active

  // Kiểm tra có thay đổi chưa lưu
  const isDirty = useMemo(() => {
    if (companyOverride !== null) {
      const orig = assign?.company_ids ?? []
      if (
        companyOverride.length !== orig.length ||
        companyOverride.some((cid) => !orig.includes(cid))
      ) {
        return true
      }
    }
    if (headOverride !== null && headOverride !== (assign?.is_head ?? false)) {
      return true
    }
    if (statusOverride !== null && statusOverride !== (assign?.status ?? CLERK_STATUS.active)) {
      return true
    }
    return false
  }, [companyOverride, headOverride, statusOverride, assign])

  // Công ty ĐÃ CHỌN để hiện thành danh sách thẻ logo + tên + MST
  const selectedCompanies = useMemo(() => {
    const byId = new Map((companies?.items ?? []).map((c) => [c.id, c]))
    return companyIds
      .map((cid) => byId.get(cid))
      .filter((c): c is NonNullable<typeof c> => Boolean(c))
  }, [companyIds, companies])

  const back = () => navigate(appRoutes.approvalSeal.clerks)

  // Lưu phân công
  const handleSave = () => {
    sync.mutate(
      {
        employee_id: employeeId,
        company_ids: companyIds,
        is_head: isHead,
        status,
        anchor_id: clerkId,
      },
      {
        onSuccess: () => {
          setCompanyOverride(null)
          setHeadOverride(null)
          setStatusOverride(null)
        },
      },
    )
  }

  // Khôi phục lại phân công vừa xóa
  const restoreAssignment = async (companyIdsToRestore: number[], head: boolean) => {
    try {
      await sealClerkApi.sync({
        employee_id: employeeId,
        company_ids: companyIdsToRestore,
        is_head: head,
      })
      await qc.invalidateQueries({ queryKey: queryKeys.sealClerk.all })
      toast.success('Đã phục hồi phân công văn thư')
    } catch {
      toast.error('Không phục hồi được phân công')
    }
  }

  // Xóa toàn bộ phân công của văn thư
  const handleDelete = async () => {
    const ok = await confirm({
      title: 'Xóa phân công văn thư?',
      message:
        `Gỡ toàn bộ công ty phụ trách của ${employee?.full_name || row?.employee_name || 'văn thư này'}. ` +
        'Sau khi xóa, người này KHÔNG còn nhận phiếu đóng dấu của công ty nào cho tới khi được phân công lại.',
      confirmLabel: 'Xóa',
    })
    if (!ok) return

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

  // Gỡ nhanh 1 công ty khỏi danh sách phụ trách
  const handleRemoveCompany = (cid: number) => {
    setCompanyOverride(companyIds.filter((id) => id !== cid))
  }

  const employeeName = employee?.full_name || row?.employee_name || `#${row?.employee_id || ''}`
  const employeeCode = employee?.code || row?.employee_code || null
  const departmentName = employee?.department_name || null
  const position = employee?.position || null
  const avatar = employee?.avatar || null

  const headerActions = (
    <div className="flex items-center gap-2">
      {canManage && (
        <>
          <Button
            variant={isDirty ? 'default' : 'outline'}
            onClick={handleSave}
            disabled={sync.isPending || remove.isPending}
            className="shadow-2xs"
          >
            <Save className="size-4" />
            {sync.isPending ? 'Đang lưu…' : isDirty ? 'Lưu thay đổi' : 'Lưu'}
          </Button>
          <Button
            variant="outline"
            onClick={handleDelete}
            disabled={sync.isPending || remove.isPending}
            className="text-destructive shadow-2xs hover:bg-destructive/10 hover:text-destructive"
          >
            <Trash2 className="size-4" />
            Xóa
          </Button>
        </>
      )}
    </div>
  )

  return (
    <PageContainer className="w-full">
      {row && (
        <SealClerkDetailHeader
          employeeName={employeeName}
          employeeCode={employeeCode}
          departmentName={departmentName}
          position={position}
          avatar={avatar}
          status={status}
          isHead={isHead}
          companies={selectedCompanies}
          isDirty={isDirty}
          onBack={back}
          actions={headerActions}
        />
      )}

      {isLoading && (
        <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
          Đang tải thông tin phân công văn thư…
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive">
          Không tải được phân công văn thư. Vui lòng thử lại sau.
        </div>
      )}

      {row && (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
          {/* Cột trái: Thông tin nhân sự & Cấu hình phân công đóng dấu */}
          <div className="flex min-w-0 flex-col gap-6">
            {/* Card 1: Thông tin nhân sự */}
            <Card className="flex flex-col gap-4 p-5 pb-4">
              <div className="-mx-5 -mt-1 flex items-center justify-between border-b px-5 pb-3">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-navy dark:text-foreground">
                  <UserCheck className="size-4 text-primary" />
                  Thông tin nhân sự
                </h3>
                {employeeId > 0 && canViewEmployee && (
                  <Link
                    to={appRoutes.hr.employeeDetail(employeeId)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary transition-colors hover:underline"
                  >
                    Xem hồ sơ chi tiết
                    <ExternalLink className="size-3" />
                  </Link>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <InfoItem
                  icon={Hash}
                  label="Mã nhân viên"
                  value={employee?.code || row.employee_code}
                />
                <InfoItem
                  icon={UserCheck}
                  label="Họ và tên"
                  value={employee?.full_name || row.employee_name}
                />
                <InfoItem
                  icon={Mail}
                  label="Email công việc"
                  value={employee?.email}
                  href={employee?.email ? `mailto:${employee.email}` : undefined}
                />
                <InfoItem
                  icon={Phone}
                  label="Số điện thoại"
                  value={employee?.phone}
                  href={employee?.phone ? `tel:${employee.phone}` : undefined}
                />
                <InfoItem
                  icon={Building2}
                  label="Phòng ban trực thuộc"
                  value={employee?.department_name}
                />
                <InfoItem
                  icon={Briefcase}
                  label="Chức danh / Vị trí"
                  value={employee?.position}
                />
                {employee?.company_name && (
                  <InfoItem
                    icon={Building}
                    label="Pháp nhân trực thuộc"
                    value={employee.company_name}
                  />
                )}
                {employee?.status_label && (
                  <InfoItem
                    icon={UserCheck}
                    label="Trạng thái nhân sự"
                    value={employee.status_label}
                  />
                )}
              </div>
            </Card>

            {/* Card 2: Cấu hình phân công đóng dấu */}
            <Card className="flex flex-col gap-5 p-5 pb-4">
              <div className="-mx-5 -mt-1 flex items-center justify-between border-b px-5 pb-3">
                <div>
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-navy dark:text-foreground">
                    <Stamp className="size-4 text-primary" />
                    Cấu hình phân công đóng dấu
                  </h3>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Thiết lập quyền nhận phiếu và danh mục công ty được giao phụ trách
                  </p>
                </div>
              </div>

              {/* Block 1: Trạng thái phân công */}
              <div className="flex flex-col gap-3 rounded-lg border border-border/70 bg-muted/10 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="text-sm font-medium text-navy dark:text-foreground">
                    Trạng thái phân công
                  </div>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Tạm dừng hoặc ngưng sử dụng thì văn thư giữ cấu hình nhưng ngừng nhận phiếu đóng dấu mới.
                  </p>
                </div>
                <Select
                  value={String(status)}
                  onValueChange={(v) => setStatusOverride(Number(v))}
                  disabled={!canManage}
                >
                  <SelectTrigger className="w-full sm:w-48 shrink-0 bg-background">
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

              {/* Block 2: Chế độ đa pháp nhân (Văn thư tổng) */}
              <div className="flex items-start justify-between gap-4 rounded-lg border border-border/70 bg-muted/10 p-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-md bg-purple-500/10 text-purple-600 dark:bg-purple-500/20 dark:text-purple-300">
                    <ShieldCheck className="size-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-navy dark:text-foreground">
                        Văn thư tổng (Đa pháp nhân)
                      </span>
                      <Badge variant="outline" className="text-[11px] font-normal border-purple-500/30 text-purple-600 dark:text-purple-300">
                        Toàn tập đoàn
                      </Badge>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      Cho phép tiếp nhận và xử lý các phiếu đóng dấu liên quan đến nhiều công ty (nhiều pháp nhân) cùng lúc.
                    </p>
                  </div>
                </div>
                <Switch
                  checked={isHead}
                  onCheckedChange={setHeadOverride}
                  disabled={!canManage}
                  aria-label="Kích hoạt chế độ văn thư tổng"
                />
              </div>

              {/* Block 3: Công ty phụ trách đóng dấu */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Công ty phụ trách đóng dấu
                    </label>
                    <Badge variant="secondary" className="font-mono text-xs">
                      {selectedCompanies.length}
                    </Badge>
                  </div>
                  {canManage && companyIds.length > 0 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs text-muted-foreground hover:text-destructive"
                      onClick={() => setCompanyOverride([])}
                    >
                      Xóa tất cả
                    </Button>
                  )}
                </div>

                <MultiPicker<number>
                  options={companyOptions}
                  value={companyIds}
                  onChange={setCompanyOverride}
                  placeholder="Tìm và chọn công ty phụ trách…"
                  searchPlaceholder="Tìm theo tên công ty hoặc mã số thuế…"
                  emptyMessage="Không tìm thấy công ty nào phù hợp."
                  contentClassName="w-[min(34rem,92vw)]"
                  clearInTrigger
                  hideChips
                  disabled={!canManage}
                />

                {/* Danh sách thẻ công ty đã chọn */}
                {selectedCompanies.length > 0 ? (
                  <div className="flex flex-col gap-2 pt-1">
                    {selectedCompanies.map((c) => (
                      <CompanyRow
                        key={c.id}
                        name={c.name}
                        logo={c.logo}
                        taxCode={c.tax_code}
                        onRemove={canManage ? () => handleRemoveCompany(c.id) : undefined}
                        disabled={!canManage}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/80 bg-muted/10 p-6 text-center">
                    <Building className="size-8 text-muted-foreground/60" />
                    <p className="mt-2 text-sm font-medium text-foreground">Chưa chọn công ty nào</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      Văn thư này cần được phân công ít nhất một công ty để bắt đầu nhận phiếu đóng dấu.
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Cột phải: Sticky scroll theo header */}
          <div className="flex flex-col gap-5 lg:sticky lg:top-[calc(var(--clerk-header-h,0px)+0.75rem)] lg:max-h-[calc(100dvh-3.5rem-var(--clerk-header-h,0px)-2rem)] lg:self-start lg:overflow-y-auto pr-0.5">
            {/* Card Tổng quan phân công */}
            <Card className="flex flex-col gap-4 p-5 pb-4">
              <h3 className="-mx-5 -mt-1 flex items-center gap-2 border-b px-5 pb-3 text-sm font-semibold text-navy dark:text-foreground">
                <ShieldCheck className="size-4 text-primary" />
                Tổng quan phân công
              </h3>

              <div className="space-y-2.5 text-sm">
                <div className="flex items-center justify-between gap-2 rounded-md bg-muted/30 px-3 py-2">
                  <span className="text-xs text-muted-foreground">Trạng thái nhận phiếu</span>
                  {status === CLERK_STATUS.active ? (
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
                      Sẵn sàng nhận phiếu
                    </span>
                  ) : status === CLERK_STATUS.onLeave ? (
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
                      <span className="size-2 rounded-full bg-amber-500" />
                      Tạm dừng (Nghỉ phép)
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                      <span className="size-2 rounded-full bg-slate-400" />
                      Ngưng hoạt động
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between gap-2 rounded-md bg-muted/30 px-3 py-2">
                  <span className="text-xs text-muted-foreground">Loại hình văn thư</span>
                  <span className="text-xs font-medium text-foreground">
                    {isHead ? 'Văn thư tổng (Đa pháp nhân)' : 'Văn thư đơn vị'}
                  </span>
                </div>

                <div className="flex items-center justify-between gap-2 rounded-md bg-muted/30 px-3 py-2">
                  <span className="text-xs text-muted-foreground">Số công ty phụ trách</span>
                  <span className="font-mono text-xs font-bold text-primary tabular-nums">
                    {companyIds.length} công ty
                  </span>
                </div>

                {companyIds.length === 0 && (
                  <div className="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-300">
                    <AlertCircle className="mt-0.5 size-4 shrink-0" />
                    <span>
                      Văn thư này hiện chưa được phân công công ty nào. Cần chọn công ty để có thể tiếp nhận phiếu đóng dấu.
                    </span>
                  </div>
                )}
              </div>
            </Card>

            {/* Trao đổi bình luận */}
            <DocumentComments entity="seal_clerk" entityId={row.id} />

            {/* Lịch sử thao tác */}
            <AuditTimeline entity="seal_clerk" entityId={row.id} showMessage dense />
          </div>
        </div>
      )}
    </PageContainer>
  )
}
