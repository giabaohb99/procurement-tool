/**
 * duoc-CR-784 — màn TÁC ĐỘNG TĂNG GIÁ BAO BÌ (bám `renderImpact` / `drawImpact` của bản mẫu
 * `Bao cao gia NVL san xuat - 11.2026.html`).
 *
 * Chọn một hoặc nhiều mã chai / nắp / nhãn / nhãn thùng / thùng → ba thẻ số liệu (mã đã chọn, sản phẩm bị ảnh
 * hưởng, sản phẩm tăng nhiều nhất /thùng), bảng mã đã chọn (giá cũ, mới, ô giá giả định), và bảng mọi sản phẩm dùng ít nhất một mã đó với chi phí bao bì /chai, /thùng cũ
 * và mới. Giá giả định trễ 400 ms rồi mới tính lại; dữ liệu cũ giữ nguyên trong lúc tính. Bảng sản phẩm phân
 * trang / tìm / lọc nâng cao / xếp tại MÁY CHỦ (có thể hàng nghìn sản phẩm khi chọn cả nhóm); ba thẻ luôn tính trên toàn bộ tập.
 */
import { Loader2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { PackagingExportExcelButton, PackagingPrintButton } from '../components/packaging-header-buttons'
import { exportPackagingImpact } from '../api/packaging-cost-api'
import { PackagingCodePicker } from '../components/packaging-code-picker'
import { PackagingImpactProductsTable } from '../components/packaging-impact-products-table'
import { PackagingImpactSelectedTable } from '../components/packaging-impact-selected-table'
import { usePackagingCodeOptions, usePackagingImpact } from '../hooks/use-packaging-impact'
import { usePackagingImpactTableState } from '../hooks/use-packaging-impact-table-state'
import type { PackagingImpactRequest } from '../types/packaging-cost-types'
import { sortPackagingCodeOptions } from '../utils/packaging-code-match'
import { impactFiltersToRequest } from '../utils/packaging-impact-filters'
import { packagingImpactPrintHref } from '../utils/packaging-impact-print'
import { buildImpactUrlSearch, parseImpactUrlState } from '../utils/packaging-impact-url-state'

/** Chỉ gửi giả định của mã còn đang chọn — bỏ mã khỏi danh sách là bỏ luôn giá giả định của nó. */
function pickAssumed(
  codes: string[],
  assumed: Record<string, number>,
): Record<string, number> | undefined {
  const picked = Object.fromEntries(
    codes.filter((code) => assumed[code] != null).map((code) => [code, assumed[code]]),
  )
  return Object.keys(picked).length ? picked : undefined
}

export function PackagingImpactPage() {
  const { can } = usePermission()
  const isMobile = useIsMobile()
  const [searchParams, setSearchParams] = useSearchParams()
  //  Lựa chọn của màn sống trên URL (F5 / gửi link mở lại đúng chỗ): đọc MỘT lần lúc mở màn, sau đó state là nguồn và
  //  URL đi theo (effect bên dưới, `replace` — gõ giá không đẻ ra cả chục mục lịch sử của nút Quay lại).
  const [initial] = useState(() => parseImpactUrlState(searchParams))
  const [pickedCodes, setCodes] = useState<string[]>(initial.codes)
  const [assumed, setAssumed] = useState<Record<string, number>>(initial.assumed)
  const [range, setRange] = useState({ from: initial.dateFrom, to: initial.dateTo })
  const debouncedAssumed = useDebouncedValue(assumed, 400)
  const once = useSingleFlight()
  const [exporting, setExporting] = useState(false)

  const optionsQuery = usePackagingCodeOptions()
  const options = useMemo(
    () => sortPackagingCodeOptions(optionsQuery.data ?? []),
    [optionsQuery.data],
  )
  //  Mã lạ trên URL (gõ tay, mã đã bỏ khỏi định mức) rơi khỏi lựa chọn ngay khi có danh sách mã; chưa nạp xong thì giữ.
  const codes = useMemo(() => {
    if (!optionsQuery.data) return pickedCodes
    const known = new Set(optionsQuery.data.map((option) => option.code))
    return pickedCodes.filter((code) => known.has(code))
  }, [optionsQuery.data, pickedCodes])

  const table = usePackagingImpactTableState([codes, range], initial)

  const urlSearch = buildImpactUrlSearch({
    codes,
    //  Giá giả định + từ khóa lên URL theo nhịp ĐÃ HOÃN (400 / 250 ms) — không ghi lại URL mỗi phím gõ.
    assumed: debouncedAssumed,
    dateFrom: range.from,
    dateTo: range.to,
    q: table.query,
    filters: table.filters,
    sortBy: table.sortBy,
    sortDir: table.sortDir,
    page: table.page,
  })
  useEffect(() => {
    if (urlSearch !== searchParams.toString()) {
      setSearchParams(new URLSearchParams(urlSearch), { replace: true })
    }
  }, [urlSearch, searchParams, setSearchParams])
  /** Đang lọc bằng từ khóa / lọc nâng cao → thẻ "Sản phẩm bị ảnh hưởng" ghi "Đang lọc: x / M". */

  /** Phần thân dùng chung cho tính toán và Xuất Excel (cùng bộ lọc + thứ tự); chưa kèm trang. */
  const filterBody = useMemo<PackagingImpactRequest>(
    () => ({
      codes,
      assumed_prices: pickAssumed(codes, debouncedAssumed),
      date_from: range.from || undefined,
      date_to: range.to || undefined,
      q: table.query || undefined,
      ...impactFiltersToRequest(table.filters),
      //  Chưa chọn cột xếp thì KHÔNG gửi — máy chủ xếp mặc định theo mã HH.
      ...(table.sortBy ? { sort_by: table.sortBy, sort_dir: table.sortDir } : {}),
    }),
    [codes, debouncedAssumed, range, table.query, table.filters, table.sortBy, table.sortDir],
  )
  const body = useMemo<PackagingImpactRequest>(
    () => ({ ...filterBody, page: table.page, page_size: table.pageSize }),
    [filterBody, table.page, table.pageSize],
  )
  const impact = usePackagingImpact(body)
  const data = codes.length ? impact.data : undefined

  const changeAssumed = useCallback((code: string, price: number | null) => {
    setAssumed((prev) => {
      const next = { ...prev }
      if (price == null) delete next[code]
      else next[code] = price
      return next
    })
  }, [])
  const removeCode = useCallback(
    (code: string) => setCodes((prev) => prev.filter((item) => item !== code)),
    [],
  )

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        //  Xuất theo giá giả định ĐANG GÕ, không đợi nhịp trễ — người bấm Xuất muốn đúng số trên ô.
        await exportPackagingImpact({ ...filterBody, assumed_prices: pickAssumed(codes, assumed) })
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })


  return (
    <PageContainer className="space-y-4">
      <PageHeader
        title="Tác động tăng giá bao bì"
        //  Câu giới thiệu ẩn ở khổ điện thoại (cùng nếp các màn CRUD): đọc một lần rồi thôi mà ăn ba bốn dòng đầu màn.
        description={
          isMobile
            ? undefined
            : 'Chọn mã bao bì, nhập giá giả định để xem sản phẩm nào tăng chi phí bao nhiêu trước khi NCC chốt giá. Đơn vị VNĐ, chưa VAT.'
        }
        actions={
          <>
            <DateRangePicker
              from={range.from}
              to={range.to}
              placeholder="Khoảng ngày tính min – max"
              className="max-md:min-w-0 max-md:flex-1"
              onChange={(from, to) => setRange({ from, to })}
            />
            {/* In = xem (quyền đọc). Mở tab mới, mã + giá giả định ĐANG GÕ + từ khóa / cột xếp của bảng; trang in tự nạp đủ mọi sản phẩm. */}
            {can('packaging_impact', 'read') && (
              <PackagingPrintButton
                href={
                  codes.length
                    ? packagingImpactPrintHref({ ...filterBody, assumed_prices: pickAssumed(codes, assumed) })
                    : undefined
                }
                disabledTitle="Chọn ít nhất một mã để in"
              />
            )}
            {can('packaging_impact', 'export') && (
              <PackagingExportExcelButton exporting={exporting} disabled={!codes.length} onClick={() => void exportExcel()} />
            )}
          </>
        }
      />

      <Card className="gap-3 p-4 max-md:gap-2 max-md:p-3">
        <PackagingCodePicker
          options={options}
          value={codes}
          onChange={setCodes}
          loading={optionsQuery.isLoading}
        />
        {codes.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Bấm vào ô trên để chọn một hoặc nhiều mã. Gõ tên nhóm (<b>chai</b>, <b>nắp</b>,{' '}
            <b>nhãn</b>…) rồi bấm <b>Chọn tất cả</b> để chọn cả nhóm.
          </p>
        ) : (
          <>
            {/* Ba thẻ số liệu (Mã đã chọn · Sản phẩm bị ảnh hưởng · Tăng nhiều nhất /thùng) đã bỏ theo người chủ (23/11/2026);
                bản in vẫn giữ thẻ. */}
            <PackagingImpactSelectedTable
              rows={data?.selected}
              isLoading={impact.isLoading}
              isError={impact.isError}
              assumed={assumed}
              onAssumedChange={changeAssumed}
              onRemove={removeCode}
              //  Số liệu đã lên thẻ; thanh công cụ chỉ còn vòng quay báo đang tính lại (bỏ hết mã = nút x trong ô chọn mã).
              toolbar={
                impact.isFetching ? (
                  <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
                ) : undefined
              }
            />
          </>
        )}
      </Card>

      {codes.length > 0 && (
        <div>
          <Card className="gap-3 p-4 max-md:gap-2 max-md:p-3">
            <PackagingImpactProductsTable
              rows={data?.products}
              total={data?.products_total ?? 0}
              affected={data?.kpis.affected_products}
              isLoading={impact.isLoading}
              isError={impact.isError}
              view={table}
            />
          </Card>
        </div>
      )}
    </PageContainer>
  )
}
