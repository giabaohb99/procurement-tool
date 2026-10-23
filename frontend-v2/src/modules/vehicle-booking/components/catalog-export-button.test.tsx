import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CatalogExportButton } from './catalog-export-button'

const can = vi.fn()
vi.mock('@/core/authorization/use-permission', () => ({ usePermission: () => ({ can }) }))
vi.mock('@/core/api', () => ({ downloadFile: vi.fn() }))

function renderButton() {
  return render(
    <MemoryRouter>
      <CatalogExportButton entity="vehicle" apiPath="/api/vehicles" searchParam="license_plate" filename="xe.xlsx" />
    </MemoryRouter>,
  )
}

describe('CatalogExportButton (duoc-CR-675)', () => {
  beforeEach(() => can.mockReset())

  //  Trước duoc-CR-675 nút luôn hiện trong khi máy chủ đã gác `export` → người chỉ có quyền Xem bấm ra 403.
  it('hides the button without export permission instead of letting it fail with 403', () => {
    can.mockReturnValue(false)
    renderButton()
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).toBeNull()
    expect(can).toHaveBeenCalledWith('vehicle', 'export')
  })

  it('shows the button when the user can export this catalog', () => {
    can.mockImplementation((entity: string, action: string) => entity === 'vehicle' && action === 'export')
    renderButton()
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeTruthy()
  })
})
