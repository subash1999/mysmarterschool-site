# Verified product scope

The private application was inspected read-only. This public repository contains no application source, tenant configuration, SQL dump, upload or production record.

| Public description | Inspected evidence |
| --- | --- |
| Five role areas and dashboard selection | Role constants, role routes, available-dashboard controller/view |
| Academic sessions, grades and subjects | School admin routes and create/show views |
| Teacher assignments and student/guardian records | School admin grade, subject, teacher, guardian and student views/models |
| Examinations, subject marks and results | Exam-group controllers/models and school admin, teacher and guardian marks views |
| Student attendance | Teacher attendance controller and create/edit/show views |
| School calendar and events | Role calendar/event routes, views and models |
| Grade fees and individual fee amounts | Accountant grade-fee controller/views and fee models |
| Monthly bills, finalization and payments | Accountant claim-bill controller/views and paid-bill models |
| Selected, carbon-copy and compact bill printing | Monthly bill view and print handlers |
| Fee collection report and CSV export | Accountant report controller, routes and views |

No separate student login was found. The site describes student information/results through the guardian role. No unsupported payments integration, mobile app, notification service, security certification, customer count or pricing claim is made.

Screenshot evidence is listed in `assets/screens/manifest.json`. Every screenshot uses a fresh local database, the app’s fake DatabaseSeeder, and a synthetic supplement. The original source checkout remains unchanged, including its pre-existing untracked files.
