$( document ).ready(function() {
    $('#patchlist').stickyTableHeaders();

    $('#check-all').change(function(e) {
        if(this.checked) {
            $('#patchlist > tbody').checkboxes('check');
        } else {
            $('#patchlist > tbody').checkboxes('uncheck');
        }
        e.preventDefault();
    });
});