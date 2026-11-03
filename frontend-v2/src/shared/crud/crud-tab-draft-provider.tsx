import { useCallback, useMemo, useState, type ReactNode } from 'react'

import { CrudTabDraftContext } from './use-crud-tab-draft'

/** Kho bản nháp của các tab con trong MỘT trang chi tiết — xem `use-crud-tab-draft.ts`. */
export function CrudTabDraftProvider({ children }: { children: ReactNode }) {
  const [drafts, setDrafts] = useState<Record<string, unknown>>({})
  const setDraft = useCallback((key: string, value: unknown) => {
    setDrafts((current) => {
      if (value !== null) return { ...current, [key]: value }
      if (!(key in current)) return current
      const { [key]: _removed, ...rest } = current
      return rest
    })
  }, [])
  const store = useMemo(() => ({ drafts, setDraft }), [drafts, setDraft])
  return <CrudTabDraftContext.Provider value={store}>{children}</CrudTabDraftContext.Provider>
}
