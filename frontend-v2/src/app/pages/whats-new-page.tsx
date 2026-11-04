import { Sparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { env } from '@/core/config/env'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDate } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'
import { filterReleases, runningVersionText } from '@/shared/release/release-format'
import { useMarkReleaseSeen, useReleaseNotes, useReleaseUnseen } from '@/shared/release/use-release-info'

const KIND_TONE: Record<string, keyof typeof TONE_CLASS> = { them: 'done', sua: 'progress', bo: 'danger' }

/**
 * CÓ GÌ MỚI — `/whats-new` (bao-CR-722). Dùng chung mọi phân hệ nên nằm ở khung launcher như Trang cá nhân.
 *
 * Mở trang là đánh dấu đã xem bản đang chạy (chấm đỏ ở chân menu tắt). Ghi im lặng: hỏng mạng thì lần sau ghi lại.
 */
export function WhatsNewPage() {
  const { data, isLoading, isError } = useReleaseNotes()
  const { unseen, version } = useReleaseUnseen()
  const markSeen = useMarkReleaseSeen()
  const [module, setModule] = useState('')

  const currentVersion = version?.version
  useEffect(() => {
    if (unseen && currentVersion) markSeen.mutate(currentVersion)
    //  Chỉ chạy khi phiên bản đang chạy đã biết và còn chưa xem — không lặp theo mutate.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unseen, currentVersion])

  const releases = useMemo(() => filterReleases(data?.releases ?? [], module), [data, module])

  return (
    <PageContainer>
      <PageHeader
        title="Có gì mới"
        description={runningVersionText(data?.version ?? version, env.buildCommit)}
        actions={
          <Select value={module || 'all'} onValueChange={(v) => setModule(v === 'all' ? '' : v)}>
            <SelectTrigger size="sm" className="w-52" aria-label="Phân hệ">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Mọi phân hệ</SelectItem>
              {(data?.modules ?? []).map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />

      {isLoading && <Skeleton className="h-64 w-full" />}
      {isError && <p className="text-sm text-destructive">Không tải được ghi chú phát hành.</p>}
      {data && releases.length === 0 && (
        <p className="text-sm text-muted-foreground">Không có thay đổi nào của phân hệ này trong các đợt gần đây.</p>
      )}

      <div className="space-y-4">
        {releases.map((rel, idx) => (
          <Card key={rel.version} className="p-5">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h2 className="text-lg font-semibold">
                {idx === 0 && !module && <Sparkles className="mr-1.5 inline size-4 text-warning" aria-hidden />}
                Bản {rel.version}
              </h2>
              <span className="text-sm text-muted-foreground">{formatDate(rel.date) || rel.date}</span>
              {idx === 0 && !module && <Badge variant="secondary">Mới nhất</Badge>}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{rel.title}</p>
            <ul className="mt-3 space-y-2">
              {rel.notes.map((n, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <Badge className={cn('mt-0.5 shrink-0', TONE_CLASS[KIND_TONE[n.kind] ?? 'neutral'])}>
                    {n.kind_label}
                  </Badge>
                  <span>
                    <span className="font-medium">{n.module}</span>
                    <span className="text-muted-foreground"> · </span>
                    {n.text}
                    {n.cr && <span className="ml-1 font-mono text-xs text-muted-foreground">{n.cr}</span>}
                  </span>
                </li>
              ))}
            </ul>
            {rel.remarks.length > 0 && (
              <div className="mt-3 rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide">Lưu ý</p>
                <ul className="list-disc space-y-1 pl-5">
                  {rel.remarks.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </Card>
        ))}
      </div>
    </PageContainer>
  )
}
