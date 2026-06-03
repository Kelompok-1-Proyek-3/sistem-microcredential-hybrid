#!/usr/bin/env python3
"""
Script untuk mempublish semua event yang sudah approved ke website.
Jalankan dengan: python odoo-bin shell -d your_database -c odoo.conf --shell-interface=ipython
Kemudian paste kode berikut di shell:

    # Cek event yang approved tapi belum published
    events = env['event.event'].search([
        ('impc_approval_state', '=', 'approved'),
        ('website_published', '=', False),
    ])
    print(f"Found {len(events)} approved but unpublished events:")
    for event in events:
        print(f"  - {event.name} (ID: {event.id})")
    
    # Publish semua event yang approved
    if events:
        events.write({'website_published': True})
        env.cr.commit()
        print(f"Successfully published {len(events)} events!")
    else:
        print("No events to publish.")
"""
