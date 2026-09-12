import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { RecentPurchaseRequest } from '../api/procurement-dashboard-api'
import { RecentPurchaseRequests } from './recent-purchase-requests'

//  Hai biến này là chỗ bài kiểm bẻ lái: khổ màn và khóa duyệt.
let mobile = false
let canApprove = true

vi.mock('@/shared/hooks/use-mobile', () => ({
  useIsMobile: () => mobile,
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (_entity: string, action: string) => (action === 'approve' ? canApprove : true),
    canAny: () => true,
  }),
}))

vi.mock('../hooks/use-purchase-request', () => ({
  usePurchaseRequestAction: () => ({ mutate: vi.fn(), isPending: false }),
}))

const ROWS: RecentPurchaseRequest[] = [
  {
    id: 1,
    code: 'PYCDEMO08',
    requester: 'Nhân viên (Demo)',
    description: 'Mua thùng mẫu trưng bày',
    department: 'Phòng Marketing',
    date: '2026-07-02',
    status: 'submitted',
    total: 10_935_000,
  },
  {
    id: 2,
    code: 'PYCDEMO07',
    requester: 'Trưởng bộ phận (Demo)',
    description: 'Mua thùng bù tồn kho quý 2',
    department: 'Phòng Kho vận',
    date: '2026-06-10',
    status: 'completed',
    total: 38_826_000,
  },
]

beforeEach(() => {
  mobile = false
  canApprove = true
})

function renderList(rows: RecentPurchaseRequest[] = ROWS) {
  return render(
    <MemoryRouter>
      <RecentPurchaseRequests rows={rows} />
    </MemoryRouter>,
  )
}

describe('RecentPurchaseRequests', () => {
  it('dựng bảng ở khổ rộng', () => {
    renderList()

    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Mã phiếu' })).toBeInTheDocument()
  })

  /**
   * ⚠️ Bài quan trọng nhất của tệp này.
   *
   * Bảng rộng tự nhiên 687px trong khung 308px của khổ điện thoại, nên cột cuối
   * — hai nút *Duyệt / Trả lại* — nằm ngoài mép phải và không có gì báo là kéo
   * ngang được. Tức chức năng chính của khối ("duyệt nhanh tại chỗ") biến mất
   * trên điện thoại. Thẻ phải giữ được nó.
   */
  it('đổi sang thẻ ở khổ điện thoại mà KHÔNG mất nút duyệt nhanh', () => {
    mobile = true

    renderList()

    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Duyệt nhanh' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Trả lại để sửa' })).toBeInTheDocument()
  })

  //  Nút chỉ mọc ở phiếu ĐANG CHỜ DUYỆT — hai phiếu mà ra hai cặp nút nghĩa là
  //  thẻ đang mời người dùng duyệt lại một phiếu đã hoàn thành.
  it('chỉ bày nút duyệt ở phiếu đang chờ duyệt', () => {
    mobile = true

    renderList()

    expect(screen.getAllByRole('button', { name: 'Duyệt nhanh' })).toHaveLength(1)
  })

  it('thiếu khóa duyệt thì thẻ không có nút nào', () => {
    mobile = true
    canApprove = false

    renderList()

    expect(screen.queryByRole('button', { name: 'Duyệt nhanh' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Trả lại để sửa' })).not.toBeInTheDocument()
  })

  /**
   * Thẻ đặt NỘI DUNG lên dòng đầu, mã phiếu xuống dòng phụ — nhưng cả hai đều
   * phải còn, cùng với giá trị ĐẦY ĐỦ (người duyệt bấm dựa trên đúng con số
   * đó, nên không được rút gọn thành "10,9 tr").
   */
  it('thẻ giữ đủ nội dung, mã phiếu, người yêu cầu và giá trị đầy đủ', () => {
    mobile = true

    renderList()

    expect(screen.getByText('Mua thùng mẫu trưng bày')).toBeInTheDocument()
    expect(screen.getByText('PYCDEMO08')).toBeInTheDocument()
    expect(screen.getByText(/Nhân viên \(Demo\) · Phòng Marketing/)).toBeInTheDocument()
    expect(screen.getByText('10.935.000 đ')).toBeInTheDocument()
  })

  it('phiếu chưa có nội dung vẫn dựng được thẻ', () => {
    mobile = true

    renderList([{ ...ROWS[0], description: '' }])

    expect(screen.getByText('—')).toBeInTheDocument()
    expect(screen.getByText('PYCDEMO08')).toBeInTheDocument()
  })

  it('rỗng thì nói chưa có phiếu nào, ở cả hai khổ', () => {
    mobile = true

    renderList([])

    expect(screen.getByText('Chưa có yêu cầu mua hàng nào.')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })
})
