# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from erpnext.tests.utils import ERPNextTestSuite

from non_profit.non_profit.doctype.member.member import get_member_customer_group
from non_profit.non_profit.doctype.membership.test_membership import setup_membership


class TestMember(ERPNextTestSuite):
	def setUp(self):
		self.plan = setup_membership()
		frappe.db.set_single_value("Non Profit Settings", "member_customer_group", "_Test Customer Group 1")

	def make_member(self, name="_Test Member Customer Group"):
		return frappe.get_doc(
			{
				"doctype": "Member",
				"member_name": name,
				"membership_type": self.plan.name,
				"email_id": "_test_member_customer_group@example.com",
			}
		).insert()

	def test_customer_created_in_member_customer_group(self):
		member = self.make_member()
		member.make_customer_and_link()

		self.assertTrue(member.customer)
		self.assertEqual(frappe.db.get_value("Customer", member.customer, "customer_group"), "_Test Customer Group 1")

	def test_customer_is_not_created_twice(self):
		member = self.make_member()
		member.make_customer_and_link()
		first_customer = member.customer

		member.make_customer_and_link()

		self.assertEqual(member.customer, first_customer)
		self.assertEqual(frappe.db.count("Customer", {"customer_name": member.member_name}), 1)

	def test_falls_back_to_selling_settings(self):
		frappe.db.set_single_value("Non Profit Settings", "member_customer_group", None)
		frappe.db.set_single_value("Selling Settings", "customer_group", "_Test Customer Group")

		self.assertEqual(get_member_customer_group(), "_Test Customer Group")

	def test_group_node_is_not_used(self):
		group_node = frappe.db.get_value("Customer Group", {"is_group": 1}, "name")
		frappe.db.set_single_value("Non Profit Settings", "member_customer_group", None)
		frappe.db.set_single_value("Selling Settings", "customer_group", group_node)

		self.assertRaises(frappe.ValidationError, get_member_customer_group)

	def test_settings_refuse_group_node(self):
		settings = frappe.get_doc("Non Profit Settings")
		settings.member_customer_group = frappe.db.get_value("Customer Group", {"is_group": 1}, "name")

		self.assertRaises(frappe.ValidationError, settings.save)
