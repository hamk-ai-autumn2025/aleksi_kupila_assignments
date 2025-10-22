document.addEventListener('DOMContentLoaded', () => {
  
    const suggest_form = document.getElementById('suggest_form');
    const execute_form = document.getElementById('execute_form');
    const analysis_form = document.getElementById('analysis_form');
    const save_form = document.getElementById('save_form');
    const responseDiv = document.getElementById('response');

  const forms = [suggest_form, execute_form, analysis_form];
  console.log("Binding forms...");

  function display_spinner(form, formData, e, s_spinner, e_spinner, a_spinner){
    if (form.id == "suggest_form"){
        s_spinner.style.display = 'block';
    }
    if (form.id == "execute_form"){
      const action = e.submitter?.value;
      if (action == "run"){
        e_spinner.style.display = 'block';
      }
      formData.append('action', action);
    }
    if (form.id == "analysis_form"){
        a_spinner.style.display = 'block';
    }
  }
  function disable_spinner(spinners){
    for (let spinner of spinners){
      if (spinner){
        spinner.style.display = 'none';
      }
    }
  }
  document.addEventListener('submit', async (e) => {
    s_spinner  = document.getElementById('suggest_spinner');
    e_spinner = document.getElementById('execute_spinner');
    a_spinner = document.getElementById('analysis_spinner');
    const form = e.target;
    if (!['suggest_form', 'execute_form', 'analysis_form', 'save_form'].includes(form.id)) return;

    e.preventDefault();
    const formData = new FormData(form)
    display_spinner(form, formData, e, s_spinner, e_spinner, a_spinner)

    try {
      const res = await fetch(form.action, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      responseDiv.innerHTML = data.html;  
    } catch (err) {
      responseDiv.textContent = 'Error: ' + err.message;
    } finally {
        disable_spinner([s_spinner, e_spinner, a_spinner])
    }
  });
});