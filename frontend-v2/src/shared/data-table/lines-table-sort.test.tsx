import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { beforeEach, describe, expect, it } from 'vitest'

import { LinesTable } from './lines-table'
import type { LinesTableColumn } from './types'

/**
 * duoc-CR-744 — bảng DÒNG CHỨNG TỪ (`LinesTable`) trước đây không sắp xếp được cột
 * nào: chi tiết YCMH, YCBG, ĐMH, Phiếu khảo sát bấm tiêu đề không có gì xảy ra.
 */
interface Row {
  id?: number
  name: string
  price: string | number | null
}

const COLUMNS: LinesTableColumn[] = [
  { key: 'no', header: 'No.' },
  { key: 'name', header: 'Tên' },
  { key: 'price', header: 'Giá', sortDescFirst: true },
  { key: 'action', header: 'Thao tác' },
]

const ROWS: Row[] = [
  { id: 1, name: 'Chai', price: '12.5' },
  { id: 2, name: 'Ảnh', price: '' },
  { id: 3, name: 'Bao', price: '12.25' },
  { id: 4, name: 'an', price: 100 },
]

function header(text: string) {
  return screen.getByText(text, { selector: 'thead span' })
}

/** Bảng SỬA ĐƯỢC: ô Tên là ô nhập, sửa theo CHỈ SỐ GỐC như mọi bảng dòng thật. */
function EditableTable({ initial }: { initial: Row[] }) {
  const [rows, setRows] = useState(initial)
  return (
    <LinesTable<Row>
      columns={COLUMNS}
      rows={rows}
      storageKey="test.lines-table-sort"
      rowKey={(row, index) => row.id ?? `new-${index}`}
      title="Dòng"
      emptyMessage="Trống"
      actions={
        <button type="button" onClick={() => setRows((prev) => [...prev, { name: 'Mới', price: 1 }])}>
          Thêm dòng
        </button>
      }
      renderCell={(key, row, index) => {
        if (key === 'no') return index + 1
        if (key === 'name') {
          return (
            <input
              aria-label={`Tên dòng ${index + 1}`}
              value={row.name}
              onChange={(event) =>
                setRows((prev) => prev.map((r, i) => (i === index ? { ...r, name: event.target.value } : r)))
              }
            />
          )
        }
        if (key === 'price') return String(row.price ?? '')
        return <button type="button">Xóa</button>
      }}
    />
  )
}

function bodyNames() {
  return screen
    .getAllByRole('row')
    .slice(1)
    .map((row) => (within(row).getByRole('textbox') as HTMLInputElement).value)
}

beforeEach(() => localStorage.clear())

describe('LinesTable sorting', () => {
  it('cycles asc → desc → original order when a data header is clicked', async () => {
    const user = userEvent.setup()
    render(<EditableTable initial={ROWS} />)

    await user.click(header('Tên'))
    expect(bodyNames()).toEqual(['an', 'Ảnh', 'Bao', 'Chai'])
    await user.click(header('Tên'))
    expect(bodyNames()).toEqual(['Chai', 'Bao', 'Ảnh', 'an'])
    await user.click(header('Tên'))
    expect(bodyNames()).toEqual(['Chai', 'Ảnh', 'Bao', 'an'])
  })

  it('starts with desc on sortDescFirst columns and keeps the blank price last', async () => {
    const user = userEvent.setup()
    render(<EditableTable initial={ROWS} />)

    await user.click(header('Giá'))
    expect(bodyNames()).toEqual(['an', 'Chai', 'Bao', 'Ảnh'])
    await user.click(header('Giá'))
    expect(bodyNames()).toEqual(['Bao', 'Chai', 'an', 'Ảnh'])
  })

  it('does not make the No. and action headers clickable — they have no value to sort by', async () => {
    const user = userEvent.setup()
    render(<EditableTable initial={ROWS} />)

    await user.click(header('No.'))
    await user.click(header('Thao tác'))
    expect(bodyNames()).toEqual(['Chai', 'Ảnh', 'Bao', 'an'])
  })

  it('edits the RIGHT row after sorting — renderCell still gets the original index', async () => {
    const user = userEvent.setup()
    render(<EditableTable initial={ROWS} />)

    await user.click(header('Tên'))
    //  Sau khi xếp, dòng đầu trên màn là "an" (chỉ số gốc 3). Sửa nhầm chỉ số là đổi tên "Chai".
    const firstInput = within(screen.getAllByRole('row')[1]).getByRole('textbox')
    await user.type(firstInput, 'x')
    expect(bodyNames()).toEqual(['anx', 'Ảnh', 'Bao', 'Chai'])
  })

  it('does not move a row while the user is typing in the sorted column', async () => {
    const user = userEvent.setup()
    render(<EditableTable initial={ROWS} />)

    await user.click(header('Tên'))
    const firstInput = within(screen.getAllByRole('row')[1]).getByRole('textbox')
    //  "zzz" lẽ ra xếp cuối, nhưng thứ tự đã chốt lúc bấm: dòng đứng yên dưới tay người gõ.
    await user.clear(firstInput)
    await user.type(firstInput, 'zzz')
    expect(bodyNames()[0]).toBe('zzz')
  })

  it('appends rows added after sorting at the end instead of dropping them', async () => {
    const user = userEvent.setup()
    render(<EditableTable initial={ROWS} />)

    await user.click(header('Tên'))
    await user.click(screen.getByRole('button', { name: 'Thêm dòng' }))
    expect(bodyNames()).toEqual(['an', 'Ảnh', 'Bao', 'Chai', 'Mới'])
  })

  it('renders an empty table without crashing when sorted', async () => {
    const user = userEvent.setup()
    render(<EditableTable initial={[]} />)
    //  Không dòng nào mang giá trị -> cột không bấm được, bấm vào cũng không vỡ.
    await user.click(header('Tên'))
    expect(screen.getByText('Trống')).toBeInTheDocument()
  })
})
