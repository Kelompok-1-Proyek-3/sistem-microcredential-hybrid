from odoo.orm.registry import Registry


def _clear_registry_caches(env):
    """Clear menu/view caches after changing backend security or menus."""
    env.registry.clear_cache()


def _ensure_demo_payment_journal(env):
    """Ensure the Demo payment provider has a journal and a payment.method.line."""
    demo_provider = env['payment.provider'].search([('code', '=', 'demo')], limit=1)
    if demo_provider:
        demo_provider._ensure_payment_journal()


def post_init_hook(env):
    """Create a default website if none exists, preventing website configurator."""
    if not env['website'].search_count([]):
        env['website'].create({
            'name': 'IMPC Microcredential Platform',
            'company_id': env.ref('base.main_company').id,
            'user_id': env.ref('base.public_user').id,
        })
    _ensure_demo_payment_journal(env)
    _clear_registry_caches(env)


def post_load():
    """Clear Python-level caches when the module is loaded by a worker."""
    for registry in Registry.registries.values():
        registry.clear_all_caches()
