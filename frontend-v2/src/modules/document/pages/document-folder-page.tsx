import { FolderTree } from 'lucide-react'
import { useState } from 'react'

import { useSetUrlParams, useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { HelpHint } from '@/shared/ui/help-hint'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { FolderContentsPanel } from '../components/folder-contents-panel'
import { FolderMyDrivePanel } from '../components/folder-my-drive-panel'
import { FolderTreePanel } from '../components/folder-tree-panel'
import { FolderTreePanelShell } from '../components/folder-tree-panel-shell'

/**
 * `/document/folders` — QUẢN LÝ CÂY THƯ MỤC (phase 05, duoc-CR-476). Hai
 * khung: cây (trái, `Sheet` ở màn hẹp) + nội dung thư mục đang chọn (phải).
 *
 * `?folder=<id|all>&tab=documents|access` là nguồn sự thật DUY NHẤT cho thư
 * mục/tab đang xem — `?q=&sub=&page=` của bảng văn bản do
 * `folder-documents-table.tsx` tự đọc/ghi (không đi qua đây, xem ghi chú ở
 * tệp đó).
 *
 * Gác `doc_folder.read` nằm Ở MỤC MENU (`routes.tsx`, `entity: 'doc_folder'`)
 * — `canAccessRoute` (`app/router/module-visibility.ts`) đọc đúng mục đó để
 * chặn gõ thẳng URL, nên trang này không tự kiểm tra quyền lần hai.
 *
 * `?doc=<id>` (duoc-CR-476, yêu cầu 23/09/2026 tối) — văn bản đang được CÂY
 * chỉ tới (bấm một lá văn bản): khung phải tự chọn + mở khung chi tiết + cuộn
 * tới đúng dòng, rồi TỰ XÓA tham số này (`clearSelectedDocument`, gọi qua
 * `onDocumentHandled` — xem `folder-contents-panel.tsx`) để lần sau người
 * dùng tự bấm chọn dòng khác không bị "kéo ngược" về văn bản cũ. Giữ trên URL
 * TRONG lúc xử lý để Back/dán link vẫn ra đúng thư mục + văn bản đó.
 */
export function DocumentFolderPage() {
  const [folderParam] = useUrlParamState('folder', 'all')
  const [tab, setTab] = useUrlParamState('tab', 'documents')
  const [docParam, setDocParam] = useUrlParamState('doc', '')
  const setUrlParams = useSetUrlParams()
  const [treeSheetOpen, setTreeSheetOpen] = useState(false)
  const selectedFolderId = folderParam === 'all' ? null : Number(folderParam)
  const selectedDocumentId = docParam ? Number(docParam) : null

  //  ⚠️ MỘT lượt ghi URL cho cả `folder` lẫn `doc`: hai `setValue` liên tiếp
  //  thì lượt sau đọc lại URL CŨ và đè mất `folder` vừa đặt — bấm thư mục
  //  trên cây/ô thư mục mà khung phải đứng yên (lỗi đại ca bắt 24/09/2026).
  function selectFolder(id: number) {
    setUrlParams({ folder: String(id), doc: null })
    setTreeSheetOpen(false)
  }

  /** Bấm một LÁ VĂN BẢN trong cây — đổi `folder` VÀ `doc` trong CÙNG một lượt
   * (không gọi hai `setValue` liên tiếp, xem cảnh báo ở `use-url-param-state.ts`). */
  function selectDocumentInFolder(folderId: number, documentId: number) {
    setUrlParams({ folder: String(folderId), doc: String(documentId) })
    setTreeSheetOpen(false)
  }

  /** Về gốc «Thư mục của bạn» — bỏ `folder` (mặc định `all`) và `doc` trong CÙNG một lượt ghi. */
  function selectRoot() {
    setUrlParams({ folder: null, doc: null })
    setTreeSheetOpen(false)
  }

  function clearSelectedDocument() {
    setDocParam('')
  }

  function openAccessTab(id: number) {
    setUrlParams({ folder: String(id), tab: 'access' })
  }

  return (
    <PageContainer fill>
      <PageHeader
        title={
          <span className="inline-flex items-center gap-1.5">
            Thư mục văn bản
            <HelpHint>Sắp xếp văn bản theo thư mục — phục vụ tìm kiếm, không thay cho phân quyền văn bản.</HelpHint>
          </span>
        }
        actions={
          <Button type="button" variant="outline" className="md:hidden" onClick={() => setTreeSheetOpen(true)}>
            <FolderTree className="size-4" />
            Thư mục
          </Button>
        }
      />

      {/*  MỘT khối viền duy nhất (kiểu Drive+VS Code) — cây trái và nội dung
          phải trước đây là hai khối rời (viền/nền khác nhau) trông như hai
          màn ghép tạm, bug lead bắt 23/09/2026. `overflow-hidden` để góc bo
          của khối ngoài cắt gọn cả hai khung con, `FolderTreePanelShell` tự
          có `border-r` làm luôn đường chia dọc. */}
      <div className="flex min-h-0 flex-1 overflow-hidden rounded-lg border bg-card">
        <FolderTreePanelShell
          selectedFolderId={selectedFolderId}
          onSelectFolder={selectFolder}
          onSelectDocument={selectDocumentInFolder}
          onOpenAccessTab={openAccessTab}
          onSelectRoot={selectRoot}
        />

        <div className="min-h-0 min-w-0 flex-1 overflow-hidden">
          {selectedFolderId ? (
            <FolderContentsPanel
              folderId={selectedFolderId}
              tab={tab}
              onTabChange={setTab}
              onSelectFolder={selectFolder}
              selectedDocumentId={selectedDocumentId}
              onDocumentHandled={clearSelectedDocument}
            />
          ) : (
            <FolderMyDrivePanel onSelectFolder={selectFolder} />
          )}
        </div>
      </div>

      <Sheet open={treeSheetOpen} onOpenChange={setTreeSheetOpen}>
        <SheetContent side="left" className="w-80 p-0">
          <SheetHeader>
            <SheetTitle>Thư mục văn bản</SheetTitle>
          </SheetHeader>
          <FolderTreePanel
            selectedFolderId={selectedFolderId}
            onSelectFolder={selectFolder}
            onSelectDocument={selectDocumentInFolder}
            onSelectRoot={selectRoot}
            onOpenAccessTab={(id) => {
              openAccessTab(id)
              setTreeSheetOpen(false)
            }}
          />
        </SheetContent>
      </Sheet>
    </PageContainer>
  )
}
