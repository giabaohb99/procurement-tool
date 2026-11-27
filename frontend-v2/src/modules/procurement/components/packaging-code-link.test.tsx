import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'

import { PackagingCodeLink } from './packaging-code-link'

let granted: string[] = []
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.includes(`${entity}:${action}`) }),
}))

function Where() {
  const location = useLocation()
  return <p data-testid="where">{location.pathname + location.search}</p>
}

describe('PackagingCodeLink', () => {
  beforeEach(() => {
    granted = ['packaging_history:read']
  })

  //  bao-CR-792 — đích là màn Lịch sử mua hàng: thiếu `packaging_history.read` thì mã là chữ thường, không bấm được.
  it('renders plain text, not a link, without packaging_history.read — whatever other packaging keys are held', () => {
    granted = [
      'packaging_impact:read',
      'packaging_product_summary:read',
      'packaging_price_list:read',
      'packaging_last_price:read',
      'packaging_bom:read',
      'packaging_cost:read',
    ]
    render(
      <MemoryRouter>
        <PackagingCodeLink code="CPT0075" />
        <PackagingCodeLink code="HH0260" product />
      </MemoryRouter>,
    )
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    expect(screen.getByText('CPT0075')).not.toHaveClass('text-primary')
    expect(screen.getByText('HH0260')).toBeInTheDocument()
  })

  it('opens the product-mode history for a product code', () => {
    render(
      <MemoryRouter>
        <PackagingCodeLink code="HH0260" product />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'HH0260' })).toHaveAttribute(
      'href',
      `${appRoutes.procurement.packagingHistory}?fg=HH0260`,
    )
  })

  //  bao-CR-801 — mã NGUYÊN LIỆU: đích là màn Lịch sử mua nguyên liệu, gác bằng khóa riêng `packaging_material_price`.
  it('opens the material history for a raw-material code, gated by packaging_material_price.read alone', () => {
    granted = ['packaging_material_price:read']
    render(
      <MemoryRouter>
        <PackagingCodeLink code="NL0001" rawMaterial />
        <PackagingCodeLink code="CPT0075" />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'NL0001' })).toHaveAttribute(
      'href',
      `${appRoutes.procurement.packagingMaterialHistory}?codes=NL0001`,
    )
    //  Khóa nguyên liệu không mở lịch sử của VTBB: mã VTBB cạnh đó vẫn là chữ thường.
    expect(screen.queryByRole('link', { name: 'CPT0075' })).not.toBeInTheDocument()
  })

  it('renders a raw-material code as plain text for someone holding only the VTBB history key', () => {
    granted = ['packaging_history:read', 'packaging_history:export']
    render(
      <MemoryRouter>
        <PackagingCodeLink code="NL0001" rawMaterial />
      </MemoryRouter>,
    )
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    expect(screen.getByText('NL0001')).not.toHaveClass('text-primary')
  })

  it('escapes a hostile raw-material code instead of letting it add query parameters', () => {
    granted = ['packaging_material_price:read']
    render(
      <MemoryRouter>
        <PackagingCodeLink code="NL&mode=product" rawMaterial />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'NL&mode=product' })).toHaveAttribute(
      'href',
      `${appRoutes.procurement.packagingMaterialHistory}?codes=NL%26mode%3Dproduct`,
    )
  })

  it('opens the purchase history of that code without triggering the row action around it', async () => {
    const onRowClick = vi.fn()
    render(
      <MemoryRouter initialEntries={['/start']}>
        <Routes>
          <Route
            path="/start"
            element={
              <div onClick={onRowClick}>
                <PackagingCodeLink code="CPT0075" />
              </div>
            }
          />
          <Route path={appRoutes.procurement.packagingHistory} element={<Where />} />
        </Routes>
      </MemoryRouter>,
    )
    await userEvent.setup().click(screen.getByRole('link', { name: 'CPT0075' }))
    expect(screen.getByTestId('where')).toHaveTextContent(
      `${appRoutes.procurement.packagingHistory}?codes=CPT0075`,
    )
    expect(onRowClick).not.toHaveBeenCalled()
  })
})
