import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { PackagingSelectedCode } from '../types/packaging-cost-types'
import { PackagingSelectedCodeCard } from './packaging-selected-code-card'

const row: PackagingSelectedCode = {
  code: 'CET0028',
  name: 'Chai PAPE tròn cổ 43',
  group: 'Chai',
  unit: 'Cái',
  old: 3170,
  new: 3500.5,
  assumed: null,
  applied: 3500.5,
  diff: 330.5,
  pct: 0.104,
  usage: 30,
  min: 3170,
  max: 4724,
  warnings: [],
}

function renderCard(over: Partial<PackagingSelectedCode> = {}) {
  const onAssumedChange = vi.fn()
  const onRemove = vi.fn()
  render(
    <MemoryRouter>
      <PackagingSelectedCodeCard
        row={{ ...row, ...over }}
        assumed={undefined}
        onAssumedChange={onAssumedChange}
        onRemove={onRemove}
      />
    </MemoryRouter>,
  )
  return { onAssumedChange, onRemove }
}

describe('PackagingSelectedCodeCard', () => {
  it('shows code (link to history), name, the old → new / diff strip, the assumed-price row and the footer', () => {
    renderCard()
    expect(screen.getByRole('link', { name: 'CET0028' })).toHaveAttribute('href', expect.stringContaining('CET0028'))
    expect(screen.getByText('Chai PAPE tròn cổ 43')).toBeInTheDocument()
    expect(screen.getByText('· Chai')).toBeInTheDocument()
    for (const label of ['Giá cũ', 'Giá mới', 'Chênh lệch', 'Giá giả định']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
    expect(screen.getByText('3.170')).toBeInTheDocument()
    expect(screen.getByText('3.500,5')).toBeInTheDocument()
    expect(screen.getByText('30 SP bị ảnh hưởng · Min–Max 3.170 – 4.724')).toBeInTheDocument()
  })

  it('shows no warning line when the row has none, and one when it has', () => {
    renderCard({ warnings: [] })
    expect(screen.queryByText(/Thiếu giá/)).not.toBeInTheDocument()
    renderCard({ code: 'NAP0001', warnings: [3] })
    expect(screen.getByText('Thiếu giá thành phần')).toBeInTheDocument()
  })

  it('colours an increase green and a decrease red, like the table', () => {
    renderCard()
    expect(screen.getByText('+330,5')).toHaveClass('text-emerald-600')
    renderCard({ code: 'NAP0001', diff: -20, pct: -0.05 })
    expect(screen.getByText('-20')).toHaveClass('text-destructive')
  })

  it('keeps the assumed-price input editable on the card', async () => {
    const { onAssumedChange } = renderCard()
    await userEvent.type(screen.getByLabelText('Giá giả định CET0028'), '4500')
    expect(onAssumedChange).toHaveBeenLastCalledWith('CET0028', 4500)
  })

  it('removes the code from the selection', () => {
    const { onRemove } = renderCard()
    fireEvent.click(screen.getByRole('button', { name: 'Bỏ CET0028' }))
    expect(onRemove).toHaveBeenCalledWith('CET0028')
  })
})
