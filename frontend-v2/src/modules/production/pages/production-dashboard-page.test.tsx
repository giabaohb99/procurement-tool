import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ProductionDashboardPage } from './production-dashboard-page'
import type { ProductionOverview } from '../api/production-dashboard-api'

//  Quyền: bài này xoay quanh việc ẩn/hiện theo quyền nên `can` phải đổi được
//  giữa các test.
let granted: string[] = []

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string) => granted.includes(entity),
    canAccess: () => true,
  }),
}))

//  Chặn ở tầng HOOK dữ liệu: trang chỉ đọc một gói duy nhất, và điều cần khẳng
//  định là nó xử lý ĐÚNG gói thiếu khóa mà backend cố tình trả về.
let overview: ProductionOverview | undefined

vi.mock('../hooks/use-production-dashboard', () => ({
  useProductionDashboard: () => ({ data: overview, isLoading: false }),
}))

function emptyOverview(): ProductionOverview {
  return {
    kpi: {},
    product_groups: [],
    expiring_contracts: [],
    can: { supplier: false, product: false, unit: false, item_group: false, contract: false },
  }
}

function build() {
  return render(
    <MemoryRouter>
      <ProductionDashboardPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  granted = []
  overview = emptyOverview()
})

describe('ProductionDashboardPage — gác theo quyền', () => {
  it('shows the blocked panel when the user may read none of the catalogs', () => {
    build()

    expect(screen.getByText(/không có quyền xem danh mục nào/i)).toBeInTheDocument()
    //  Không được để lọt lối tắt nào: bấm vào là ăn 403 rồi bị đá về.
    expect(screen.queryByText('Nhà cung cấp')).not.toBeInTheDocument()
    expect(screen.queryByText('Hợp đồng')).not.toBeInTheDocument()
  })

  it('opens the page for a user who only holds ONE small catalog', () => {
    //  Người giữ mỗi danh mục ĐVT vẫn phải vào được trang — gác cả trang theo
    //  `supplier.read` như bản cũ là khóa nhầm họ ra ngoài.
    granted = ['unit']
    overview = { ...emptyOverview(), kpi: { unit_total: 12 } }
    build()

    expect(screen.queryByText(/không có quyền xem danh mục nào/i)).not.toBeInTheDocument()
    //  Hai chỗ mang tên danh mục: thẻ KPI và ô lối tắt.
    expect(screen.getAllByText('Đơn vị tính')).toHaveLength(2)
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('hides every block of a catalog the user cannot read', () => {
    granted = ['supplier']
    overview = {
      ...emptyOverview(),
      kpi: { supplier_goods: 5, supplier_transport: 2 },
    }
    build()

    expect(screen.getByText('Nhà cung cấp hàng hóa')).toBeInTheDocument()
    expect(screen.getByText('Đơn vị vận chuyển')).toBeInTheDocument()
    //  Thẻ KPI, biểu đồ và lối tắt của các danh mục khác đều phải biến mất.
    expect(screen.queryByText('Sản phẩm & Vật tư')).not.toBeInTheDocument()
    expect(screen.queryByText('Sản phẩm theo phân loại')).not.toBeInTheDocument()
    expect(screen.queryByText('Hợp đồng sắp hết hạn')).not.toBeInTheDocument()
    expect(screen.queryByText('Phân loại VTBB')).not.toBeInTheDocument()
  })

  it('lists a shortcut for each catalog the user may read, and no others', () => {
    granted = ['product', 'contract']
    build()

    expect(screen.getByRole('link', { name: /Sản phẩm & Vật tư/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Hợp đồng/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Nhà cung cấp/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Đơn vị tính/ })).not.toBeInTheDocument()
  })
})

describe('ProductionDashboardPage — số liệu thiếu khóa', () => {
  it('reads a missing kpi key as 0 instead of blowing up', () => {
    //  Backend BỎ HẲN khóa khi gác khối, và quyền phía giao diện có thể tươi hơn
    //  gói dữ liệu đang nằm trong cache — hai bên lệch nhau là chuyện thường.
    granted = ['product']
    overview = { ...emptyOverview(), kpi: {} }
    build()

    expect(screen.getAllByText('Sản phẩm & Vật tư')).toHaveLength(2)
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('Toàn bộ đang dùng')).toBeInTheDocument()
  })

  it('says how many products are retired only when there are any', () => {
    granted = ['product']
    overview = { ...emptyOverview(), kpi: { product_total: 40, product_inactive: 3 } }
    build()

    expect(screen.getByText('3 mã đã ngừng dùng')).toBeInTheDocument()
  })

  it('shows the empty label when the catalog has no product at all', () => {
    granted = ['product']
    overview = { ...emptyOverview(), kpi: { product_total: 0 }, product_groups: [] }
    build()

    expect(screen.getByText('Chưa có sản phẩm nào trong danh mục.')).toBeInTheDocument()
  })
})

describe('ProductionDashboardPage — hợp đồng sắp hết hạn', () => {
  const rows: ProductionOverview['expiring_contracts'] = [
    {
      id: 7,
      code: 'HD00007',
      title: 'Hợp đồng nguyên tắc cung cấp thùng carton',
      party_name: 'Công ty TNHH Bao bì Phương Nam',
      end_date: '2026-09-10',
    },
    { id: 9, code: 'HD00009', title: '', party_name: 'Nhà xe Ba Miền', end_date: '2026-09-20' },
  ]

  it('links each row to the contract detail screen', () => {
    granted = ['contract']
    overview = { ...emptyOverview(), expiring_contracts: rows }
    build()

    expect(screen.getByText('HD00007').closest('a')).toHaveAttribute(
      'href',
      '/production/contracts/7',
    )
  })

  it('falls back to the party name when the contract has no title', () => {
    //  `title` rỗng là chuyện thường trên dữ liệu nhập từ Excel — để trống ô thì
    //  dòng đó chỉ còn mã, không ai đọc ra là hợp đồng của ai.
    granted = ['contract']
    overview = { ...emptyOverview(), expiring_contracts: rows }
    build()

    expect(screen.getAllByText('Nhà xe Ba Miền')).toHaveLength(2)
  })

  it('formats the due date the Vietnamese way', () => {
    granted = ['contract']
    overview = { ...emptyOverview(), expiring_contracts: rows }
    build()

    expect(screen.getByText('10/09/2026')).toBeInTheDocument()
  })

  it('flags the card as danger only when something is already overdue', () => {
    granted = ['contract']
    overview = { ...emptyOverview(), kpi: { contract_expiring: 2, contract_expired: 4 } }
    build()

    expect(screen.getByText('4 hợp đồng đã quá hạn')).toBeInTheDocument()
  })

  it('says "trong 30 ngày tới" when nothing is overdue yet', () => {
    granted = ['contract']
    overview = { ...emptyOverview(), kpi: { contract_expiring: 2, contract_expired: 0 } }
    build()

    expect(screen.getByText('Trong 30 ngày tới')).toBeInTheDocument()
  })
})
