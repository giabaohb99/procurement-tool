import { Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { listDossierDepartments } from '../api/dossier-api'
import { DOSSIER_COLUMNS } from '../config/dossier-columns'
import { useDossiers } from '../hooks/use-dossiers'
import { DOSSIER_STATUS_LABEL } from '../types/dossier'

/**
 * Mốc "tất cả" của ô CHỌN. Radix Select không nhận `value=""` (chuỗi rỗng là
 * tín hiệu xóa lựa chọn của nó), nên phải có một chuỗi thật; lớp gọi API đổi nó
 * về `''` trước khi gửi đi.
 */
const ALL = 'all'

/** Đổ ô chọn *Bộ phận*. Hằng số tầng module — dữ liệu mẫu không đổi lúc chạy. */
const DEPARTMENTS = listDossierDepartments()

/** Mã trạng thái luôn là SỐ (R2/QĐ-11); trên URL thì nó đi dưới dạng chuỗi. */
const STATUS_OPTIONS = Object.entries(DOSSIER_STATUS_LABEL)

/**
 * Danh sách hồ sơ — **màn MẪU, CHƯA ĐĂNG KÝ ROUTE**.
 *
 * ⚠️ Không chỗ nào gọi tới tệp này, và đó là chủ ý về BẢO MẬT: khóa quyền
 * `dossier` chưa có ở backend, mà mục menu không khai `entity` thì hiện với
 * **mọi người đăng nhập** — hôm nay lộ dữ liệu giả, ngày nối API thật thì lộ hồ
 * sơ pháp lý của công ty. Lý do đầy đủ và bốn việc phải làm để bật lại nằm ở
 * `modules/dossier/routes.tsx`. **Đừng thêm nó vào `routes` nếu chưa làm đủ.**
 *
 * Khuôn màn giữ nguyên vì đã theo đúng quy ước danh sách của dự án
 * (`docs/ui/table.md`): state bộ lọc trên URL, phân trang ngoài URL, `DataTable`
 * tự lo nút *Xóa lọc* / *Tải lại* / *Cột*. Nối backend là đổi ruột
 * `fetchDossiers`, trang không phải sửa.
 */
export function DossierListPage() {
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [department, setDepartment] = useUrlParamState('department', ALL)
  const [pageSize, setPageSize] = useState(20)
  //  Đổi bộ lọc là về trang 1 NGAY trong lượt render — xem
  //  `use-page-reset-on-filter-change.ts` về việc vì sao không dùng `useEffect`.
  const [page, setPage] = usePageResetOnFilterChange([debouncedValue, status, department])

  const { data, isLoading, isError } = useDossiers({
    keyword: debouncedValue,
    status: status === ALL ? '' : status,
    department: department === ALL ? '' : department,
    page,
    pageSize,
  })

  const isFiltering = debouncedValue !== '' || status !== ALL || department !== ALL

  return (
    <PageContainer fill className="gap-6">
      <PageHeader
        title="Hồ sơ"
        description={
          <span className="flex flex-wrap items-center gap-2">
            Kho hồ sơ của công ty — theo dõi nơi lưu bản gốc, người phụ trách và hạn hiệu lực.
            <Badge variant="outline" className="border-amber-300 text-amber-700 dark:text-amber-400">
              Dữ liệu mẫu
            </Badge>
          </span>
        }
        actions={
          <Button
            onClick={() =>
              toast.info('Màn tạo hồ sơ chưa dựng — bản mẫu mới có danh sách.')
            }
          >
            <Plus className="size-4" />
            Thêm hồ sơ
          </Button>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={DOSSIER_COLUMNS}
          rows={data?.items}
          getRowId={(row) => row.id}
          isLoading={isLoading}
          isError={isError}
          storageKey="dossier.dossiers"
          //  Hai câu khác nhau: rỗng vì bộ lọc ≠ rỗng vì chưa có hồ sơ nào. Một
          //  câu chung thì người vừa gõ nhầm một chữ đọc ra "chưa có dữ liệu".
          emptyMessage={
            isFiltering
              ? 'Không có hồ sơ nào khớp điều kiện đang lọc.'
              : 'Chưa có hồ sơ nào.'
          }
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'hồ sơ',
          }}
          toolbar={
            <>
              <div className="relative w-full max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo mã, tên, loại, người phụ trách…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {STATUS_OPTIONS.map(([code, label]) => (
                    <SelectItem key={code} value={code}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={department} onValueChange={setDepartment}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả bộ phận</SelectItem>
                  {DEPARTMENTS.map((name) => (
                    <SelectItem key={name} value={name}>
                      {name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
