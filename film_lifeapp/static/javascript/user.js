function changeBackground() {
    const element = document.getElementById('show_password');
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');


    if (element.classList.contains('bg1')) {
        password1.setAttribute('type', 'text');
        password2.setAttribute('type', 'text');

        element.classList.remove('bg1');
        element.classList.add('bg2');
    } else {
        password1.setAttribute('type', 'password');
        password2.setAttribute('type', 'password');
        element.classList.remove('bg2');
        element.classList.add('bg1');
    }
}

