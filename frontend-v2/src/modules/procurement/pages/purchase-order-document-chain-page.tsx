import {
  ArrowLeft,
  Eye,
  Download,
  File as FileIcon,
  FileImage,
  FileText,
  FolderArchive,
  FolderOpen,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatFileSize } from '@/shared/utils/format-file-size'
import { ChainFilePreviewDialog } from '../components/chain-file-preview-dialog'
import { documentChainApi } from '../api/document-chain-api'
import { useDocumentChain } from '../hooks/use-document-chain'
import { usePurchaseOrder } from '../hooks/use-purchase-order'
import type { ChainAttachment } from '../types/document-chain'
import type { ChainSourceGroup } from '../utils/group-document-chain'
import { groupDocumentChain, isPreviewableChainFile } from '../utils/group-document-chain'

/**
 * Trang «Chứng từ» của một đơn mua hàng — xem TOÀN BỘ hồ sơ của chuỗi
 * ĐMH → YCMH → Phiếu khảo sát → YCBG ở một chỗ, thay vì mở lần lượt bốn phiếu.
 *
 * Dời từ bản cũ `frontend/src/pages/Documents.tsx` (màn cuối cùng của kế hoạch
 * `doc/erp/13`). Khác bản cũ ba điểm, đều là lỗi của bản cũ:
 *  - khử tệp trùng (xem `groupDocumentChain`);
 *  - xem trước qua API có kiểm quyền chứ không trỏ thẳng kho lưu trữ;
 *  - vào bằng đường `/purchase-orders/:id/documents` nên F5 hay dán link đều
 *    còn đúng đơn — bản cũ đọc id từ query `?po=` của một route ngoài menu.
 */
export function PurchaseOrderDocumentChainPage() {
  const { id } = useParams()
  const purchaseOrderId = Number(id) || 0
  const navigate = useNavigate()
  const { can } = usePermission()

  const [preview, setPreview] = useState<ChainAttachment | null>(null)
  const [zipping, setZipping] = useState(false)

  const { data: order } = usePurchaseOrder(purchaseOrderId)
  const { data, isLoading, isError } = useDocumentChain(purchaseOrderId)

  const groups = useMemo(() => groupDocumentChain(data ?? []), [data])
  const total = useMemo(() => groups.reduce((sum, group) => sum + group.total, 0), [groups])

  const orderCode = order?.code ?? ''
  const backTo = appRoutes.procurement.purchaseOrderDetail(purchaseOrderId)

  async function downloadOne(file: ChainAttachment) {
    try {
      await documentChainApi.downloadChainFile(file.link_id, file.filename)
    } catch {
      // GET không tự bật toast (xem `http-client`) — im lặng là người dùng bấm
      // xong không thấy gì và tưởng máy treo.
      toast.error('Không tải được tệp này. Có thể bạn không còn quyền xem chứng từ gốc.')
    }
  }

  async function downloadAll() {
    setZipping(true)
    try {
      await documentChainApi.downloadChainZip(
        purchaseOrderId,
        `chung-tu-${orderCode || purchaseOrderId}.zip`,
      )
    } catch {
      toast.error('Không tải được chuỗi chứng từ. Có thể cả chuỗi chưa có tệp nào.')
    } finally {
      setZipping(false)
    }
  }

  if (!can('purchase_order', 'read')) {
    return (
      <ErrorState
        title="Không có quyền xem chứng từ"
        description="Hồ sơ chứng từ đi theo đơn mua hàng, nên cần quyền xem đơn mua hàng."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.purchaseOrders)}>
          <ArrowLeft />
          Về danh sách đơn hàng
        </Button>
      </ErrorState>
    )
  }

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-12 w-full" />
        <Skeleton className="h-96 w-full" />
      </PageContainer>
    )
  }

  if (isError) {
    return (
      <ErrorState
        title="Không mở được hồ sơ chứng từ"
        description="Đơn hàng có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" asChild>
          <Link to={backTo}>
            <ArrowLeft />
            Về đơn hàng
          </Link>
        </Button>
      </ErrorState>
    )
  }

  return (
    <PageContainer className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về đơn mua hàng">
          <Link to={backTo}>
            <ArrowLeft />
          </Link>
        </Button>

        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold tracking-tight text-navy dark:text-foreground">
            Chứng từ đơn {orderCode || `#${purchaseOrderId}`}
          </h1>
          <p className="text-sm text-muted-foreground">
            Toàn bộ hồ sơ của chuỗi — {total} tệp ở {groups.length} chứng từ
          </p>
        </div>

        <Button
          className="ml-auto"
          variant="outline"
          size="sm"
          disabled={zipping || total === 0}
          onClick={() => void downloadAll()}
        >
          <FolderArchive />
          {zipping ? 'Đang nén' : 'Tải tất cả (.zip)'}
        </Button>
      </div>

      {groups.length === 0 ? (
        <p className="rounded-lg border border-dashed bg-muted/20 py-10 text-center text-sm text-muted-foreground">
          Cả chuỗi chưa có tệp đính kèm nào.
        </p>
      ) : (
        groups.map((group) => (
          <SourceCard
            key={group.source}
            group={group}
            onPreview={setPreview}
            onDownload={(file) => void downloadOne(file)}
          />
        ))
      )}

      <ChainFilePreviewDialog
        file={preview}
        onClose={() => setPreview(null)}
        onDownload={(file) => void downloadOne(file)}
      />
    </PageContainer>
  )
}

interface SourceCardProps {
  group: ChainSourceGroup
  onPreview: (file: ChainAttachment) => void
  onDownload: (file: ChainAttachment) => void
}

/** Một nấc của chuỗi: ĐMH · YCMH · Phiếu khảo sát · YCBG. */
function SourceCard({ group, onPreview, onDownload }: SourceCardProps) {
  return (
    <Card className="gap-4 py-4">
      <CardHeader className="min-h-9 flex flex-row items-center gap-2 border-b px-4 pb-3!">
        <FolderOpen className="size-4 text-primary" />
        <CardTitle className="text-base text-navy dark:text-foreground">{group.label}</CardTitle>
        {group.code && (
          <span className="font-mono text-xs text-muted-foreground">{group.code}</span>
        )}
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
          {group.total} tệp
        </span>
      </CardHeader>

      <CardContent className="space-y-4 px-4">
        {group.types.map((type) => (
          <div key={type.label} className="space-y-1.5">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              {type.label}
            </p>
            <div className="divide-y rounded-lg border">
              {type.files.map((file) => (
                <FileRow
                  key={file.link_id}
                  file={file}
                  onPreview={onPreview}
                  onDownload={onDownload}
                />
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

interface FileRowProps {
  file: ChainAttachment
  onPreview: (file: ChainAttachment) => void
  onDownload: (file: ChainAttachment) => void
}

function FileRow({ file, onPreview, onDownload }: FileRowProps) {
  return (
    <div className="flex items-center gap-3 px-3 py-2">
      {renderChainFileIcon(file)}

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm">{file.filename}</p>
        <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
      </div>

      {/* Tệp không xem trước được (Word/Excel, hoặc backend không trả đường đọc)
          thì bỏ hẳn nút, đừng để nút bấm vào mở ra khung trống. */}
      {isPreviewableChainFile(file) && (
        <Button type="button" variant="ghost" size="sm" onClick={() => onPreview(file)}>
          <Eye />
          Xem
        </Button>
      )}

      <Button type="button" variant="ghost" size="sm" onClick={() => onDownload(file)}>
        <Download />
        Tải
      </Button>
    </div>
  )
}

/**
 * Icon theo loại tệp. Trả thẳng phần tử đã dựng chứ không trả *component* rồi
 * để nơi gọi viết `<Icon />`: cách kia làm luật `react-hooks/static-components`
 * kêu "tạo component trong lúc render".
 */
function renderChainFileIcon(file: ChainAttachment) {
  const className = 'size-4 shrink-0 text-muted-foreground'
  if (file.content_type?.startsWith('image/')) return <FileImage className={className} />
  if (file.content_type?.includes('pdf') || /\.(pdf|docx?|xlsx?)$/i.test(file.filename)) {
    return <FileText className={className} />
  }
  return <FileIcon className={className} />
}
