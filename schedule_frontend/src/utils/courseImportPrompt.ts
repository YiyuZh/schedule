import type { CourseImportPayload } from '@/types/course'

export interface CourseImportPromptContext {
  semesterName: string
  termStartDate: string
  termEndDate: string
  scheduleHints: string
}

export function buildCourseImportJsonExample(): CourseImportPayload {
  return {
    file_name: 'ai-course-import.json',
    semester_name: '2026 春季学期',
    term_start_date: '2026-02-24',
    term_end_date: '2026-06-28',
    courses: [
      {
        course_name: '高等数学',
        weekday: 1,
        start_time: '08:00',
        end_time: '09:35',
        location: 'A-203',
        teacher: '张老师',
        weeks: [1, 2, 3, 4, 5, 6, 7, 8],
        color: '#7aa2f7',
        notes: '如图片中未写明教师，可留空',
      },
    ],
  }
}

export function buildCourseImportAiPrompt(context: CourseImportPromptContext): string {
  const semesterName = context.semesterName.trim() || '请填写学期名称'
  const termStartDate = context.termStartDate.trim() || '请填写学期开始日期'
  const termEndDate = context.termEndDate.trim() || '请填写学期结束日期'
  const scheduleHints = context.scheduleHints.trim() || '无额外说明'

  return [
    '你是一个“课表图片转 JSON”助手。',
    '我会另外给你一张课表图片，你必须结合图片内容和下面的补充说明，输出一个可直接导入系统的 JSON。',
    '',
    '硬性要求：',
    '1. 只返回 JSON 本体，不要返回 Markdown，不要加代码块，不要写解释。',
    '2. 返回结构必须严格符合下面这个对象结构：',
    JSON.stringify(buildCourseImportJsonExample(), null, 2),
    '3. weekday 使用 1=周一, 2=周二, 3=周三, 4=周四, 5=周五, 6=周六, 7=周日。',
    '4. 同一门课如果在不同时间段出现，请拆成多条课程项。',
    '5. weeks 必须是数字数组，例如 [1,2,3,4]。',
    '6. start_time / end_time 必须使用 24 小时制 HH:MM。',
    '7. 看不清、图片里没有、无法确定的信息不要编造；teacher、location、color、notes 可以留空或填 null。',
    '8. semester_name、term_start_date、term_end_date 必须使用我给你的值，不要擅自改动。',
    '',
    '本次固定信息：',
    `semester_name = ${semesterName}`,
    `term_start_date = ${termStartDate}`,
    `term_end_date = ${termEndDate}`,
    '',
    '补充说明：',
    scheduleHints,
    '',
    '请再次确认：最终只输出 JSON。不要输出任何解释性文字。',
  ].join('\n')
}
