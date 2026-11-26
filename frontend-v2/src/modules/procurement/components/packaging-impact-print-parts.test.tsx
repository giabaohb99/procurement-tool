import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PackagingSelectedCode } from '../types/packaging-cost-types'
import { PrintImpactSelection } from './packaging-impact-print-parts'

const baseRow: PackagingSelectedCode = {
  code: 'CHT0023',
  name: 'Chai HDPE',
  group: 'Chai',
  unit: 'Cái',
  old: 4061,
  new: 4061,
  assumed: null,
  applied: 4061,
  diff: null,
  pct: null,
  usage: 10,
  min: 3000,
  max: 4061,
}

describe('PrintImpactSelection', () => {
  it('shows a dash (not the words "Bỏ trống") for a code without an assumed price', () => {
    render(<PrintImpactSelection codes={['CHT0023']} extras={[]} rows={[baseRow]} />)
    expect(screen.queryByText('Bỏ trống')).not.toBeInTheDocument()
    expect(document.querySelector('.cell-inp')?.textContent).toBe('—')
  })

  it('shows the assumed price inside the input-looking cell when there is one', () => {
    render(<PrintImpactSelection codes={['CHT0023']} extras={[]} rows={[{ ...baseRow, assumed: 4500 }]} />)
    expect(document.querySelector('.cell-inp')?.textContent).toBe('4.500')
  })
})
