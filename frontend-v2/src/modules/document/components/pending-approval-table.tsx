import { AlertTriangle, Inbox, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { MyTask } from '@/modules/approval/types/approval'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate } from '@/shared/utils/format-date'
import { useMyDocumentTasks } from '../hooks/use-my-document-approvals'

const TAT_CA = 'all'

/**
 * Bảng VĂN BẢN ĐANG CHỜ TÔI DUYỆT.
 *
 * **Tìm và lọc chạy NGAY TẠI TRÌNH DUYỆT**, khác các màn danh sách gọi API phân
 * trang: hộp việc của một người là danh sách ngắn (vài dòng tới vài chục) và đã
 * nằm sẵn trong bộ nhớ — gọi thêm một vòng mạng cho mỗi ký tự gõ là đắt hơn
 * chính việc lọc.
 *
 * Không có nút duyệt trên dòng: bấm dòng là mở văn bản ra đọc rồi duyệt tại đó.
 */
export function PendingApprovalTable() {
  const navigate = useNavigate()
  const { items: tatCa, isLoading } = useMyDocumentTasks()
  const [tuKhoa, setTuKhoa] = useState('')
  const [han, setHan] = useState(TAT_CA)
  const [nguoiTrinh, setNguoiTrinh] = useState(TAT_CA)

  //  Danh sách người trình dựng từ CHÍNH dữ liệu đang có, không hỏi danh mục
  //  nhân sự: ô lọc chỉ nên bày ra những cái thật sự lọc ra được dòng nào.
  const cacNguoiTrinh = useMemo(
    () => [...new Set(tatCa.map((row) => row.started_by_name).filter(Boolean))].sort(),
    [tatCa],
  )

  const items = useMemo(() => {
    const can = tuKhoa.trim().toLowerCase()
    return tatCa.filter((row) => {
      if (han !== TAT_CA && row.is_overdue !== (han === 'overdue')) return false
      if (nguoiTrinh !== TAT_CA && row.started_by_name !== nguoiTrinh) return false
      if (!can) return true
      return [row.entity_code, row.entity_title, row.node_name, row.started_by_name].some(
        (o) => (o ?? '').toLowerCase().includes(can),
      )
    })
  }, [tatCa, tuKhoa, han, nguoiTrinh])

  const soQuaHan = tatCa.filter((row) => row.is_overdue).length

  const columns = useMemo<DataTableColumn<MyTask>[]>(
    () => [
      {
        key: 'entity_code',
        header: 'Số hiệu',
        width: 180,
        hideable: false,
        cell: (row) => (
          <span className="font-medium text-navy">
            {/* Chưa duyệt thì thường chưa có số — nói rõ chứ đừng để ô trống. */}
            {row.entity_code || <span className="text-muted-foreground">Chưa cấp số</span>}
          </span>
        ),
      },
      {
        key: 'entity_title',
        header: 'Tên văn bản',
        width: 400,
        cell: (row) => <span className="truncate">{row.entity_title}</span>,
      },
      {
        key: 'node_name',
        header: 'Bước đang chờ',
        width: 210,
        cell: (row) => row.node_name || `Bước ${row.node_seq}`,
      },
      {
        key: 'started_by_name',
        header: 'Người trình',
        width: 170,
        cell: (row) => row.started_by_name,
      },
      {
        key: 'due_at',
        header: 'Hạn duyệt',
        width: 160,
        cell: (row) =>
          row.due_at ? (
            <span className={row.is_overdue ? 'font-medium text-destructive' : undefined}>
              {formatDate(row.due_at)}
              {row.is_overdue && ' · quá hạn'}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        key: 'on_behalf_of_name',
        header: 'Bấm thay',
        width: 170,
        //  Phải thấy TRƯỚC khi mở phiếu: ký thay người khác là việc khác hẳn ký
        //  cho mình, và nhật ký sẽ ghi cả hai tên.
        cell: (row) =>
          row.on_behalf_of_name || <span className="text-muted-foreground">—</span>,
      },
    ],
    [],
  )

  return (
    //  `contents` để hai con (băng cảnh báo + Card) nằm THẲNG trong lưới flex
    //  của tab: bọc thêm một `div` là Card mất `flex-1` và bảng không cao bằng
    //  khung nữa.
    <div className="contents">
      {soQuaHan > 0 && (
        <p className="mb-3 flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
          <span>
            <b>{soQuaHan}</b> văn bản đã quá hạn duyệt.
          </span>
        </p>
      )}

      {/*  Bộ ba fit chiều cao: `PageContainer fill` → `Card flex min-h-0 flex-1
           flex-col` → `DataTable fillHeight` (xem `docs/ui/table.md` mục 2). */}
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={items}
          getRowId={(row) => row.id}
          storageKey="document.pending-approval"
          fillHeight
          isLoading={isLoading}
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.entity_id))}
          emptyMessage={
            //  Phân biệt "hộp việc rỗng" với "lọc không ra gì": một bên là tin
            //  mừng, một bên là phải xóa bớt điều kiện.
            tatCa.length > 0
              ? 'Không có văn bản nào khớp điều kiện đang lọc.'
              : 'Không có văn bản nào đang chờ bạn duyệt.'
          }
          toolbar={
            <>
              <div className="relative w-full max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo số hiệu, tên, bước, người trình…"
                  value={tuKhoa}
                  onChange={(event) => setTuKhoa(event.target.value)}
                />
              </div>

              {/*  Lọc nhanh "quá hạn" để NGOÀI thanh công cụ: đó là câu người ta
                   hỏi mỗi sáng, giấu sau một cú bấm nữa là không ai dùng. */}
              <Select value={han} onValueChange={setHan}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={TAT_CA}>Mọi hạn duyệt</SelectItem>
                  <SelectItem value="overdue">Đã quá hạn</SelectItem>
                  <SelectItem value="ontime">Còn hạn</SelectItem>
                </SelectContent>
              </Select>

              {/* Chỉ bày ô lọc người trình khi có từ hai người trở lên — một
                  người thì ô đó không lọc ra được gì khác. */}
              {cacNguoiTrinh.length > 1 && (
                <Select value={nguoiTrinh} onValueChange={setNguoiTrinh}>
                  <SelectTrigger className="w-52">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={TAT_CA}>Mọi người trình</SelectItem>
                    {cacNguoiTrinh.map((ten) => (
                      <SelectItem key={ten} value={ten}>
                        {ten}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Inbox className="size-4" />
                {items.length} văn bản
              </span>
            </>
          }
        />
      </Card>
    </div>
  )
}
