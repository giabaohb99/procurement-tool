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

/**
 * ─── BA TRẠNG THÁI RỖNG (D1–D3) ───
 *
 * Kiểu hỏng đắt nhất của giao diện phân quyền: **một bảng trống có ba nghĩa**
 * hoàn toàn khác nhau và người dùng không phân biệt được cái nào —
 *
 * | Thật ra là | Người dùng thấy |
 * |---|---|
 * | Không có dữ liệu | bảng rỗng |
 * | Có dữ liệu nhưng ngoài phạm vi | bảng rỗng |
 * | Không có quyền (403) | bảng rỗng |
 *
 * Đây là nguồn số 1 của câu "hệ thống lỗi rồi" mỗi lần khai quyền hẹp, và cũng
 * là lý do một lỗ phạm vi sống rất lâu: người bị lọc nhầm trông giống hệt người
 * không có dữ liệu. `DataTable` phải tách được ÍT NHẤT hai nhánh (rỗng / lỗi),
 * và trang gọi nó có trách nhiệm truyền câu chữ đúng cho nhánh còn lại.
 */
function buildState(props: Partial<Parameters<typeof DataTable<Row>>[0]>) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const { container } = render(
    <QueryClientProvider client={client}>
      <DataTable
        columns={[{ key: 'id', header: 'Mã', cell: (r) => r.id, width: 100 }]}
        rows={[]}
        getRowId={(r) => r.id}
        {...props}
      />
    </QueryClientProvider>,
  )
  return container
}

describe('DataTable — ba trạng thái rỗng', () => {
  it('không có dữ liệu và lỗi tải là HAI câu khác nhau', () => {
    const rong = buildState({}).textContent ?? ''
    const loi = buildState({ isError: true }).textContent ?? ''

    expect(rong).toContain('Không có dữ liệu.')
    expect(loi).toContain('Không tải được danh sách')
    //  Dùng chung một câu = mất luôn khả năng phân biệt, và đó chính là lỗ 09-C.
    expect(loi).not.toContain('Không có dữ liệu.')
  })

  it('đang tải KHÔNG được hiện câu "không có dữ liệu"', () => {
    //  Nháy câu đó trong lúc chờ mạng là người dùng đọc được "không có gì" rồi
    //  bỏ đi trước khi dữ liệu về.
    const container = buildState({ isLoading: true })
    expect(container.textContent).not.toContain('Không có dữ liệu.')
    expect(container.textContent).not.toContain('Không tải được danh sách')
  })

  it('lỗi thì KHÔNG vẽ dòng dữ liệu cũ lẫn vào', () => {
    const container = buildState({ isError: true, rows: ROWS })
    expect(container.textContent).not.toContain('Nguyễn Văn A')
  })

  it('trang truyền được câu riêng cho nhánh THIẾU QUYỀN', () => {
    //  Backend lọc phạm vi bằng cách trả DANH SÁCH RỖNG (không phải 403), nên
    //  chính trang mới biết nên nói gì. `DataTable` chỉ cần đừng nói dối thay nó.
    const container = buildState({
      emptyMessage: 'Không có chứng từ nào trong phạm vi dữ liệu của bạn.',
    })
    expect(container.textContent).toContain('trong phạm vi dữ liệu của bạn')
    expect(container.textContent).not.toContain('Không có dữ liệu.')
  })

  it('câu lỗi MẶC ĐỊNH có nhắc tới quyền, vì 403 trên GET không bật toast', () => {
    //  `core/api/http-client.ts` chỉ toast cho POST/PATCH/PUT/DELETE. Nghĩa là
    //  ô chữ này là NƠI DUY NHẤT người dùng biết mình vừa bị chặn.
    expect(buildState({ isError: true }).textContent).toMatch(/quyền/)
  })

  it('`rows` chưa về (undefined) khác hẳn `rows` rỗng', () => {
    //  `data?.items ?? []` ở tầng trang biến "chưa gọi xong" thành "rỗng" —
    //  bảng phải không tự bịa thêm câu nào khi chưa có mảng.
    expect(buildState({ rows: undefined }).textContent).not.toContain('Không có dữ liệu.')
  })
})
