import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
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
vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: [] } }),
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

/** Dựng đúng cách trang TẠO văn bản dùng: state ở ngoài, truyền xuống bằng props. */
function ManTao() {
  const [rows, setRows] = useState<PendingScope[]>([])
  return <DocumentScopeFields rows={rows} onChange={setRows} />
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
})
