import { Plus, Search } from 'lucide-react'
import { useState } from 'react'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { SupplierFormDialog } from '../components/supplier-form-dialog'
import { useSuppliers } from '../hooks/use-suppliers'
import { SUPPLIER_TYPE_LABELS, type Supplier } from '../types/supplier'

/**
 * Màn danh sách mẫu: tìm kiếm có debounce + react-query + phân quyền theo nút.
 * Dùng file này làm khuôn khi dựng các màn danh sách khác.
 */
export function SupplierListPage() {
  const [keyword, setKeyword] = useState('')
  const [editing, setEditing] = useState<Supplier | null>(null)
  const [isFormOpen, setFormOpen] = useState(false)

  const debouncedKeyword = useDebouncedValue(keyword)
  const { can } = usePermission()

  // `name` nằm trong whitelist FILTERABLE của backend -> lọc LIKE %keyword%.
  const { data, isLoading, isError } = useSuppliers(
    debouncedKeyword ? { name: debouncedKeyword } : {},
  )

  function openCreateForm() {
    setEditing(null)
    setFormOpen(true)
  }

  function openEditForm(supplier: Supplier) {
    setEditing(supplier)
    setFormOpen(true)
  }

  return (
    <>
      <PageHeader
        title="Nhà cung cấp"
        description="Danh mục nhà cung cấp hàng hóa và đơn vị vận chuyển."
        actions={
          <PermissionGate entity="supplier" action="create">
            <Button onClick={openCreateForm}>
              <Plus className="size-4" />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      <Card className="p-4">
        <div className="relative mb-4 max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Tìm theo tên nhà cung cấp…"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-36">Tên viết tắt</TableHead>
              <TableHead>Tên pháp lý</TableHead>
              <TableHead className="w-48">Loại</TableHead>
              <TableHead className="w-36">Mã số thuế</TableHead>
              <TableHead className="w-24 text-right">VAT</TableHead>
              <TableHead className="w-28">Trạng thái</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {isLoading &&
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={index}>
                  <TableCell colSpan={6}>
                    <Skeleton className="h-6 w-full" />
                  </TableCell>
                </TableRow>
              ))}

            {isError && (
              <TableRow>
                <TableCell colSpan={6} className="py-10 text-center text-destructive">
                  Không tải được danh sách. Kiểm tra kết nối hoặc quyền truy cập.
                </TableCell>
              </TableRow>
            )}

            {data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                  Chưa có nhà cung cấp nào.
                </TableCell>
              </TableRow>
            )}

            {data?.items.map((supplier) => (
              <TableRow
                key={supplier.id}
                // Không có quyền sửa thì bấm vào dòng cũng không mở form.
                className={can('supplier', 'write') ? 'cursor-pointer' : undefined}
                onClick={() => can('supplier', 'write') && openEditForm(supplier)}
              >
                <TableCell className="font-medium">{supplier.code}</TableCell>
                <TableCell>{supplier.name}</TableCell>
                <TableCell>{SUPPLIER_TYPE_LABELS[supplier.supplier_type]}</TableCell>
                <TableCell>{supplier.tax_code}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {Math.round(supplier.vat * 1000) / 10}%
                </TableCell>
                <TableCell>
                  <Badge variant={supplier.is_active ? 'default' : 'secondary'}>
                    {supplier.is_active ? 'Đang dùng' : 'Ngừng'}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {data && data.total > 0 && (
          <p className="mt-3 text-sm text-muted-foreground">
            Tổng {data.total.toLocaleString('vi-VN')} nhà cung cấp
          </p>
        )}
      </Card>

      <SupplierFormDialog
        open={isFormOpen}
        onOpenChange={setFormOpen}
        supplier={editing}
      />
    </>
  )
}
