import { useCallback, useEffect, useRef } from 'react'

import { getCurrentRoute, telemetry } from './telemetry-queue'
import { UI_EVENT, type UiFormCode } from './ui-event-codes'

/**
 * Đo vòng đời một biểu mẫu (chép từ ERP v2 `use-form-telemetry.ts`, bao-CR-649): `active` thành true → FORM_OPEN;
 * `markSubmitted()` → FORM_SUBMIT(duration); đóng/rời trang khi chưa gửi → FORM_ABANDON(duration).
 * `active=false` thì im hoàn toàn. Không đọc giá trị ô nhập.
 *
 * Ở app cũ, sau khi tạo xong trang `navigate('/x/<id>')` trên CÙNG component nên `isNew` chuyển false và cleanup
 * phát FORM_ABANDON — vì vậy phải gọi `markSubmitted()` NGAY sau POST thành công, TRƯỚC `navigate`.
 */
export function useFormTelemetry(form: UiFormCode, active: boolean) {
  const openedAt = useRef<number | null>(null)
  const done = useRef(false)

  const finish = useCallback(
    (type: typeof UI_EVENT.FORM_SUBMIT | typeof UI_EVENT.FORM_ABANDON) => {
      if (openedAt.current === null || done.current) return
      done.current = true
      telemetry.enqueue({
        type,
        route: getCurrentRoute(),
        form,
        duration_ms: Date.now() - openedAt.current,
      })
    },
    [form],
  )

  useEffect(() => {
    if (!active) return
    openedAt.current = Date.now()
    done.current = false
    telemetry.enqueue({ type: UI_EVENT.FORM_OPEN, route: getCurrentRoute(), form })
    const offHide = telemetry.onPageHide(() => finish(UI_EVENT.FORM_ABANDON))
    return () => {
      offHide()
      finish(UI_EVENT.FORM_ABANDON)
      openedAt.current = null
    }
  }, [active, form, finish])

  const markSubmitted = useCallback(() => finish(UI_EVENT.FORM_SUBMIT), [finish])
  return { markSubmitted }
}
