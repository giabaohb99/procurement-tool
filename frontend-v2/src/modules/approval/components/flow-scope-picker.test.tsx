import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FlowScopePicker } from './flow-scope-picker'

//  Hai danh mục này gọi API qua TanStack Query — thay bằng dữ liệu tĩnh để bài
//  kiểm chỉ nói về BỘ CHỌN, không nói về mạng.
vi.mock('@/modules/document/hooks/use-document-types', () => ({
  useActiveDocumentTypes: () => [
    { id: 3, name: 'Quy chế', code: 'QC', is_active: true },
    { id: 4, name: 'Quy trình', code: 'QT', is_active: true },
  ],
}))

vi.mock('@/modules/document/hooks/use-documents', () => ({
  useDocuments: () => ({
    data: { total: 1, items: [{ id: 9, title: 'Quy chế chi tiêu', display_code: 'QC-01' }] },
  }),
}))

//  bao-CR-579: Đặt xe / Duyệt dấu dùng bộ dựng điều kiện, bộ này nạp thêm bốn
//  danh mục — thay bằng dữ liệu tĩnh như hai danh mục trên.
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { items: [{ id: 1, name: 'DEGO HOLDING', code: 'DEGO' }] } }),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({
    data: { items: [{ id: 17, name: 'Lập trình & IT nội bộ', code: 'IT', is_active: true }] },
  }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({ data: { items: [{ id: 258, full_name: 'Nguyễn Kỷ Thảo Thơ', code: 'TESTREQ' }] } }),
}))
vi.mock('@/modules/approval-seal/hooks/use-seal-types', () => ({
  useSealTypes: () => ({
    data: {
      items: [
        { id: 5, name: 'Dấu công ty', is_active: true },
        { id: 6, name: 'Dấu đã ngừng dùng', is_active: false },
      ],
    },
  }),
}))

describe('FlowScopePicker', () => {
  it('chọn «một số loại văn bản» thì hiện ngay ô chọn loại', async () => {
    //  LỖI ĐÃ XẢY RA: kiểu đang chọn suy thẳng từ chuỗi điều kiện, mà chuỗi chỉ
    //  mang được lựa chọn đã đủ — chưa tick loại nào thì chuỗi rỗng, đọc ngược
    //  ra «tất cả», ô chọn bật về dòng đầu và KHÔNG có gì hiện ra để tick.
    const user = userEvent.setup()
    render(<FlowScopePicker entity="document" condition="" onChange={vi.fn()} />)

    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByRole('option', { name: 'Chỉ một số loại văn bản' }))

    expect(screen.getByRole('button', { name: /Chọn loại văn bản/ })).toBeInTheDocument()
  })

  it('chọn «một số văn bản cụ thể» thì hiện ô chọn văn bản', async () => {
    const user = userEvent.setup()
    render(<FlowScopePicker entity="document" condition="" onChange={vi.fn()} />)

    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByRole('option', { name: 'Chỉ một số văn bản cụ thể' }))

    expect(screen.getByRole('button', { name: /Chọn văn bản/ })).toBeInTheDocument()
  })

  it('chọn kiểu hẹp mà chưa tick gì thì báo luồng vẫn áp cho mọi văn bản', async () => {
    const user = userEvent.setup()
    render(<FlowScopePicker entity="document" condition="" onChange={vi.fn()} />)

    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByRole('option', { name: 'Chỉ một số loại văn bản' }))

    expect(screen.getByText(/vẫn áp cho/)).toBeInTheDocument()
  })

  it('đọc lại được điều kiện đã lưu: đúng kiểu và đúng mục đã chọn', () => {
    render(
      <FlowScopePicker
        entity="document"
        condition='[{"field":"doc_type_id","op":"in","value":[3]}]'
        onChange={vi.fn()}
      />,
    )

    expect(screen.getByRole('combobox')).toHaveTextContent('Chỉ một số loại văn bản')
    expect(screen.getByText('Quy chế')).toBeInTheDocument()
  })

  it('says the flow applies to every ticket when the entity has no condition fields', () => {
    render(<FlowScopePicker entity="purchase_order" condition="" onChange={vi.fn()} />)

    expect(screen.getByText(/chưa có ô nào để đặt điều kiện/)).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })

  it('vehicle booking without a condition is the default flow, not the document picker', () => {
    //  LỖI ĐÃ XẢY RA (bao-CR-579): Đặt xe rơi vào câu «chưa có bộ chọn riêng» dù
    //  bộ máy duyệt đã đọc được điều kiện trên phiếu đặt xe — người cấu hình không
    //  khai nổi luồng riêng cho phiếu giao hàng.
    render(<FlowScopePicker entity="vehicle_booking" condition="" onChange={vi.fn()} />)

    expect(screen.getByText(/luồng/)).toBeInTheDocument()
    expect(screen.getByText(/mặc định/)).toBeInTheDocument()
    expect(screen.queryByText('Chỉ một số loại văn bản')).not.toBeInTheDocument()
  })

  it('reads a saved booking condition back as a sentence with the type label', () => {
    render(
      <FlowScopePicker
        entity="vehicle_booking"
        condition='[{"field":"request_type","op":"eq","value":2}]'
        onChange={vi.fn()}
      />,
    )

    expect(screen.getAllByText(/Giao hàng/).length).toBeGreaterThan(0)
    expect(screen.queryByText(/khai tay/)).not.toBeInTheDocument()
  })

  it('reads a saved seal condition back with the seal type name', () => {
    render(
      <FlowScopePicker
        entity="seal_request"
        condition='[{"field":"seal_type_id","op":"in","value":[5]}]'
        onChange={vi.fn()}
      />,
    )

    expect(screen.getAllByText(/Dấu công ty/).length).toBeGreaterThan(0)
  })

  it('keeps an unknown hand-written booking condition visible instead of dropping it', () => {
    render(
      <FlowScopePicker
        entity="vehicle_booking"
        condition='[{"field":"total","op":"gte","value":50000000}]'
        onChange={vi.fn()}
      />,
    )

    expect(screen.getByText(/khai tay/)).toBeInTheDocument()
  })
})
