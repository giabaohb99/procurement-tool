import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { SUPPLIER_METRICS, type MatrixRow, type ReportMonth } from '../types/purchase-report'
import { ReportMatrixTab } from './report-matrix-tab'

//  Khổ màn đổi theo từng bài — biến này là chỗ bài kiểm bẻ lái.
let mobile = false
vi.mock('@/shared/hooks/use-mobile', () => ({
  useIsMobile: () => mobile,
}))

//  Bảng chỉ gọi API khi người dùng bấm *Xem* trên khoảng ngày; không bài nào ở
//  đây đi đường đó, nên trả hook rỗng là đủ và tránh dựng QueryClientProvider.
vi.mock('../hooks/use-purchase-report', () => ({
  useReportRange: () => ({ data: undefined, isLoading: false }),
}))

/** Ba tháng, nhưng chỉ tháng 02 có phát sinh. */
const MONTHS: ReportMonth[] = [
  { key: '2026-01', label: '01/2026' },
  { key: '2026-02', label: '02/2026' },
  { key: '2026-03', label: '03/2026' },
]

const ROWS: MatrixRow[] = [
  {
    key: 'CÔNG TY TNHH SẢN XUẤT BAO BÌ ĐÔNG TÂY',
    trans: 4,
    late: 1,
    rate: 25,
    m: { '2026-02': { trans: 4, late: 1, rate: 25 } },
  },
]

function renderTab(rows: MatrixRow[] = ROWS) {
  return render(
    <ReportMatrixTab
      rows={rows}
      months={MONTHS}
      metrics={SUPPLIER_METRICS}
      nameLabel="Nhà cung cấp"
      title="Giao dịch nhà cung cấp"
      yearLabel="Năm 2026"
      rangeEndpoint="/api/reports/sup-range"
      nameWidth={260}
    />,
  )
}

beforeEach(() => {
  mobile = false
})

describe('ReportMatrixTab', () => {
  /**
   * ⚠️ Bài quan trọng nhất của tệp này.
   *
   * Bảng "Ngang" là pivot 12 tháng × 5 chỉ số — đo ở 390px là 41 cột / 2896px
   * trong khung 324px, tức nhìn thấy đúng cột tên. Khổ hẹp phải mở sẵn "Dọc".
   */
  it('mở sẵn chế độ Dọc ở khổ điện thoại', () => {
    mobile = true

    renderTab()

    expect(screen.getByRole('button', { name: 'Dọc' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Ngang' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('giữ chế độ Ngang ở màn rộng', () => {
    renderTab()

    expect(screen.getByRole('button', { name: 'Ngang' })).toHaveAttribute('aria-pressed', 'true')
  })

  /**
   * Tháng rỗng từng dựng đủ thẻ (viền màu + tiêu đề + hàng tiêu đề bảng + một ô
   * «Không có dữ liệu») ≈ 180px cho một thông tin bằng không.
   */
  it('không dựng khối cho tháng chưa phát sinh, nhưng NÓI RA là đã bỏ tháng nào', () => {
    mobile = true

    renderTab()

    expect(screen.getByText('Tháng 02/2026')).toBeInTheDocument()
    expect(screen.queryByText('Tháng 01/2026')).not.toBeInTheDocument()
    expect(screen.queryByText('Tháng 03/2026')).not.toBeInTheDocument()
    //  ⚠️ Không được im lặng: người dùng tự tick tháng ở nút «Tháng: n/12», tick
    //  xong không thấy gì mà không có câu này thì đọc ra là màn hình lỗi.
    expect(screen.getByText(/Chưa phát sinh trong 2 tháng/)).toBeInTheDocument()
    expect(screen.getByText(/01\/2026 · 03\/2026/)).toBeInTheDocument()
  })

  it('không có tháng nào rỗng thì không mọc câu thông báo', () => {
    mobile = true

    renderTab([
      {
        key: 'A',
        m: {
          '2026-01': { trans: 1 },
          '2026-02': { trans: 1 },
          '2026-03': { trans: 1 },
        },
      },
    ])

    expect(screen.queryByText(/Chưa phát sinh trong/)).not.toBeInTheDocument()
  })

  //  Không dòng nào thì mọi tháng đều rỗng — câu tóm tắt vẫn phải đúng số, chứ
  //  không được rơi vào «Chưa phát sinh trong 0 tháng».
  it('rỗng hoàn toàn thì đếm đúng số tháng bị bỏ', () => {
    mobile = true

    renderTab([])

    expect(screen.getByText(/Chưa phát sinh trong 3 tháng/)).toBeInTheDocument()
  })

  /**
   * ⚠️ Ở chế độ «Dọc» màn này dựng tới mười khối; nếu mỗi khối là một BẢNG thì
   * hàng tiêu đề «# · Nhà cung cấp · …» lặp lại mười lần, mỗi bảng một thanh
   * cuộn ngang, và cột tên bị bóp tới mức ba dòng «CÔNG TY TNHH …» giống hệt
   * nhau. Khổ hẹp phải là THẺ.
   */
  it('khổ điện thoại bày thẻ chứ không bày bảng, và tên hiện ĐỦ', () => {
    mobile = true

    renderTab()

    expect(document.querySelector('table')).toBeNull()
    //  Tên đầy đủ, không cắt — có hai chỗ (tổng năm + tháng 02).
    expect(
      screen.getAllByText('CÔNG TY TNHH SẢN XUẤT BAO BÌ ĐÔNG TÂY').length,
    ).toBeGreaterThan(0)
    //  Mọi chỉ số phải thấy được mà không cần kéo ngang.
    expect(screen.getAllByText('Tỷ lệ trễ').length).toBeGreaterThan(0)
  })

  /**
   * Thẻ không có hàng tiêu đề để bấm, nên phải có ô chọn sắp xếp riêng — bỏ
   * quên là khổ điện thoại mất hẳn khả năng sắp xếp.
   *
   * ⚠️ MỘT ô chọn chứ không phải dải nút bo tròn: dải nút chiếm hai hàng và khi
   * trôi qua dải điều khiển đang ghim thì viền bị cắt ngang thân, đọc ra như
   * lỗi vẽ (khách báo 12/09/2026).
   */
  it('khổ điện thoại có ô chọn sắp xếp, mặc định là chưa sắp xếp', () => {
    mobile = true

    renderTab()

    expect(screen.getByText('Sắp xếp:')).toBeInTheDocument()
    expect(screen.getByText('Mặc định')).toBeInTheDocument()
  })

  it('màn rộng giữ bảng và KHÔNG mọc ô sắp xếp', () => {
    renderTab()

    expect(document.querySelector('table')).not.toBeNull()
    expect(screen.queryByText('Sắp xếp:')).not.toBeInTheDocument()
  })
})
