-- V2 Faculty Output Repository master data seed

BEGIN;

INSERT INTO work_category (code, label_th, label_en, description, display_order, is_active)
VALUES
  ('TEACHING', 'งานสอน', 'Teaching', 'Teaching workload and course-related work', 10, true),
  ('RESEARCH', 'งานวิชาการ/วิจัย', 'Research and Academic Output', 'Research projects, publications, grants, books, academic outputs', 20, true),
  ('SUPERVISION', 'การดูแลนักศึกษา', 'Student Supervision', 'Advising, thesis, senior project, cooperative education supervision', 30, true),
  ('ACADEMIC_SERVICE', 'งานบริการวิชาการ', 'Academic Service', 'Committee, reviewer, invited speaker, editor, external academic service', 40, true),
  ('ADMINISTRATION', 'งานบริหาร', 'Administration', 'Administrative roles and academic administration', 50, true),
  ('OTHER', 'อื่น ๆ', 'Other', 'Other source-reported workload or special items', 90, true)
ON CONFLICT (code) DO UPDATE SET
  label_th = EXCLUDED.label_th,
  label_en = EXCLUDED.label_en,
  description = EXCLUDED.description,
  display_order = EXCLUDED.display_order,
  is_active = EXCLUDED.is_active,
  updated_at = now();

INSERT INTO work_type (code, category_code, label_th, label_en, description, default_visibility, display_order, is_active)
VALUES
  ('LECTURE', 'TEACHING', 'วิชาบรรยาย', 'Lecture', 'Lecture teaching workload', 'INTERNAL', 10, true),
  ('LAB', 'TEACHING', 'วิชาปฏิบัติการ', 'Laboratory', 'Laboratory or practical teaching workload', 'INTERNAL', 20, true),
  ('SEMINAR', 'TEACHING', 'สัมมนา', 'Seminar', 'Seminar teaching or seminar committee workload', 'INTERNAL', 30, true),
  ('COURSE_COORDINATOR', 'ADMINISTRATION', 'ผู้ประสานงานรายวิชา', 'Course Coordinator', 'Course coordination workload', 'INTERNAL', 40, true),

  ('SENIOR_PROJECT', 'SUPERVISION', 'ซีเนียร์โปรเจกต์/ปัญหาพิเศษ', 'Senior Project', 'Senior project or special problem supervision', 'INTERNAL', 110, true),
  ('COOPERATIVE_EDUCATION', 'SUPERVISION', 'สหกิจศึกษา', 'Cooperative Education', 'Cooperative education advising or committee workload', 'INTERNAL', 120, true),
  ('THESIS', 'SUPERVISION', 'วิทยานิพนธ์/สารนิพนธ์', 'Thesis or Independent Study', 'Graduate thesis, independent study, dissertation supervision', 'RESTRICTED', 130, true),
  ('GENERAL_ADVISOR', 'SUPERVISION', 'อาจารย์ที่ปรึกษา', 'General Advisor', 'General student advisor workload', 'INTERNAL', 140, true),

  ('PUBLICATION', 'RESEARCH', 'ผลงานตีพิมพ์', 'Publication', 'Journal, proceedings, data article, or other publication', 'PUBLIC', 210, true),
  ('RESEARCH_PROJECT', 'RESEARCH', 'โครงการวิจัย', 'Research Project', 'Research project report or progress', 'INTERNAL', 220, true),
  ('RESEARCH_GRANT', 'RESEARCH', 'ทุนวิจัย', 'Research Grant', 'Research grant or funded project', 'INTERNAL', 230, true),
  ('CONFERENCE_PRESENTATION', 'RESEARCH', 'นำเสนอผลงานวิชาการ', 'Conference Presentation', 'Academic conference presentation', 'PUBLIC', 240, true),
  ('BOOK_OR_CHAPTER', 'RESEARCH', 'หนังสือ/ตำรา/บทในหนังสือ', 'Book or Book Chapter', 'Book, textbook, translation, or book chapter', 'PUBLIC', 250, true),
  ('PATENT_OR_INVENTION', 'RESEARCH', 'สิทธิบัตร/สิ่งประดิษฐ์', 'Patent or Invention', 'Patent, invention, copyright, teaching innovation', 'PUBLIC', 260, true),
  ('ACADEMIC_AWARD', 'RESEARCH', 'รางวัลทางวิชาการ', 'Academic Award', 'Academic award or student competition output', 'PUBLIC', 270, true),
  ('RESEARCH_UTILIZATION', 'RESEARCH', 'การนำผลงานวิจัยไปใช้ประโยชน์', 'Research Utilization', 'Research utilization or impact record', 'PUBLIC', 280, true),

  ('COMMITTEE', 'ACADEMIC_SERVICE', 'คณะกรรมการ/คณะทำงาน', 'Committee', 'Committee or working group appointment', 'INTERNAL', 310, true),
  ('ACADEMIC_REVIEWER', 'ACADEMIC_SERVICE', 'ผู้ประเมินผลงานทางวิชาการ', 'Academic Reviewer', 'Reviewer for papers, projects, academic outputs, or academic rank', 'INTERNAL', 320, true),
  ('EDITOR', 'ACADEMIC_SERVICE', 'บรรณาธิการ', 'Editor', 'Editor or editorial contribution', 'PUBLIC', 330, true),
  ('INVITED_SPEAKER', 'ACADEMIC_SERVICE', 'วิทยากร/ผู้ทรงคุณวุฒิ', 'Invited Speaker or Expert', 'Academic service as speaker, consultant, expert, or examiner', 'PUBLIC', 340, true),
  ('EXTERNAL_SERVICE', 'ACADEMIC_SERVICE', 'บริการวิชาการภายนอก', 'External Academic Service', 'Academic service for external organizations', 'INTERNAL', 350, true),

  ('ADMIN_POSITION', 'ADMINISTRATION', 'ตำแหน่งบริหาร', 'Administrative Position', 'Administrative position or formal appointment', 'INTERNAL', 410, true),
  ('PROGRAM_ADMINISTRATION', 'ADMINISTRATION', 'งานบริหารหลักสูตร/สาขา', 'Program Administration', 'Program, department, branch, or curriculum administration', 'INTERNAL', 420, true),
  ('INTERNSHIP_COORDINATOR', 'ADMINISTRATION', 'ผู้ประสานงานฝึกงาน/ฝึกภาคสนาม', 'Internship Coordinator', 'Internship or field training coordination', 'INTERNAL', 430, true),

  ('OTHER_WORKLOAD', 'OTHER', 'ภาระงานอื่น', 'Other Workload', 'Other source-reported workload item', 'INTERNAL', 900, true),
  ('SPECIAL_SCORE', 'OTHER', 'คะแนนพิเศษ', 'Special Score', 'Source-reported special score or adjustment', 'INTERNAL', 910, true)
ON CONFLICT (code) DO UPDATE SET
  category_code = EXCLUDED.category_code,
  label_th = EXCLUDED.label_th,
  label_en = EXCLUDED.label_en,
  description = EXCLUDED.description,
  default_visibility = EXCLUDED.default_visibility,
  display_order = EXCLUDED.display_order,
  is_active = EXCLUDED.is_active,
  updated_at = now();

COMMIT;

