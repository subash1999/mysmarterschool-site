import { readFileSync, mkdirSync, mkdtempSync, writeFileSync, realpathSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';

const root = realpathSync(process.cwd());
const { demoUrl, demoDirectory } = await import(pathToFileURL(join(root, 'tools', 'safety.mjs')));
const base = demoUrl('http://127.0.0.1:8025');
const appRoot = demoDirectory(process.env.DEMO_APP || '', root);
if (realpathSync(appRoot) !== appRoot) throw new Error('Demo runtime must not be a symlink.');
const demo = JSON.parse(readFileSync(join(appRoot, 'capture-context.json'), 'utf8'));
if (demo.school !== 'Demo Academy' || demo.provenance !== 'DatabaseSeeder + synthetic supplement; no imports'
    || Object.values(demo.users).some(email => !email.endsWith('@demo.example.test'))) {
  throw new Error('Expected synthetic demo provenance and accounts.');
}
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright');
execFileSync('cwebp', ['-version'], { stdio: 'ignore' });
const output = join(root, 'assets', 'screens');
mkdirSync(output, { recursive: true });
const temporary = mkdtempSync(join(tmpdir(), 'smart-school-capture-'));
const attendanceQuery = new URLSearchParams({ school_session: demo.sessionId, grade: demo.gradeId, subject: demo.subjectId, date: demo.date });
const screens = [
  ['super-admin-schools', 'Super Admin', '/super-admin/school', 'Super admin: manage school records.'],
  ['admin-dashboard', 'School Admin', '/school-admin', 'School admin overview for the fictional Demo Academy.'],
  ['admin-sessions', 'School Admin', '/school-admin/school_session', 'Set up and select an academic session.'],
  ['admin-grades', 'School Admin', '/school-admin/grade', 'Organize grades within the selected session.'],
  ['admin-subjects', 'School Admin', '/school-admin/subject', 'Maintain the school subject list.'],
  ['admin-students', 'School Admin', '/school-admin/student', 'Browse synthetic student records.'],
  ['admin-exams', 'School Admin', '/school-admin/exam-group', 'Set up an examination group for the academic session.'],
  ['admin-calendar', 'School Admin', '/school-admin/school-calendar', 'School calendar and a fictional parent–teacher meeting.'],
  ['teacher-attendance', 'Teacher', '/teacher/student-attendance/edit?' + attendanceQuery, 'Record attendance for a grade, subject and date.'],
  ['teacher-marks', 'Teacher', `/teacher/exam-group/${demo.examId}/${demo.examGradeId}/edit_marks`, 'Enter subject marks for the first term examination.'],
  ['accountant-fees', 'Accountant', '/accountant/grade-fee', 'Configure grade fee structures. Amounts are illustrative.'],
  ['accountant-monthly-bills', 'Accountant', `/accountant/claim-bills/createMonthly?schoolSession=${demo.sessionId}&grade=${demo.gradeId}&month=6`, 'Choose a grade, month and fee items for monthly bills.'],
  ['accountant-batch-print', 'Accountant', `/accountant/claim-bills/monthly/${demo.gradeId}/6`, 'Review monthly bills and select bills for batch printing.'],
  ['accountant-report', 'Accountant', '/accountant/fees-collection-report', 'Filter the fee collection report by academic session and dates.'],
  ['guardian-dashboard', 'Guardian', '/guardian', 'Guardian dashboard linked to synthetic student records.'],
  ['guardian-results', 'Guardian', `/guardian/exam_group/${demo.examId}/${demo.examGradeId}/view_marks`, 'View a first term result from the guardian role.'],
];
const selectedNames = (process.env.CAPTURE_ONLY || '').split(',').filter(Boolean);
const selectedScreens = selectedNames.length ? screens.filter(screen => selectedNames.includes(screen[0])) : screens;
if (selectedNames.some(name => !screens.some(screen => screen[0] === name))) throw new Error('Unknown CAPTURE_ONLY screen.');
const allowedStaticHosts = new Set(['cdnjs.cloudflare.com', 'cdn.datatables.net', 'fonts.googleapis.com', 'fonts.gstatic.com', 'fonts.bunny.net', 'flagsapi.com', 'unpkg.com', 'printjs-4de6.kxcdn.com']);
const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
const manifest = { school: demo.school, data: demo.provenance, capturedAt: new Date().toISOString(), screens: selectedNames.length ? JSON.parse(readFileSync(join(output, 'manifest.json'), 'utf8')).screens.filter(screen => !selectedNames.includes(screen.screen)) : [] };
try {
  for (const [device, viewport] of [['desktop', { width: 1440, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
    for (const role of [...new Set(selectedScreens.map(s => s[1]))]) {
      const context = await browser.newContext({ viewport, deviceScaleFactor: 1, locale: 'en-US', reducedMotion: 'reduce' });
      await context.route('**/*', route => {
        const url = new URL(route.request().url());
        if (url.origin === base || (url.protocol === 'https:' && allowedStaticHosts.has(url.hostname))) return route.continue();
        return route.abort('blockedbyclient');
      });
      const page = await context.newPage();
      await page.goto(base + '/login', { waitUntil: 'networkidle' });
      await page.locator('input[name="email"]').fill(demo.users[role]);
      await page.locator('input[name="password"]').fill('demo-capture-only');
      await Promise.all([page.waitForURL('**/available-dashboard'), page.locator('input[type="submit"][value="Login"]').click()]);
      const selector = 'form:has(input[name="role"][value="' + role + '"])' + (role === 'Super Admin' ? '' : ':has(input[name="school_id"][value="' + demo.schoolId + '"])');
      await Promise.all([page.waitForURL(url => !url.pathname.includes('available-dashboard')), page.locator(selector).locator('input[type="submit"]').click()]);
      if (role !== 'Super Admin') {
        const token = await page.locator('meta[name="csrf-token"]').getAttribute('content');
        const result = await context.request.post(base + '/change-current-school-session-id', { form: { _token: token, school_session_id: String(demo.sessionId) } });
        if (!result.ok()) throw new Error('Failed to select the demo academic session.');
      }
      for (const [screen, , path, caption] of selectedScreens.filter(s => s[1] === role)) {
        const response = await page.goto(base + path, { waitUntil: 'networkidle' });
        if (response?.status() !== 200 || new URL(page.url()).pathname === '/login') throw new Error(`${screen}: expected authenticated 200, got ${response?.status()} at ${page.url()}`);
        const body = await page.locator('body').innerText();
        if (/Server Error|Whoops|SQLSTATE|Stack trace/i.test(body) || !((await page.title()).includes('Demo') || body.includes('Demo'))) throw new Error(`${screen}: invalid demo screen`);
        await page.evaluate(() => document.fonts.ready);
        if (screen === 'guardian-results' || screen === 'teacher-marks') await page.locator('#marks_table').scrollIntoViewIfNeeded();
        if (screen === 'teacher-marks' && device === 'mobile') {
          await page.locator('#sidebarCollapse').click();
          // The existing sidebar handler redraws DataTables after one second.
          await page.waitForTimeout(1100);
          await page.locator('#marks_table input.marks_table_input').first().scrollIntoViewIfNeeded();
        }
        const png = join(temporary, screen + '-' + device + '.png');
        const file = screen + '-' + device + '.webp';
        await page.screenshot({ path: png, animations: 'disabled' });
        execFileSync('cwebp', ['-quiet', '-q', '84', '-m', '6', png, '-o', join(output, file)]);
        manifest.screens.push({ screen, role, caption, device, ...viewport, file, path });
        console.log(`${device}: ${screen}`);
      }
      await context.close();
    }
  }
  writeFileSync(join(output, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  console.log(`Captured ${manifest.screens.length} optimized WebP images.`);
} finally {
  await browser.close();
  rmSync(temporary, { recursive: true, force: true });
}
