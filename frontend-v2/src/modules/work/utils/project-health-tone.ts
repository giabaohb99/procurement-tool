import { PROJECT_HEALTH } from '../hooks/use-work-overview'

/**
 * Màu nhãn sức khỏe dự án theo MÃ (nhãn chữ do backend trả, giao diện không tự dịch) — dùng chung cho bảng sức khỏe
 * dự án và khối theo dõi từng dự án của màn Tổng quan (duoc-CR-782).
 */
export const PROJECT_HEALTH_TONE: Record<number, string> = {
  [PROJECT_HEALTH.NO_TASKS]: 'border-border bg-muted text-muted-foreground',
  [PROJECT_HEALTH.ON_TRACK]: 'border-success/30 bg-success/10 text-success',
  [PROJECT_HEALTH.AT_RISK]: 'border-warning/30 bg-warning/10 text-warning',
  [PROJECT_HEALTH.LATE]: 'border-destructive/30 bg-destructive/10 text-destructive',
}
