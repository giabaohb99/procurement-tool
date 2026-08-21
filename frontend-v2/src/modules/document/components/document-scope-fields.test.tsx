import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { DocumentScopeFields, type PendingScope } from './document-scope-fields'

//  Ba pháp nhân là đủ để lộ lỗi: chọn tất cả phải ra ĐỦ BA dòng.
const PHAP_NHAN = [
  { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', code: 'DEGO' },
  { id: 2, name: 'CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL', code: 'IDA' },
  { id: 3, name: 'CÔNG TY TNHH SẢN XUẤT HÓA CHẤT ABA', code: 'ABA' },
]

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { items: PHAP_NHAN } }),
}))
//  Các CẶP (phòng ban × pháp nhân). Cố ý có **cùng một tên phòng ở hai pháp
//  nhân** — đó là ca mà khóa theo mỗi `department_id` sẽ dính hai dòng làm một.
const CAP_PHONG_BAN = [
  {
    department_id: 4,
    department_name: 'Phòng Kế toán',
    department_code: 'KT',
    company_id: 1,
    company_name: PHAP_NHAN[0].name,
  },
  {
    department_id: 4,
    department_name: 'Phòng Kế toán',
    department_code: 'KT',
    company_id: 2,
    company_name: PHAP_NHAN[1].name,
  },
]

vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: [] } }),
  //  Chiều PHÒNG BAN hỏi các CẶP của những pháp nhân đang tick. Ở đây trả cố
  //  định cả hai cặp — bài kiểm bên dưới tự tick pháp nhân rồi tick phòng ban.
  useDepartmentsByCompanies: () => ({ data: CAP_PHONG_BAN }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({ data: { items: [] } }),
}))
vi.mock('../hooks/use-document-scopes', () => ({
  useScopeOptions: () => ({
    data: {
      dims: [
        { value: 1, label: 'Pháp nhân' },
        { value: 2, label: 'Phòng ban' },
        { value: 3, label: 'Cá nhân' },
      ],
      modes: [
        { value: 1, label: 'Bao gồm' },
        { value: 2, label: 'Loại trừ' },
      ],
    },
  }),
}))

/**
 * Dựng đúng cách trang TẠO văn bản dùng: state ở ngoài, truyền xuống bằng props.
 *
 * Bọc `MemoryRouter` vì câu cảnh báo "pháp nhân chưa khai phòng ban" có một
 * `<Link>` chỉ sang màn Nhân sự → Phòng ban.
 */
function ManTao() {
  const [rows, setRows] = useState<PendingScope[]>([])
  return (
    <MemoryRouter>
      <DocumentScopeFields rows={rows} onChange={setRows} />
    </MemoryRouter>
  )
}

describe('DocumentScopeFields', () => {
  it('chọn tất cả pháp nhân thì ra ĐỦ số dòng, không rơi mất dòng nào', async () => {
    //  LỖI ĐÃ XẢY RA (20/08/2026): form thêm dòng gọi `onAdd` một lần cho MỖI
    //  pháp nhân, trong một vòng lặp đồng bộ. Mỗi lần gọi lại đọc `rows` từ
    //  closure — React chưa kịp dựng lại nên cả ba lần đều thấy mảng RỖNG, và
    //  lần cuối ghi đè hai lần trước. Chọn 13 pháp nhân chỉ còn 1 dòng.
    const user = userEvent.setup()
    render(<ManTao />)

    await user.click(screen.getByRole('button', { name: /Chọn pháp nhân/ }))
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: /Thêm dòng phạm vi/ }))

    for (const row of PHAP_NHAN) {
      expect(screen.getByText(row.name)).toBeInTheDocument()
    }
  })

  it('bỏ trống thì nói rõ mặc định áp cho toàn bộ pháp nhân ban hành', () => {
    render(<ManTao />)

    expect(screen.getByText(/mặc định áp cho toàn bộ pháp nhân ban hành/)).toBeInTheDocument()
  })

  it('thêm rồi thì băng «bỏ trống được» biến mất', async () => {
    const user = userEvent.setup()
    render(<ManTao />)

    await user.click(screen.getByRole('button', { name: /Chọn pháp nhân/ }))
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: /Thêm dòng phạm vi/ }))

    expect(
      screen.queryByText(/mặc định áp cho toàn bộ pháp nhân ban hành/),
    ).not.toBeInTheDocument()
  })

  it('thêm lại đúng pháp nhân đã có thì không đẻ dòng trùng', async () => {
    //  Backend trả "Dòng phạm vi này đã khai rồi", mà lỗi đó chỉ nổ SAU khi văn
    //  bản đã được tạo — lúc người dùng không còn ở màn này để sửa.
    const user = userEvent.setup()
    render(<ManTao />)

    for (let lan = 0; lan < 2; lan++) {
      await user.click(screen.getByRole('button', { name: /Chọn pháp nhân/ }))
      await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
      await user.keyboard('{Escape}')
      await user.click(screen.getByRole('button', { name: /Thêm dòng phạm vi/ }))
    }

    expect(screen.getAllByText(PHAP_NHAN[0].name)).toHaveLength(1)
  })

  it('chiều PHÒNG BAN: chọn nhiều pháp nhân rồi chọn nhiều phòng, mỗi cặp một dòng', async () => {
    //  Yêu cầu 21/08/2026: bản cũ bắt chọn ĐÚNG MỘT pháp nhân rồi một phòng ban,
    //  nên áp cùng một phòng cho năm công ty là năm lượt bấm y hệt nhau.
    //
    //  Ca canh ở đây là **cùng tên phòng ở hai pháp nhân**: khóa theo mỗi
    //  `department_id` thì hai cặp dính làm một và chỉ ra một dòng.
    const user = userEvent.setup()
    render(<ManTao />)

    //  Ô thứ hai là «Áp theo» (ô đầu là «Cách áp») — đổi chiều sang Phòng ban.
    await user.click(screen.getAllByRole('combobox')[1])
    await user.click(screen.getByRole('option', { name: 'Phòng ban' }))

    //  Tên KHỚP CHÍNH XÁC: ô phòng ban lúc chưa chọn gì mang chữ "Chọn pháp
    //  nhân trước…", regex lỏng sẽ vớ luôn cả hai nút.
    await user.click(screen.getByRole('button', { name: 'Chọn pháp nhân…' }))
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    await user.keyboard('{Escape}')

    await user.click(screen.getByRole('button', { name: 'Chọn phòng ban…' }))
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    await user.keyboard('{Escape}')

    await user.click(screen.getByRole('button', { name: /Thêm dòng phạm vi/ }))

    //  Hai dòng, mỗi dòng kèm ĐÚNG pháp nhân của nó — đọc trơ trọi "Phòng Kế
    //  toán" là câu chưa đủ nghĩa.
    expect(
      screen.getByText(`Phòng Kế toán — ${PHAP_NHAN[0].name}`),
    ).toBeInTheDocument()
    expect(
      screen.getByText(`Phòng Kế toán — ${PHAP_NHAN[1].name}`),
    ).toBeInTheDocument()
  })

  it('pháp nhân chưa khai phòng ban nào thì GỌI TÊN nó, không bỏ mặc ô trống', async () => {
    //  LỖI ĐÃ XẢY RA (21/08/2026): chọn SAM thì ô phòng ban rỗng và chỉ nói
    //  "Không tìm thấy mục nào" — người dùng đọc ra là hệ thống hỏng, trong khi
    //  sự thật là 11/13 pháp nhân chưa khai phòng ban nào.
    const user = userEvent.setup()
    render(<ManTao />)

    await user.click(screen.getAllByRole('combobox')[1])
    await user.click(screen.getByRole('option', { name: 'Phòng ban' }))

    //  PHAP_NHAN[2] (ABA) không có cặp nào trong `CAP_PHONG_BAN`.
    await user.click(screen.getByRole('button', { name: 'Chọn pháp nhân…' }))
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    await user.keyboard('{Escape}')

    //  Tên pháp nhân còn nằm trên chip đã chọn, nên khẳng định TRÊN CHÍNH câu
    //  cảnh báo chứ không phải trên cả trang.
    const canhBao = screen.getByText(/chưa khai\s+phòng ban nào nên không có gì để chọn/)
    expect(canhBao).toHaveTextContent(PHAP_NHAN[2].name)
    expect(screen.getByRole('link', { name: /Nhân sự → Phòng ban/ })).toHaveAttribute(
      'href',
      '/hr/departments',
    )
  })
})
