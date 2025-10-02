function formValidation(){
    const start = new Date(document.getElementById('id_loan_start').value);
    const end = new Date(document.getElementById('id_loan_end').value);
    let errorField = document.getElementById('id_errorField');
    let errors = [];
    if (start >= end) {
        errors.push("Please check the fields")
        errorField.innerHTML=`<p class="text-danger">${errors.join("<br>")}</p>`;
        console.log("JS false");
        return false;
    }
    console.log("JS true");
    return true;
}