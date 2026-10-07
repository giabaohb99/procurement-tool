import { fireEvent, render, screen } from '@testing-library/react'
import type { FormEvent } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { LaborContractTermPresets } from './labor-contract-term-presets'

function renderPresets(props: Partial<Parameters<typeof LaborContractTermPresets>[0]> = {}) {
  const onPick = vi.fn()
  const onOuterSubmit = vi.fn((e: FormEvent) => e.preventDefault())
  render(
    <form onSubmit={onOuterSubmit}>
      <LaborContractTermPresets contractType={2} startDate="2026-11-01" endDate="" onPick={onPick} {...props} />
    </form>,
  )
  return { onPick, onOuterSubmit }
}

describe('LaborContractTermPresets', () => {
  it('fills the end date computed from the start date when a preset is clicked', () => {
    const { onPick } = renderPresets()
    fireEvent.click(screen.getByRole('button', { name: '36 tháng' }))
    expect(onPick).toHaveBeenCalledWith('2029-10-31')
  })

  //  Bẫy «nút trong <form> thiếu type=button»: hộp HĐ nằm trong form hồ sơ nhân sự, bấm nút
  //  chọn nhanh mà thành submit là lưu đè luôn hồ sơ.
  it('does not submit the surrounding form', () => {
    const { onOuterSubmit } = renderPresets()
    fireEvent.click(screen.getByRole('button', { name: '12 tháng' }))
    expect(onOuterSubmit).not.toHaveBeenCalled()
  })

  it('disables every preset and says why when there is no start date yet', () => {
    const { onPick } = renderPresets({ startDate: '' })
    for (const label of ['12 tháng', '24 tháng', '36 tháng']) {
      expect(screen.getByRole('button', { name: label })).toBeDisabled()
    }
    expect(screen.getByText('Chọn ngày bắt đầu trước')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '12 tháng' }))
    expect(onPick).not.toHaveBeenCalled()
  })

  it('marks the preset matching the current end date as pressed, and only that one', () => {
    renderPresets({ endDate: '2028-10-31' })
    expect(screen.getByRole('button', { name: '24 tháng' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '12 tháng' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('shows day-based presets for probation contracts', () => {
    const { onPick } = renderPresets({ contractType: 1 })
    expect(screen.queryByRole('button', { name: '12 tháng' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '60 ngày' }))
    expect(onPick).toHaveBeenCalledWith('2026-12-30')
  })

  it('renders nothing for indefinite-term contracts or before a type is chosen', () => {
    const { container } = render(
      <>
        <LaborContractTermPresets contractType={3} startDate="2026-11-01" endDate="" onPick={vi.fn()} />
        <LaborContractTermPresets contractType={0} startDate="2026-11-01" endDate="" onPick={vi.fn()} />
      </>,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
