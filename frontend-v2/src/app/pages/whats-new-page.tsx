import { Sparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { env } from '@/core/config/env'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/shared/ui/accordion'
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
 * Danh sách THU GỌN (đại ca chốt 04/11): mỗi đợt một dòng "Bản X · ngày · tiêu đề", bấm sổ xuống; đợt mới nhất mở
 * sẵn, các đợt khác đóng. Mã CR của từng dòng KHÔNG hiện — người dùng chỉ cần biết đổi gì; `cr` giữ trong JSON cho
 * nội bộ tra.
 *
 * Mở trang là đánh dấu đã xem bản đang chạy (chấm đỏ tắt). Ghi im lặng: hỏng mạng thì lần sau ghi lại.
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
  //  `key` theo danh sách đang hiện: đổi bộ lọc là dựng lại accordion để đợt đầu của danh sách mới mở sẵn.
  const accordionKey = releases.map((r) => r.version).join('|')

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

      {releases.length > 0 && (
        <Card className="px-5 py-1">
          <Accordion key={accordionKey} type="multiple" defaultValue={[releases[0].version]}>
            {releases.map((rel, idx) => (
              <AccordionItem key={rel.version} value={rel.version}>
                <AccordionTrigger aria-label={`Bản ${rel.version}`}>
                  <span className="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-1">
                    <span className="font-semibold">
                      {idx === 0 && !module && (
                        <Sparkles className="mr-1.5 inline size-4 text-warning" aria-hidden />
                      )}
                      Bản {rel.version}
                    </span>
                    <span className="text-muted-foreground">· {formatDate(rel.date) || rel.date}</span>
                    <span className="font-normal text-muted-foreground">· {rel.title}</span>
                    {idx === 0 && !module && <Badge variant="secondary">Mới nhất</Badge>}
                  </span>
                </AccordionTrigger>
                <AccordionContent>
                  <ul className="space-y-2">
                    {rel.notes.map((n, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <Badge className={cn('mt-0.5 shrink-0', TONE_CLASS[KIND_TONE[n.kind] ?? 'neutral'])}>
                          {n.kind_label}
                        </Badge>
                        <span>
                          <span className="font-medium">{n.module}</span>
                          <span className="text-muted-foreground"> · </span>
                          {n.text}
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
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </Card>
      )}
    </PageContainer>
  )
}
