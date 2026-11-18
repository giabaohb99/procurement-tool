import { CHART_COLORS, CHART_NEUTRAL, ChartCard } from '@/shared/ui/chart'
import { DonutChart, type DonutSlice } from '@/shared/ui/donut-chart'
import {
  StackedColumnLineChart,
  type ComboDatum,
  type ComboSeries,
} from '@/shared/ui/stacked-column-line-chart'

import type { WorkOverview } from '../hooks/use-work-overview'

/** Số hạng mục tối đa mỗi biểu đồ cột — nhiều hơn thì chữ trục chồng nhau, phần đuôi toàn hạng mục một hai việc. */
const TOP_PROJECTS = 8
const TOP_PEOPLE = 10

/**
 * Màu theo NGHĨA, cố định cho cả màn (không theo thứ hạng): quá hạn luôn đỏ, sắp tới hạn luôn cam, còn hạn luôn xanh
 * lá, chưa đặt hạn luôn xám; phần "chưa quá hạn" của cột màu phân loại thứ nhất (xanh dương), đường "đã xong" màu phân
 * loại thứ ba (xanh ngọc).
 *
 * Đã chạy bộ kiểm màu (dataviz `validate_palette.js`, nền sáng #fff và nền tối #1e293b):
 * - cột đỏ + xanh dương + đường xanh ngọc: đạt mọi mục ở cả hai nền. Bản đầu cho đường màu xanh lá trạng thái thì
 *   trượt ở nền tối — đỏ ↔ xanh lá chỉ cách ΔE 5,0 với người mù màu đỏ-lục, dưới mức sàn 6;
 * - vòng tình trạng: xanh lá ↔ cam ở mức sàn (ΔE 6,2) và xám tương phản thấp — hợp lệ vì vòng có khe 2px giữa lát và
 *   chú giải ghi chữ + số + %.
 */
const COLOR = {
  overdue: 'var(--destructive)',
  dueSoon: 'var(--warning)',
  onTrack: 'var(--success)',
  noDue: CHART_NEUTRAL,
  openRest: CHART_COLORS[0],
  done: CHART_COLORS[2],
} as const

/** Phần cột: việc đang mở tách quá hạn (chân cột, đỏ) và phần còn lại. */
const OPEN_BARS: ComboSeries[] = [
  { key: 'overdue', label: 'Đang mở · quá hạn', color: COLOR.overdue },
  { key: 'rest', label: 'Đang mở · chưa quá hạn', color: COLOR.openRest },
]

interface ChartProps {
  data: WorkOverview | undefined
  periodDays: number
  isLoading: boolean
}

/*
 * Ba thẻ biểu đồ của màn Tổng quan Dự án (duoc-CR-782), mỗi thẻ trả lời MỘT câu hỏi của người quản lý và đứng ở tab
 * của chủ đề đó (bố cục ba tab anh Được chọn 18/11/2026):
 * - tab Tổng quan: việc đang mở khỏe cỡ nào (vòng tình trạng);
 * - tab Dự án: dự án nào đang dồn việc, trễ ở đâu, làm ra bao nhiêu (cột chồng việc mở + đường việc xong trong kỳ);
 * - tab Nhân sự: ai đang ôm nhiều mà làm ra ít (cùng kiểu, theo người).
 *
 * Cột + đường chung MỘT trục vì cùng đơn vị "việc".
 */

/** Tình trạng việc đang mở: quá hạn / đến hạn 7 ngày / còn hạn / chưa đặt hạn. */
export function WorkOverviewStatusChart({ data, isLoading }: Omit<ChartProps, 'periodDays'>) {
  const overdue = data?.task_overdue ?? 0
  const dueSoon = data?.task_due_soon ?? 0
  const noDue = data?.task_no_due ?? 0
  const onTrack = Math.max((data?.task_open ?? 0) - overdue - dueSoon - noDue, 0)
  //  Đủ bốn phần, cả phần bằng 0: chú giải "Quá hạn 0" là một câu trả lời, giấu đi thì người đọc phải đoán.
  const status: DonutSlice[] = [
    { label: 'Quá hạn', value: overdue, color: COLOR.overdue },
    { label: 'Đến hạn trong 7 ngày', value: dueSoon, color: COLOR.dueSoon },
    { label: 'Còn hạn', value: onTrack, color: COLOR.onTrack },
    { label: 'Chưa đặt hạn', value: noDue, color: COLOR.noDue },
  ]
  return (
    <ChartCard
      title="Tình trạng việc đang mở"
      description="Việc chưa xong chia theo hạn: quá hạn, đến hạn trong 7 ngày, còn hạn, chưa đặt hạn."
      loading={isLoading}
      isEmpty={(data?.task_open ?? 0) === 0}
      emptyLabel="Không có việc nào đang mở."
    >
      <DonutChart data={status} centerLabel="việc mở" unit="việc" />
    </ChartCard>
  )
}

/** Dự án: cột việc đang mở (phần đỏ quá hạn) + đường việc xong trong kỳ. */
export function WorkOverviewProjectChart({ data, periodDays, isLoading }: ChartProps) {
  //  Dự án có việc mở HOẶC có việc xong trong kỳ — dự án không động tĩnh gì thì không có gì để vẽ. Đường là việc xong
  //  TRONG KỲ, không phải tổng từ trước tới nay: tổng đó lớn gấp nhiều lần việc mở, chung một trục là cột bị bẹp.
  const byProject: ComboDatum[] = (data?.projects ?? [])
    .filter((p) => p.open > 0 || p.done_in_period > 0)
    .sort((a, b) => b.open - a.open || b.done_in_period - a.done_in_period)
    .slice(0, TOP_PROJECTS)
    .map((p) => ({
      label: p.name,
      values: { overdue: p.overdue, rest: p.open - p.overdue, done: p.done_in_period },
    }))
  return (
    <ChartCard
      title="Dự án: đang mở và làm ra"
      description={`${TOP_PROJECTS} dự án nhiều việc mở nhất. Cột: việc đang mở (đỏ là quá hạn). Đường: việc xong trong ${periodDays} ngày.`}
      loading={isLoading}
      isEmpty={byProject.length === 0}
      emptyLabel="Chưa dự án nào có việc."
    >
      <StackedColumnLineChart
        data={byProject}
        bars={OPEN_BARS}
        line={{ key: 'done', label: `Xong trong ${periodDays} ngày`, color: COLOR.done }}
        unit="việc"
      />
    </ChartCard>
  )
}

/** Theo người: cột việc đang mở (phần đỏ quá hạn) + đường việc xong trong kỳ. */
export function WorkOverviewPeopleChart({ data, periodDays, isLoading }: ChartProps) {
  const byPerson: ComboDatum[] = (data?.people ?? [])
    .filter((p) => p.open > 0 || p.done_in_period > 0)
    .sort((a, b) => b.open - a.open || b.done_in_period - a.done_in_period)
    .slice(0, TOP_PEOPLE)
    .map((p) => ({
      label: p.name || `Nhân sự #${p.employee_id}`,
      values: { overdue: p.overdue, rest: p.open - p.overdue, done: p.done_in_period },
    }))
  return (
    <ChartCard
      title="Theo người: đang giữ và làm ra"
      description={`${TOP_PEOPLE} người đang giữ nhiều việc nhất. Cột: việc đang mở (đỏ là quá hạn). Đường: việc xong trong ${periodDays} ngày.`}
      loading={isLoading}
      isEmpty={byPerson.length === 0}
      emptyLabel="Chưa có việc nào được giao cho ai."
    >
      <StackedColumnLineChart
        data={byPerson}
        bars={OPEN_BARS}
        line={{ key: 'done', label: `Xong trong ${periodDays} ngày`, color: COLOR.done }}
        unit="việc"
      />
    </ChartCard>
  )
}
