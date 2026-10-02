// Mục «Thuế» của Tra cứu thị trường — tra biểu thuế nhập khẩu 2026 theo mã HS (P-04). Tách từ
// mục «Pháp lý & thuế» cũ (29/09/2026); phần hóa chất theo văn bản sang mục «Pháp lý». Ô mã HS
// lấy sẵn mã HS đang lọc ở thanh lọc trang, đổi mã ở đó thì ô này tra lại theo.
import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import { extractErrorMessage } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Card, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'

import { useCustomsTariff } from '../../hooks/use-customs'
import type { CustomsFilters, CustomsTariffRow } from '../../types/customs'
import { isValidHsLookup } from '../../utils/customs'

interface CustomsTariffTabProps {
  filters: CustomsFilters
}

export function CustomsTariffTab({ filters }: CustomsTariffTabProps) {
  const [hsCode, setHsCode] = useState(filters.hs_code)
  const [lookupHs, setLookupHs] = useState(() =>
    isValidHsLookup(filters.hs_code) ? filters.hs_code.trim() : '',
  )
  const [hsError, setHsError] = useState('')

  //  Đổi mã HS ở thanh lọc trang → ô tra theo giá trị mới.
  const hsChanged = useHasChanged(filters.hs_code)
  if (hsChanged) {
    setHsCode(filters.hs_code)
    setLookupHs(isValidHsLookup(filters.hs_code) ? filters.hs_code.trim() : '')
    setHsError('')
  }

  const tariff = useCustomsTariff(lookupHs)

  function submitHs() {
    if (!isValidHsLookup(hsCode)) {
      setHsError('Mã HS phải có ít nhất 4 chữ số.')
      return
    }
    setHsError('')
    setLookupHs(hsCode.trim())
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted-foreground">
        Tra cứu tham khảo từ biểu thuế 2026 đã nạp — đối chiếu văn bản gốc trước khi
        quyết định.
      </p>
      <Card className="gap-3 p-4">
        <CardTitle className="text-base">Biểu thuế theo mã HS</CardTitle>
        <div className="flex flex-wrap gap-2">
          <Input
            value={hsCode}
            onChange={(event) => setHsCode(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') submitHs()
            }}
            placeholder="Mã HS, vd 38089199"
            aria-label="Mã HS"
            className="w-56"
          />
          <Button type="button" onClick={submitHs}>
            <Search className="size-4" />
            Tra
          </Button>
        </div>
        {hsError && <p className="text-sm text-destructive">{hsError}</p>}
        {tariff.isError && (
          <p className="text-sm text-destructive">{extractErrorMessage(tariff.error)}</p>
        )}
        {lookupHs && !tariff.isError && (
          <TariffTables rows={tariff.data} isLoading={tariff.isLoading} />
        )}
      </Card>
    </div>
  )
}

/** Thuế suất để nguyên chữ của biểu thuế (có dòng ghi "*", "5 (a)"…) — trống là gạch ngang. */
function formatRate(value: string | number | null | undefined): string {
  return value === null || value === undefined || value === '' ? '—' : String(value)
}

function TariffTables({
  rows,
  isLoading,
}: {
  rows: CustomsTariffRow[] | undefined
  isLoading: boolean
}) {
  const leaves = useMemo(() => (rows ?? []).filter((row) => row.hs_code.length >= 8), [rows])
  const ftaKeys = useMemo(
    () => [...new Set(leaves.flatMap((row) => Object.keys(row.fta ?? {})))].sort(),
    [leaves],
  )

  const columns = useMemo<DataTableColumn<CustomsTariffRow>[]>(
    () => [
      {
        key: 'hs_code',
        header: 'Mã HS',
        width: 110,
        hideable: false,
        //  Mã cha (4 · 6 số) chỉ để đọc mô tả nhóm — chữ mờ; dòng lá (8 số) đậm.
        cell: (r) => (
          <span className={r.hs_code.length >= 8 ? 'font-semibold' : 'text-muted-foreground'}>
            {r.hs_code}
          </span>
        ),
      },
      { key: 'name_vn', header: 'Mô tả', width: 360, hideable: false, wrap: true, cell: (r) => r.name_vn },
      { key: 'unit', header: 'ĐVT', width: 80, hideable: false, cell: (r) => r.unit },
      {
        key: 'rate_normal',
        header: 'Thông thường',
        width: 110,
        align: 'right',
        hideable: false,
        cell: (r) => formatRate(r.rate_normal),
      },
      {
        key: 'rate_mfn',
        header: 'Ưu đãi (MFN)',
        width: 110,
        align: 'right',
        hideable: false,
        cell: (r) => formatRate(r.rate_mfn),
      },
      {
        key: 'rate_vat',
        header: 'VAT',
        width: 80,
        align: 'right',
        hideable: false,
        cell: (r) => formatRate(r.rate_vat),
      },
      { key: 'policy', header: 'Chính sách', width: 240, hideable: false, wrap: true, cell: (r) => r.policy },
    ],
    [],
  )

  const ftaColumns = useMemo<DataTableColumn<CustomsTariffRow>[]>(
    () => [
      { key: 'hs_code', header: 'Mã HS', width: 110, hideable: false, cell: (r) => r.hs_code },
      ...ftaKeys.map<DataTableColumn<CustomsTariffRow>>((key) => ({
        key: `fta-${key}`,
        header: key,
        width: 90,
        align: 'right',
        hideable: false,
        cell: (r) => formatRate(r.fta?.[key]),
      })),
    ],
    [ftaKeys],
  )

  return (
    <div className="flex flex-col gap-3">
      <DataTable
        columns={columns}
        rows={rows}
        getRowId={(r) => r.hs_code}
        isLoading={isLoading}
        emptyMessage="Không có mã này trong biểu thuế đã nạp."
      />
      {ftaKeys.length > 0 && (
        <>
          <p className="text-sm font-semibold">Thuế suất theo hiệp định thương mại tự do (%)</p>
          <DataTable columns={ftaColumns} rows={leaves} getRowId={(r) => r.hs_code} />
        </>
      )}
    </div>
  )
}
