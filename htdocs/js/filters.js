
var available_filters = new Array();

function Filter(param, input_html, fn)
{
	this.param = param;
	this.input_html = input_html;
	this.fn = fn;
}

function add_filter_change(input)
{
	index = input.selectedIndex - 1;

	if (index < 0 || index >= available_filters.length)
		return;

	filter = available_filters[index];

	value_element = document.getElementById("addfiltervalue");
	value_element.innerHTML = filter.input_html;
}

function filter_form_submit(form)
{
	filter_index = form.filtertype.selectedIndex - 1;

	if (filter_index < 0 || filter_index >= available_filters.length)
		return false;

	filter = available_filters[filter_index];

	value = filter.fn(form);
	updated = false;

	form = document.forms.filterparams;

	for (x = 0; x < form.elements.length; x++) {
		if (form.elements[x].name == filter.param) {
			form.elements[x].value = value;
			updated = true;
		}
	}

	if (!updated && value) {
		form.innerHTML = form.innerHTML +
			'<input type="hidden" name="' + filter.param +
			'" value="' + value + '"/>';
	}

	form.submit();

	return false;
}


var submitter_input_prev_value = '';

function submitter_input_change(input)
{
	value = input.value;

	if (value.length < 3)
		return;

	if (value == submitter_input_prev_value)
		return;

	div = document.getElementById('submitter_complete');
	div.innerHTML = value;
	div.style.display = 'block';
	div.style.position = 'relative';
	div.style.top = '4em';
	div.style.width = '15em';
	div.style.background = '#f0f0f0';
	div.style.padding = '0.2em';
	div.style.border = 'thin solid red';
}
