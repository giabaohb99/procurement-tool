import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import type { BookingPickOptions } from '../types/vehicle-booking'
import { approverSelectOptions, companySelectOptions } from '../utils/booking-pick-options'

interface BookingApprovalRoutingFieldsProps {
  data: BookingPickOptions | undefined
  isLoading: boolean
  companyId: number
  approverUserId: number
  /** Tên lưu sẵn trên phiếu — để ô vẫn đọc được khi giá trị cũ không còn trong danh sách. */
  savedCompanyName?: string
  savedApproverName?: string
  /** Tài khoản đang lập phiếu — bị bỏ khỏi danh sách người duyệt. */
  selfUserId?: number
  /** Tải danh sách lỗi — nói thẳng ra, đừng để ô trống đọc như «chưa ai có quyền». */
  isError?: boolean
  onCompanyChange: (id: number) => void
  onApproverChange: (userId: number) => void
}

/**
 * Khối «Người phê duyệt + Công ty» của phiếu đặt xe (duoc-CR-681) — người phê duyệt đứng TRƯỚC (anh Được
 * chốt 24/10/2026). Hai ô độc lập.
 *
 * Người duyệt = người có quyền Duyệt đặt xe ở màn Phân quyền (không tính Quản trị, chỉ phạm vi Phòng
 * ban / Công ty / Tất cả). Gửi duyệt xong, thư «Gửi duyệt» đi tới đúng người này.
 */
export function BookingApprovalRoutingFields({
  data,
  isLoading,
  companyId,
  approverUserId,
  savedCompanyName = '',
  savedApproverName = '',
  selfUserId = 0,
  isError = false,
  onCompanyChange,
  onApproverChange,
}: BookingApprovalRoutingFieldsProps) {
  const companies = companySelectOptions(data, companyId, savedCompanyName)
  const approvers = approverSelectOptions(data, approverUserId, savedApproverName, selfUserId)
  const noApprover = data !== undefined && data.approvers.length === 0

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <Label htmlFor="booking-approver">
            Người phê duyệt <RequiredMark />
          </Label>
          <SearchSelect
            id="booking-approver"
            value={approverUserId ? String(approverUserId) : ''}
            onChange={(value) => onApproverChange(Number(value) || 0)}
            options={approvers}
            placeholder={isLoading ? 'Đang tải…' : 'Chọn người phê duyệt'}
            searchPlaceholder="Tìm theo tên hoặc mã nhân viên…"
            emptyMessage="Không tìm thấy người phê duyệt."
            disabled={isLoading}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="booking-company">
            Công ty <RequiredMark />
          </Label>
          <SearchSelect
            id="booking-company"
            value={companyId ? String(companyId) : ''}
            onChange={(value) => onCompanyChange(Number(value) || 0)}
            options={companies}
            placeholder={isLoading ? 'Đang tải…' : 'Chọn công ty'}
            searchPlaceholder="Tìm theo tên hoặc MST…"
            emptyMessage="Không tìm thấy công ty."
            disabled={isLoading}
          />
        </div>
      </div>
      {isError ? (
        <p className="text-xs text-destructive">
          Không tải được danh sách công ty và người duyệt — tải lại trang rồi thử lại.
        </p>
      ) : noApprover ? (
        <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Chưa ai được cấp quyền duyệt phiếu đặt xe — nhờ quản trị cấp ở màn Phân quyền tài khoản.
        </p>
      ) : (
        <p className="text-xs text-muted-foreground">
          Danh sách người duyệt lấy theo phân quyền duyệt phiếu đặt xe. Gửi duyệt xong, thư báo đi tới
          người được chọn — trừ khi luồng duyệt đặt xe khai bước khác (trưởng bộ phận, theo vai trò…),
          lúc đó phiếu đi theo luồng.
        </p>
      )}
    </>
  )
}
