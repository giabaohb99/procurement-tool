import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { FormSectionProvider } from '@/shared/ui/form-section'
import { SectionHeading } from '@/shared/ui/section-heading'
import { EmployeeDetailBlock } from './employee-detail-block'

describe('EmployeeDetailBlock', () => {
  it('renders the child untouched outside the flat profile screen (e.g. the personal page)', () => {
    render(
      <EmployeeDetailBlock title="Người báo tin">
        <SectionHeading>Người báo tin</SectionHeading>
      </EmployeeDetailBlock>,
    )
    expect(screen.queryByRole('button', { name: /Người báo tin/ })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Người báo tin' })).toBeInTheDocument()
  })

  it('becomes a collapsible group on the flat screen and keeps the content mounted when collapsed', () => {
    render(
      <FormSectionProvider value={{ variant: 'flat' }}>
        <EmployeeDetailBlock title="Phiên đăng nhập">
          <button type="button">Bắt đăng nhập lại</button>
        </EmployeeDetailBlock>
      </FormSectionProvider>,
    )
    const toggle = screen.getByRole('button', { name: 'Phiên đăng nhập' })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    //  Gập chỉ là ẩn: nút bên trong vẫn còn trong cây, không bị hủy mount.
    expect(screen.getByText('Bắt đăng nhập lại')).not.toBeVisible()
  })
})
