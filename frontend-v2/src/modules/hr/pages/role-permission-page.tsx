import { Loader2, Save, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import {
  RolePermissionMatrix,
  toPermissionPayload,
} from '../components/role-permission-matrix'
import { RoleNameInlineEdit } from '../components/role-name-inline-edit'
import { RoleSidePanel } from '../components/role-side-panel'
import { UserAccountTable } from '../components/user-account-table'
import {
  useDeleteRole,
  usePermissionMeta,
  useRolePermissions,
  useRoles,
  useSaveRolePermissions,
  useUpdateRole,
} from '../hooks/use-roles'
import type { RolePermissionRow } from '../types/role'

/**
 * Màn Phân quyền tài khoản — hai tab của hệ phân quyền hai trục:
 *  • "Vai trò & quyền": ma trận (đối tượng × hành động) của từng vai trò.
 *  • "Người dùng": ai đang giữ vai trò nào, mở tiếp để đặt phạm vi dữ liệu.
 */
export function RolePermissionPage() {
  const [tab, setTab] = useUrlParamState('tab', 'roles')
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null)
  const [matrix, setMatrix] = useState<Record<string, RolePermissionRow>>({})

  const { can } = usePermission()
  const { user } = useAuth()
  const { data: roles, isLoading: rolesLoading } = useRoles()
  const { data: meta, isLoading: metaLoading } = usePermissionMeta()
  const { data: savedRows, isFetching: permissionsLoading } = useRolePermissions(
    selectedRoleId ?? 0,
  )
  const savePermissions = useSaveRolePermissions()
  const deleteRole = useDeleteRole()
  const updateRole = useUpdateRole()

  // Đổi vai trò -> nạp lại ma trận. Khóa theo `entity` để tra nhanh khi tick ô.
  if (useHasChanged(savedRows)) {
    setMatrix(Object.fromEntries((savedRows ?? []).map((row) => [row.entity, row])))
  }

  const selectedRole = roles?.find((role) => role.id === selectedRoleId) ?? null

  //  Vai trò MÌNH ĐANG GIỮ thì chỉ xem, không sửa. Tick thêm một ô vào đây là
  //  quyền của chính mình lên ngay ở request sau — cửa sau của tự nâng quyền,
  //  backend đã chặn bằng `privilege_escalation.chan_sua_vai_tro_cua_chinh_minh`.
  //  Khóa luôn ở giao diện để người ta biết là có LUẬT, chứ không tick xong hai
  //  chục ô rồi ăn 403 và tưởng hệ hỏng (CR-158).
  const dangGiuVaiTroNay = !!selectedRoleId && !!user?.role_ids?.includes(selectedRoleId)
  const canWriteRole = can('role', 'write') && !dangGiuVaiTroNay

  async function handleSave() {
    if (!selectedRoleId || !meta) return
    await savePermissions.mutateAsync({
      roleId: selectedRoleId,
      rows: toPermissionPayload(meta, matrix),
    })
  }

  async function handleDelete() {
    if (!selectedRoleId) return
    await deleteRole.mutateAsync(selectedRoleId)
    setSelectedRoleId(null)
    setMatrix({})
  }

  return (
    <PageContainer>
      <PageHeader
        title="Phân quyền tài khoản"
        description="Hành động thuộc vai trò; phạm vi dữ liệu đặt riêng cho từng tài khoản."
      />

      {/* Tab ghi lên URL (`?tab=users`): F5 hay gửi link cho người khác vẫn ở
          đúng tab đang xem. Tab mặc định không ghi param cho link gọn. */}
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="roles">Vai trò &amp; quyền</TabsTrigger>
          <TabsTrigger value="users">Người dùng</TabsTrigger>
        </TabsList>

        <TabsContent value="roles">
          <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
            {rolesLoading ? (
              <Skeleton className="h-96 w-full" />
            ) : (
              <RoleSidePanel
                roles={roles ?? []}
                selectedId={selectedRoleId}
                onSelect={setSelectedRoleId}
              />
            )}

            {/*
              `min-w-0`: ô grid mặc định không co dưới min-content của nội dung,
              nên ma trận quyền (rộng ~860px) sẽ nong cả trang thay vì tự cuộn
              ngang trong khung của nó.
            */}
            {/*  `gap-3` ĐÈ lên `gap-6` mặc định của `Card`: không đè thì mỗi khối
                 cách nhau 24px, cộng thêm mb/mt riêng của từng khối thành 40px —
                 ba khối trông rời rạc như ba thẻ khác nhau (khách báo
                 26/08/2026). Đặt gap ở đây rồi bỏ hết mb/mt bên trong, để chỉ
                 MỘT chỗ quyết định khoảng thở. */}
            <Card className="min-w-0 gap-3 p-4">
              {!selectedRole ? (
                <p className="py-16 text-center text-sm text-muted-foreground">
                  Chọn một vai trò để xem hoặc chỉnh ma trận quyền.
                </p>
              ) : (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-3">
                    <RoleNameInlineEdit
                      role={selectedRole}
                      canWrite={can('role', 'write')}
                      pending={updateRole.isPending}
                      onRename={(roleId, name) => updateRole.mutate({ roleId, name })}
                    />

                    <div className="flex items-center gap-2">
                      <PermissionGate entity="role" action="write">
                        <Button
                          onClick={handleSave}
                          disabled={savePermissions.isPending || dangGiuVaiTroNay}
                        >
                          {savePermissions.isPending ? (
                            <Loader2 className="animate-spin" />
                          ) : (
                            <Save />
                          )}
                          Lưu quyền
                        </Button>
                      </PermissionGate>

                      <PermissionGate entity="role" action="delete">
                        {/*  Trước 25/08/2026 nút này XÓA NGAY, không hỏi gì: một
                             biểu tượng nhỏ cạnh nút Lưu, bấm nhầm là mất cả vai
                             trò lẫn ma trận quyền của nó. */}
                        <ConfirmIconButton
                          icon={Trash2}
                          title="Xóa vai trò"
                          destructive
                          disabled={deleteRole.isPending}
                          confirmTitle={`Xóa vai trò «${selectedRole.name}»?`}
                          confirmDescription="Ma trận quyền của vai trò này sẽ mất theo. Vai trò đang gán cho tài khoản nào thì phải gỡ hết mới xóa được."
                          confirmLabel="Xóa vai trò"
                          onConfirm={handleDelete}
                        />
                      </PermissionGate>
                    </div>
                  </div>

                  {dangGiuVaiTroNay && (
                    <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                      Bạn đang giữ vai trò này nên chỉ xem được, không sửa. Tự tick
                      thêm quyền cho vai trò của chính mình là tự nâng quyền — nhờ
                      một quản trị khác thao tác.
                    </p>
                  )}

                  {metaLoading || permissionsLoading || !meta ? (
                    <Skeleton className="h-96 w-full" />
                  ) : (
                    <RolePermissionMatrix
                      meta={meta}
                      rows={matrix}
                      onChange={setMatrix}
                      readOnly={!canWriteRole}
                    />
                  )}

                  <p className="text-xs text-muted-foreground">
                    Cột "Phạm vi" là mặc định của vai trò. Phạm vi RIÊNG theo từng tài
                    khoản chỉnh ở tab Người dùng. Lưu ý: backend nhớ hồ sơ phân quyền
                    tối đa 60 giây, người đang đăng nhập có thể chờ tới một phút mới
                    thấy thay đổi.
                  </p>
                </>
              )}
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users">
          <UserAccountTable roles={roles ?? []} />
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
