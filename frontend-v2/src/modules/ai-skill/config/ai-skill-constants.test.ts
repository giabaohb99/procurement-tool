import { describe, expect, it } from 'vitest'

import { JOB_LEVEL_OPTIONS } from '@/modules/hr/types/employee-codes'
import { SUBJECT_KIND_LABELS } from '@/shared/access-subject/subject-kind'
import {
  AI_SKILL_SUBJECT_LABELS,
  AI_SKILL_SUBJECT_ORDER,
  FILE_PATH_MAX,
  JOB_LEVEL_SUBJECT_OPTIONS,
  PACKAGE_MAX_BYTES,
  checkPackageFile,
  formatBytes,
  upperFirst,
  validateFilePath,
  validateSlug,
} from './ai-skill-constants'

/**
 * Luật kiểm ở giao diện của Kho skill AI phải khớp backend `ai_skill/schema.py` (SLUG_RE) và `service.py`
 * (`check_file_path` + `_SEGMENT_RE`). Lệch một bên là người dùng hoặc bị chặn oan, hoặc qua được giao diện rồi ăn 400.
 */

describe('validateSlug', () => {
  it('accepts the backend examples and the 2 / 100 length bounds', () => {
    for (const ok of ['bao-cao-mua-hang-thang', 'ab', 'A_1', 'x'.repeat(100), '  co-khoang-trang  ']) {
      expect(validateSlug(ok)).toBe('')
    }
  })

  it('rejects empty, too short, too long, accents, spaces inside, and a leading dash or underscore', () => {
    for (const bad of ['', '   ', 'a', 'x'.repeat(101), 'báo-cáo', 'bao cao', '-abc', '_abc', 'abc/def', '../etc', 'abc\nxyz']) {
      expect(validateSlug(bad)).not.toBe('')
    }
  })
})

describe('validateFilePath', () => {
  it('accepts nested text files up to six levels', () => {
    for (const ok of ['bang-gia.csv', 'mau/phieu.md', 'a/b/c/d/e/f.txt', 'Docs/README.markdown', 'v1.2/notes.yaml']) {
      expect(validateFilePath(ok)).toBe('')
    }
  })

  it('blocks traversal, absolute paths, hidden files, backslashes and empty segments', () => {
    for (const bad of ['../x.md', 'a/../b.md', '/etc/x.md', 'C:/x.md', '.env.md', 'a/.hidden.md', 'a\\b.md', 'a//b.md', 'a/', '']) {
      expect(validateFilePath(bad)).not.toBe('')
    }
  })

  it('blocks binary or unknown extensions and paths that are too deep or too long', () => {
    expect(validateFilePath('anh.png')).not.toBe('')
    expect(validateFilePath('script.js')).not.toBe('')
    expect(validateFilePath('tep-khong-duoi')).not.toBe('')
    expect(validateFilePath('a/b/c/d/e/f/g.md')).not.toBe('')
    expect(validateFilePath(`${'a'.repeat(FILE_PATH_MAX)}.md`)).not.toBe('')
  })

  it('rejects Vietnamese letters in file names like the backend segment rule', () => {
    expect(validateFilePath('bảng-giá.csv')).not.toBe('')
  })
})

describe('checkPackageFile', () => {
  it('accepts zip and skill packages within the size cap, case-insensitively', () => {
    expect(checkPackageFile({ name: 'goi.zip', size: 10 })).toBe('')
    expect(checkPackageFile({ name: 'GOI.SKILL', size: PACKAGE_MAX_BYTES })).toBe('')
  })

  it('rejects other types, empty files and files one byte over the cap', () => {
    expect(checkPackageFile({ name: 'goi.rar', size: 10 })).not.toBe('')
    expect(checkPackageFile({ name: 'goi.zip.exe', size: 10 })).not.toBe('')
    expect(checkPackageFile({ name: 'goi.zip', size: 0 })).not.toBe('')
    expect(checkPackageFile({ name: 'goi.zip', size: PACKAGE_MAX_BYTES + 1 })).not.toBe('')
  })
})

describe('formatBytes', () => {
  it('reads small, kilo and mega sizes and refuses nonsense', () => {
    expect(formatBytes(0)).toBe('0 B')
    expect(formatBytes(1536)).toBe('1.5 KB')
    expect(formatBytes(2 * 1024 * 1024)).toBe('2.0 MB')
    expect(formatBytes(-1)).toBe('—')
    expect(formatBytes(Number.NaN)).toBe('—')
  })
})

describe('subject kinds of the skill store', () => {
  it('extends the four shared kinds with position (5) and job level (6) without touching the shared table', () => {
    expect(AI_SKILL_SUBJECT_LABELS[5]).toBe('Chức vụ')
    expect(AI_SKILL_SUBJECT_LABELS[6]).toBe('Cấp bậc')
    //  Bảng chung KHÔNG được mọc thêm hai loại này — hộp quyền văn bản lặp qua nó để bày ô chọn loại.
    expect(Object.keys(SUBJECT_KIND_LABELS)).toEqual(['1', '2', '3', '4'])
    expect([...AI_SKILL_SUBJECT_ORDER].sort()).toEqual([1, 2, 3, 4, 5, 6])
  })

  it('offers every known job level except the unknown code 0', () => {
    expect(JOB_LEVEL_SUBJECT_OPTIONS.map((o) => o.subject_id)).toEqual(
      JOB_LEVEL_OPTIONS.filter((o) => o.value > 0).map((o) => o.value),
    )
    expect(JOB_LEVEL_SUBJECT_OPTIONS.every((o) => o.subject_kind === 6 && o.label !== '')).toBe(true)
  })
})

describe('upperFirst', () => {
  it('capitalises only the first letter, Vietnamese included, and leaves empty text alone', () => {
    expect(upperFirst('chỉ đọc')).toBe('Chỉ đọc')
    expect(upperFirst('được ghi')).toBe('Được ghi')
    expect(upperFirst('')).toBe('')
  })
})
