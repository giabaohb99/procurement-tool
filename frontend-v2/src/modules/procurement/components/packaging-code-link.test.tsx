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
