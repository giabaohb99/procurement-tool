import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { DashboardOverview } from '@/modules/procurement/api/procurement-dashboard-api'
import { InventoryDashboardPage } from './inventory-dashboard-page'

let overview: Partial<DashboardOverview> | undefined

vi.mock('@/modules/procurement/hooks/use-procurement-dashboard', () => ({
  useProcurementDashboard: () => ({ data: overview, isLoading: false }),
}))
vi.mock('../hooks/use-inventory', () => ({
  useInventoryItems: () => ({ data: { total: 3, items: [] }, isLoading: false }),
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

const EMPTY_LABEL = /Chưa có giá trị tồn ở kho nào/

function build() {
  return render(
    <MemoryRouter>
      <InventoryDashboardPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  overview = {
    kpi: { inv_value: 1_500_000, out_of_stock: 0 },
    low_stock: [],
    kpi_inv_by_warehouse: [
      { warehouse_code: 'KTP', warehouse_name: 'Kho thành phẩm', value: 1_000_000, lines: 4 },
      { warehouse_code: '', warehouse_name: '', value: 500_000, lines: 1 },
    ],
  }
})

describe('InventoryDashboardPage — biểu đồ giá trị tồn theo kho (kh-NT2-8)', () => {
  it('shows the chart card, not the empty message, when warehouses have stock value', () => {
    build()
    expect(screen.getByText('Giá trị tồn theo kho')).toBeInTheDocument()
    expect(screen.queryByText(EMPTY_LABEL)).not.toBeInTheDocument()
  })

  it('shows the empty message when the list is empty — e.g. no inventory permission on the server', () => {
    overview = { ...overview, kpi_inv_by_warehouse: [] }
    build()
    expect(screen.getByText(EMPTY_LABEL)).toBeInTheDocument()
  })

  it('does not break against an older server that does not send the key yet', () => {
    overview = { kpi: { inv_value: 0 }, low_stock: [] }
    build()
    expect(screen.getByText(EMPTY_LABEL)).toBeInTheDocument()
  })

  it('treats a list with only zero values as empty', () => {
    overview = {
      ...overview,
      kpi_inv_by_warehouse: [{ warehouse_code: 'K1', warehouse_name: 'Kho 1', value: 0, lines: 2 }],
    }
    build()
    expect(screen.getByText(EMPTY_LABEL)).toBeInTheDocument()
  })
})
