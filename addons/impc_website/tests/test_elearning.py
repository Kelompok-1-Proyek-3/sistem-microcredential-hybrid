"""
IMPC eLearning Module - Test Suite
==================================

Comprehensive tests for all functionality.
Run with: pytest tests/ or odoo-bin -m pytest addons/impc_website/tests/
"""

import unittest
from odoo.tests.common import TransactionCase, tagged
from datetime import datetime, timedelta, date


@tagged('impc', 'elearning', 'unit')
class TestElearningCourse(TransactionCase):
    """Test elearning.course model."""
    
    def setUp(self):
        super().setUp()
        self.Course = self.env['elearning.course']
        self.Category = self.env['elearning.course_category']
    
    def test_course_creation(self):
        """Test basic course creation."""
        category = self.Category.create({
            'name': 'Test Category',
        })
        
        course = self.Course.create({
            'name': 'Test Course',
            'code': 'TEST-001',
            'learning_mode': 'ONLINE',
            'difficulty_level': 'BEGINNER',
            'price': 1000000.0,
            'category_id': category.id,
        })
        
        self.assertTrue(course.exists())
        self.assertEqual(course.code, 'TEST-001')
        self.assertEqual(course.learning_mode, 'ONLINE')
    
    def test_course_publish_validation(self):
        """Test that HYBRID courses require event_id to publish."""
        from odoo.exceptions import ValidationError
        
        category = self.Category.create({'name': 'Test'})
        course = self.Course.create({
            'name': 'Hybrid Course',
            'code': 'HYBRID-001',
            'learning_mode': 'HYBRID',
            'difficulty_level': 'INTERMEDIATE',
            'price': 2000000.0,
            'category_id': category.id,
            'is_published': True,
        })
        
        # Should raise ValidationError due to missing event_id
        with self.assertRaises(ValidationError):
            course.action_publish()


@tagged('impc', 'elearning', 'unit')
class TestElearningEnrollment(TransactionCase):
    """Test elearning.course_enrollment model."""
    
    def setUp(self):
        super().setUp()
        self.Enrollment = self.env['elearning.course_enrollment']
        self.Course = self.env['elearning.course']
        self.Partner = self.env['res.partner']
    
    def test_b2c_enrollment_creation(self):
        """Test B2C enrollment creation."""
        # Create course
        course = self.Course.create({
            'name': 'Test Course',
            'code': 'TEST-B2C-001',
            'learning_mode': 'ONLINE',
            'difficulty_level': 'BEGINNER',
            'price': 1000000.0,
        })
        
        # Create student
        student = self.Partner.create({
            'name': 'Test Student',
            'email': 'student@test.com',
        })
        
        # Create B2C enrollment
        enrollment = self.Enrollment.create_b2c_enrollment(
            course_id=course.id,
            student_id=student.id,
            payment_id='PAY-123',
            amount=1000000.0,
        )
        
        self.assertTrue(enrollment.exists())
        self.assertEqual(enrollment.enrollment_type, 'B2C_PAID')
        self.assertEqual(enrollment.status, 'ACTIVE')


@tagged('impc', 'elearning', 'unit')
class TestRedeemCode(TransactionCase):
    """Test elearning.redeem_code model."""
    
    def setUp(self):
        super().setUp()
        self.RedeemCode = self.env['elearning.redeem_code']
        self.Course = self.env['elearning.course']
    
    def test_redeem_code_generation(self):
        """Test redeem code generation."""
        course = self.Course.create({
            'name': 'Test Course',
            'code': 'TEST-REDEEM-001',
            'learning_mode': 'ONLINE',
            'difficulty_level': 'BEGINNER',
            'price': 1000000.0,
        })
        
        # Generate codes
        codes = self.RedeemCode.generate_codes(
            course_id=course.id,
            quantity=5,
            expiry_days=90,
        )
        
        self.assertEqual(len(codes), 5)
        for code in codes:
            self.assertTrue(code.code.startswith('IMPC-'))
            self.assertTrue(code.isValid)
    
    def test_redeem_code_validation(self):
        """Test redeem code validation."""
        course = self.Course.create({
            'name': 'Test Course',
            'code': 'TEST-VALIDATE-001',
            'learning_mode': 'ONLINE',
            'difficulty_level': 'BEGINNER',
            'price': 1000000.0,
        })
        
        # Create redeem code
        redeem = self.RedeemCode.create({
            'course_id': course.id,
            'code': 'IMPC-TEST-XXXX-XXXX',
            'expiry_date': date.today() + timedelta(days=90),
            'quota': 10,
        })
        
        # Validation should pass
        self.assertTrue(redeem.isValid)
        self.assertEqual(redeem.quota_remaining, 10)


@tagged('impc', 'elearning', 'integration')
class TestEnrollmentFlow(TransactionCase):
    """Integration test for complete enrollment flow."""
    
    def setUp(self):
        super().setUp()
        self.Course = self.env['elearning.course']
        self.Enrollment = self.env['elearning.course_enrollment']
        self.Progress = self.env['elearning.student_progress']
        self.Partner = self.env['res.partner']
    
    def test_complete_b2c_enrollment_flow(self):
        """Test complete B2C enrollment workflow."""
        # 1. Create course
        course = self.Course.create({
            'name': 'Complete Flow Course',
            'code': 'FLOW-001',
            'learning_mode': 'ONLINE',
            'difficulty_level': 'BEGINNER',
            'price': 1000000.0,
        })
        course.action_publish()
        
        # 2. Create student
        student = self.Partner.create({
            'name': 'Flow Student',
            'email': 'flow@test.com',
        })
        
        # 3. Create B2C enrollment
        enrollment = self.Enrollment.create_b2c_enrollment(
            course_id=course.id,
            student_id=student.id,
            payment_id='PAY-FLOW-001',
            amount=1000000.0,
        )
        
        # 4. Verify enrollment created
        self.assertTrue(enrollment.exists())
        self.assertEqual(enrollment.status, 'ACTIVE')
        
        # 5. Verify progress tracking created
        progress = enrollment.student_progress_id
        self.assertTrue(progress.exists())
        self.assertEqual(progress.completion_percentage, 0.0)
        self.assertEqual(progress.status, 'IN_PROGRESS')


@tagged('impc', 'elearning', 'api')
class TestPublicAPI(TransactionCase):
    """Test public API endpoints."""
    
    def setUp(self):
        super().setUp()
        self.Course = self.env['elearning.course']
    
    def test_course_api_listing(self):
        """Test course listing API."""
        # Create courses
        for i in range(3):
            self.Course.create({
                'name': f'API Test Course {i}',
                'code': f'API-{i:03d}',
                'learning_mode': 'ONLINE',
                'difficulty_level': 'BEGINNER',
                'price': 1000000.0 * (i + 1),
                'is_published': True,
                'active': True,
            })
        
        # List courses
        courses = self.Course.search([
            ('active', '=', True),
            ('is_published', '=', True),
        ])
        
        self.assertEqual(len(courses), 3)


if __name__ == '__main__':
    unittest.main()
