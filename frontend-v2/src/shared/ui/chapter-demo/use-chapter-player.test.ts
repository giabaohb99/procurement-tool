import { describe, expect, it } from 'vitest'

import { stepPlayer, type PlayerState } from './use-chapter-player'

const durations = [1000, 2000, 500]
const at = (index: number, elapsed: number, playing = true): PlayerState => ({ index, elapsed, playing })

describe('stepPlayer', () => {
  it('counts time only while playing', () => {
    expect(stepPlayer(at(0, 100), { type: 'tick', ms: 50 }, durations)).toEqual(at(0, 150))
    expect(stepPlayer(at(0, 100, false), { type: 'tick', ms: 50 }, durations)).toEqual(at(0, 100, false))
  })

  it('moves to the next chapter from its start when time runs out (leftover time is not carried over)', () => {
    expect(stepPlayer(at(0, 990), { type: 'tick', ms: 50 }, durations)).toEqual(at(1, 0))
  })

  it('stops on the final frame of the last chapter instead of looping', () => {
    expect(stepPlayer(at(2, 480), { type: 'tick', ms: 50 }, durations)).toEqual(at(2, 500, false))
  })

  it('restarts from chapter one when play is pressed after the end', () => {
    expect(stepPlayer(at(2, 500, false), { type: 'toggle' }, durations)).toEqual(at(0, 0, true))
  })

  it('pauses and resumes in place mid-chapter', () => {
    const paused = stepPlayer(at(1, 700), { type: 'toggle' }, durations)
    expect(paused).toEqual(at(1, 700, false))
    expect(stepPlayer(paused, { type: 'toggle' }, durations)).toEqual(at(1, 700, true))
  })

  it('jumps to the start of the picked chapter and clamps silly targets', () => {
    expect(stepPlayer(at(0, 300), { type: 'goTo', index: 2 }, durations)).toEqual(at(2, 0))
    expect(stepPlayer(at(1, 300), { type: 'goTo', index: -5 }, durations).index).toBe(0)
    expect(stepPlayer(at(1, 300), { type: 'goTo', index: 99 }, durations).index).toBe(2)
    expect(stepPlayer(at(1, 300), { type: 'goTo', index: Number.NaN }, durations).index).toBe(0)
  })

  it('ignores negative ticks and survives zero or broken durations', () => {
    expect(stepPlayer(at(0, 100), { type: 'tick', ms: -500 }, durations)).toEqual(at(0, 100))
    expect(stepPlayer(at(0, 0), { type: 'tick', ms: 50 }, [0, Number.NaN])).toEqual(at(1, 0))
  })

  it('does nothing useful with no chapters at all', () => {
    expect(stepPlayer(at(3, 10), { type: 'tick', ms: 50 }, [])).toEqual(at(0, 0, false))
  })
})
