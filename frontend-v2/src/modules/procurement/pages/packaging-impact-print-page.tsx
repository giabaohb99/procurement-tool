/**
 * duoc-CR-784 — BẢN IN Tác động giá bao bì (A4 nằm ngang). Mã đã chọn, giá giả định, khoảng ngày, từ khóa + cột xếp của
 * bảng sản phẩm (kèm lọc nâng cao) đi qua query string (xem `parseImpactPrintSearch`); trang tự nạp ĐỦ mọi sản phẩm bị ảnh hưởng (bảng trên
 * màn hình phân trang tại máy chủ), tới trần `IMPACT_PRINT_ROW_CAP` — quá thì cắt và báo rõ trên tờ giấy.
 *
 * Route đứng NGOÀI khung ứng dụng (như mọi trang in), cổng quyền ở `print-route-access.ts`.
 */
import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

import { extractErrorMessage } from '@/core/api'

import { PackagingPrintShell } from '../components/packaging-print-shell'
import {
  PrintImpactProducts,
  PrintImpactSelection,
} from '../components/packaging-impact-print-parts'
import { usePackagingImpactPrint } from '../hooks/use-packaging-impact-print'
import { describeCappedPrint } from '../utils/packaging-history-print'
import { describeImpactAdvancedFilters } from '../utils/packaging-impact-filters'
import { describeImpactFilters, parseImpactPrintSearch } from '../utils/packaging-impact-print'

export function PackagingImpactPrintPage() {
  const [searchParams] = useSearchParams()
  const request = useMemo(() => parseImpactPrintSearch(searchParams), [searchParams])
  const query = usePackagingImpactPrint(request)
  const data = query.data
  const noCode = request.codes.length === 0

  const status = noCode || query.isError ? 'error' : data ? 'ready' : 'loading'
  return (
    <PackagingPrintShell
      subtitle="Tác động giá bao bì"
      status={status}
      errorMessage={
        noCode
          ? 'Chưa chọn mã nào để in — quay lại màn Tác động giá, chọn mã rồi bấm In.'
          : query.isError
            ? `Không tải được số liệu tác động giá: ${extractErrorMessage(query.error)}`
            : undefined
      }
    >
      {data && (
        <>
          <PrintImpactSelection
            codes={request.codes}
            extras={describeImpactFilters(request)}
            rows={data.selected}
          />
          {data.capped && (
            <p role="status" className="banner">
              {describeCappedPrint(data.products_total, 'sản phẩm')}
            </p>
          )}
          <PrintImpactProducts
            rows={data.products}
            matched={data.products_total}
            empty={
              request.q || describeImpactAdvancedFilters(request).length
                ? 'Không có sản phẩm khớp từ khóa / bộ lọc.'
                : 'Không có sản phẩm nào dùng các mã đã chọn.'
            }
          />
        </>
      )}
    </PackagingPrintShell>
  )
}
