import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useSetUrlParams } from '@/shared/hooks/use-url-param-state'

import {
  DEFAULT_REPORT_PRESET,
  isReportPresetKey,
  resolveLocalPresetRange,
  type ReportPresetKey,
} from '../config/report-period-presets'
import type { ReportCompareMode } from '../types/report-analytics'

export const ALL_COMPANY = 'all'
const DEFAULT_COMPARE: ReportCompareMode = 'previous'
const COMPARE_MODES: ReportCompareMode[] = ['previous', 'year', 'none']

function isCompareMode(value: string | null): value is ReportCompareMode {
  return value !== null && (COMPARE_MODES as string[]).includes(value)
}

export interface UseReportFiltersConfig {
  /** `group_by` khi URL chưa có tham số đó — `ReportPageConfig.defaultGroupBy`. */
  defaultGroupBy: string
}

export interface ReportFiltersState {
  preset: ReportPresetKey
  /** Chỉ có nghĩa khi `preset === 'custom'`. */
  from: string
  to: string
  compare: ReportCompareMode
  groupBy: string
  companyId: string
  /** `undefined` = tất cả công ty — dạng tham số API cần. */
  company?: string
  setPreset: (preset: ReportPresetKey) => void
  /** Áp một khoảng ngày TÙY CHỌN — cũng tự chuyển `preset` sang `'custom'`. */
  setCustomRange: (from: string, to: string) => void
  setCompare: (compare: ReportCompareMode) => void
  setGroupBy: (groupBy: string) => void
  setCompanyId: (companyId: string) => void
  /**
   * Áp CẢ preset/khoảng ngày TÙY CHỌN/so sánh trong MỘT lượt ghi URL — dùng bởi
   * `ReportPeriodControl` khi bấm "Áp dụng" trong popover kỳ kiểu Haravan.
   *
   * ⚠️ Không thay bằng `setPreset(...)` rồi `setCompare(...)` gọi liên tiếp:
   * cùng bẫy đã ghi ở `resetFilters` — hai lượt `setSearchParams` trong một lần
   * bấm thì lượt sau đọc URL CŨ, đè mất lượt trước (`use-url-param-state.ts`).
   * Popover giữ NHÁP cục bộ (preset/khoảng ngày/so sánh) và chỉ gọi hàm này một
   * lần khi người dùng chốt, nên nháp không rò ra URL cho tới lúc đó.
   */
  applyPeriod: (input: {
    preset: ReportPresetKey
    from: string
    to: string
    compare: ReportCompareMode
  }) => void
  /**
   * Đặt lại "Xem theo" và/hoặc kỳ về mặc định TRONG MỘT lượt ghi URL — dùng khi
   * `/summary` lỗi (403 `group_by` không có quyền, 422 kỳ sai — M6, xem
   * `ReportAnalyticsPage`). ⚠️ KHÔNG thay bằng `setGroupBy(...)` rồi
   * `setPreset(...)` gọi liên tiếp: `useSetUrlParams` cảnh báo sẵn — hai lượt
   * `setSearchParams` trong cùng một lần bấm thì lượt sau đọc URL CŨ, đè mất
   * lượt trước (đúng bẫy đã vấp ở màn Lịch nghỉ, xem `use-url-param-state.ts`).
   */
  resetFilters: (options: { groupBy?: boolean; period?: boolean }) => void
  /**
   * Tham số gửi backend: lõi (`preset`/`date_from`/`date_to`/`compare`/
   * `group_by`/`company_id`) GHI ĐÈ mọi tham số lọc riêng của trang đang có
   * trên URL (vd `department_id` của `ReportPageConfig.extraFilters`) — nhờ
   * vậy trang không cần biết tên các tham số riêng đó là gì.
   */
  queryParams: Record<string, string>
}

/**
 * Bộ lọc kỳ của MỘT trang báo cáo Haravan — state nằm trên URL nên F5 hay gửi
 * link cho đồng nghiệp vẫn mở đúng kỳ đang xem.
 *
 * Tương thích ngược: link cũ `?year=2025` (không có `preset`) được ĐỌC như
 * `preset=custom&date_from=2025-01-01&date_to=2025-12-31` — chỉ suy ra lúc
 * đọc, KHÔNG viết đè URL. Đổi bất kỳ bộ lọc nào sau đó ghi bộ tham số mới và
 * `year` tự biến mất khỏi URL (mọi setter đều xóa nó).
 */
export function useReportFilters({ defaultGroupBy }: UseReportFiltersConfig): ReportFiltersState {
  const [searchParams] = useSearchParams()
  const setParams = useSetUrlParams()

  const presetParam = searchParams.get('preset')
  const legacyYear = searchParams.get('year')
  const isLegacyYear = !presetParam && legacyYear !== null && /^\d{4}$/.test(legacyYear)

  const preset: ReportPresetKey = isLegacyYear
    ? 'custom'
    : isReportPresetKey(presetParam)
      ? presetParam
      : DEFAULT_REPORT_PRESET

  const from = isLegacyYear ? `${legacyYear}-01-01` : (searchParams.get('date_from') ?? '')
  const to = isLegacyYear ? `${legacyYear}-12-31` : (searchParams.get('date_to') ?? '')

  const compareParam = searchParams.get('compare')
  const compare: ReportCompareMode = isCompareMode(compareParam) ? compareParam : DEFAULT_COMPARE

  const groupBy = searchParams.get('group_by') ?? defaultGroupBy
  const companyId = searchParams.get('company_id') ?? ALL_COMPANY

  const queryParams = useMemo(() => {
    const params: Record<string, string> = {}
    for (const [key, value] of searchParams.entries()) {
      //  `year` đã được dịch sang `preset=custom` ở trên — không gửi cả hai.
      if (key !== 'year') params[key] = value
    }
    params.preset = preset
    if (preset === 'custom') {
      params.date_from = from
      params.date_to = to
    } else {
      delete params.date_from
      delete params.date_to
    }
    params.compare = compare
    params.group_by = groupBy
    if (companyId === ALL_COMPANY) delete params.company_id
    else params.company_id = companyId
    return params
  }, [searchParams, preset, from, to, compare, groupBy, companyId])

  return {
    preset,
    from,
    to,
    compare,
    groupBy,
    companyId,
    company: companyId === ALL_COMPANY ? undefined : companyId,

    setPreset: (next) => {
      if (next === 'custom') {
        //  Mồi một khoảng CÓ SẴN (xem `resolveLocalPresetRange`) thay vì gửi
        //  `preset=custom` không kèm ngày — backend đòi đủ cả hai (422 nếu thiếu).
        const [seedFrom, seedTo] = resolveLocalPresetRange('custom')
        setParams({
          preset: 'custom',
          year: null,
          date_from: from || seedFrom,
          date_to: to || seedTo,
        })
        return
      }
      setParams({
        preset: next === DEFAULT_REPORT_PRESET ? null : next,
        year: null,
        date_from: null,
        date_to: null,
      })
    },

    setCustomRange: (nextFrom, nextTo) => {
      const [seedFrom, seedTo] = resolveLocalPresetRange('custom')
      setParams({
        preset: 'custom',
        year: null,
        //  Bấm ✕ xóa khoảng trên `DateRangePicker` trả hai chuỗi rỗng — quay về
        //  khoảng mồi thay vì để trống, cùng lý do như lúc mới chuyển "Tùy chọn".
        date_from: nextFrom || seedFrom,
        date_to: nextTo || seedTo,
      })
    },

    setCompare: (next) => setParams({ compare: next === DEFAULT_COMPARE ? null : next }),
    setGroupBy: (next) => setParams({ group_by: next === defaultGroupBy ? null : next }),
    setCompanyId: (next) => setParams({ company_id: next === ALL_COMPANY ? null : next }),

    applyPeriod: ({ preset: nextPreset, from: nextFrom, to: nextTo, compare: nextCompare }) => {
      const next: Record<string, string | null> = {
        preset: nextPreset === DEFAULT_REPORT_PRESET ? null : nextPreset,
        year: null,
        compare: nextCompare === DEFAULT_COMPARE ? null : nextCompare,
      }
      if (nextPreset === 'custom') {
        const [seedFrom, seedTo] = resolveLocalPresetRange('custom')
        next.date_from = nextFrom || seedFrom
        next.date_to = nextTo || seedTo
      } else {
        next.date_from = null
        next.date_to = null
      }
      setParams(next)
    },

    resetFilters: ({ groupBy = false, period = false }) => {
      const next: Record<string, string | null> = {}
      if (groupBy) next.group_by = null
      if (period) {
        next.preset = null
        next.year = null
        next.date_from = null
        next.date_to = null
      }
      setParams(next)
    },

    queryParams,
  }
}
