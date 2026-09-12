import { CalendarDays, Columns3, Rows3, Search, Sigma, X } from 'lucide-react'
import { Fragment, useMemo, useState, type CSSProperties, type ReactNode } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatPercent } from '@/shared/utils/format-money'
import { useReportRange } from '../hooks/use-purchase-report'
import {
  ALL_PERIOD,
  isWarnRow,
  metricValue,
  NAME_SORT_KEY,
  nextSort,
  RATE_METRIC,
  type MatrixRow,
  type ReportMetric,
  type ReportMonth,
  type ReportSort,
} from '../types/purchase-report'
import { ReportMetricTable } from './report-metric-table'

/**
 * Sáu tông xoay vòng cho các cụm cột tháng.
 *
 * Bảng "Ngang" rộng tới 12 tháng × 5 chỉ số; không chia cụm màu thì mắt trượt
 * sang cột tháng bên cạnh lúc nào không biết. Lấy đúng sáu tông của bảng màu tô
 * cột (`COLUMN_COLORS`) cho cả hệ cùng một gam, và pha bằng `color-mix` với nền
 * nguyên bản để ra màu ĐỤC — ô cột tên bị ghim, nền có alpha là lộ phần bảng
 * cuộn ngang phía dưới.
 */
const MONTH_TONES = ['#2563eb', '#16a34a', '#d97706', '#7c3aed', '#dc2626', '#0891b2']

function toneStyle(color: string, part: 'head' | 'cell'): CSSProperties {
  const [ratio, base] = part === 'head' ? ['20%', 'var(--muted)'] : ['8%', 'var(--card)']
  return { backgroundColor: `color-mix(in oklab, ${color} ${ratio}, ${base})` }
}

function monthStyle(index: number, part: 'head' | 'cell'): CSSProperties {
  return toneStyle(MONTH_TONES[index % MONTH_TONES.length], part)
}

/** Cụm "Tổng cả năm" — xám trung tính để tách hẳn khỏi dải màu tháng. */
const TOTAL_HEAD_STYLE: CSSProperties = { backgroundColor: 'var(--muted)' }
const TOTAL_CELL_STYLE: CSSProperties = {
  backgroundColor: 'color-mix(in oklab, var(--chart-neutral) 22%, var(--card))',
}

/** Nền đục cho ô cột tên bị ghim. */
const STICKY_HEAD_STYLE: CSSProperties = { backgroundColor: 'var(--muted)' }
const STICKY_CELL_STYLE: CSSProperties = { backgroundColor: 'var(--card)' }

interface ReportMatrixTabProps {
  rows: MatrixRow[]
  months: ReportMonth[]
  metrics: ReportMetric[]
  nameLabel: string
  title: string
  /** Chú thích ngưỡng cảnh báo, vd "đỏ = tỷ lệ trễ > 30%". Bỏ trống = bảng không tô cảnh báo. */
  warnHint?: string
  /** Nhãn kỳ đang xem, vd "Năm 2026" — dùng cho tiêu đề và bản in. */
  yearLabel: string
  /** Đường dẫn tính realtime theo khoảng ngày, vd `/api/reports/sup-range`. */
  rangeEndpoint: string
  /** Chỉ dùng cho báo cáo yêu cầu: `pyc` | `ycks`. */
  rangeKind?: string
  companyId?: string
  /** Bề rộng cột tên — tên NCC dài hơn tên bộ phận nhiều. */
  nameWidth?: number
  isLoading?: boolean
}

/**
 * Tab báo cáo ma trận (đối tượng × tháng), dùng chung cho NCC / phân loại / nhân
 * sự phụ trách / bộ phận / yêu cầu.
 *
 * Ba chế độ xem:
 *  - **Ngang** — pivot: mỗi đối tượng một dòng, mỗi tháng một cụm cột, cuối cùng
 *    là cụm "Tổng cả năm".
 *  - **Dọc** — khối tổng cả năm rồi lần lượt từng khối tháng (hợp để in / đọc
 *    trên màn hẹp).
 *  - **Khoảng ngày** — gọi backend tính lại theo đúng hai mốc ngày, trả về một
 *    bảng phẳng; lúc này hai chế độ trên tạm ẩn vì số liệu không còn cắt theo
 *    tháng nữa.
 *
 * Khác bản v1 hai chỗ: ô lọc theo tên là ô GÕ (v1 là dropdown chọn đúng một đối
 * tượng — v2 chưa có select tìm kiếm được, mà gõ để lọc còn rộng hơn: gõ vài
 * chữ là ra cả nhóm), và bản in dùng `print:` của Tailwind thay cho hai lớp
 * `screen-only` / `print-only` của v1.
 */
export function ReportMatrixTab({
  rows,
  months,
  metrics,
  nameLabel,
  title,
  warnHint,
  yearLabel,
  rangeEndpoint,
  rangeKind,
  companyId,
  nameWidth = 150,
  isLoading = false,
}: ReportMatrixTabProps) {
  const isMobile = useIsMobile()

  /**
   * ⚠️ **Khổ điện thoại mở sẵn chế độ DỌC.** Bảng "Ngang" là pivot 12 tháng ×
   * 5 chỉ số — đo ở 390px là **41 cột, rộng 2896px trong khung 324px**, tức
   * nhìn thấy đúng cột tên cộng nửa cột số. Chế độ "Dọc" tách thành từng khối
   * tháng rộng ~500px, vẫn phải kéo ngang nhưng là kéo trong một bảng đọc được.
   * Ghi chú gốc của component đã nói Dọc *"hợp để in / đọc trên màn hẹp"* —
   * đây chỉ là để nó tự chọn đúng thay vì bắt người dùng đi tìm.
   *
   * Khởi tạo một lần rồi thôi: đổi theo `isMobile` ở mỗi lần render thì người
   * xoay ngang máy mất luôn chế độ họ vừa chọn tay.
   */
  const [view, setView] = useState<'ngang' | 'doc'>(() => (isMobile ? 'doc' : 'ngang'))

  /**
   * Cột tên phải hẹp lại ở khổ điện thoại. `nameWidth` khai theo màn rộng (tên
   * NCC 260px); giữ nguyên thì cột tên nuốt **260/324px** khung nhìn và không
   * còn chỗ cho lấy một cột số — người dùng kéo ngang mà không bao giờ thấy
   * tên đi cùng con số.
   *
   * ⚠️ **140 đi CÙNG `line-clamp-3` ở `ReportMetricTable`, đừng tách đôi.** Đã
   * thử bản «rộng hơn, ít dòng hơn» (170px × 2 dòng, cùng ~44 ký tự trên giấy):
   * hỏng cả hai đầu — chữ ngắt theo TỪ nên mỗi dòng chỉ dùng hết ~16 ký tự, ba
   * nhà cung cấp lại ra cùng một câu «CÔNG TY TNHH SẢN XUẤT BAO BÌ ĐÔNG…», mà
   * cột *Số lần giao dịch* thì bị đẩy quá mép phải, «65» hiện thành «6». Hẹp +
   * ba dòng vừa nhận ra tên vừa còn chỗ cho một cột số trọn vẹn.
   */
  const shownNameWidth = isMobile ? Math.min(nameWidth, 140) : nameWidth
  const [rangeFrom, setRangeFrom] = useState('')
  const [rangeTo, setRangeTo] = useState('')
  /** Khoảng ngày ĐÃ bấm "Xem". `null` = đang xem cả năm theo tháng. */
  const [applied, setApplied] = useState<{ from: string; to: string } | null>(null)
  const [keyword, setKeyword] = useState('')
  const [sort, setSort] = useState<ReportSort | null>(null)
  /**
   * Tháng đang hiện. `null` = NGƯỜI DÙNG CHƯA CHỌN TAY, lấy mặc định suy từ
   * `months`. Không thể chốt mặc định một lần lúc dựng component như v1: ở đây
   * `months` về sau react-query nên lần dựng đầu nó còn rỗng, chốt lúc đó là ẩn
   * sạch mọi tháng.
   */
  const [visibleMonths, setVisibleMonths] = useState<Set<string> | null>(null)

  const rangeQuery = useReportRange(
    rangeEndpoint,
    {
      date_from: applied?.from ?? '',
      date_to: applied?.to ?? '',
      company_id: companyId,
      kind: rangeKind,
    },
    applied !== null,
  )

  // Bọc `useMemo` chứ không tính thẳng: `?? []` đẻ mảng mới mỗi lần render, làm
  // `shownRows` phía dưới tính lại liên tục dù dữ liệu không đổi.
  const baseRows = useMemo(
    () => (applied ? (rangeQuery.data ?? []) : rows),
    [applied, rangeQuery.data, rows],
  )
  const shownRows = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    if (!needle) return baseRows
    return baseRows.filter((row) => row.key.toLowerCase().includes(needle))
  }, [baseRows, keyword])

  const defaultMonths = useMemo(() => defaultVisibleMonths(months), [months])
  const visible = visibleMonths ?? defaultMonths
  //  `useMemo` chứ không lọc thẳng: `filter` đẻ mảng mới mỗi lần render, mà
  //  `monthBlocks` bên dưới nhận nó làm phụ thuộc — không bọc thì memo kia tính
  //  lại ở mọi lượt render và coi như không có.
  const shownMonths = useMemo(
    () => months.filter((month) => visible.has(month.key)),
    [months, visible],
  )

  /**
   * Các khối tháng của chế độ "Dọc" — **tháng không phát sinh thì bỏ hẳn khối**.
   *
   * Trước đây tháng rỗng vẫn dựng đủ thẻ: viền màu, tiêu đề, hàng tiêu đề bảng
   * và một ô «Không có dữ liệu» — **~180px cho một thông tin bằng không**, và
   * ở khổ điện thoại (mở sẵn chế độ này) mấy tháng đầu năm thường rỗng nên
   * người dùng vuốt qua ba bốn thẻ trống trước khi tới số thật. Danh sách tháng
   * vẫn nguyên ở nút *Tháng: n/12*, nên không mất đường nào để kiểm chứng.
   *
   * Giữ `index` GỐC của tháng trong `shownMonths` để màu viền không đổi khi một
   * tháng ở giữa biến mất — sáu tông xoay vòng theo vị trí, lọc trước rồi mới
   * đánh số là cả dải màu trượt đi mỗi lần dữ liệu thay đổi.
   */
  const monthBlocks = useMemo(
    () =>
      shownMonths
        .map((month, index) => ({
          month,
          index,
          rows: shownRows.filter((row) => row.m?.[month.key]),
        }))
        .filter((block) => block.rows.length > 0),
    [shownMonths, shownRows],
  )

  /** Tháng đang bật nhưng không có dòng nào — chỉ để nói thành lời, không dựng khối. */
  const emptyMonths = shownMonths.filter(
    (month) => !monthBlocks.some((block) => block.month.key === month.key),
  )

  // Chỉ tô cảnh báo khi tab có khai ngưỡng — bảng đếm trạng thái yêu cầu không
  // có "tỷ lệ trễ" nào để mà vượt ngưỡng.
  const warnMetric = warnHint ? RATE_METRIC : undefined
  const canApply = !!rangeFrom && !!rangeTo && rangeFrom <= rangeTo

  function toggleMonth(key: string) {
    const next = new Set(visible)
    if (next.has(key)) next.delete(key)
    else next.add(key)
    setVisibleMonths(next)
  }

  function clearRange() {
    setApplied(null)
    setRangeFrom('')
    setRangeTo('')
  }

  function handleSort(key: string) {
    setSort((current) => nextSort(current, key))
  }

  const rangeLabel = applied ? `${formatDate(applied.from)} → ${formatDate(applied.to)}` : yearLabel

  return (
    <div className="flex flex-col gap-3">
      {/* ==== Thanh điều khiển ==== */}
      <div className="flex flex-wrap items-center gap-2 print:hidden">
        {!applied && (
          <div className="inline-flex overflow-hidden rounded-md border">
            <ViewButton
              active={view === 'ngang'}
              icon={<Columns3 className="size-4" />}
              label="Ngang"
              onClick={() => setView('ngang')}
            />
            <ViewButton
              active={view === 'doc'}
              icon={<Rows3 className="size-4" />}
              label="Dọc"
              onClick={() => setView('doc')}
            />
          </div>
        )}

        {!applied && months.length > 0 && (
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="gap-2">
                <CalendarDays className="size-4" />
                Tháng: {shownMonths.length}/{months.length}
              </Button>
            </PopoverTrigger>
            <PopoverContent align="start" className="w-56 p-2">
              <div className="mb-2 flex gap-2 border-b pb-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setVisibleMonths(new Set(months.map((month) => month.key)))}
                >
                  Tất cả
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setVisibleMonths(new Set())}>
                  Bỏ chọn
                </Button>
              </div>
              <div className="max-h-60 space-y-1 overflow-y-auto">
                {months.map((month) => (
                  <label
                    key={month.key}
                    className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-accent"
                  >
                    <Checkbox
                      checked={visible.has(month.key)}
                      onCheckedChange={() => toggleMonth(month.key)}
                    />
                    Tháng {month.label}
                  </label>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        )}

        <div className="ml-auto flex flex-wrap items-center gap-2 max-md:w-full">
          {/*  Ô tìm chiếm TRỌN hàng ở khổ hẹp: `min-w-48` (192px) đằng nào cũng
               không đứng chung được với hai ô ngày, nên để nó co theo nội dung
               thì chỉ được một mẩu 192px và một khoảng trống dài bên phải. */}
          <div className="relative min-w-48 max-md:w-full">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder={`Lọc theo ${nameLabel.toLowerCase()}…`}
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </div>

          {/*  ⚠️ Hai ô ngày + nút *Xem* phải nằm CÙNG một hàng ở khổ hẹp. Bề
               rộng cứng `w-40` (160px ×2 = 320px) vừa đúng khít 358px nên nút
               *Xem* bị đẩy xuống hàng thứ ba — một nút đứng trơ một mình, và
               tệ hơn là nó rời khỏi cặp ô mà nó dùng để làm gì. Cho hai ô co
               (`flex-1`) thì cả ba đứng chung: 141 + 141 + 60. */}
          <DatePicker
            value={rangeFrom}
            onChange={setRangeFrom}
            placeholder="Từ ngày"
            className="w-40 max-md:w-auto max-md:flex-1"
          />
          <DatePicker
            value={rangeTo}
            onChange={setRangeTo}
            placeholder="Đến ngày"
            className="w-40 max-md:w-auto max-md:flex-1"
          />
          <Button
            variant="secondary"
            disabled={!canApply}
            onClick={() => setApplied({ from: rangeFrom, to: rangeTo })}
          >
            Xem
          </Button>
          {applied && (
            <Button variant="ghost" className="gap-2" onClick={clearRange}>
              <X className="size-4" />
              Xóa lọc
            </Button>
          )}
        </div>
      </div>

      {/*  Dải sắp xếp chỉ mọc ở khổ điện thoại và chỉ khi có thẻ để mà sắp:
           chế độ «Ngang» vẫn là bảng pivot, tiêu đề cột của nó bấm được như cũ. */}
      {isMobile && (applied || view === 'doc') && (
        <MobileSortSelect
          metrics={metrics}
          nameLabel={nameLabel}
          sort={sort}
          onChange={setSort}
        />
      )}

      {/* ==== Trên màn hình ==== */}
      <div className="print:hidden">
        {applied ? (
          <Card className="p-4">
            <SectionTitle title={`${title} — ${rangeLabel}`} />
            {rangeQuery.isLoading ? (
              <LoadingLine />
            ) : (
              <ReportMetricTable
                rows={shownRows}
                metrics={metrics}
                period={ALL_PERIOD}
                nameLabel={nameLabel}
                warnMetric={warnMetric}
                nameWidth={shownNameWidth}
                sort={sort}
                onSort={handleSort}
              />
            )}
          </Card>
        ) : view === 'doc' ? (
          <div className="flex flex-col gap-3">
            <Card className="p-4">
              <SectionTitle
                title={`Tổng cả năm — ${yearLabel}`}
                hint={warnHint}
                icon={<Sigma className="size-4 text-primary" />}
              />
              {isLoading ? (
                <LoadingLine />
              ) : (
                <ReportMetricTable
                  rows={shownRows}
                  metrics={metrics}
                  period={ALL_PERIOD}
                  nameLabel={nameLabel}
                  warnMetric={warnMetric}
                  nameWidth={shownNameWidth}
                  sort={sort}
                  onSort={handleSort}
                />
              )}
            </Card>

            {monthBlocks.map(({ month, index, rows: monthRows }) => (
              <Card
                key={month.key}
                className="gap-0 overflow-hidden p-0"
                style={{ borderLeft: `4px solid ${MONTH_TONES[index % MONTH_TONES.length]}` }}
              >
                <h3
                  className="px-4 py-3 text-sm font-semibold text-navy dark:text-foreground"
                  style={monthStyle(index, 'head')}
                >
                  Tháng {month.label}
                </h3>
                <div className="p-4">
                  <ReportMetricTable
                    rows={monthRows}
                    metrics={metrics}
                    period={month.key}
                    nameLabel={nameLabel}
                    warnMetric={warnMetric}
                    nameWidth={shownNameWidth}
                    sort={sort}
                    onSort={handleSort}
                  />
                </div>
              </Card>
            ))}

            {/*  ⚠️ Nói ra tháng nào bị bỏ. Người dùng tự tick tháng ở nút
                 *Tháng: n/12*; tick xong mà không thấy khối nào hiện ra, không
                 có câu này thì đọc ra là màn hình lỗi chứ không phải là tháng
                 đó chưa phát sinh gì. */}
            {emptyMonths.length > 0 && (
              <p className="px-1 text-xs text-muted-foreground">
                Chưa phát sinh trong {emptyMonths.length} tháng:{' '}
                {emptyMonths.map((month) => month.label).join(' · ')}.
              </p>
            )}
          </div>
        ) : (
          <Card className="p-4">
            <SectionTitle
              title={`${title} — ${yearLabel}`}
              hint={`phân cụm theo tháng · cuộn ngang · cụm xám = tổng cả năm${
                warnHint ? ` · ${warnHint}` : ''
              }`}
            />
            {isLoading ? (
              <LoadingLine />
            ) : (
              <PivotTable
                rows={shownRows}
                months={shownMonths}
                metrics={metrics}
                nameLabel={nameLabel}
                nameWidth={shownNameWidth}
                warnMetric={warnMetric}
              />
            )}
          </Card>
        )}
      </div>

      {/* ==== Khi IN: bản tổng hợp một dòng một đối tượng ==== */}
      <div className="hidden print:block">
        <SectionTitle title={`${title} — ${rangeLabel}`} hint="bản tổng hợp" />
        <ReportMetricTable
          rows={shownRows}
          metrics={metrics}
          period={ALL_PERIOD}
          nameLabel={nameLabel}
          warnMetric={warnMetric}
          nameWidth={shownNameWidth}
        />
      </div>
    </div>
  )
}

/** Giá trị "chưa sắp xếp" của ô chọn — `SelectItem` không nhận value rỗng. */
const SORT_NONE = 'none'

/**
 * Ô chọn SẮP XẾP cho khổ điện thoại.
 *
 * Ở đó `ReportMetricTable` bày thẻ chứ không bày bảng, nên không còn hàng tiêu
 * đề để bấm. Đặt MỘT ô cho cả tab là đúng hơn bản cũ chứ không phải chữa cháy:
 * trạng thái sắp xếp vốn dùng chung cho mọi khối tháng, nên chín hàng tiêu đề
 * bấm được của chế độ «Dọc» thật ra là chín bản sao của cùng một cái công tắc.
 *
 * ⚠️ **MỘT ô chọn, không phải một dải nút tròn.** Bản đầu là bốn nút bo tròn và
 * hỏng hai đường: chúng chiếm **hai hàng ~70px** chồng lên bốn hàng công cụ đã
 * có, và — thấy rõ hơn — khi cuộn qua dải điều khiển đang ghim thì viền nút bị
 * **cắt ngang chính giữa**, đọc ra như lỗi vẽ chứ không như nội dung đang trôi
 * xuống dưới (khách báo 12/09/2026). Ô chọn thì trôi qua giống hệt hai ô *công
 * ty · năm* ngay trên nó, mắt đã quen, và chỉ tốn một hàng 36px.
 *
 * Chiều sắp xếp nằm luôn trong từng mục thay vì phải bấm hai lần đoán chiều.
 */
function MobileSortSelect({
  metrics,
  nameLabel,
  sort,
  onChange,
}: {
  metrics: ReportMetric[]
  nameLabel: string
  sort: ReportSort | null
  onChange: (next: ReportSort | null) => void
}) {
  const options = [{ key: NAME_SORT_KEY, label: nameLabel }, ...metrics]

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className="shrink-0">Sắp xếp:</span>
      <Select
        value={sort ? `${sort.key}:${sort.dir}` : SORT_NONE}
        onValueChange={(value) => {
          if (value === SORT_NONE) return onChange(null)
          const [key, dir] = value.split(':')
          onChange({ key, dir: dir as ReportSort['dir'] })
        }}
      >
        <SelectTrigger className="h-9 min-w-0 flex-1">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={SORT_NONE}>Mặc định</SelectItem>
          {options.map((option) => {
            //  Cột TÊN nói «A → Z», cột số nói «cao → thấp»: cùng là `asc` cả
            //  nhưng đọc lên phải khác nhau, không thì người dùng phải tự dịch.
            const isName = option.key === NAME_SORT_KEY
            return (
              <Fragment key={option.key}>
                <SelectItem value={`${option.key}:desc`}>
                  {option.label} — {isName ? 'Z → A' : 'cao → thấp'}
                </SelectItem>
                <SelectItem value={`${option.key}:asc`}>
                  {option.label} — {isName ? 'A → Z' : 'thấp → cao'}
                </SelectItem>
              </Fragment>
            )
          })}
        </SelectContent>
      </Select>
    </div>
  )
}

/** Pivot đối tượng (dòng) × tháng (cụm cột) + cụm "Tổng cả năm" ở cuối. */
function PivotTable({
  rows,
  months,
  metrics,
  nameLabel,
  nameWidth,
  warnMetric,
}: {
  rows: MatrixRow[]
  months: ReportMonth[]
  metrics: ReportMetric[]
  nameLabel: string
  nameWidth: number
  warnMetric?: string
}) {
  return (
    <Table className="min-w-[520px]">
      <TableHeader className="bg-muted">
        <TableRow className="hover:bg-muted">
          <TableHead
            rowSpan={2}
            className="sticky left-0 z-20 align-bottom"
            style={{ ...STICKY_HEAD_STYLE, width: nameWidth, minWidth: nameWidth }}
          >
            {nameLabel}
          </TableHead>
          {months.map((month, index) => (
            <TableHead
              key={month.key}
              colSpan={metrics.length}
              className="border-l text-center"
              style={monthStyle(index, 'head')}
            >
              Tháng {month.label}
            </TableHead>
          ))}
          <TableHead
            colSpan={metrics.length}
            className="border-l-2 text-center text-navy dark:text-foreground"
            style={TOTAL_HEAD_STYLE}
          >
            Tổng cả năm
          </TableHead>
        </TableRow>
        <TableRow className="hover:bg-muted">
          {months.map((month, index) =>
            metrics.map((metric, metricIndex) => (
              <TableHead
                key={`${month.key}-${metric.key}`}
                className={cn('text-right text-xs font-normal', metricIndex === 0 && 'border-l')}
                style={monthStyle(index, 'head')}
              >
                {metric.label}
              </TableHead>
            )),
          )}
          {metrics.map((metric, metricIndex) => (
            <TableHead
              key={`total-${metric.key}`}
              className={cn('text-right text-xs font-semibold', metricIndex === 0 && 'border-l-2')}
              style={TOTAL_HEAD_STYLE}
            >
              {metric.label}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>

      <TableBody>
        {rows.length === 0 && (
          <TableRow>
            <TableCell
              colSpan={1 + (months.length + 1) * metrics.length}
              className="h-20 text-center text-muted-foreground"
            >
              Không có dữ liệu
            </TableCell>
          </TableRow>
        )}

        {rows.map((row) => {
          const totalWarn = isWarnRow(row, ALL_PERIOD, warnMetric)
          return (
            <TableRow key={row.key}>
              <TableCell
                className="sticky left-0 z-10 font-medium"
                style={{
                  ...STICKY_CELL_STYLE,
                  width: nameWidth,
                  minWidth: nameWidth,
                  maxWidth: nameWidth,
                }}
                title={row.key}
              >
                {/*  Hai dòng ở khổ hẹp — cùng lý do và cùng cách làm với
                     `ReportMetricTable`, xem ghi chú dài ở đó. */}
                <span className="line-clamp-3 whitespace-normal md:line-clamp-none md:block md:truncate">
                  {row.key}
                </span>
              </TableCell>

              {months.map((month, index) => {
                const hasData = !!row.m?.[month.key]
                const warn = isWarnRow(row, month.key, warnMetric)
                return metrics.map((metric, metricIndex) => (
                  <TableCell
                    key={`${month.key}-${metric.key}`}
                    className={cn(
                      'text-right tabular-nums',
                      metricIndex === 0 && 'border-l',
                      // Tháng không phát sinh vẫn ghi 0 nhưng làm mờ đi, để mắt
                      // phân biệt được "bằng 0" với "không có giao dịch nào".
                      !hasData && 'text-muted-foreground/50',
                      warn && metric.key === warnMetric && 'font-semibold text-destructive',
                    )}
                    style={monthStyle(index, 'cell')}
                  >
                    {formatCell(metric, metricValue(row, metric.key, month.key))}
                  </TableCell>
                ))
              })}

              {metrics.map((metric, metricIndex) => (
                <TableCell
                  key={`total-${metric.key}`}
                  className={cn(
                    'text-right font-semibold tabular-nums',
                    metricIndex === 0 && 'border-l-2',
                    totalWarn && metric.key === warnMetric && 'text-destructive',
                  )}
                  style={TOTAL_CELL_STYLE}
                >
                  {formatCell(metric, metricValue(row, metric.key, ALL_PERIOD))}
                </TableCell>
              ))}
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}

function formatCell(metric: ReportMetric, value: number): string {
  return metric.pct ? formatPercent(value) : formatMoney(value)
}

function ViewButton({
  active,
  icon,
  label,
  onClick,
}: {
  active: boolean
  icon: ReactNode
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        'inline-flex h-9 items-center gap-1.5 px-3 text-sm font-medium transition-colors',
        active ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent',
      )}
    >
      {icon}
      {label}
    </button>
  )
}

function SectionTitle({
  title,
  hint,
  icon,
}: {
  title: string
  hint?: string
  icon?: ReactNode
}) {
  return (
    //  ⚠️ Khổ hẹp XUỐNG DÒNG, chú thích nằm dưới tiêu đề. Một hàng ngang thì
    //  hai vế chia nhau 324px, mà chú thích của bảng pivot dài gấp ba tiêu đề
    //  («phân cụm theo tháng · cuộn ngang · cụm xám = tổng cả năm · đỏ = tỷ lệ
    //  trễ > 30%») nên nó đẩy «Giao dịch nhà cung cấp — Năm 2026» xuống ba dòng
    //  mỗi dòng hai chữ, trong khi phần chữ nhỏ màu mờ lại chiếm hai phần ba bề
    //  ngang. Từ `md` thẻ đã rộng, một hàng như cũ.
    <h3 className="mb-3 flex flex-wrap items-center gap-x-1.5 text-sm font-semibold text-navy max-md:flex-col max-md:items-start max-md:gap-y-0.5 dark:text-foreground">
      <span className="flex items-center gap-1.5">
        {icon}
        {title}
      </span>
      {hint && <span className="font-normal text-muted-foreground">({hint})</span>}
    </h3>
  )
}

function LoadingLine() {
  return <p className="py-6 text-center text-sm text-muted-foreground">Đang tải…</p>
}

/**
 * Mặc định chỉ hiện các tháng TỚI tháng hiện tại — tháng sau chưa phát sinh, để
 * nguyên là bảng thừa mấy cụm cột rỗng. Người dùng vẫn tick lại được.
 */
function defaultVisibleMonths(months: ReportMonth[]): Set<string> {
  const now = new Date()
  const current = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  return new Set(months.filter((month) => month.key <= current).map((month) => month.key))
}
