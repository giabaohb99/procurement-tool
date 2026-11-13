import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { useAttachParam } from './use-attach-param'

function Probe() {
  return <span data-testid="attach">{useAttachParam() ? 'mở' : 'không'}</span>
}

function read(url: string) {
  render(
    <MemoryRouter initialEntries={[url]}>
      <Probe />
    </MemoryRouter>,
  )
  return screen.getByTestId('attach').textContent
}

/** ai-CR-240 — `?attach=1` của link trợ lý AI. */
describe('useAttachParam', () => {
  it('bật khi có attach=1', () => {
    expect(read('/procurement/purchase-orders/7?delivery=800&attach=1')).toBe('mở')
  })

  it('tắt khi thiếu hoặc giá trị khác 1', () => {
    expect(read('/procurement/purchase-orders/7?delivery=800')).toBe('không')
  })

  it('giá trị lạ không bật', () => {
    expect(read('/finance/payment-requests/3?attach=yes')).toBe('không')
  })
})
