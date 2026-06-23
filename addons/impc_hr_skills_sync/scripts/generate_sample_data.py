# -*- coding: utf-8 -*-
"""
HR Web Integration - Sample Data Generator

Run this script via Odoo shell to generate comprehensive test data:

    cd /path/to/odoo
    ./odoo-bin shell -c /path/to/config.conf -f addons/impc_hr_skills_sync/scripts/generate_sample_data.py

Or inside the Odoo shell interactively:

    >>> exec(open('addons/impc_hr_skills_sync/scripts/generate_sample_data.py').read())
    >>> generate_sample_data(env)
    >>> env.cr.commit()
"""

from datetime import datetime, timedelta
import random


def generate_sample_data(env):
    """Generate comprehensive sample data for HR web testing."""
    
    print("\n" + "=" * 60)
    print("GENERATING HR WEB INTEGRATION SAMPLE DATA...")
    print("=" * 60 + "\n")

    # ========================================
    # 1. Create/Ensure Departments
    # ========================================
    print("1. Creating departments...")
    departments_data = [
        ('Information Technology', 'IT'),
        ('Human Resources', 'HR'),
        ('Finance & Accounting', 'FIN'),
        ('Marketing', 'MKT'),
        ('Operations', 'OPS'),
        ('Sales', 'SLS'),
        ('Research & Development', 'RND'),
        ('Customer Support', 'CS'),
    ]
    
    departments = []
    for name, code in departments_data:
        dept = env['hr.department'].search([('name', '=', name)], limit=1)
        if not dept:
            dept = env['hr.department'].create({'name': name})
        departments.append(dept)
    
    print(f"   Created/found {len(departments)} departments")

    # ========================================
    # 2. Create HR Manager User
    # ========================================
    print("2. Creating HR Manager user...")
    hr_manager_group = env.ref('hr.group_hr_manager')
    
    hr_manager_user = env['res.users'].search([('login', '=', 'hr_manager_test')], limit=1)
    if not hr_manager_user:
        hr_manager_user = env['res.users'].create({
            'name': 'HR Manager Test',
            'login': 'hr_manager_test',
            'email': 'hr_manager@impc.test',
            'password': 'admin123',
            'groups_id': [(6, 0, [hr_manager_group.id])],
        })
        env['hr.employee'].create({
            'name': 'HR Manager Test',
            'user_id': hr_manager_user.id,
            'department_id': departments[1].id,  # HR Department
            'work_email': 'hr_manager@impc.test',
            'job_title': 'HR Manager',
        })
    print(f"   HR Manager: hr_manager_test / admin123")

    # ========================================
    # 3. Create HR User
    # ========================================
    print("3. Creating HR User...")
    hr_user_group = env.ref('hr.group_hr_user')
    
    hr_user = env['res.users'].search([('login', '=', 'hr_user_test')], limit=1)
    if not hr_user:
        hr_user = env['res.users'].create({
            'name': 'HR User Test',
            'login': 'hr_user_test',
            'email': 'hr_user@impc.test',
            'password': 'admin123',
            'groups_id': [(6, 0, [hr_user_group.id])],
        })
        env['hr.employee'].create({
            'name': 'HR User Test',
            'user_id': hr_user.id,
            'department_id': departments[1].id,
            'work_email': 'hr_user@impc.test',
            'job_title': 'HR Staff',
        })
    print(f"   HR User: hr_user_test / admin123")

    # ========================================
    # 4. Create Regular Employee Users
    # ========================================
    print("4. Creating regular employees...")
    employees_data = [
        ('Ahmad Rizki', 'ahmad.rizki@impc.test', departments[0], 'Software Developer'),
        ('Siti Nurhaliza', 'siti.nurhaliza@impc.test', departments[0], 'Senior Developer'),
        ('Budi Santoso', 'budi.santoso@impc.test', departments[0], 'DevOps Engineer'),
        ('Dewi Lestari', 'dewi.lestari@impc.test', departments[2], 'Accountant'),
        ('Eko Prasetyo', 'eko.prasetyo@impc.test', departments[2], 'Financial Analyst'),
        ('Fitri Handayani', 'fitri.handayani@impc.test', departments[3], 'Marketing Manager'),
        ('Gunawan Wibowo', 'gunawan.wibowo@impc.test', departments[3], 'Content Creator'),
        ('Hesti Rahayu', 'hesti.rahayu@impc.test', departments[4], 'Operations Lead'),
        ('Irwan Setiawan', 'irwan.setiawan@impc.test', departments[5], 'Sales Executive'),
        ('Joko Widodo', 'joko.widodo@impc.test', departments[5], 'Sales Manager'),
        ('Kartini Sari', 'kartini.sari@impc.test', departments[6], 'Researcher'),
        ('Lukman Hakim', 'lukman.hakim@impc.test', departments[7], 'Support Agent'),
        ('Maya Indah', 'maya.indah@impc.test', departments[7], 'Support Lead'),
        ('Nurul Huda', 'nurul.huda@impc.test', departments[0], 'QA Engineer'),
        ('Oscar Pratama', 'oscar.pratama@impc.test', departments[0], 'Backend Developer'),
    ]

    employees = []
    user_group = env.ref('base.group_user')
    
    for name, email, dept, job_title in employees_data:
        user = env['res.users'].search([('login', '=', email)], limit=1)
        if not user:
            user = env['res.users'].create({
                'name': name,
                'login': email,
                'email': email,
                'password': 'admin123',
                'groups_id': [(6, 0, [user_group.id])],
            })
            employee = env['hr.employee'].create({
                'name': name,
                'user_id': user.id,
                'department_id': dept.id,
                'work_email': email,
                'job_title': job_title,
            })
            employees.append(employee)
        else:
            employee = env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee:
                employees.append(employee)
    
    print(f"   Created/found {len(employees)} employees")

    # ========================================
    # 5. Create Courses
    # ========================================
    print("5. Creating courses...")
    courses_data = [
        ('Python Programming Fundamentals', 'Beginner'),
        ('Advanced Python Development', 'Advanced'),
        ('Odoo 19 Development', 'Intermediate'),
        ('Data Science with Python', 'Intermediate'),
        ('Project Management Professional', 'Intermediate'),
        ('Digital Marketing Essentials', 'Beginner'),
        ('Cloud Computing with AWS', 'Advanced'),
        ('Agile & Scrum Methodology', 'Beginner'),
        ('Business Communication', 'Beginner'),
        ('Leadership & Management', 'Advanced'),
    ]

    courses = []
    for name, level in courses_data:
        course = env['slide.channel'].search([('name', '=', name)], limit=1)
        if not course:
            course = env['slide.channel'].create({
                'name': name,
                'is_published': True,
                'channel_type': 'training',
                'enroll': 'public',
                'description': f'{level} level course on {name}',
            })
        courses.append(course)
    
    print(f"   Created/found {len(courses)} courses")

    # ========================================
    # 6. Create Enrollments & Learning Progress
    # ========================================
    print("6. Creating enrollments and learning progress...")
    
    status_distribution = ['in_progress', 'in_progress', 'in_progress', 'completed', 'at_risk']
    completion_ranges = {
        'in_progress': (30, 80),
        'completed': (100, 100),
        'at_risk': (5, 25),
    }

    progress_count = 0
    for i, employee in enumerate(employees):
        # Each employee enrolls in 2-4 courses
        num_courses = random.randint(2, 4)
        selected_courses = random.sample(courses, min(num_courses, len(courses)))
        
        for course in selected_courses:
            status = random.choice(status_distribution)
            completion_min, completion_max = completion_ranges[status]
            completion = random.randint(completion_min, completion_max)
            
            # Check if enrollment exists
            enrollment = env['slide.channel.partner'].search([
                ('partner_id', '=', employee.user_id.partner_id.id),
                ('channel_id', '=', course.id),
            ], limit=1)
            
            if not enrollment:
                enrollment = env['slide.channel.partner'].create({
                    'partner_id': employee.user_id.partner_id.id,
                    'channel_id': course.id,
                    'member_status': 'completed' if status == 'completed' else 'joined',
                    'completion': completion,
                })
            
            # Check if progress exists
            progress = env['hr.learning.progress'].search([
                ('employee_id', '=', employee.id),
                ('channel_id', '=', course.id),
            ], limit=1)
            
            if not progress:
                days_ago = random.randint(1, 60)
                env['hr.learning.progress'].create({
                    'employee_id': employee.id,
                    'channel_id': course.id,
                    'channel_partner_id': enrollment.id,
                    'completion_percentage': completion,
                    'status': status,
                    'last_accessed_date': datetime.now() - timedelta(days=days_ago),
                    'attendance_status': random.choice(['not_required', 'not_required', 'hadir']),
                })
                progress_count += 1

    print(f"   Created {progress_count} learning progress records")

    # ========================================
    # 7. Create Skills
    # ========================================
    print("7. Creating skills...")
    
    # Create skill type
    skill_type = env['hr.skill.type'].search([('name', '=', 'Technical Skills')], limit=1)
    if not skill_type:
        skill_type = env['hr.skill.type'].create({'name': 'Technical Skills'})
    
    # Create skill levels
    levels_data = [
        ('Beginner', 25),
        ('Intermediate', 50),
        ('Advanced', 75),
        ('Expert', 100),
    ]
    skill_levels = {}
    for name, progress in levels_data:
        level = env['hr.skill.level'].search([
            ('name', '=', name),
            ('skill_type_id', '=', skill_type.id),
        ], limit=1)
        if not level:
            level = env['hr.skill.level'].create({
                'name': name,
                'level_progress': progress,
                'skill_type_id': skill_type.id,
            })
        skill_levels[name] = level

    # Create skills
    skills_data = [
        'Python',
        'JavaScript',
        'Odoo Development',
        'Data Analysis',
        'Project Management',
        'Communication',
    ]
    
    skills = []
    for skill_name in skills_data:
        skill = env['hr.skill'].search([
            ('name', '=', skill_name),
            ('skill_type_id', '=', skill_type.id),
        ], limit=1)
        if not skill:
            skill = env['hr.skill'].create({
                'name': skill_name,
                'skill_type_id': skill_type.id,
            })
        skills.append(skill)

    # Assign skills to employees
    skill_assign_count = 0
    for i, employee in enumerate(employees):
        # Assign 1-3 skills per employee
        num_skills = random.randint(1, 3)
        selected_skills = random.sample(skills, num_skills)
        
        for skill in selected_skills:
            existing = env['hr.employee.skill'].search([
                ('employee_id', '=', employee.id),
                ('skill_id', '=', skill.id),
            ], limit=1)
            
            if not existing:
                level_name = random.choice(list(skill_levels.keys()))
                env['hr.employee.skill'].create({
                    'employee_id': employee.id,
                    'skill_id': skill.id,
                    'skill_level_id': skill_levels[level_name].id,
                    'skill_type_id': skill_type.id,
                })
                skill_assign_count += 1

    print(f"   Assigned {skill_assign_count} skills to employees")

    # ========================================
    # 8. Create Learning Notes
    # ========================================
    print("8. Creating learning notes...")
    
    notes_data = [
        ('Showing excellent progress in technical courses.', employees[0] if employees else False),
        ('Needs support with project management concepts.', employees[3] if len(employees) > 3 else False),
        ('Completed all assigned courses ahead of schedule.', employees[1] if len(employees) > 1 else False),
        ('At risk due to low engagement. Follow-up scheduled.', employees[4] if len(employees) > 4 else False),
    ]
    
    note_count = 0
    for note_text, employee in notes_data:
        if employee:
            env['hr.learning.profile.note'].create({
                'employee_id': employee.id,
                'note_text': note_text,
                'note_date': datetime.now().date() - timedelta(days=random.randint(0, 7)),
            })
            note_count += 1

    print(f"   Created {note_count} learning notes")

    # ========================================
    # 9. Generate Analytics Snapshots
    # ========================================
    print("9. Generating analytics snapshots...")
    env['hr.learning.analytics.snapshot']._generate_daily_snapshot()
    print("   Analytics snapshot generated")

    # ========================================
    # Summary
    # ========================================
    total_progress = env['hr.learning.progress'].search_count([])
    at_risk = env['hr.learning.progress'].search_count([('status', '=', 'at_risk')])
    completed = env['hr.learning.progress'].search_count([('status', '=', 'completed')])
    
    print("\n" + "=" * 60)
    print("SAMPLE DATA GENERATION COMPLETE!")
    print("=" * 60)
    print(f"\nStatistics:")
    print(f"  - Departments: {len(departments)}")
    print(f"  - Employees: {len(employees)}")
    print(f"  - Courses: {len(courses)}")
    print(f"  - Learning Progress: {total_progress}")
    print(f"  - At-Risk: {at_risk}")
    print(f"  - Completed: {completed}")
    print("\nTest Users:")
    print("  - hr_manager_test / admin123")
    print("  - hr_user_test / admin123")
    print("\nTest Routes (login as HR Manager):")
    print("  - http://localhost:8069/hr/dashboard")
    print("  - http://localhost:8069/hr/analytics")
    print("  - http://localhost:8069/hr/employees")
    print("  - http://localhost:8069/hr/at-risk")
    print("=" * 60 + "\n")

    return True


# For direct shell execution
if __name__ == '__main__':
    # This block runs when executed in Odoo shell
    generate_sample_data(env)
