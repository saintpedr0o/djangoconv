document.addEventListener('DOMContentLoaded', function () {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const checkmark = dropZone.querySelector('.file-selected-checkmark');
    const form = document.getElementById('upload-form');
    const errorDiv = document.getElementById('file-error');

    let requiredFormat = '';
    const heading = document.querySelector('.convert-heading');
    if (heading) {
        const match = heading.textContent.match(/Convert your (\w+) file/i);
        if (match) {
            requiredFormat = match[1].toLowerCase();
        }
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    function clearError() {
        errorDiv.textContent = '';
        errorDiv.style.display = 'none';
    }

    function validateFile(file) {
        clearError();
        if (!file) {
            showError('Please select a file');
            return false;
        }
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.' + requiredFormat)) {
            showError(`Invalid file format. Please upload a .${requiredFormat} file`);
            return false;
        }
        return true;
    }

    let fileDialogOpen = false;

    dropZone.addEventListener('click', (e) => {
        e.preventDefault();
        if (!fileDialogOpen) {
            fileDialogOpen = true;
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', () => {
        fileDialogOpen = false;
        const file = fileInput.files[0];
        if (validateFile(file)) {
            checkmark.style.display = 'inline';
            clearError();
        } else {
            checkmark.style.display = 'none';
            fileInput.value = '';
        }
    });

    dropZone.addEventListener('keydown', (e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !fileDialogOpen) {
            e.preventDefault();
            fileDialogOpen = true;
            fileInput.click();
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            if (validateFile(file)) {
                fileInput.files = e.dataTransfer.files;
                checkmark.style.display = 'inline';
                clearError();
            } else {
                fileInput.value = '';
                checkmark.style.display = 'none';
            }
        }
    });

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const file = fileInput.files[0];
            if (!validateFile(file)) {
                return;
            }

            const formData = new FormData(form);

            fetch(window.location.href, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': '{{ csrf_token }}'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.redirect_url) {
                        form.reset();
                        window.location.href = data.redirect_url;
                    } else if (data.error) {
                        showError(data.error);
                    }
                })
                .catch(() => {
                    showError('Request error. Please try again');
                });
        });
    }
});