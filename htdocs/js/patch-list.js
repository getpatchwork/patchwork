$( document ).ready(function() {
    $("#patch-list").stickyTableHeaders();

    $("#patch-list").checkboxes("range", true);

    $("#check-all").change(function(e) {
        if(this.checked) {
            $("#patch-list > tbody").checkboxes("check");
        } else {
            $("#patch-list > tbody").checkboxes("uncheck");
        }
        e.preventDefault();
    });
});
