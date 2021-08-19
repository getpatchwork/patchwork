/**
 * Sends PATCH requests to update objects' properties using the REST API.
 * @param {string} url Path to the REST API endpoint.
 * @param {{field: string, value: string}} data
 *     field: Name of the property field to update.
 *     value: Value to update the property field to.
 * @param {{error: string, success: string}} updateMessage
 *     error: Message when object update failed due to errors.
 *     success: Message when object update successful.
 * @return {boolean} Whether the request was successful.
 */
async function updateProperty(url, data, updateMessage) {
    const request = new Request(url, {
        method: 'PATCH',
        mode: "same-origin",
        headers: {
            // Get csrftoken using 'js-cookie' module
            "X-CSRFToken": Cookies.get("csrftoken"),
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });

    return await fetch(request)
        .then(response => {
            let message = updateMessage.success;
            if (!response.ok) {
                response.json().then(responseObject => {
                    // Add error messages from response body to page
                    // which can be an array of errors for a given key
                    for (const [key, value] of Object.entries(responseObject)) {
                        if (Array.isArray(value)) {
                            for (const error of value) {
                                handleErrorMessage(`${key} : ${error}`);
                            }
                        } else {
                            handleErrorMessage(`${key} : ${value}`);
                        }
                    }
                });
                // Update message to be unsuccessful
                message = updateMessage.error;
            }
            handleUpdateMessage(message, response.ok);
            return response.ok
        }).catch(error => {
            handleErrorMessage(error);
            return false
        });
}

/**
 * Populates update messages for API REST requests.
 * @param {string} message Text for update message.
 * @param {boolean} success Whether the request was successful.
 */
function handleUpdateMessage(message, success) {
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
        const currentMessageCount = messages.firstChild.textContent.match('^([0-9]+)');
        // Number matched in message
        if (currentMessageCount != null) {
            const newMessageCount = parseInt(currentMessageCount) + 1;
            message = newMessageCount + message.slice(1);
        } else {
            // No number matched in message
            message = "1" + message.slice(1);
        }
    }

    // Create new message element and add to list
    const messageElem = document.createElement("li");
    messageElem.setAttribute("class", "message");
    if (success) {
        messageElem.classList.add("success");
    } else {
        messageElem.classList.add("error");
    }
    messageElem.textContent = message;
    messages.replaceChildren(...[messageElem]);
}

/**
 * Populates error messages for API REST requests.
 * @param {string} message Text for error message.
 */
function handleErrorMessage(message) {
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
    error.textContent = message;
    errorList.appendChild(error);
}

export { updateProperty };
