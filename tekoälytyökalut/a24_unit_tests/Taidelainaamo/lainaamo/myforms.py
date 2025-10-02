from django import forms
from .models import Loan
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta  # pip install python-dateutil if needed
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

class LoanForm(forms.ModelForm):  # Borrowing form in detail page
    loan_start = forms.DateField(
        label="Loan starting date",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control w-50',
            'id': 'id_loan_start'
        })
    )
    loan_end = forms.DateField(
        label="Loan ending date",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control w-50',
            'id': 'id_loan_end'
        })
    )
    agreement = forms.BooleanField(
        label="I understand this is not an actual art lending site",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_agreement'
        })
    )
    class Meta:
        model = Loan
        fields = ['loan_start', 'loan_end']
            
            
    def __init__(self, *args, work=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.work = work

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("loan_start")
        end = cleaned_data.get("loan_end")
        # Server-side validations for dates
        if start and end:
            today = date.today()
            # 1. Loan starting date must be after today (not in the past or same day)
            if start <= today:
                raise ValidationError("Loan starting date must be after the current day.")
            # 2. Loan starting date cannot be more than 2 months into the future
            max_start = today + relativedelta(months=2)
            if start > max_start:
                raise ValidationError("Loan starting date cannot be more than 2 months into the future.")
            # 3 & 5. Ending date must be after starting date
            if end <= start:
                raise ValidationError("Loan ending date must be after the starting date.")
            # 4. Minimum lending period of 1 day
            min_end = start + timedelta(days=1)
            if end < min_end:
                raise ValidationError("Minimum lending period is 1 day.")
            # 4 (alternative check) & 6. Starting and ending dates cannot be the same
            if start == end:
                raise ValidationError("Starting and ending dates cannot be the same.")
            # 4. Maximum lending period of 2 months
            max_end = start + relativedelta(months=2)
            if end > max_end:
                raise ValidationError("The maximum lending period is 2 months.")
        
        # Check for active loans and related validations; only the first error will be shown.
        userLoans = Loan.objects.filter(user=self.user, work__isnull=False, return_time__isnull=True)
        duplicateLoans = [loan for loan in userLoans if loan.work == self.work]

        if userLoans.count() >= 3:
            raise ValidationError("You already have the maximum amount of active loans (3).")
        if duplicateLoans:
            raise ValidationError("You already have an active loan of this artwork.")
        if self.work and not self.work.is_available_during(start, end):
            raise ValidationError("This artwork is not available for the selected time period.")
        if not cleaned_data.get("agreement"):
            raise ValidationError("You must agree to the terms to proceed.")
            
        return cleaned_data
            
            
class ReturnForm(forms.Form):  # Return button in my_loans
    return_this_artwork = forms.CharField(
        label='',
        widget=forms.widgets.Input(
            attrs={
                'type': 'submit',
                'value': 'Return artwork',
                'id': 'returnButton',
                'name': 'returnButton',
                'class': 'btn btn-sm btn-outline-danger w-50 h-100'
            }
        ),
        required=False
    )

# Overrides Django's default login form, includes bootstrap classes for fields
class CustomLoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _(
        "Login failed: Please check your username and password."),
        'inactive': _("This account is inactive. Please contact support."),
    }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control', 
                'placeholder': field.label
                })
            

# Same for signup form
class CustomSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]
        error_messages = {
            "username": {
                "required": "Please enter a username.",
                "unique": "This username is already taken. Try something else.",
            },
            "password1": {
                "required": "Please enter a password.",
            },
            "password2": {
                "required": "Please confirm your password.",
                "password_mismatch": "Passwords do not match.",
            },
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control', 
                'placeholder': field.label
                })
