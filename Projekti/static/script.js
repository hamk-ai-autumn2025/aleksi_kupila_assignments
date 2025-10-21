const suggest_form = document.getElementById('suggest_form');
const execute_form = document.getElementById('execute_form');
const analysis_form = document.getElementById('analysis_form');
const responseDiv = document.getElementById('response');
const spinner = document.getElementById('spinner');

const forms = [suggest_form, execute_form, analysis_form];
console.log("Binding forms...");
document.addEventListener('submit', async (e) => {
  const form = e.target;
  if (!['suggest_form', 'execute_form', 'analysis_form'].includes(form.id)) return;

  e.preventDefault();
  spinner.style.display = 'block';

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
    spinner.style.display = 'none';
  }
});