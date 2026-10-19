import { describe, expect, it } from 'vitest'

import { createDwellTimer } from './dwell-timer'

describe('createDwellTimer', () => {
  it('counts only the time the tab is visible', () => {
    let t = 0
    const timer = createDwellTimer(() => t, true)
    t = 10_000
    timer.setVisible(false)
    t = 70_000
    timer.setVisible(true)
    t = 75_000
    expect(timer.elapsed()).toBe(15_000)
  })

  it('take() returns the total and restarts from zero', () => {
    let t = 0
    const timer = createDwellTimer(() => t, true)
    t = 4_000
    expect(timer.take()).toBe(4_000)
    t = 6_000
    expect(timer.take()).toBe(2_000)
  })

  it('stays at zero when hidden from the start and ignores repeated toggles', () => {
    let t = 0
    const timer = createDwellTimer(() => t, false)
    t = 50_000
    timer.setVisible(false)
    expect(timer.elapsed()).toBe(0)
    timer.setVisible(true)
    timer.setVisible(true)
    t = 51_000
    expect(timer.elapsed()).toBe(1_000)
  })
})
