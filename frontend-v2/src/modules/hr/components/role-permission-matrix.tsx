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
 * Ma trận (đối tượng × hành động) + cột Phạm vi của MỘT vai trò.
 *
 * Đây là trục thứ nhất của hệ phân quyền hai trục: HÀNH ĐỘNG thuộc VAI TRÒ.
 * Trục còn lại — phạm vi dữ liệu theo từng người dùng — nằm ở
 * `user-scope-dialog.tsx`. Cột "Phạm vi" ở đây chỉ là mặc định của vai trò.
 */
export function RolePermissionMatrix({
  meta,
  rows,
  onChange,
  readOnly,
}: RolePermissionMatrixProps) {
  const actionKeys = meta.actions.map((action) => action.key)

  /** Dòng của một entity; chưa có thì trả về dòng rỗng (chưa cấp quyền gì). */
  const rowOf = (entity: string): RolePermissionRow =>
    rows[entity] ?? { entity, scope: 'own' }

  const setRow = (entity: string, next: RolePermissionRow) =>
    onChange({ ...rows, [entity]: next })

  const toggleAction = (entity: string, action: string) => {
    const row = rowOf(entity)
    setRow(entity, { ...row, [permissionField(action)]: !row[permissionField(action)] })
  }

  /** Bật hết / tắt hết cả dòng — tắt chỉ khi đang bật đủ mọi hành động. */
  const toggleWholeRow = (entity: string) => {
    const row = rowOf(entity)
    const turnOn = !actionKeys.every((action) => row[permissionField(action)])
    const next = { ...row }
    for (const action of actionKeys) next[permissionField(action)] = turnOn
    setRow(entity, next)
  }

  return (
    <div className="overflow-hidden rounded-lg border">
      {/* Bảng dài (gần 30 đối tượng) và rộng: cuộn TRONG khung này, giữ tiêu đề
          cột và cột "Chức năng" dính lại để không bị lạc ô khi cuộn. */}
      <Table containerClassName="max-h-[62vh] overflow-auto" className="min-w-[880px]">
        {/* Nền phải nằm trên TỪNG ô `th`: Chrome không vẽ nền của `thead`/`tr`
            khi chúng sticky, để trên đó thì dòng đầu tiên chạy xuyên qua tiêu đề. */}
        <TableHeader className="sticky top-0 z-20">
          <TableRow className="hover:bg-transparent">
            {/* `border-r` nằm trên chính ô dính: cuộn ngang thì vạch ngăn đi
                theo cột, không trôi mất như khi đặt ở cột hành động đầu tiên. */}
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
          {meta.entities.map((entity) => {
            const row = rowOf(entity.key)
            const grantedCount = actionKeys.filter(
              (action) => row[permissionField(action)],
            ).length

            return (
              <TableRow
                key={entity.key}
                // Nền đặt thẳng trên `tr` để ô dính bên trái `bg-inherit` ăn theo
                // được cả sọc chẵn/lẻ lẫn trạng thái hover.
                //
                // ⚠️ Phải là màu ĐẶC, không dùng biến thể trong suốt kiểu
                // `bg-muted/50`: ô dính đè lên phần bảng đang cuộn ngang, nền
                // mờ sẽ để lộ các ô tick chạy bên dưới.
                // `h-12` để mọi dòng cao bằng nhau — ô có dropdown "Phạm vi"
                // không được kéo dòng đó cao hơn các dòng chỉ có ô tick.
                // ⚠️ Vằn hàng chẵn dùng `--row-stripe`, KHÔNG dùng `--canvas`:
                // `--canvas` là nền TRANG (mặt phẳng sau thẻ), mượn nó làm nền
                // hàng là trông vào chuyện hai màu đó tình cờ khác nhau. Từ
                // 27/08/2026 nền trang suy ra bằng đúng `--background` nên ở
                // bảng màu có `card` = `background` thì vằn hàng biến mất sạch.
                className="group/row h-12 bg-card even:bg-row-stripe hover:bg-accent even:hover:bg-accent"
              >
                <TableCell className="sticky left-0 z-10 border-r bg-inherit">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{entity.label}</span>

                    {/* Đếm nhanh đã cấp mấy hành động — quét dọc dễ hơn nhiều so
                        với việc đếm ô tick bằng mắt. */}
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
                          // Thiết bị cảm ứng không có hover -> luôn hiện.
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
                    {/* Chưa cấp hành động nào thì phạm vi chưa có tác dụng — làm
                        mờ để mắt bỏ qua, nhưng vẫn chỉnh được. */}
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
