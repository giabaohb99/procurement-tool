import { Lock, LockOpen, Pencil, Search, Trash2 } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useDepartments } from '../hooks/use-departments'
import {
  useDeleteUserAccount,
  useSetUserActive,
  useUserAccounts,
} from '../hooks/use-user-accounts'
import type { Role } from '../types/role'
import type { UserAccount } from '../types/user-account'

const ALL = 'all'

/**
 * Tab "Người dùng" của màn Phân quyền: lọc, khóa/mở, xóa tài khoản không còn
 * hồ sơ nhân sự (`is_orphan`).
 *
 * ⚠️ KHÔNG có "Bộ lọc" nâng cao ở đây. `/api/users` không chạy qua
 * `apply_filters` mà tự đọc các tham số riêng (`search`, `department`,
 * `role_id`, `no_role`, `orphan`), nên cú pháp `<field>__<op>` vô tác dụng.
 *
 * Bộ lọc ghi lên URL đúng bằng TÊN THAM SỐ của backend (`search`, `department`,
 * `role_id`) cho dễ đối chiếu khi debug. Trang này không có `FilterProvider`
 * nên không cần khai `preserveParams`.
 */
export function UserAccountTable({ roles }: { roles: Role[] }) {
  const navigate = useNavigate()

  const {
    value: keyword,
    setValue: setKeyword,
    debouncedValue: debouncedKeyword,
  } = useUrlSearchParam('search')
  const [department, setDepartment] = useUrlParamState('department', ALL)
  const [roleId, setRoleId] = useUrlParamState('role_id', ALL)
  const [flag, setFlag] = useUrlParamState('flag', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: departments } = useDepartments({ page_size: 500 })
  const setActive = useSetUserActive()
  const deleteAccount = useDeleteUserAccount()

  // Đổi bất kỳ bộ lọc nào cũng về trang 1, tránh đứng ở trang trống.
  const [page, setPage] = usePageResetOnFilterChange([debouncedKeyword, department, roleId, flag])

  const params: ListParams = { page, page_size: pageSize }
  if (debouncedKeyword) params.search = debouncedKeyword
  if (department !== ALL) params.department = department
  if (roleId !== ALL) params.role_id = Number(roleId)
  if (flag === 'no_role') params.no_role = true
  if (flag === 'orphan') params.orphan = true

  const { data, isLoading, isError } = useUserAccounts(params)

  // useCallback để đưa được vào deps của `columns` mà không phá memo:
  // hàm khai báo thẳng trong thân component sẽ đổi danh tính mỗi lần render.
  const roleName = useCallback(
    (id: number) => roles.find((role) => role.id === id)?.name ?? String(id),
    [roles],
  )

  const columns = useMemo<DataTableColumn<UserAccount>[]>(
    () => [
      {
        key: 'user',
        header: 'Người dùng',
        width: 320,
        hideable: false,
        cell: (account) => (
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="truncate font-medium">{account.full_name}</span>
              {account.is_orphan && (
                <Badge variant="destructive" title="Không gắn hồ sơ nhân sự nào">
                  Thiếu hồ sơ
                </Badge>
              )}
              {!account.is_active && <Badge variant="secondary">Đã khóa</Badge>}
            </div>
            <span className="block truncate text-xs text-muted-foreground">
              {account.email || '(chưa có email)'}
            </span>
          </div>
        ),
      },
      {
        key: 'department_name',
        header: 'Phòng ban',
        width: 180,
        cell: (account) => account.department_name || '—',
      },
      {
        key: 'roles',
        header: 'Vai trò',
        width: 300,
        cell: (account) =>
          account.role_ids.length === 0 ? (
            <span className="text-muted-foreground">Chưa gán</span>
          ) : (
            <div className="flex flex-wrap gap-1">
              {account.role_ids.slice(0, 3).map((id) => (
                <Badge key={id} variant="outline">
                  {roleName(id)}
                </Badge>
              ))}
              {account.role_ids.length > 3 && (
                <Badge
                  variant="outline"
                  title={account.role_ids.slice(3).map(roleName).join(', ')}
                >
                  +{account.role_ids.length - 3}
                </Badge>
              )}
            </div>
          ),
      },
      {
        key: 'actions',
        header: '',
        width: 140,
        align: 'right',
        hideable: false,
        cell: (account) => (
          // Chặn click lan lên dòng, nếu không mỗi lần khóa tài khoản lại mở
          // luôn trang chi tiết.
          <div
            className="flex justify-end gap-1"
            onClick={(event) => event.stopPropagation()}
          >
            <Button
              variant="ghost"
              size="icon-sm"
              title="Sửa phân quyền"
              onClick={() => navigate(appRoutes.hr.userPermissionDetail(account.id))}
            >
              <Pencil />
            </Button>

            {/* Khóa/mở khóa và xóa đều đổi trạng thái đăng nhập của người khác
                ngay lập tức -> hỏi lại trước khi chạy. */}
            <ConfirmIconButton
              icon={account.is_active ? Lock : LockOpen}
              title={account.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}
              confirmTitle={
                account.is_active
                  ? `Khóa tài khoản "${account.full_name}"?`
                  : `Mở khóa tài khoản "${account.full_name}"?`
              }
              confirmDescription={
                account.is_active
                  ? 'Người dùng sẽ không đăng nhập được cho tới khi mở khóa lại.'
                  : 'Người dùng đăng nhập lại được ngay sau khi mở khóa.'
              }
              confirmLabel={account.is_active ? 'Khóa' : 'Mở khóa'}
              // Không tô đỏ nút trong bảng: khóa là thao tác đảo được, đỏ hết
              // cả cột chỉ làm rối mắt. Chỉ nút Xóa mới đỏ.
              onConfirm={() =>
                setActive.mutate({ userId: account.id, isActive: !account.is_active })
              }
            />

            {/* Chỉ tài khoản KHÔNG CÒN HỒ SƠ mới xóa được — còn hồ sơ nhân sự
                thì khóa, đừng xóa. */}
            {account.is_orphan && (
              <ConfirmIconButton
                icon={Trash2}
                title="Xóa hẳn tài khoản"
                confirmTitle={`Xóa tài khoản "${account.full_name}"?`}
                confirmDescription="Tài khoản này không còn gắn hồ sơ nhân sự nào. Nhật ký thao tác cũ vẫn giữ lại. Không khôi phục được."
                confirmLabel="Xóa"
                destructive
                onConfirm={() => deleteAccount.mutate(account.id)}
              />
            )}
          </div>
        ),
      },
    ],
    [roleName, navigate, setActive, deleteAccount],
  )

  return (
    <DataTable
      columns={columns}
      rows={data?.items}
      getRowId={(account) => account.id}
      isLoading={isLoading}
      isError={isError}
      emptyMessage="Không có tài khoản nào khớp bộ lọc."
      storageKey="hr.user-accounts"
      onRowClick={(account) =>
        navigate(appRoutes.hr.userPermissionDetail(account.id))
      }
      pagination={{
        page,
        pageSize,
        total: data?.total ?? 0,
        onPageChange: setPage,
        onPageSizeChange: setPageSize,
        unitLabel: 'tài khoản',
      }}
      toolbar={
        <>
          <div className="relative min-w-56 flex-1 md:max-w-xs">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Tìm theo tên / email / mã NV…"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </div>

          <Select value={department} onValueChange={setDepartment}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Phòng ban" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Tất cả phòng ban</SelectItem>
              {(departments?.items ?? []).map((item) => (
                // Backend lọc tài khoản theo TÊN phòng ban, không phải id.
                <SelectItem key={item.id} value={item.name}>
                  {item.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={roleId} onValueChange={setRoleId}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder="Vai trò" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Tất cả vai trò</SelectItem>
              {roles.map((role) => (
                <SelectItem key={role.id} value={String(role.id)}>
                  {role.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={flag} onValueChange={setFlag}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="Tình trạng" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Tất cả tình trạng</SelectItem>
              <SelectItem value="no_role">Chưa gán vai trò</SelectItem>
              <SelectItem value="orphan">Không có hồ sơ nhân sự</SelectItem>
            </SelectContent>
          </Select>
        </>
      }
    />
  )
}
