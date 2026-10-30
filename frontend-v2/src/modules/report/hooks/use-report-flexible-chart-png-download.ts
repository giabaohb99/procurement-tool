import { useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'

import { downloadChartPng, type ChartPngInput } from '../utils/report-flexible-chart-png'

/**
 * Nút "Tải ảnh PNG" của biểu đồ linh hoạt: giữ `ref` khung vẽ, chặn bấm đúp bằng `useRef`
 * (state `downloading` chỉ đúng ở lần render sau — bẫy thứ tư của biểu mẫu), lỗi thì toast.
 */
export function useReportFlexibleChartPngDownload() {
  const plotRef = useRef<HTMLElement>(null)
  const busyRef = useRef(false)
  const [downloading, setDownloading] = useState(false)

  const download = useCallback(async (input: Omit<ChartPngInput, 'container'>) => {
    const container = plotRef.current
    if (!container || busyRef.current) return
    busyRef.current = true
    setDownloading(true)
    try {
      await downloadChartPng({ ...input, container })
    } catch {
      toast.error('Không tải được ảnh biểu đồ. Thử lại hoặc chụp màn hình.')
    } finally {
      busyRef.current = false
      setDownloading(false)
    }
  }, [])

  return { plotRef, downloading, download }
}
