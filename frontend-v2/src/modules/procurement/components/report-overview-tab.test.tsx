import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ALL_PERIOD } from '../types/purchase-report'
import { ReportOverviewTab } from './report-overview-tab'

//  Khổ màn đổi theo từng bài — biến này là chỗ bài kiểm bẻ lái.
let mobile = false
vi.mock('@/shared/hooks/use-mobile', () => ({
  useIsMobile: () => mobile,
}))

//  Hộp thoại chi tiết theo ngày gọi react-query; bài này không đụng tới nó nên
//  thay bằng khối rỗng, đỡ phải dựng QueryClientProvider.
vi.mock('./report-daily-dialog', () => ({
  ReportDailyDialog: () => null,
}))

/** Câu chốt của đoạn giải thích — dùng để biết nội dung có đang hiện không. */
const BODY = /Hai con số đo khác nhau/

function renderTab(period = ALL_PERIOD) {
  return render(
    <ReportOverviewTab
      data={undefined}
      months={[]}
      period={period}
      periodLabel="Cả năm"
      isLoading={false}
    />,
  )
}

beforeEach(() => {
  mobile = false
})

describe('ReportOverviewTab — khối «Lưu ý cách đọc số»', () => {
  /**
   * Ở màn rộng khối này mở sẵn và KHÔNG có nút đóng: nó là lời giải thích vì
   * sao *Giá trị đặt hàng* khác biểu đồ *Chi phí mua theo tháng* — hai con số
   * nằm cạnh nhau và trông như phải bằng nhau.
   */
  it('mở sẵn, không có nút gấp, ở màn rộng', () => {
    renderTab()

    expect(screen.getByText(BODY)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Lưu ý cách đọc số/ })).not.toBeInTheDocument()
  })

  /**
   * ⚠️ Bài quan trọng nhất của tệp này. Ở 390px đoạn văn này dài 7 dòng ≈ 150px
   * và chắn ngay trên dải thẻ số — thứ người ta mở tab ra để xem.
   */
  it('gấp lại ở khổ điện thoại nhưng vẫn nói là CÓ lời giải thích', () => {
    mobile = true

    renderTab()

    expect(screen.queryByText(BODY)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Lưu ý cách đọc số/ })).toBeInTheDocument()
  })

  it('bấm vào là mở ra, bấm lần nữa là gấp lại', async () => {
    mobile = true

    renderTab()
    const toggle = screen.getByRole('button', { name: /Lưu ý cách đọc số/ })

    await userEvent.click(toggle)
    expect(screen.getByText(BODY)).toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    await userEvent.click(toggle)
    expect(screen.queryByText(BODY)).not.toBeInTheDocument()
  })

  //  Câu nhắc «đang lọc theo tháng X» chỉ mọc khi thật sự đang lọc — nó giải
  //  thích vì sao thẻ số và biểu đồ không cùng một kỳ.
  it('thêm câu nhắc khi đang lọc theo một tháng', () => {
    renderTab('2026-07')

    expect(screen.getByText(/riêng biểu đồ "Chi phí mua theo tháng" vẫn hiển thị cả năm/)).
      toBeInTheDocument()
  })
})
