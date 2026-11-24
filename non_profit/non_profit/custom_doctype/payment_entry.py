import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import get_bank_cash_account, get_reference_details
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_account_currency
from frappe.utils.data import flt, getdate


class NonProfitPaymentEntry:
	"""Mixin for Payment Entry (registered via `extend_doctype_class`).

	Adds support for receiving payments from a `Donor` against a `Donation`.
	Everything else is delegated to the standard (or otherwise extended) controller.
	"""

	def get_valid_reference_doctypes(self):
		if self.party_type == "Donor":
			return ("Donation",)

		return super().get_valid_reference_doctypes()

	def set_missing_ref_details(
		self,
		force: bool = False,
		update_ref_details_only_for: list | None = None,
		reference_exchange_details: dict | None = None,
	) -> None:
		# ERPNext doesn't know how to compute the outstanding amount of a Donation,
		# so let it handle every other reference and fill Donation rows here.
		other_references = [
			(d.reference_doctype, d.reference_name)
			for d in self.get("references")
			if d.reference_doctype != "Donation"
			and (
				not update_ref_details_only_for
				or (d.reference_doctype, d.reference_name) in update_ref_details_only_for
			)
		]

		if other_references:
			super().set_missing_ref_details(
				force=force,
				update_ref_details_only_for=other_references,
				reference_exchange_details=reference_exchange_details,
			)

		for d in self.get("references"):
			if d.reference_doctype != "Donation" or not d.allocated_amount:
				continue

			if (
				update_ref_details_only_for
				and (d.reference_doctype, d.reference_name) not in update_ref_details_only_for
			):
				continue

			ref_details = get_donation_reference_details(d.reference_name)
			values = {
				field: value
				for field, value in ref_details.items()
				if field == "exchange_rate" or not d.get(field) or force
			}

			if values and self.get("_action") in ("submit", "cancel") and not self.is_new():
				d.db_set(values)
			else:
				d.update(values)


@frappe.whitelist()
def get_donation_payment_entry(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	reference_doc = None
	doc = frappe.get_doc(dt, dn)

	party_account = get_party_account("Donor", doc.get("donor"), doc.company)
	party_account_currency = doc.get("party_account_currency") or get_account_currency(party_account)
	grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(party_amount, doc)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = set_paid_amount_and_received_amount(
		party_account_currency, bank, outstanding_amount, bank_amount, doc
	)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Receive"
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = getdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = "Donor"
	pe.party = doc.get("donor")
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")

	pe.paid_from = party_account
	pe.paid_to = bank.account
	pe.paid_from_account_currency = party_account_currency
	pe.paid_to_account_currency = bank.account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	pe.append(
		"references",
		{
			"reference_doctype": dt,
			"reference_name": dn,
			"bill_no": doc.get("bill_no"),
			"due_date": doc.get("due_date"),
			"total_amount": grand_total,
			"outstanding_amount": outstanding_amount,
			"allocated_amount": outstanding_amount,
		},
	)

	pe.setup_party_account_field()
	pe.set_missing_values()

	if party_account and bank:
		pe.set_exchange_rate(ref_doc=reference_doc)
		pe.set_amounts()

	return pe


def set_grand_total_and_outstanding_amount(party_amount, doc):
	if party_amount:
		grand_total = outstanding_amount = party_amount
	else:
		grand_total = outstanding_amount = doc.amount

	return grand_total, outstanding_amount


def set_paid_amount_and_received_amount(party_account_currency, bank, outstanding_amount, bank_amount, doc):
	if party_account_currency == bank.account_currency:
		paid_amount = received_amount = abs(outstanding_amount)
	else:
		paid_amount = abs(outstanding_amount)
		if bank_amount:
			received_amount = bank_amount
		else:
			received_amount = paid_amount * doc.get("conversion_rate", 1)

	return paid_amount, received_amount


@frappe.whitelist()
def get_payment_reference_details(
	reference_doctype, reference_name, party_account_currency, party_type=None, party=None, party_account=None
):
	"""Same as ERPNext's `get_reference_details`, with support for `Donation`."""
	if reference_doctype != "Donation":
		return get_reference_details(
			reference_doctype,
			reference_name,
			party_account_currency,
			party_type,
			party,
			party_account=party_account,
		)

	frappe.has_permission(reference_doctype, "read", reference_name, throw=True)
	return get_donation_reference_details(reference_name)


def get_donation_reference_details(donation):
	total_amount = flt(frappe.db.get_value("Donation", donation, "amount"))

	return frappe._dict(
		{
			"due_date": None,
			"total_amount": total_amount,
			"outstanding_amount": total_amount,
			"exchange_rate": 1,
			"bill_no": None,
		}
	)
