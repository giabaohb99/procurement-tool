import { Newspaper, Trash2 } from 'lucide-react'
import { useRef } from 'react'

import { botBriefApi, type BriefItem } from '@/modules/system/api/bot-memory-api'
import { useBotBriefAction, useBotBriefs } from '@/modules/system/hooks/use-bot-memory'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { Switch } from '@/shared/ui/switch'

/**
 * Thẻ «Bản tin bot tự gửi» (ai-CR-140) trong tab «Bot nhớ gì về tôi».
 *
 * Bật / tắt cũng làm được ngay trong chat («bật bản tin», «tắt bản tin 2», «sáng thứ hai gửi anh công nợ quá hạn») — thẻ
 * này chỉ để nhìn tổng và bấm nhanh. Bản tin sáng ngầm (người đã nối Google mà chưa tự đặt) có `id` 0: bật / tắt đi
 * đường `daily`, không đi đường theo id.
 */
export function ProfileBriefCard() {
  const { data, isLoading } = useBotBriefs()
  const busy = useRef(false)
  const setDaily = useBotBriefAction(botBriefApi.setDaily, 'Đã lưu bản tin sáng.')
  const toggle = useBotBriefAction(botBriefApi.toggle, 'Đã lưu.')
  const remove = useBotBriefAction(botBriefApi.remove, 'Đã bỏ bản tin.')

  async function once(run: () => Promise<unknown>) {
    if (busy.current) return
    busy.current = true
    try {
      await run()
    } catch {
      //  Lỗi đã hiện toast ở tầng API.
    } finally {
      busy.current = false
    }
  }

  function onToggle(item: BriefItem, enabled: boolean) {
    void once(() =>
      item.kind === 1 ? setDaily.mutateAsync({ enabled }) : toggle.mutateAsync({ id: item.id, enabled }),
    )
  }

  return (
    <Card>
      <CardHeader>
        <SectionHeading>Bản tin bot tự gửi</SectionHeading>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {isLoading || !data ? (
          <Skeleton className="h-16" />
        ) : (
          <ul className="divide-y rounded-md border">
            {data.items.map((item) => (
              <li key={`${item.kind}-${item.id}`} className="flex items-center justify-between gap-2 px-3 py-2">
                <div className="flex items-start gap-2">
                  <Newspaper className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                  <div>
                    <div>{item.kind === 1 ? item.label : item.topic}</div>
                    <div className="text-xs text-muted-foreground">
                      {item.when}
                      {item.kind === 1 && ' · lịch, việc riêng, việc Dự án tới hạn, phiếu chờ duyệt'}
                    </div>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <Switch
                    checked={item.enabled}
                    aria-label={`${item.enabled ? 'Tắt' : 'Bật'}: ${item.kind === 1 ? item.label : item.topic}`}
                    onCheckedChange={(v) => onToggle(item, v)}
                  />
                  {item.kind === 2 && (
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      aria-label={`Bỏ bản tin: ${item.topic}`}
                      onClick={async () => {
                        const ok = await confirm({ title: 'Bỏ bản tin', message: `Bỏ bản tin «${item.topic}»?`, confirmLabel: 'Bỏ' })
                        if (ok) void once(() => remove.mutateAsync(item.id))
                      }}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
        <p className="text-muted-foreground">
          Trong chat với bot nhắn: bật bản tin · tắt bản tin · bản tin lúc 6h45 ngày thường · bản tin hôm nay · hoặc nói tự
          nhiên «sáng thứ hai gửi anh công nợ quá hạn của DEGO».
        </p>
      </CardContent>
    </Card>
  )
}
