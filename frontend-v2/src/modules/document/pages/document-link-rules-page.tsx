import { Plus } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { CatalogTable } from '../components/catalog-table'
import { countText } from '../helpers/link-rule-count-text'
import { useDocumentLinkRules } from '../hooks/use-document-link-rules'
import type { DocTypeLinkRule } from '../types/document-link-rule'

/**
 * DANH SÁCH QUY TẮC QUAN HỆ CHA–CON (E01).
 *
 * Bảng nhỏ — 15–25 dòng cho cả hệ — nhưng nó điều khiển hai thứ người dùng gặp
 * hằng ngày: form soạn thảo tự hiện ô quan hệ nào, và văn bản nào bị chặn gửi
 * duyệt vì thiếu quan hệ bắt buộc.
 */
export function DocumentLinkRulesPage() {
  const navigate = useNavigate()
  const { data } = useDocumentLinkRules()
  const items = useMemo(() => data?.items ?? [], [data?.items])

  const columns = useMemo<DataTableColumn<DocTypeLinkRule>[]>(
    () => [
      {
        key: 'source_type_name',
        header: 'Loại văn bản áp dụng',
        width: 220,
        hideable: false,
        cell: (row) => <span className="font-medium text-navy">{row.source_type_name}</span>,
      },
      {
        key: 'relation_label',
        header: 'Loại quan hệ',
        width: 150,
        cell: (row) => (
          <div className="flex items-center gap-2">
            <span>{row.relation_label}</span>
            {/*  Dòng trích từ khóa ba cột — nói ngay ở danh sách để người khai
                 khỏi mở ra rồi mới thấy ô bị tắt. */}
            {row.is_locked && <Badge variant="secondary">Khóa</Badge>}
          </div>
        ),
      },
      {
        key: 'target_type_name',
        header: 'Trỏ tới loại',
        width: 220,
        cell: (row) => row.target_type_name,
      },
      {
        key: 'is_required',
        header: 'Ràng buộc',
        width: 130,
        cell: (row) =>
          row.is_required ? (
            <Badge>Bắt buộc</Badge>
          ) : (
            <span className="text-muted-foreground">Tùy chọn</span>
          ),
      },
      {
        key: 'count',
        header: 'Số văn bản',
        width: 140,
        cell: (row) => countText(row),
      },
      {
        key: 'inherit_code',
        header: 'Đánh số nối theo',
        width: 130,
        defaultHidden: true,
        cell: (row) => (row.inherit_code ? 'Có' : 'Không'),
      },
      {
        key: 'inherit_secrecy',
        header: 'Không hạ mức mật',
        width: 150,
        defaultHidden: true,
        cell: (row) => (row.inherit_secrecy ? 'Có' : 'Không'),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Quy tắc quan hệ"
        description="Toàn cảnh quy tắc quan hệ của cả hệ thống. Khai theo từng loại thì mở trang loại văn bản tương ứng."
        actions={
          <Button onClick={() => navigate(appRoutes.document.linkRuleNew)}>
            <Plus className="size-4" />
            Thêm mới
          </Button>
        }
      />

      <CatalogTable
        storageKey="document.link-rules"
        items={items}
        columns={columns}
        searchFields={(row) => [
          row.source_type_name,
          row.relation_label,
          row.target_type_name,
        ]}
        searchPlaceholder="Tìm theo loại văn bản hoặc quan hệ…"
        detailPath={appRoutes.document.linkRuleDetail}
        emptyMessage="Chưa có quy tắc quan hệ nào."
      />
    </PageContainer>
  )
}
