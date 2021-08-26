import { updateProperty } from "./rest.js";

$( document ).ready(function() {
    const patchMeta = document.getElementById("patch-meta");
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

    $("button[class^='comment-action']").click((event) => {
        const submissionType = patchMeta.dataset.submissionType;
        const submissionId = patchMeta.dataset.submissionId;
        const commentId = event.target.parentElement.dataset.commentId;
        const url = `/api/${submissionType}/${submissionId}/comments/${commentId}/`;
        const data = {'addressed': event.target.value} ;
        const updateMessage = {
            'error': "No comments updated",
            'success': "1 comment(s) updated",
        };
        updateProperty(url, data, updateMessage).then(isSuccess => {
            if (isSuccess) {
                // The API won't accept anything but true or false, so we
                // always hide the -action-required element
                $("div[class='comment-status-bar-action-required'][data-comment-id='"+commentId+"']").addClass("hidden");

                if (event.target.value === "true") {
                    $("div[class^='comment-status-bar-addressed'][data-comment-id='"+commentId+"']").removeClass("hidden");
                    $("div[class^='comment-status-bar-unaddressed'][data-comment-id='"+commentId+"']").addClass("hidden");
                } else if (event.target.value === "false") {
                    $("div[class^='comment-status-bar-addressed'][data-comment-id='"+commentId+"']").addClass("hidden");
                    $("div[class^='comment-status-bar-unaddressed'][data-comment-id='"+commentId+"']").removeClass("hidden");
                }
            }
        })
    });

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
