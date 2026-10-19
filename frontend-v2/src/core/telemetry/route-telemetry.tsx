import { useEffect } from 'react'

import { useAuth } from '@/core/auth/use-auth'

import { installGlobalErrorCapture } from './install-global-error-capture'
import { installTelemetryLifecycle, telemetry } from './telemetry-queue'
import { useRouteTelemetry } from './use-route-telemetry'
import { env } from '@/core/config/env'

/**
 * Không vẽ gì — gắn MỘT lần trong `protected-route.tsx`. Bật bộ thu khi đã đăng
 * nhập và hồ sơ không khai `usage_tracking === false` (mặc định BẬT; máy chủ có
 * thể tự trả 204 khi công tắc tắt). Môi trường test: tắt hẳn.
 */
export function RouteTelemetry() {
  const { user } = useAuth()
  const enabled = !!user && user.usage_tracking !== false && !env.isTest

  useEffect(() => {
    telemetry.setEnabled(enabled)
    if (enabled) {
      installTelemetryLifecycle()
      installGlobalErrorCapture()
    }
  }, [enabled])

  useRouteTelemetry()
  return null
}
