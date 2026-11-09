import { render, screen, within } from '@testing-library/react'
import { useState } from 'react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { SurveyRequestLine } from '../types/survey-request-detail'
import { SurveyRequestLinesTable } from './survey-request-lines-table'

// Bảng này nói về CÁCH HIỆN dòng cần khảo sát, không nói về mạng — cắt hết lượt
// gọi danh mục (ĐVT / phân loại).
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestUnits: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestItemGroups: () => ({ data: { items: [] }, isLoading: false }),
}))

const LINES: SurveyRequestLine[] = [
  {
    id: 5,
    item_group: 'Bao bì',
    requirement_detail: 'Thùng carton 5 lớp, sóng BC, 400x300x250mm, in flexo 2 màu',
    other_requirement: '',
    request_qty: 12000,
    uom: 'Cái',
    proposed_price: 9500,
    received_date: '2026-03-04',
    result_due_date: '2026-03-18',
    result_date: '2026-03-16',
    assignee: 'DEMO_PURCHASER',
    assignee_name: 'Nhân viên Thu mua (Demo)',
    pr_id: 0,
    pr_code: '',
    is_completed: false,
    line_status: '',
    no_option: false,
    option_count: 2,
    has_chosen: true,
    progress_state: 'Đã chọn phương án',
    progress_tone: 'ok',
  },
]

function renderTable(
  props: Partial<Parameters<typeof SurveyRequestLinesTable>[0]> = {},
) {
  return render(
    <SurveyRequestLinesTable
      lines={LINES}
      editing={false}
      showNstmColumns
      showStatus
      canAssignNstm={false}
      purchasers={[]}
      onChange={vi.fn()}
      onOpenDetail={vi.fn()}
      onAssigneeChange={vi.fn()}
      {...props}
    />,
  )
}

describe('SurveyRequestLinesTable', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('khổ rộng vẫn là BẢNG — thẻ chỉ thay ở khổ hẹp', () => {
    const { container } = renderTable()

    expect(container.querySelector('table')).not.toBeNull()
    expect(screen.getByText('Chi tiết thông số')).toBeInTheDocument()
  })
})

/**
 * Khổ điện thoại — bảng đổi sang THẺ, xem `SurveyRequestLineCard`.
 *
 * Riêng ba cột ghim (*No. · Phân loại · Chi tiết thông số*) đã 548px, rộng hơn cả
 * khung 322px của máy 390px — tức ở khổ đó KHÔNG tồn tại vị trí cuộn nào nhìn
 * thấy được *SL dự kiến* hay *Trạng thái*: cột ghim luôn đứng chắn bên trái.
 *
 * `setup.ts` cố định `matchMedia` ở khổ desktop cho cả bộ test, nên khổ hẹp phải
 * nói rõ ra ngay tại đây.
 */
describe('SurveyRequestLinesTable — khổ điện thoại', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it('bày SL, GIÁ ĐỀ XUẤT và TRẠNG THÁI — ba cột bị cột ghim chắn mất', () => {
    const { container } = renderTable()

    expect(container.querySelector('table')).toBeNull()
    // Phân loại · SL · giá đứng cùng một hàng chữ, mỗi mẩu một `<span>`.
    expect(screen.getByText('12.000 Cái')).toBeInTheDocument()
    expect(screen.getByText('9.500 đ')).toBeInTheDocument()
    expect(screen.getByText('Đã chọn phương án')).toBeInTheDocument()
  })

  it('cả thẻ là một nút mở hộp chi tiết — mọi ô vẫn sửa được ở đó', async () => {
    const onOpenDetail = vi.fn()
    renderTable({ onOpenDetail })

    await userEvent.click(screen.getByRole('button', { name: /Thùng carton 5 lớp/ }))
    expect(onOpenDetail).toHaveBeenCalledWith(0)
  })

  it('đánh dấu dòng còn ô bắt buộc chưa điền — thẻ không có ô nào để tô đỏ', () => {
    //  Bấm *Gửi duyệt* mà còn ô trống thì bảng tô đỏ ô Phân loại. Không có dấu
    //  này thì người dùng bị chặn mà KHÔNG có cách nào biết dòng nào thiếu.
    renderTable({ invalid: new Set(['line-0-item_group']) })

    expect(screen.getByText('Thiếu ô')).toBeInTheDocument()
  })

  it('không đánh dấu khi chưa ai bấm Gửi duyệt', () => {
    renderTable()

    expect(screen.queryByText('Thiếu ô')).toBeNull()
  })

  it('giấu cột nội bộ của thu mua khi người xem là người YÊU CẦU', () => {
    //  `showNstmColumns` là chốt che NSTM và ngày tiếp nhận. Thẻ phải theo đúng
    //  luật của bảng, không thì dời sang khổ hẹp là rò dữ liệu nội bộ.
    renderTable({ showNstmColumns: false })

    expect(screen.queryByText(/Nhân viên Thu mua \(Demo\)/)).toBeNull()
    expect(screen.queryByText(/Nhận 04\/03\/2026/)).toBeNull()
    // Hạn trả KQ thì người YC vẫn thấy — nó là cam kết với họ.
    expect(screen.getByText(/Hạn KQ 18\/03\/2026/)).toBeInTheDocument()
  })

  it('chỉ hiện nút Nhân đôi / Xóa khi phiếu còn sửa được', () => {
    const { unmount } = renderTable({ editing: false })
    expect(screen.queryByRole('button', { name: /Xóa dòng/ })).toBeNull()
    unmount()

    renderTable({ editing: true })
    expect(screen.getByRole('button', { name: /Xóa dòng 1/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Nhân đôi dòng 1/ })).toBeInTheDocument()
  })
})

/**
 * duoc-CR-737 — *Xóa đã chọn (n)* đứng ở góc phải tiêu đề THẺ cạnh *Thêm dòng* như bản
 * v1, không còn ở thanh tiêu đề của `LinesTable`. Trang xếp khung qua `renderFrame`.
 */
describe('SurveyRequestLinesTable — Xóa đã chọn ở tiêu đề thẻ (duoc-CR-737)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  const second: SurveyRequestLine = { ...LINES[0], id: 6, requirement_detail: 'Băng keo trong 48mm' }

  it('moves the bulk-delete button into the header slot and still drops ticked lines', async () => {
    const onChange = vi.fn()
    const onLineRemoved = vi.fn()
    renderTable({
      lines: [LINES[0], second],
      editing: true,
      bulkRemovable: true,
      onChange,
      onLineRemoved,
      renderFrame: ({ headerActions, body }) => (
        <>
          <div role="toolbar" aria-label="Tiêu đề thẻ">
            {headerActions}
          </div>
          <div role="region" aria-label="Thân thẻ">
            {body}
          </div>
        </>
      ),
    })

    const header = screen.getByRole('toolbar', { name: 'Tiêu đề thẻ' })
    const body = screen.getByRole('region', { name: 'Thân thẻ' })
    expect(within(header).queryByRole('button')).toBeNull()

    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn dòng 2' }))
    expect(within(body).queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()
    await userEvent.click(within(header).getByRole('button', { name: 'Xóa đã chọn (1)' }))
    //  duoc-CR-741: hộp hỏi nói đúng câu v1 và nút đồng ý là "Đồng ý" như v1.
    const dialog = screen.getByRole('alertdialog', { name: 'Xác nhận' })
    expect(dialog).toHaveTextContent(
      'Xóa 1 dòng đã chọn? Dòng bỏ khỏi phiếu ngay trên màn hình, bấm Lưu mới ghi xuống.',
    )
    expect(within(dialog).getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))

    expect(onChange).toHaveBeenCalledWith([LINES[0]])
    expect(onLineRemoved).toHaveBeenCalledWith(1)
  })
})

/** duoc-CR-741 — gợi ý nút biểu tượng ở khổ rộng lấy nguyên chữ bản v1. */
describe('SurveyRequestLinesTable — gợi ý nút theo v1 (duoc-CR-741)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('labels the row icons Chi tiết / hình ảnh · Nhân đôi · Xóa like v1, and they act on the right row', async () => {
    const onChange = vi.fn()
    const onOpenDetail = vi.fn()
    const second: SurveyRequestLine = { ...LINES[0], id: 6, requirement_detail: 'Băng keo trong 48mm' }
    renderTable({ lines: [LINES[0], second], editing: true, onChange, onOpenDetail })

    expect(screen.getByRole('button', { name: 'Chi tiết / hình ảnh dòng 2' })).toHaveAttribute(
      'title',
      'Chi tiết / hình ảnh',
    )
    expect(screen.getByRole('button', { name: 'Nhân đôi dòng 2' })).toHaveAttribute('title', 'Nhân đôi')
    expect(screen.getByRole('button', { name: 'Xóa dòng 2' })).toHaveAttribute('title', 'Xóa')
    expect(screen.queryByTitle('Nhân bản dòng')).toBeNull()
    expect(screen.queryByTitle('Chi tiết dòng')).toBeNull()

    await userEvent.click(screen.getByRole('button', { name: 'Chi tiết / hình ảnh dòng 2' }))
    expect(onOpenDetail).toHaveBeenCalledWith(1)
    await userEvent.click(screen.getByRole('button', { name: 'Xóa dòng 2' }))
    expect(onChange).toHaveBeenLastCalledWith([LINES[0]])
  })

  it('hides Nhân đôi / Xóa on a read-only sheet but keeps Chi tiết / hình ảnh', () => {
    renderTable({ editing: false })

    expect(screen.getByRole('button', { name: 'Chi tiết / hình ảnh dòng 1' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Nhân đôi/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Xóa dòng/ })).toBeNull()
  })
})

/**
 * Rà mã duoc-CR-741: dòng chưa lưu khóa tick theo chỉ số (`new-${index}`). Tick dòng 4 rồi
 * Nhân đôi dòng 1 thì dấu tick trôi sang dòng 3 cũ, *Xóa đã chọn* xóa nhầm. Nay chèn / bỏ một
 * dòng là bỏ hết dấu tick.
 */
describe('SurveyRequestLinesTable — dấu tick không trôi khi chèn / bỏ dòng', () => {
  beforeEach(() => localStorage.clear())

  const unsaved: SurveyRequestLine[] = ['A', 'B', 'C', 'D'].map((code) => ({
    ...LINES[0],
    id: 0,
    requirement_detail: `Hàng ${code}`,
  }))

  function StatefulTable() {
    const [lines, setLines] = useState(unsaved)
    return (
      <SurveyRequestLinesTable
        lines={lines}
        editing
        bulkRemovable
        showNstmColumns={false}
        showStatus={false}
        canAssignNstm={false}
        purchasers={[]}
        onChange={setLines}
        onOpenDetail={vi.fn()}
        onAssigneeChange={vi.fn()}
      />
    )
  }

  it('duplicating line 1 drops the tick on line 4 instead of moving it to another line', async () => {
    render(<StatefulTable />)
    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn dòng 4' }))
    expect(screen.getByRole('button', { name: 'Xóa đã chọn (1)' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Nhân đôi dòng 1' }))

    expect(screen.getAllByRole('checkbox', { name: /^Chọn dòng/ })).toHaveLength(5)
    expect(screen.queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()
  })

  it('deleting one line drops the ticks too', async () => {
    render(<StatefulTable />)
    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn dòng 4' }))
    await userEvent.click(screen.getByRole('button', { name: 'Xóa dòng 1' }))

    expect(screen.getAllByRole('checkbox', { name: /^Chọn dòng/ })).toHaveLength(3)
    expect(screen.queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()
  })
})
