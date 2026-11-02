import { createContext, useContext } from 'react'

import type { OrgChartForest } from './org-chart-forest'

/** Kiểu vẽ: `tree` trên xuống dưới · `columns` trái sang phải · `list` xếp dọc (điện thoại). */
export type OrgChartLayout = 'tree' | 'columns' | 'list'

export interface OrgChartContextValue {
  forest: OrgChartForest
  expanded: ReadonlySet<number>
  selectedId: number | null
  /** Hồ sơ nhân sự của người đang đăng nhập; `0` = tài khoản chưa gắn nhân sự. */
  meId: number
  layout: OrgChartLayout
  toggle: (id: number) => void
  select: (id: number) => void
}

/** Chia dữ liệu sơ đồ cho các nút cây lồng nhau, khỏi truyền prop qua từng tầng (như `provide` của bản Vue). */
export const OrgChartContext = createContext<OrgChartContextValue | null>(null)

export function useOrgChartContext(): OrgChartContextValue {
  const value = useContext(OrgChartContext)
  if (!value) throw new Error('useOrgChartContext phải nằm trong OrgChartContext.Provider')
  return value
}
