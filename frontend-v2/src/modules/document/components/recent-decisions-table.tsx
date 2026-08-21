import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ACTION_TONE } from '@/modules/approval/helpers/decision-tone'
import type { MyDecision } from '@/modules/approval/types/approval'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import { useMyDocumentDecisions } from '../hooks/use-my-document-approvals'

/** Khoảng nhìn lại. 30 ngày là mặc định — đủ phủ một chu kỳ làm việc. */
const KHOANG = [
  { value: '7', label: '7 ngày qua' },
  { value: '30', label: '30 ngày qua' },
  { value: '90', label: '90 ngày qua' },
]

/**
 * ĐÃ DUYỆT GẦN ĐÂY — nhìn lại văn bản chính mình vừa quyết định.
 *
 * Là một TAB của màn «Chờ tôi duyệt», không phải khối xếp dưới: hai bảng chồng
 * nhau thì mỗi bảng chỉ còn nửa màn hình và cái nào cũng cụt. Tab chia **tập dữ
 * liệu** (việc chưa làm / việc đã làm) nên đúng chỗ dùng tab — xem
 * `docs/ui/table.md` mục 3.
 *
 * Hai cột dễ đọc nhầm nên tách hẳn: **việc tôi đã làm** (duyệt / trả lại / từ
 * chối) và **trạng thái của phiếu bây giờ** — ký xong bước của mình mà phiếu
 * vẫn còn ba bước nữa là chuyện thường.
 *
 * ⚠️ Ô tìm và ô chọn khoảng đi vào prop `toolbar`, KHÔNG để trong `CardHeader`:
 * `DataTable` tự vẽ cụm ⟳ / Cột ở mép phải của chính hàng công cụ đó. Đặt ra
 * ngoài là màn hình có HAI hàng công cụ chồng nhau — đúng lỗi phải vá ở đây.
 * Xem `docs/ui/table.md` mục 3.
 */
export function RecentDecisionsTable() {
  const navigate = useNavigate()
  const [ngay, setNgay] = useState('30')
  const [tuKhoa, setTuKhoa] = useState('')
  const { items: tatCa, isLoading } = useMyDocumentDecisions(Number(ngay))

  const items = useMemo(() => {
    const can = tuKhoa.trim().toLowerCase()
    if (!can) return tatCa
    return tatCa.filter((row) =>
      [row.entity_code, row.entity_title, row.node_name, row.comment].some((o) =>
        (o ?? '').toLowerCase().includes(can),
      ),
    )
  }, [tatCa, tuKhoa])

  const columns = useMemo<DataTableColumn<MyDecision>[]>(
    () => [
      {
        key: 'decided_at',
        header: 'Lúc',
        width: 150,
        cell: (row) => <span className="tabular-nums">{formatDateTime(row.decided_at)}</span>,
      },
      {
        key: 'entity_code',
        header: 'Số hiệu',
        width: 170,
        hideable: false,
        cell: (row) => (
          <span className="truncate font-medium text-navy">
            {row.entity_code || <span className="text-muted-foreground">Chưa cấp số</span>}
          </span>
        ),
      },
      {
        key: 'entity_title',
        header: 'Tên văn bản',
        width: 300,
        //  Bảng chạy `table-fixed` nên ô không tự nong ra — chữ dài phải tự cắt.
        cell: (row) => <span className="truncate">{row.entity_title}</span>,
      },
      {
        key: 'action_label',
        header: 'Tôi đã',
        width: 110,
        cell: (row) => (
          <Badge variant={ACTION_TONE[row.action] ?? 'outline'}>{row.action_label}</Badge>
        ),
      },
      {
        key: 'node_name',
        header: 'Ở bước',
        width: 190,
        cell: (row) => (
          <span className="truncate">{row.node_name || `Bước ${row.node_seq}`}</span>
        ),
      },
      {
        key: 'instance_status_label',
        header: 'Phiếu bây giờ',
        width: 140,
        cell: (row) => (
          <span className="truncate text-muted-foreground">{row.instance_status_label}</span>
        ),
      },
      {
        key: 'comment',
        header: 'Ý kiến',
        width: 280,
        defaultHidden: true,
        cell: (row) => <span className="truncate">{row.comment}</span>,
      },
      {
        key: 'on_behalf_of_name',
        header: 'Bấm thay',
        width: 160,
        defaultHidden: true,
        cell: (row) =>
          row.on_behalf_of_name || <span className="text-muted-foreground">—</span>,
      },
    ],
    [],
  )

  return (
    //  Bộ ba fit chiều cao: `PageContainer fill` → `Card flex min-h-0 flex-1
    //  flex-col` → `DataTable fillHeight`. Thiếu một mắt là bảng không cao bằng
    //  khung (xem `docs/ui/table.md` mục 2).
    <Card className="flex min-h-0 flex-1 flex-col p-4">
      <DataTable
        columns={columns}
        rows={items}
        getRowId={(row) => row.id}
        storageKey="document.my-decisions"
        fillHeight
        isLoading={isLoading}
        onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.entity_id))}
        emptyMessage={
          tatCa.length > 0
            ? 'Không có dòng nào khớp từ khóa.'
            : 'Bạn chưa duyệt văn bản nào trong khoảng này.'
        }
        toolbar={
          <>
            <div className="relative w-full max-w-xs">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Tìm trong danh sách này…"
                value={tuKhoa}
                onChange={(event) => setTuKhoa(event.target.value)}
              />
            </div>

            <Select value={ngay} onValueChange={setNgay}>
              <SelectTrigger className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {KHOANG.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </>
        }
      />
    </Card>
  )
}
