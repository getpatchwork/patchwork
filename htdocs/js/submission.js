$( document ).ready(function() {
    function toggleDiv(link_id, headers_id, label_show, label_hide) {
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
        toggleDiv("toggle-patch-headers", "patch-headers");
    });

    // Click listener to expand/collapse series
    document.getElementById("toggle-patch-series").addEventListener("click", function() {
        toggleDiv("toggle-patch-series", "patch-series", "expand", "collapse");
    });

    // Click listener to show/hide related patches
    let related = document.getElementById("toggle-related");
    if (related) {
        document.getElementById("toggle-related").addEventListener("click", function() {
            toggleDiv("toggle-related", "related");
        });
    }

    // Click listener to show/hide related patches from different projects
    let relatedOutside = document.getElementById("toggle-related-outside");
    if (relatedOutside) {
        document.getElementById("toggle-related-outside").addEventListener("click", function() {
            toggleDiv("toggle-related-outside", "related-outside", "show from other projects");
        });
    }
});