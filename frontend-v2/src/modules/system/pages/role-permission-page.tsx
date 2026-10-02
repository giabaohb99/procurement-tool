import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { ReportAccessTab } from '../components/report-access-tab'
import { RolePermissionRolesTab } from '../components/role-permission-roles-tab'
import { UserAccountTable } from '../components/user-account-table'
import { useRoles } from '@/modules/hr/hooks/use-roles'
import { usePermission } from '@/core/authorization/use-permission'

/**
 * Màn Phân quyền tài khoản — hai tab của hệ phân quyền hai trục:
 *  • "Vai trò & quyền": ma trận (đối tượng × hành động) của từng vai trò.
 *  • "Người dùng": ai đang giữ vai trò nào, mở tiếp để đặt phạm vi dữ liệu.
 */
export function RolePermissionPage() {
  const [tab, setTab] = useUrlParamState('tab', 'roles')
  //  Vai trò đang mở ghi lên URL (`?role=7`) để hộp thoại Phạm vi ở màn tài khoản
  //  trỏ thẳng tới ma trận của ĐÚNG vai trò đó. Không có nó thì câu "sửa bậc ở
  //  màn Ma trận quyền" biến thành bài tập tự tìm trong danh sách vai trò.
  const [roleParam, setRoleParam] = useUrlParamState('role', '')
  const selectedRoleId = Number(roleParam) || null

  const { can } = usePermission()
  const { data: roles, isLoading: rolesLoading } = useRoles()

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
          {/*  `role.read` đủ để XEM tab này — nút Sửa trong bảng tự ẩn riêng
               theo `role.write` (`ReportAccessTab` nhận `canWrite` qua prop). */}
          {can('role', 'read') && <TabsTrigger value="reports">Báo cáo</TabsTrigger>}
        </TabsList>

        <TabsContent value="roles">
          <RolePermissionRolesTab
            roles={roles}
            rolesLoading={rolesLoading}
            selectedRoleId={selectedRoleId}
            onSelectRole={(roleId) => setRoleParam(roleId === null ? '' : String(roleId))}
          />
        </TabsContent>

        <TabsContent value="users">
          <UserAccountTable roles={roles ?? []} />
        </TabsContent>

        {can('role', 'read') && (
          <TabsContent value="reports">
            <ReportAccessTab canWrite={can('role', 'write')} />
          </TabsContent>
        )}
      </Tabs>
    </PageContainer>
  )
}
