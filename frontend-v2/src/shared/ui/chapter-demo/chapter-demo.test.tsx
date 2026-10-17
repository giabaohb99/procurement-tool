import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ChapterDemo } from './chapter-demo'
import type { DemoChapter } from './chapter-demo-types'
import { PLAYER_TICK_MS } from './use-chapter-player'

const chapters: DemoChapter[] = [
  { id: 'a', title: 'Mở đầu', caption: 'Câu một', durationMs: 200, render: ({ progress }) => <p>cảnh a {progress}</p> },
  { id: 'b', title: 'Giữa', caption: 'Câu hai', durationMs: 200, render: () => <p>cảnh b</p> },
  { id: 'c', title: 'Kết', caption: 'Câu ba', durationMs: 200, render: () => <p>cảnh c</p> },
]

describe('ChapterDemo', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('lists every chapter with a two-digit number and marks the running one', () => {
    render(<ChapterDemo chapters={chapters} autoplay={false} reducedMotion={false} />)
    const steps = screen.getAllByRole('listitem')
    expect(steps).toHaveLength(3)
    expect(screen.getByRole('button', { name: /01\s*Mở đầu/ })).toHaveAttribute('aria-current', 'step')
    expect(screen.getByRole('heading')).toHaveTextContent('Chương 01 · Mở đầu')
    expect(screen.getByText('Câu một')).toBeInTheDocument()
  })

  it('jumps to a chapter when it is clicked and reports the change', () => {
    const onChange = vi.fn()
    render(<ChapterDemo chapters={chapters} autoplay={false} reducedMotion={false} onChapterChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: /03\s*Kết/ }))
    expect(screen.getByRole('heading')).toHaveTextContent('Chương 03 · Kết')
    expect(screen.getByText('cảnh c')).toBeInTheDocument()
    expect(onChange).toHaveBeenCalledWith(2)
  })

  it('plays through chapters on its own and stops at the end', () => {
    const onChange = vi.fn()
    render(<ChapterDemo chapters={chapters} reducedMotion={false} onChapterChange={onChange} />)
    expect(screen.getByRole('button', { name: 'Tạm dừng' })).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(200 + PLAYER_TICK_MS))
    expect(screen.getByRole('heading')).toHaveTextContent('Chương 02')
    act(() => vi.advanceTimersByTime(2000))
    expect(screen.getByRole('heading')).toHaveTextContent('Chương 03')
    expect(screen.getByRole('button', { name: 'Chạy tiếp' })).toBeInTheDocument()
    expect(onChange.mock.calls.map((c) => c[0])).toEqual([1, 2])
  })

  it('stays on the chapter while paused', () => {
    render(<ChapterDemo chapters={chapters} reducedMotion={false} />)
    fireEvent.click(screen.getByRole('button', { name: 'Tạm dừng' }))
    act(() => vi.advanceTimersByTime(5000))
    expect(screen.getByRole('heading')).toHaveTextContent('Chương 01')
  })

  it('with reduced motion shows each chapter as a still final frame and never autoplays', () => {
    render(<ChapterDemo chapters={chapters} reducedMotion />)
    expect(screen.queryByRole('button', { name: 'Tạm dừng' })).toBeNull()
    expect(screen.getByText('cảnh a 1')).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(5000))
    expect(screen.getByRole('heading')).toHaveTextContent('Chương 01')
  })

  it('renders nothing for an empty chapter list instead of crashing', () => {
    const { container } = render(<ChapterDemo chapters={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})
