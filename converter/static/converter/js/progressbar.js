document.addEventListener("DOMContentLoaded", function () {
    const downloadBtn = document.getElementById('download-btn');
    const homeBtn = document.getElementById('home-btn');
    const checkmark = document.querySelector('.progress-checkmark');
    const errormark = document.querySelector('.progress-error');
    const heading = document.querySelector('.convert-heading');

    if (downloadBtn && downloadUrl) {
        downloadBtn.addEventListener('click', function () {
            window.location.href = downloadUrl;
        });
    }

    if (homeBtn && errorUrl) {
        homeBtn.addEventListener('click', function () {
            window.location.href = errorUrl;
        });
    }

    function customResult(resultElement, result) {
        const content = document.getElementById('progress-bar-message').innerText.trim();

        if (content === 'Success!') {
            checkmark.style.display = 'inline';
            errormark.style.display = 'none';
            downloadBtn.style.display = 'inline-block';
            homeBtn.style.display = 'none';
        } else {
            errormark.style.display = 'inline';
            checkmark.style.display = 'none';
            downloadBtn.style.display = 'none';
            homeBtn.style.display = 'inline-block';

            if (heading) {
                heading.textContent = 'Conversion failed';
            }
        }
    }

    CeleryProgressBar.initProgressBar(progressUrl, {
        onResult: customResult
    });
});

