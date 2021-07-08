$( document ).ready(function() {
    function toggle_div(link_id, headers_id, label_show, label_hide) {
        const link = document.getElementById(link_id)
        const headers = document.getElementById(headers_id)

        const hidden = headers.style['display'] == 'none';

        if (hidden) {
            link.innerHTML = label_hide || 'hide';
            headers.style['display'] = 'block';
        } else {
            link.innerHTML = label_show || 'show';
            headers.style['display'] = 'none';
        }
    }

    // Click listener to show/hide headers
    document.getElementById("toggle-patch-headers").addEventListener("click", function() {
        toggle_div("toggle-patch-headers", "patch-headers");
    });

    // Click listener to expand/collapse series
    document.getElementById("toggle-patch-series").addEventListener("click", function() {
        toggle_div("toggle-patch-series", "patch-series", "expand", "collapse");
    });

    // Click listener to show/hide related patches
    document.getElementById("toggle-related").addEventListener("click", function() {
        toggle_div("toggle-related", "related");
    });

    // Click listener to show/hide related patches from different projects
    document.getElementById("toggle-related-outside").addEventListener("click", function() {
        toggle_div("toggle-related-outside", "related-outside", "show from other projects");
    });

});