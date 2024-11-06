console.log('main.js loaded');

document.addEventListener('click', (ev) =>{
    let target  = ev.target;

    if(target.matches('.alert')){
        target.remove();
    }else if(target.matches('.details')){
        if(target.textContent == '+'){
            target.textContent  = '-';
            target.closest('tr').nextElementSibling.classList.remove('hidden');
        }else{
            target.textContent  = '+';
            target.closest('tr').nextElementSibling.classList.add('hidden');
        }
    }else if(target.dataset.year != undefined){
        document.querySelector(`div[data-year="${target.dataset.year}"]`).classList.toggle('hidden');
    }else if(target.dataset.month != undefined){
        document.querySelector(`div[data-month="${target.dataset.month}"]`).classList.toggle('hidden');
    }else if(target.dataset.user != undefined){
        document.querySelector(`div[data-user="${target.dataset.user}"]`).classList.toggle('hidden');
    }
})

