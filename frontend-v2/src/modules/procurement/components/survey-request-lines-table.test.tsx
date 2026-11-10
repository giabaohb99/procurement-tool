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

/**
 * duoc-CR-744 — bấm tiêu đề cột xếp dòng khảo sát theo đúng thứ ô ĐANG HIỆN: ô NSTM hiện
 * TÊN tra từ mã, cột Trạng thái xếp theo dòng đời của nhãn tiến độ (không theo chữ cái),
 * ngày xếp theo ISO chứ không theo chữ dd/mm/yyyy trong ô.
 */
describe('SurveyRequestLinesTable — xếp cột khi bấm tiêu đề (duoc-CR-744)', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  const base = LINES[0]
  const SORT_LINES: SurveyRequestLine[] = [
    {
      ...base,
      id: 1,
      requirement_detail: 'Gamma',
      item_group: 'Bao bì',
      request_qty: 20,
      proposed_price: 9500,
      received_date: '2026-03-04',
      result_due_date: '2026-03-18',
      uom: 'Cái',
      assignee: 'U2',
      assignee_name: '',
      progress_state: 'Đã chọn phương án',
    },
    {
      ...base,
      id: 2,
      requirement_detail: 'Alpha',
      item_group: 'Hóa chất',
      request_qty: 3,
      proposed_price: 100,
      received_date: '',
      result_due_date: '2026-01-20',
      uom: 'Kg',
      assignee: 'U1',
      assignee_name: 'Trần A',
      progress_state: 'Chưa tiếp nhận',
    },
    {
      ...base,
      id: 3,
      requirement_detail: 'Beta',
      item_group: 'Dịch vụ',
      request_qty: 100,
      proposed_price: 50,
      received_date: '2026-02-01',
      result_due_date: '2026-12-01',
      uom: 'Bộ',
      assignee: '',
      assignee_name: '',
      progress_state: 'Đang khảo sát',
    },
  ]
  const PURCHASERS = [{ code: 'U2', name: 'Lê Zed' }]

  async function clickHeader(name: RegExp) {
    const header = screen.getByRole('columnheader', { name })
    const clickArea = header.firstElementChild
    if (!clickArea) throw new Error('tiêu đề cột không có vùng bấm')
    await userEvent.click(clickArea)
  }

  /** Chữ trong cột `name` theo thứ tự dòng đang hiện (bỏ hàng tiêu đề). */
  function columnTexts(name: RegExp): string[] {
    const index = screen.getAllByRole('columnheader').findIndex((h) => name.test(h.textContent ?? ''))
    return screen
      .getAllByRole('row')
      .slice(1)
      .map((row) => within(row).getAllByRole('cell')[index]?.textContent ?? '')
  }

  const order = () => columnTexts(/^Chi tiết thông số/)

  it('sorts by the specification text asc, then desc, then back to the original order', async () => {
    renderTable({ lines: SORT_LINES, purchasers: PURCHASERS })
    expect(order()).toEqual(['Gamma', 'Alpha', 'Beta'])

    await clickHeader(/^Chi tiết thông số/)
    expect(order()).toEqual(['Alpha', 'Beta', 'Gamma'])
    await clickHeader(/^Chi tiết thông số/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])
    await clickHeader(/^Chi tiết thông số/)
    expect(order()).toEqual(['Gamma', 'Alpha', 'Beta'])
  })

  it('sorts SL dự kiến and Giá đề xuất by number, not by text ("100" < "20" < "3")', async () => {
    renderTable({ lines: SORT_LINES, purchasers: PURCHASERS })
    await clickHeader(/^SL dự kiến/)
    expect(order()).toEqual(['Alpha', 'Gamma', 'Beta'])
    await clickHeader(/^Giá đề xuất/)
    expect(order()).toEqual(['Beta', 'Alpha', 'Gamma'])
  })

  it('sorts the assignee by the displayed NAME (looked up from the code) and keeps the unassigned line last', async () => {
    renderTable({ lines: SORT_LINES, purchasers: PURCHASERS })
    //  U2 hiện "Lê Zed" (tra từ danh sách), U1 hiện "Trần A" (assignee_name); theo MÃ sẽ ra U1 trước U2.
    await clickHeader(/^Nhân sự phụ trách/)
    expect(order()).toEqual(['Gamma', 'Alpha', 'Beta'])
    await clickHeader(/^Nhân sự phụ trách/)
    expect(order()).toEqual(['Alpha', 'Gamma', 'Beta'])
  })

  it('sorts Trạng thái along the line life cycle, not alphabetically', async () => {
    renderTable({ lines: SORT_LINES, purchasers: PURCHASERS })
    //  Dòng đời: Chưa tiếp nhận < Đang khảo sát < Đã chọn phương án. Theo chữ cái sẽ ra
    //  Chưa tiếp nhận < Đã chọn phương án < Đang khảo sát.
    await clickHeader(/^Trạng thái/)
    expect(order()).toEqual(['Alpha', 'Beta', 'Gamma'])
    await clickHeader(/^Trạng thái/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])
  })

  it('sorts dates by the ISO value and drops the blank received date to the end in both directions', async () => {
    renderTable({ lines: SORT_LINES, purchasers: PURCHASERS })
    await clickHeader(/^Ngày tiếp nhận/)
    expect(order()).toEqual(['Beta', 'Gamma', 'Alpha'])
    await clickHeader(/^Ngày tiếp nhận/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])

    //  18/03/2026 · 20/01/2026 · 01/12/2026: so chữ dd/mm sẽ đặt 01/12 đầu tiên.
    await clickHeader(/^Ngày YC trả KQ/)
    expect(order()).toEqual(['Alpha', 'Gamma', 'Beta'])
  })

  it('does not make the No. and Thao tác headers clickable', async () => {
    renderTable({ lines: SORT_LINES, purchasers: PURCHASERS })
    await clickHeader(/^Chi tiết thông số/)
    await clickHeader(/^Chi tiết thông số/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])

    await clickHeader(/^No\./)
    await clickHeader(/^Thao tác/)
    expect(order()).toEqual(['Gamma', 'Beta', 'Alpha'])
  })

  it('hides the internal columns, and with them their sort, from the requester', () => {
    renderTable({ lines: SORT_LINES, purchasers: PURCHASERS, showNstmColumns: false })
    expect(screen.queryByRole('columnheader', { name: /^Nhân sự phụ trách/ })).toBeNull()
    expect(screen.queryByRole('columnheader', { name: /^Ngày tiếp nhận/ })).toBeNull()
  })

  it('does not crash on an empty list', async () => {
    renderTable({ lines: [] })
    await clickHeader(/^Chi tiết thông số/)
    expect(screen.getByText(/Chưa có dòng nào/)).toBeInTheDocument()
  })
})
