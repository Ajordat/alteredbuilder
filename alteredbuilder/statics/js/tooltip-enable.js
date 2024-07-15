
let tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]:not([data-bs-disable="true"])');
[...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
