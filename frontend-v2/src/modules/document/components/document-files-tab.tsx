import { useSearchParams } from 'react-router-dom'

import { ErrorState } from '@/shared/ui/error-state'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { Skeleton } from '@/shared/ui/skeleton'
import { useDocumentFiles, useUploadDocumentFile } from '../hooks/use-document-files'
import { DocumentFileList } from './document-file-list'
import { DocumentFileViewerLayout } from './document-file-viewer-layout'

interface DocumentFilesTabProps {
  documentId: number
  /** Phiên bản để gắn tệp mới lên — dùng lúc 0 tệp bấm tải. */
  currentVersionId: number | null
  documentCode?: string
  /** Có quyền sửa (`canWrite` của trang chi tiết) — quyết định có bày nút tải lên hay không. */
  canWrite: boolean
}

const FILE_PARAM = 'file'

/**
 * Tab «Tệp» của văn bản (phase 09) — rẽ theo SỐ TỆP:
 *  - 0 tệp: trạng thái rỗng + nút tải lên (khi có quyền sửa);
 *  - 1 tệp: mở THẲNG khung xem, không bày danh sách;
 *  - ≥ 2 tệp: bảng danh sách → bấm dòng vào khung xem + cây theo phiên bản.
 *
 * Trạng thái trên URL (`?file=<linkId>`) chỉ áp cho ca ≥ 2 tệp —
 * ca 1 tệp không cần vì không có "danh sách" nào để phân biệt. Mở tệp từ
 * DANH SÁCH thì PUSH (Back quay lại danh sách); mọi lượt đổi tệp SAU ĐÓ trong
 * khung xem (cây, nút trước/sau) dùng REPLACE — không thì Back phải bấm lại
 * đúng số lần đã xem qua mới về được danh sách.
 */
export function DocumentFilesTab({
  documentId,
  currentVersionId,
  documentCode,
  canWrite,
}: DocumentFilesTabProps) {
  const { data: files, isLoading, isError, refetch } = useDocumentFiles(documentId)
  const [searchParams, setSearchParams] = useSearchParams()
  const upload = useUploadDocumentFile(documentId, currentVersionId ?? undefined)

  function openFile(linkId: number | null, push = false) {
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev)
        if (linkId) params.set(FILE_PARAM, String(linkId))
        else params.delete(FILE_PARAM)
        return params
      },
      { replace: !push },
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorState
        title="Chưa tải được danh sách tệp"
        description="Có thể do mất mạng hoặc văn bản vừa bị đổi quyền. Thử tải lại."
      >
        <button type="button" className="text-sm text-primary underline" onClick={() => refetch()}>
          Tải lại
        </button>
      </ErrorState>
    )
  }

  const items = files ?? []

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-md border border-dashed p-10 text-center">
        <p className="text-sm text-muted-foreground">Văn bản chưa có tệp đính kèm nào.</p>
        {canWrite && currentVersionId && (
          <FileDropzone
            className="w-full max-w-md"
            hint="Kéo thả tệp vào đây hoặc bấm để tải lên"
            busy={upload.isPending}
            onFiles={(picked) => upload.mutate(picked)}
          />
        )}
      </div>
    )
  }

  if (items.length === 1) {
    //  Chỉ MỘT tệp — chiếm cả bề rộng, không có danh sách để về nên không
    //  truyền `onBackToList`. Không đồng bộ URL: chỉ mình nó, mở lại tab «Văn bản»
    //  lúc nào cũng ra đúng khung xem này.
    return (
      <DocumentFileViewerLayout
        files={items}
        selectedId={items[0]!.id}
        onSelect={() => {}}
        documentCode={documentCode}
      />
    )
  }

  const fileParam = Number(searchParams.get(FILE_PARAM)) || 0
  const selected = items.find((file) => file.id === fileParam)

  if (selected) {
    return (
      <DocumentFileViewerLayout
        files={items}
        selectedId={selected.id}
        onSelect={(id) => openFile(id)}
        onBackToList={() => openFile(null)}
        documentCode={documentCode}
      />
    )
  }

  return <DocumentFileList files={items} onOpen={(file) => openFile(file.id, true)} />
}
