import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TooltipProvider } from '@/shared/ui/tooltip'
import { CompanyAvatarGroup } from './company-avatar-group'
import type { SealCompanyRef } from '../types/seal-request'

const MOCK_COMPANIES: SealCompanyRef[] = [
  { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', tax_code: '0312345678', logo: '/dego-icon.png' },
  { id: 2, name: 'CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL', tax_code: '0312345679', logo: '/ida-icon.png' },
  { id: 3, name: 'CÔNG TY TNHH HÓA CHẤT ABA', tax_code: '0312345680', logo: '' },
]

function renderWithTooltip(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>)
}

describe('CompanyAvatarGroup', () => {
  it('hiển thị gạch ngang khi không có công ty', () => {
    const { container } = renderWithTooltip(<CompanyAvatarGroup companies={[]} />)
    expect(container).toHaveTextContent('—')
  })

  it('hiển thị 1 avatar và tên khi chỉ có 1 công ty', () => {
    renderWithTooltip(<CompanyAvatarGroup companies={[MOCK_COMPANIES[0]]} />)
    expect(screen.getByText('CÔNG TY TNHH DEGO HOLDING')).toBeInTheDocument()
  })

  it('hiển thị avatar group và số lượng khi có nhiều công ty', () => {
    renderWithTooltip(<CompanyAvatarGroup companies={MOCK_COMPANIES} />)
    expect(screen.getByText('(3 công ty)')).toBeInTheDocument()
  })

  it('hỗ trợ hiển thị đúng số lượng avatar tooltip trigger trong group', () => {
    const { container } = renderWithTooltip(<CompanyAvatarGroup companies={MOCK_COMPANIES} />)
    const avatarTriggers = container.querySelectorAll('[data-slot="avatar-group"] [data-slot="tooltip-trigger"]')
    expect(avatarTriggers.length).toBe(3)
  })
})
