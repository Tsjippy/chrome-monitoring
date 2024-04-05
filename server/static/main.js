console.log('main.js loaded');

document.addEventListener('click', (ev) =>{
    let target  = ev.target;

    if(target.matches('.alert')){
        target.remove();
    }

    if(target.matches('.details')){
        if(target.textContent == '+'){
            target.textContent  = '-';
            target.closest('tr').nextElementSibling.classList.remove('hidden');
        }else{
            target.textContent  = '+';
            target.closest('tr').nextElementSibling.classList.add('hidden');
        }
    }
})

