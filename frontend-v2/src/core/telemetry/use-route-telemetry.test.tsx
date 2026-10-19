import { act, render } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { telemetry } from './telemetry-queue'
import { UI_EVENT } from './ui-event-codes'
import { useRouteTelemetry } from './use-route-telemetry'

afterEach(() => vi.restoreAllMocks())

function Shell() {
  useRouteTelemetry()
  return null
}

describe('useRouteTelemetry', () => {
  it('emits PAGE_VIEW with an id-free pattern, then PAGE_LEAVE + PAGE_VIEW on navigation', async () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const router = createMemoryRouter(
      [{ element: <Shell />, children: [{ path: '/po/:id', element: null }, { path: '/list', element: null }] }],
      { initialEntries: ['/po/129?q=secret'] },
    )
    await act(async () => {
      render(<RouterProvider router={router} />)
    })
    await act(async () => {
      await router.navigate('/list')
    })
    const calls = spy.mock.calls.map((c) => c[0] as { type: number; route: string })
    expect(calls.map((c) => [c.type, c.route])).toEqual([
      [UI_EVENT.PAGE_VIEW, '/po/:id'],
      [UI_EVENT.PAGE_LEAVE, '/po/:id'],
      [UI_EVENT.PAGE_VIEW, '/list'],
    ])
    expect(JSON.stringify(calls)).not.toContain('secret')
    expect(JSON.stringify(calls)).not.toContain('129')
  })

  it('emits PAGE_LEAVE for the open screen on pagehide', async () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const router = createMemoryRouter([{ element: <Shell />, children: [{ path: '/a', element: null }] }], {
      initialEntries: ['/a'],
    })
    await act(async () => {
      render(<RouterProvider router={router} />)
    })
    spy.mockClear()
    telemetry.handlePageHide()
    expect(spy.mock.calls.map((c) => (c[0] as { type: number }).type)).toEqual([UI_EVENT.PAGE_LEAVE])
  })
})
