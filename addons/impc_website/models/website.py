from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    impc_homepage_title = fields.Char(
        string='IMPC Homepage Title',
        default='Indonesia Microcredential Platform Center',
    )
    impc_homepage_subtitle = fields.Char(
        string='IMPC Homepage Subtitle',
        default='Tingkatkan kompetensi Anda dengan sertifikasi mikro yang diakui industri',
    )
    impc_stats_students = fields.Integer(
        string='Total Students (Display)',
        default=0,
    )
    impc_stats_courses = fields.Integer(
        string='Total Courses (Display)',
        default=0,
    )
    impc_stats_certificates = fields.Integer(
        string='Total Certificates (Display)',
        default=0,
    )
    impc_stats_partners = fields.Integer(
        string='Total Corporate Partners (Display)',
        default=0,
    )
