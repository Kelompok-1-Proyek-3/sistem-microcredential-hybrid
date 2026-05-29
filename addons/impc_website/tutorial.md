# IMPC Endpoint Access Tutorial

This guide lists the required Odoo modules and Python libraries, then shows how to install them and access all IMPC endpoints.

## 1) Required Odoo modules (addons)
These are required by the module manifest and are installed automatically when you install `impc_website`:

- website_slides
- website_sale_slides
- website_sale
- website_slides_survey
- event
- portal
- mail

Notes:
- Their dependencies (website, sale, account, etc) are handled by Odoo automatically.
- If any of these are missing, the module will not load and the routes will return 404.

## 2) Required Python libraries
These are used for certificate PDF and QR features:

- reportlab
- qrcode
- pillow

Install them inside the Odoo container.

## 3) One time setup (Docker)
Assume the database name is `Odoo` and the web container is `sistem-microcredential-hybrid-web-1`.

1) Start the stack
```bash
docker compose up -d
```

2) Ensure the Odoo config includes custom addons
File: /etc/odoo/odoo.conf in the container should include `/mnt/extra-addons`.
Example content:
```ini
[options]
db_host = db
db_port = 5432
db_user = odoo
db_password = !password123
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons,/var/lib/odoo/.local/share/Odoo/addons/19.0
```

3) Install Python libraries
```bash
docker exec -i sistem-microcredential-hybrid-web-1 python3 -m pip install reportlab qrcode pillow
```

4) Install the module and its dependencies
```bash
docker exec -i sistem-microcredential-hybrid-web-1 \
  odoo -d Odoo -i impc_website --stop-after-init

docker restart sistem-microcredential-hybrid-web-1
```

## 4) Public routes (no login)
Open these in your browser:
- http://localhost:8069/impc
- http://localhost:8069/impc/courses
- http://localhost:8069/impc/courses/<course_id>
- http://localhost:8069/impc/about
- http://localhost:8069/impc/pricing
- http://localhost:8069/impc/corporate-training
- http://localhost:8069/impc/verify
- http://localhost:8069/impc/faq

Notes:
- `/impc/courses/<course_id>` requires a published course. Create a course in `/slides` and set it to published.

## 5) Protected routes (login required)
Login at:
- http://localhost:8069/web/login

Then open:
- http://localhost:8069/impc/my-learning

## 6) Public API endpoint (no login)
Certificate verification (needs a real verification code in DB):

```bash
curl http://localhost:8069/api/v1/certificate/verify/<code>
```

## 7) Authenticated JSON endpoints (login required)
These endpoints are `type="json"` and require JSON-RPC plus a session cookie.

1) Create a session
```bash
curl -c cookies.txt -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","params":{"db":"Odoo","login":"admin","password":"admin"}}' \
  http://localhost:8069/web/session/authenticate
```

2) Example: redeem code validation
```bash
curl -b cookies.txt -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","params":{"code":"IMPC-XXXX-XXXX-XXXX"}}' \
  http://localhost:8069/api/v1/redeem/validate
```

3) Example: student progress
```bash
curl -b cookies.txt -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","params":{}}' \
  http://localhost:8069/api/v1/student/progress
```

## 8) Data prerequisites
Some endpoints require real data:
- Courses: create and publish at least one course in `/slides`.
- Certificates: complete a course to generate a certificate and get its `verification_code`.
- Redeem codes: generate a batch in the backend or via the redeem code menu.

## 9) Important notes about missing endpoints
The following routes are listed in the README but are not implemented in code yet. No module install will enable them until they are coded:

- GET /impc/logout
- GET /impc/my-learning/<enrollment_id>
- POST /api/v1/elearning/courses
- GET /api/v1/elearning/courses/<id>
- POST /api/v1/elearning/redeem/claim
- GET /api/v1/elearning/enrollments/<id>/status
- GET /api/v1/elearning/enrollments/my
- GET /api/v1/elearning/progress/<enrollment_id>
- POST /api/v1/elearning/progress/<enrollment_id>/update
- GET /api/v1/elearning/certificates/my
- GET /api/v1/elearning/certificates/download/<id>
- GET /api/v1/elearning/certificates/<id>/qrcode
- POST /api/v1/elearning/certificates/verify
- POST /api/v1/webhooks/invoice-paid

If you want, create these endpoints or update README to match the current implementation.
