import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ProcessOptionCard, type ProcessOptionCardData } from './process-option-card'

function option(overrides: Partial<ProcessOptionCardData> = {}): ProcessOptionCardData {
  return {
    display_label: 'Phương án 2',
    public_id: 2,
    is_chosen: false,
    supplier_code: 'NCC-CH',
    supplier_name: 'CÔNG TY TNHH BAO BÌ CẨM HÙNG',
    snap_product_name: 'Thùng carton 5 lớp',
    snap_spec: '60x40x40',
    snap_price_by_volume: 12_500,
    snap_moq: 100,
    snap_quote_unit: 'Cái',
    snap_vat: 8,
    ...overrides,
  }
}

describe('ProcessOptionCard', () => {
  it('puts the supplier first and drops the option label to the sky sub-line', () => {
    render(<ProcessOptionCard option={option()} labelPrefix="Phương án" sourceLabel="Từ khảo sát" />)

    const supplier = screen.getByText('CÔNG TY TNHH BAO BÌ CẨM HÙNG')
    const label = screen.getByText('Phương án 2')
    //  Thứ tự trong DOM = thứ tự mắt đọc: NCC phải đứng TRƯỚC nhãn phương án.
    expect(supplier.compareDocumentPosition(label) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByText(/Từ khảo sát/)).toBeInTheDocument()
    expect(screen.getByText('12.500 đ/Cái')).toBeInTheDocument()
    expect(screen.getByText('MOQ 100')).toBeInTheDocument()
    expect(screen.getByText('VAT 8%')).toBeInTheDocument()
  })

  it('hides every trace of the supplier when the viewer lacks supplier:read', () => {
    //  Backend trả NCC rỗng cho người thiếu quyền — thẻ không được bày "(chưa có NCC)"
    //  vì như vậy là nói sai: phương án CÓ NCC, chỉ là người này không được xem.
    render(
      <ProcessOptionCard
        option={option({ supplier_name: '', supplier_code: '' })}
        labelPrefix="Phương án"
        showSupplier={false}
      />,
    )

    expect(screen.queryByText(/chưa có NCC/)).toBeNull()
    expect(screen.getByText('Thùng carton 5 lớp')).toBeInTheDocument()
  })

  it('says the supplier is missing instead of opening the card with a blank line', () => {
    render(
      <ProcessOptionCard
        option={option({ supplier_name: '', supplier_code: '' })}
        labelPrefix="Phương án"
      />,
    )

    expect(screen.getByText('(chưa có NCC)')).toBeInTheDocument()
  })

  it('falls back to prefix + public id when the option has no label (option 0 included)', () => {
    render(
      <ProcessOptionCard option={option({ display_label: '', public_id: 0 })} labelPrefix="Option" />,
    )

    expect(screen.getByText('Option 0')).toBeInTheDocument()
  })

  it('price 0 reads "Chưa có giá", not "0 đ" that looks like a free quote', () => {
    render(
      <ProcessOptionCard
        option={option({ snap_price_by_volume: 0, snap_moq: 0, snap_vat: 0 })}
        labelPrefix="Phương án"
      />,
    )

    expect(screen.getByText('Chưa có giá')).toBeInTheDocument()
    expect(screen.queryByText(/MOQ/)).toBeNull()
    expect(screen.queryByText(/VAT/)).toBeNull()
  })

  it('shows the chosen badge only when the requester picked this option', () => {
    const { rerender } = render(<ProcessOptionCard option={option()} labelPrefix="Phương án" />)
    expect(screen.getByText('Chưa chọn')).toBeInTheDocument()

    rerender(<ProcessOptionCard option={option({ is_chosen: true })} labelPrefix="Phương án" />)
    expect(screen.getByText('Người YC đã chọn')).toBeInTheDocument()
  })

  it('renders editor fields and action buttons outside of any button', () => {
    render(
      <ProcessOptionCard
        option={option()}
        labelPrefix="Phương án"
        fields={[{ label: 'Ghi chú NSTM', content: <input aria-label="ghi chú" /> }]}
        actions={<button type="button">Gỡ</button>}
      />,
    )

    expect(screen.getByText('Ghi chú NSTM')).toBeInTheDocument()
    const remove = screen.getByRole('button', { name: 'Gỡ' })
    //  Lồng nút trong nút là HTML sai — thẻ không được tự bọc mình trong một `<button>`.
    expect(remove.parentElement?.closest('button')).toBeNull()
    expect(screen.getByLabelText('ghi chú').closest('button')).toBeNull()
  })
})
