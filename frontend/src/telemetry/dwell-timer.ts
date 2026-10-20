/**
 * Cộng dồn thời gian ở lại một màn — CHỈ tính lúc tab đang hiện (chép từ ERP v2 `core/telemetry/dwell-timer.ts`,
 * bao-CR-649). Thuần: đồng hồ và trạng thái hiển thị được truyền vào.
 */
export function createDwellTimer(now: () => number, initiallyVisible: boolean) {
  let accumulated = 0
  let visibleSince: number | null = initiallyVisible ? now() : null

  return {
    setVisible(visible: boolean) {
      if (visible && visibleSince === null) visibleSince = now()
      else if (!visible && visibleSince !== null) {
        accumulated += now() - visibleSince
        visibleSince = null
      }
    },
    /** Số ms đã cộng dồn tới giờ (không đặt lại). */
    elapsed(): number {
      return accumulated + (visibleSince === null ? 0 : now() - visibleSince)
    },
    /** Đọc rồi đặt lại về 0 — dùng khi sang màn mới. */
    take(): number {
      const value = this.elapsed()
      accumulated = 0
      if (visibleSince !== null) visibleSince = now()
      return value
    },
  }
}

export type DwellTimer = ReturnType<typeof createDwellTimer>
