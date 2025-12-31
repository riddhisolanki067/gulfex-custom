import frappe
from frappe.desk.reportview import get_form_params,is_virtual_doctype,get_controller,execute,compress

ALLOWED_DOCTYPES = {"Sales Invoice", "Sales Order"}

CHILD_TABLE = "Job Details"
CHILD_FIELD = "job"

@frappe.whitelist()
@frappe.read_only()
def custom_get():
	args = get_form_params()
	doctype = args.doctype

	if doctype not in ALLOWED_DOCTYPES:
		if is_virtual_doctype(doctype):
			controller = get_controller(doctype)
			return compress(controller.get_list(args))
		return compress(execute(**args), args=args)

	custom_job = None
	filters = args.get("filters") or []

	new_filters = []

	for f in filters:
		if isinstance(f, (list, tuple)) and len(f) == 4:
			_, fieldname, operator, value = f

			if fieldname == "custom_jobs":
				custom_job = value
				continue

		new_filters.append(f)

	args["filters"] = new_filters

	# default query
	data = execute(**args)

	# child-table filtering
	if custom_job and data:
		names = [d["name"] for d in data]

		valid = frappe.db.sql(f"""
			SELECT DISTINCT parent
			FROM `tab{CHILD_TABLE}`
			WHERE parent IN %(names)s
			AND `{CHILD_FIELD}` = %(job)s
		""", {
			"names": tuple(names),
			"job": custom_job
		}, as_dict=True)

		valid_names = {r.parent for r in valid}
		data = [d for d in data if d["name"] in valid_names]

	return compress(data, args=args)

@frappe.whitelist()
@frappe.read_only()
def custom_get_list():
	args = get_form_params()
	doctype = args.doctype

	if doctype not in ALLOWED_DOCTYPES:
		if is_virtual_doctype(doctype):
			controller = get_controller(doctype)
			return controller.get_list(args)
		return execute(**args)

	custom_job = getattr(frappe.local, "custom_jobs", None)

	data = execute(**args)

	if custom_job and data:
		names = [d["name"] for d in data]

		valid = frappe.db.sql(f"""
			SELECT DISTINCT parent
			FROM `tab{CHILD_TABLE}`
			WHERE parent IN %(names)s
			AND `{CHILD_FIELD}` = %(job)s
		""", {
			"names": tuple(names),
			"job": custom_job
		}, as_dict=True)

		valid_names = {r.parent for r in valid}
		data = [d for d in data if d["name"] in valid_names]

	return data

    

frappe.desk.reportview.get = custom_get
frappe.desk.reportview.get_list = custom_get_list