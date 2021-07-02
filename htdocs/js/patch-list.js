$( document ).ready(function() {
    function postPatchListData(formID) {
        console.log(formID);
        const formData = new FormData(document.getElementById(formID));

        // Get all checked checkbox elements
        $("input[type='checkbox'][name^='patch_id']").filter(':checked').each((i, elem) => {
            formData.append(elem.getAttribute('name'), 'on'); // Add checked checkBox's patch ids to form data
        });
        for(var pair of formData.entries()) {
            console.log(pair[0]+ ', '+ pair[1]);
        }
        const requestData = new URLSearchParams(formData);
        const request = new Request(document.URL, {
            method: 'POST',
            mode: 'same-origin',
            body: requestData,
            headers: {
                'X-CSRFToken': Cookies.get('csrftoken'),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        fetch(request)
            .then(data => console.log(data))
            .catch((error) => {
                console.error('Error:', error);
            });
    }

    $("#patchform-properties").submit((event) => {
        postPatchListData(event.target.id);
        event.preventDefault();
    });

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