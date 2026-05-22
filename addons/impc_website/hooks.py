def post_init_hook(env):
    """Create a default website if none exists, preventing website configurator."""
    if not env['website'].search_count([]):
        env['website'].create({
            'name': 'IMPC Microcredential Platform',
            'company_id': env.ref('base.main_company').id,
            'user_id': env.ref('base.public_user').id,
        })
