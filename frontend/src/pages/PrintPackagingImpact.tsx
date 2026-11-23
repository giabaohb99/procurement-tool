import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchAllImpact, printErrorMessage } from '../api/packaging-print'
import type { PackagingImpactPrintData } from '../api/packaging-print'
import { PrintImpactProducts, PrintImpactSelection } from '../components/packaging/PackagingImpactPrintParts'
import PackagingPrintShell from '../components/packaging/PackagingPrintShell'
import { describeImpactAdvancedFilters } from '../utils/packaging-impact-filters'
import { cappedPrintNotice, describeImpactFilters, parseImpactPrintSearch } from '../utils/packaging-print'

/**
 * duoc-CR-784 — BẢN IN Tác động giá bao bì (A4 nằm ngang, bản v1). Mã đã chọn, giá giả định, khoảng ngày, từ khóa + lọc nâng cao + cột xếp của
 * bảng sản phẩm đi qua query string (xem `parseImpactPrintSearch`); trang tự nạp ĐỦ mọi sản phẩm bị ảnh hưởng (bảng trên màn
 * hình phân trang tại máy chủ), tới trần `PRINT_ROW_CAP` — quá thì cắt và báo rõ trên tờ giấy. Route đứng NGOÀI `AppLayout`.
 */
export default function PrintPackagingImpact() {
  const [sp] = useSearchParams()
  const query = sp.toString()
  const request = useMemo(() => parseImpactPrintSearch(new URLSearchParams(query)), [query])
  const noCode = request.codes.length === 0
  const [data, setData] = useState<PackagingImpactPrintData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    //  Link hỏng (không có mã nào): không gọi máy chủ, trang tự báo "chưa chọn mã".
    if (noCode) return
    let alive = true
    setData(null); setError('')
    fetchAllImpact(request)
      .then((d) => { if (alive) setData(d) })
      .catch((e) => { if (alive) setError(`Không tải được số liệu tác động giá: ${printErrorMessage(e)}`) })
    return () => { alive = false }
  }, [request, noCode])

  const message = noCode ? 'Chưa chọn mã nào để in — quay lại màn Tác động giá, chọn mã rồi bấm In.' : error
  return (
    <PackagingPrintShell subtitle="Tác động giá bao bì" status={message ? 'error' : data ? 'ready' : 'loading'} errorMessage={message}>
      {data && (
        <>
          <PrintImpactSelection codes={request.codes}
            extras={describeImpactFilters(request)} rows={data.selected} />
          {data.capped && <p role="status" className="banner">{cappedPrintNotice(data.products_total, 'sản phẩm')}</p>}
          <PrintImpactProducts rows={data.products} matched={data.products_total}
            empty={request.q || describeImpactAdvancedFilters(request).length ? 'Không có sản phẩm khớp từ khóa / bộ lọc.' : 'Không có sản phẩm nào dùng các mã đã chọn.'} />
        </>
      )}
    </PackagingPrintShell>
  )
}
