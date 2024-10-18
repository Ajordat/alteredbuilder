
document.querySelectorAll('.profile-pic-choice').forEach(function(pic) {
    pic.addEventListener('click', function() {
        // Get the clicked picture's value and image URL
        const selectedPicName = this.getAttribute('data-pic-name');
        const selectedPicUrl = `/static/img/avatars/${selectedPicName}`;

        // Update the displayed image and name
        document.getElementById('selected-profile-pic').src = selectedPicUrl;
        // document.getElementById('selected-profile-name').textContent = selectedPicName;

        // Mark the corresponding radio button as checked
        document.querySelector(`input[value="${selectedPicName}"]`).checked = true;
    });
});