import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PackagingBom } from '../types/packaging-cost-types'
import { PackagingBomCard } from './packaging-bom-card'

describe('PackagingBomCard', () => {
  it('lists carton qty and the five components, red for a code missing from the catalog', () => {
    const bom = {
      id: 1,
      fg_code: 'HH0260',
      fg_name: 'GC - I - 260 - Bohex SC',
      legal_name: '',
      bottle_code: 'CPT0042',
      cap_code: '',
      label_code: 'NHG0260',
      carton_label_code: '',
      carton_code: '',
      carton_qty: 40,
      parts: [
        { role: 1, code: 'CPT0042', name: 'Chai PET tròn', unit: 'Cái', in_catalog: true },
        { role: 3, code: 'NHG0260', name: '', unit: '', in_catalog: false },
      ],
    } as PackagingBom
    render(<PackagingBomCard row={bom} />)
    expect(screen.getByText('HH0260')).toBeInTheDocument()
    expect(screen.getByText('Quy cách thùng')).toBeInTheDocument()
    expect(screen.getByText('40')).toBeInTheDocument()
    expect(screen.getByText('Chai PET tròn')).toBeInTheDocument()
    expect(screen.getByText('NHG0260')).toHaveClass('text-destructive')
    expect(screen.getByText('chưa có trong danh mục')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
