import frappe


def execute():
	"""Pre-fill Non Profit Settings > Default Customer Group for Members.

	Uses the non-group Customer Group most of the existing member customers are in, so the
	"Create Customer" button on Member keeps creating customers the way they were created so far.
	"""
	if frappe.db.get_single_value("Non Profit Settings", "member_customer_group"):
		return

	member = frappe.qb.DocType("Member")
	customer = frappe.qb.DocType("Customer")
	customer_group = frappe.qb.DocType("Customer Group")
	count = frappe.query_builder.functions.Count(customer.name)

	most_used = (
		frappe.qb.from_(member)
		.join(customer)
		.on(customer.name == member.customer)
		.join(customer_group)
		.on(customer_group.name == customer.customer_group)
		.select(customer.customer_group, count.as_("customers"))
		.where(customer_group.is_group == 0)
		.groupby(customer.customer_group)
		.orderby(count, order=frappe.qb.desc)
		.limit(1)
	).run(as_dict=True)

	if most_used:
		frappe.db.set_single_value("Non Profit Settings", "member_customer_group", most_used[0].customer_group)
