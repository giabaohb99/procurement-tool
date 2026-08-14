import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { BookCounterCard } from '../components/book-counter-card'
import { BookEntriesCard } from '../components/book-entries-card'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentBookForm } from '../components/document-book-form'
import {
  useDeleteDocumentBook,
  useDocumentBook,
  useSaveDocumentBook,
} from '../hooks/use-document-books'
import { BOOK_KIND_LABELS } from '../types/document-book'

const FORM_ID = 'document-book-form'

/**
 * Trang MỞ SỔ / SỬA SỔ.
 *
 * Ba khối, xếp theo thứ tự người dùng cần: khai báo sổ → bộ đếm đang tới đâu →
 * văn bản đã vào sổ. Trang thêm mới chỉ có khối đầu: sổ chưa tồn tại thì chưa có
 * số nào để đếm và chưa có văn bản nào để liệt kê.
 */
export function DocumentBookDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()

  const bookId = Number(id)
  const isCreating = !Number.isFinite(bookId)

  const { data: book, isLoading } = useDocumentBook(isCreating ? undefined : bookId)
  const save = useSaveDocumentBook()
  const remove = useDeleteDocumentBook()

  const [year, setYear] = useState(new Date().getFullYear())

  const backTo = appRoutes.document.books

  return (
    <DetailPageShell
      title={isCreating ? 'Mở sổ văn bản' : (book?.name ?? '')}
      description={
        isCreating
          ? 'Mỗi sổ có bộ đếm số riêng — khai xong là dùng được ngay.'
          : `${book ? BOOK_KIND_LABELS[book.kind] : ''} · mã ${book?.code} · ${book?.company_name}`
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={backTo}
      isMissing={!isCreating && !isLoading && !book}
      missingTitle="Không tìm thấy sổ"
      audit={book ? { entity: 'document_book', id: book.id } : undefined}
      deleteConfirmDescription="Chỉ xóa được sổ chưa cấp số nào. Sổ đã dùng thì chuyển sang Ngừng dùng."
      onDelete={
        book ? () => remove.mutate(book.id, { onSuccess: () => navigate(backTo) }) : undefined
      }
    >
      <DocumentBookForm
        formId={FORM_ID}
        book={book}
        onSubmit={(values) =>
          save.mutate(
            { id: book?.id, values },
            {
              onSuccess: (saved) => {
                if (isCreating) {
                  navigate(appRoutes.document.bookDetail(saved.id), { replace: true })
                }
              },
            },
          )
        }
      />

      {!isCreating && book && (
        <>
          <BookCounterCard bookId={book.id} year={year} onYearChange={setYear} />
          <BookEntriesCard bookId={book.id} year={year} />
        </>
      )}
    </DetailPageShell>
  )
}
