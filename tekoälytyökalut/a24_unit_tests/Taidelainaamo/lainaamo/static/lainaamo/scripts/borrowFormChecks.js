function validateForm() {
    let errors = [];
    const today = new Date();
    const startDate = new Date(document.getElementById('id_loan_start').value);
    const endDate = new Date(document.getElementById('id_loan_end').value);
    const agreementChecked = document.getElementById("id_agreement").checked;
    const errorField = document.getElementById('id_errorField');

    // Validate the starting date.
    const twoMonthsFromToday = new Date(today);
    twoMonthsFromToday.setMonth(twoMonthsFromToday.getMonth() + 2);

    if (startDate < today) {
        errors.push('The starting date cannot be in the past.');
    }
    if (startDate > twoMonthsFromToday) {
        errors.push('The starting date cannot be more than 2 months into the future.');
    }

    // Validate the ending date.
    const oneDayAfterStart = new Date(startDate);
    oneDayAfterStart.setDate(startDate.getDate() + 1);
    const twoMonthsFromStart = new Date(startDate);
    twoMonthsFromStart.setMonth(startDate.getMonth() + 2);

    if (endDate < oneDayAfterStart) {
        errors.push('Minimum lending period is 1 day.');
    }
    if (endDate > twoMonthsFromStart) {
        errors.push('Maximum lending period is 2 months.');
    }

    // Check if the agreement checkbox is ticked.
    if (!agreementChecked) {
        errors.push('Please agree to the terms.');
    }

    // If there are errors, show them; otherwise, consider validation successful.
    // If errors are found and server errors are already showing, hide server errors
    if (errors.length > 0) {
        const errorHtml = `<p class="text-danger">${errors.join("<br>")}</p>`;
        const serverErrors = document.getElementById("server-errors"); 
        if (serverErrors){
            serverErrors.style.display = "none"; 
        }
        errorField.innerHTML = errorHtml;
        console.log("JS fail");
        return false;
    } else {
        console.log("JS pass");
        return true;
    }
}

