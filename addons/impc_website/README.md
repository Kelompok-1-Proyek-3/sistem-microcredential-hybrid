# IMPC Website Module - Complete Documentation

## Overview

The IMPC Website Module provides a complete hybrid eLearning platform with the following features:
- Public course catalog with filtering
- B2C direct enrollment via eCommerce
- B2B bulk enrollment via redeem codes/vouchers
- Student progress tracking
- Hybrid attendance syncing from Events module
- Digital certificate generation with QR codes
- Public certificate verification API

## Architecture

### Models (12 total)

1. **elearning.course** - Core course entity
   - Supports ONLINE, OFFLINE, HYBRID modes
   - Links to Events module for hybrid sessions
   - Computed fields: completion rates, enrollment stats

2. **elearning.course_category** - Course organization

3. **elearning.course_enrollment** - Student enrollments
   - Types: B2C_PAID, B2B_VOUCHER, FREE
   - Links to payment info and redeem codes
   - Auto-creates progress tracking

4. **elearning.student_progress** - Per-enrollment progress
   - Completion percentage (0-100%)
   - Quiz scores and passing status
   - Status tracking (IN_PROGRESS, COMPLETED, AT_RISK)

5. **elearning.module_completion** - Granular module tracking
   - Tracks individual module completion
   - Contributes to overall completion %

6. **elearning.redeem_code** - B2B vouchers
   - Cryptographically random 16-char codes (IMPC-XXXX-XXXX-XXXX)
   - SHA-256 hashed storage
   - Quota management with audit logging

7. **elearning.redeem_code_batch** - Bulk code generation tracking

8. **elearning.redeem_code_audit** - Action audit trail
   - Logs: CREATED, CLAIMED, INVALIDATED, OVERRIDE

9. **elearning.session_attendance** - Hybrid attendance tracking
   - Synced from event.registration every 2 minutes (scheduled action)
   - Exam eligibility enforcement for HYBRID/OFFLINE courses

10. **elearning.certificate** - Issued certificates
    - One per completed enrollment
    - SHA-256 hash for integrity
    - Revocation tracking

11. **elearning.certificate_template** - Certificate designs
    - Customizable QR code positioning
    - Template versioning

12. **elearning.certificate_verification_log** - Verification audit trail

### Routes

#### Public Routes (auth='public')
- `GET /impc` - Homepage with featured courses
- `GET /impc/courses` - Course catalog (filterable)
- `GET /impc/courses/<code>` - Course detail page
- `GET /impc/about` - About page
- `GET /impc/faq` - FAQ
- `GET /impc/verify` - Certificate verification

#### Protected Routes (auth='user')
- `GET /impc/my-learning` - Student dashboard
- `GET /impc/my-learning/<enrollment_id>` - Enrollment detail
- `GET /impc/logout` - Logout & redirect

#### JSON API Endpoints

**Courses**
- `POST /api/v1/elearning/courses` - List courses (filterable)
- `GET /api/v1/elearning/courses/<id>` - Course details

**Redeem Codes (B2B)**
- `POST /api/v1/elearning/redeem/validate` - Validate code without claiming
- `POST /api/v1/elearning/redeem/claim` - Claim code & create enrollment (auth=user)

**Enrollment**
- `GET /api/v1/elearning/enrollments/<id>/status` - Enrollment status (auth=user)
- `GET /api/v1/elearning/enrollments/my` - Student's enrollments (auth=user)

**Progress**
- `GET /api/v1/elearning/progress/<enrollment_id>` - Student progress (auth=user)
- `POST /api/v1/elearning/progress/<enrollment_id>/update` - Update progress (auth=user)

**Certificates**
- `GET /api/v1/elearning/certificates/my` - Student's certificates (auth=user)
- `GET /api/v1/elearning/certificates/download/<id>` - Download PDF (auth=user)
- `GET /api/v1/elearning/certificates/<id>/qrcode` - QR code image (auth=public)
- `POST /api/v1/elearning/certificates/verify` - Verify certificate (auth=public)

**Webhooks**
- `POST /api/v1/webhooks/invoice-paid` - Payment webhook → B2C enrollment

## Data Models

### Course Fields
```python
name: Char (required)
code: Char (unique, required)
learning_mode: Selection (ONLINE, OFFLINE, HYBRID)
difficulty_level: Selection (BEGINNER, INTERMEDIATE, ADVANCED)
price: Float (required, >= 0)
passing_score: Float (70 default, 0-100 range)
is_published: Boolean (default False)
active: Boolean (default True)
rating: Float (0-5, default 0)
enrollment_count: Integer (computed)
event_id: Many2one (link to event.event for HYBRID)
```

### Enrollment Fields
```python
course_id: Many2one (required)
student_id: Many2one (required)
enrollment_type: Selection (B2C_PAID, B2B_VOUCHER, FREE)
status: Selection (ACTIVE, COMPLETED, DROPPED, AT_RISK)
payment_id: Char (invoice ID for B2C)
redeem_code_id: Many2one (link to redeem_code for B2B)
```

### Progress Fields
```python
enrollment_id: Many2one (1:1 link)
completion_percentage: Float (0-100, computed)
status: Selection (IN_PROGRESS, COMPLETED, AT_RISK)
quiz_score: Float (percentage)
quiz_passed: Boolean (score >= course.passing_score)
completion_date: Datetime (set when 100% + passed)
```

### Redeem Code Fields
```python
code: Char (unique, IMPC-XXXX-XXXX-XXXX format)
hash_id: Char (SHA-256, unique)
course_id: Many2one
quota: Integer (initial allocation)
quota_used: Integer (current claims)
quota_remaining: Integer (computed)
expiry_date: Date
isValid: Boolean (can be invalidated)
status: Selection (VALID, INVALID, EXPIRED, EXHAUSTED)
```

## Business Logic

### Enrollment Flow

**B2C (Direct Purchase)**
1. Customer adds course to cart
2. eCommerce checkout → Accounting invoice created
3. Payment processed → invoice.state = 'paid'
4. Webhook `/api/v1/webhooks/invoice-paid` triggered
5. B2C enrollment auto-created with `enrollment_type=B2C_PAID`
6. Student progress initialized (0% completion)

**B2B (Voucher)**
1. Student enters redeem code on course detail page
2. Frontend calls `POST /api/v1/elearning/redeem/validate`
3. If valid, frontend shows enroll button
4. Student clicks "Enroll with Voucher"
5. `POST /api/v1/elearning/redeem/claim` called (auth=user)
6. validate_code method:
   - Checks: valid, not expired, quota available
   - Creates B2B enrollment with `enrollment_type=B2B_VOUCHER`
   - Decrements quota
   - Logs audit entry
7. Student progress initialized

### Progress Tracking

- Students must complete ALL modules (100% completion)
- Students must pass final exam (score >= course.passing_score)
- HYBRID courses require offline session attendance (elearning.session_attendance.status='HADIR')
- When both module completion AND exam passing → completion_date set
- Scheduled action every 5 minutes generates certificates

### Exam Eligibility

- **ONLINE**: Always eligible if modules complete
- **HYBRID**: Must have attendance record with status='HADIR'
- **OFFLINE**: Must have attendance record with status='HADIR'

### Certificate Issuance

1. Scheduled action checks: completion_percentage==100 AND quiz_passed==True
2. Validates mode-specific requirements
3. Generates certificate:
   - Certificate number: CERT-YYYY-XXXXX (sequential)
   - Hash ID: SHA-256(student_id + course_id + timestamp + salt)
   - QR code: /impc/verify?hash=<hash_id>&cert=<number>
   - PDF generated (ReportLab)
   - Stored locally or S3 (configurable)
4. Email sent to student with download link
5. Certificate marked VALID, accessible via dashboard

### Redeem Code Security

- Generated via Python secrets (cryptographically random)
- Stored as SHA-256 hashes (one-way)
- Uniqueness guaranteed via DB constraint
- Anti-fraud: last name validation on verification
- Audit trail: every claim/invalidation logged
- Rate limiting: verification log tracks IP + timestamp

## Configuration

### Settings (to be added to settings.xml)

```xml
<data noupdate="1">
    <!-- Certificate generation -->
    <record id="certificate_pdf_generation_enabled" model="ir.config_parameter">
        <field name="key">impc.certificate.pdf_generation</field>
        <field name="value">True</field>
    </record>
    
    <!-- PDF storage location -->
    <record id="certificate_storage_path" model="ir.config_parameter">
        <field name="key">impc.certificate.storage_path</field>
        <field name="value">/var/impc/certificates</field>
    </record>
    
    <!-- Attendance sync interval -->
    <record id="attendance_sync_interval" model="ir.config_parameter">
        <field name="key">impc.attendance.sync_interval</field>
        <field name="value">2</field>  <!-- minutes -->
    </record>
</data>
```

## Testing

Run tests:
```bash
# Unit tests
odoo-bin -m pytest addons/impc_website/tests/ -v

# Test specific class
odoo-bin -m pytest addons/impc_website/tests/test_elearning.py::TestElearningCourse -v

# Test with coverage
odoo-bin -m pytest addons/impc_website/tests/ --cov=addons/impc_website --cov-report=html
```

## Deployment

### Dependencies
```
# In __manifest__.py
'depends': [
    'website',
    'website_slides',
    'portal',
    'event',
    'sale',
    'account',
],

# Python packages
reportlab
qrcode
pillow
```

### Installation
```bash
# 1. Copy module to addons
cp -r addons/impc_website /path/to/odoo/addons/

# 2. Install module
odoo-bin -d <database> -i impc_website

# 3. Create scheduled actions (automatic via data files)
# attendance sync: every 2 minutes
# certificate generation: every 5 minutes
```

### Database Backups
Before deploying:
```bash
pg_dump odoo_production > backup_$(date +%Y%m%d).sql
```

## Event Publishing

### Automatic Publishing
When an event is approved through the IMPC approval workflow, it is automatically published to the website:

```python
def action_impc_approve(self):
    """Administrator approves the event and confirms it."""
    self.write({
        "impc_approval_state": "approved",
        "impc_reviewed_by": self.env.user.id,
        "impc_review_date": fields.Datetime.now(),
        "website_published": True,  # Auto-publish
    })
```

### Manual Publishing Options

**Option 1: Individual Event (UI)**
1. Open event in backend
2. Go to "IMPC Approval" tab
3. Click "Publish to Website" button (only visible for approved but unpublished events)

**Option 2: Bulk Publish (Wizard)**
1. Go to Events > Events list view
2. Select multiple approved events (optional)
3. Click Action > "Publish Approved Events"
4. Wizard shows count of events to publish
5. Click "Publish Events" button

**Option 3: Programmatic (Shell)**
```python
# In Odoo shell
events = env['event.event'].search([
    ('impc_approval_state', '=', 'approved'),
    ('website_published', '=', False),
])
events.write({'website_published': True})
env.cr.commit()
```

### Auto-Publish Hook
The module includes a `post_load_hook` that automatically publishes all approved but unpublished events when the module is upgraded:

```bash
python odoo-bin -u impc_website -d your_database
```

This ensures legacy events are automatically published after upgrade.

## Future Enhancements (Beyond Scope)

1. **Recommendations Engine** - Suggest courses based on completion history
2. **Leaderboards** - Student rankings by completion rate
3. **Mobile App** - React Native app for course access
4. **Adaptive Learning** - ML-based difficulty adjustment
5. **Corporate Analytics** - B2B company dashboards
6. **Microlearning** - 5-minute micro-content modules
7. **Gamification** - Badges, streaks, achievements
8. **Peer Review** - Student assessment workflows

## Support & Troubleshooting

### Issue: Attendance not syncing
**Solution**: Check scheduled action `cron_sync_attendance_from_events` is active. Verify event.registration records exist.

### Issue: Certificate PDF generation fails
**Solution**: Install reportlab: `pip install reportlab`. Check `/var/impc/certificates` directory exists and is writable.

### Issue: Redeem code not validating
**Solution**: Check code hasn't been invalidated. Check expiry_date. Check quota_remaining > 0.

## Performance Considerations

- Course listings indexed on: code, learning_mode, is_published
- Progress queries use course_id + student_id composite index
- Attendance sync runs every 2 min (not real-time) to avoid overload
- Certificate generation batched every 5 min
- Use read replicas for reporting queries

## Security

- All user data is encrypted in transit (HTTPS enforced)
- Redeem codes stored as hashes (one-way)
- Certificate verification logs rate-limited per IP
- API endpoints require authentication (except public course listing)
- CSRF tokens enabled on all POST endpoints
- SQL injection prevention via ORM parameterization
