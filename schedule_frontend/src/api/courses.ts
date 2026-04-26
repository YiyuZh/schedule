import { del, get, put, post } from '@/api/client'
import type { DeleteResult } from '@/types/common'
import type {
  CourseDayViewData,
  CourseListData,
  CourseRule,
  CourseWeekViewData,
} from '@/types/course'

export async function fetchCourses(query?: {
  term_name?: string
  weekday?: number
  batch_id?: number
}): Promise<CourseRule[]> {
  const data = await get<CourseListData>('/api/courses', { query })
  return data.items
}

export function fetchCourse(courseId: number): Promise<CourseRule> {
  return get<CourseRule>(`/api/courses/${courseId}`)
}

export function fetchCoursesDayView(date: string): Promise<CourseDayViewData> {
  return get<CourseDayViewData>('/api/courses/day-view', { query: { date } })
}

export function fetchCoursesWeekView(startDate: string, endDate: string): Promise<CourseWeekViewData> {
  return get<CourseWeekViewData>('/api/courses/week-view', {
    query: { start_date: startDate, end_date: endDate },
  })
}

export function createCourse(payload: Record<string, unknown>): Promise<CourseRule> {
  return post<CourseRule>('/api/courses', { body: payload })
}

export function updateCourse(courseId: number, payload: Record<string, unknown>): Promise<CourseRule> {
  return put<CourseRule>(`/api/courses/${courseId}`, { body: payload })
}

export function deleteCourse(courseId: number): Promise<DeleteResult> {
  return del<DeleteResult>(`/api/courses/${courseId}`)
}
