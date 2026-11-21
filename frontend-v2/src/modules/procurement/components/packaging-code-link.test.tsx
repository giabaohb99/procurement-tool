import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'

import { PackagingCodeLink } from './packaging-code-link'

function Where() {
  const location = useLocation()
  return <p data-testid="where">{location.pathname + location.search}</p>
}

describe('PackagingCodeLink', () => {
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
