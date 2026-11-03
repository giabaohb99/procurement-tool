import { useState } from 'react'
import { ArchiveRestore, CalendarPlus, ClipboardList } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { useCloseLeaveYear } from '../hooks/use-leave'
import { LeaveBalanceAllocateDialog } from './leave-balance-allocate-dialog'
import { LeaveCloseYearReviewDialog } from './leave-close-year-review-dialog'

interface LeaveBalancePageActionsProps {
  /** Năm đang xem trên màn (chuỗi từ URL). */
  year: string
}

/**
 * Cụm nút đầu màn Quỹ phép năm + hai hộp thoại của nó (tách khỏi `leave-balance-page.tsx`, review L6 của
 * duoc-CR-717). Cả ba thao tác đều ĐỤNG VÀO NGÀY PHÉP CỦA NGƯỜI KHÁC, nên gác `leave_balance.create` /
 * `write` chứ không đi chung khóa với đơn nghỉ:
 *  · **Cấp quỹ năm** (`create`) — mở hộp có lọc (D9a); chạy lại được, chỉ tạo dòng còn thiếu.
 *  · **Kết sổ cuối năm** (`write`, sửa hai dòng quỹ đã có) — đẩy số dư năm cũ sang năm mới theo luật khai ở
 *    từng loại nghỉ; chạy lại được, dòng đã kết sổ mang dấu `carried_out_days` nên lượt sau bỏ qua.
 *  · **Đối chiếu kết sổ** (duoc-CR-664) — tự mở ngay sau khi kết sổ xong, mở lại được để xem / xuất Excel.
 *
 * ⚠️ Kết sổ đứng TRƯỚC và ở dạng nút phụ: nó chạy mỗi năm một lần, còn Cấp quỹ là nút hằng ngày — hai nút
 * cùng cỡ cùng màu thì bấm nhầm, mà nhầm ở đây là dời phép của cả công ty.
 *
 * ⚠️ Khổ hẹp: các nút CHIA một hàng (`max-md:flex-1`) và nhãn rút gọn giữ tới tận `lg` — ở dải 768–1024px
 * nhãn đầy đủ cộng tiêu đề vượt bề ngang, cụm nút rớt xuống hàng riêng nép mép phải.
 */
export function LeaveBalancePageActions({ year }: LeaveBalancePageActionsProps) {
  const { can } = usePermission()
  const canAllocate = can('leave_balance', 'create')
  const canCloseYear = can('leave_balance', 'write')
  const closeYear = useCloseLeaveYear()
  const previousYear = Number(year) - 1
  //  `null` = đóng. Hộp Cấp quỹ khóa theo năm đang xem; bảng đối chiếu theo năm vừa kết sổ.
  const [allocateYear, setAllocateYear] = useState<number | null>(null)
  const [reviewYear, setReviewYear] = useState<number | null>(null)

  //  Kết sổ năm TRƯỚC năm đang xem. Hỏi lại trước khi chạy — nó chạm tới quỹ của mọi người trong phạm vi,
  //  và câu hỏi là chỗ duy nhất nói ra rằng nó chỉ chuyển những loại nghỉ CÓ khai luật.
  const closeYearNow = async () => {
    const ok = await confirm({
      title: `Kết sổ quỹ phép năm ${previousYear}?`,
      message:
        `Số dư năm ${previousYear} của những loại nghỉ có khai "Mang sang năm sau" hoặc ` +
        `"Quy đổi sang loại nghỉ khác" sẽ được đẩy sang năm ${previousYear + 1}. ` +
        'Loại để mặc định "Hết năm là mất" thì không đụng tới. ' +
        'Chạy lại được: dòng đã kết sổ sẽ bị bỏ qua, không nhân đôi số ngày.',
      confirmLabel: 'Kết sổ',
      tone: 'default',
    })
    if (ok) closeYear.mutate({ year: previousYear }, { onSuccess: () => setReviewYear(previousYear) })
  }

  return (
    <>
      {canCloseYear && (
        <Button
          variant="outline"
          className="max-md:flex-1 max-md:px-2 max-md:text-xs"
          onClick={closeYearNow}
          disabled={closeYear.isPending}
        >
          <ArchiveRestore className="size-4" />
          <span className="lg:hidden">Kết sổ {previousYear}</span>
          <span className="max-lg:hidden">Kết sổ năm {previousYear}</span>
        </Button>
      )}
      <Button
        variant="outline"
        className="max-md:flex-1 max-md:px-2 max-md:text-xs"
        onClick={() => setReviewYear(previousYear)}
      >
        <ClipboardList className="size-4" />
        <span className="lg:hidden">Đối chiếu {previousYear}</span>
        <span className="max-lg:hidden">Đối chiếu kết sổ {previousYear}</span>
      </Button>
      {canAllocate && (
        <Button className="max-md:flex-1 max-md:px-2 max-md:text-xs" onClick={() => setAllocateYear(Number(year))}>
          <CalendarPlus className="size-4" />
          <span className="lg:hidden">Cấp quỹ {year}</span>
          <span className="max-lg:hidden">Cấp quỹ năm {year}</span>
        </Button>
      )}
      <LeaveCloseYearReviewDialog year={reviewYear} onClose={() => setReviewYear(null)} />
      <LeaveBalanceAllocateDialog year={allocateYear} onClose={() => setAllocateYear(null)} />
    </>
  )
}
