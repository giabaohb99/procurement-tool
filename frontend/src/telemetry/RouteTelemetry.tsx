import { useEffect } from 'react'

import { useAuth } from '../auth/AuthContext'
import { installGlobalErrorCapture } from './error-capture'
import { installTelemetryLifecycle, telemetry } from './telemetry-queue'
import { useRouteTelemetry } from './use-route-telemetry'

/**
 * Không vẽ gì — gắn MỘT lần trong `layouts/AppLayout.tsx` (bao-CR-649, chép từ ERP v2 `route-telemetry.tsx`).
 * Bật bộ thu khi đã đăng nhập và hồ sơ không khai `usage_tracking === false` (mặc định BẬT; máy chủ tự trả 204
 * khi công tắc `usage_tracking_enabled` tắt). Trang in `/print/...` nằm ngoài AppLayout nên không đo — cố ý.
 */
export default function RouteTelemetry() {
  const { user } = useAuth()
  const enabled = !!user && user.usage_tracking !== false

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
