import { useMutation } from '@tanstack/react-query'
import { ExternalLink, FileX, Loader2, Lock, Plus, Upload, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

//  Dùng lại đúng hook tra văn bản của phân hệ Văn bản (danh sách đã lọc theo quyền đọc ở backend) —
//  chép một bản thứ hai là hai nơi lệch nhau ở luật «ai thấy văn bản nào».
import { useDocuments } from '@/modules/document/hooks/use-documents'
import { STATUS_LABELS as DOCUMENT_STATUS_LABELS } from '@/modules/document/types/document-record'
import { extractErrorMessage } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { headcountPlanApi } from '../api/headcount-plan-api'
import type { HeadcountPlanDocumentLink } from '../types/headcount-plan'

/** Trần dung lượng 1 tệp của đính kèm Văn bản (`file_registry`: document_version = 50 MB) — chặn sớm đỡ tải rồi mới bị từ chối. */
const MAX_UPLOAD_MB = 50

/** Ít hơn 2 ký tự thì chưa tra — cùng mốc với ô tìm của phân hệ Văn bản. */
const MIN_QUERY = 2

interface HeadcountPlanLinkedDocumentsProps {
  documents: HeadcountPlanDocumentLink[]
  onChange: (documents: HeadcountPlanDocumentLink[]) => void
  readOnly: boolean
  /** `document.read` — thiếu thì không dựng ô tra (cứ gọi là ăn 403). */
  canSearch: boolean
}

/** Một dòng văn bản đã gắn — ba dạng: đọc được · không được xem · đã xóa. */
function LinkedDocumentRow({ doc }: { doc: HeadcountPlanDocumentLink }) {
  if (doc.deleted) {
    return (
      <span className="flex items-center gap-2 text-muted-foreground">
        <FileX className="size-4" />
        Văn bản đã xóa
      </span>
    )
  }
  if (doc.can_read === false) {
    //  KHÔNG lộ số, trích yếu hay trạng thái — backend cũng không gửi; câu này nói rõ là CÓ văn bản.
    return (
      <span className="flex items-center gap-2 text-muted-foreground">
        <Lock className="size-4" />
        Văn bản bạn chưa được xem
      </span>
    )
  }
  return (
    <span className="flex min-w-0 flex-wrap items-center gap-2">
      {doc.code && <span className="font-mono text-xs font-semibold text-primary">{doc.code}</span>}
      <span className="min-w-0 break-words">{doc.title}</span>
      {(doc.status_label || (doc.status && DOCUMENT_STATUS_LABELS[doc.status])) && (
        <Badge variant="outline">{doc.status_label || (doc.status ? DOCUMENT_STATUS_LABELS[doc.status] : '')}</Badge>
      )}
      <Link
        to={appRoutes.document.documentDetail(doc.document_id)}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
      >
        <ExternalLink className="size-3" />
        Mở
      </Link>
    </span>
  )
}

/**
 * VĂN BẢN LIÊN KẾT của kế hoạch (tài liệu 06 §2.1, §8): chọn văn bản CÓ SẴN ở phân hệ Văn bản
 * (quyết định duyệt ngân sách, tờ trình…) HOẶC «Tải tệp lên» để hệ thống tự tạo một văn bản KÍN có tệp đó (duoc-CR-690). Chỉ tra ra văn bản người lập đọc được — danh sách
 * `/api/documents` đã lọc theo luật đọc của phân hệ Văn bản; backend còn chặn lại lúc lưu (403).
 */
export function HeadcountPlanLinkedDocuments({
  documents,
  onChange,
  readOnly,
  canSearch,
}: HeadcountPlanLinkedDocumentsProps) {
  const [query, setQuery] = useState('')
  const q = useDebouncedValue(query.trim(), 350)
  const search = useDocuments({ q, page_size: 8 }, { enabled: canSearch && !readOnly && q.length >= MIN_QUERY })
  const fileInput = useRef<HTMLInputElement>(null)
  const [progress, setProgress] = useState(0)
  const [uploadError, setUploadError] = useState('')
  //  Dùng bản `documents` MỚI NHẤT lúc tải xong (người dùng có thể gỡ/gắn trong lúc chờ) — không chụp bản cũ.
  const latest = useRef(documents)
  useEffect(() => {
    latest.current = documents
  }, [documents])
  const upload = useMutation({
    mutationFn: (file: File) => headcountPlanApi.uploadBasisDocument(file, setProgress),
    onSuccess: (created) => {
      setUploadError('')
      onChange([...latest.current.filter((d) => d.document_id !== created.document_id), created])
    },
    onError: (error) => setUploadError(extractErrorMessage(error)),
  })

  function pickFile(file: File | undefined) {
    if (fileInput.current) fileInput.current.value = '' // chọn lại đúng tệp vừa rồi vẫn bắn `change`
    if (!file) return
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setUploadError(`Tệp «${file.name}» lớn hơn ${MAX_UPLOAD_MB} MB, không tải lên được.`)
      return
    }
    setUploadError('')
    setProgress(0)
    upload.mutate(file)
  }

  const linked = new Set(documents.map((d) => d.document_id))
  const results = q.length >= MIN_QUERY ? (search.data?.items ?? []).filter((d) => !linked.has(d.id)) : []

  return (
    <div className="space-y-2">
      {documents.length === 0 ? (
        <p className="text-sm text-muted-foreground">Chưa gắn văn bản nào.</p>
      ) : (
        <ul className="space-y-1.5">
          {documents.map((doc) => (
            <li key={doc.document_id} className="flex items-start justify-between gap-2 rounded-md border px-2.5 py-1.5 text-sm">
              <LinkedDocumentRow doc={doc} />
              {!readOnly && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="size-7 shrink-0"
                  aria-label="Gỡ văn bản khỏi kế hoạch"
                  title="Gỡ khỏi kế hoạch (văn bản vẫn còn ở phân hệ Văn bản)"
                  onClick={() => onChange(documents.filter((d) => d.document_id !== doc.document_id))}
                >
                  <X className="size-4" />
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      {!readOnly && !canSearch && (
        <p className="text-xs text-muted-foreground">Bạn chưa có quyền xem phân hệ Văn bản nên chưa gắn thêm được.</p>
      )}
      {!readOnly && canSearch && (
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={fileInput}
              type="file"
              hidden
              aria-label="Chọn tệp căn cứ để tải lên"
              onChange={(e) => pickFile(e.target.files?.[0])}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={upload.isPending}
              onClick={() => fileInput.current?.click()}
            >
              {upload.isPending ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
              {upload.isPending ? `Đang tải lên… ${progress}%` : 'Tải tệp lên'}
            </Button>
            <span className="text-xs text-muted-foreground">
              Tệp quyết định, tờ trình… (tối đa {MAX_UPLOAD_MB} MB) sẽ thành một văn bản riêng tư ở phân hệ Văn bản và được gắn vào kế hoạch.
            </span>
          </div>
          {uploadError && (
            <p role="alert" className="text-xs text-destructive">
              {uploadError}
            </p>
          )}
          <Input
            value={query}
            placeholder="Gõ số hiệu hoặc trích yếu để tìm văn bản…"
            aria-label="Tìm văn bản để gắn"
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
          />
          {q.length >= MIN_QUERY && !search.isFetching && results.length === 0 && (
            <p className="text-xs text-muted-foreground">Không tìm thấy văn bản nào bạn đọc được khớp «{q}».</p>
          )}
          {results.length > 0 && (
            <ul className="divide-y rounded-md border text-sm" aria-label="Kết quả tìm văn bản">
              {results.map((d) => (
                <li key={d.id}>
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left hover:bg-muted"
                    onClick={() => {
                      onChange([
                        ...documents,
                        {
                          document_id: d.id,
                          code: d.display_code,
                          title: d.title,
                          status: d.status,
                          status_label: d.status_label,
                          can_read: true,
                        },
                      ])
                      setQuery('')
                    }}
                  >
                    <Plus className="size-4 shrink-0 text-muted-foreground" />
                    {d.display_code && <span className="font-mono text-xs font-semibold">{d.display_code}</span>}
                    <span className="min-w-0 flex-1 truncate">{d.title}</span>
                    <Badge variant="outline">{d.status_label}</Badge>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
