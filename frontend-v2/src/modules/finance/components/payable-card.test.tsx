import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PayableCard } from './payable-card'
import type { Payable } from '../types/payable'

function payable(overrides: Partial<Payable> = {}): Payable {
  return {
    id: 1,
    company_id: 1,
    supplier_code: 'Cẩm Hùng',
    supplier_name: 'CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI BAO BÌ CẨM HÙNG',
    source_type: 'goods',
    po_id: 9,
    po_code: 'PO-DEMO-009',
    misa_code: '',
    invoice_no: 'DEMO-009',
    invoice_date: '2026-03-01',
    incur_date: '2026-03-01',
    due_date: '2026-03-31',
    created_at: '2026-03-01T08:00:00',
    amount: 26_000_000,
    vat: 2_620_000,
    total: 28_620_000,
    paid_amount: 0,
    remaining: 28_620_000,
    status: 'unpaid',
    status_label: 'Chờ thanh toán',
    aging: '>90',
    ...overrides,
  }
}

/**
 * Chữ của DÒNG GIỮA (mã ĐMH · loại nợ · số hóa đơn), gộp khoảng trắng.
 *
 * ⚠️ Đừng khẳng định số hóa đơn bằng `getByText(/DEMO-009/)`: mã ĐMH là
 * `PO-DEMO-009` nên chuỗi con đó khớp HAI phần tử và bài kiểm đỏ vì bản thân
 * nó sai, không phải vì mã sai.
 */
function metaTextOf(poCode: string): string {
  const meta = screen.getByText(poCode).parentElement
  return (meta?.textContent ?? '').replace(/\s+/g, ' ').trim()
}

describe('PayableCard', () => {
  it('bày đủ thứ nhận ra một khoản nợ: NCC · mã ĐMH · loại nợ · số HĐ · hạn trả · còn lại', () => {
    render(<PayableCard row={payable()} />)

    expect(
      screen.getByText('CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI BAO BÌ CẨM HÙNG'),
    ).toBeInTheDocument()
    //  Khẳng định theo TỪNG ĐOẠN `· …`, không so cả chuỗi: khoảng hở giữa các
    //  vế là `gap` của flex chứ không phải ký tự, nên chuỗi ghép ra
    //  "PO-DEMO-009· Hàng hóa· DEMO-009" — so nguyên chuỗi là buộc bài kiểm
    //  vào một chi tiết bố cục, đổi `gap` thành khoảng trắng là đỏ oan.
    const meta = metaTextOf('PO-DEMO-009')
    expect(meta).toContain('· Hàng hóa')
    expect(meta).toContain('· DEMO-009')
    expect(screen.getByText(/Hạn 31\/03\/2026/)).toBeInTheDocument()
    expect(screen.getByText('28.620.000 đ')).toBeInTheDocument()
  })

  it('KHÔNG cắt cụt tên NCC — đây là sổ để đối chiếu', () => {
    //  Khách báo 31/08/2026 rằng tên bị cắt thành "Công ty TNHH Thương mại…"
    //  nên phải rê chuột từng dòng mới đọc nổi. Cột `supplier_name` của bảng vì
    //  vậy khai `wrap: true`; thẻ cũng phải giữ nguyên luật đó.
    const { container } = render(<PayableCard row={payable()} />)

    expect(container.querySelector('.truncate')).toBeNull()
  })

  it('thiếu số hóa đơn thì nói thẳng "chưa có HĐ", không để trống', () => {
    //  Rỗng = chưa lên được đề nghị thanh toán. Để trống như một ô rỗng bình
    //  thường thì người dùng không biết vì sao khoản này không chọn được.
    render(<PayableCard row={payable({ invoice_no: '' })} />)

    expect(screen.getByText(/chưa có HĐ/)).toBeInTheDocument()
  })

  it('trả một phần thì bày kèm phần ĐÃ TRẢ để "còn lại" nhỏ hơn tổng có lời giải thích', () => {
    render(
      <PayableCard row={payable({ paid_amount: 2_786_400, remaining: 1_857_600 })} />,
    )

    expect(screen.getByText(/đã trả 2\.786\.400 đ/)).toBeInTheDocument()
    expect(screen.getByText('1.857.600 đ')).toBeInTheDocument()
  })

  it('chưa trả đồng nào thì KHÔNG bày "(đã trả 0 đ)" — một dòng nhiễu không nói gì', () => {
    render(<PayableCard row={payable({ paid_amount: 0 })} />)

    expect(screen.queryByText(/đã trả/)).toBeNull()
  })

  it('tất toán rồi thì còn lại 0, vẫn phải hiện số chứ không để trống ô tiền', () => {
    //  `formatMoney(0)` trả "0" chứ không trả chuỗi rỗng — nếu có ngày nó đổi,
    //  thẻ sẽ mất hẳn con số và bài kiểm này đỏ lên trước khi ai kịp giao.
    render(<PayableCard row={payable({ paid_amount: 28_620_000, remaining: 0 })} />)

    expect(screen.getByText('0 đ')).toBeInTheDocument()
  })

  it('nợ ÂM (trả dư / cấn trừ quá tay) vẫn hiện nguyên dấu trừ, không nuốt mất', () => {
    //  Dữ liệu thật có khoản `remaining` âm (xem PO-DEMO-014). Nuốt dấu trừ thì
    //  một khoản công ty đang trả DƯ đọc ra như một khoản còn nợ.
    render(<PayableCard row={payable({ remaining: -4_860_000 })} />)

    expect(screen.getByText('-4.860.000 đ')).toBeInTheDocument()
  })

  it('NCC chưa có tên chụp lại thì lấy MÃ thay, không mở đầu bằng dòng trống', () => {
    render(<PayableCard row={payable({ supplier_name: '' })} />)

    expect(screen.getByText('Cẩm Hùng')).toBeInTheDocument()
  })

  it('thiếu cả tên lẫn mã NCC thì vẫn có dấu gạch, không để thẻ bắt đầu bằng khoảng trắng', () => {
    render(<PayableCard row={payable({ supplier_name: '', supplier_code: '' })} />)

    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('loại nợ luôn có mặt — một ĐMH đẻ hai dòng (hàng hóa + vận chuyển) trùng mọi thứ khác', () => {
    //  Bỏ trường này thì hai thẻ liền nhau giống hệt nhau và không cách nào
    //  biết thẻ nào là thẻ nào.
    render(<PayableCard row={payable({ source_type: 'shipping' })} />)

    expect(screen.getByText(/Vận chuyển/)).toBeInTheDocument()
  })

  it('mã nguồn nợ lạ thì hiện nguyên mã, không để trống chỗ đó', () => {
    render(<PayableCard row={payable({ source_type: 'ma_la' as Payable['source_type'] })} />)

    expect(screen.getByText(/ma_la/)).toBeInTheDocument()
  })

  it('chưa có hạn trả thì bỏ hẳn dòng hạn, không hiện "Hạn " cụt đuôi', () => {
    render(<PayableCard row={payable({ due_date: '' })} />)

    expect(screen.queryByText(/Hạn/)).toBeNull()
  })
})
