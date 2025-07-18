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

   const formatAliases = {
    jpeg: ['jpeg', 'jpg', 'jpe', 'jfif'],
    tiff: ['tiff', 'tif'],
    bmp: ['bmp', 'bmpf', 'dib'],
    html: ['html', 'htm']
    };

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
        if (file.size > MAX_SIZE_BYTES) {
            showError(`Max file size is ${(MAX_SIZE_BYTES / (1024 ** 3)).toFixed(1)} GB`);
            return false;
        }
        const fileName = file.name.toLowerCase();
        const validExtensions = formatAliases[requiredFormat] || [requiredFormat];
        const isValid = validExtensions.some(ext => fileName.endsWith('.' + ext));
        if (!isValid) {
            showError(`Invalid file format. Please upload a file with extension: ${validExtensions.map(e => '.' + e).join(', ')}`);
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
                        if (typeof data.error === 'object') {
                            const firstField = Object.keys(data.error)[0];
                            if (firstField && data.error[firstField].length > 0) {
                                showError(data.error[firstField][0]);
                            } else {
                                showError('Unknown error');
                            }
                        } else {
                            showError(data.error);
                        }
                    }
                })
                .catch(() => {
                    showError('Request error. Please try again');
                });
        });
    }
});
