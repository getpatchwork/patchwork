/**
 * Sends PATCH requests to update objects' properties using the REST API.
 * @param {string} url Path to the REST API endpoint.
 * @param {{field: string, value: string}} data
 *     field: Name of the property field to update.
 *     value: Value to update the property field to.
 * @param {{none: string, some: string}} updateMessage
 *     none: Message when object update failed due to errors.
 *     some: Message when object update successful.
 */
async function updateProperty(url, data, updateMessage) {
    const request = new Request(url, {
        method: 'PATCH',
        mode: "same-origin",
        headers: {
            "X-CSRFToken": Cookies.get("csrftoken"),
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });

    return await fetch(request)
        .then(response => {
            let message = updateMessage.some;
            let success = true;
            if (!response.ok) {
                response.text().then(text => {
                    const responseObject = JSON.parse(text);
                    // Add error messages from response to page
                    for (const [key,value] of Object.entries(responseObject)) {
                        if (Array.isArray(value)) {
                            for (const error of value) {
                                handleErrorMessages(key + ": " + error);
                            }
                        } else {
                            handleErrorMessages(key + ": " + value);
                        }
                    }
                });
                // Update message to be unsuccessful
                message = updateMessage.none;
                success = false;
            }
            handleUpdateMessages(message, success);
            return response.ok
        });
}

/**
 * Populates update messages for API REST requests.
 * @param {string} messageContent Text for update message.
 */
function handleUpdateMessages(messageContent, success) {
    // Replace error and failure update messages with success update message
    const errorContainer = document.getElementById("errors");
    let messages = document.getElementsByClassName("messages")[0];
    if (success && errorContainer.firstChild != null) {
        messages.replaceChildren();
        errorContainer.replaceChildren();
    } else if (!success) {
        messages.replaceChildren();
    }

    // Increment counter of consecutive success update messages
    if (messages.firstChild != null) {
        const newMessageCount = parseInt(messages.firstChild.textContent.slice(0,1)) + 1
        messageContent = newMessageCount + messageContent.slice(1);
    }

    // Create new message element and add to list
    const message = document.createElement("li");
    message.setAttribute("class", "message");
    if (success) {
        message.classList.add("class", "success");
    } else {
        message.classList.add("class", "error");
    }
    message.textContent = messageContent;
    messages.replaceChildren(...[message]);
}

/**
 * Populates error messages for API REST requests.
 * @param {string} errorMessage Text for error message.
 */
function handleErrorMessages(errorMessage) {
    let errorContainer = document.getElementById("errors");
    let errorHeader = document.getElementById("errors-header");
    let errorList = document.getElementsByClassName("error-list")[0];

    // Create errors list and error header if container contents removed
    if (errorList == null) {
        errorHeader = document.createElement("p");
        errorList = document.createElement("ul");
        errorHeader.setAttribute("id", "errors-header")
        errorHeader.textContent = "The following errors were encountered while making updates:";
        errorList.setAttribute("class", "error-list");
        errorContainer.appendChild(errorHeader);
        errorContainer.appendChild(errorList);
    }

    const error = document.createElement("li");
    error.textContent = errorMessage;
    errorList.appendChild(error);
}

export { updateProperty };
