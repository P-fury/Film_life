document.addEventListener('DOMContentLoaded', function () {
    const typeOfWorkdaySelect = document.getElementById('type_of_day');
    const percentOfDailyInput = document.getElementById('percent_of_daily');
    const labelForPercent = document.querySelector('label[for="percent_of_daily"]')



    function toggleLabelAndInputDisplay(display){
        if (labelForPercent){
            labelForPercent.style.display = display
        }
        if (percentOfDailyInput){
            percentOfDailyInput.style.display = display;
            if (display === 'block'){
                percentOfDailyInput.setAttribute('required','required');
            } else {
                percentOfDailyInput.removeAttribute('required');
            }
        }
    }

    typeOfWorkdaySelect.addEventListener('change', function () {
        if (typeOfWorkdaySelect.value === 'other'){
            toggleLabelAndInputDisplay('block');
        } else {
            toggleLabelAndInputDisplay('none');
        }
    });
    if(typeOfWorkdaySelect.value === 'other'){
        toggleLabelAndInputDisplay('block');
    }else{
        toggleLabelAndInputDisplay('none');
    }
});
