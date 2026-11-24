import frappe

from non_profit.setup import setup_non_profit


NON_PROFIT_DOCTYPES = (
	"Member",
	"Membership",
	"Donor",
	"Donation",
	"Volunteer",
	"Chapter",
	"Grant Application",
	"Tax Exemption 80G Certificate",
)


def check_app_permission():
	"""Show the Non Profit app on the apps screen to desk users who can read any of its records."""
	if frappe.session.user == "Administrator":
		return True

	if frappe.get_cached_value("User", frappe.session.user, "user_type") != "System User":
		return False

	return any(frappe.has_permission(doctype, "read") for doctype in NON_PROFIT_DOCTYPES)


def get_company():
	company = frappe.defaults.get_defaults().company
	if company:
		return company
	else:
		company = frappe.get_list("Company", limit=1)
		if company:
			return company[0].name
	return None


def before_tests():
	# complete setup if missing
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
	from frappe.utils import getdate

	if not frappe.get_list("Company"):
		year = getdate().year
		setup_complete(
			{
				"currency": "USD",
				"full_name": "Test User",
				"company_name": "Frappe Non Profit LLC",
				"timezone": "America/New_York",
				"company_abbr": "FNP",
				"country": "United States",
				"fy_start_date": f"{year}-01-01",
				"fy_end_date": f"{year}-12-31",
				"language": "english",
				"company_tagline": "Testing",
				"email": "test@erpnext.com",
				"password": "test",
				"chart_of_accounts": "Standard",
			}
		)

	setup_non_profit()
	frappe.db.commit()
