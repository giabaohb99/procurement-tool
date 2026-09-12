import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { DashboardAlert } from '../api/procurement-dashboard-api'
import { ProcurementAlertList } from './procurement-alert-list'

//  Khổ màn đổi theo từng bài — biến này là chỗ bài kiểm bẻ lái.
let mobile = false
vi.mock('@/shared/hooks/use-mobile', () => ({
  useIsMobile: () => mobile,
}))

/** Backend trả tối đa 6 việc (`alerts[:6]` trong `dashboard/controller.py`). */
function makeAlerts(count: number): DashboardAlert[] {
  return Array.from({ length: count }, (_, index) => ({
    type: 'delivery',
    level: index === 0 ? 'danger' : 'warn',
    title: `Giao hàng TRỄ: PO0${index} · Thùng carton 5 lớp (hẹn 2026-07-0${index})`,
    link: `/purchase-orders/${index}`,
  }))
}

beforeEach(() => {
  mobile = false
})

describe('ProcurementAlertList', () => {
  it('bày đủ mọi việc trên màn rộng, không có nút xem thêm', () => {
    render(<ProcurementAlertList alerts={makeAlerts(6)} />)

    expect(screen.getAllByRole('listitem')).toHaveLength(6)
    expect(screen.queryByRole('button', { name: /Xem thêm/ })).not.toBeInTheDocument()
  })

  /**
   * ⚠️ Bài quan trọng nhất của tệp này.
   *
   * Ở khổ điện thoại danh sách này KHÔNG được nằm trong một ô cuộn lồng (xem
   * ghi chú ở `procurement-dashboard-page`), nên nó phải tự cắt bớt. Mỗi câu
   * cảnh báo dài 3-4 dòng: bày cả sáu là đẩy bốn khối biểu đồ phía dưới ra
   * ngoài tầm với.
   */
  it('cắt còn 3 việc ở khổ điện thoại và nói rõ còn mấy việc chưa bày', () => {
    mobile = true

    render(<ProcurementAlertList alerts={makeAlerts(6)} />)

    expect(screen.getAllByRole('listitem')).toHaveLength(3)
    expect(screen.getByRole('button', { name: /Xem thêm 3 việc/ })).toBeInTheDocument()
  })

  it('bấm xem thêm là bày nốt phần còn lại và nút biến mất', async () => {
    mobile = true

    render(<ProcurementAlertList alerts={makeAlerts(6)} />)
    await userEvent.click(screen.getByRole('button', { name: /Xem thêm/ }))

    expect(screen.getAllByRole('listitem')).toHaveLength(6)
    expect(screen.queryByRole('button', { name: /Xem thêm/ })).not.toBeInTheDocument()
  })

  //  Vừa đúng ngưỡng thì đừng mọc nút: «Xem thêm 0 việc» là câu vô nghĩa, mà
  //  `alerts.length - MOBILE_PREVIEW` rất dễ ra 0 vì backend hay trả ít việc.
  it('không mọc nút khi số việc vừa đúng phần bày sẵn', () => {
    mobile = true

    render(<ProcurementAlertList alerts={makeAlerts(3)} />)

    expect(screen.getAllByRole('listitem')).toHaveLength(3)
    expect(screen.queryByRole('button', { name: /Xem thêm/ })).not.toBeInTheDocument()
  })

  it('rỗng thì nói không có việc nào, không dựng danh sách', () => {
    mobile = true

    render(<ProcurementAlertList alerts={[]} />)

    expect(screen.getByText('Không có việc nào cần xử lý.')).toBeInTheDocument()
    expect(screen.queryByRole('listitem')).not.toBeInTheDocument()
  })
})
