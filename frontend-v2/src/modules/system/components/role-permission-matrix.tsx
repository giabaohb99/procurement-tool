import { Fragment, useState } from 'react'
import { ChevronDown, ChevronRight, Search, X } from 'lucide-react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
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
import {
  buildPermissionTree,
  filterPermissionTree,
  type MetaEntity,
} from '../config/permission-groups'
import {
  cellsState,
  collapseGroupsWithoutTicks,
  emptyRow,
  setCells,
  toggleCells,
} from '../utils/permission-matrix-cells'
import {
  PermissionBulkButton,
  PermissionRowBulkButton,
} from './permission-bulk-buttons'
import type { PermissionMeta, RolePermissionRow } from '@/modules/hr/types/role'
import { permissionField } from '@/modules/hr/types/role'

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
 * Nhóm khai ở `config/permission-groups.ts`.
 *
 * ⚠️ **"Chọn hết" có mặt ở BỐN cỡ, cố ý vậy** (duoc-CR-407). Vai trò mẫu cần
 * 55 entity × 8 hành động = 440 ô; khai một vai trò quản trị bằng cách tick tay
 * là việc không ai làm xong. Bốn cỡ đó:
 *   • cả bảng — hai nút ở thanh trên;
 *   • một CỘT (một hành động cho mọi entity) — ô tick dưới tiêu đề cột;
 *   • một PHÂN HỆ (mọi hành động của mọi mục con) — nút ở dòng cấp 1;
 *   • một DÒNG (mọi hành động của một entity) — nút ở dòng cấp 2.
 * Cả bốn chạy trên `utils/permission-matrix-cells.ts`, đừng viết lại phép toán.
 *
 * ⚠️ Mấy nút này **luôn hiện**, không ẩn chờ rê chuột. Bản trước để
 * `opacity-0 group-hover:opacity-100` cho dòng cấp 2 và khách báo màn "không có
 * chức năng chọn hết" — một chức năng chỉ hiện khi rê chuột vào đúng dòng thì
 * bằng như không có, nhất là trên máy cảm ứng.
 *
 * ⚠️ **Ô TÌM và "chọn hết" dính nhau, đừng tách rời** (duoc-CR-408). Đang lọc thì
 * mọi cỡ "chọn hết" — kể cả hai nút cả-bảng và ô tick ở tiêu đề cột — chỉ áp cho
 * DÒNG ĐANG HIỆN, vì `allEntityKeys` lấy từ cây đã lọc. Đó là chủ đích (lọc
 * "văn bản" rồi cho cả phân hệ một nhịp), nhưng cũng là chỗ dễ hiểu sai nhất
 * của màn, nên thanh trên **phải nói ra bằng chữ** khi có từ khóa. Quyền của
 * những dòng đang bị ẩn KHÔNG mất: `rows` giữ nguyên và `toPermissionPayload`
 * đọc `meta.entities` chứ không đọc cây.
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
  const fullTree = buildPermissionTree(meta.entities)
  //  Mở sẵn phân hệ CÓ tick, gập phân hệ trống (bao-CR-428): 60 mục xổ hết thì
  //  người đọc phải cuộn qua hai chục nhóm trắng mới tới chỗ vai trò này thật
  //  sự có quyền. Chưa tick gì cả (vai trò mới) thì mở hết — gập hết lúc đó là
  //  một bảng chỉ toàn dòng tiêu đề, không biết bắt đầu tick từ đâu.
  //  Chỉ tính MỘT LẦN lúc mount: nơi gọi truyền `key={roleId}` nên đổi vai trò
  //  là dựng lại; còn trong lúc tick thì không tự gập/mở gì cả.
  const [collapsed, setCollapsed] = useState<Set<string>>(() =>
    collapseGroupsWithoutTicks(fullTree, rows, actionKeys),
  )
  const [keyword, setKeyword] = useState('')
  const groups = filterPermissionTree(fullTree, keyword)
  const isFiltering = keyword.trim().length > 0

  //  Gõ tìm là MỞ HẾT. Kết quả nằm trong một phân hệ đang gập thì bảng trả về
  //  rỗng trong khi rõ ràng có dòng khớp — người dùng đọc ra "hệ không có chức
  //  năng đó". Đặt lại state ngay trong lúc render (xem `useHasChanged`) thay vì
  //  bỏ qua `collapsed` khi đang lọc: bỏ qua thì mũi tên xổ bấm vào không có gì
  //  xảy ra, nhìn như hỏng.
  if (useHasChanged(keyword) && isFiltering) setCollapsed(new Set())

  //  Mọi entity ĐANG HIỆN trên bảng — lấy từ cây ĐÃ LỌC chứ không từ
  //  `meta.entities`: "chọn hết" phải khớp đúng những gì người dùng nhìn thấy.
  const allEntityKeys = groups.flatMap((group) => group.entities.map((e) => e.key))
  const totalEntityCount = fullTree.reduce((sum, group) => sum + group.entities.length, 0)

  const toggleCollapse = (groupId: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(groupId)) next.delete(groupId)
      else next.add(groupId)
      return next
    })
  //  `fullTree` chứ không phải `groups`: "Gập hết" lúc đang lọc mà chỉ gập mấy
  //  nhóm đang hiện thì xóa từ khóa xong bảng lại xổ ra đầy, không ai gọi đó là
  //  gập hết.
  const setAllCollapsed = (value: boolean) =>
    setCollapsed(value ? new Set(fullTree.map((g) => g.id)) : new Set())

  /** Dòng của một entity; chưa có thì trả về dòng rỗng (chưa cấp quyền gì). */
  const rowOf = (entity: string): RolePermissionRow => rows[entity] ?? emptyRow(entity)

  const toggle = (entities: string[], actions: string[]) =>
    onChange(toggleCells(rows, entities, actions))

  const keysOf = (entities: MetaEntity[]) => entities.map((entity) => entity.key)

  return (
    <div className="overflow-hidden rounded-lg border">
      {/*  Thanh trên dựng CẢ KHI chỉ-xem: ô tìm vẫn phải có. Người mở vai trò
           của chính mình (readOnly) là người đi tra "vai trò này có quyền gì
           trên Đơn mua hàng" — đúng việc cần ô tìm nhất. Chỉ mấy nút sửa mới ẩn. */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b bg-card px-3 py-2 text-xs text-muted-foreground">
        <div className="relative w-full sm:w-64">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="h-8 pl-8 pr-8 text-xs"
            placeholder="Tìm chức năng…"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            aria-label="Tìm chức năng trong ma trận quyền"
          />
          {isFiltering && (
            <button
              type="button"
              className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground transition hover:bg-accent hover:text-foreground"
              onClick={() => setKeyword('')}
              aria-label="Xóa từ khóa tìm"
            >
              <X className="size-3.5" />
            </button>
          )}
        </div>

        {/*  ĐANG LỌC THÌ NÓI RA, và nói luôn hệ quả. "Chọn hết" lúc này chỉ áp
             cho dòng đang hiện — tiện đúng ý (lọc một phân hệ rồi cho cả cụm một
             nhịp) nhưng im lặng thì người dùng tưởng vừa cấp quyền cho cả hệ. */}
        {isFiltering ? (
          <span className={cn('text-foreground', allEntityKeys.length === 0 && 'text-muted-foreground')}>
            Đang lọc <b className="tabular-nums">{allEntityKeys.length}</b>/
            <span className="tabular-nums">{totalEntityCount}</span> chức năng
            {!readOnly && allEntityKeys.length > 0 && ' — «chọn hết» chỉ áp cho các dòng đang hiện'}
          </span>
        ) : (
          !readOnly && (
            <span>
              Tick ở tiêu đề cột = cả bảng; tick ở phân hệ (cấp 1) = tất cả mục con.
            </span>
          )
        )}

        <div className="ml-auto flex items-center gap-1">
          {!readOnly && (
            <>
              {/*  Hai nút RIÊNG, không dùng một nút lật trạng thái: nút lật thì cú
                   bấm "cho hết quyền" và cú bấm "xóa sạch quyền" nằm ở cùng một
                   chỗ, chỉ khác nhau cái nhãn — bấm theo quán tính là mất cả ma
                   trận của vai trò. */}
              <PermissionBulkButton
                disabled={allEntityKeys.length === 0}
                onClick={() => onChange(setCells(rows, allEntityKeys, actionKeys, true))}
              >
                {isFiltering ? 'Chọn hết đang hiện' : 'Chọn hết quyền'}
              </PermissionBulkButton>
              <PermissionBulkButton
                danger
                disabled={allEntityKeys.length === 0}
                onClick={() => onChange(setCells(rows, allEntityKeys, actionKeys, false))}
              >
                {isFiltering ? 'Bỏ hết đang hiện' : 'Bỏ hết quyền'}
              </PermissionBulkButton>

              <span className="mx-1 h-4 w-px bg-border" aria-hidden />
            </>
          )}

          <PermissionBulkButton onClick={() => setAllCollapsed(false)}>
            Mở hết
          </PermissionBulkButton>
          <PermissionBulkButton onClick={() => setAllCollapsed(true)}>
            Gập hết
          </PermissionBulkButton>
        </div>
      </div>
      {/* Bảng dài và rộng: cuộn TRONG khung này, giữ tiêu đề cột và cột "Chức năng"
          dính lại để không bị lạc ô khi cuộn. */}
      <Table containerClassName="max-h-[62dvh] overflow-auto" className="min-w-[880px]">
        {/* Nền phải nằm trên TỪNG ô `th`: Chrome không vẽ nền của `thead`/`tr`
            khi chúng sticky, để trên đó thì dòng đầu tiên chạy xuyên qua tiêu đề. */}
        <TableHeader className="sticky top-0 z-20">
          <TableRow className="hover:bg-transparent">
            <TableHead className="sticky left-0 z-30 h-12 min-w-56 border-r bg-card align-middle">
              Chức năng
            </TableHead>
            {meta.actions.map((action) => (
              <TableHead
                key={action.key}
                className="h-12 w-16 bg-card text-center align-middle text-xs font-medium uppercase tracking-wide text-muted-foreground"
              >
                <div className="flex flex-col items-center gap-1">
                  <span>{action.label}</span>
                  {!readOnly && (
                    <Checkbox
                      checked={cellsState(rows, allEntityKeys, [action.key])}
                      onCheckedChange={() => toggle(allEntityKeys, [action.key])}
                      aria-label={`${action.label} — chọn hết cho mọi chức năng`}
                    />
                  )}
                </div>
              </TableHead>
            ))}
            <TableHead className="h-12 w-44 border-l bg-card align-middle text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Phạm vi
            </TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {/*  Câu rỗng phải phân biệt RỖNG VÌ LỌC với RỖNG VÌ CHƯA CÓ GÌ. Một
               câu chung cho cả hai thì người vừa gõ nhầm một chữ đọc ra "hệ
               không có chức năng đó" và tin là vậy. Ma trận luôn có dữ liệu
               (`meta` do backend trả), nên nhánh thứ hai chỉ để phòng khi
               `/api/roles/meta` trả rỗng — lúc đó lỗi nằm ở backend, và câu chữ
               phải chỉ đúng về đó. */}
          {groups.length === 0 && (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={actionKeys.length + 2} className="py-10 text-center">
                {isFiltering ? (
                  <>
                    <p className="text-sm text-muted-foreground">
                      Không có chức năng nào khớp «{keyword.trim()}».
                    </p>
                    <button
                      type="button"
                      className="mt-1 text-xs text-primary underline-offset-2 hover:underline"
                      onClick={() => setKeyword('')}
                    >
                      Xóa từ khóa để xem lại {totalEntityCount} chức năng
                    </button>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Backend chưa khai chức năng nào ở <code>/api/roles/meta</code>.
                  </p>
                )}
              </TableCell>
            </TableRow>
          )}

          {groups.map((group) => {
            const isOpen = !collapsed.has(group.id)
            const groupKeys = keysOf(group.entities)
            return (
              <Fragment key={group.id}>
                {/* ---------- CẤP 1: phân hệ ---------- */}
                {/* Cấp 1 dùng CÙNG độ cao + vằn chẵn/lẻ như cấp 2 (theo yêu cầu):
                    tham gia chung một dải zebra của bảng. Phân cấp thể hiện bằng
                    mũi tên xổ + chữ đậm + thụt lề, KHÔNG bằng màu nền riêng. */}
                {/* Cao 53px cho BẰNG dòng cấp 2 — cấp 2 bị ô Select phạm vi kéo cao
                    hơn h-12 (48px), nên cấp 1 ghim đúng chiều cao đó. */}
                <TableRow className="h-[53px] bg-card even:bg-row-stripe hover:bg-accent even:hover:bg-accent">
                  <TableCell className="sticky left-0 z-10 border-r bg-inherit">
                    {/*  Nút xổ và nút "chọn hết" là HAI nút cạnh nhau, không lồng
                         nhau: `<button>` trong `<button>` là HTML không hợp lệ,
                         Chrome tự tách thẻ ra và cú bấm rơi vào nút ngoài. */}
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        className="flex min-w-0 items-center gap-1.5 text-left font-semibold"
                        onClick={() => toggleCollapse(group.id)}
                      >
                        {isOpen ? (
                          <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
                        ) : (
                          <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
                        )}
                        <span className="truncate">{group.title}</span>
                        <span className="shrink-0 text-[11px] font-normal tabular-nums text-muted-foreground">
                          {group.entities.length} mục
                        </span>
                      </button>

                      {!readOnly && (
                        <PermissionRowBulkButton
                          className="ml-auto"
                          allOn={cellsState(rows, groupKeys, actionKeys) === true}
                          label={`phân hệ ${group.title}`}
                          onClick={() => toggle(groupKeys, actionKeys)}
                        />
                      )}
                    </div>
                  </TableCell>

                  {actionKeys.map((action) => (
                    <TableCell key={action} className="text-center">
                      <Checkbox
                        className="mx-auto"
                        checked={cellsState(rows, groupKeys, [action])}
                        disabled={readOnly}
                        onCheckedChange={() => toggle(groupKeys, [action])}
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
                        className="h-12 bg-card even:bg-row-stripe hover:bg-accent even:hover:bg-accent"
                      >
                        <TableCell className="sticky left-0 z-10 border-r bg-inherit">
                          <div className="flex items-center gap-2 pl-6">
                            <span className="truncate font-medium">{entity.label}</span>
                            <span className="shrink-0 text-[11px] tabular-nums text-muted-foreground">
                              {grantedCount}/{actionKeys.length}
                            </span>

                            {!readOnly && (
                              <PermissionRowBulkButton
                                className="ml-auto"
                                allOn={grantedCount === actionKeys.length}
                                label={entity.label}
                                onClick={() => toggle([entity.key], actionKeys)}
                              />
                            )}
                          </div>
                        </TableCell>

                        {actionKeys.map((action) => (
                          <TableCell key={action} className="text-center">
                            <Checkbox
                              className="mx-auto"
                              checked={!!row[permissionField(action)]}
                              disabled={readOnly}
                              onCheckedChange={() => toggle([entity.key], [action])}
                              aria-label={`${entity.label} — ${action}`}
                            />
                          </TableCell>
                        ))}

                        <TableCell className="border-l">
                          <Select
                            value={row.scope || 'own'}
                            disabled={readOnly}
                            onValueChange={(scope) =>
                              onChange({ ...rows, [entity.key]: { ...row, scope } })
                            }
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
