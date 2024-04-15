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

function displaySimpleToast(displayText) {
    let myToastEl = document.getElementById('simple-toast');
    let myToast = bootstrap.Toast.getOrCreateInstance(myToastEl);
    let toastText = document.getElementById('toast-text');
    toastText.innerHTML = displayText;
    myToast.show();
}