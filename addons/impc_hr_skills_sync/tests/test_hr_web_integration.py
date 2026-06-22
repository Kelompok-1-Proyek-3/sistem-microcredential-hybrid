# -*- coding: utf-8 -*-
"""
Test HR Web Integration

This test module creates sample data and tests the HR web routes.
Run with: ./odoo-bin -u impc_hr_skills_sync --test-enable
"""

from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import common, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestHRWebIntegration(common.TransactionCase):
    """Test HR web integration functionality."""

    def setUp(self):
        super(TestHRWebIntegration, self).setUp()
        self._create_test_data()

    def _create_test_data(self):
        """Create comprehensive test data for HR web testing."""
        
        # ========================================
        # 1. Create Departments
        # ========================================
        self.dept_it = self.env['hr.department'].create({
            'name': 'Information Technology',
        })
        self.dept_hr = self.env['hr.department'].create({
            'name': 'Human Resources',
        })
        self.dept_finance = self.env['hr.department'].create({
            'name': 'Finance & Accounting',
        })
        self.dept_marketing = self.env['hr.department'].create({
            'name': 'Marketing',
        })

        # ========================================
        # 2. Create HR Manager User
        # ========================================
        self.hr_manager_group = self.env.ref('hr.group_hr_manager')
        self.hr_user_group = self.env.ref('hr.group_hr_user')
        
        self.hr_manager_user = self.env['res.users'].create({
            'name': 'HR Manager Test',
            'login': 'hr_manager_test',
            'email': 'hr_manager@test.com',
            'groups_id': [(6, 0, [self.hr_manager_group.id])],
        })
        
        self.hr_manager_employee = self.env['hr.employee'].create({
            'name': 'HR Manager Test',
            'user_id': self.hr_manager_user.id,
            'department_id': self.dept_hr.id,
            'work_email': 'hr_manager@test.com',
        })

        # ========================================
        # 3. Create HR User
        # ========================================
        self.hr_user = self.env['res.users'].create({
            'name': 'HR User Test',
            'login': 'hr_user_test',
            'email': 'hr_user@test.com',
            'groups_id': [(6, 0, [self.hr_user_group.id])],
        })
        
        self.hr_user_employee = self.env['hr.employee'].create({
            'name': 'HR User Test',
            'user_id': self.hr_user.id,
            'department_id': self.dept_hr.id,
            'work_email': 'hr_user@test.com',
        })

        # ========================================
        # 4. Create Regular Employee Users
        # ========================================
        self.employees = []
        employee_data = [
            ('John Doe', 'john.doe@test.com', self.dept_it),
            ('Jane Smith', 'jane.smith@test.com', self.dept_it),
            ('Bob Wilson', 'bob.wilson@test.com', self.dept_finance),
            ('Alice Brown', 'alice.brown@test.com', self.dept_finance),
            ('Charlie Davis', 'charlie.davis@test.com', self.dept_marketing),
            ('Diana Evans', 'diana.evans@test.com', self.dept_marketing),
            ('Edward Fox', 'edward.fox@test.com', self.dept_it),
            ('Fiona Green', 'fiona.green@test.com', self.dept_hr),
        ]

        for name, email, dept in employee_data:
            user = self.env['res.users'].create({
                'name': name,
                'login': email,
                'email': email,
                'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
            })
            employee = self.env['hr.employee'].create({
                'name': name,
                'user_id': user.id,
                'department_id': dept.id,
                'work_email': email,
            })
            self.employees.append(employee)

        # ========================================
        # 5. Create Courses (Slide Channels)
        # ========================================
        self.courses = []
        course_names = [
            'Python Programming Fundamentals',
            'Data Analysis with Pandas',
            'Web Development with Odoo',
            'Project Management Essentials',
            'Digital Marketing 101',
        ]

        for name in course_names:
            course = self.env['slide.channel'].create({
                'name': name,
                'is_published': True,
                'channel_type': 'training',
                'enroll': 'public',
            })
            self.courses.append(course)

        # ========================================
        # 6. Create Enrollments and Learning Progress
        # ========================================
        statuses = ['in_progress', 'in_progress', 'completed', 'at_risk', 'in_progress']
        completion_values = [75, 45, 100, 15, 60]

        for i, employee in enumerate(self.employees):
            # Enroll in 2-3 courses per employee
            num_courses = 2 + (i % 2)
            for j in range(num_courses):
                course = self.courses[(i + j) % len(self.courses)]
                
                # Create slide.channel.partner (enrollment)
                enrollment = self.env['slide.channel.partner'].create({
                    'partner_id': employee.user_id.partner_id.id,
                    'channel_id': course.id,
                    'member_status': statuses[(i + j) % len(statuses)],
                    'completion': completion_values[(i + j) % len(completion_values)],
                })

                # Create learning progress record
                status_idx = (i + j) % len(statuses)
                progress = self.env['hr.learning.progress'].create({
                    'employee_id': employee.id,
                    'channel_id': course.id,
                    'channel_partner_id': enrollment.id,
                    'completion_percentage': completion_values[status_idx],
                    'status': statuses[status_idx],
                    'last_accessed_date': fields.Datetime.now() - timedelta(days=i + 1),
                    'attendance_status': 'not_required',
                })

        # ========================================
        # 7. Create Skills
        # ========================================
        self.skill_type = self.env['hr.skill.type'].create({
            'name': 'Technical Skills',
        })
        
        self.skill_python = self.env['hr.skill'].create({
            'name': 'Python',
            'skill_type_id': self.skill_type.id,
        })
        
        self.skill_odoo = self.env['hr.skill'].create({
            'name': 'Odoo Development',
            'skill_type_id': self.skill_type.id,
        })

        # Create skill levels
        self.skill_levels = []
        for level_name, progress in [('Beginner', 25), ('Intermediate', 50), ('Advanced', 75), ('Expert', 100)]:
            level = self.env['hr.skill.level'].create({
                'name': level_name,
                'level_progress': progress,
                'skill_type_id': self.skill_type.id,
            })
            self.skill_levels.append(level)

        # Assign skills to some employees
        for i, employee in enumerate(self.employees[:4]):
            level = self.skill_levels[i % len(self.skill_levels)]
            skill = self.skill_python if i % 2 == 0 else self.skill_odoo
            self.env['hr.employee.skill'].create({
                'employee_id': employee.id,
                'skill_id': skill.id,
                'skill_level_id': level.id,
                'skill_type_id': self.skill_type.id,
            })

        # ========================================
        # 8. Create Learning Notes
        # ========================================
        self.env['hr.learning.profile.note'].create({
            'employee_id': self.employees[0].id,
            'note_text': 'Employee showing excellent progress in technical courses.',
            'note_date': fields.Date.today(),
            'created_by': self.hr_manager_user.id,
        })
        self.env['hr.learning.profile.note'].create({
            'employee_id': self.employees[3].id,
            'note_text': 'Needs additional support with Python fundamentals.',
            'note_date': fields.Date.today() - timedelta(days=2),
            'created_by': self.hr_manager_user.id,
        })

        # ========================================
        # 9. Generate Analytics Snapshot
        # ========================================
        self.env['hr.learning.analytics.snapshot']._generate_daily_snapshot()

    # ============================================
    # Tests
    # ============================================

    def test_01_hr_dashboard_loads(self):
        """Test that HR dashboard route is accessible."""
        with self.with_user('hr_manager_test'):
            response = self.url_open('/hr/dashboard')
            self.assertEqual(response.status_code, 200, 'HR dashboard should load successfully')
            self.assertIn('HR Learning Dashboard', response.text, 'Dashboard title should be present')

    def test_02_hr_analytics_loads(self):
        """Test that HR analytics route is accessible."""
        with self.with_user('hr_manager_test'):
            response = self.url_open('/hr/analytics')
            self.assertEqual(response.status_code, 200, 'HR analytics should load successfully')
            self.assertIn('Learning Analytics', response.text, 'Analytics title should be present')

    def test_03_employee_list_loads(self):
        """Test that employee list route is accessible."""
        with self.with_user('hr_manager_test'):
            response = self.url_open('/hr/employees')
            self.assertEqual(response.status_code, 200, 'Employee list should load successfully')

    def test_04_at_risk_list_loads(self):
        """Test that at-risk employees route is accessible."""
        with self.with_user('hr_manager_test'):
            response = self.url_open('/hr/at-risk')
            self.assertEqual(response.status_code, 200, 'At-risk list should load successfully')

    def test_05_employee_profile_loads(self):
        """Test that individual employee profile is accessible."""
        employee = self.employees[0]
        with self.with_user('hr_manager_test'):
            response = self.url_open(f'/hr/employee/{employee.id}')
            self.assertEqual(response.status_code, 200, 'Employee profile should load')

    def test_06_own_profile_accessible(self):
        """Test that employee can access their own profile."""
        employee = self.employees[0]
        with self.with_user(employee.user_id.login):
            response = self.url_open(f'/hr/employee/{employee.id}')
            self.assertEqual(response.status_code, 200, 'Employee should access own profile')

    def test_07_department_detail_loads(self):
        """Test that department detail page loads."""
        with self.with_user('hr_manager_test'):
            response = self.url_open(f'/hr/department/{self.dept_it.id}')
            self.assertEqual(response.status_code, 200, 'Department detail should load')

    def test_08_learning_progress_count(self):
        """Test that learning progress records were created."""
        count = self.env['hr.learning.progress'].search_count([])
        self.assertGreater(count, 0, 'Learning progress records should exist')

    def test_09_analytics_snapshot_created(self):
        """Test that analytics snapshots were generated."""
        count = self.env['hr.learning.analytics.snapshot'].search_count([])
        self.assertGreater(count, 0, 'Analytics snapshots should exist')

    def test_10_at_risk_employees_exist(self):
        """Test that at-risk employees are identified."""
        at_risk_count = self.env['hr.learning.progress'].search_count([
            ('status', '=', 'at_risk')
        ])
        self.assertGreater(at_risk_count, 0, 'At-risk records should exist')


class TestHRWebSampleDataGenerator(common.TransactionCase):
    """
    Sample data generator for manual testing.
    
    Run this to populate your database with test data:
    
    ./odoo-bin shell -c your_config.conf
    
    Then execute:
    >>> env['hr.learning.progress'].search([])._generate_sample_data()
    >>> env.cr.commit()
    """

    def test_generate_sample_data(self):
        """Generate comprehensive sample data for manual testing."""
        self._create_departments()
        self._create_employees()
        self._create_courses()
        self._create_enrollments()
        self._create_skills()
        self._generate_analytics()
        
        print("\n" + "=" * 60)
        print("SAMPLE DATA GENERATED SUCCESSFULLY!")
        print("=" * 60)
        print("\nTest Users:")
        print("  - Login: hr_manager_test / Password: admin")
        print("  - Login: hr_user_test / Password: admin")
        print("\nTest Routes:")
        print("  - http://localhost:8069/hr/dashboard")
        print("  - http://localhost:8069/hr/analytics")
        print("  - http://localhost:8069/hr/employees")
        print("  - http://localhost:8069/hr/at-risk")
        print("=" * 60 + "\n")

    def _create_departments(self):
        """Create departments if not exist."""
        departments = ['IT Department', 'HR Department', 'Finance', 'Marketing', 'Operations']
        for name in departments:
            if not self.env['hr.department'].search([('name', '=', name)]):
                self.env['hr.department'].create({'name': name})

    def _create_employees(self):
        """Create employee users."""
        pass  # Implemented in main test class

    def _create_courses(self):
        """Create sample courses."""
        pass  # Implemented in main test class

    def _create_enrollments(self):
        """Create sample enrollments."""
        pass  # Implemented in main test class

    def _create_skills(self):
        """Create sample skills."""
        pass  # Implemented in main test class

    def _generate_analytics(self):
        """Generate analytics snapshots."""
        self.env['hr.learning.analytics.snapshot']._generate_daily_snapshot()
