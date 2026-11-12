import { usePermission } from '@/core/authorization/use-permission'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { HrSettingsForm } from '../components/hr-settings-form'
import { useHrSettings } from '../hooks/use-hr-settings'

/**
 * CÀI ĐẶT NHÂN SỰ (duoc-CR-713) — bố cục theo trang HR Settings của ERPNext: tiêu đề, dải tab gạch chân, các nhóm
 * cài đặt bên dưới. Mới có tab "Nghỉ phép" (chặn đơn lùi ngày · chặn tự duyệt); các tab còn lại của ERPNext (Chi phí,
 * Chấm công, Thâm niên, Tuyển dụng) thuộc phần DEGO đã chốt không làm nên không dựng tab rỗng.
 *
 * Gác `setting.read` (mục menu + trang); sửa cần `setting.write` — cùng khóa với Cấu hình hệ thống.
 */
export function HrSettingsPage() {
  const { can } = usePermission()
  const canRead = can('setting', 'read')
  const { data: fields, isPending, isError, refetch } = useHrSettings({ enabled: canRead })

  if (!canRead) {
    return (
      <ErrorState
        code="403"
        title="Không có quyền xem Cài đặt nhân sự"
        description="Trang này cần quyền Cấu hình hệ thống (setting:read). Liên hệ quản trị nếu bạn cần quyền này."
      />
    )
  }

  return (
    <PageContainer className="flex min-h-full flex-col">
      {/*  duoc-CR-753: dải tab của mục menu Thiết lập — chuyển sang năm màn cấu hình còn lại. */}
      <HrSetupTabs />
      {isPending ? (
        <div className="space-y-3">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-28" />
          <Skeleton className="h-20" />
        </div>
      ) : isError || !fields ? (
        <ErrorState
          title="Không tải được cài đặt"
          description="Thử tải lại; nếu vẫn lỗi hãy báo quản trị."
        >
          <button type="button" className="text-primary underline" onClick={() => void refetch()}>
            Tải lại
          </button>
        </ErrorState>
      ) : (
        <HrSettingsForm
          //  Lưu xong dữ liệu đổi → form dựng lại từ giá trị mới (nút Lưu tắt lại).
          key={JSON.stringify(fields.map((field) => field.value))}
          fields={fields}
          canWrite={can('setting', 'write')}
          canReadRoles={can('role', 'read')}
        />
      )}
    </PageContainer>
  )
}
