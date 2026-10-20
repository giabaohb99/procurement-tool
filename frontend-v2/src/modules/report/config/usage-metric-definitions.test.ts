import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

import { USAGE_DEFERRED_METRICS, USAGE_METRIC_DEFINITIONS, USAGE_METRIC_SECTIONS } from './usage-metric-definitions'
import { USAGE_METRIC_LABELS } from './usage-metric-labels'

//  Bản chép tay khóa của backend (`metric_catalog.py`) — nếu có cả cây mã nguồn thì đọc thẳng để đối chiếu.
const BACKEND_CATALOG = resolve(process.cwd(), '../backend/app/modules/usage_profile/metric_catalog.py')

describe('usage metric definitions (duoc-CR-644)', () => {
  it('has a complete definition for every labelled metric', () => {
    for (const key of Object.keys(USAGE_METRIC_LABELS)) {
      const d = USAGE_METRIC_DEFINITIONS[key]
      expect(d, `thiếu định nghĩa cho ${key}`).toBeDefined()
      expect(d.meaning.length).toBeGreaterThan(10)
      expect(d.formula.length).toBeGreaterThan(10)
      expect(d.source.length).toBeGreaterThan(3)
    }
  })

  it('does not define metrics that have no label', () => {
    for (const key of Object.keys(USAGE_METRIC_DEFINITIONS)) {
      expect(USAGE_METRIC_LABELS[key], `định nghĩa thừa: ${key}`).toBeDefined()
    }
  })

  it('covers every key and section of the backend catalog when the source is mounted', () => {
    if (!existsSync(BACKEND_CATALOG)) return
    const src = readFileSync(BACKEND_CATALOG, 'utf8')
    const catalog = src.slice(src.indexOf('METRIC_CATALOG'), src.indexOf('DEFERRED_METRICS ='))
    const keys = [...catalog.matchAll(/^\s+"([a-z0-9_]+)": MetricMeta\("[a-z0-9_]+", "(3\.\d)"/gm)]
    expect(keys.length).toBeGreaterThan(40)
    const sections = new Set(USAGE_METRIC_SECTIONS.map((s) => s.section))
    for (const [, key, section] of keys) {
      expect(USAGE_METRIC_DEFINITIONS[key], `backend có khóa ${key} mà chưa có định nghĩa`).toBeDefined()
      expect(sections.has(section), `chưa có nhóm ${section}`).toBe(true)
    }
    const deferred = [...src.slice(src.indexOf('DEFERRED_METRICS =')).matchAll(/^\s+"([a-z0-9_]+)":/gm)].map((m) => m[1])
    for (const key of deferred) expect(USAGE_DEFERRED_METRICS[key], `thiếu lý do hoãn: ${key}`).toBeDefined()
  })
})
