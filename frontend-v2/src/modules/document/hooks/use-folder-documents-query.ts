import { useEffect, useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { useFilterQuery } from '@/shared/conditional-filter'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { sortDocumentRows, type DocumentSortField, type SortDirection } from '../helpers/sort-document-rows'
import { useDocumentSearch } from './use-document-search'
import { useDocuments } from './use-documents'

const ALL = 'all'

/**
 * Truy vấn + BỘ LỌC của bảng «Văn bản» trong khung nội dung thư mục — tách
 * khỏi `folder-documents-table.tsx` để tệp đó dưới 200 dòng, đúng luật «xem
 * xét mô-đun hóa» của repo. Gồm cả phần RESET TRANG khi bộ lọc đổi, chạy
 * trong `useEffect` (không phải giữa render) vì `setPage` ở đây ghi THẲNG vào
 * URL (`setSearchParams` của Router, một component KHÁC) — rà soát
 * code-reviewer 23/09/2026, M10.
 */
export function useFolderDocumentsQuery(folderId: number, sortField: DocumentSortField, sortDir: SortDirection) {
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam('q')
  //  Mặc định CHỈ văn bản nằm TRỰC TIẾP trong thư mục (kiểu Drive, chốt lead
  //  24/09/2026): trước đây mặc định gộp cả nhánh, nên thư mục gốc «Công ty»
  //  chỉ chứa thư mục con vẫn bày 7 văn bản của các thư mục con bên dưới.
  const [subRaw, setSub] = useUrlParamState('sub', '0')
  const includeSubfolders = subRaw === '1'
  const [pageRaw, setPage] = useUrlParamState('page', '1')
  const page = Math.max(1, Number(pageRaw) || 1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const [typeId, setTypeId] = useState(ALL)
  const [status, setStatus] = useState(ALL)
  const [year, setYear] = useState(ALL)
  const [fullTextRaw, setFullTextRaw] = useUrlParamState('full_text', 'false')
  const isFullText = fullTextRaw === 'true'
  //  «Bộ lọc nâng cao» (đặc tả A, phản hồi 24/09/2026) — cùng `DOCUMENT_LIST_FILTER_FIELDS`
  //  với danh sách Văn bản chung (`outgoing-documents-tab.tsx`), bọc `FilterProvider`
  //  ở `folder-documents-table.tsx`. `useFilterQuery` tự trả `{}` khi KHÔNG có
  //  `FilterProvider` bao ngoài (test cũ dựng thẳng `FolderDocumentsTable` không cần sửa).
  const {
    queryParams: advancedFilterParams,
    queryKey: advancedFilterKey,
    activeCount: advancedFilterCount,
  } = useFilterQuery()

  const filterSignature = JSON.stringify([
    folderId, includeSubfolders, debouncedValue, typeId, status, year, isFullText, advancedFilterKey,
  ])
  useEffect(() => {
    setPage('1')
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `setPage` ổn định, chỉ cần theo đúng `filterSignature`
  }, [filterSignature])

  //  Ô lọc NHANH (Loại/Trạng thái/Năm) ĐÈ lên điều kiện cùng tên của bộ lọc
  //  nâng cao — cùng thứ tự spread với `outgoing-documents-tab.tsx`
  //  (`baseFilterParams`): `...advancedFilterParams` trước, khóa tường minh
  //  sau, để ba ô nhanh luôn thắng nếu người dùng đồng thời khai cả hai nơi.
  const sharedParams = {
    ...advancedFilterParams,
    folder_id: folderId,
    include_subfolders: includeSubfolders,
    doc_type_id: typeId === ALL ? undefined : Number(typeId),
    status: status === ALL ? undefined : Number(status),
    effective_from: year === ALL ? undefined : `${year}-01-01`,
    effective_to: year === ALL ? undefined : `${year}-12-31`,
    page,
    page_size: pageSize,
  }
  const { data, isLoading, isError } = useDocuments(
    { ...sharedParams, q: debouncedValue.trim() || undefined },
    { enabled: !isFullText },
  )
  const {
    data: searchData,
    isLoading: searchLoading,
    isError: searchError,
  } = useDocumentSearch(keyword, sharedParams, isFullText)

  const activeData = isFullText ? searchData : data
  const activeLoading = isFullText ? searchLoading : isLoading
  const activeError = isFullText ? searchError : isError

  const rows = useMemo(
    () => sortDocumentRows(activeData?.items ?? [], sortField, sortDir),
    [activeData, sortField, sortDir],
  )

  const filtersActive =
    debouncedValue.trim() !== '' ||
    typeId !== ALL ||
    status !== ALL ||
    year !== ALL ||
    advancedFilterCount > 0

  function resetFilters() {
    setKeyword('')
    setTypeId(ALL)
    setStatus(ALL)
    setYear(ALL)
  }

  return {
    keyword, setKeyword,
    includeSubfolders, setIncludeSubfolders: (v: boolean) => setSub(v ? '1' : '0'),
    typeId, setTypeId,
    status, setStatus,
    year, setYear,
    isFullText, setIsFullText: (v: boolean) => setFullTextRaw(v ? 'true' : 'false'),
    page, setPage: (next: number) => setPage(String(next)),
    pageSize, setPageSize,
    rows,
    total: activeData?.total ?? 0,
    isLoading: activeLoading,
    isError: activeError,
    filtersActive,
    resetFilters,
    filterSignature,
  }
}
