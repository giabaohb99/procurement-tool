import { Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { LineApproveBadge } from '@/modules/procurement/components/document-status-badge'
import { SURVEY_APPROVE_OPTIONS } from '@/modules/procurement/types/survey-detail'
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
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { useSupplierSurveys } from '../hooks/use-supplier-surveys'
import type { Supplier } from '../types/supplier'
import type { SupplierSurveyLine, SupplierSurveyProductLine } from '../types/supplier-survey'
import { SURVEY_APPROVE_ALL, filterSurveyLines } from '../utils/supplier-survey-filter'

type SubTab = 'ncc' | 'sp'

/**
 * Tab "Khảo sát của NCC" trên trang chi tiết nhà cung cấp.
 *
 * Hai bảng con dùng CHUNG một bộ lọc (trạng thái duyệt + từ khóa): người dùng
 * đang truy một đợt khảo sát nên đổi tab mà bộ lọc reset thì phải gõ lại.
 */
export function SupplierSurveysPanel({ supplier }: { supplier: Supplier }) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canRead = can('survey', 'read')

  const [subTab, setSubTab] = useState<SubTab>('ncc')
  const [approve, setApprove] = useState<string>(SURVEY_APPROVE_ALL)
  const [keyword, setKeyword] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data, isLoading, isError, refetch } = useSupplierSurveys(
    { taxCode: supplier.tax_code, supplierCode: supplier.code },
    { enabled: canRead },
  )

  const supplierLines = useMemo(
    () =>
      filterSurveyLines(data?.supplier_lines ?? [], keyword, approve, (line) => [
        line.survey_code,
        line.supplier_code,
        line.supplier_name,
        line.tax_code,
        line.contact_person,
        line.contact_phone,
      ]),
    [data?.supplier_lines, keyword, approve],
  )

  const productLines = useMemo(
    () =>
      filterSurveyLines(data?.product_lines ?? [], keyword, approve, (line) => [
        line.survey_code,
        line.internal_code,
        line.product_name,
        line.quote_unit,
      ]),
    [data?.product_lines, keyword, approve],
  )

  const supplierColumns = useMemo<DataTableColumn<SupplierSurveyLine>[]>(
    () => [
      {
        key: 'survey_code',
        header: 'Mã phiếu',
        width: 150,
        hideable: false,
        defaultPinned: true,
        cell: (line) => (
          <span className="font-semibold text-primary">{line.survey_code || '—'}</span>
        ),
      },
      {
        key: 'contact_date',
        header: 'Ngày liên hệ',
        width: 130,
        cell: (line) => formatDate(line.contact_date) || '—',
      },
      { key: 'supplier_code', header: 'NCC (viết tắt)', width: 150, cell: (l) => l.supplier_code },
      {
        key: 'supplier_name',
        header: 'Tên pháp lý',
        width: 280,
        wrap: true,
        cell: (l) => l.supplier_name,
      },
      { key: 'tax_code', header: 'Mã số thuế', width: 140, cell: (l) => l.tax_code },
      { key: 'contact_person', header: 'Người liên hệ', width: 180, cell: (l) => l.contact_person },
      { key: 'contact_phone', header: 'Điện thoại', width: 140, cell: (l) => l.contact_phone },
      {
        key: 'line_approve',
        header: 'Duyệt',
        width: 140,
        cell: (l) => <LineApproveBadge status={l.line_approve} />,
      },
      { key: 'note', header: 'Ghi chú', width: 240, wrap: true, defaultHidden: true, cell: (l) => l.note },
    ],
    [],
  )

  const productColumns = useMemo<DataTableColumn<SupplierSurveyProductLine>[]>(
    () => [
      {
        key: 'survey_code',
        header: 'Mã phiếu',
        width: 150,
        hideable: false,
        defaultPinned: true,
        cell: (line) => (
          <span className="font-semibold text-primary">{line.survey_code || '—'}</span>
        ),
      },
      { key: 'internal_code', header: 'Mã hàng', width: 150, cell: (l) => l.internal_code },
      {
        key: 'product_name',
        header: 'Tên sản phẩm',
        width: 300,
        wrap: true,
        cell: (l) => l.product_name,
      },
      { key: 'quote_unit', header: 'ĐVT báo giá', width: 130, cell: (l) => l.quote_unit },
      {
        key: 'price_by_volume',
        header: 'Giá theo sản lượng',
        width: 170,
        align: 'right',
        // Đơn giá giữ tới 4 số lẻ (xem `format-money.ts`) — làm tròn tới đồng ở
        // đây là báo giá lệch so với phiếu khảo sát gốc.
        cell: (l) => <span className="tabular-nums">{formatUnitPrice(l.price_by_volume)}</span>,
      },
      {
        key: 'moq',
        header: 'MOQ',
        width: 120,
        align: 'right',
        cell: (l) => <span className="tabular-nums">{formatQuantity(l.moq)}</span>,
      },
      {
        key: 'line_approve',
        header: 'Duyệt',
        width: 140,
        cell: (l) => <LineApproveBadge status={l.line_approve} />,
      },
      { key: 'note', header: 'Ghi chú', width: 240, wrap: true, defaultHidden: true, cell: (l) => l.note },
    ],
    [],
  )

  if (!canRead) {
    return (
      <Card className="p-10 text-center text-sm text-muted-foreground">
        Tài khoản của bạn chưa được cấp quyền đọc Phiếu khảo sát.
      </Card>
    )
  }

  function resetPage() {
    setPage(1)
  }

  const openSurvey = (surveyId: number) => {
    if (surveyId > 0) navigate(appRoutes.procurement.surveyDetail(surveyId))
  }

  const toolbar = (
    <div className="flex flex-wrap items-center gap-3">
      <Select
        value={approve}
        onValueChange={(next) => {
          setApprove(next)
          resetPage()
        }}
      >
        <SelectTrigger className="h-9 w-48">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={SURVEY_APPROVE_ALL}>Tất cả trạng thái</SelectItem>
          {SURVEY_APPROVE_OPTIONS.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <div className="relative w-72">
        <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
        <Input
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value)
            resetPage()
          }}
          placeholder="Tìm mã phiếu, tên, mã hàng…"
          className="h-9 pl-9 pr-8 text-sm"
        />
        {keyword && (
          <button
            type="button"
            onClick={() => {
              setKeyword('')
              resetPage()
            }}
            className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
            aria-label="Xóa từ khóa"
          >
            <X className="size-4" />
          </button>
        )}
      </div>
    </div>
  )

  const paginate = <T,>(rows: T[]) => rows.slice((page - 1) * pageSize, page * pageSize)

  const pagination = (total: number) => ({
    page,
    pageSize,
    total,
    onPageChange: setPage,
    onPageSizeChange: (size: number) => {
      setPageSize(size)
      resetPage()
    },
    unitLabel: 'dòng',
  })

  const emptyMessage =
    keyword || approve !== SURVEY_APPROVE_ALL
      ? 'Không có dòng khảo sát nào khớp bộ lọc.'
      : 'Nhà cung cấp này chưa xuất hiện trong phiếu khảo sát nào.'

  return (
    <div className="space-y-4">
      <Tabs
        value={subTab}
        onValueChange={(next) => {
          setSubTab(next as SubTab)
          resetPage()
        }}
      >
        <TabsList>
          <TabsTrigger value="ncc">Khảo sát NCC ({supplierLines.length})</TabsTrigger>
          <TabsTrigger value="sp">Khảo sát Sản phẩm ({productLines.length})</TabsTrigger>
        </TabsList>
      </Tabs>

      {/*
        Hai bảng KHÔNG nằm trong `TabsContent`: chúng dùng chung state phân trang
        và bộ lọc, để Radix tự tháo lắp nội dung thì đổi tab là bố cục cột đã nhớ
        bị dựng lại từ đầu.
      */}
      <Card className="p-4">
        {subTab === 'ncc' ? (
          <DataTable
            toolbar={toolbar}
            columns={supplierColumns}
            rows={isLoading ? undefined : paginate(supplierLines)}
            getRowId={(l) => l.line_id}
            isLoading={isLoading}
            isError={isError}
            onRefresh={() => refetch()}
            onRowClick={(l) => openSurvey(l.survey_id)}
            storageKey="production.supplier.surveys.ncc"
            emptyMessage={emptyMessage}
            pagination={pagination(supplierLines.length)}
          />
        ) : (
          <DataTable
            toolbar={toolbar}
            columns={productColumns}
            rows={isLoading ? undefined : paginate(productLines)}
            getRowId={(l) => l.line_id}
            isLoading={isLoading}
            isError={isError}
            onRefresh={() => refetch()}
            onRowClick={(l) => openSurvey(l.survey_id)}
            storageKey="production.supplier.surveys.sp"
            emptyMessage={emptyMessage}
            pagination={pagination(productLines.length)}
          />
        )}
      </Card>
    </div>
  )
}
