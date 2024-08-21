/**
 * Retrieve the value of the specified cookie, or null if it doesn't exist.
 * 
 * @param {string} name The name of the cookie.
 * @returns {string} The cookie's value or null.
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


/**
 * Display a message on a simple toast. The toast element must exist on the HTML beforehand.
 * 
 * @param {string} displayText The message to display. 
 */
function displaySimpleToast(displayText) {
    let myToastEl = document.getElementById('simple-toast');
    let myToast = bootstrap.Toast.getOrCreateInstance(myToastEl);
    let toastText = document.getElementById('toast-text');
    toastText.innerHTML = displayText;
    myToast.show();
}


/**
 * Send an AJAX request.
 * 
 * @param {string} url The URL to send the request to.
 * @param {string} body The body of the request.
 * @returns The Promise of the request.
 */
function ajaxRequest(url, body = {}) {
    let csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    return fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify(body)
    })
}