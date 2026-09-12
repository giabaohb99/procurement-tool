import { Check } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { SurveyRequestReport } from '../../types/survey-request-report'
import {
  filterReportDocs,
  isReportDocDone,
  reportPercent,
  trackingMarkers,
} from '../../utils/survey-report-helpers'

interface SurveyReportTrackingProps {
  report: SurveyRequestReport
  /** Nút dòng hàng đang lọc (`REPORT_FILTER_ALL` = tất cả). */
  itemFilter: number
  className?: string
}

/**
 * Khung TRACKING dọc của khối báo cáo: mỗi giai đoạn một điểm từ trên xuống.
 *
 * Điểm NHẤP NHÁY = giai đoạn hiện tại của track đang xem. Ở «Tất cả», mỗi nút
 * dòng hàng có track riêng nên có thể nhiều điểm cùng nháy — huy hiệu trên
 * điểm ghi SỐ THỨ TỰ nút (1, 2…), nhiều nút đứng cùng giai đoạn thì ghi «+n»
 * (rê chuột đọc tên đầy đủ). Track dựa theo bộ lọc NÚT, cố ý bỏ qua ô tìm kiếm
 * và bộ lọc trạng thái — tiến độ thật không đổi theo từ khóa đang gõ.
 */
export function SurveyReportTracking({ report, itemFilter, className }: SurveyReportTrackingProps) {
  if (!report.phases.length) return null
  const scopeDocs = filterReportDocs(report.docs, itemFilter)
  const markersByPhase = new Map(
    trackingMarkers(report, itemFilter).map((marker) => [marker.phaseId, marker]),
  )

  return (
    <div className={cn('h-fit rounded-lg border bg-muted/20 p-3 lg:sticky lg:top-4', className)}>
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Tiến trình
      </p>
      <ol className="relative space-y-4">
        <span aria-hidden className="absolute top-2 bottom-2 left-[11px] w-px bg-border" />
        {report.phases.map((phase, index) => {
          const phaseDocs = scopeDocs.filter((doc) => doc.phase_id === phase.id)
          const doneCount = phaseDocs.filter(isReportDocDone).length
          const done = phaseDocs.length > 0 && doneCount === phaseDocs.length
          const marker = markersByPhase.get(phase.id)
          return (
            <li key={phase.id} className="relative flex items-start gap-2.5">
              <span
                title={marker?.names.length ? `Đang ở đây: ${marker.names.join(', ')}` : undefined}
                className={cn(
                  'relative z-10 grid size-6 shrink-0 place-items-center rounded-full border-2 bg-card text-[11px] font-semibold',
                  done
                    ? 'border-success bg-success text-white'
                    : marker
                      ? 'border-warning text-warning'
                      : 'border-border text-muted-foreground',
                )}
              >
                {marker && (
                  <span aria-hidden className="absolute inset-0 animate-ping rounded-full bg-warning/40" />
                )}
                <span className="relative">
                  {done ? <Check className="size-3.5" /> : index + 1}
                </span>
                {marker?.label && (
                  <span className="absolute -top-2 -right-2 z-20 grid min-w-4 place-items-center rounded-full bg-warning px-1 text-[9px] leading-4 font-bold text-white">
                    {marker.label}
                  </span>
                )}
              </span>
              <div className="min-w-0 pt-0.5">
                <p
                  className={cn(
                    'truncate text-xs font-medium',
                    marker ? 'text-foreground' : 'text-muted-foreground',
                  )}
                >
                  {phase.name}
                </p>
                <p className="text-[11px] tabular-nums text-muted-foreground">
                  {phaseDocs.length
                    ? `${doneCount}/${phaseDocs.length} hồ sơ · ${reportPercent(phaseDocs)}%`
                    : 'Chưa có hồ sơ'}
                </p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
