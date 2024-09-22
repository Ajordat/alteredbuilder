
var notificationDropdown = document.getElementById('notificationList');


function getDropdownItem(message) {
    let notificationItem = document.createElement('li');
    notificationItem.classList.add("dropdown-item", "notification-item", "text-muted", "disabled");
    notificationItem.innerText = message;
    return notificationItem;
}

function clearNotifications() {
    let notificationItems = notificationDropdown.getElementsByClassName("notification-item");
    for (let i = notificationItems.length - 1; i >= 0; i--) {
        notificationItems[i].remove();
    }
}

function setNotificationMessage(message) {
    clearNotifications(notificationDropdown);

    document.getElementById("notificationsDivider").insertAdjacentElement("afterend", getDropdownItem(message));
}

function fetchNotifications() {

    setNotificationMessage(gettext('Loading...'));

    let currentLanguage = window.location.pathname.slice(0, 3);
    let url =  `${currentLanguage}/notifications/fetch/`;

    fetch(url, {
        method: "GET",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        }
    })
    .then(response => response.json())
    .then(payload => {
        if ("error" in payload) {
            let displayMessage;

            if (payload.error.code == 401) {
                displayMessage = gettext("Authentication required");
            } else {
                displayMessage = gettext("Error loading notifications");
            }
            setNotificationMessage(displayMessage);
        } else {
            clearNotifications();

            notifications = payload.data.notifications;
            if (notifications.length > 0) {
                // If there are notifications, render each of them
                notifications.forEach(notification => {
                    // <li> element will contain the notification
                    let notificationItem = document.createElement('li');
                    notificationItem.classList.add("p-0", "dropdown-item", "notification-item");
                    // <a> element has to be clickable and needs to go to the notification detail view
                    let anchor = document.createElement("a");
                    anchor.href = `${currentLanguage}/notifications/${notification.id}/`;
                    anchor.classList.add("dropdown-item", "d-block");
                    // <span> will contain the notification text
                    let span = document.createElement("span");
    
                    if (!notification.read) {
                        // If it's a new notification, create a red dot in a <span> and add 2 whitespaces
                        // to the message text to avoid overlap
                        notificationItem.classList.add("new-notification");
                        let redDotSpan = document.createElement("span");
                        redDotSpan.classList.add("position-absolute", "p-1", "bg-danger", "border", "border-light", "rounded-circle");
                        anchor.appendChild(redDotSpan);
                        span.innerHTML = "&nbsp;&nbsp;";
                    }
                    // Insert the notification text into the <span>
                    span.innerHTML += notification.message;
                    anchor.appendChild(span);
                    // Break the line with <br> and create a <small> element with the date
                    anchor.appendChild(document.createElement("br"));
                    let small = document.createElement("small");
                    small.classList.add("text-muted");
                    small.innerText = notification.timestamp;
                    anchor.appendChild(small);
                    notificationItem.appendChild(anchor);
                    notificationDropdown.appendChild(notificationItem);
                });
            } else {                
                setNotificationMessage(gettext('No new notifications'));
            }
        }
    });
}

document.getElementById("notificationDropdown").addEventListener("click", event => {
    if (event.currentTarget.classList.contains("show")) {
        fetchNotifications();
    }
});