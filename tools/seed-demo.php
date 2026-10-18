<?php
// Supplemental fake records, run only AFTER the app's DatabaseSeeder.
$root = $argv[1] ?? '';
if (!preg_match('#^/(?:private/)?tmp/smart-school-demo-[a-z0-9-]+$#', $root) || realpath($root) !== $root) {
    throw new RuntimeException('A disposable absolute demo runtime path is required.');
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
if (config('database.connections.mysql.host') !== '127.0.0.1'
    || (int) config('database.connections.mysql.port') !== 33318
    || config('database.connections.mysql.database') !== 'smart_school_capture_demo'
    || !app()->environment('local')) {
    throw new RuntimeException('Refusing to seed anything except the dedicated local demo DB.');
}
use Illuminate\Support\Facades\DB;
fake()->seed(20261019);
$now = now();
DB::transaction(function () use ($root, $now) {
    DB::table('schools')->update([
        'name' => 'Demo Academy', 'address' => 'Demo Campus, Pokhara', 'district' => 'Kaski',
        'phone1' => '000-0000000', 'phone2' => null, 'email1' => 'office@demo.example.test', 'email2' => null,
        'description' => 'Fictional school. All records are generated for product demonstrations.',
        'logo' => 'http://127.0.0.1:8025/images/demo-academy.svg', 'attendance_type' => 'classwise',
    ]);
    foreach (['super_admins' => 'Operator', 'school_admins' => 'Admin', 'teachers' => 'Teacher', 'accountants' => 'Accountant', 'guardians' => 'Guardian', 'students' => 'Student'] as $table => $role) {
        foreach (DB::table($table)->get() as $row) {
            $data = ['name' => 'Demo ' . fake()->firstName() . ' ' . $role];
            if ($table !== 'super_admins') {
                $data += ['address' => 'Demo Campus, Pokhara', 'district' => 'Kaski', 'phone1' => '000-0000000', 'phone2' => null,
                    'description' => 'Synthetic demo record.', 'passport_photo' => 'http://127.0.0.1:8025/images/demo-avatar.svg'];
            }
            if ($table === 'students') $data['email'] = 'student' . $row->id . '@demo.example.test';
            DB::table($table)->where('id', $row->id)->update($data);
        }
    }
    $hash = Illuminate\Support\Facades\Hash::make('demo-capture-only');
    foreach (DB::table('users')->get() as $user) {
        DB::table('users')->where('id', $user->id)->update(['email' => 'user' . $user->id . '@demo.example.test', 'password' => $hash, 'avatar' => 'http://127.0.0.1:8025/images/demo-avatar.svg']);
    }
    $schoolId = DB::table('schools')->min('id');
    $sessionId = DB::table('school_sessions')->where('school_id', $schoolId)->min('id');
    DB::table('school_sessions')->where('id', $sessionId)->update(['name' => '2026–2027', 'from' => '2026-01-01', 'to' => '2027-12-31']);
    $grade = DB::table('grades')->where('school_session_id', $sessionId)->first();
    $gradeId = $grade->id;
    $teacher = DB::table('teachers')->where('school_id', $schoolId)->first();
    foreach (DB::table('grade_subject')->where('grade_id', $gradeId)->get() as $gs) {
        if (!DB::table('grade_subject_teacher')->where('teacher_id', $teacher->id)->where('grade_subject_id', $gs->id)->exists()) {
            DB::table('grade_subject_teacher')->insert(['teacher_id' => $teacher->id, 'grade_subject_id' => $gs->id, 'created_at' => $now, 'updated_at' => $now]);
        }
    }
    $accountant = DB::table('accountants')->first();
    DB::table('accountants')->where('id', $accountant->id)->update(['school_id' => $schoolId]);
    $firstStudent = DB::table('student_grade')->where('grade_id', $gradeId)->first();
    $guardian = DB::table('guardians')->where('school_id', $schoolId)->first();
    if (!DB::table('guardian_student')->where('guardian_id', $guardian->id)->where('student_id', $firstStudent->student_id)->exists()) {
        DB::table('guardian_student')->insert(['guardian_id' => $guardian->id, 'student_id' => $firstStudent->student_id, 'relation_to_student' => 'Guardian', 'created_at' => $now, 'updated_at' => $now]);
    }
    $examId = DB::table('exam_groups')->insertGetId(['exam_group_name' => 'First Term Examination', 'result_publish_timestamp' => '2026-09-01 10:00:00', 'description' => 'Demo results', 'school_session_id' => $sessionId, 'created_at' => $now, 'updated_at' => $now]);
    $examGradeId = DB::table('exam_group_grades')->insertGetId(['exam_group_id' => $examId, 'grade_id' => $gradeId, 'created_at' => $now, 'updated_at' => $now]);
    foreach (DB::table('grade_subject')->where('grade_id', $gradeId)->get() as $gs) {
        $esId = DB::table('exam_group_grade_subjects')->insertGetId(['exam_group_grade_id' => $examGradeId, 'grade_subject_id' => $gs->id, 'full_marks' => 100, 'pass_marks' => 40, 'created_at' => $now, 'updated_at' => $now]);
        foreach (DB::table('student_grade')->where('grade_id', $gradeId)->get() as $sg) {
            DB::table('exam_group_marks')->insert(['exam_group_grade_subject_id' => $esId, 'student_id' => $sg->student_id, 'marks_obtained' => fake()->numberBetween(61, 96), 'is_absent' => false, 'created_at' => $now, 'updated_at' => $now]);
            DB::table('student_attendance')->insert(['school_session_id' => $sessionId, 'student_id' => $sg->student_id, 'grade_subject_id' => $gs->id, 'grade_id' => $gradeId, 'date' => $now->toDateString(), 'is_present' => ($sg->student_id % 5 !== 0), 'created_at' => $now, 'updated_at' => $now]);
        }
    }
    $feeIds = [];
    foreach (['Tuition Fee' => 2400, 'Computer Fee' => 300, 'Library Fee' => 150] as $name => $amount) {
        $feeId = DB::table('school_fee_types')->insertGetId(['school_id' => $schoolId, 'fee_type' => $name, 'description' => 'Illustrative demo fee', 'created_at' => $now, 'updated_at' => $now]);
        DB::table('grade_fees')->insert(['grade_id' => $gradeId, 'school_fee_type_id' => $feeId, 'amount' => $amount, 'frequency' => 'monthly', 'fee_applicability' => 'gradewise', 'created_at' => $now, 'updated_at' => $now]);
        $feeIds[$feeId] = [$name, $amount];
    }
    foreach (DB::table('student_grade')->where('grade_id', $gradeId)->limit(6)->get() as $sg) {
        $student = DB::table('students')->where('id', $sg->student_id)->first();
        $billId = DB::table('student_claim_bills')->insertGetId([
            'student_id' => $student->id, 'name' => $student->name, 'grade_id' => $gradeId, 'grade' => $grade->grade_name, 'section' => $grade->section ?? '', 'roll_no' => $sg->roll_no,
            'school_session_id' => $sessionId, 'school_session_name' => '2026–2027', 'issued_by_user_id' => $accountant->user_id, 'issued_by_name' => 'Demo Accountant', 'issued_by_user_type' => 'Accountant',
            'finalized_by_user_id' => $accountant->user_id, 'finalized_by_name' => 'Demo Accountant', 'finalized_by_user_type' => 'Accountant',
            'date_of_issue' => $now, 'bill_month' => '6', 'is_monthly_bill' => true, 'is_finalized' => true, 'is_paid' => false, 'previous_due' => 0, 'description' => 'Fictional amounts for demonstration', 'created_at' => $now, 'updated_at' => $now,
        ]);
        foreach ($feeIds as $feeId => [$name, $amount]) {
            DB::table('student_claim_bill_fees')->insert(['student_claim_bill_id' => $billId, 'school_fee_type_id' => $feeId, 'fee_type' => $name, 'quantity' => 1, 'unit_amount' => $amount, 'unit_discount' => 0, 'created_at' => $now, 'updated_at' => $now]);
        }
    }
    DB::table('school_events')->insert(['school_id' => $schoolId, 'text' => 'Demo: Parent–teacher meeting', 'start_date' => $now->copy()->setTime(10, 0), 'end_date' => $now->copy()->setTime(12, 0), 'color' => '#18725f', 'created_at' => $now, 'updated_at' => $now]);
    $admin = DB::table('school_admins')->where('school_id', $schoolId)->first();
    $super = DB::table('super_admins')->first();
    $gs = DB::table('grade_subject')->where('grade_id', $gradeId)->first();
    file_put_contents($root . '/capture-context.json', json_encode([
        'provenance' => 'DatabaseSeeder + synthetic supplement; no imports', 'school' => 'Demo Academy',
        'schoolId' => $schoolId, 'sessionId' => $sessionId, 'gradeId' => $gradeId, 'subjectId' => $gs->subject_id,
        'examId' => $examId, 'examGradeId' => $examGradeId, 'date' => $now->toDateString(),
        'users' => ['Super Admin' => 'user' . $super->user_id . '@demo.example.test', 'School Admin' => 'user' . $admin->user_id . '@demo.example.test', 'Teacher' => 'user' . $teacher->user_id . '@demo.example.test', 'Accountant' => 'user' . $accountant->user_id . '@demo.example.test', 'Guardian' => 'user' . $guardian->user_id . '@demo.example.test'],
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
});
echo "Synthetic demo data ready.\n";
