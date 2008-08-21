

function ac_keyup(input)
{
	input.autocomplete.keyup();
}

function AutoComplete(input)
{
	this.input = input;
	this.div = null;
	this.last_value = '';

	input.autocomplete = this;

	this.hide = function()
	{
		if (this.div) {
			this.div.style.display = 'none';
			this.div = null;
		}

	}

	this.show = function()
	{
		if (!this.div) {
			this.div = 

	this.keyup = function()
	{
		value = input.value;

		if (value == this.last_value)
			return;

		if (value.length < 3) {
			this.hide();
		}


}

