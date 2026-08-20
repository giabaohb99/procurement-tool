import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { buildSurveyCatalog } from '../helpers/survey-catalog'
import type { SurveyLine } from '../types/survey-detail'
import { SurveyLinesTable } from './survey-lines-table'

const CATALOG = buildSurveyCatalog([], ['Cái', 'Kg'])

const LINES: SurveyLine[] = [
  { id: 1, supplier_code: 'NCC-A', supplier_name: 'CÔNG TY A', note: 'ghi chú 1' },
  { id: 2, supplier_code: 'NCC-B', supplier_name: 'CÔNG TY B', note: 'ghi chú 2' },
]

function renderTable(props: Partial<Parameters<typeof SurveyLinesTable>[0]> = {}) {
  return render(
    <SurveyLinesTable
      table="supplier"
      lines={LINES}
      editable={false}
      approveEditable={false}
      invalid={new Set()}
      catalog={CATALOG}
      selected={new Set()}
      canFill={false}
      onSelectedChange={vi.fn()}
      onChangeLine={vi.fn()}
      onOpenLine={vi.fn()}
      onDuplicate={vi.fn()}
      onRemove={vi.fn()}
      {...props}
    />,
  )
}

function headerNames() {
  return within(screen.getAllByRole('rowgroup')[0])
    .getAllByRole('columnheader')
    .map((cell) => cell.textContent)
}

describe('SurveyLinesTable', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('mở lần đầu ở bảng rút gọn — cột phụ ẩn, cột cốt lõi vẫn hiện', () => {
    renderTable()
    const headers = headerNames()

    // Tiêu đề khai là 'NCC (viết tắt) *' nhưng bảng tách đuôi " *" ra thành dấu
    // sao đỏ (`shared/data-table/required-header.ts`), nên chữ đọc được không
    // còn dấu cách trước dấu sao.
    expect(headers).toContain('NCC (viết tắt)*')
    expect(headers).not.toContain('Chính sách công nợ')
  })

  it('bấm "Bảng đầy đủ" thì bung hết nhóm cột phụ', async () => {
    const user = userEvent.setup()
    renderTable()

    await user.click(screen.getByRole('button', { name: /Bảng đầy đủ/ }))

    expect(headerNames()).toContain('Chính sách công nợ')
  })

  /**
   * Đúng câu hỏi đã dẫn tới CR-103: trước đây chỉ có hai nấc rút gọn / đầy đủ,
   * muốn thêm MỘT cột là phải bung cả 27 cột.
   */
  it('bật lẻ được từng cột trong menu "Cột", không phải bung cả bảng', async () => {
    const user = userEvent.setup()
    renderTable()

    await user.click(screen.getByRole('button', { name: /Cột/ }))
    await user.click(screen.getByRole('button', { name: 'Chính sách công nợ' }))
    // Menu Radix che phần còn lại của trang bằng `aria-hidden` — đóng lại rồi
    // mới đọc được tiêu đề bảng.
    await user.keyboard('{Escape}')

    const headers = headerNames()
    expect(headers).toContain('Chính sách công nợ')
    // Các cột phụ khác vẫn ẩn — chỉ bật đúng cột vừa chọn.
    expect(headers).not.toContain('Công nghệ SX')
  })

  it('nhớ bố cục cột theo TỪNG bảng, hai bảng không giẫm lên nhau', async () => {
    const user = userEvent.setup()
    const { unmount } = renderTable()
    await user.click(screen.getByRole('button', { name: /Bảng đầy đủ/ }))
    unmount()

    expect(localStorage.getItem('erp.table.survey-supplier-lines')).toBeTruthy()
    expect(localStorage.getItem('erp.table.survey-product-lines')).toBeNull()
  })

  it('phiếu đọc-only thì không có cột tick chọn lẫn nút Chọn tất cả', () => {
    renderTable()

    expect(headerNames()).not.toContain('Chọn')
    expect(screen.queryByLabelText('Chọn tất cả dòng')).toBeNull()
  })

  it('sửa được thì có tick chọn từng dòng và tick chọn tất cả', () => {
    renderTable({ editable: true })

    expect(headerNames()).toContain('Chọn')
    expect(screen.getByLabelText('Chọn tất cả dòng')).toBeInTheDocument()
    expect(screen.getByLabelText('Chọn dòng 1')).toBeInTheDocument()
  })

  it('bảng sản phẩm cộng tổng thành tiền, bảng NCC thì không', () => {
    const { unmount } = renderTable()
    expect(screen.queryByText('Tổng thành tiền')).toBeNull()
    unmount()

    renderTable({ table: 'product' })
    expect(screen.getByText('Tổng thành tiền')).toBeInTheDocument()
  })
})
