import { ChevronDown, Loader2 } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/shared/ui/collapsible'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import {
  useEmployee,
  useEmployeeDepartments,
  useEmployees,
} from '@/modules/hr/hooks/use-employees'
import { usePermissionMeta, useRolePermissions } from '@/modules/hr/hooks/use-roles'
import { useSaveUserScope, useUserScope } from '@/modules/hr/hooks/use-user-accounts'
import { EMPTY_USER_SCOPE, type UserScope } from '@/modules/hr/types/user-account'
import {
  countScopeExceptions,
  findContradictingDepartments,
  findSelfExcludedDepartments,
  groupEntitiesByScope,
  summarizeScopeLimits,
  type ScopeOwnerProfile,
} from '../utils/scope-summary'
import { AccountScopeSummaryPanel } from './account-scope-summary-panel'
import { ScopeChip } from './scope-chip'
import { ScopeEmployeePicker } from './scope-employee-picker'

interface UserScopeDialogProps {
  userId: number
  /**
   * Hồ sơ nhân sự gắn với tài khoản (`UserAccount.employee_id`), `0` = chưa gắn ai.
   *
   * Đây là nguồn của công ty / phòng ban MẶC ĐỊNH — thứ backend đọc để dựng phạm
   * vi. Không có nó thì hộp thoại chỉ nói được "công ty của người này" và người
   * đọc vẫn phải đi tra xem người này thuộc công ty nào.
   */
  employeeId: number
  /** `null` = đóng. Mở bằng cách truyền id vai trò cần chỉnh phạm vi. */
  roleId: number | null
  roleName: string
  onClose: () => void
}

/**
 * Phạm vi dữ liệu của cặp (tài khoản × vai trò) — trục thứ hai của hệ phân quyền.
 *
 * Quy ước quan trọng: mảng RỖNG nghĩa là KHÔNG giới hạn chiều đó, không phải
 * "không thấy gì".
 *
 * **HAI TẦNG GỘP LÀM MỘT** (đại ca chốt 19/09/2026). Bản trước bày hai khối
 * "Tầng 1" / "Tầng 2" ngang nhau, và đại ca bác đúng: gán vai trò xong là tài
 * khoản **đã có phạm vi rồi** — bậc «Công ty» nghĩa là công ty trong hồ sơ của
 * chính người đó, không ai phải tick gì cả. Bày hai tầng ngang hàng khiến năm ô
 * tick trông như phần bắt buộc phải khai; đo trên dữ liệu thật thì 25 trong 27
 * dòng khai công ty chỉ chép lại đúng công ty đã có trong hồ sơ.
 *
 * Nên hộp thoại nay có MỘT khối trả lời "tài khoản này thấy gì" (in tên công ty
 * / phòng ban thật), còn năm ô tick tụt xuống mục «Ngoại lệ» **gấp lại**.
 *
 * ⚠️ Gấp chứ KHÔNG bỏ, và `core/scoping.py` không đụng tới: 11 tài khoản chưa
 * gắn hồ sơ và 2 tài khoản khai công ty khác hồ sơ đang sống nhờ đúng mấy dòng
 * đó. Bỏ ô tick hôm nay là mười ba người mất phạm vi trong im lặng.
 *
 * ⚠️ Hai chiều CỘNG THÊM chứ không thu hẹp, ngược hẳn với cái tên:
 * «Phòng ban được xem» ghép bằng `or_` với bậc vai trò (`scope_condition`). Tick
 * một phòng vào đó KHÔNG làm tài khoản chỉ còn thấy phòng đó. Mọi câu chữ trong
 * hộp thoại phải nói đúng chiều này, xem `utils/scope-summary.ts`.
 *
 * ⚠️ **Phòng ban gửi đi bằng TÊN, và đó là một QUẢ MÌN chưa nổ (09-A).**
 * `ScopeUpdate` của backend vẫn nhận `departments: list[str]`, nhưng
 * `tab_user_scope` đã lưu **id** từ CR-086 — backend chỉ đổi tên→id lúc ghi và
 * id→tên lúc đọc. Vòng đọc–ghi hôm nay khớp nên chưa ai thấy gì. Nó hỏng khi có
 * HAI phòng trùng tên ở hai pháp nhân, mà hệ có 11 pháp nhân và tên phòng đặt
 * theo khuôn ("Phòng Kế toán"…):
 *   1. hộp thoại nạp phòng của MỌI pháp nhân và không hiện pháp nhân bên cạnh
 *      tên -> hai chip chữ giống hệt nhau;
 *   2. `active` so bằng tên -> tick một chip thì cả hai cùng sáng;
 *   3. `dept_id_by_name` gặp tên nhập nhằng thì trả 0 và backend rơi về lưu TÊN;
 *   4. `auth.py:_dept_ref_map` dựng `{tên: id}` -> giữ đúng dòng CUỐI.
 * Kết quả: loại trừ nhầm phòng của pháp nhân khác, không một triệu chứng nào.
 * Sửa = đổi hợp đồng API (`list[int]`, vẫn phải nhận `list[str]` cho bản
 * `frontend/` đã đóng băng) nên tách thành việc riêng, xem ca A2 trong
 * `user-scope-dialog.test.tsx`.
 */
export function UserScopeDialog({
  userId,
  employeeId,
  roleId,
  roleName,
  onClose,
}: UserScopeDialogProps) {
  const [scope, setScope] = useState<UserScope>(EMPTY_USER_SCOPE)
  const [showExceptions, setShowExceptions] = useState(false)
  const { can } = usePermission()

  const { data: saved, isLoading } = useUserScope(userId, roleId)
  const saveScope = useSaveUserScope(userId)

  //  ⚠️ Ba danh mục dưới đây thuộc phân hệ KHÁC, mỗi cái một khóa quyền riêng.
  //  Không tắt thì hộp thoại vừa mở đã bắn ba lượt gọi; thiếu quyền là ăn 403,
  //  mà 403 trên GET không bật toast (`core/api/http-client.ts`) nên ô chỉ hiện
  //  rỗng — người khai quyền đọc ra thành "công ty này chưa khai phòng ban nào"
  //  rồi khai phạm vi hụt. Cùng bẫy đã dính ở tab «Công nợ» của Nhà cung cấp.
  //
  //  Gác thêm `roleId !== null`: hộp thoại luôn được dựng ở cây React, chỉ có
  //  `open` là đổi — không có nhịp này thì đóng hộp vẫn nạp 2000 nhân sự.
  const isOpen = roleId !== null
  const canReadCompany = isOpen && can('company', 'read')
  const canReadDepartment = isOpen && can('department', 'read')
  const canReadEmployee = isOpen && can('employee', 'read')
  //  Ma trận quyền của vai trò (= TẦNG 1) cũng là một khóa quyền riêng. Thiếu
  //  `role.read` thì không nạp, và panel nói thẳng là đang khai mà không thấy nền
  //  — hơn hẳn việc bày một khung trống.
  const canReadRole = isOpen && can('role', 'read')

  const { data: companies } = useCompanies({ page_size: 1000 }, { enabled: canReadCompany })
  const { data: departments } = useDepartments({ page_size: 1000 }, { enabled: canReadDepartment })
  const { data: employees } = useEmployees({ page_size: 2000 }, { enabled: canReadEmployee })
  const { data: meta } = usePermissionMeta({ enabled: canReadRole })
  const { data: rolePermissions, isLoading: tierLoading } = useRolePermissions(roleId ?? 0, {
    enabled: canReadRole,
  })
  const { data: owner } = useEmployee(employeeId, { enabled: canReadEmployee })
  //  Phòng kiêm nhiệm của chủ tài khoản (bao-CR-430): `owner.department_name`
  //  chỉ là phòng CHÍNH, mà `profile.dept_ids` ở backend gom cả kiêm nhiệm nên
  //  cảnh báo "trừ phòng của chính mình" phải nhìn đủ cả hai. Cùng cửa quyền
  //  với `useEmployee` — thiếu `employee.read` thì không gọi.
  const { data: ownerDepartments } = useEmployeeDepartments(employeeId, {
    enabled: canReadEmployee,
  })

  const companyItems = companies?.items ?? []
  const departmentItems = departments?.items ?? []
  const employeeItems = employees?.items ?? []

  //  Tên phòng của chính chủ tài khoản: phòng chính lấy thẳng từ hồ sơ; phòng
  //  kiêm nhiệm chỉ có id nên tra ngược qua danh mục phòng ban (popup làm việc
  //  bằng TÊN, lỗ 09-A). Thiếu danh mục thì chỉ còn phòng chính — cảnh báo
  //  vẫn đúng, chỉ thiếu phần kiêm nhiệm, không báo sai.
  const ownDepartmentNames = [
    owner?.department_name ?? '',
    ...(ownerDepartments?.extra_department_ids ?? []).map(
      (id) => departmentItems.find((department) => department.id === id)?.name ?? '',
    ),
  ]

  //  Ba trạng thái, đừng gộp hai cái sau: `employee_id = 0` là SỰ THẬT đọc thẳng
  //  từ tài khoản (chưa gắn hồ sơ ai) nên cảnh báo được ngay, không cần quyền xem
  //  nhân sự. Còn "có hồ sơ mà chưa đọc được" thì `null` — im lặng, vì lúc đó
  //  mình không biết người ta đã gắn công ty hay chưa.
  const ownerProfile: ScopeOwnerProfile | null =
    employeeId === 0
      ? { hasProfile: false }
      : owner
        ? {
            hasProfile: true,
            companyName: owner.company_name,
            departmentName: owner.department_name,
          }
        : null

  const tierGroups = meta ? groupEntitiesByScope(rolePermissions ?? [], meta) : []
  //  Vai trò chỉ toàn bậc «Tất cả» thì ô "xem thêm phòng ban" không đổi được gì:
  //  `scope_condition` bỏ qua phần cộng thêm khi bậc đã thấy hết.
  const roleSeesEverything = tierGroups.length === 1 && tierGroups[0].scope === 'all'

  // Nạp phạm vi đã lưu vào state cục bộ mỗi lần mở một vai trò khác.
  if (useHasChanged(saved)) setScope(saved ?? EMPTY_USER_SCOPE)

  /** Bật/tắt một id trong chiều dùng ID (công ty, nhân sự). */
  function toggleId(key: 'companies' | 'employees' | 'exclude_employees', id: number) {
    setScope((current) => ({ ...current, [key]: flip(current[key], id) }))
  }

  /** Bật/tắt một TÊN phòng ban — backend định danh phòng ban bằng tên, không phải id. */
  function toggleDeptName(key: 'departments' | 'exclude_departments', name: string) {
    setScope((current) => ({ ...current, [key]: flip(current[key], name) }))
  }

  //  Đóng hộp trong `onSuccess`, KHÔNG đóng ngay sau lời gọi: lưu hỏng (403/500)
  //  mà hộp đã biến mất thì người dùng tưởng đã lưu xong, và mọi ô vừa tick mất
  //  sạch. `mutate` chứ không `mutateAsync` — bản async ném lỗi ra ngoài trình
  //  xử lý sự kiện, thành một unhandled rejection không ai bắt.
  function handleSave() {
    if (!roleId) return
    saveScope.mutate({ roleId, scope }, { onSuccess: onClose })
  }

  /** Id -> tên để câu tóm tắt đọc được. Không tra ra thì in id, đừng bỏ im. */
  function nameCompany(id: number): string {
    const found = companyItems.find((item) => item.id === id)
    return found ? found.code || found.name : `Công ty #${id}`
  }

  function nameEmployee(id: number): string {
    const found = employeeItems.find((item) => item.id === id)
    return found ? found.full_name : `Nhân sự #${id}`
  }

  //  Câu tóm tắt dựng lại theo TỪNG lần tick, không chờ bấm Lưu: người khai phải
  //  đọc được hậu quả trước khi ghi xuống, chứ không phải sau.
  const limitLines = summarizeScopeLimits({
    companies: scope.companies.map(nameCompany),
    departments: scope.departments,
    employees: scope.employees.map(nameEmployee),
    excludeDepartments: scope.exclude_departments,
    excludeEmployees: scope.exclude_employees.map(nameEmployee),
  })
  const contradictions = findContradictingDepartments(
    scope.departments,
    scope.exclude_departments,
  )
  const selfExcluded = findSelfExcludedDepartments(
    scope.exclude_departments,
    ownDepartmentNames,
  )
  //  ĐẾM từng mục, không đếm số câu tóm tắt: `summarizeScopeLimits` gộp cả một
  //  chiều thành một câu, nên tick thêm phòng thứ hai thì số trên nhãn đứng yên
  //  và người khai tưởng lần tick vừa rồi rơi mất.
  const exceptionCount = countScopeExceptions(scope)

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[85dvh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Phạm vi — {roleName}</DialogTitle>
          <DialogDescription>
            Gán vai trò là tài khoản đã có sẵn phạm vi bên dưới, không phải khai gì
            thêm. Chỉ mở mục Ngoại lệ khi người này cần khác với mặc định.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="space-y-4">
            <AccountScopeSummaryPanel
              roleId={roleId}
              roleName={roleName}
              groups={tierGroups}
              owner={ownerProfile}
              exceptionLines={limitLines}
              isLoading={canReadRole && (tierLoading || !meta)}
              canReadRole={canReadRole}
              canReadEmployee={canReadEmployee}
            />

            {contradictions.length > 0 && (
              //  Trước 19/09/2026 hộp thoại im lặng ở đúng chỗ này: tick một phòng
              //  vào cả hai ô thì loại trừ THẮNG, phần mở thêm thành vô nghĩa.
              //
              //  Câu này ở NGOÀI mục gấp, cố ý: mâu thuẫn chỉ sinh ra được khi người
              //  ta đã mở mục ra tick, nhưng nó vẫn còn đó sau khi gấp lại — giấu đi
              //  là giấu đúng thứ đang làm hỏng phần vừa khai.
              <p className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-xs font-medium text-destructive">
                Phòng {contradictions.join(', ')} đang nằm ở cả ô xem thêm lẫn ô loại
                trừ. Loại trừ thắng, nên phần xem thêm không có tác dụng — bỏ bớt một
                bên.
              </p>
            )}

            {selfExcluded.length > 0 && (
              //  bao-CR-430 (đại ca 19/09/2026: "cảnh báo thôi, đừng chặn"). Trừ
              //  đúng phòng của chính chủ tài khoản là hợp lệ — có thể là ý muốn
              //  (nhà máy chỉ xem phiếu phòng khác NHỜ mình) — nên tông vàng chứ
              //  không đỏ, và nút Lưu vẫn bấm được. Cũng đặt NGOÀI mục gấp như câu
              //  mâu thuẫn ở trên, cùng lý do.
              <p
                role="status"
                className="rounded-lg border border-warning/40 bg-warning/5 p-3 text-xs font-medium text-warning"
              >
                Phòng {selfExcluded.join(', ')} là phòng của chính người này. Loại trừ
                thắng mọi bậc phạm vi, nên với mọi vai trò có gắn phạm vi này, phiếu
                của phòng đó sẽ không còn thấy — chỉ còn phiếu phòng khác nhờ phòng
                này xử lý. Vẫn lưu được nếu đó là ý muốn.
              </p>
            )}

            {/*  Gấp lại và MẶC ĐỊNH ĐÓNG: đa số tài khoản không cần ngoại lệ nào, mà
                 bày sẵn năm ô tick thì ai mở hộp thoại cũng tưởng mình phải khai.
                 Số trên nhãn là thứ duy nhất nói được "trong này đang có gì" khi mục
                 đang đóng — không có nó thì gấp lại thành giấu. */}
            <Collapsible open={showExceptions} onOpenChange={setShowExceptions}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" size="sm" className="w-full justify-between">
                  <span>
                    Ngoại lệ
                    {exceptionCount > 0 ? ` (${exceptionCount})` : ''}
                  </span>
                  <ChevronDown
                    className={cn('size-4 transition-transform', showExceptions && 'rotate-180')}
                  />
                </Button>
              </CollapsibleTrigger>

              <CollapsibleContent className="mt-3 space-y-4">
                <p className="text-xs text-muted-foreground">
                  Chỉ dùng khi người này cần khác mặc định ở trên — chừa ra một phòng,
                  hoặc mở thêm một phòng ngoài công ty của họ. Để trống một mục = không
                  giới hạn chiều đó.
                </p>

                <div className="grid gap-4 sm:grid-cols-2">
                  <ScopeBox
                    title="Chỉ trong công ty"
                    hint="THU HẸP. Bỏ trống = đúng công ty trong hồ sơ của người này."
                  >
                    <ChipList empty={emptyHint(canReadCompany, companyItems.length, 'công ty')}>
                      {companyItems.map((company) => (
                        <ScopeChip
                          key={company.id}
                          label={company.code || company.name}
                          active={scope.companies.includes(company.id)}
                          onToggle={() => toggleId('companies', company.id)}
                        />
                      ))}
                    </ChipList>
                  </ScopeBox>

                  <ScopeBox
                    title="Xem THÊM phòng ban"
                    hint={
                      roleSeesEverything
                        ? 'Vai trò đã ở bậc «Tất cả» nên cộng thêm phòng ban không đổi được gì.'
                        : 'CỘNG THÊM, không thu hẹp: tài khoản thấy chứng từ của các phòng này NGOÀI phần mặc định ở trên.'
                    }
                    muted={roleSeesEverything}
                  >
                    <ChipList
                      empty={emptyHint(canReadDepartment, departmentItems.length, 'phòng ban')}
                    >
                      {departmentItems.map((department) => (
                        <ScopeChip
                          key={department.id}
                          label={department.name}
                          active={scope.departments.includes(department.name)}
                          onToggle={() => toggleDeptName('departments', department.name)}
                        />
                      ))}
                    </ChipList>
                  </ScopeBox>
                </div>

                <ScopeBox
                  title="Chỉ xem chứng từ do nhân sự tạo"
                  hint="THU HẸP. Bỏ trống = không giới hạn theo người lập."
                >
                  <ScopeEmployeePicker
                    selected={scope.employees}
                    onChange={(ids) => setScope((s) => ({ ...s, employees: ids }))}
                    employees={employeeItems}
                    idleHint={
                      canReadEmployee
                        ? 'Mặc định: không giới hạn theo nhân sự.'
                        : 'Bạn không có quyền xem danh bạ nhân sự, nên không giới hạn được theo chiều này.'
                    }
                    clearLabel="Bỏ giới hạn"
                  />
                </ScopeBox>

                <ScopeBox
                  title="Loại trừ phòng ban"
                  hint="TRỪ RA, thắng mọi ô ở trên. Phiếu của phòng bị trừ mà NHỜ phòng của người này mua giúp thì vẫn thấy."
                  danger
                >
                  <ChipList
                    empty={emptyHint(canReadDepartment, departmentItems.length, 'phòng ban')}
                  >
                    {departmentItems.map((department) => (
                      <ScopeChip
                        key={department.id}
                        label={department.name}
                        danger
                        active={scope.exclude_departments.includes(department.name)}
                        onToggle={() => toggleDeptName('exclude_departments', department.name)}
                      />
                    ))}
                  </ChipList>
                </ScopeBox>

                <ScopeBox
                  title="Loại trừ nhân sự"
                  hint="TRỪ RA. Chứng từ do những người này lập thì tài khoản không thấy."
                  danger
                >
                  <ScopeEmployeePicker
                    selected={scope.exclude_employees}
                    onChange={(ids) => setScope((s) => ({ ...s, exclude_employees: ids }))}
                    employees={employeeItems}
                    idleHint={
                      canReadEmployee
                        ? 'Không loại trừ nhân sự nào.'
                        : 'Bạn không có quyền xem danh bạ nhân sự, nên không loại trừ được theo chiều này.'
                    }
                    clearLabel="Bỏ"
                    danger
                  />
                </ScopeBox>
              </CollapsibleContent>
            </Collapsible>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Hủy
          </Button>
          <Button onClick={handleSave} disabled={saveScope.isPending || isLoading}>
            {saveScope.isPending && <Loader2 className="size-4 animate-spin" />}
            Lưu phạm vi
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Một chiều của phạm vi.
 *
 * `hint` là BẮT BUỘC về mặt thiết kế dù TypeScript cho phép bỏ: bốn trong năm ô
 * có tên nghe giống nhau ("được xem", "loại trừ") nhưng ba ô thu hẹp, một ô cộng
 * thêm. Không có câu này thì cái tên tự nó đọc ra nghĩa ngược.
 *
 * `muted` = ô có khai cũng không đổi được gì ở bậc hiện tại. Cố ý KHÔNG khóa
 * chip: giá trị cũ vẫn phải gỡ được, và bậc của vai trò có thể đổi ngày mai.
 */
function ScopeBox({
  title,
  hint,
  danger,
  muted,
  children,
}: {
  title: string
  hint?: string
  danger?: boolean
  muted?: boolean
  children: ReactNode
}) {
  return (
    <div className={cn('rounded-lg border p-3', muted && 'opacity-60')}>
      <p
        className={cn(
          'text-xs font-semibold',
          danger ? 'text-destructive' : 'text-navy',
        )}
      >
        {title}
      </p>
      {hint && <p className="mt-0.5 mb-2 text-xs text-muted-foreground">{hint}</p>}
      {!hint && <div className="mb-2" />}
      {children}
    </div>
  )
}

/**
 * Khung chip. `empty` = danh sách không có chip nào; phải NÓI RA vì sao, đừng để
 * một khung trắng: ở màn phân quyền, "chưa khai phòng ban nào" và "bạn không
 * được xem danh mục phòng ban" dẫn tới hai hành động hoàn toàn khác nhau.
 */
function ChipList({ children, empty }: { children: ReactNode; empty: string | null }) {
  if (empty) return <p className="text-xs text-muted-foreground">{empty}</p>
  return <div className="flex max-h-36 flex-wrap gap-1.5 overflow-y-auto">{children}</div>
}

/** Câu giải thích cho một khung chip rỗng — phân biệt thiếu quyền với thiếu dữ liệu. */
function emptyHint(allowed: boolean, count: number, ten: string): string | null {
  if (!allowed) return `Bạn không có quyền xem danh mục ${ten}, nên không giới hạn được theo chiều này.`
  if (count === 0) return `Chưa có ${ten} nào trong danh mục.`
  return null
}

/** Có thì bỏ ra, chưa có thì thêm vào. */
function flip<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}
