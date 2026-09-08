import { Loader2 } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
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
 * "không thấy gì".
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
  roleId,
  roleName,
  onClose,
}: UserScopeDialogProps) {
  const [scope, setScope] = useState<UserScope>(EMPTY_USER_SCOPE)
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

  const { data: companies } = useCompanies({ page_size: 1000 }, { enabled: canReadCompany })
  const { data: departments } = useDepartments({ page_size: 1000 }, { enabled: canReadDepartment })
  const { data: employees } = useEmployees({ page_size: 2000 }, { enabled: canReadEmployee })

  const companyItems = companies?.items ?? []
  const departmentItems = departments?.items ?? []
  const employeeItems = employees?.items ?? []

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

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
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
                <ChipList
                  empty={emptyHint(canReadCompany, companyItems.length, 'công ty')}
                >
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

              <ScopeBox title="Phòng ban được xem">
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

            <ScopeBox title="Chỉ xem chứng từ do nhân sự tạo">
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

            <ScopeBox title="Loại trừ phòng ban" danger>
              <ChipList empty={emptyHint(canReadDepartment, departmentItems.length, 'phòng ban')}>
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

            <ScopeBox title="Loại trừ nhân sự" danger>
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
