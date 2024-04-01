document.addEventListener('DOMContentLoaded', function () {
    const typeOfWorkdaySelect = document.getElementById('id_type_of_workday');
    const percentOfDailyInput = document.querySelector('#id_percent_of_daily').parentElement;

    typeOfWorkdaySelect.addEventListener('change', function () {
        if (typeOfWorkdaySelect.value === 'other') {
            percentOfDailyInput.style.display = 'block';
        } else {
            percentOfDailyInput.style.display = 'none';
        }
    });
    if (typeOfWorkdaySelect.value !== 'other') {
        percentOfDailyInput.style.display = 'none';
    } else if (typeOfWorkdaySelect.value === 'other') {
        percentOfDailyInput.style.display = 'block';
    }

});
