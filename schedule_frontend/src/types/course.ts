export interface CourseRule {
  id: number
  batch_id?: number | null
  course_name: string
  weekday: number
  start_time: string
  end_time: string
  location?: string | null
  teacher?: string | null
  term_name?: string | null
  term_start_date: string
  term_end_date: string
  week_list: number[]
  week_list_json: string
  color?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface CourseOccurrence {
  course_id: number
  course_name: string
  date: string
  weekday: number
  start_time: string
  end_time: string
  location?: string | null
  teacher?: string | null
  term_name?: string | null
  week_index: number
  batch_id?: number | null
  color?: string | null
  notes?: string | null
}

export interface CourseListData {
  items: CourseRule[]
}

export interface CourseDayViewData {
  date: string
  items: CourseOccurrence[]
}

export interface CourseWeekViewData {
  start_date: string
  end_date: string
  items: CourseOccurrence[]
}

export interface CourseImportCourseItem {
  course_name: string
  weekday: number
  start_time: string
  end_time: string
  location?: string | null
  teacher?: string | null
  weeks: number[]
  color?: string | null
  notes?: string | null
}

export interface CourseImportPayload {
  file_name?: string | null
  semester_name: string
  term_start_date: string
  term_end_date: string
  courses: CourseImportCourseItem[]
}

export interface CourseImportPreviewItem {
  course_name: string
  weekday: number
  start_time: string
  end_time: string
  location?: string | null
  teacher?: string | null
  term_name: string
  term_start_date: string
  term_end_date: string
  week_list: number[]
  color?: string | null
  notes?: string | null
}

export interface CourseImportValidateResult {
  valid: boolean
  parsed_count: number
  preview_items: CourseImportPreviewItem[]
  errors: string[]
}

export interface CourseImportResult {
  batch_id: number
  parsed_count: number
  preview_items: CourseImportPreviewItem[]
}

export interface ImportBatch {
  id: number
  import_type: 'course' | 'csv' | 'json'
  file_name?: string | null
  raw_content?: string | null
  parsed_count: number
  status: 'success' | 'failed' | 'partial'
  error_message?: string | null
  created_at: string
}
