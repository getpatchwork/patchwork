$( document ).ready(function() {
    async function postPropertyChange(property, patchId, propertyValue, project) {
        const formData = getFormData(property, patchId, propertyValue, project);
        const requestData = new URLSearchParams(formData);
        const request = new Request(document.URL, {
            method: 'POST',
            mode: 'same-origin',
            headers: {
                'X-CSRFToken': Cookies.get('csrftoken'),
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: requestData,
        });

        fetch(request)
            .then(response => response.json())
            .then(data => console.log(data))
            .catch((error) => {
                console.error('Error:', error);
        });
    }

    // Returns form data object for POST request for property change
    function getFormData(property, patchId, propertyValue, project) {
        const formData = new FormData();

        // Static form data fields and values
        formData.append('form', 'patchlistform');
        formData.append('action', 'update');
        formData.append('archived', '*');
        formData.append('bundle_name', '');

        // Dynamic form data fields and values
        formData.append('project', project);
        formData.append(patchId, 'on');
        if (property === 'delegate') {
            formData.append('delegate', propertyValue);
            formData.append('state', '*');
        } else if (property === 'state') {
            formData.append('delegate', '*');
            formData.append('state', propertyValue);
        }
        return formData;
    }

    function getPatchProperties(target) {
        return {
            'patchId': "patch_id:" + target.parentElement.parentElement.dataset.patchId,
            'propertyValue': target.value,
            'project': $("input[name='project']").val(),
        }
    }

    $(".change-property-delegate").change((event) => {
        const property = 'delegate';
        const { patchId, propertyValue, project } = getPatchProperties(event.target);
        postPropertyChange(property, patchId, propertyValue, project);
    });

    $(".change-property-state").change((event) => {
        const property = 'state';
        const { patchId, propertyValue, project } = getPatchProperties(event.target);
        postPropertyChange(property, patchId, propertyValue, project);
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