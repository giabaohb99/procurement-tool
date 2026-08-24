import { Search } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  applyClientFilter,
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Badge } from '@/shared/ui/badge'
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
import { DOCUMENT_APPLIED_FILTER_FIELDS } from '../config/document-applied-filter-fields'
import { effectiveLabel } from '../helpers/document-status'
import { useDocumentsAppliedToMe } from '../hooks/use-document-scopes'
import { useSecurityLevelLabel } from '../hooks/use-document-catalogs'
import { SECURITY_LEVEL_KIND_CONFIDENTIAL } from '../types/security-level'
import type { DocumentRecord } from '../types/document-record'

const ALL = 'all'

/**
 * `preserveParams`: thiếu tên nào ở đây thì bấm "Áp dụng" bộ lọc nâng cao sẽ
 * xóa mất tham số đó khỏi URL. Không cần kể `q` — `searchParamName` giữ sẵn.
 * `tab` phải có, nếu không áp bộ lọc xong là màn hình nhảy về tab kia.
 */
const FILTER_CONFIG = {
  fields: DOCUMENT_APPLIED_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['review', 'tab'],
}

export function IncomingDocumentsTab() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <IncomingDocumentsContent />
    </FilterProvider>
  )
}

/**
 * VĂN BẢN ĐẾN — những văn bản mà người đang đăng nhập **nằm trong phạm vi áp
 * dụng**, tức là phải làm theo (F05, trước đây là màn riêng "Áp dụng cho tôi").
 *
 * Khác "tất cả văn bản tôi đọc được": đọc được mà không thuộc phạm vi áp dụng
 * thì không hiện ở đây — đó là tab «Văn bản đi» bên cạnh.
 *
 * ⚠️ Tìm và lọc chạy NGAY TẠI TRÌNH DUYỆT, khác mọi màn danh sách khác trong
 * hệ. Không phải chọn cho tiện: `/api/documents/applies-to-me` tính phạm vi bằng
 * vòng lặp Python rồi mới trả về nên không có tầng truy vấn để cắm điều kiện
 * vào, mà đằng nào nó cũng trả hết một lượt. Ngày nào endpoint nhận được tham số
 * lọc thì đổi sang `useFilterQuery` như các màn khác.
 */
function IncomingDocumentsContent() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useDocumentsAppliedToMe()
  const { appliedState } = useFilterContext()
  const secrecyLabel = useSecurityLevelLabel()

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [review, setReview] = useUrlParamState('review', ALL)

  const rows = useMemo(() => {
    const needle = debouncedValue.trim().toLowerCase()
    const found = (data?.items ?? []).filter((row) => {
      if (review !== ALL && row.needs_review !== (review === 'yes')) return false
      if (!needle) return true
      //  Quét đúng những cột đang bày trên bảng cộng thêm số hiệu cũ của bản
      //  giấy (C12) — người ta hay tra bằng chính con số ghi trên tờ giấy.
      return [row.title, row.display_code, row.doc_type_name, row.legacy_code, row.keywords]
        .some((field) => (field ?? '').toLowerCase().includes(needle))
    })
    return applyClientFilter(found, appliedState)
  }, [data?.items, debouncedValue, review, appliedState])

  const columns = useMemo<DataTableColumn<DocumentRecord>[]>(
    () => [
      {
        key: 'display_code',
        header: 'Số hiệu',
        width: 180,
        hideable: false,
        cell: (row) => <span className="font-mono text-navy">{row.display_code || '—'}</span>,
      },
      {
        key: 'title',
        header: 'Trích yếu',
        width: 380,
        cell: (row) => (
          <div>
            <div className="font-medium">{row.title}</div>
            {row.needs_review && <div className="text-xs text-amber-800">Cần rà lại</div>}
          </div>
        ),
      },
      { key: 'doc_type_name', header: 'Loại', width: 160, cell: (row) => row.doc_type_name },
      {
        key: 'status_label',
        header: 'Trạng thái',
        width: 140,
        //  Nhãn TÍNH RA lúc hiển thị (hết hạn theo ngày) như bảng Văn bản, chứ
        //  không phải trạng thái thô — hai bảng nói khác nhau về cùng một văn
        //  bản là chuyện không giải thích được với người dùng.
        cell: (row) => {
          const label = effectiveLabel(row)
          return <Badge variant={label.variant}>{label.text}</Badge>
        },
      },
      {
        key: 'effective_date',
        header: 'Hiệu lực từ',
        width: 140,
        cell: (row) => (row.effective_date ? formatDate(row.effective_date) : '—'),
      },
      {
        key: 'company_name',
        header: 'Pháp nhân ban hành',
        width: 220,
        defaultHidden: true,
        cell: (row) => row.company_name,
      },
      {
        key: 'department_name',
        header: 'Phòng chủ trì',
        width: 170,
        defaultHidden: true,
        cell: (row) => row.department_name,
      },
      {
        key: 'secrecy_level',
        header: 'Mức mật',
        width: 120,
        defaultHidden: true,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {secrecyLabel(SECURITY_LEVEL_KIND_CONFIDENTIAL, row.secrecy_level)}
          </Badge>
        ),
      },
      {
        key: 'owner_name',
        header: 'Người chịu trách nhiệm',
        width: 180,
        defaultHidden: true,
        cell: (row) => row.owner_name,
      },
    ],
    [secrecyLabel],
  )

  return (
    <Card className="flex min-h-0 flex-1 flex-col p-4">
      <DataTable
        columns={columns}
        rows={rows}
        getRowId={(row) => row.id}
        storageKey="document.applies-to-me"
        fillHeight
        isLoading={isLoading}
        isError={isError}
        onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
        emptyMessage={
          //  Phân biệt "chưa có gì" với "lọc không ra gì": hai câu này dẫn tới
          //  hai hành động khác hẳn nhau — một bên đi hỏi người khai phạm vi,
          //  một bên chỉ cần xóa điều kiện lọc.
          (data?.items?.length ?? 0) > 0
            ? 'Không có văn bản nào khớp điều kiện đang lọc.'
            : 'Chưa có văn bản nào áp dụng cho bạn.'
        }
        toolbar={
          <>
            <div className="relative w-full max-w-xs">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Tìm theo trích yếu, số hiệu, loại, từ khóa…"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
              />
            </div>

            {/*  Lọc nhanh "Cần rà lại" để sẵn ngoài thanh công cụ chứ không
                 giấu trong bộ lọc nâng cao: đó là lý do chính người ta mở tab
                 này ra — văn bản mình phải làm theo vừa bị đổi. */}
            <Select value={review} onValueChange={setReview}>
              <SelectTrigger className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Tất cả văn bản</SelectItem>
                <SelectItem value="yes">Cần rà lại</SelectItem>
                <SelectItem value="no">Không cần rà lại</SelectItem>
              </SelectContent>
            </Select>

            <ConditionalFilter />
          </>
        }
      />
    </Card>
  )
}
