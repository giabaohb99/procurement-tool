import { Fragment, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/utils/cn'
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
import { buildPermissionTree, type MetaEntity } from '../config/permission-groups'
import type { PermissionMeta, RolePermissionRow } from '../types/role'
import { permissionField } from '../types/role'

interface RolePermissionMatrixProps {
  meta: PermissionMeta
  /** Trạng thái ma trận, khóa theo `entity`. */
  rows: Record<string, RolePermissionRow>
  onChange: (rows: Record<string, RolePermissionRow>) => void
  /** Thiếu quyền sửa vai trò thì chỉ cho xem. */
  readOnly?: boolean
}

/**
 * Ma trận (đối tượng × hành động) + cột Phạm vi của MỘT vai trò, dạng CÂY hai cấp.
 *
 * Cấp 1 = phân hệ (Đặt xe, Văn thư…), cấp 2 = entity con (Yêu cầu đặt xe, Tài xế…).
 * Tick một hành động ở cấp 1 = bật/tắt hành động đó cho TẤT CẢ entity con của nhóm;
 * ô cấp 1 hiện dấu gạch (một phần) khi các con chỉ chọn một số. Nhóm khai ở
 * `config/permission-groups.ts`.
 *
 * Đây là trục thứ nhất của hệ phân quyền hai trục: HÀNH ĐỘNG thuộc VAI TRÒ. Trục
 * còn lại — phạm vi dữ liệu theo từng người dùng — nằm ở `user-scope-dialog.tsx`.
 * Cột "Phạm vi" ở đây chỉ là mặc định của vai trò, đặt trên TỪNG entity con.
 */
export function RolePermissionMatrix({
  meta,
  rows,
  onChange,
  readOnly,
}: RolePermissionMatrixProps) {
  const actionKeys = meta.actions.map((action) => action.key)
  const groups = buildPermissionTree(meta.entities)
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set())

  const toggleCollapse = (groupId: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(groupId)) next.delete(groupId)
      else next.add(groupId)
      return next
    })
  const setAllCollapsed = (value: boolean) =>
    setCollapsed(value ? new Set(groups.map((g) => g.id)) : new Set())

  /** Dòng của một entity; chưa có thì trả về dòng rỗng (chưa cấp quyền gì). */
  const rowOf = (entity: string): RolePermissionRow =>
    rows[entity] ?? { entity, scope: 'own' }

  const setRow = (entity: string, next: RolePermissionRow) =>
    onChange({ ...rows, [entity]: next })

  const toggleAction = (entity: string, action: string) => {
    const row = rowOf(entity)
    setRow(entity, { ...row, [permissionField(action)]: !row[permissionField(action)] })
  }

  /** Bật hết / tắt hết cả dòng entity — tắt chỉ khi đang bật đủ mọi hành động. */
  const toggleWholeRow = (entity: string) => {
    const row = rowOf(entity)
    const turnOn = !actionKeys.every((action) => row[permissionField(action)])
    const next = { ...row }
    for (const action of actionKeys) next[permissionField(action)] = turnOn
    setRow(entity, next)
  }

  /** Trạng thái tổng của một hành động ở CẤP NHÓM: đủ / một phần / không. */
  const groupState = (entities: MetaEntity[], action: string): boolean | 'indeterminate' => {
    const on = entities.filter((e) => rowOf(e.key)[permissionField(action)]).length
    if (on === 0) return false
    if (on === entities.length) return true
    return 'indeterminate'
  }

  /** Tick hành động ở cấp nhóm → đặt hành động đó cho MỌI entity con. */
  const toggleGroupAction = (entities: MetaEntity[], action: string) => {
    const turnOn = !entities.every((e) => rowOf(e.key)[permissionField(action)])
    const next = { ...rows }
    for (const e of entities) {
      const row = next[e.key] ?? { entity: e.key, scope: 'own' }
      next[e.key] = { ...row, [permissionField(action)]: turnOn }
    }
    onChange(next)
  }

  return (
    <div className="overflow-hidden rounded-lg border">
      {!readOnly && (
        <div className="flex items-center gap-3 border-b bg-card px-3 py-1.5 text-xs text-muted-foreground">
          <span>Tick ở phân hệ (cấp 1) sẽ chọn cho tất cả mục con.</span>
          <button
            type="button"
            className="ml-auto rounded px-1.5 py-0.5 hover:bg-accent hover:text-foreground"
            onClick={() => setAllCollapsed(false)}
          >
            Mở hết
          </button>
          <button
            type="button"
            className="rounded px-1.5 py-0.5 hover:bg-accent hover:text-foreground"
            onClick={() => setAllCollapsed(true)}
          >
            Gập hết
          </button>
        </div>
      )}
      {/* Bảng dài và rộng: cuộn TRONG khung này, giữ tiêu đề cột và cột "Chức năng"
          dính lại để không bị lạc ô khi cuộn. */}
      <Table containerClassName="max-h-[62vh] overflow-auto" className="min-w-[880px]">
        {/* Nền phải nằm trên TỪNG ô `th`: Chrome không vẽ nền của `thead`/`tr`
            khi chúng sticky, để trên đó thì dòng đầu tiên chạy xuyên qua tiêu đề. */}
        <TableHeader className="sticky top-0 z-20">
          <TableRow className="hover:bg-transparent">
            <TableHead className="sticky left-0 z-30 h-11 min-w-56 border-r bg-card">
              Chức năng
            </TableHead>
            {meta.actions.map((action) => (
              <TableHead
                key={action.key}
                className="h-11 w-16 bg-card text-center text-xs font-medium uppercase tracking-wide text-muted-foreground"
              >
                {action.label}
              </TableHead>
            ))}
            <TableHead className="h-11 w-44 border-l bg-card text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Phạm vi
            </TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {groups.map((group) => {
            const isOpen = !collapsed.has(group.id)
            return (
              <Fragment key={group.id}>
                {/* ---------- CẤP 1: phân hệ ---------- */}
                <TableRow className="bg-muted hover:bg-muted">
                  <TableCell className="sticky left-0 z-10 border-r bg-inherit">
                    <button
                      type="button"
                      className="flex w-full items-center gap-1.5 text-left font-semibold"
                      onClick={() => toggleCollapse(group.id)}
                    >
                      {isOpen ? (
                        <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
                      )}
                      <span>{group.title}</span>
                      <span className="shrink-0 text-[11px] font-normal tabular-nums text-muted-foreground">
                        {group.entities.length} mục
                      </span>
                    </button>
                  </TableCell>

                  {actionKeys.map((action) => (
                    <TableCell key={action} className="text-center">
                      <Checkbox
                        className="mx-auto"
                        checked={groupState(group.entities, action)}
                        disabled={readOnly}
                        onCheckedChange={() => toggleGroupAction(group.entities, action)}
                        aria-label={`${group.title} — ${action} (tất cả mục con)`}
                      />
                    </TableCell>
                  ))}

                  {/* Phạm vi đặt trên TỪNG entity con, cấp nhóm để trống. */}
                  <TableCell className="border-l" />
                </TableRow>

                {/* ---------- CẤP 2: entity con ---------- */}
                {isOpen &&
                  group.entities.map((entity) => {
                    const row = rowOf(entity.key)
                    const grantedCount = actionKeys.filter(
                      (action) => row[permissionField(action)],
                    ).length

                    return (
                      <TableRow
                        key={entity.key}
                        // Nền ĐẶC (không alpha): ô dính bên trái đè lên phần cuộn ngang.
                        className="group/row h-12 bg-card even:bg-row-stripe hover:bg-accent even:hover:bg-accent"
                      >
                        <TableCell className="sticky left-0 z-10 border-r bg-inherit">
                          <div className="flex items-center gap-2 pl-6">
                            <span className="font-medium">{entity.label}</span>
                            <span className="shrink-0 text-[11px] tabular-nums text-muted-foreground">
                              {grantedCount}/{actionKeys.length}
                            </span>

                            {!readOnly && (
                              <button
                                type="button"
                                className={cn(
                                  'ml-auto rounded px-1.5 py-0.5 text-xs text-muted-foreground opacity-0 transition',
                                  'hover:bg-background hover:text-foreground focus-visible:opacity-100',
                                  'group-hover/row:opacity-100',
                                  '[@media(hover:none)]:opacity-100',
                                )}
                                onClick={() => toggleWholeRow(entity.key)}
                              >
                                {grantedCount === actionKeys.length ? 'Bỏ hết' : 'Chọn hết'}
                              </button>
                            )}
                          </div>
                        </TableCell>

                        {actionKeys.map((action) => (
                          <TableCell key={action} className="text-center">
                            <Checkbox
                              className="mx-auto"
                              checked={!!row[permissionField(action)]}
                              disabled={readOnly}
                              onCheckedChange={() => toggleAction(entity.key, action)}
                              aria-label={`${entity.label} — ${action}`}
                            />
                          </TableCell>
                        ))}

                        <TableCell className="border-l">
                          <Select
                            value={row.scope || 'own'}
                            disabled={readOnly}
                            onValueChange={(scope) => setRow(entity.key, { ...row, scope })}
                          >
                            <SelectTrigger
                              size="sm"
                              className={cn('w-full', grantedCount === 0 && 'opacity-50')}
                            >
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {meta.scopes.map((scope) => (
                                <SelectItem key={scope.key} value={scope.key}>
                                  {scope.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                      </TableRow>
                    )
                  })}
              </Fragment>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

/**
 * Ép state ma trận về payload gửi lên backend.
 * Dòng KHÔNG bật hành động nào bị loại — backend hiểu là "vai trò không có
 * quyền gì trên entity đó", giữ lại chỉ tạo rác trong bảng phân quyền.
 */
export function toPermissionPayload(
  meta: PermissionMeta,
  rows: Record<string, RolePermissionRow>,
): RolePermissionRow[] {
  const actionKeys = meta.actions.map((action) => action.key)

  return meta.entities
    .map((entity) => {
      const row = rows[entity.key] ?? { entity: entity.key, scope: 'own' }
      const payload: RolePermissionRow = {
        entity: entity.key,
        scope: row.scope || 'own',
      }
      for (const action of actionKeys) {
        payload[permissionField(action)] = !!row[permissionField(action)]
      }
      return payload
    })
    .filter((row) => actionKeys.some((action) => row[permissionField(action)]))
}
