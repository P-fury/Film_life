
const selector = document.getElementById('type_of_day')
const  percent_of_daily = document.getElementById('percent_of_daily')
selector.addEventListener('change',function (e){
    if(selector.value === 'other'){
        percent_of_daily.style.display = 'block';
    }else{
        percent_of_daily.style.display = 'none';
    }
})