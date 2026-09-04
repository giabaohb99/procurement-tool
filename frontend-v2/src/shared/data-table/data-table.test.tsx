import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { DataTable } from './data-table'
import type { DataTableColumn } from './types'

interface Row {
  id: number
  name: string
  note: string
}

const ROWS: Row[] = [{ id: 1, name: 'Nguyễn Văn A', note: 'ghi chú rất dài '.repeat(20) }]

function build(columns: DataTableColumn<Row>[], storageKey?: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const { container } = render(
    <QueryClientProvider client={client}>
      <DataTable
        columns={columns}
        rows={ROWS}
        getRowId={(r) => r.id}
        storageKey={storageKey}
      />
    </QueryClientProvider>,
  )
  return container.querySelector('table') as HTMLTableElement
}

beforeEach(() => {
  //  Bố cục cột nhớ trong `localStorage`; sót lại giữa hai bài là bề rộng của
  //  bài trước đè lên bài sau.
  localStorage.clear()
})

/**
 * SÀN bề rộng của bảng.
 *
 * ⚠️ LỖI ĐÃ XẢY RA (04/09/2026, màn Đơn nghỉ phép trong khung 940px): không có
 * sàn thì `table-fixed` + `w-full` co MỌI cột lại theo tỷ lệ, cột khai `wrap`
 * bị bóp còn vài chục pixel và chữ trong đó rớt xuống ba mươi dòng — một hàng
 * cao 600px, còn thẻ chứa bảng thì đội cả trang trượt ngang.
 */
describe('DataTable — sàn bề rộng', () => {
  it('sàn bằng TỔNG bề rộng các cột đang hiện', () => {
    const table = build([
      { key: 'id', header: 'Mã', cell: (r) => r.id, width: 100 },
      { key: 'name', header: 'Tên', cell: (r) => r.name, width: 250 },
    ])
    expect(table.style.minWidth).toBe('350px')
  })

  it('cột KHÔNG khai bề rộng vẫn góp sàn của chính nó, không tụt về 0', () => {
    //  Đây là chỗ `min-w-max` của Tailwind bó tay: bảng `table-fixed` chỉ tính
    //  `max-content` từ cột CÓ khai bề rộng, nên cột để trống biến mất hẳn.
    const table = build([
      { key: 'id', header: 'Mã', cell: (r) => r.id, width: 100 },
      { key: 'note', header: 'Ghi chú', cell: (r) => r.note, wrap: true, minWidth: 180 },
    ])
    expect(table.style.minWidth).toBe('280px')
  })

  it('cột không khai gì cả thì lấy sàn mặc định', () => {
    const table = build([{ key: 'name', header: 'Tên', cell: (r) => r.name }])
    expect(table.style.minWidth).toBe('64px')
  })

  it('cột ĐANG ẨN không tính vào sàn — bảng phải co lại theo', () => {
    //  Ẩn bớt cột mà sàn giữ nguyên thì bảng vẫn rộng như cũ, chừa một khoảng
    //  trắng bên phải trong khung viền (đúng lỗi CR-102 của `LinesTable`).
    const table = build([
      { key: 'id', header: 'Mã', cell: (r) => r.id, width: 100 },
      { key: 'name', header: 'Tên', cell: (r) => r.name, width: 250, defaultHidden: true },
    ])
    expect(table.style.minWidth).toBe('100px')
  })

  it('lấy bề rộng NGƯỜI DÙNG ĐÃ KÉO, không lấy số khai trong code', () => {
    //  Kéo cột rộng ra rồi mà sàn vẫn tính theo số cũ thì bảng lại bị bóp đúng
    //  bằng phần vừa kéo thêm — công kéo giãn đổ sông.
    localStorage.setItem(
      'erp.table.test.leave-types',
      JSON.stringify({
        hiddenColumns: [],
        columnWidths: { id: 400 },
        columnOrder: [],
        pinnedColumns: [],
        columnColors: {},
      }),
    )
    const table = build(
      [{ key: 'id', header: 'Mã', cell: (r) => r.id, width: 100 }],
      'test.leave-types',
    )
    expect(table.style.minWidth).toBe('400px')
  })

  it('ẩn HẾT cột thì sàn về 0, không nổ', () => {
    const table = build([
      { key: 'id', header: 'Mã', cell: (r) => r.id, width: 100, defaultHidden: true },
    ])
    expect(table.style.minWidth).toBe('0px')
  })

  it('KHÔNG đặt bề rộng cứng — bảng vẫn giãn hết khung khi màn rộng', () => {
    const table = build([{ key: 'id', header: 'Mã', cell: (r) => r.id, width: 100 }])
    expect(table.style.width).toBe('')
    expect(table.className).toContain('table-fixed')
  })
})
