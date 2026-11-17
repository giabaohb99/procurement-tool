import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { CardCollapseScope } from './card-collapse'
import { FormCard } from './form-card'

function renderCard(withScope: boolean) {
  const card = (
    <FormCard title="Quỹ phép 2026">
      <p>Phép năm còn 10 ngày</p>
    </FormCard>
  )
  return render(withScope ? <CardCollapseScope scope="me">{card}</CardCollapseScope> : card)
}

describe('FormCard collapse (duoc-CR-772)', () => {
  beforeEach(() => localStorage.clear())

  it('has no toggle outside a collapse scope, so other screens stay unchanged', () => {
    renderCard(false)
    expect(screen.queryByRole('button', { name: /Thu gọn|Mở/ })).not.toBeInTheDocument()
    expect(screen.getByText('Phép năm còn 10 ngày')).toBeVisible()
  })

  it('starts open with a chevron up, collapses on click and shows a chevron down to reopen', () => {
    renderCard(true)
    const toggle = screen.getByRole('button', { name: 'Thu gọn Quỹ phép 2026' })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    fireEvent.click(toggle)
    expect(screen.getByText('Phép năm còn 10 ngày')).not.toBeVisible()
    const reopen = screen.getByRole('button', { name: 'Mở Quỹ phép 2026' })
    expect(reopen).toHaveAttribute('aria-expanded', 'false')

    fireEvent.click(reopen)
    expect(screen.getByText('Phép năm còn 10 ngày')).toBeVisible()
  })

  it('remembers a collapsed card after the page is opened again', () => {
    const { unmount } = renderCard(true)
    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn Quỹ phép 2026' }))
    unmount()

    renderCard(true)
    expect(screen.getByRole('button', { name: 'Mở Quỹ phép 2026' })).toBeInTheDocument()
    expect(screen.getByText('Phép năm còn 10 ngày')).not.toBeVisible()
  })

  it('keeps the card body mounted while collapsed so typed drafts are not lost', () => {
    renderCard(true)
    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn Quỹ phép 2026' }))
    expect(screen.getByText('Phép năm còn 10 ngày')).toBeInTheDocument()
  })
})
