import { ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Skeleton } from '@/shared/ui/skeleton'
import { useSuppliers } from '../hooks/use-suppliers'
import type { Contract } from '../types/contract'

/**
 * Tab "Đối tác liên quan" — bên còn lại đứng tên trên hợp đồng.
 *
 * Đối tác là NHÀ CUNG CẤP thì tra ngược hồ sơ NCC theo `party_code` để xem nhanh
 * MST / người liên hệ mà không phải rời màn hình.
 *
 * ⚠️ Lọc bằng `code`, KHÔNG bằng `search`: whitelist `FILTERABLE` của NCC chỉ có
 * code · name · tax_code · supplier_type · is_active, tham số lạ bị `apply_filters`
 * bỏ qua IM LẶNG và API trả về nguyên trang đầu — bản cũ lấy `items[0]` nên gắn hồ
 * sơ của một NCC bất kỳ vào hợp đồng. Lọc kiểu LIKE nên vẫn phải khớp lại đúng mã.
 */
export function ContractPartnerTab({ contract }: { contract: Contract }) {
  const { can } = usePermission()
  const isSupplier = contract.party_type === 'Nhà cung cấp'
  const canReadSupplier = can('supplier', 'read')

  const { data, isLoading } = useSuppliers(
    { code: contract.party_code, page_size: 20 },
    { enabled: isSupplier && canReadSupplier && Boolean(contract.party_code) },
  )
  const supplier = data?.items?.find((item) => item.code === contract.party_code)

  return (
    <Card className="gap-4 p-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label>Loại đối tác ký kết</Label>
          <ReadOnlyValue>{contract.party_type}</ReadOnlyValue>
        </div>
        <div className="space-y-1.5">
          <Label>Mã đối tác</Label>
          <ReadOnlyValue>{contract.party_code}</ReadOnlyValue>
        </div>
        <div className="space-y-1.5 sm:col-span-2">
          <Label>Tên đối tác</Label>
          <ReadOnlyValue>{contract.party_name}</ReadOnlyValue>
        </div>
      </div>

      {isSupplier && (
        <div className="space-y-3 border-t pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-navy dark:text-foreground">
              Hồ sơ nhà cung cấp liên kết
            </h3>
            {supplier && (
              <Button variant="outline" size="sm" asChild>
                <Link to={appRoutes.production.supplierDetail(supplier.id)}>
                  <ExternalLink />
                  Xem hồ sơ nhà cung cấp
                </Link>
              </Button>
            )}
          </div>

          <PartnerSupplierBody
            canRead={canReadSupplier}
            hasCode={Boolean(contract.party_code)}
            isLoading={isLoading}
            partyCode={contract.party_code}
            supplier={supplier}
          />
        </div>
      )}
    </Card>
  )
}

function PartnerSupplierBody({
  canRead,
  hasCode,
  isLoading,
  partyCode,
  supplier,
}: {
  canRead: boolean
  hasCode: boolean
  isLoading: boolean
  partyCode: string
  supplier?: { tax_code: string; contact_person: string; phone: string }
}) {
  if (!canRead) {
    return (
      <p className="text-sm text-muted-foreground">
        Tài khoản của bạn chưa có quyền đọc danh mục Nhà cung cấp nên không xem được hồ sơ liên
        kết.
      </p>
    )
  }

  if (!hasCode) {
    return (
      <p className="text-sm text-muted-foreground">
        Hợp đồng chưa điền mã nhà cung cấp nên không tra được hồ sơ. Điền mã ở tab Thông tin để
        nối hai bên với nhau.
      </p>
    )
  }

  if (isLoading) return <Skeleton className="h-20 w-full" />

  if (!supplier) {
    return (
      <p className="text-sm text-muted-foreground">
        Không tìm thấy nhà cung cấp mang mã &quot;{partyCode}&quot; trong danh mục.
      </p>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <div className="space-y-1.5">
        <Label>Mã số thuế</Label>
        <ReadOnlyValue>{supplier.tax_code}</ReadOnlyValue>
      </div>
      <div className="space-y-1.5">
        <Label>Người liên hệ</Label>
        <ReadOnlyValue>{supplier.contact_person}</ReadOnlyValue>
      </div>
      <div className="space-y-1.5">
        <Label>Điện thoại</Label>
        <ReadOnlyValue>{supplier.phone}</ReadOnlyValue>
      </div>
    </div>
  )
}
