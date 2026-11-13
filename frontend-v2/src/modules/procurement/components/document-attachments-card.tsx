import {
  Check,
  ChevronDown,
  Download,
  ExternalLink,
  Eye,
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
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { PO_DOCUMENT_STATUS } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { ImageLightbox, useImageLightbox } from '@/shared/ui/image-lightbox'
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
import { AttachmentPreviewDialog } from '@/shared/attachments/attachment-preview-dialog'
import { DocumentStatusBadge } from './document-status-badge'
import { DocumentUploadDialog } from './document-upload-dialog'

interface DocumentAttachmentsCardProps {
  /** `purchase_request` · `purchase_order` · `contract` — quyết định chính sách file ở backend. */
  entity: string
  entityId: number
  canManage: boolean
  /**
   * Hạn mức dung lượng MỘT tệp, tính bằng MB — chỉ để hiện đúng câu nhắc.
   *
   * Ngưỡng thật nằm ở `FILE_POLICY` trong `backend/app/core/file_registry.py`.
   * Từ CR-148 (main) mọi ô chứng từ cùng trần 50MB nên mặc định là đủ; chỉ
   * truyền đè khi backend khai một entity với trần khác đi.
   */
  maxSizeMb?: number
  /**
   * Tình trạng hồ sơ chứng từ, hiện ở tiêu đề thẻ. Rỗng = không hiện.
   *
   * duoc-CR-741: ở màn Thu mua (`v1Wording`) ô sửa dời về ĐÂY như bản v1 (trước nằm ở thẻ
   * Thông tin chung của ĐMH) và đứng đầu cụm nút bên phải. Màn khác (Đề nghị thanh toán…)
   * giữ huy hiệu chỉ đọc *Hồ sơ:* cạnh tiêu đề như cũ.
   */
  documentStatus?: string
  /**
   * Bấm huy hiệu hồ sơ ra menu chọn tình trạng (cần thêm `onDocumentStatusChange`). Chỉ có
   * tác dụng khi bật `v1Wording`.
   */
  documentStatusEditable?: boolean
  onDocumentStatusChange?: (value: string) => void
  /**
   * duoc-CR-741 — chữ và vị trí của bản v1, CHỈ cho màn Thu mua (YCMH · Phiếu khảo sát ·
   * ĐMH): *Hồ sơ chứng từ:* ở cụm nút, hộp xóa tệp *Xóa file "x"?* + *Đồng ý*, *Chuỗi chứng
   * từ (PYC/PKS)*, *Upload thêm file cho mục này*, gợi ý *Bỏ file* / *Xóa dòng* trong hộp tải.
   * Đại ca chốt 09/11/2026: Thu mua v2 khớp v1 từng chữ, phân hệ khác GIỮ chữ v2 hiện có —
   * nên mặc định tắt.
   */
  v1Wording?: boolean
  /**
   * Mục (thư mục) chọn sẵn khi tải lên — mặc định "Khác". Duyệt dấu truyền
   * `signed_doc` để thư mục mặc định là "Chứng từ đã ký".
   */
  defaultDocType?: string
  /**
   * Ẩn nút "Upload chứng từ" (hộp thoại tải nhiều loại). Dùng khi màn đã có ô kéo-thả
   * kèm ô chọn mục ngay tại chỗ nên không cần thêm hộp thoại (vd. Duyệt dấu).
   */
  hideUploadButton?: boolean
  /**
   * ai-CR-240 — mở sẵn hộp "Upload chứng từ" MỘT lần khi thẻ hiện ra (link trợ lý AI có `?attach=1`). Chỉ có tác dụng
   * khi người xem được quản lý tệp (`canManage`) của chứng từ đã lưu; không có quyền thì thẻ hiện như thường.
   */
  autoOpenUpload?: boolean
}

/** Giá trị của chip "Tất cả": xem hết, không lọc theo mục nào. */
const ALL = '__all__'

/** Hai bộ chữ của thẻ — xem prop `v1Wording`. */
const CARD_WORDING = {
  v1: {
    documentStatusLabel: 'Hồ sơ chứng từ:',
    chainTitle: 'Xem và tải toàn bộ chứng từ liên kết từ PYC, PKS, YCBG',
    chainLabel: 'Chuỗi chứng từ (PYC/PKS)',
    uploadMore: 'Upload thêm file cho mục này',
  },
  v2: {
    documentStatusLabel: 'Hồ sơ:',
    chainTitle: 'Mở trang xem toàn bộ chứng từ của chuỗi (YCMH, phiếu khảo sát, YCBG)',
    chainLabel: 'Xem cả chuỗi chứng từ',
    uploadMore: 'Upload thêm tệp cho mục này',
  },
} as const

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
  maxSizeMb = 50,
  documentStatus = '',
  documentStatusEditable = false,
  onDocumentStatusChange,
  defaultDocType = OTHER_DOC_TYPE,
  hideUploadButton = false,
  v1Wording = false,
  autoOpenUpload = false,
}: DocumentAttachmentsCardProps) {
  const wording = v1Wording ? CARD_WORDING.v1 : CARD_WORDING.v2
  const [openType, setOpenType] = useState(ALL)
  const [uploadType, setUploadType] = useState(defaultDocType)
  const [zipping, setZipping] = useState(false)
  /** Hộp thoại tải theo loại; `docType` là mục điền sẵn cho mục đầu tiên. */
  const [uploadDialog, setUploadDialog] = useState({ open: false, docType: defaultDocType })
  //  Tệp đang xem trước trên popup (nút "Xem" của từng dòng).
  const [previewFile, setPreviewFile] = useState<AttachmentFile | null>(null)
  const { data: files, isLoading, isError } = usePurchaseRequestAttachments(entity, entityId)
  const { data: documentTypes } = useDocumentTypes()
  const upload = useUploadPurchaseRequestAttachments(entity, entityId)
  const remove = useDeletePurchaseRequestAttachment(entity, entityId)
  const isNew = entityId <= 0
  //  ai-CR-240: mở hộp tải đúng một lần (đóng rồi không tự bật lại khi thẻ render lại).
  const [autoOpened, setAutoOpened] = useState(false)
  if (autoOpenUpload && !autoOpened && canManage && !isNew && !hideUploadButton) {
    setAutoOpened(true)
    setUploadDialog({ open: true, docType: defaultDocType })
  }

  const options = useMemo(() => withOtherType(documentTypes ?? []), [documentTypes])
  const groups = useMemo(() => groupAttachmentsByType(files ?? [], options), [files, options])
  // Bấm ảnh mở lightbox tại chỗ, lật qua lại trong TẤT CẢ ảnh của chứng từ.
  //
  // ⚠️ Chỉ ảnh CÓ `url` mới vào được lightbox: nó nhúng thẳng `url` vào thẻ ảnh,
  // nên ảnh không có đường công khai (tệp nhập từ app đặt xe cũ — byte còn nằm ở
  // kho khác, backend cố ý để `url` rỗng) sẽ hiện ra một khung vỡ. Ảnh đó rơi
  // xuống nút XEM TRƯỚC, nơi đi qua `/view` có kiểm quyền và lấy được byte thật.
  const imageFiles = useMemo(
    () => (files ?? []).filter((f) => f.content_type?.startsWith('image/') && f.url),
    [files],
  )
  const lightbox = useImageLightbox()
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
      {/*
        ⚠️ **Khổ điện thoại XẾP DỌC** (`max-md:flex-col`). Bản cũ khóa cứng
        `flex-row` không cho xuống dòng: ở 356px không đủ chỗ nên flex bóp nhóm
        bên trái xuống **min-content**, mà tiêu đề không có `min-w-0` nên nó tụt
        thành MỘT TỪ MỖI DÒNG ("Chứng / từ & Tài / liệu / đính / kèm"), trong
        khi nút *Upload chứng từ* không co được nữa và **tràn hẳn ra ngoài mép
        thẻ** (đo 12/09/2026: 374px trong khung 356px). Sửa ở đây là sửa cho cả
        9 màn đang dùng thẻ này.
      */}
      <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3! max-md:flex-col max-md:items-start max-md:gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <Paperclip className="size-4 shrink-0 text-primary" />
          <CardTitle className="text-base text-navy dark:text-foreground">
            Chứng từ &amp; Tài liệu đính kèm
          </CardTitle>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {files?.length ?? 0} tệp
          </span>
          {/*  Màn ngoài Thu mua: huy hiệu chỉ đọc cạnh tiêu đề, giữ nguyên như trước duoc-CR-741. */}
          {!v1Wording && documentStatus && (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              {wording.documentStatusLabel}
              <DocumentStatusBadge status={documentStatus} />
            </span>
          )}
        </div>

        {/*  `max-md:w-full`: cụm nút chiếm trọn hàng riêng ở khổ hẹp — nhóm này
             có tới ba nút ở màn ĐMH, nhét chung hàng với tiêu đề là cả hai bên
             cùng bị bóp. */}
        <div className="flex flex-wrap items-center gap-2 max-md:w-full">
          {/*  duoc-CR-741: ở Thu mua cụm Hồ sơ chứng từ đứng đầu nhóm nút như bản v1. */}
          {v1Wording && documentStatus && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
              {wording.documentStatusLabel}
              {documentStatusEditable && onDocumentStatusChange ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      type="button"
                      className="inline-flex items-center gap-0.5 rounded-full focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                      title="Bấm để thay đổi trạng thái hồ sơ chứng từ"
                    >
                      <DocumentStatusBadge status={documentStatus} />
                      <ChevronDown className="size-3.5 opacity-70" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel className="text-xs text-muted-foreground uppercase">
                      Cập nhật hồ sơ chứng từ
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {PO_DOCUMENT_STATUS.map((option) => (
                      <DropdownMenuItem
                        key={option.value}
                        onSelect={() => {
                          //  Chọn lại đúng tình trạng đang có thì thôi, khỏi gọi API thừa.
                          if (option.value !== documentStatus) onDocumentStatusChange(option.value)
                        }}
                      >
                        <span className="flex-1">{option.label}</span>
                        {option.value === documentStatus && <Check className="text-primary" />}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <DocumentStatusBadge status={documentStatus} />
              )}
            </span>
          )}
          {canManage && !isNew && !hideUploadButton && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              title="Tải nhiều loại chứng từ trong một lượt và xếp sẵn vào đúng mục"
              onClick={() => setUploadDialog({ open: true, docType: defaultDocType })}
            >
              <Upload />
              Upload chứng từ
            </Button>
          )}

          {/* Hai lối vào hồ sơ CẢ CHUỖI, chỉ có ở ĐMH vì `/api/attachments/chain`
              chỉ nhận `entity = purchase_order` (nấc khác trả 400). */}
          {entity === 'purchase_order' && !isNew && (
            <>
              <Button
                variant="outline"
                size="sm"
                asChild
                title={wording.chainTitle}
              >
                <Link to={appRoutes.procurement.purchaseOrderDocuments(entityId)}>
                  <FolderOpen />
                  {wording.chainLabel}
                </Link>
              </Button>

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
            </>
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

                {/*  ⚠️ Chỉ hiện khi KHÔNG có vùng kéo thả. Người quản lý được
                     thì `FileDropzone` đã đứng ngay trên, cũng viền đứt, cũng
                     nói "chưa có gì, thả tệp vào đi" — bày thêm hộp này là hai
                     khung viền đứt chồng nhau, đọc ra như một control bị vỡ làm
                     đôi chứ không ra hai khối khác nhau.

                     Người CHỈ XEM thì không có vùng kéo thả, bỏ nốt câu này đi
                     là cả mục còn lại một khoảng trắng không lời giải thích. */}
                {groups.length === 0 && !canManage && (
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
                          {wording.uploadMore}
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
                          v1Wording={v1Wording}
                          onDelete={() => void remove.mutateAsync(file.id)}
                          onView={
                            imageFiles.includes(file)
                              ? () => lightbox.openAt(imageFiles.indexOf(file))
                              : undefined
                          }
                          onPreview={() => setPreviewFile(file)}
                        />
                      ))}
                    </div>
                  </div>
                ))}

                <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Info className="size-3.5" />
                  Mỗi tệp tối đa {maxSizeMb} MB. Hỗ trợ PDF, ảnh, Word, Excel, XML, TXT, CSV,
                  Email và CorelDRAW.
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
        maxSizeMb={maxSizeMb}
        initialDocType={uploadDialog.docType}
        v1Wording={v1Wording}
      />

      {imageFiles.length > 0 && (
        <ImageLightbox
          images={imageFiles.map((f) => ({ url: f.url, name: f.filename }))}
          {...lightbox.bind}
        />
      )}

      <AttachmentPreviewDialog
        file={previewFile}
        open={previewFile !== null}
        onOpenChange={(open) => !open && setPreviewFile(null)}
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
  onView,
  onPreview,
  v1Wording,
}: {
  file: AttachmentFile
  canDelete: boolean
  pending: boolean
  /** Hộp xóa tệp nói chữ v1 (Thu mua) hay chữ v2 cũ — xem `v1Wording` của thẻ. */
  v1Wording: boolean
  onDelete: () => void
  /** Có = tệp ảnh: bấm tên mở lightbox tại chỗ thay vì mở tab mới. */
  onView?: () => void
  /** Mở popup XEM TRƯỚC tài liệu ngay tại trang (nút con mắt). */
  onPreview?: () => void
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

  //  Bấm vào TÊN tệp thì mở cái gì. Ảnh có `url` → lightbox. Tệp KHÔNG có `url`
  //  (tệp nhập từ app đặt xe cũ, byte còn ở kho khác) → popup xem trước, vì thẻ
  //  `<a href="">` không dẫn đi đâu cả: bấm vào là NẠP LẠI chính trang đang mở,
  //  đọc y như một lỗi không rõ nguyên nhân. Còn lại giữ nguyên thẻ liên kết cũ.
  const openByName = onView ?? (file.url ? undefined : onPreview)

  return (
    <div className="flex min-h-12 items-center gap-3 px-3 py-2">
      {/* eslint-disable-next-line react-hooks/static-components */}
      <Icon className="size-5 shrink-0 text-primary" />
      <div className="min-w-0 flex-1">
        {openByName ? (
          <button
            type="button"
            className="block max-w-full truncate text-left text-sm font-medium text-navy transition-colors hover:text-primary hover:underline dark:text-foreground"
            onClick={openByName}
            title={file.filename}
          >
            {file.filename}
          </button>
        ) : (
          <a
            className="block truncate text-sm font-medium text-navy transition-colors hover:text-primary hover:underline dark:text-foreground"
            href={file.url}
            target="_blank"
            rel="noreferrer"
            title={file.filename}
          >
            {file.filename}
          </a>
        )}
        <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
      </div>
      {onPreview && (
        <Button
          variant="ghost"
          size="icon-sm"
          title="Xem trước tài liệu"
          aria-label={`Xem trước ${file.filename}`}
          onClick={onPreview}
        >
          <Eye />
        </Button>
      )}
      {file.url && (
        <Button
          asChild
          variant="ghost"
          size="icon-sm"
          title="Mở ở tab mới"
        >
          <a href={file.url} target="_blank" rel="noreferrer" aria-label={`Mở ${file.filename} ở tab mới`}>
            <ExternalLink />
          </a>
        </Button>
      )}
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
          confirmTitle={v1Wording ? `Xóa file "${file.filename}"?` : `Xóa "${file.filename}"?`}
          confirmDescription="Tệp sẽ bị gỡ khỏi chứng từ này."
          confirmLabel={v1Wording ? 'Đồng ý' : 'Xóa'}
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
