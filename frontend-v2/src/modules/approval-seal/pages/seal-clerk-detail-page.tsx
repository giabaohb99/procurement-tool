import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Save, ShieldCheck, Stamp, Trash2 } from 'lucide-react'
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
import { SealClerkEmployeeCard } from '../components/seal-clerk-employee-card'
import { useSealClerk, useSealClerkByEmployee, useSyncSealClerks } from '../hooks/use-seal-clerks'
import { CLERK_STATUS, CLERK_STATUS_LABELS } from '../types/seal-clerk'

/**
 * Trang CHI TIẾT phân công văn thư đóng dấu (`/approval-seal/clerks/:id`).
 *
 * Bố cục cải tiến:
 * - Header dính đỉnh màn hình (`sticky top-0`) hiển thị tên văn thư, ảnh đại diện,
 *   trạng thái, dải metadata và cụm nút thao tác (Lưu thay đổi, Xóa phân công).
 * - Thân trang chia 2 cột (xếp lại 22/09/2026):
 *   + Cột trái = nơi LÀM VIỆC: Cấu hình phân công đóng dấu (Trạng thái · Văn thư
 *     tổng · Danh sách công ty), rồi Trao đổi.
 *   + Cột phải = khối CHỈ ĐỌC: Thông tin nhân sự (`SealClerkEmployeeCard`) và Lịch
 *     sử thao tác. Cuộn theo trang, KHÔNG ghim và KHÔNG có vùng cuộn riêng.
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
          {/* Cột trái: phần việc chính của trang + hai khối dài theo thời gian */}
          <div className="flex min-w-0 flex-col gap-6">
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
                  //  Khung rỗng + câu cảnh báo (dời từ thẻ «Tổng quan phân công»
                  //  ở cột phải sang, 22/09/2026): cảnh báo phải đứng ngay cạnh
                  //  thứ sửa được nó — ô chọn công ty ở ngay trên. Nằm tận cột
                  //  bên kia thì người đọc phải tự nối hai chỗ với nhau.
                  <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-amber-500/40 bg-amber-500/5 p-6 text-center">
                    <AlertCircle className="size-8 text-amber-500/70" />
                    <p className="mt-2 text-sm font-medium text-foreground">Chưa chọn công ty nào</p>
                    <p className="mt-0.5 max-w-sm text-xs text-muted-foreground">
                      Văn thư này chưa nhận phiếu đóng dấu của công ty nào. Chọn ít nhất một
                      công ty ở ô phía trên rồi bấm <span className="font-medium">Lưu</span>.
                    </p>
                  </div>
                )}
              </div>
            </Card>

            {/*  Trao đổi khép lại CỘT TRÁI: nó là thứ NGƯỜI TA GÕ VÀO nên cần bề
                 ngang của cột chính — ô nhập rộng 380px thì một câu ba dòng đọc
                 như cột báo. Lịch sử thao tác thì ngược lại, sang cột phải. */}
            <DocumentComments entity="seal_clerk" entityId={row.id} />
          </div>

          {/*  Cột phải — khối THAM CHIẾU, chỉ đọc. Thẻ «Tổng quan phân công» đã
               BỎ (22/09/2026): ba dòng của nó — trạng thái nhận phiếu · loại hình
               văn thư · số công ty — đọc từ đúng ba ô người dùng đang chỉnh ở cột
               trái, tức là một tấm gương. Tệ hơn: nó soi cả những thay đổi CHƯA
               LƯU, nên nó không nói được điều gì mà nhìn sang cột trái không
               thấy. Trạng thái và loại hình còn nằm sẵn trên dải tóm tắt ở tiêu
               đề trang. Câu cảnh báo «chưa phân công công ty nào» thì KHÔNG bỏ —
               nó dời xuống ngay dưới danh sách công ty, chỗ người ta sửa được.

               ⚠️ KHÔNG có vùng cuộn riêng (cùng luật đã áp cho chi tiết phiếu
               đóng dấu): không `sticky`, không `max-h`, không `overflow-y-auto`
               — hai vùng cuộn cạnh nhau làm bánh xe chuột đổi nghĩa tùy con trỏ
               đang đậu ở nửa nào. */}
          <div className="flex flex-col gap-5">
            <SealClerkEmployeeCard
              employeeId={employeeId}
              fallbackName={row.employee_name}
              fallbackCode={row.employee_code}
              employee={employee}
              canViewEmployee={canViewEmployee}
            />

            {/*  Lịch sử thao tác đứng CUỐI cột phải (dời 22/09/2026 — cùng cách
                 đã chốt ở phiếu đặt xe, CR-439). Nó chỉ để ĐỌC và mỗi dòng là một
                 câu ngắn tự mô tả nên chịu được cột hẹp; để nó ở cột trái thì cột
                 phải chỉ còn một thẻ cao 300px, bỏ trống hơn nửa màn. Tự dựng thẻ
                 có tiêu đề riêng nên KHÔNG bọc thêm `Card` kẻo lặp tiêu đề. */}
            <AuditTimeline entity="seal_clerk" entityId={row.id} showMessage dense />
          </div>
        </div>
      )}
    </PageContainer>
  )
}
