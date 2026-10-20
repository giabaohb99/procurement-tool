import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

import { createDwellTimer } from './dwell-timer'
import { toRoutePattern } from './route-pattern'
import { setCurrentRoute, telemetry } from './telemetry-queue'
import { UI_EVENT } from './ui-event-codes'

/**
 * Mỗi lần đổi màn: PAGE_LEAVE (màn cũ, duration = thời gian tab đang hiện) rồi PAGE_VIEW (màn mới). `pagehide` →
 * PAGE_LEAVE cho màn đang mở. Chép từ ERP v2 (bao-CR-649); khác v2: app cũ dùng `BrowserRouter` nên không có
 * `useMatches`, route mẫu dựng từ `pathname` bằng lưới an toàn (xem `route-pattern.ts`).
 */
export function useRouteTelemetry() {
  const location = useLocation()
  const dwell = useRef<ReturnType<typeof createDwellTimer> | null>(null)
  const current = useRef<string | null>(null)
  const pattern = toRoutePattern(location.pathname)

  useEffect(() => {
    if (!dwell.current) dwell.current = createDwellTimer(() => Date.now(), document.visibilityState !== 'hidden')
    const timer = dwell.current
    const onVisibility = () => timer.setVisible(document.visibilityState !== 'hidden')
    document.addEventListener('visibilitychange', onVisibility)
    const offHide = telemetry.onPageHide(() => {
      if (current.current) {
        telemetry.enqueue({ type: UI_EVENT.PAGE_LEAVE, route: current.current, duration_ms: timer.take() })
        current.current = null
      }
    })
    return () => {
      document.removeEventListener('visibilitychange', onVisibility)
      offHide()
    }
  }, [])

  useEffect(() => {
    const timer = dwell.current
    if (!timer || current.current === pattern) return
    if (current.current) {
      telemetry.enqueue({ type: UI_EVENT.PAGE_LEAVE, route: current.current, duration_ms: timer.take() })
    } else {
      timer.take()
    }
    current.current = pattern
    setCurrentRoute(pattern)
    telemetry.enqueue({ type: UI_EVENT.PAGE_VIEW, route: pattern })
  }, [pattern])
}
