import { Pause, Play } from 'lucide-react'
import { useReducedMotion } from 'motion/react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

import type { DemoChapter } from './chapter-demo-types'
import { chapterNumber, cursorAt } from './chapter-timeline'
import { DemoCursor } from './demo-cursor'
import { useChapterPlayer } from './use-chapter-player'

interface ChapterDemoProps {
  chapters: readonly DemoChapter[]
  autoplay?: boolean
  onChapterChange?: (index: number) => void
  /** Ép chế độ giảm chuyển động (mặc định theo `prefers-reduced-motion` của máy). */
  reducedMotion?: boolean
  className?: string
}

/**
 * Khung DEMO THEO CHƯƠNG (ai-CR-214, K8 doc/erp/21 §6.4): khung 16:9 dựng bằng chính
 * component v2 với dữ liệu giả, con trỏ giả di chuyển + gõ chữ; dưới là dải chương đánh số,
 * chương đang chạy có gạch tiến độ, bấm chương nào nhảy chương đó, nút tạm dừng / chạy tiếp.
 * Máy bật giảm chuyển động thì không tự chạy: mỗi chương là một ảnh tĩnh ở trạng thái cuối
 * kèm chữ, người xem tự bấm chương.
 */
export function ChapterDemo({ chapters, autoplay = true, onChapterChange, reducedMotion, className }: ChapterDemoProps) {
  const prefersReduced = useReducedMotion()
  const reduced = reducedMotion ?? Boolean(prefersReduced)
  const player = useChapterPlayer({
    durations: chapters.map((c) => c.durationMs),
    autoplay,
    reduced,
    onChapterChange,
  })

  if (chapters.length === 0) return null
  const chapter = chapters[player.index]
  const cursor = !reduced && chapter.cursor ? cursorAt(chapter.cursor, player.progress) : null

  return (
    <section className={cn('space-y-3', className)} aria-label="Demo theo chương">
      <div className="relative aspect-video w-full overflow-hidden rounded-xl border bg-muted/40">
        {/* Cảnh chỉ để xem: `inert` để nút / ô giả trong cảnh không nhận phím Tab hay cú bấm thật. */}
        <div className="absolute inset-0 p-4" key={chapter.id} inert aria-hidden>
          {chapter.render({ progress: player.progress, reduced })}
        </div>
        {cursor && <DemoCursor state={cursor} />}
      </div>

      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold">
            <span className="text-muted-foreground">Chương {chapterNumber(player.index)}</span> · {chapter.title}
          </h3>
          <p className="text-sm text-muted-foreground">{chapter.caption}</p>
        </div>
        {!reduced && (
          <Button type="button" variant="outline" size="sm" onClick={player.toggle}>
            {player.playing ? <Pause className="size-4" /> : <Play className="size-4" />}
            {player.playing ? 'Tạm dừng' : 'Chạy tiếp'}
          </Button>
        )}
      </div>

      <ol className="grid grid-cols-3 gap-2 sm:grid-cols-5 lg:grid-cols-9">
        {chapters.map((c, i) => {
          const active = i === player.index
          const done = i < player.index
          return (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => player.goTo(i)}
                aria-current={active ? 'step' : undefined}
                className={cn(
                  'w-full rounded-md border px-2 py-1.5 text-left text-xs transition-colors hover:bg-accent',
                  active && 'border-primary bg-accent',
                )}
              >
                <span className="block font-semibold tabular-nums">{chapterNumber(i)}</span>
                <span className="line-clamp-2 text-muted-foreground">{c.title}</span>
                <span className="mt-1 block h-0.5 overflow-hidden rounded bg-muted" aria-hidden>
                  <span
                    className="block h-full bg-primary"
                    style={{ width: `${(active ? player.progress : done ? 1 : 0) * 100}%` }}
                  />
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
