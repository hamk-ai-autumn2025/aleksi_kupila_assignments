const suggest_form = document.getElementById('suggest_form');
const execute_form = document.getElementById('execute_form');
const analysis_form = document.getElementById('analysis_form');
const responseDiv = document.getElementById('response');
const spinner = document.getElementById('spinner');

const forms = [suggest_form, execute_form, analysis_form];

forms.forEach(form => {
    if (form) {
        form.addEventListener('submit', async (e) =>{

            spinner.style.display = 'block';
            try {
                const formData = new FormData(form);
                const res = await fetch(form.action, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                responseDiv.innerHTML = data.html; // insert the rendered HTML
            } catch (err) {
                responseDiv.textContent = 'Error: ' + err.message;
            } finally {
                spinner.style.display = 'none';
            }
        });
    }
});