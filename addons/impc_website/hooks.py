def post_init_hook(env):
    """Create a default website if none exists, preventing website configurator."""
    if not env['website'].search_count([]):
        env['website'].create({
            'name': 'IMPC Microcredential Platform',
            'company_id': env.ref('base.main_company').id,
            'user_id': env.ref('base.public_user').id,
        })


def post_load_hook(env):
    """Auto-publish all approved events when module is upgraded."""
    EventEvent = env['event.event']
    if hasattr(EventEvent, '_auto_publish_approved_events'):
        EventEvent._auto_publish_approved_events()
