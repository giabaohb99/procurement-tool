import type { AxiosError } from 'axios'
import { useMemo, useState } from 'react'

import { useAuthStore } from '@/core/auth/auth-store'
import { usePermission } from '@/core/authorization/use-permission'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { SearchSelect } from '@/shared/ui/search-select'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { OrgChartBoard } from '../components/org-chart-board'
import { useOrgChart } from '../hooks/use-org-chart'
import { buildOrgChartForest, collectOrgDepartmentIds } from '../utils/org-chart-forest'

const ALL = 'all'
const LAYOUT_KEY = 'erp.hr.org-chart.layout'

//  Bộ nhớ trình duyệt bị chặn thì coi như chưa chọn — mở kiểu mặc định.
function readSavedLayout(): 'tree' | 'columns' {
  try {
    return localStorage.getItem(LAYOUT_KEY) === 'columns' ? 'columns' : 'tree'
  } catch {
    return 'tree'
  }
}

/**
 * Sơ đồ tổ chức kiểu ERPNext (duoc-CR-711): khung vẽ kéo-thả, thẻ người nối theo QUẢN LÝ TRỰC TIẾP,
 * bấm nút dưới thẻ để mở nhóm, bấm thẻ ra khung thông tin. Lọc thêm theo pháp nhân / phòng ban
 * (ERPNext chỉ có pháp nhân — mình có cây phòng ban nên cho lọc).
 *
 * Vẽ thẳng từ `/api/org-chart` theo PHẠM VI người xem — backend đã lọc, người ngoài phạm vi không
 * có mặt; quản lý ngoài phạm vi thì người đó thành gốc một nhánh.
 */
export function OrgChartPage() {
  const { can } = usePermission()
  const allowed = can('employee', 'read')
  const { data, isPending, isError, error, refetch } = useOrgChart({ enabled: allowed })
  //  duoc-CR-713: Cài đặt nhân sự TẮT «Sơ đồ tổ chức cho mọi nhân viên» → backend trả 403 cho người không xem được toàn
  //  bộ hồ sơ. Nói đúng lý do, đừng để câu «không tải được» làm người ta bấm Tải lại mãi.
  const closedBySetting = (error as AxiosError | null)?.response?.status === 403
  const meId = useAuthStore((state) => state.user?.employee_id ?? 0)
  const isMobile = useIsMobile()
  const [chosenLayout, setChosenLayout] = useState(readSavedLayout)
  const layout = isMobile ? 'list' : chosenLayout
  const [companyChoice, setCompanyChoice] = useState<string | null>(null)
  const [department, setDepartment] = useState(ALL)

  //  Pháp nhân để chọn: các pháp nhân trả về + nhóm «Chưa gán» (0) nếu có người lạc nhóm.
  const companyOptions = useMemo(() => {
    if (!data) return []
    const known = new Set(data.companies.map((company) => company.id))
    const options = data.companies.map((company) => ({ value: String(company.id), label: company.name }))
    if (data.employees.some((employee) => !known.has(employee.company_id))) {
      options.push({ value: '0', label: 'Chưa gán pháp nhân' })
    }
    return options
  }, [data])

  //  Mặc định mở pháp nhân của chính mình (như ERPNext), không thì xem tất cả.
  const myCompany = data?.employees.find((employee) => employee.id === meId)?.company_id
  const defaultCompany =
    myCompany !== undefined && companyOptions.some((option) => option.value === String(myCompany))
      ? String(myCompany)
      : ALL
  const company = companyChoice ?? defaultCompany

  const departmentOptions = useMemo(() => {
    if (!data) return []
    const list = data.departments
      .filter((dept) => company === ALL || String(dept.company_id) === company)
      .map((dept) => ({ value: String(dept.id), label: dept.name, hint: dept.code }))
    return [{ value: ALL, label: 'Tất cả phòng ban' }, { value: '0', label: 'Chưa gắn phòng ban' }, ...list]
  }, [data, company])

  const forest = useMemo(() => {
    if (!data) return null
    return buildOrgChartForest(data, {
      companyId: company === ALL ? null : Number(company),
      departmentIds: department === ALL ? null : collectOrgDepartmentIds(data.departments, Number(department)),
    })
  }, [data, company, department])

  const changeLayout = (next: 'tree' | 'columns') => {
    setChosenLayout(next)
    try {
      localStorage.setItem(LAYOUT_KEY, next)
    } catch {
      //  Bộ nhớ bị chặn: lần sau mở lại kiểu mặc định.
    }
  }

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
    <PageContainer fill className="p-0 lg:p-0">
      {isPending ? (
        <div className="flex h-full flex-col items-center gap-8 p-10">
          <Skeleton className="h-14 w-52" />
          <div className="flex gap-6">
            <Skeleton className="h-14 w-52" />
            <Skeleton className="h-14 w-52" />
            <Skeleton className="h-14 w-52" />
          </div>
        </div>
      ) : closedBySetting ? (
        <ErrorState
          code="403"
          title="Sơ đồ tổ chức chưa mở cho bạn"
          description="Công ty đang chỉ mở sơ đồ tổ chức cho người xem được toàn bộ hồ sơ nhân sự. Liên hệ phòng Nhân sự nếu bạn cần xem."
        />
      ) : isError || !data || !forest ? (
        <ErrorState title="Không tải được sơ đồ tổ chức" description="Thử tải lại; nếu vẫn lỗi hãy báo quản trị.">
          <button type="button" className="text-primary underline" onClick={() => void refetch()}>
            Tải lại
          </button>
        </ErrorState>
      ) : data.employees.length === 0 ? (
        <p className="p-6 text-sm text-muted-foreground">Chưa có nhân sự nào trong phạm vi bạn được xem.</p>
      ) : (
        <div className="relative min-h-0 flex-1">
          <OrgChartBoard
            //  Đổi bộ lọc = sơ đồ mới: nhóm đang mở / thẻ đang chọn của bộ lọc cũ không còn nghĩa.
            key={`${company}|${department}`}
            forest={forest}
            meId={meId}
            layout={layout}
            onLayoutChange={changeLayout}
            filters={
              <>
                {companyOptions.length > 1 && (
                  <Select
                    value={company}
                    onValueChange={(value) => {
                      setCompanyChoice(value)
                      setDepartment(ALL)
                    }}
                  >
                    <SelectTrigger className="min-w-0 flex-1 bg-card sm:w-44 sm:flex-none" aria-label="Pháp nhân">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={ALL}>Tất cả pháp nhân</SelectItem>
                      {companyOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                <SearchSelect
                  value={department}
                  onChange={(value) => setDepartment(value || ALL)}
                  options={departmentOptions}
                  placeholder="Tất cả phòng ban"
                  searchPlaceholder="Tìm phòng ban…"
                  className="min-w-0 flex-1 bg-card sm:w-48 sm:flex-none"
                />
              </>
            }
          />
        </div>
      )}
    </PageContainer>
  )
}
