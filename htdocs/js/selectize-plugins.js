Selectize.define('enter_key_submit', function (options) {
    var self = this;

    this.onKeyDown = (function (e) {
        var original = self.onKeyDown;

        return function (e) {
            var wasOpened = this.isOpen;
            original.apply(this, arguments);

            if (e.keyCode === 13 &&
                (this.$control_input.val() != '' || !wasOpened))
                self.trigger('submit');
        };
    })();
});

// Submit form on shift+enter or ctrl+enter
Selectize.define('mod_enter_key_submit', function (options) {
    var self = this;

    this.onKeyDown = (function (e) {
        var original = self.onKeyDown;

        return function (e) {
            var wasOpened = this.isOpen;

            if (e.keyCode === 13 && (e.shiftKey || e.ctrlKey)) {
                self.trigger('submit');
                return;
            }

            original.apply(this, arguments);
        };
    })();
});

// Focus search input after item from dropdown is selected for multiselects
Selectize.define('mod_focus_input_after_select', function (options) {
    let prevSelect = this.onOptionSelect.bind(this);

    this.onOptionSelect = e => {
        // delegateTarget - div with dropdown
        // delegateTarget.parentElement - input div created by selectize
        //  ^ contains selected items and actual <input> control
        e.delegateTarget.parentElement.getElementsByTagName('input')[0].focus();
        prevSelect(e);
    };
});
