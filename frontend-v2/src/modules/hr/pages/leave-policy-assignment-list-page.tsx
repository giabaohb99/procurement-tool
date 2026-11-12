import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'
import { Plus, Users } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { useAuthStore } from '@/core/auth/auth-store'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { useCrudList } from '@/shared/crud'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { useUrlSort } from '@/shared/hooks/use-url-sort'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { LeavePolicyAssignDialog } from '../components/leave-policy-assign-dialog'
import { LeavePolicyAssignmentDeleteDialog } from '../components/leave-policy-assignment-delete-dialog'
import { LeavePolicyAssignmentEndDialog } from '../components/leave-policy-assignment-end-dialog'
import { LeavePolicyAssignmentListToolbar } from '../components/leave-policy-assignment-list-toolbar'
import { LeavePolicyAssignmentMobileCard } from '../components/leave-policy-assignment-mobile-card'
import { LeavePolicyAssignmentRowActions } from '../components/leave-policy-assignment-row-actions'
import { buildLeavePolicyAssignmentColumns } from '../config/leave-policy-assignment-columns'
import { useCompanies } from '../hooks/use-companies'
import { useLeavePolicyAssignments } from '../hooks/use-leave-policy'
import type { LeavePolicy, LeavePolicyAssignment } from '../types/leave-policy'
import { LEAVE_POLICY_HUB_TITLE } from '../utils/leave-policy-hub-tabs'
import { ASSIGNMENT_ACTIVE_TODAY, ASSIGNMENT_FILTER_ALL as ALL } from '../utils/leave-policy-assignment-filters'
import { todayInVietnamISO } from '../utils/work-roster-range'

interface LeavePolicyAssignmentListPageProps {
  /** Dải tab Thiết lập nhân sự — đặt TRÊN tiêu đề, cùng khe `topContent` của `CrudListPage` (duoc-CR-753). */
  topContent?: ReactNode
  /** Hàng tiêu đề gọn trong cụm tab Thiết lập — cùng nghĩa `compactHeader` của `CrudListPage` (duoc-CR-753). */
  compactHeader?: boolean
  /** Thanh tab của màn Chính sách nghỉ phép — chèn giữa tiêu đề và bảng (cùng khe của `CrudListPage`). */
  beforeContent?: ReactNode
  /** Class ghim thanh công cụ ở khổ điện thoại, mốc `top` theo dải nằm trên (`list-sticky.ts`). */
  toolbarClassName?: string
}

/**
 * Tab PHÂN BỔ của màn Chính sách nghỉ phép — `/hr/leave-policy-assignments?tab=assignments` (duoc-CR-717 dựng thành
 * màn riêng "Phân bổ chính sách"; duoc-CR-750 gom làm tab, `leave-policy-hub-page.tsx` dựng nó).
 *
 * Tiêu đề trang vẫn do chính màn này vẽ để hai nút Phân bổ · Phân bổ hàng loạt nằm ở đầu trang và đổi theo tab
 * (tab Chính sách thì `CrudListPage` vẽ tiêu đề kèm nút Thêm chính sách).
 *
 * Route gác `leave_balance.write` HOẶC `leave_type.write` (mục menu, xem `routes.tsx`); tab này chỉ dựng khi có
 * `leave_balance.write`, các nút ghi vẫn tự gác `write` phòng khi trang được dựng ở chỗ khác. Ô "Trạng thái" lọc phân
 * bổ CÒN HIỆU LỰC HÔM NAY (`active_on`, giờ VN), cột Trạng thái đọc `state` của backend. Dòng của chính người đang
 * đăng nhập không có nút Kết thúc / Xóa (D5).
 */
const ASSIGNMENT_PAGE_DESCRIPTION =
  'Gán chính sách cho từng nhân sự theo khoảng ngày. Người không có phân bổ nhận hạn mức của loại nghỉ.'

export function LeavePolicyAssignmentListPage({
  topContent,
  compactHeader,
  beforeContent,
  toolbarClassName,
}: LeavePolicyAssignmentListPageProps = {}) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canWrite = can('leave_balance', 'write')
  const canReadCompany = can('company', 'read')
  const myEmployeeId = useAuthStore((s) => s.user?.employee_id)

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [policyId, setPolicyId] = useUrlParamState('policy_id', ALL)
  const [active, setActive] = useUrlParamState('active', ALL)
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  //  duoc-CR-748: sắp xếp tại máy chủ (nhân sự, chính sách, từ / đến ngày, trạng thái, ghi chú); không chọn = từ ngày mới nhất trước.
  const { sortBy, sortDir, handleSortChange } = useUrlSort()
  const [page, setPage] = usePageResetOnFilterChange([debouncedValue, policyId, active, companyId, pageSize, sortBy, sortDir])

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue.trim()) p.search = debouncedValue.trim()
    if (policyId !== ALL) p.policy_id = policyId
    if (companyId !== ALL) p.company_id = companyId
    if (active === ASSIGNMENT_ACTIVE_TODAY) p.active_on = todayInVietnamISO()
    if (sortBy) {
      p.sort_by = sortBy
      p.sort_dir = sortDir
    }
    return p
  }, [page, pageSize, debouncedValue, policyId, companyId, active, sortBy, sortDir])
  const { data, isLoading, isError } = useLeavePolicyAssignments(params)

  //  Mọi gói (kể cả đã ngừng) — lọc theo gói đã ngừng vẫn phải được.
  const { data: policyData } = useCrudList<LeavePolicy>('/api/leave-policies', {
    page_size: 200,
    sort_by: 'name',
    sort_dir: 'asc',
  })
  const { data: companies } = useCompanies({ page_size: 200, is_active: true }, { enabled: canReadCompany })

  const [assignOpen, setAssignOpen] = useState(false)
  const [ending, setEnding] = useState<LeavePolicyAssignment | null>(null)
  const [deleting, setDeleting] = useState<LeavePolicyAssignment | null>(null)

  const renderActions = useCallback(
    (a: LeavePolicyAssignment) => (
      <LeavePolicyAssignmentRowActions
        assignment={a}
        myEmployeeId={myEmployeeId}
        onEnd={setEnding}
        onDelete={setDeleting}
      />
    ),
    [myEmployeeId],
  )
  const columns = useMemo(
    () => buildLeavePolicyAssignmentColumns({ showPolicy: true, renderActions: canWrite ? renderActions : undefined }),
    [canWrite, renderActions],
  )

  const filtered = Boolean(debouncedValue) || policyId !== ALL || active !== ALL || companyId !== ALL
  //  Dải ghim đầu trang chỉ đổ bóng khi đã cuộn — cùng khuôn `CrudListPage` (tab Chính sách) để hai tab giống nhau.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  return (
    <PageContainer fill className="max-md:h-auto">
      {topContent}
      <PageHeader
        title={LEAVE_POLICY_HUB_TITLE}
        hideTitle={compactHeader}
        description={
          compactHeader ? (
            //  Tiêu đề đã ẩn: mô tả MỘT dòng (cắt "…", rê chuột xem đủ) — cùng khuôn `compactHeader` của `CrudListPage`.
            <span className="block max-w-[60rem] truncate max-md:hidden" title={ASSIGNMENT_PAGE_DESCRIPTION}>
              {ASSIGNMENT_PAGE_DESCRIPTION}
            </span>
          ) : (
            <span className="max-md:hidden">{ASSIGNMENT_PAGE_DESCRIPTION}</span>
          )
        }
        actions={
          canWrite ? (
            <>
              <Button type="button" variant="outline" onClick={() => navigate(appRoutes.hr.leavePolicyBulkAssign)}>
                <Users className="size-4" />
                Phân bổ hàng loạt
              </Button>
              <Button type="button" onClick={() => setAssignOpen(true)}>
                <Plus className="size-4" />
                Phân bổ
              </Button>
            </>
          ) : undefined
        }
        actionsClassName="max-md:[&>button]:flex-1"
      />

      <div ref={stickyRef} data-scrolled={scrolled ? '' : undefined} className="group flex min-h-0 flex-1 flex-col">
        {beforeContent}

        <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
          <DataTable
            fillHeight
            columns={columns}
            rows={data?.items}
            getRowId={(a) => a.id}
            isLoading={isLoading}
            isError={isError}
            emptyMessage={filtered ? 'Không có phân bổ nào khớp bộ lọc.' : 'Chưa phân bổ chính sách cho ai.'}
            storageKey="hr.leave-policy-assignments"
            toolbarClassName={toolbarClassName}
            sortBy={sortBy}
            sortDir={sortDir}
            onSortChange={handleSortChange}
            mobileCard={(a) => (
              <LeavePolicyAssignmentMobileCard assignment={a} actions={canWrite ? renderActions(a) : undefined} />
            )}
            pagination={{
              page,
              pageSize,
              total: data?.total ?? 0,
              onPageChange: setPage,
              onPageSizeChange: setPageSize,
              unitLabel: 'phân bổ',
            }}
            toolbar={
              <LeavePolicyAssignmentListToolbar
                keyword={keyword}
                onKeywordChange={setKeyword}
                policyId={policyId}
                onPolicyIdChange={setPolicyId}
                policies={policyData?.items ?? []}
                active={active}
                onActiveChange={setActive}
                companies={canReadCompany ? (companies?.items ?? []) : undefined}
                companyId={companyId}
                onCompanyIdChange={setCompanyId}
              />
            }
          />
        </Card>
      </div>

      <LeavePolicyAssignDialog open={assignOpen} onOpenChange={setAssignOpen} />
      <LeavePolicyAssignmentEndDialog assignment={ending} onClose={() => setEnding(null)} />
      <LeavePolicyAssignmentDeleteDialog assignment={deleting} onClose={() => setDeleting(null)} />
    </PageContainer>
  )
}
