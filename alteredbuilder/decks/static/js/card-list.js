let exampleModal = document.getElementById('add-card-modal');

if (exampleModal) {
  exampleModal.addEventListener('show.bs.modal', event => {
    // Button that triggered the modal
    let button = event.relatedTarget;
    let cardNameElement = document.getElementById("modal-card-name");
    let cardReferenceElement = document.getElementById("modal-card-reference");

    cardNameElement.value = button.getAttribute('data-bs-name');
    cardReferenceElement.value = button.getAttribute('data-bs-reference');
  });
}