document.addEventListener('DOMContentLoaded', () => {
  
    const suggest_form = document.getElementById('suggest_form');
    const execute_form = document.getElementById('execute_form');
    const analysis_form = document.getElementById('analysis_form');
    const save_form = document.getElementById('save_form');
    const responseDiv = document.getElementById('response');

  const forms = [suggest_form, execute_form, analysis_form];
  console.log("Binding forms...");

  document.addEventListener('submit', async (e) => {
    const suggest_spinner = document.getElementById('suggest_spinner');
    const execute_spinner = document.getElementById('execute_spinner');
    const analysis_spinner = document.getElementById('analysis_spinner');
    const form = e.target;
    if (!['suggest_form', 'execute_form', 'analysis_form', 'save_form'].includes(form.id)) return;

    e.preventDefault();
    
    if (form.id == "suggest_form"){
        suggest_spinner.style.display = 'block';
    }
    if (form.id == "execute_form"){
        execute_spinner.style.display = 'block';
    }
    if (form.id == "analysis_form"){
        analysis_spinner.style.display = 'block';
    }

    try {
      const res = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form)
      });
      const data = await res.json();
      responseDiv.innerHTML = data.html;  
    } catch (err) {
      responseDiv.textContent = 'Error: ' + err.message;
    } finally {
        if (suggest_spinner){
            suggest_spinner.style.display = 'none';
        }
        if (execute_spinner){
            execute_spinner.style.display = 'none';
        }
        if (analysis_spinner){
            analysis_spinner.style.display = 'none';
        }
    }
  });
});