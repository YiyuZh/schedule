import { describe, expect, it } from 'vitest'

import { buildCourseImportAiPrompt, buildCourseImportJsonExample } from '@/utils/courseImportPrompt'

describe('course import prompt helpers', () => {
  it('builds a prompt with semester context and strict JSON instructions', () => {
    const prompt = buildCourseImportAiPrompt({
      semesterName: '2026 春季学期',
      termStartDate: '2026-02-24',
      termEndDate: '2026-06-28',
      scheduleHints: '上午 1-2 节 = 08:00-09:35',
    })

    expect(prompt).toContain('semester_name = 2026 春季学期')
    expect(prompt).toContain('term_start_date = 2026-02-24')
    expect(prompt).toContain('term_end_date = 2026-06-28')
    expect(prompt).toContain('只返回 JSON 本体')
    expect(prompt).toContain('weekday 使用 1=周一')
  })

  it('returns an example payload matching the import structure', () => {
    const example = buildCourseImportJsonExample()

    expect(example).toMatchObject({
      file_name: 'ai-course-import.json',
      semester_name: '2026 春季学期',
      term_start_date: '2026-02-24',
      term_end_date: '2026-06-28',
    })
    expect(example.courses[0]).toMatchObject({
      course_name: '高等数学',
      weekday: 1,
      start_time: '08:00',
      end_time: '09:35',
    })
    expect(example.courses[0].weeks).toEqual(expect.arrayContaining([1, 2, 3]))
  })
})
