from odoo import SUPERUSER_ID, api


def post_init_hook(env):
    """Force certification + scoring on both IMPC survey templates every install/upgrade."""
    env = api.Environment(env.cr, SUPERUSER_ID, {})
    mail_template = env.ref(
        'marketing_microcredential.mail_template_survey_invite',
        raise_if_not_found=False,
    )
    survey_xmlids = [
        'marketing_microcredential.survey_post_course_satisfaction',
        'marketing_microcredential.survey_nps',
    ]
    for xmlid in survey_xmlids:
        survey = env.ref(xmlid, raise_if_not_found=False)
        if not survey:
            continue
        vals = {
            'certification': True,
            'scoring_type': 'scoring_without_answers',
        }
        if mail_template:
            vals['certification_mail_template_id'] = mail_template.id
        survey.write(vals)

        for question in survey.question_ids.filtered(
            lambda q: q.question_type != 'text_box'
        ):
            pass
