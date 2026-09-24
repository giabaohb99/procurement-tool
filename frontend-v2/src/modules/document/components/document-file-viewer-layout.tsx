import { useMutation } from '@tanstack/react-query'
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Download,
  FileWarning,
  Loader2,
  Menu,
} from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { downloadFile, extractErrorMessage } from '@/core/api'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/shared/ui/sheet'
import type { DocumentVersionFile } from '../api/document-api'
import { canPreviewInline } from '../helpers/inline-viewable'
import { AttachmentViewerPane } from './attachment-viewer-pane'
import { DocumentFileTree } from './document-file-tree'

interface DocumentFileViewerLayoutProps {
  files: DocumentVersionFile[]
  selectedId: number
  onSelect: (id: number) => void
  /** Có sẵn = hiện nút «Về danh sách». Bỏ trống ở ca CHỈ 1 tệp — không có danh sách để về. */
  onBackToList?: () => void
  documentCode?: string
}

/**
 * KHUNG XEM CHI TIẾT của tab «Tệp» (phase 09) — trái khung xem, phải cây tệp
 * theo phiên bản. Màn hẹp: cây chuyển vào `Sheet` mở bằng nút «Danh sách tệp».
 *
 * Không còn thanh tiêu đề tên tệp (24/09/2026) — tệp đang xem đã tô sáng
 * trong cây; cụm «Tệp x/y · trước · sau · tải về» nằm ở đầu cột cây, khung xem
 * cao hết màn hình (`fill`).
 *
 * ↑↓ trong cây ĐỔI NGAY tệp đang xem (`DocumentFileTree` → `TreeView`
 * `onFocusChange`); nút trước/sau làm việc tương tự, cả hai đều
 * BỎ QUA tệp đã biết là khóa (403 lúc mở) — bộ luật «Thấy một phần» ở phase 04.
 */
export function DocumentFileViewerLayout({
  files,
  selectedId,
  onSelect,
  onBackToList,
  documentCode,
}: DocumentFileViewerLayoutProps) {
  const isMobile = useIsMobile()
  const [treeSheetOpen, setTreeSheetOpen] = useState(false)
  //  Tệp đã THỬ MỞ và bị 403/404 — biết được lúc `AttachmentViewerPane` báo
  //  lỗi, không phải trước đó (backend không có API "kiểm quyền hàng loạt").
  const [lockedIds, setLockedIds] = useState<Set<number>>(new Set())

  const index = files.findIndex((file) => file.id === selectedId)
  const current = files[index] ?? files[0] ?? null

  const download = useMutation({
    mutationFn: (file: DocumentVersionFile) =>
      downloadFile(`/api/attachments/${file.id}/download`, file.filename),
    onError: (error) => toast.error(extractErrorMessage(error)),
  })

  function goRelative(delta: 1 | -1) {
    if (files.length <= 1 || index < 0) return
    for (let attempt = 1; attempt <= files.length; attempt++) {
      const nextIndex = (index + delta * attempt + files.length * attempt) % files.length
      const candidate = files[nextIndex]
      if (candidate && !lockedIds.has(candidate.id)) {
        onSelect(candidate.id)
        return
      }
    }
    //  Mọi tệp còn lại đều đã khóa (vd cả văn bản hết hạn xem) — không có chỗ
    //  nào để nhảy tới, giữ nguyên tệp đang xem.
  }

  if (!current) return null

  const tree = (
    <DocumentFileTree
      files={files}
      selectedId={selectedId}
      lockedIds={lockedIds}
      onSelect={(file) => {
        onSelect(file.id)
        setTreeSheetOpen(false)
      }}
    />
  )

  //  Cụm điều hướng tệp — ĐẦU CỘT danh sách bên phải (màn rộng) hoặc một dòng
  //  gọn trên khung xem (màn hẹp). Trước 24/09/2026 nằm trên một thanh tiêu đề
  //  riêng kèm tên tệp, ăn mất một dòng chiều cao của khung xem.
  const controls = (
    <div className="flex shrink-0 items-center gap-1">
      <Button
        type="button"
        variant="outline"
        size="icon-sm"
        disabled={files.length <= 1}
        title="Tệp trước"
        aria-label="Tệp trước"
        onClick={() => goRelative(-1)}
      >
        <ChevronLeft className="size-4" />
      </Button>
      <Button
        type="button"
        variant="outline"
        size="icon-sm"
        disabled={files.length <= 1}
        title="Tệp sau"
        aria-label="Tệp sau"
        onClick={() => goRelative(1)}
      >
        <ChevronRight className="size-4" />
      </Button>
      <Button
        type="button"
        variant="outline"
        size="icon-sm"
        disabled={download.isPending}
        title="Tải về"
        aria-label="Tải về"
        onClick={() => download.mutate(current)}
      >
        {download.isPending ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Download className="size-4" />
        )}
      </Button>
    </div>
  )

  const position = (
    <span className="min-w-0 truncate text-xs whitespace-nowrap text-muted-foreground">
      Tệp {index + 1}/{files.length}
    </span>
  )

  const backButton = onBackToList && (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      title="Về danh sách"
      aria-label="Về danh sách"
      onClick={onBackToList}
    >
      <ArrowLeft className="size-4" />
    </Button>
  )

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_260px]">
      <div className="min-w-0 space-y-2">
        {isMobile && (
          <div className="flex items-center justify-between gap-2">
            <div className="flex min-w-0 items-center gap-1">
              {backButton}
              <Sheet open={treeSheetOpen} onOpenChange={setTreeSheetOpen}>
                <SheetTrigger asChild>
                  <Button type="button" variant="outline" size="sm">
                    <Menu className="size-4" />
                    Danh sách tệp
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-[300px] gap-0 sm:max-w-sm">
                  <SheetHeader>
                    <SheetTitle>Danh sách tệp</SheetTitle>
                  </SheetHeader>
                  <div className="min-h-0 flex-1 overflow-auto px-4 pb-4">{tree}</div>
                </SheetContent>
              </Sheet>
              {position}
            </div>
            {controls}
          </div>
        )}

        {canPreviewInline(current.content_type, current.filename) ? (
          <AttachmentViewerPane
            key={current.id}
            linkId={current.id}
            filename={current.filename}
            contentType={current.content_type}
            documentCode={documentCode}
            watermark={false}
            fill
            onViewError={() =>
              setLockedIds((prev) => (prev.has(current.id) ? prev : new Set(prev).add(current.id)))
            }
          />
        ) : (
          //  Không phải lỗi quyền — chỉ là KIỂU TỆP hệ thống chưa vẽ được tại
          //  chỗ (zip, dwg…). Không gọi `/view` (tránh một lượt gọi mạng chắc
          //  chắn hỏng), không đánh dấu khóa: cây vẫn dùng bình thường.
          <div className="flex min-h-64 flex-col items-center justify-center gap-3 rounded-md border bg-muted/30 p-8 text-center">
            <FileWarning className="size-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Tệp «{current.filename}» không xem được ngay trong trang — tải về máy để mở.
            </p>
            <Button
              type="button"
              variant="outline"
              disabled={download.isPending}
              onClick={() => download.mutate(current)}
            >
              <Download className="size-4" />
              Tải về
            </Button>
          </div>
        )}
      </div>

      {!isMobile && (
        <aside className="min-w-0 space-y-2">
          <div className="flex items-center justify-between gap-2 border-b pb-2">
            <div className="flex min-w-0 items-center gap-1">
              {backButton}
              {position}
            </div>
            {controls}
          </div>
          {tree}
        </aside>
      )}
    </div>
  )
}
