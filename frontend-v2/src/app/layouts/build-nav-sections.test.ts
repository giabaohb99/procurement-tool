// duoc-CR-784 (25/11/2026) — chia mục menu trái thành khối: mục không nhóm khai sau một nhóm đứng đúng chỗ khai.
import { describe, expect, it } from 'vitest'

import type { ModuleNavItem } from '@/app/router/module-definition'

import { buildNavSections } from './build-nav-sections'

function item(path: string, group?: string): ModuleNavItem {
  return { label: path, path, group }
}

function shape(items: ModuleNavItem[]) {
  return buildNavSections(items).map((section) => [section.label ?? null, section.items.map((i) => i.path)])
}

describe('buildNavSections', () => {
  it('keeps ungrouped items declared before any group in the leading section, groups after it', () => {
    expect(shape([item('/a'), item('/b', 'G1'), item('/c', 'G1'), item('/d', 'G2')])).toEqual([
      [null, ['/a']],
      ['G1', ['/b', '/c']],
      ['G2', ['/d']],
    ])
  })

  it('always returns a leading section, even when every item has a group', () => {
    expect(shape([item('/b', 'G1')])).toEqual([
      [null, []],
      ['G1', ['/b']],
    ])
  })

  it('places an ungrouped item declared after a group as an untitled section in place', () => {
    expect(
      shape([item('/a'), item('/b', 'G1'), item('/x'), item('/y'), item('/c', 'G2')]),
    ).toEqual([
      [null, ['/a']],
      ['G1', ['/b']],
      [null, ['/x', '/y']],
      ['G2', ['/c']],
    ])
  })

  it('still merges items of the same group declared apart, at the first position of that group', () => {
    expect(shape([item('/b', 'G1'), item('/c', 'G2'), item('/d', 'G1')])).toEqual([
      [null, []],
      ['G1', ['/b', '/d']],
      ['G2', ['/c']],
    ])
  })
})
