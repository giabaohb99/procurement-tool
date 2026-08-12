import { Loader2, Save, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import {
  RolePermissionMatrix,
  toPermissionPayload,
} from '../components/role-permission-matrix'
import { RoleSidePanel } from '../components/role-side-panel'
import { UserAccountTable } from '../components/user-account-table'
import {
  useDeleteRole,
  usePermissionMeta,
  useRolePermissions,
  useRoles,
  useSaveRolePermissions,
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
  const { data: roles, isLoading: rolesLoading } = useRoles()
  const { data: meta, isLoading: metaLoading } = usePermissionMeta()
  const { data: savedRows, isFetching: permissionsLoading } = useRolePermissions(
    selectedRoleId ?? 0,
  )
  const savePermissions = useSaveRolePermissions()
  const deleteRole = useDeleteRole()

  // Đổi vai trò -> nạp lại ma trận. Khóa theo `entity` để tra nhanh khi tick ô.
  useEffect(() => {
    setMatrix(Object.fromEntries((savedRows ?? []).map((row) => [row.entity, row])))
  }, [savedRows])

  const selectedRole = roles?.find((role) => role.id === selectedRoleId) ?? null
  const canWriteRole = can('role', 'write')

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
            <Card className="min-w-0 p-4">
              {!selectedRole ? (
                <p className="py-16 text-center text-sm text-muted-foreground">
                  Chọn một vai trò để xem hoặc chỉnh ma trận quyền.
                </p>
              ) : (
                <>
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b pb-4">
                    <div>
                      <p className="font-semibold text-navy">{selectedRole.name}</p>
                      <p className="font-mono text-xs text-muted-foreground">
                        {selectedRole.code}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <PermissionGate entity="role" action="write">
                        <Button onClick={handleSave} disabled={savePermissions.isPending}>
                          {savePermissions.isPending ? (
                            <Loader2 className="animate-spin" />
                          ) : (
                            <Save />
                          )}
                          Lưu quyền
                        </Button>
                      </PermissionGate>

                      <PermissionGate entity="role" action="delete">
                        <Button
                          variant="outline"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          title="Xóa vai trò"
                          onClick={handleDelete}
                          disabled={deleteRole.isPending}
                        >
                          <Trash2 />
                        </Button>
                      </PermissionGate>
                    </div>
                  </div>

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

                  <p className="mt-3 text-xs text-muted-foreground">
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
