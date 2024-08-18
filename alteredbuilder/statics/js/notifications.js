
function getDropdownItem(message) {
    return `<li class="dropdown-item text-muted disabled">${message}</li>`;
}

function fetchNotifications() {
    let notificationDropdown = document.getElementById('notificationList');

    notificationDropdown.innerHTML = getDropdownItem('Loading...');
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
    .then(data => {
        notificationDropdown.innerHTML = '';
        notifications = data.data.notifications;
        if (notifications.length > 0) {
            notifications.forEach(notification => {
                let notificationItem = document.createElement('li');
                let anchor = document.createElement("a");
                anchor.href = `${currentLanguage}/notifications/${notification.id}/`;
                anchor.classList.add("dropdown-item", "d-block");
                if (!notification.read) {
                    notificationItem.classList.add("new-notification");
                    let span = document.createElement("span");
                    span.classList.add("position-absolute", "p-1", "bg-danger", "border", "border-light", "rounded-circle");
                    anchor.appendChild(span);
                }
                let span = document.createElement("span");
                span.innerHTML = "&nbsp;&nbsp;" + notification.message;
                anchor.appendChild(span);
                anchor.appendChild(document.createElement("br"));
                let small = document.createElement("small");
                small.classList.add("text-muted");
                small.innerText = notification.timestamp;
                anchor.appendChild(small);
                notificationItem.appendChild(anchor);
                notificationDropdown.appendChild(notificationItem);
            });
        } else {
            notificationDropdown.innerHTML = getDropdownItem('No new notifications');
        }

    })
    .catch(error => {
        console.log(error);
        notificationDropdown.innerHTML = getDropdownItem('Error loading notifications');
    });
}

document.getElementById("notificationDropdown").addEventListener("click", event => {
    if (event.currentTarget.classList.contains("show")) {
        fetchNotifications();
    }
});