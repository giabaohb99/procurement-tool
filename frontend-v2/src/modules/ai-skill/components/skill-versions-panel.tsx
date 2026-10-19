import { useMemo, useState } from 'react'

import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { useSkillVersion, useSkillVersions } from '../hooks/use-ai-skill'
import { diffLines, type DiffLine } from '../utils/line-diff'

/** Giá trị ô chọn trỏ vào bản NHÁP đang soạn thay cho một phiên bản đã xuất bản. */
const DRAFT = 'draft'

interface SkillVersionsPanelProps {
  skillId: number
  /** Nội dung nháp đang trên màn (kể cả chưa lưu) — để so «nháp này khác bản AI đang đọc chỗ nào». */
  draftBody: string
}

/**
 * Tab «Phiên bản» của trang soạn (G4): danh sách bản đã xuất bản + so HAI bản cạnh nhau, dòng bớt tô đỏ bên trái,
 * dòng thêm tô xanh bên phải. Mặc định so bản AI đang đọc với bản nháp đang soạn — câu hỏi hay gặp nhất trước khi bấm
 * Xuất bản.
 */
export function SkillVersionsPanel({ skillId, draftBody }: SkillVersionsPanelProps) {
  const { data, isLoading } = useSkillVersions(skillId)
  const versions = useMemo(() => data?.items ?? [], [data])
  const current = versions.find((v) => v.is_current) ?? versions[0]
  const [leftChoice, setLeftChoice] = useState('')
  const [rightChoice, setRightChoice] = useState(DRAFT)
  const left = leftChoice || (current ? String(current.id) : '')

  const leftVersion = useSkillVersion(Number(left) || 0)
  const rightVersion = useSkillVersion(rightChoice === DRAFT ? 0 : Number(rightChoice))
  const leftBody = leftVersion.data?.body_md ?? ''
  const rightBody = rightChoice === DRAFT ? draftBody : (rightVersion.data?.body_md ?? '')
  const diff = useMemo(() => diffLines(leftBody, rightBody), [leftBody, rightBody])

  if (isLoading) return <Skeleton className="h-40 w-full" />
  if (versions.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          Chưa xuất bản lần nào — AI chưa đọc được skill này. Bấm Xuất bản khi nội dung và tóm tắt đã xong.
        </CardContent>
      </Card>
    )
  }

  const options = versions.map((v) => ({
    value: String(v.id),
    label: `v${v.version_no}${v.is_current ? ' (AI đang đọc)' : ''} · ${formatDateTime(v.published_at)}`,
  }))

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <SectionHeading>Các bản đã xuất bản</SectionHeading>
        </CardHeader>
        <CardContent>
          <ul className="divide-y rounded-md border text-sm">
            {versions.map((v) => (
              <li key={v.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2">
                <span className="font-medium">v{v.version_no}</span>
                {v.is_current && <span className="text-xs text-success">AI đang đọc</span>}
                <span className="text-xs text-muted-foreground">{formatDateTime(v.published_at)}</span>
                <span className="min-w-0 flex-1 truncate text-muted-foreground">{v.change_note || 'Không ghi chú'}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeading>So hai bản</SectionHeading>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label>Bản bên trái</Label>
              <Select value={left} onValueChange={setLeftChoice}>
                <SelectTrigger className="w-full" aria-label="Bản bên trái">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {options.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Bản bên phải</Label>
              <Select value={rightChoice} onValueChange={setRightChoice}>
                <SelectTrigger className="w-full" aria-label="Bản bên phải">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={DRAFT}>Bản nháp đang soạn</SelectItem>
                  {options.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            {diff.tooLarge
              ? 'Hai bản quá dài để tô khác biệt — chỉ đặt cạnh nhau.'
              : diff.added + diff.removed === 0
                ? 'Hai bản giống hệt nhau.'
                : `Bên phải thêm ${diff.added} dòng, bớt ${diff.removed} dòng so với bên trái.`}
          </p>
          <div className="grid gap-3 lg:grid-cols-2">
            <DiffPane lines={diff.left} loading={leftVersion.isLoading} />
            <DiffPane lines={diff.right} loading={rightChoice !== DRAFT && rightVersion.isLoading} />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function DiffPane({ lines, loading }: { lines: DiffLine[]; loading: boolean }) {
  if (loading) return <Skeleton className="h-40 w-full" />
  return (
    <pre className="max-h-[32rem] min-w-0 overflow-auto rounded-md border bg-muted/30 p-2 font-mono text-xs leading-5">
      {lines.length === 0 ? (
        <span className="text-muted-foreground">(rỗng)</span>
      ) : (
        lines.map((line, index) => (
          <div
            key={index}
            className={cn(
              'px-1 whitespace-pre-wrap break-words',
              line.kind === 'removed' && 'bg-destructive/15 text-destructive',
              line.kind === 'added' && 'bg-success/15 text-success',
            )}
          >
            {line.text || ' '}
          </div>
        ))
      )}
    </pre>
  )
}
