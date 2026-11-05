import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CustomsPesticideUseCard } from './customs-pesticide-use-card'

describe('CustomsPesticideUseCard', () => {
  it('labels every field so crop and pest cannot be confused', () => {
    render(
      <CustomsPesticideUseCard
        row={{
          id: 1,
          crop: 'Lúa',
          pest: 'Cỏ lồng vực',
          dosage: '1,5 kg/ha',
          pre_harvest_interval: '14 ngày',
          usage: 'Pha 1,5 kg thuốc với 400 lít nước, phun sau sạ 3 ngày.',
        }}
      />,
    )

    expect(screen.getByText('Lúa')).toBeInTheDocument()
    expect(screen.getByText('Dịch hại: Cỏ lồng vực')).toBeInTheDocument()
    expect(screen.getByText('Liều lượng: 1,5 kg/ha')).toBeInTheDocument()
    expect(screen.getByText('Cách ly: 14 ngày')).toBeInTheDocument()
    expect(screen.getByText(/Pha 1,5 kg thuốc/)).toBeInTheDocument()
  })

  it('skips empty fields entirely instead of printing "Liều lượng: "', () => {
    render(
      <CustomsPesticideUseCard
        row={{ id: 2, crop: '', pest: 'Rầy nâu', dosage: '', pre_harvest_interval: '', usage: '' }}
      />,
    )

    expect(screen.getByText('—')).toBeInTheDocument()
    expect(screen.queryByText(/Liều lượng/)).toBeNull()
    expect(screen.queryByText(/Cách ly/)).toBeNull()
  })

  it('two fields with the same text still both render', () => {
    render(
      <CustomsPesticideUseCard
        row={{ id: 3, crop: 'Lúa', pest: 'X', dosage: 'X', pre_harvest_interval: 'X', usage: '' }}
      />,
    )

    expect(screen.getByText('Dịch hại: X')).toBeInTheDocument()
    expect(screen.getByText('Liều lượng: X')).toBeInTheDocument()
    expect(screen.getByText('Cách ly: X')).toBeInTheDocument()
  })
})
