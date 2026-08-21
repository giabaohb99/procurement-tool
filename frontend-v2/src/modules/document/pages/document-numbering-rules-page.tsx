import { Plus, Tags } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { CatalogTable } from '../components/catalog-table'
import { IssueCodeDialog } from '../components/issue-code-dialog'
import { useDocumentNumberingRules } from '../hooks/use-document-numbering-rules'
import {
  NUMBERING_DIRECTIONS,
  type DocumentNumberingRule,
  type NumberingDirection,
} from '../types/document-numbering-rule'

/** Phạm vi áp dụng đọc thành chữ — dùng cho cả cột và ô tìm kiếm. */
function scopeText(rule: DocumentNumberingRule) {
  const types = rule.doc_type_mode === 1 ? 'Tất cả loại văn bản' : rule.doc_type_names.join(', ')
  const books =
    rule.book_mode === 1
      ? 'Tất cả sổ'
      : rule.book_mode === 3
        ? 'Không vào sổ'
        : rule.book_names.join(', ')
  return { types, books }
}

/**
 * DANH SÁCH QUY TẮC ĐÁNH SỐ — ba tab theo chiều văn bản: đến · đi · nội bộ.
 *
 * Dựng đúng khuôn của Sổ văn bản: tab nằm ngay dưới tiêu đề (ngoài card), bảng
 * là `CatalogTable` dùng chung, và **thêm/sửa đi sang trang riêng** chứ không mở
 * hộp thoại — form quy tắc dài (mẫu số + hai khối phạm vi) nên nhồi vào hộp
 * thoại là phải cuộn trong khung cuộn.
 *
 * Chiều ghi lên URL nên gửi link cho nhau vẫn ra đúng tab, và trang chi tiết
 * quay lại được đúng chỗ vừa đứng.
 */
export function DocumentNumberingRulesPage() {
  const navigate = useNavigate()
  const [direction, setDirection] = useUrlParamState('direction', '1')
  const [maDialogOpen, setMaDialogOpen] = useState(false)

  const { data, isLoading } = useDocumentNumberingRules(Number(direction) as NumberingDirection)
  const items = useMemo(() => data?.items ?? [], [data?.items])

  const columns = useMemo<DataTableColumn<DocumentNumberingRule>[]>(
    () => [
      {
        key: 'pattern',
        header: 'Quy tắc đánh số',
        width: 280,
        hideable: false,
        cell: (row) => (
          <div>
            <div className="font-mono font-medium text-navy">{row.pattern}</div>
            <div className="mt-1 text-xs text-muted-foreground">
              Ưu tiên {row.priority}
              {row.has_issued_numbers ? ' · Đã cấp số' : ''}
            </div>
          </div>
        ),
      },
      {
        key: 'scope',
        header: 'Đối tượng áp dụng',
        width: 320,
        cell: (row) => {
          const scope = scopeText(row)
          return (
            <div>
              <div className="line-clamp-1 font-medium">{scope.types}</div>
              <div className="line-clamp-1 text-xs text-muted-foreground">{scope.books}</div>
            </div>
          )
        },
      },
      {
        key: 'start_no',
        header: 'Bắt đầu',
        width: 100,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{row.start_no}</span>,
      },
      {
        key: 'reset_yearly',
        header: 'Cách đếm',
        width: 150,
        cell: (row) => (row.reset_yearly ? 'Theo từng năm' : 'Liên tục các năm'),
      },
      {
        key: 'allow_manual',
        header: 'Sửa số',
        width: 120,
        defaultHidden: true,
        cell: (row) => (row.allow_manual ? 'Cho phép' : 'Không'),
      },
      {
        key: 'is_active',
        header: 'Trạng thái',
        width: 120,
        cell: (row) => (
          <Badge variant={row.is_active ? 'default' : 'secondary'}>
            {row.is_active ? 'Đang dùng' : 'Ngừng dùng'}
          </Badge>
        ),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Quy tắc đánh số"
        description="Thiết lập mẫu số hiệu và bộ đếm tự động cho từng chiều văn bản."
        actions={
          <>
            {/*  Sửa mã ngay tại đây (CR-118): mẫu số hiệu ghép từ mã của pháp
                 nhân · phòng ban · loại văn bản · sổ, mà bốn thứ đó vốn nằm ở
                 bốn màn thuộc ba phân hệ — và ba trong bốn màn người khai quy
                 tắc có thể không có quyền vào. */}
            <Button variant="outline" onClick={() => setMaDialogOpen(true)}>
              <Tags className="size-4" />
              Mã đưa vào số hiệu
            </Button>

            <Button
              onClick={() =>
                navigate(`${appRoutes.document.numberingRuleNew}?direction=${direction}`)
              }
            >
              <Plus className="size-4" />
              Thêm mới
            </Button>
          </>
        }
      />

      <IssueCodeDialog open={maDialogOpen} onOpenChange={setMaDialogOpen} />

      <Tabs value={direction} onValueChange={setDirection} className="mb-4">
        <TabsList>
          {NUMBERING_DIRECTIONS.map((item) => (
            <TabsTrigger key={item.value} value={String(item.value)}>
              {item.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <CatalogTable
        // Khóa nhớ layout tách theo tab, giống Sổ văn bản: ba chiều có nhu cầu
        // ẩn/hiện cột khác nhau.
        storageKey={`document.numbering-rules.${direction}`}
        items={items}
        columns={columns}
        searchFields={(row) => {
          const scope = scopeText(row)
          return [row.pattern, scope.types, scope.books]
        }}
        searchPlaceholder="Tìm theo mẫu số hoặc phạm vi áp dụng…"
        detailPath={appRoutes.document.numberingRuleDetail}
        emptyMessage={
          isLoading ? 'Đang tải quy tắc…' : 'Chưa có quy tắc nào khớp điều kiện đang lọc.'
        }
      />
    </PageContainer>
  )
}
