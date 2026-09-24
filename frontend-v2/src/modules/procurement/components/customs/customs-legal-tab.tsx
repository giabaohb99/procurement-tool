// bao-CR-470 — thẻ «Pháp lý & thuế» (P-03 · P-04): cảnh báo pháp lý cho từ khóa đang tra,
// ô tra hóa chất trong danh mục pháp lý (tên / số CAS / công thức) và tra biểu thuế nhập
// khẩu theo mã HS. Ô tra hóa chất chạy độc lập với bộ lọc trang; đổi từ khóa / mã HS ở
// thanh lọc thì hai ô tự tra lại theo giá trị mới.
import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import { extractErrorMessage } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

import { useCustomsRegulationLookup, useCustomsTariff } from '../../hooks/use-customs'
import type { CustomsFilters, CustomsRegulationHit, CustomsTariffRow } from '../../types/customs'
import {
  formatBannedLabel,
  formatThresholdKg,
  isValidHsLookup,
  isValidRegulationLookup,
  sortRegulationsBySeverity,
} from '../../utils/customs'

interface CustomsLegalTabProps {
  filters: CustomsFilters
  alerts: CustomsRegulationHit[]
}

export function CustomsLegalTab({ filters, alerts }: CustomsLegalTabProps) {
  const [term, setTerm] = useState(filters.q)
  const [lookupTerm, setLookupTerm] = useState(() =>
    isValidRegulationLookup(filters.q) ? filters.q.trim() : '',
  )
  const [termError, setTermError] = useState('')
  const [hsCode, setHsCode] = useState(filters.hs_code)
  const [lookupHs, setLookupHs] = useState(() =>
    isValidHsLookup(filters.hs_code) ? filters.hs_code.trim() : '',
  )
  const [hsError, setHsError] = useState('')

  //  Đổi từ khóa / mã HS ở thanh lọc trang → hai ô tra theo giá trị mới.
  const queryChanged = useHasChanged(filters.q)
  if (queryChanged) {
    setTerm(filters.q)
    setLookupTerm(isValidRegulationLookup(filters.q) ? filters.q.trim() : '')
    setTermError('')
  }
  const hsChanged = useHasChanged(filters.hs_code)
  if (hsChanged) {
    setHsCode(filters.hs_code)
    setLookupHs(isValidHsLookup(filters.hs_code) ? filters.hs_code.trim() : '')
    setHsError('')
  }

  const regulation = useCustomsRegulationLookup(lookupTerm)
  const tariff = useCustomsTariff(lookupHs)

  function submitTerm() {
    if (!isValidRegulationLookup(term)) {
      setTermError('Nhập ít nhất 2 ký tự: tên hóa chất, số CAS hoặc công thức.')
      return
    }
    setTermError('')
    setLookupTerm(term.trim())
  }

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
        Tra cứu tham khảo từ văn bản đã nạp (NĐ 24/2026/NĐ-CP · TT 75/2025/TT-BNNMT · TT
        01/2026/TT-BCT · biểu thuế 2026). Không thay cho ý kiến pháp chế — đối chiếu văn bản gốc
        trước khi quyết định.
      </p>

      {alerts.length > 0 && (
        <Card className="gap-3 p-4">
          <CardTitle className="text-base">Cảnh báo cho từ khóa «{filters.q}»</CardTitle>
          <RegulationTable items={alerts} />
        </Card>
      )}

      <Card className="gap-3 p-4">
        <CardTitle className="text-base">Tra hóa chất trong danh mục pháp lý</CardTitle>
        <div className="flex flex-wrap gap-2">
          <Input
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') submitTerm()
            }}
            placeholder="Tên, số CAS hoặc công thức (vd H2SO4, 7664-93-9, Ammonia)"
            aria-label="Tên, số CAS hoặc công thức hóa chất"
            className="min-w-0 flex-1 basis-64"
          />
          <Button type="button" onClick={submitTerm}>
            <Search className="size-4" />
            Tra
          </Button>
        </div>
        {termError && <p className="text-sm text-destructive">{termError}</p>}
        {regulation.isError && (
          <p className="text-sm text-destructive">{extractErrorMessage(regulation.error)}</p>
        )}
        {regulation.data?.formula_cas && (
          <p className="text-xs text-muted-foreground">
            Công thức {regulation.data.term} → CAS {regulation.data.formula_cas}
          </p>
        )}
        {lookupTerm && !regulation.isError && (
          <RegulationTable
            items={regulation.data?.items}
            isLoading={regulation.isLoading}
            emptyMessage="Không có trong danh mục nào đã nạp."
          />
        )}
      </Card>

      <Card className="gap-3 p-4">
        <CardTitle className="text-base">Biểu thuế nhập khẩu theo mã HS</CardTitle>
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

/**
 * bao-CR-477 — tông huy hiệu theo MỨC NGHIÊM TRỌNG (xem `regulationSeverity`): cấm và tiền chất
 * vũ khí hóa học = đỏ · có ngưỡng khối lượng = cam · phải công bố theo lô (thủ tục, không phải
 * giới hạn) = xanh · chỉ có tên trong danh mục = xám. Trước đây mọi thứ ngoài «cấm» và «ngưỡng»
 * đều xanh, nên tiền chất vũ khí hóa học trông nhẹ ngang một thủ tục công bố.
 */
const THRESHOLD_TONE = 'bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300'

function regulationTone(listCode: number): string {
  if (listCode === 10 || listCode === 3) return TONE_CLASS.danger
  if (listCode === 4) return THRESHOLD_TONE
  if (listCode === 11) return TONE_CLASS.progress
  return TONE_CLASS.neutral
}

interface RegulationTableProps {
  items: CustomsRegulationHit[] | undefined
  isLoading?: boolean
  emptyMessage?: string
}

function RegulationTable({ items, isLoading, emptyMessage }: RegulationTableProps) {
  const columns = useMemo<DataTableColumn<CustomsRegulationHit>[]>(
    () => [
      {
        key: 'list_label',
        header: 'Danh mục',
        width: 230,
        hideable: false,
        wrap: true,
        cell: (r) => (
          <Badge className={cn('whitespace-normal', regulationTone(r.list_code))}>
            {r.list_label || `Danh sách ${r.list_code}`}
          </Badge>
        ),
      },
      {
        key: 'name',
        header: 'Tên',
        width: 260,
        hideable: false,
        wrap: true,
        cell: (r) => (
          <span>
            {r.name}
            {r.name_vi && r.name_vi !== r.name && (
              <span className="block text-xs text-muted-foreground">{r.name_vi}</span>
            )}
          </span>
        ),
      },
      { key: 'cas_no', header: 'Số CAS', width: 120, hideable: false, cell: (r) => r.cas_no },
      //  bao-CR-477 — con số quan trọng nhất của dòng đứng thành CỘT RIÊNG, chữ to đậm; trước
      //  đây nó nằm lẫn giữa một câu chữ thường ở cột «Lưu ý», đọc lướt là trôi mất.
      {
        key: 'limit',
        header: 'Ngưỡng / Mức cấm',
        width: 150,
        hideable: false,
        cell: (r) => {
          if (r.list_code === 10) {
            return (
              <Badge className={cn('font-bold', TONE_CLASS.danger)}>
                {formatBannedLabel(r.banned_year)}
              </Badge>
            )
          }
          const threshold = formatThresholdKg(r.threshold_kg)
          if (!threshold) return null
          return (
            <span className="text-base font-bold tabular-nums text-orange-700 dark:text-orange-300">
              {threshold}
            </span>
          )
        },
      },
      {
        key: 'obligation',
        header: 'Lưu ý',
        width: 360,
        hideable: false,
        wrap: true,
        cell: (r) => r.obligation,
      },
    ],
    [],
  )

  //  bao-CR-477 — dòng nặng nhất lên đầu: tra «Ethylene glycol» ra bốn danh sách thì thứ cần
  //  thấy trước là dòng có nghĩa vụ, không phải dòng đứng đầu theo mã danh sách.
  const sortedItems = useMemo(() => (items ? sortRegulationsBySeverity(items) : items), [items])

  return (
    <DataTable
      columns={columns}
      rows={sortedItems}
      getRowId={(r) => r.id}
      isLoading={isLoading}
      emptyMessage={emptyMessage ?? 'Không có mục nào.'}
    />
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
