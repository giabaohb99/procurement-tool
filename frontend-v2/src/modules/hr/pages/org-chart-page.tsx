import { usePermission } from '@/core/authorization/use-permission'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import { OrgChartDepartmentNode } from '../components/org-chart-department-node'
import { useOrgChart } from '../hooks/use-org-chart'

/**
 * Sơ đồ tổ chức: pháp nhân › phòng ban (cây `parent`) › người (cây quản lý trực tiếp).
 * Vẽ thẳng từ dữ liệu, theo PHẠM VI người xem — backend đã lọc, người ngoài phạm vi
 * không có mặt (kể cả khi là trưởng phòng / quản lý của người trong phạm vi).
 */
export function OrgChartPage() {
  const { can } = usePermission()
  const allowed = can('employee', 'read')
  const { tree, isPending, isError, refetch } = useOrgChart({ enabled: allowed })

  if (!allowed) {
    return (
      <ErrorState
        code="403"
        title="Không có quyền xem sơ đồ tổ chức"
        description="Sơ đồ cần quyền xem hồ sơ nhân sự (employee:read). Liên hệ quản trị nếu bạn cần quyền này."
      />
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title="Sơ đồ tổ chức"
        description="Vẽ tự động từ phòng ban, trưởng phòng và quản lý trực tiếp; chỉ hiện những người trong phạm vi bạn được xem."
      />
      {isPending ? (
        <div className="space-y-2">
          <Skeleton className="h-12" />
          <Skeleton className="h-12" />
          <Skeleton className="h-12" />
        </div>
      ) : isError ? (
        <ErrorState
          title="Không tải được sơ đồ tổ chức"
          description="Thử tải lại; nếu vẫn lỗi hãy báo quản trị."
        >
          <button type="button" className="text-primary underline" onClick={() => void refetch()}>
            Tải lại
          </button>
        </ErrorState>
      ) : tree.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          Chưa có phòng ban hay nhân sự nào trong phạm vi bạn được xem.
        </p>
      ) : (
        <div className="space-y-6">
          {tree.map((company) => (
            <section key={company.id}>
              <h2 className="mb-2 text-base font-semibold">
                {company.name}
                <span className="text-muted-foreground ml-2 text-sm font-normal">
                  {company.headcount} người
                </span>
              </h2>
              {company.departments.map((dept) => (
                <OrgChartDepartmentNode key={dept.id} node={dept} />
              ))}
            </section>
          ))}
        </div>
      )}
    </PageContainer>
  )
}
