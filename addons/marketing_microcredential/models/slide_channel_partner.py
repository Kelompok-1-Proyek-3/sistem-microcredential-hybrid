from datetime import timedelta

from odoo import fields, models


class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    post_course_survey_sent = fields.Boolean(
        string='Post-course Survey Sent',
        default=False,
        readonly=True,
    )
    post_course_survey_sent_at = fields.Datetime(
        string='Post-course Survey Sent At',
        readonly=True,
    )
    nps_survey_sent = fields.Boolean(
        string='NPS Survey Sent',
        default=False,
        readonly=True,
    )
    nps_survey_sent_at = fields.Datetime(
        string='NPS Survey Sent At',
        readonly=True,
    )

    def action_send_completion_surveys(self):
        template = self.env.ref(
            'marketing_microcredential.mail_template_survey_invite',
            raise_if_not_found=False,
        )
        for record in self:
            if record.member_status != 'completed' or record.completion < 100:
                continue
            partner = record.partner_id
            if not partner or not partner.email:
                continue

            if not record.post_course_survey_sent:
                record._send_survey_invite(
                    survey_xmlid='marketing_microcredential.survey_post_course_satisfaction',
                    template=template,
                    sent_field='post_course_survey_sent',
                    sent_at_field='post_course_survey_sent_at',
                )
            if not record.nps_survey_sent:
                record._send_survey_invite(
                    survey_xmlid='marketing_microcredential.survey_nps',
                    template=template,
                    sent_field='nps_survey_sent',
                    sent_at_field='nps_survey_sent_at',
                )
        return True

    def _send_survey_invite(self, survey_xmlid, template, sent_field, sent_at_field):
        self.ensure_one()
        survey = self.env.ref(survey_xmlid, raise_if_not_found=False)
        if not survey:
            return False

        partner = self.partner_id
        if not partner or not partner.email:
            return False

        user_input = self.env['survey.user_input'].sudo().create({
            'survey_id': survey.id,
            'partner_id': partner.id,
            'email': partner.email,
            'deadline': fields.Datetime.now() + timedelta(days=14),
        })

        if template:
            template.sudo().send_mail(user_input.id, force_send=True)

        self.sudo().write({
            sent_field: True,
            sent_at_field: fields.Datetime.now(),
        })
        return True
