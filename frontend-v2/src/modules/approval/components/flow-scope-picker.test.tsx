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

  it('loại chứng từ khác văn bản thì nói thẳng là chưa có bộ chọn', () => {
    render(<FlowScopePicker entity="purchase_order" condition="" onChange={vi.fn()} />)

    expect(screen.getByText(/chưa có bộ chọn riêng/)).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })
})
