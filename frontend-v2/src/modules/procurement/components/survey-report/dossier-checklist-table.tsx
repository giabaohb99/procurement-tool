import { CalendarClock, ChevronDown, ChevronRight } from 'lucide-react'
import { Fragment } from 'react'

import type { ApplicableDossier } from '@/modules/dossier/types/dossier-applicability'
import type { DossierType } from '@/modules/dossier/types/dossier-type'
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { ChecklistProgressBar, ChecklistRow } from './dossier-checklist-groups'
import {
  EXPIRY_TONE_CLASS,
  expiryTone,
  groupByPhase,
  isDossierDone,
  nearestExpiryDoc,
  type ChecklistGroup,
} from '../../utils/dossier-checklist-helpers'

/** Số cột của bảng — dùng cho `colSpan` của dải sổ. Khớp đúng `ITEM_TABLE_COLUMNS` bản gốc. */
const TABLE_COLUMNS = 6

interface DossierChecklistTableProps {
  /** Một dòng bảng cho mỗi nhóm: «Chung (cả phiếu)» rồi tới từng dòng hàng. */
  rows: ChecklistGroup[]
  /** TOÀN BỘ hồ sơ của phiếu — dòng TỔNG đếm theo đây, không theo bộ lọc. */
  allDocs: ApplicableDossier[]
  /** Danh mục Loại hồ sơ — dải sổ xếp hồ sơ theo giai đoạn nên cần tên + thứ tự. */
  types: DossierType[]
  /** Khóa của dòng đang SỔ. Mặc định mọi dòng đều gập, y như bản gốc. */
  openRows: Set<string>
  /** Đang lọc thì sổ hết, bất kể trạng thái gập — kẻo kết quả tìm nấp sau dòng gập. */
  forceOpen: boolean
  onToggleRow: (key: string) => void
  onEdit?: (doc: ApplicableDossier) => void
  onToggleDone?: (doc: ApplicableDossier) => void
  busy?: boolean
}

/**
 * CHẾ ĐỘ XEM «Theo dòng hàng» — chép `ReportItemTable` của khối *Báo cáo thực
 * hiện*: mỗi dòng hàng một dòng bảng, bấm để sổ hồ sơ của riêng nó, dưới cùng
 * là dòng TỔNG của cả phiếu.
 *
 * ⚠️ **Thiếu dòng «Thêm nút dòng hàng» của bản gốc, và thiếu CÓ LÝ DO.** Bên
 * kia «nút dòng hàng» là bản ghi người dùng tự đặt; ở đây dòng hàng là dòng
 * THẬT của tờ YCBG, thêm bớt ở màn sửa phiếu chứ không ở đây.
 */
export function DossierChecklistTable({
  rows,
  allDocs,
  types,
  openRows,
  forceOpen,
  onToggleRow,
  onEdit,
  onToggleDone,
  busy,
}: DossierChecklistTableProps) {
  const doneCount = allDocs.filter(isDossierDone).length

  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-8" />
            <TableHead>Dòng hàng</TableHead>
            <TableHead className="w-20 text-center">Hồ sơ</TableHead>
            <TableHead className="w-20 text-center">Đã xong</TableHead>
            <TableHead className="w-40">Tiến độ</TableHead>
            <TableHead className="w-32">Hạn gần nhất</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => {
            const open = forceOpen || openRows.has(row.key)
            return (
              <Fragment key={row.key}>
                <TableRow className="cursor-pointer" onClick={() => onToggleRow(row.key)}>
                  <TableCell className="text-muted-foreground">
                    {open ? (
                      <ChevronDown className="size-4" />
                    ) : (
                      <ChevronRight className="size-4" />
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="font-medium">{row.name}</span>
                  </TableCell>
                  <TableCell className="text-center tabular-nums">{row.docs.length}</TableCell>
                  <TableCell className="text-center tabular-nums">
                    {row.docs.filter(isDossierDone).length}
                  </TableCell>
                  <TableCell>
                    <ChecklistProgressBar docs={row.docs} className="w-full" />
                  </TableCell>
                  <TableCell>
                    <ChecklistExpiryChip docs={row.docs} />
                  </TableCell>
                </TableRow>
                {open && (
                  <TableRow className="hover:bg-transparent">
                    <TableCell colSpan={TABLE_COLUMNS} className="bg-muted/40 p-3">
                      <ChecklistRowDetail
                        docs={row.docs}
                        types={types}
                        onEdit={onEdit}
                        onToggleDone={onToggleDone}
                        busy={busy}
                      />
                    </TableCell>
                  </TableRow>
                )}
              </Fragment>
            )
          })}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={2} className="font-semibold">
              Tổng cả phiếu
            </TableCell>
            <TableCell className="text-center font-semibold tabular-nums">
              {allDocs.length}
            </TableCell>
            <TableCell className="text-center font-semibold tabular-nums">{doneCount}</TableCell>
            <TableCell>
              <ChecklistProgressBar docs={allDocs} className="w-full" />
            </TableCell>
            <TableCell>
              <ChecklistExpiryChip docs={allDocs} />
            </TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  )
}

/**
 * Dải sổ ra dưới một dòng hàng: hồ sơ của dòng đó, xếp theo GIAI ĐOẠN (= Loại
 * hồ sơ). Giai đoạn không có hồ sơ của dòng này thì bỏ qua — chép đúng
 * `ReportRowDetail`, bày đủ năm giai đoạn rỗng dưới từng dòng chỉ làm dải sổ
 * dài ra mà không nói thêm điều gì.
 */
function ChecklistRowDetail({
  docs,
  types,
  onEdit,
  onToggleDone,
  busy,
}: {
  docs: ApplicableDossier[]
  types: DossierType[]
  onEdit?: (doc: ApplicableDossier) => void
  onToggleDone?: (doc: ApplicableDossier) => void
  busy?: boolean
}) {
  if (docs.length === 0) {
    return <p className="text-xs text-muted-foreground">Chưa có hồ sơ nào ở dòng hàng này.</p>
  }

  return (
    <div className="space-y-4">
      {groupByPhase(docs, types).map((group, index) => (
        <div key={group.key} className="space-y-2">
          <div className="flex items-center gap-2.5">
            <span className="grid size-6 place-items-center rounded-md bg-navy text-xs font-semibold text-white dark:bg-muted dark:text-foreground">
              {index + 1}
            </span>
            <span className="text-sm font-semibold">{group.name}</span>
            {group.hint && <span className="text-xs text-muted-foreground">{group.hint}</span>}
            <ChecklistProgressBar docs={group.docs} className="ml-auto" />
          </div>
          <div className="space-y-1.5">
            {group.docs.map((doc) => (
              //  KHÔNG truyền `itemTag`: dòng bảng bên trên đã nói hồ sơ này
              //  thuộc dòng hàng nào, lặp lại chỉ chiếm chỗ của cột mô tả.
              <ChecklistRow
                key={doc.id}
                doc={doc}
                onEdit={onEdit}
                onToggleDone={onToggleDone}
                busy={busy}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * Ô «Hạn gần nhất» của bảng — chép `ExpiryChip` bản gốc. Không tờ nào có hạn
 * thì GẠCH NGANG chứ không để trống: ô trống đọc ra như dữ liệu chưa tải xong.
 */
function ChecklistExpiryChip({ docs }: { docs: ApplicableDossier[] }) {
  const nearest = nearestExpiryDoc(docs)
  if (!nearest?.expiry_date) return <span className="text-muted-foreground">—</span>
  return (
    <span
      title={`Hết hiệu lực ${formatDate(nearest.expiry_date)} · ${nearest.expiry_state_label}`}
      className={cn(
        'inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums',
        EXPIRY_TONE_CLASS[expiryTone(nearest.expiry_state)],
      )}
    >
      <CalendarClock className="size-3" />
      {formatDate(nearest.expiry_date)}
    </span>
  )
}
