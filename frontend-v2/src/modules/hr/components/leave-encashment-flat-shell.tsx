import { ArrowLeft } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { ERP_FILLED_FIELDS, ERP_FLATTEN_CARDS } from '@/shared/ui/erp-flat-styles'
import { FormSectionProvider, type FormSectionContextValue } from '@/shared/ui/form-section'
import { PageContainer } from '@/shared/ui/page-container'
import { cn } from '@/shared/utils/cn'

/** Kiểu nhóm phẳng của trang — cùng bộ với `CrudDetailFlatLayout` (Loại nghỉ, Chính sách nghỉ phép). */
const SECTION_STYLE: FormSectionContextValue = {
  variant: 'flat',
  inset: true,
  storagePrefix: 'hr.leave-encashment',
  hints: 'icon',
}

interface LeaveEncashmentFlatShellProps {
  title: string
  /** Nhãn cạnh tiêu đề (trạng thái, lý do). */
  chips?: ReactNode
  /** Nút bên phải hàng tiêu đề: Lưu nháp / Gửi duyệt / Duyệt / Hủy… */
  actions?: ReactNode
  onBack: () => void
  /** Dải cảnh báo mảnh ngay dưới hàng tiêu đề (vd. kế toán từ chối chi). */
  banner?: ReactNode
  children: ReactNode
}

/**
 * KHUNG PHẲNG của trang lập / chi tiết phiếu thanh toán nghỉ phép (duoc-CR-719) — chép khuôn `CrudDetailFlatLayout`:
 * mặt phẳng trắng tràn khung, hàng tiêu đề dính (mũi tên lùi · tiêu đề · nhãn · nút bên phải), các nhóm ngăn bằng
 * đường kẻ, ô nhập nền xám không viền, chú thích thu vào (i). Không dùng thẳng `CrudDetailFlatLayout` vì nút lùi ở đây
 * phải LÙI THEO LỊCH SỬ (giữ bộ lọc của danh sách) và nhãn trạng thái dùng màu của `LeaveStatusBadge`.
 *
 * Dính chỉ từ `md` (như hồ sơ nhân sự): ở điện thoại cụm tiêu đề + nút cao 2–3 hàng, dính lại mất cả khúc màn hình;
 * nút vẫn nằm ngay đầu trang. Dưới `md` cụm nút chiếm trọn một hàng để `PRIMARY_ACTION_SLOT` trải hết bề ngang.
 */
export function LeaveEncashmentFlatShell({
  title,
  chips,
  actions,
  onBack,
  banner,
  children,
}: LeaveEncashmentFlatShellProps) {
  return (
    <PageContainer className="flex min-h-full flex-col bg-card p-0 lg:p-0">
      <div className="z-20 bg-card md:sticky md:top-0">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b px-4 py-3 md:px-6">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="-ml-2 shrink-0"
            aria-label="Về danh sách"
            title="Về danh sách"
            onClick={onBack}
          >
            <ArrowLeft />
          </Button>
          <h1 className="line-clamp-2 min-w-0 text-lg font-semibold">{title}</h1>
          {chips}
          {actions && (
            <div className="ml-auto flex flex-wrap items-center justify-end gap-2 max-md:w-full">{actions}</div>
          )}
        </div>
        {banner}
      </div>

      <FormSectionProvider value={SECTION_STYLE}>
        <div className={cn('min-w-0', ERP_FILLED_FIELDS, ERP_FLATTEN_CARDS)}>{children}</div>
      </FormSectionProvider>
    </PageContainer>
  )
}
