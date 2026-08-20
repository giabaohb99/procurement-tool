import {
  Download,
  // Đổi tên: icon `File` của lucide trùng tên với kiểu `File` của trình duyệt —
  // ngay bên dưới có `selected: File[]` là tệp thật, để trùng tên đọc rất dễ nhầm.
  File as FileIcon,
  FileImage,
  FileText,
  FolderArchive,
  FolderClosed,
  FolderOpen,
  Info,
  Paperclip,
  Trash2,
  Upload,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatFileSize } from '@/shared/utils/format-file-size'
import type { AttachmentFile } from '../api/purchase-request-support-api'
import {
  useDeletePurchaseRequestAttachment,
  useDocumentTypes,
  usePurchaseRequestAttachments,
  useUploadPurchaseRequestAttachments,
} from '../hooks/use-purchase-request-support'
import {
  groupAttachmentsByType,
  OTHER_DOC_TYPE,
  withOtherType,
} from '../utils/document-attachment-groups'
import { DocumentStatusBadge } from './document-status-badge'
import { DocumentUploadDialog } from './document-upload-dialog'

interface DocumentAttachmentsCardProps {
  /** `purchase_request` hoặc `purchase_order` — quyết định chính sách file ở backend. */
  entity: string
  entityId: number
  canManage: boolean
  /**
   * Tình trạng hồ sơ chứng từ của ĐMH, hiện CHỈ ĐỌC ở đây.
   *
   * Ô sửa nằm ở thẻ Thông tin chung; đặt thêm một ô sửa nữa ngay trên đống tệp
   * thì cùng một trường có hai chỗ bấm, người dùng không biết chỗ nào là thật.
   */
  documentStatus?: string
}

/** Giá trị của chip "Tất cả": xem hết, không lọc theo mục nào. */
const ALL = '__all__'

/**
 * Chứng từ của chứng từ mua hàng — dùng chung cho YCMH và ĐMH.
 *
 * Bố cục theo MỤC chứ không phải một danh sách phẳng: hồ sơ một đơn hàng gồm
 * nhiều loại giấy tờ (báo giá, PO ký, hóa đơn GTGT, biên bản giao nhận…), người
 * làm kế toán vào đây để tìm ĐÚNG MỘT loại chứ ít khi đọc cả xấp. Mỗi mục là
 * một chip đếm số tệp, bấm vào là mở mục đó và cũng là chọn luôn nơi lưu cho
 * tệp sắp thả vào — nên không còn cảnh chọn nhầm loại rồi cả xấp rơi vào "Khác"
 * như hồi ô chọn nằm rời trên đầu thẻ.
 */
export function DocumentAttachmentsCard({
  entity,
  entityId,
  canManage,
  documentStatus = '',
}: DocumentAttachmentsCardProps) {
  const [openType, setOpenType] = useState(ALL)
  const [uploadType, setUploadType] = useState(OTHER_DOC_TYPE)
  const [zipping, setZipping] = useState(false)
  /** Hộp thoại tải theo loại; `docType` là mục điền sẵn cho mục đầu tiên. */
  const [uploadDialog, setUploadDialog] = useState({ open: false, docType: OTHER_DOC_TYPE })
  const { data: files, isLoading, isError } = usePurchaseRequestAttachments(entity, entityId)
  const { data: documentTypes } = useDocumentTypes()
  const upload = useUploadPurchaseRequestAttachments(entity, entityId)
  const remove = useDeletePurchaseRequestAttachment(entity, entityId)
  const isNew = entityId <= 0

  const options = useMemo(() => withOtherType(documentTypes ?? []), [documentTypes])
  const groups = useMemo(() => groupAttachmentsByType(files ?? [], options), [files, options])
  // Xóa hết tệp của mục đang mở thì mục đó biến mất khỏi hàng chip — không quay
  // về "Tất cả" là màn hình còn mỗi hàng chip với một khoảng trống bên dưới.
  const activeType = groups.some((group) => group.type === openType) ? openType : ALL
  const shown = activeType === ALL ? groups : groups.filter((group) => group.type === activeType)
  const uploadLabel = options.find((option) => option.value === uploadType)?.label ?? 'Khác'

  async function handleFiles(selected: File[]) {
    await upload.mutateAsync({ files: selected, docType: uploadType })
  }

  async function handleChainZip() {
    setZipping(true)
    try {
      await downloadFile(
        `/api/attachments/chain/zip?entity=purchase_order&entity_id=${entityId}`,
        `chung-tu-don-${entityId}.zip`,
      )
    } catch {
      // Lỗi của GET không được bật toast tự động (xem `http-client`), mà đây là
      // hành động người dùng bấm nên im lặng là coi như hỏng mà không ai biết.
      toast.error('Không tải được chuỗi chứng từ. Có thể cả chuỗi chưa có tệp nào.')
    } finally {
      setZipping(false)
    }
  }

  return (
    <Card className="gap-4 py-4">
      {/*
        `pb-3!` chứ không phải `pb-3`: `CardHeader` của shadcn có luật
        `[.border-b]:pb-6` — selector kép nên thắng class thường, không đánh dấu
        important thì mọi thẻ có gạch chân đều bị đệm 24px, cao thấp lệch nhau.
      */}
      <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
        <div className="flex items-center gap-2">
          <Paperclip className="size-4 text-primary" />
          <CardTitle className="text-base text-navy dark:text-foreground">
            Chứng từ &amp; Tài liệu đính kèm
          </CardTitle>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {files?.length ?? 0} tệp
          </span>
          {documentStatus && (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              Hồ sơ:
              <DocumentStatusBadge status={documentStatus} />
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {canManage && !isNew && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              title="Tải nhiều loại chứng từ trong một lượt và xếp sẵn vào đúng mục"
              onClick={() => setUploadDialog({ open: true, docType: OTHER_DOC_TYPE })}
            >
              <Upload />
              Upload chứng từ
            </Button>
          )}

          {entity === 'purchase_order' && !isNew && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={zipping}
              title="Tải toàn bộ chứng từ của cả chuỗi (YCMH, phiếu khảo sát, đơn hàng) trong một tệp nén"
              onClick={() => void handleChainZip()}
            >
              <FolderArchive />
              {zipping ? 'Đang nén' : 'Tải chuỗi chứng từ (.zip)'}
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 px-4">
        {isNew ? (
          <p className="flex items-center justify-center gap-2 rounded-lg border border-dashed bg-muted/20 py-5 text-center text-sm text-muted-foreground">
            <Info className="size-4" />
            Vui lòng lưu chứng từ trước khi đính kèm tài liệu.
          </p>
        ) : (
          <>
            {isLoading && <Skeleton className="h-24 w-full" />}
            {isError && (
              <p className="text-sm text-destructive">Không tải được danh sách chứng từ.</p>
            )}

            {!isLoading && !isError && (
              <>
                {groups.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    <TypeChip
                      label="Tất cả"
                      count={files?.length ?? 0}
                      active={activeType === ALL}
                      onClick={() => setOpenType(ALL)}
                    />
                    {groups.map((group) => (
                      <TypeChip
                        key={group.type}
                        label={group.label}
                        count={group.files.length}
                        active={activeType === group.type}
                        onClick={() => {
                          setOpenType(group.type)
                          // Mở một mục cũng là chọn chỗ để tệp sắp thả vào rơi
                          // đúng mục đó — giống mở thư mục rồi mới thả file.
                          setUploadType(group.type)
                        }}
                      />
                    ))}
                  </div>
                )}

                {canManage && (
                  <FileDropzone
                    busy={upload.isPending}
                    onFiles={(selected) => void handleFiles(selected)}
                    hint="Kéo thả tệp vào đây hoặc bấm để chọn tệp"
                  >
                    <span className="text-xs text-muted-foreground">Lưu vào mục</span>
                    <Select value={uploadType} onValueChange={setUploadType}>
                      <SelectTrigger size="sm" className="w-56 bg-background">
                        <SelectValue placeholder="Chọn loại chứng từ" />
                      </SelectTrigger>
                      <SelectContent>
                        {options.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FileDropzone>
                )}

                {groups.length === 0 && (
                  <p className="rounded-lg border border-dashed bg-muted/20 py-5 text-center text-sm text-muted-foreground">
                    Chưa có tài liệu đính kèm.
                  </p>
                )}

                {shown.map((group) => (
                  <div key={group.type} className="overflow-hidden rounded-lg border">
                    <div className="flex items-center gap-2 border-b bg-muted/40 px-3 py-2">
                      <FolderOpen className="size-4 text-primary" />
                      <span className="text-sm font-medium text-navy dark:text-foreground">
                        {group.label}
                      </span>
                      <Badge variant="secondary" className="border-0">
                        {group.files.length} tệp
                      </Badge>
                      {canManage && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="xs"
                          className="ml-auto text-muted-foreground"
                          onClick={() => setUploadDialog({ open: true, docType: group.type })}
                        >
                          <Upload />
                          Upload thêm tệp cho mục này
                        </Button>
                      )}
                    </div>
                    <div className="divide-y">
                      {group.files.map((file) => (
                        <AttachmentRow
                          key={file.id}
                          file={file}
                          canDelete={canManage}
                          pending={remove.isPending}
                          onDelete={() => void remove.mutateAsync(file.id)}
                        />
                      ))}
                    </div>
                  </div>
                ))}

                <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Info className="size-3.5" />
                  Mỗi tệp tối đa 20 MB. Hỗ trợ PDF, ảnh, Word, Excel, XML, TXT, CSV, Email và
                  CorelDRAW.
                  {canManage && ` Tệp mới sẽ nằm trong mục "${uploadLabel}".`}
                </p>
              </>
            )}
          </>
        )}
      </CardContent>

      <DocumentUploadDialog
        open={uploadDialog.open}
        onOpenChange={(open) => setUploadDialog((current) => ({ ...current, open }))}
        entity={entity}
        entityId={entityId}
        initialDocType={uploadDialog.docType}
      />
    </Card>
  )
}

function TypeChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string
  count: number
  active: boolean
  onClick: () => void
}) {
  const Icon = active ? FolderOpen : FolderClosed
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
        active
          ? 'border-primary bg-primary/10 text-primary'
          : 'border-input text-muted-foreground hover:border-primary/50 hover:text-foreground',
      )}
    >
      <Icon className="size-3.5" />
      {label}
      <span
        className={cn(
          'rounded-full px-1.5 py-0.5 text-[11px] tabular-nums',
          active ? 'bg-primary/15' : 'bg-muted',
        )}
      >
        {count}
      </span>
    </button>
  )
}

function AttachmentRow({
  file,
  canDelete,
  pending,
  onDelete,
}: {
  file: AttachmentFile
  canDelete: boolean
  pending: boolean
  onDelete: () => void
}) {
  // `attachmentIcon` chỉ TRA CỨU và trả về một trong các icon lucide khai báo sẵn ở
  // cấp module, không tạo component mới mỗi lần render -> không có chuyện remount.
  const Icon = attachmentIcon(file)

  /**
   * Tải qua API có kiểm quyền chứ không qua `file.url`.
   *
   * `file.url` đọc thẳng kho lưu trữ, không qua đăng nhập — ai cầm được chuỗi đó
   * đều mở được tệp. Dùng làm đường XEM NHANH (bấm vào tên tệp) thì chấp nhận
   * được, nhưng nút tải thì đi đường chính thống để backend còn chặn người đã bị
   * thu hồi quyền.
   */
  async function download() {
    try {
      await downloadFile(`/api/attachments/${file.id}/download`, file.filename)
    } catch {
      // GET không tự bật toast (xem `http-client`) mà đây là hành động bấm tay.
      toast.error(`Không tải được tệp "${file.filename}".`)
    }
  }

  return (
    <div className="flex min-h-12 items-center gap-3 px-3 py-2">
      {/* eslint-disable-next-line react-hooks/static-components */}
      <Icon className="size-5 shrink-0 text-primary" />
      <div className="min-w-0 flex-1">
        <a
          className="block truncate text-sm font-medium text-navy hover:text-primary hover:underline dark:text-foreground"
          href={file.url}
          target="_blank"
          rel="noreferrer"
          title={file.filename}
        >
          {file.filename}
        </a>
        <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
      </div>
      <Button
        variant="ghost"
        size="icon-sm"
        title="Tải tệp về máy"
        aria-label={`Tải tệp ${file.filename}`}
        onClick={() => void download()}
      >
        <Download />
      </Button>
      {canDelete && (
        <ConfirmIconButton
          icon={Trash2}
          title="Xóa tệp"
          confirmTitle={`Xóa "${file.filename}"?`}
          confirmDescription="Tệp sẽ bị gỡ khỏi chứng từ này."
          confirmLabel="Xóa"
          destructive
          disabled={pending}
          onConfirm={onDelete}
        />
      )}
    </div>
  )
}

function attachmentIcon(file: AttachmentFile) {
  if (file.content_type?.startsWith('image/')) return FileImage
  if (file.content_type?.includes('pdf') || /\.(pdf|docx?|xlsx?)$/i.test(file.filename)) {
    return FileText
  }
  return FileIcon
}
