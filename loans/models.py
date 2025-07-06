from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os


def borrower_id_proof_path(instance, filename):
    """Generate file path for borrower ID proof"""
    return f'borrower_documents/{instance.id}/{filename}'


class Borrower(models.Model):
    """Model for storing borrower information"""
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    id_proof = models.FileField(
        upload_to=borrower_id_proof_path,
        help_text="Upload ID proof (PDF/Image)",
        blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.phone}"

    def get_active_loans(self):
        return self.loans.filter(status='ACTIVE')

    def get_total_outstanding(self):
        """Calculate total outstanding amount for all active loans"""
        total = Decimal('0')
        for loan in self.get_active_loans():
            total += loan.get_outstanding_amount()
        return total


class Loan(models.Model):
    """Model for storing loan information"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('DEFAULTED', 'Defaulted'),
    ]

    borrower = models.ForeignKey(Borrower, on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1000'))]
    )
    interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Annual interest rate in percentage"
    )
    tenure_months = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Loan tenure in months"
    )
    start_date = models.DateField()
    installment_day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of month for installment (1-31)"
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Total amount to be repaid (Principal + Interest)"
    )
    monthly_installment = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Monthly installment amount"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.borrower.name} - ₹{self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        """Override save to calculate total_amount and monthly_installment"""
        if not self.total_amount:
            self.calculate_totals()
        super().save(*args, **kwargs)
        
        # Create installments if this is a new loan
        if not self.installments.exists():
            self.generate_installments()

    def calculate_totals(self):
        """Calculate total amount and monthly installment"""
        # Simple interest calculation: Principal + (Principal * Rate * Time)
        principal = self.amount
        rate = self.interest_rate / 100  # Convert percentage to decimal
        time_years = self.tenure_months / 12
        
        interest = principal * rate * Decimal(str(time_years))
        self.total_amount = (principal + interest).quantize(Decimal('1'))  # Round to whole number
        self.monthly_installment = (self.total_amount / self.tenure_months).quantize(Decimal('1'))  # Round to whole number

    def generate_installments(self):
        """Generate monthly installment records starting from next month"""
        # Start from next month after loan disbursement
        current_date = self.start_date + relativedelta(months=1)
        
        for i in range(1, self.tenure_months + 1):
            # Calculate due date for this installment
            due_date = current_date.replace(day=min(self.installment_day, 
                                                   self._get_last_day_of_month(current_date)))
            
            Installment.objects.create(
                loan=self,
                installment_number=i,
                due_date=due_date,
                amount_due=self.monthly_installment
            )
            
            # Move to next month
            current_date = current_date + relativedelta(months=1)

    def _get_last_day_of_month(self, date):
        """Get the last day of the month for the given date"""
        next_month = date.replace(day=28) + timedelta(days=4)
        return (next_month - timedelta(days=next_month.day)).day

    def get_outstanding_amount(self):
        """Calculate remaining amount to be paid"""
        paid_amount = self.installments.aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0')
        return self.total_amount - paid_amount

    def get_paid_amount(self):
        """Calculate total amount paid so far"""
        return self.installments.aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0')

    def get_overdue_installments(self):
        """Get overdue installments"""
        return self.installments.filter(
            status__in=['PENDING', 'PARTIAL'],
            due_date__lt=timezone.now().date()
        )

    def get_next_installment(self):
        """Get the next pending installment"""
        return self.installments.filter(status='PENDING').first()

    def is_fully_paid(self):
        """Check if loan is fully paid"""
        return self.get_outstanding_amount() <= 0

    def close_loan(self):
        """Close the loan if fully paid"""
        if self.is_fully_paid():
            self.status = 'CLOSED'
            self.save()
            return True
        return False


class Installment(models.Model):
    """Model for storing installment information"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial'),
        ('OVERDUE', 'Overdue'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.IntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, help_text="Payment notes or remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']
        unique_together = ['loan', 'installment_number']

    def __str__(self):
        return f"{self.loan.borrower.name} - Installment {self.installment_number}"

    def save(self, *args, **kwargs):
        """Override save to update status based on payment"""
        if self.amount_paid >= self.amount_due:
            self.status = 'PAID'
            if not self.payment_date:
                self.payment_date = timezone.now().date()
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        elif self.due_date < timezone.now().date():
            self.status = 'OVERDUE'
        else:
            self.status = 'PENDING'
        
        super().save(*args, **kwargs)

    def get_remaining_amount(self):
        """Get remaining amount to be paid for this installment"""
        return self.amount_due - self.amount_paid

    def is_overdue(self):
        """Check if installment is overdue"""
        return self.due_date < timezone.now().date() and self.status != 'PAID'

    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue():
            return (timezone.now().date() - self.due_date).days
        return 0


class Payment(models.Model):
    """Model for recording payment history"""
    installment = models.ForeignKey(Installment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('CASH', 'Cash'),
            ('BANK', 'Bank Transfer'),
            ('ONLINE', 'Online Payment'),
            ('CHECK', 'Check'),
        ],
        default='CASH'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"₹{self.amount} - {self.installment.loan.borrower.name}"

    def save(self, *args, **kwargs):
        """Override save to update installment"""
        super().save(*args, **kwargs)
        
        # Update installment amount_paid
        total_paid = self.installment.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        self.installment.amount_paid = total_paid
        self.installment.save()
