import { cn } from '@/shared/utils/cn'
import { useOrgChartContext } from '../utils/org-chart-context'
import { OrgChartPersonCard } from './org-chart-person-card'
import { OrgChartTeamToggle } from './org-chart-team-toggle'

//  Mọi đoạn đường nối: không bắt chuột, cùng một màu.
const LINE = 'pointer-events-none absolute border-muted-foreground/40'

/**
 * Một người và nhóm của họ (nếu đang mở), vẽ đệ quy — chép bố cục `TreeNode.vue` của ERPNext.
 *
 * - `tree` (trên xuống dưới): nhóm trải ngang dưới thanh nối bo góc; riêng nhóm mà KHÔNG ai có cấp
 *   dưới thì xếp dọc, để một nhóm 40 người không kéo sơ đồ dài ngang cả chục màn hình.
 * - `columns` (trái sang phải): nhóm xếp dọc bên phải người quản lý, nối bằng một sống dọc.
 * - `list` (điện thoại): nhóm nào cũng xếp dọc.
 *
 * Số đo đường nối (top-7, h-[60px]…) tính theo thẻ cao 56px — xem `OrgChartPersonCard`.
 */
export function OrgChartTreeNode({ id }: { id: number }) {
  const { forest, expanded, layout } = useOrgChartContext()
  const person = forest.people.get(id)
  if (!person) return null
  const open = expanded.has(id)
  const team = open ? person.reportIds : []
  const last = team.length - 1
  const hasReports = person.reportIds.length > 0

  if (layout === 'columns') {
    return (
      <div className="flex items-start">
        <div className="relative shrink-0">
          <OrgChartPersonCard person={person} />
          {hasReports && (
            <OrgChartTeamToggle
              person={person}
              open={open}
              direction="right"
              className="absolute top-1/2 left-full z-10 -ml-3 -translate-y-1/2"
            />
          )}
        </div>
        {team.length > 0 && (
          <div className="relative flex flex-col gap-6 pl-16">
            <span className={cn(LINE, 'top-7 left-0 w-8 border-t')} />
            {team.map((member, index) => (
              <div key={member} className="relative">
                {index > 0 && (
                  <span className={cn(LINE, '-left-8 border-l', index === last ? '-top-6 h-10' : '-top-6 h-[52px]')} />
                )}
                {index < last && <span className={cn(LINE, 'top-7 bottom-0 -left-8 border-l')} />}
                {index > 0 && index === last ? (
                  <span className={cn(LINE, 'top-4 -left-8 h-3 w-8 rounded-bl-[12px] border-b border-l')} />
                ) : (
                  <span className={cn(LINE, 'top-7 -left-8 w-8 border-t')} />
                )}
                <OrgChartTreeNode id={member} />
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const list = layout === 'list'
  const stacked = list || team.every((member) => (forest.people.get(member)?.reportIds.length ?? 0) === 0)

  //  Nhóm xếp dọc: mỗi người tự vẽ đoạn nối phía trên mình.
  const lineAbove = (index: number) => {
    const isLast = index === last
    if (index === 0) return isLast ? '-top-8 h-12' : '-top-8 h-[60px]'
    if (list) return isLast ? '-top-5 h-9' : '-top-5 h-12'
    return isLast ? '-top-2 h-6' : '-top-2 h-9'
  }
  //  Nhóm trải ngang: đoạn từ thanh ngang xuống từng thẻ, bo tròn hai đầu thanh.
  const connector = (index: number) => {
    if (last === 0) return 'left-1/2 top-0 h-8 border-l'
    if (index === 0) return 'left-1/2 right-0 top-0 h-8 rounded-tl-[12px] border-l border-t'
    if (index === last) return 'left-0 right-[calc(50%_-_1px)] top-0 h-8 rounded-tr-[12px] border-r border-t'
    return 'inset-x-0 top-0 h-8 border-t'
  }

  return (
    <div className={cn('flex flex-col', list ? 'items-start' : 'items-center')}>
      <div className="relative">
        <OrgChartPersonCard person={person} />
        {hasReports && (
          <OrgChartTeamToggle
            person={person}
            open={open}
            className="absolute top-full left-1/2 z-10 -mt-1.5 -translate-x-1/2"
          />
        )}
      </div>

      {team.length > 0 && stacked && (
        <div className={cn('flex flex-col pt-8 pl-12', list ? 'gap-5' : 'w-64 gap-2')}>
          {team.map((member, index) => (
            <div key={member} className="relative">
              <span className={cn(LINE, '-left-3 border-l', lineAbove(index))} />
              {index < last ? (
                <>
                  <span className={cn(LINE, 'top-7 bottom-0 -left-3 border-l')} />
                  <span className={cn(LINE, 'top-7 -left-3 w-3 border-t')} />
                </>
              ) : (
                <span className={cn(LINE, 'top-4 -left-3 h-3 w-3 rounded-bl-[12px] border-b border-l')} />
              )}
              <OrgChartTreeNode id={member} />
            </div>
          ))}
        </div>
      )}

      {team.length > 0 && !stacked && (
        <div className="relative flex items-start pt-8">
          <span className={cn(LINE, 'top-0 left-1/2 h-8 border-l')} />
          {team.map((member, index) => (
            <div key={member} className="relative px-2.5 pt-8">
              <span className={cn(LINE, connector(index))} />
              {index > 0 && index < last && <span className={cn(LINE, 'top-0 left-1/2 h-8 border-l')} />}
              <OrgChartTreeNode id={member} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
