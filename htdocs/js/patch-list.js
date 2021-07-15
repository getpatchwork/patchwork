$( document ).ready(function() {
    async function postPropertyChange(property, patchId, propertyValue) {
        const url = "/api/patches/" + patchId + "/";
        const data = {};
        data[property] = propertyValue;
        const request = new Request(url, {
            method: "PATCH",
            mode: "same-origin",
            headers: {
                "X-CSRFToken": Cookies.get("csrftoken"),
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });

        await fetch(request)
            .then(response => {
                if (!response.ok) {
                    response.text().then(text => {
                        handleUpdateMessage("No patches updated");
                        handleErrorMessage(JSON.parse(text).detail);
                    });
                } else {
                    handleUpdateMessage("1 patch updated");
                }
            });
    }

    function getPatchProperties(target, property) {
        const selectedOption = target.options[target.selectedIndex];
        return {
            "patchId": target.parentElement.parentElement.dataset.patchId,
            "propertyValue": (property === "state") ? selectedOption.text
                            : (selectedOption.value === "*") ? null : selectedOption.value,
        }
    }

    function handleUpdateMessage(messageContent) {
        let messages = document.getElementById("messages");
        if (messages == null) {
            messages = document.createElement("div");
            messages.setAttribute("id", "messages");
        }
        let message = document.createElement("div");
        message.setAttribute("class", "message");
        message.textContent = messageContent;
        messages.appendChild(message);
        if (messages) $(messages).insertAfter("nav");
    }

    function handleErrorMessage(errorMessage) {
        let container = document.getElementById("main-content");
        let errorHeader = document.createElement("p");
        let errorList = document.createElement("ul");
        let error = document.createElement("li");
        errorHeader.textContent = "The following error was encountered while updating patches:";
        errorList.setAttribute("class", "errorlist");
        error.textContent = errorMessage;
        errorList.appendChild(error);
        container.prepend(errorList);
        container.prepend(errorHeader);
    }

    $(".change-property-delegate").change((event) => {
        const property = "delegate";
        const { patchId, propertyValue } = getPatchProperties(event.target, property);
        postPropertyChange(property, patchId, propertyValue);
    });

    $(".change-property-state").change((event) => {
        const property = "state";
        const { patchId, propertyValue } = getPatchProperties(event.target, property);
        postPropertyChange(property, patchId, propertyValue);
    });

    $("#patchlist").stickyTableHeaders();

    $("#check-all").change(function(e) {
        if(this.checked) {
            $("#patchlist > tbody").checkboxes("check");
        } else {
            $("#patchlist > tbody").checkboxes("uncheck");
        }
        e.preventDefault();
    });
});