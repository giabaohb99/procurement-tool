import { Loader2 } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
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
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { useEmployees } from '../hooks/use-employees'
import { useSaveUserScope, useUserScope } from '../hooks/use-user-accounts'
import { EMPTY_USER_SCOPE, type UserScope } from '../types/user-account'
import { ScopeChip } from './scope-chip'
import { ScopeEmployeePicker } from './scope-employee-picker'

interface UserScopeDialogProps {
  userId: number
  /** `null` = đóng. Mở bằng cách truyền id vai trò cần chỉnh phạm vi. */
  roleId: number | null
  roleName: string
  onClose: () => void
}

/**
 * Phạm vi dữ liệu của cặp (tài khoản × vai trò) — trục thứ hai của hệ phân quyền.
 *
 * Quy ước quan trọng: mảng RỖNG nghĩa là KHÔNG giới hạn chiều đó, không phải
 * "không thấy gì". Phòng ban định danh bằng TÊN chứ không phải id (theo
 * `ScopeUpdate` của backend).
 */
export function UserScopeDialog({
  userId,
  roleId,
  roleName,
  onClose,
}: UserScopeDialogProps) {
  const [scope, setScope] = useState<UserScope>(EMPTY_USER_SCOPE)

  const { data: saved, isLoading } = useUserScope(userId, roleId)
  const saveScope = useSaveUserScope(userId)

  const { data: companies } = useCompanies({ page_size: 1000 })
  const { data: departments } = useDepartments({ page_size: 1000 })
  const { data: employees } = useEmployees({ page_size: 2000 })

  // Nạp phạm vi đã lưu vào state cục bộ mỗi lần mở một vai trò khác.
  useEffect(() => {
    setScope(saved ?? EMPTY_USER_SCOPE)
  }, [saved])

  /** Bật/tắt một id trong chiều dùng ID (công ty, nhân sự). */
  function toggleId(key: 'companies' | 'employees' | 'exclude_employees', id: number) {
    setScope((current) => ({ ...current, [key]: flip(current[key], id) }))
  }

  /** Bật/tắt một TÊN phòng ban — backend định danh phòng ban bằng tên, không phải id. */
  function toggleDeptName(key: 'departments' | 'exclude_departments', name: string) {
    setScope((current) => ({ ...current, [key]: flip(current[key], name) }))
  }

  async function handleSave() {
    if (!roleId) return
    await saveScope.mutateAsync({ roleId, scope })
    onClose()
  }

  return (
    <Dialog open={roleId !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Phạm vi — {roleName}</DialogTitle>
          <DialogDescription>
            Để trống một mục = không giới hạn chiều đó. Chỉ áp dụng cho vai trò này.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <ScopeBox title="Công ty được xem">
                <ChipList>
                  {(companies?.items ?? []).map((company) => (
                    <ScopeChip
                      key={company.id}
                      label={company.code || company.name}
                      active={scope.companies.includes(company.id)}
                      onToggle={() => toggleId('companies', company.id)}
                    />
                  ))}
                </ChipList>
              </ScopeBox>

              <ScopeBox title="Phòng ban được xem">
                <ChipList>
                  {(departments?.items ?? []).map((department) => (
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

            <ScopeBox title="Chỉ xem chứng từ do nhân sự tạo">
              <ScopeEmployeePicker
                selected={scope.employees}
                onChange={(ids) => setScope((s) => ({ ...s, employees: ids }))}
                employees={employees?.items ?? []}
                idleHint="Mặc định: không giới hạn theo nhân sự."
                clearLabel="Bỏ giới hạn"
              />
            </ScopeBox>

            <ScopeBox title="Loại trừ phòng ban" danger>
              <ChipList>
                {(departments?.items ?? []).map((department) => (
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

            <ScopeBox title="Loại trừ nhân sự" danger>
              <ScopeEmployeePicker
                selected={scope.exclude_employees}
                onChange={(ids) => setScope((s) => ({ ...s, exclude_employees: ids }))}
                employees={employees?.items ?? []}
                idleHint="Không loại trừ nhân sự nào."
                clearLabel="Bỏ"
                danger
              />
            </ScopeBox>
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

function ScopeBox({
  title,
  danger,
  children,
}: {
  title: string
  danger?: boolean
  children: ReactNode
}) {
  return (
    <div className="rounded-lg border p-3">
      <p
        className={cn(
          'mb-2 text-xs font-semibold',
          danger ? 'text-destructive' : 'text-navy',
        )}
      >
        {title}
      </p>
      {children}
    </div>
  )
}

function ChipList({ children }: { children: ReactNode }) {
  return <div className="flex max-h-36 flex-wrap gap-1.5 overflow-y-auto">{children}</div>
}

/** Có thì bỏ ra, chưa có thì thêm vào. */
function flip<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}
