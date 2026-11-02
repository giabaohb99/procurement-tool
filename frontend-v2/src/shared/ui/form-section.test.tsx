import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { FormSection, FormSectionProvider } from './form-section'

describe('FormSection', () => {
  it('keeps a collapsed body mounted (hidden) so field rules are not unmounted', () => {
    //  Hủy mount ô nhập là mất luôn luật chặn submit của nó (bẫy duoc-CR-317).
    render(
      <FormSection title="Lương" collapsible defaultOpen={false}>
        <input aria-label="Lương" />
      </FormSection>,
    )
    const input = screen.getByLabelText('Lương')
    expect(input).toBeInTheDocument()
    expect(input).not.toBeVisible()
  })

  it('toggles on click and never submits the surrounding form', () => {
    const onSubmit = vi.fn((event: { preventDefault: () => void }) => event.preventDefault())
    render(
      <form onSubmit={onSubmit}>
        <FormSection title="Kiêm nhiệm" collapsible defaultOpen={false} summary="2 phòng">
          <span>nội dung</span>
        </FormSection>
      </form>,
    )
    const toggle = screen.getByRole('button', { name: /Kiêm nhiệm/ })
    expect(toggle).toHaveAttribute('type', 'button')
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByText('2 phòng')).toBeInTheDocument()

    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('nội dung')).toBeVisible()
    //  Tóm tắt chỉ hiện khi đang gập.
    expect(screen.queryByText('2 phòng')).not.toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('forces the body open when it holds an invalid field, even after the user collapsed it', () => {
    const { rerender } = render(
      <FormSection title="Lương" collapsible>
        <span>ô lương</span>
      </FormSection>,
    )
    fireEvent.click(screen.getByRole('button', { name: /Lương/ }))
    expect(screen.getByText('ô lương')).not.toBeVisible()

    rerender(
      <FormSection title="Lương" collapsible forceOpen>
        <span>ô lương</span>
      </FormSection>,
    )
    expect(screen.getByText('ô lương')).toBeVisible()
    expect(screen.getByRole('button', { name: /Lương/ })).toHaveAttribute('aria-expanded', 'true')
  })

  it('renders a plain heading (no button) when not collapsible, in both variants', () => {
    render(
      <FormSectionProvider value={{ variant: 'flat' }}>
        <FormSection title="Công việc" collapsible={false}>
          <span>ô</span>
        </FormSection>
        <FormSection title="Ngân hàng" variant="default">
          <span>ô</span>
        </FormSection>
      </FormSectionProvider>,
    )
    expect(screen.getByRole('heading', { name: 'Công việc' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Ngân hàng' })).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
