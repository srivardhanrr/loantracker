from django import forms
from django.core.exceptions import ValidationError
from .models import Borrower, Loan, Payment
from decimal import Decimal
import os


class BorrowerForm(forms.ModelForm):
    """Form for creating and editing borrowers"""
    
    class Meta:
        model = Borrower
        fields = ['name', 'phone', 'email', 'address', 'id_proof']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address (optional)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete address'
            }),
            'id_proof': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }

    def clean_id_proof(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('id_proof')
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 5MB")
            
            # Check file extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                raise ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed")
        
        return file

    def clean_phone(self):
        """Validate phone number"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            digits_only = ''.join(filter(str.isdigit, phone))
            if len(digits_only) < 10:
                raise ValidationError("Phone number must be at least 10 digits")
        return phone


class LoanForm(forms.ModelForm):
    """Form for creating and editing loans"""
    
    class Meta:
        model = Loan
        fields = ['borrower', 'amount', 'interest_rate', 'tenure_months', 'start_date', 'installment_day']
        widgets = {
            'borrower': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter loan amount',
                'min': '1000',
                'step': '0.01'
            }),
            'interest_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter annual interest rate (%)',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'tenure_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tenure in months',
                'min': '1',
                'max': '60'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'installment_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Day of month (1-31)',
                'min': '1',
                'max': '31'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values
        if not self.instance.pk:
            self.fields['interest_rate'].initial = 24.00
            self.fields['tenure_months'].initial = 12
            self.fields['installment_day'].initial = 5

    def clean_amount(self):
        """Validate loan amount"""
        amount = self.cleaned_data.get('amount')
        if amount and amount < 1000:
            raise ValidationError("Minimum loan amount is ₹1,000")
        return amount

    def clean_interest_rate(self):
        """Validate interest rate"""
        rate = self.cleaned_data.get('interest_rate')
        if rate and (rate < 0 or rate > 100):
            raise ValidationError("Interest rate must be between 0% and 100%")
        return rate

    def clean_tenure_months(self):
        """Validate tenure"""
        tenure = self.cleaned_data.get('tenure_months')
        if tenure and (tenure < 1 or tenure > 60):
            raise ValidationError("Tenure must be between 1 and 60 months")
        return tenure

    def clean_installment_day(self):
        """Validate installment day"""
        day = self.cleaned_data.get('installment_day')
        if day and (day < 1 or day > 31):
            raise ValidationError("Installment day must be between 1 and 31")
        return day


class PaymentForm(forms.ModelForm):
    """Form for recording payments"""
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'payment_method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment amount',
                'min': '0.01',
                'step': '0.01'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter payment notes (optional)'
            })
        }

    def __init__(self, *args, installment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.installment = installment
        
        if installment:
            # Set maximum amount based on remaining installment amount
            remaining = installment.get_remaining_amount()
            self.fields['amount'].widget.attrs['max'] = str(remaining)
            self.fields['amount'].initial = remaining

    def clean_amount(self):
        """Validate payment amount"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Payment amount must be greater than 0")
        
        if self.installment and amount:
            remaining = self.installment.get_remaining_amount()
            if amount > remaining:
                raise ValidationError(f"Payment amount cannot exceed remaining amount: ₹{remaining}")
        
        return amount


class LoanSearchForm(forms.Form):
    """Form for searching and filtering loans"""
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('DEFAULTED', 'Defaulted'),
    ]
    
    borrower_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by borrower name'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    start_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    start_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class BorrowerSearchForm(forms.Form):
    """Form for searching borrowers"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or phone'
        })
    )
