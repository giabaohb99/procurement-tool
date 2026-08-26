import { ArrowLeft, Printer, TriangleAlert, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { DocumentPrintSheet } from '../components/document-print-sheet'
import { useDocument } from '../hooks/use-documents'
import { useDocumentVersion, useDocumentVersions } from '../hooks/use-document-versions'
import { DOCUMENT_STATUS } from '../types/document-record'

/**
 * BẢN IN của một văn bản — route nằm NGOÀI `ModuleLayout` để trang in không
 * mang theo menu và thanh tiêu đề.
 *
 * In đúng bản nào: mặc định là **bản đang dùng** của văn bản, hoặc bản chỉ đích
 * danh qua `?version=`. Bản chưa ban hành in ra vẫn được (soát bản thảo trên
 * giấy là việc thật) nhưng đóng chữ chìm "BẢN NHÁP" — tờ giấy rời khỏi màn hình
 * là không còn trạng thái nào đi kèm, người cầm nó không có cách nào biết.
 */
export function DocumentPrintPage() {
  const { id } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const documentId = Number(id)

  const { data: record, isLoading, isError } = useDocument(documentId)
  const { data: versions = [] } = useDocumentVersions(documentId)
  const [layout, setLayout] = useState<{ pages: number; oversized: number } | null>(null)

  const askedVersionId = Number(params.get('version'))
  const versionId =
    (versions.some((item) => item.id === askedVersionId) ? askedVersionId : null) ??
    record?.current_version_id ??
    versions.find((item) => item.is_current)?.id ??
    versions[0]?.id ??
    null

  const { data: version } = useDocumentVersion(documentId, versionId)

  useEffect(() => {
    if (!record) return
    const truoc = document.title
    document.title = `${record.display_code || 'Văn bản'} — ${record.title}`
    return () => {
      document.title = truoc
    }
  }, [record])

  if (isLoading) {
    return (
      <main className="min-h-[100dvh] bg-slate-200 p-6">
        <Skeleton className="mx-auto mb-3 h-10 max-w-[210mm]" />
        <Skeleton className="mx-auto h-[297mm] max-w-[210mm] bg-white" />
      </main>
    )
  }

  if (isError || !record) {
    return (
      <ErrorState
        title="Không mở được bản in"
        description="Văn bản có thể đã bị xóa, hoặc bạn không có quyền đọc văn bản này."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.document.documentsTab('outgoing'))}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  const issued =
    record.status === DOCUMENT_STATUS.approved || record.status === DOCUMENT_STATUS.effective
  const whichVersion = versions.find((item) => item.id === versionId)

  return (
    <main className="doc-print-root min-h-[100dvh] bg-slate-200 p-6">
      <style>{PRINT_STYLES}</style>

      <div className="no-print mx-auto mb-3 flex max-w-[210mm] flex-wrap items-center gap-2">
        <Button onClick={() => window.print()}>
          <Printer />
          In / Lưu PDF
        </Button>
        <Button variant="outline" onClick={() => navigate(appRoutes.document.documentDetail(documentId))}>
          <ArrowLeft />
          Về văn bản
        </Button>
        <Button variant="outline" onClick={() => window.close()}>
          <X />
          Đóng
        </Button>

        <span className="ml-auto text-sm text-slate-700">
          {record.display_code || 'Chưa cấp số'}
          {whichVersion && ` · bản ${whichVersion.version_no}`}
          {layout && ` · ${layout.pages} trang`}
        </span>
      </div>

      {/*  Nói ra chỗ bản in KHÔNG chính xác, thay vì im lặng: khối cao hơn một
           trang (bảng dài, ảnh lớn) không cắt đôi được nên nó tràn sang tờ sau
           và số trang từ đó trở đi lệch. */}
      {layout && layout.oversized > 0 && (
        <div className="no-print mx-auto mb-3 flex max-w-[210mm] items-start gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          <span>
            Có {layout.oversized} khối (bảng hoặc ảnh) cao hơn một trang giấy. Hệ không cắt đôi
            khối, nên chỗ đó sẽ tràn sang tờ sau và số trang in ra lệch với số đếm ở đây. Tách
            bảng đó thành nhiều bảng nhỏ nếu cần số trang chuẩn.
          </span>
        </div>
      )}

      {version && (
        <DocumentPrintSheet
          html={version.content_html ?? ''}
          marginLeftMm={version.margin_left_mm}
          marginRightMm={version.margin_right_mm}
          watermark={issued ? undefined : 'BẢN NHÁP'}
          autoNumber={version.auto_heading_number}
          pageFrame={{
            header_left: version.header_left,
            header_right: version.header_right,
            footer_left: version.footer_left,
            footer_right: version.footer_right,
          }}
          markers={{
            docNumber: record.display_code || '',
            documentTitle: record.title,
            ngay: new Date().toLocaleDateString('vi-VN'),
          }}
          onLayout={setLayout}
        />
      )}
    </main>
  )
}

/**
 * `@page { margin: 0 }`: trình duyệt vẽ ngày giờ / đường dẫn / số trang của
 * CHÍNH NÓ vào dải lề — bỏ lề đi thì không còn chỗ cho mấy dòng đó, và số trang
 * duy nhất trên giấy là số của mình đặt theo Nghị định 30.
 *
 * Lúc IN thì tờ giấy để cao TỰ NHIÊN (`height: auto`) và cắt trang bằng
 * `break-after`: ghim đúng 297mm hay bị dôi ra vài phần trăm milimet do làm
 * tròn, đủ để đẻ thêm một tờ trắng sau mỗi trang.
 */
const PRINT_STYLES = `
  .doc-print-sheet {
    position: relative;
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto 8mm;
    padding-top: 20mm;
    padding-bottom: 20mm;
    background: #fff;
    box-shadow: 0 1px 3px rgb(15 23 42 / 0.16), 0 8px 24px rgb(15 23 42 / 0.10);
    /* KHÔNG cắt phần thừa: khối cao hơn một trang mà bị overflow hidden là mất
       chữ trên bản in. Thà để nó tràn ra ngoài tờ giấy cho thấy rõ, và băng
       cảnh báo ở trên đã nói ra chỗ đó. */
  }

  /* Thân bài dùng lại NGUYÊN bộ kiểu chữ của trang soạn thảo (.doc-page trong
     index.css) — cùng phông, cùng giãn dòng, cùng khe giữa các khối — chỉ bỏ
     phần khổ giấy vì tờ giấy đã do .doc-print-sheet lo. */
  .doc-print-body {
    /* width KHÔNG để !important: bản đo đặt bề ngang thật bằng style nội
       tuyến, mà !important thì đè cả style nội tuyến — đo sai bề ngang là chia
       trang sai theo. */
    width: 100%;
    max-width: none !important;
    margin-inline: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
  }

  /* Dải đầu/chân trang nằm TRONG phần lề (20mm), không lấn vào vùng chữ —
     nếu lấn thì phần chia trang đã đo theo vùng chữ sẽ sai. */
  .doc-print-frame {
    position: absolute;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-between;
    gap: 8mm;
    padding-left: var(--doc-print-pad-left, 20mm);
    padding-right: var(--doc-print-pad-right, 20mm);
    font-family: 'Times New Roman', serif;
    font-size: 11pt;
    color: #374151;
  }
  .doc-print-frame--top { top: 8mm; }
  .doc-print-frame--bottom { bottom: 8mm; }

  .doc-print-page-number {
    position: absolute;
    top: 10mm;
    left: 0;
    right: 0;
    text-align: center;
    font-family: 'Times New Roman', serif;
    font-size: 13pt;
    color: #111827;
  }

  .doc-print-watermark {
    position: absolute;
    top: 45%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-30deg);
    font-family: 'Times New Roman', serif;
    font-size: 72pt;
    font-weight: 700;
    letter-spacing: 6px;
    color: rgb(148 163 184 / 0.28);
    white-space: nowrap;
    pointer-events: none;
  }

  @media print {
    @page { size: A4 portrait; margin: 0; }
    html, body { margin: 0 !important; background: #fff !important; }
    .no-print { display: none !important; }
    .doc-print-root { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
    .doc-print-sheet {
      height: auto;
      min-height: 0;
      margin: 0 !important;
      box-shadow: none !important;
      break-after: page;
    }
    .doc-print-sheet:last-child { break-after: auto; }
  }
`
