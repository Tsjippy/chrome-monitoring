console.log('main.js loaded');

document.addEventListener('click', async (ev) =>{
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
        document.querySelectorAll(`div[data-year="${target.dataset.year}"]`).forEach(el=>el.classList.toggle('hidden'));
    }else if(target.dataset.month != undefined){
        document.querySelectorAll(`div[data-month="${target.dataset.month}"]`).forEach(el=>el.classList.toggle('hidden'));
    }else if(target.dataset.user != undefined){
        document.querySelectorAll(`div[data-user="${target.dataset.user}"]`).forEach(el=>el.classList.toggle('hidden'));
    }else if(target.type == 'submit'){
        let row = target.closest('tr')

        let formData    = new FormData()

        row.querySelectorAll('input').forEach(input => formData.append(input.name, input.value));

        const response = await fetch("",
        {
            body: formData,
            method: "post"
        });

        const html  = await response.text();

        // Show the updated users limits again
        let shownUsers  = [];
        document.querySelectorAll('.user-wrapper:not(.hidden)').forEach(el=>shownUsers.push(el.dataset.user))

        document.querySelector("html").innerHTML = html;

        shownUsers.forEach(user => {
            document.querySelector(`.user-wrapper[data-user='${user}']`).classList.remove('hidden');
        });
    }
})

