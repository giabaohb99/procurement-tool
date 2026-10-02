import { Loader2, Save, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  useDeleteRole,
  usePermissionMeta,
  useRolePermissions,
  useSaveRolePermissions,
  useUpdateRole,
} from '@/modules/hr/hooks/use-roles'
import type { Role, RolePermissionRow } from '@/modules/hr/types/role'
import {
  SYSTEM_ADMIN_FULL_NOTE,
  holdsSystemAdminRole,
  isSystemAdminRole,
} from '@/modules/hr/utils/system-admin-role'
import { rowsToMatrix, toPermissionPayload } from '../utils/permission-matrix-cells'
import { RoleNameInlineEdit } from './role-name-inline-edit'
import { RolePermissionMatrix } from './role-permission-matrix'
import { RoleSidePanel } from './role-side-panel'

interface RolePermissionRolesTabProps {
  roles: Role[] | undefined
  rolesLoading: boolean
  selectedRoleId: number | null
  /** `null` = bỏ chọn (dùng khi xóa vai trò đang mở). */
  onSelectRole: (roleId: number | null) => void
}

/**
 * Tab «Vai trò & quyền»: cột trái chọn vai trò (`RoleSidePanel`), cột phải ma
 * trận (đối tượng × hành động) của vai trò đang chọn. Tách khỏi
 * `role-permission-page.tsx` (giữ trang < 200 dòng, bao-CR-5xx finding Low #4
 * của đợt rà soát tính năng phân quyền tung báo cáo) — HÀNH VI giữ nguyên
 * 100%, không đổi API/props ra ngoài trang.
 */
export function RolePermissionRolesTab({
  roles,
  rolesLoading,
  selectedRoleId,
  onSelectRole,
}: RolePermissionRolesTabProps) {
  const { can } = usePermission()
  const { user } = useAuth()
  const { data: meta, isLoading: metaLoading } = usePermissionMeta()
  const { data: savedRows, isFetching: permissionsLoading } = useRolePermissions(
    selectedRoleId ?? 0,
  )
  const savePermissions = useSaveRolePermissions()
  const deleteRole = useDeleteRole()
  const updateRole = useUpdateRole()

  //  ⚠️ Khởi tạo LẤY LUÔN dữ liệu đang có, đừng đổi về `useState({})`.
  //  `?role=7` nằm trên URL, nên vào lại trang bằng link đó (hoặc quay ra rồi
  //  bấm back) là `savedRows` có sẵn trong bộ đệm NGAY ở lượt render đầu — mà ở
  //  lượt đầu `useHasChanged` luôn trả `false`, nên nhịp dưới không chạy và ma
  //  trận hiện ra TRẮNG. Bấm «Lưu quyền» lúc đó là gửi danh sách rỗng, mà
  //  `role/service.set_permissions` xóa hết rồi ghi lại: mất sạch quyền của vai
  //  trò, kéo theo mọi tài khoản đang giữ nó (bao-CR-492).
  const [matrix, setMatrix] = useState<Record<string, RolePermissionRow>>(() =>
    rowsToMatrix(savedRows),
  )

  // Đổi vai trò -> nạp lại ma trận. Khóa theo `entity` để tra nhanh khi tick ô.
  if (useHasChanged(savedRows)) setMatrix(rowsToMatrix(savedRows))

  const selectedRole = roles?.find((role) => role.id === selectedRoleId) ?? null

  //  Vai trò MÌNH ĐANG GIỮ thì chỉ xem, không sửa. Tick thêm một ô vào đây là
  //  quyền của chính mình lên ngay ở request sau — cửa sau của tự nâng quyền,
  //  backend đã chặn bằng `privilege_escalation.chan_sua_vai_tro_cua_chinh_minh`.
  //  Khóa luôn ở giao diện để người ta biết là có LUẬT, chứ không tick xong hai
  //  chục ô rồi ăn 403 và tưởng hệ hỏng (CR-158).
  //  bao-CR-523: Quản trị hệ thống được MIỄN chốt này (backend miễn L1 cho họ).
  const isSystemAdmin = holdsSystemAdminRole(roles, user?.role_ids)
  const holdsThisRole =
    !!selectedRoleId && !!user?.role_ids?.includes(selectedRoleId) && !isSystemAdmin
  //  Ma trận của CHÍNH vai trò Quản trị hệ thống luôn FULL — chỉ xem, không có
  //  nút Lưu. Backend từ chối mọi bản làm hụt (400) và seed ép lại mỗi lần deploy.
  const viewingAdminRole = isSystemAdminRole(selectedRole)
  const canWriteRole = can('role', 'write') && !holdsThisRole && !viewingAdminRole

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
    onSelectRole(null)
    setMatrix({})
  }

  return (
    //  Cột trái 320px (trước là 260px): dòng vai trò nay in cả mô tả +
    //  chip phân hệ, và tên KHÔNG cắt "..." nữa (bao-CR-428).
    <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
      {rolesLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <RoleSidePanel
          roles={roles ?? []}
          selectedId={selectedRoleId}
          onSelect={(roleId) => onSelectRole(roleId)}
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
                onDescribe={(roleId, description) => updateRole.mutate({ roleId, description })}
              />

              <div className="flex items-center gap-2">
                {!viewingAdminRole && (
                  <PermissionGate entity="role" action="write">
                    <Button onClick={handleSave} disabled={savePermissions.isPending || holdsThisRole}>
                      {savePermissions.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                      Lưu quyền
                    </Button>
                  </PermissionGate>
                )}

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

            {viewingAdminRole && (
              <p className="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-sky-900">
                {SYSTEM_ADMIN_FULL_NOTE} — ma trận này chỉ để xem. Phân hệ mới ra
                đời thì hệ thống tự cấp đủ cho vai trò này ở lần cập nhật kế tiếp.
              </p>
            )}

            {holdsThisRole && !viewingAdminRole && (
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
                //  Dựng lại theo vai trò để tập mở/gập ban đầu tính từ ma
                //  trận của ĐÚNG vai trò đó (xem `collapseGroupsWithoutTicks`).
                key={selectedRoleId}
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
  )
}
