import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PackagingImpactSummary } from './packaging-impact-summary'

const kpis = {
  selected_count: 3,
  selected_by_group: { Chai: 2, Nắp: 1 },
  assumed_count: 1,
  affected_products: 284,
  increased: 0,
  decreased: 0,
  max_increase_carton: null,
  max_increase_bottle: null,
}

describe('PackagingImpactSummary', () => {
  it('shows the selected count with its groups and the affected product count in one line', () => {
    render(<PackagingImpactSummary kpis={kpis} />)
    const line = screen.getByText(/Mã đã chọn/)
    expect(line).toHaveTextContent('Mã đã chọn 3 (2 chai · 1 nắp · 1 mã giả định)')
    expect(line).toHaveTextContent('Sản phẩm bị ảnh hưởng 284')
  })

  it('renders nothing before the first answer arrives', () => {
    const { container } = render(<PackagingImpactSummary kpis={undefined} />)
    expect(container).toBeEmptyDOMElement()
  })
})
