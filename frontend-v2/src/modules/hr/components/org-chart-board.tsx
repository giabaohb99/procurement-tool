import { Columns3, FoldVertical, LocateFixed, Network, UnfoldVertical } from 'lucide-react'
import { useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { flushSync } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { SearchSelect } from '@/shared/ui/search-select'
import { cn } from '@/shared/utils/cn'
import { OrgChartContext, type OrgChartLayout } from '../utils/org-chart-context'
import { getOrgChartManagerPath, listOrgChartManagers, type OrgChartForest } from '../utils/org-chart-forest'
import { OrgChartCanvas, type OrgChartCanvasHandle } from './org-chart-canvas'
import { OrgChartConcurrentSection } from './org-chart-concurrent-section'
import { OrgChartPersonPopover } from './org-chart-person-popover'
import { OrgChartTreeNode } from './org-chart-tree-node'

interface OrgChartBoardProps {
  forest: OrgChartForest
  meId: number
  layout: OrgChartLayout
  /** Người dùng đổi kiểu vẽ (chỉ hiện nút trên màn rộng; điện thoại luôn `list`). */
  onLayoutChange: (layout: 'tree' | 'columns') => void
  /** Ô lọc pháp nhân / phòng ban của trang, đặt cạnh ô tìm người. */
  filters?: ReactNode
  /** Backend cắt danh sách kiêm nhiệm ở trần dòng — báo ở phần Kiêm nhiệm. */
  concurrentsTruncated?: boolean
}

/** Một người đứng đầu = trưởng cả cây, nên mở sẵn nhóm của họ (như ERPNext). */
function initialExpanded(forest: OrgChartForest): Set<number> {
  return new Set(forest.roots.length === 1 ? forest.roots : [])
}

/**
 * Sơ đồ đang xem: giữ nhóm nào đang mở, thẻ nào đang chọn, và các lệnh nhảy tới người.
 * Trang gắn `key` theo bộ lọc nên đổi pháp nhân / phòng là sơ đồ dựng lại từ đầu.
 */
export function OrgChartBoard({
  forest,
  meId,
  layout,
  onLayoutChange,
  filters,
  concurrentsTruncated = false,
}: OrgChartBoardProps) {
  const canvas = useRef<OrgChartCanvasHandle>(null)
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState<ReadonlySet<number>>(() => initialExpanded(forest))
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const managers = useMemo(() => listOrgChartManagers(forest), [forest])
  const allOpen = managers.length > 0 && managers.every((id) => expanded.has(id))
  const meVisible = meId > 0 && forest.visibleIds.has(meId)

  useLayoutEffect(() => {
    canvas.current?.showTop()
  }, [layout])

  //  Thu một nhóm: thẻ quản lý đứng yên. Mở: thẻ đứng yên rồi dời cho cả nhóm vào tầm nhìn.
  const toggle = (id: number) => {
    const handle = canvas.current
    if (!handle) return
    const card = handle.findCard(id)
    const opening = !expanded.has(id)
    handle.keepInPlace(card, () =>
      setExpanded((current) => {
        const next = new Set(current)
        if (opening) next.add(id)
        else next.delete(id)
        return next
      }),
    )
    if (opening) {
      const team = forest.people.get(id)?.reportIds ?? []
      handle.reveal([id, ...team].map(handle.findCard))
    }
  }

  //  Mở mọi nhóm phía trên người đó, rồi đưa thẻ vào giữa và chọn.
  const showPerson = (id: number) => {
    const handle = canvas.current
    if (!handle) return
    const path = getOrgChartManagerPath(forest, id)
    flushSync(() => setExpanded((current) => new Set([...current, ...path])))
    const card = handle.findCard(id)
    if (!card) {
      toast.warning('Người này không có trên sơ đồ đang xem.')
      return
    }
    handle.center(card)
    setSelectedId(id)
  }

  const showManager = (id: number) => {
    if (forest.visibleIds.has(id)) showPerson(id)
    else navigate(appRoutes.hr.employeeDetail(id))
  }

  const toggleAll = () => {
    const handle = canvas.current
    flushSync(() => setExpanded(allOpen ? initialExpanded(forest) : new Set(managers)))
    if (allOpen) handle?.showTop()
    else handle?.fit()
  }

  const searchOptions = useMemo(
    () =>
      [...forest.visibleIds]
        .map((id) => forest.people.get(id))
        .filter((person) => person !== undefined)
        .sort((a, b) => a.fullName.localeCompare(b.fullName, 'vi'))
        .map((person) => ({
          value: String(person.id),
          label: person.fullName,
          hint: [person.code, person.position || person.departmentName].filter(Boolean).join(' · '),
        })),
    [forest],
  )

  const selected = selectedId !== null ? forest.people.get(selectedId) : undefined
  const select = (id: number) => setSelectedId((current) => (current === id ? null : id))

  return (
    <OrgChartContext.Provider value={{ forest, expanded, selectedId, meId, layout, toggle, select }}>
      <OrgChartCanvas
        ref={canvas}
        selectedId={selectedId}
        onDeselect={() => setSelectedId(null)}
        panel={
          <div className="flex flex-wrap gap-2">
            <SearchSelect
              value=""
              onChange={(value) => value && showPerson(Number(value))}
              options={searchOptions}
              placeholder="Tìm một người"
              searchPlaceholder="Gõ tên, mã hoặc chức vụ…"
              emptyMessage="Không tìm thấy ai."
              searchInTrigger
              className="w-full bg-card sm:w-72"
            />
            {filters}
          </div>
        }
        popover={
          selected && (
            <OrgChartPersonPopover person={selected} onClose={() => setSelectedId(null)} onShowManager={showManager} />
          )
        }
        actions={
          <>
            {meVisible && (
              <IconTooltip label="Tìm tôi">
                <Button type="button" variant="ghost" size="icon-sm" aria-label="Tìm tôi" onClick={() => showPerson(meId)}>
                  <LocateFixed />
                </Button>
              </IconTooltip>
            )}
            {layout !== 'list' && (
              <>
                <span aria-hidden className="mx-1 h-4 w-px bg-border" />
                <Button type="button" variant="ghost" size="sm" onClick={toggleAll} disabled={managers.length === 0}>
                  {allOpen ? <FoldVertical /> : <UnfoldVertical />}
                  {allOpen ? 'Thu gọn' : 'Mở hết'}
                </Button>
                <span aria-hidden className="mx-1 h-4 w-px bg-border" />
                {(
                  [
                    { value: 'tree', label: 'Trên xuống dưới', Icon: Network },
                    { value: 'columns', label: 'Trái sang phải', Icon: Columns3 },
                  ] as const
                ).map(({ value, label, Icon }) => (
                  <IconTooltip key={value} label={label}>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label={label}
                      aria-pressed={layout === value}
                      className={cn(layout === value && 'bg-accent text-accent-foreground')}
                      onClick={() => onLayoutChange(value)}
                    >
                      <Icon />
                    </Button>
                  </IconTooltip>
                ))}
              </>
            )}
          </>
        }
      >
        {forest.roots.length === 0 && forest.concurrentGroups.length === 0 ? (
          <p className="rounded-lg border bg-card px-6 py-4 text-sm text-muted-foreground">
            Không có ai trong phần đang xem — thử bỏ bớt bộ lọc.
          </p>
        ) : (
          <>
            {forest.roots.length > 0 && (
              <div className={cn('flex items-start', layout === 'tree' ? 'gap-8' : 'flex-col gap-6')}>
                {forest.roots.map((id) => (
                  <OrgChartTreeNode key={id} id={id} />
                ))}
              </div>
            )}
            {/*  duoc-CR-755: người kiêm nhiệm ở phòng đang xem — ngoài cây quản lý, không thêm vào quân số. */}
            <OrgChartConcurrentSection groups={forest.concurrentGroups} truncated={concurrentsTruncated} />
          </>
        )}
      </OrgChartCanvas>
    </OrgChartContext.Provider>
  )
}
