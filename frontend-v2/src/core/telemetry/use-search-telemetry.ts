import { useEffect, useRef } from 'react'

import { getCurrentRoute, telemetry } from './telemetry-queue'
import { UI_EVENT } from './ui-event-codes'

/**
 * Báo một SEARCH khi kết quả của từ khóa MỚI về: chỉ gửi route + SỐ kết quả.
 * Từ khóa KHÔNG BAO GIỜ rời hook này (không hash, không độ dài) — nó chỉ được
 * so với từ khóa liền trước để khỏi báo trùng.
 */
export function useSearchTelemetry(query: string, total: number | undefined, isFetching: boolean) {
  const lastReported = useRef<string | null>(null)
  const trimmed = query.trim()

  useEffect(() => {
    if (!trimmed) {
      lastReported.current = null
      return
    }
    if (isFetching || total === undefined || lastReported.current === trimmed) return
    lastReported.current = trimmed
    telemetry.enqueue({ type: UI_EVENT.SEARCH, route: getCurrentRoute(), result_count: total })
  }, [trimmed, total, isFetching])
}
