import frappe


def execute():
	# The standard portal menu item used to point to /certification, which never existed.
	# The hook now points to /certification-application; drop the stale synced entry.
	frappe.db.delete(
		"Portal Menu Item",
		{"route": "/certification", "reference_doctype": "Certification Application"},
	)
