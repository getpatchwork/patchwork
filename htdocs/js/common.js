
function confirm_delete(type, name)
{
	return confirm("Are you sure you want to delete the " + type +
			" '" + name + "'?");
}

function select_all(obj)
{
	var value = obj.checked;
	var form = obj.form;

	select_all_checkbox = obj;

	for (var i = 0; i < form.elements.length; i++ ) {
		var element = form.elements[i];
		if (element.type != 'checkbox') {
			continue;
		}
		if (element.name.substring(0, 9) != 'patch_id:') {
			continue;
		}
		element.checked = value;
	}
}
