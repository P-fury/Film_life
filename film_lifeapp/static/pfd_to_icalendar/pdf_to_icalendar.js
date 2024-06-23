         document.addEventListener('DOMContentLoaded', function () {
            const realFileBtn = document.getElementById('pdf_file');
            const customBtn = document.getElementById('custom-button');
            const customText = document.getElementById('custom-text');

            if (realFileBtn && customBtn && customText) {
                customBtn.addEventListener("click", function () {
                    event.preventDefault();
                    realFileBtn.click();
                });

                realFileBtn.addEventListener("change", function () {
                    if (realFileBtn.files.length > 0) {
                        customText.innerHTML = realFileBtn.files[0].name;
                    } else {
                        customText.innerHTML = 'No file chosen.';
                    }
                });
            } else {
                console.error("Elements with the specified IDs were not found in the DOM.");
            }
        });