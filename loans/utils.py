from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import datetime, timedelta
from .models import Loan, Installment, Payment


def get_dashboard_stats():
    """Get dashboard statistics"""
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # Total amount disbursed
    total_disbursed = Loan.objects.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Total amount receivable (outstanding from all active loans)
    total_receivable = Decimal('0')
    for loan in Loan.objects.filter(status='ACTIVE'):
        total_receivable += loan.get_outstanding_amount()
    
    # Expected income for current month
    current_month_installments = Installment.objects.filter(
        due_date__month=current_month,
        due_date__year=current_year,
        loan__status='ACTIVE'
    )
    
    expected_income = current_month_installments.aggregate(
        total=Sum('amount_due')
    )['total'] or Decimal('0')
    
    received_this_month = current_month_installments.aggregate(
        total=Sum('amount_paid')
    )['total'] or Decimal('0')
    
    pending_this_month = expected_income - received_this_month
    
    # Overdue installments
    overdue_installments = Installment.objects.filter(
        due_date__lt=today,
        status__in=['PENDING', 'PARTIAL'],
        loan__status='ACTIVE'
    )
    
    overdue_count = overdue_installments.count()
    overdue_amount = Decimal('0')
    for installment in overdue_installments:
        overdue_amount += installment.get_remaining_amount()
    
    # Active loans count
    active_loans_count = Loan.objects.filter(status='ACTIVE').count()
    
    # Total borrowers
    total_borrowers = Loan.objects.values('borrower').distinct().count()
    
    return {
        'total_disbursed': total_disbursed,
        'total_receivable': total_receivable,
        'expected_income': expected_income,
        'received_this_month': received_this_month,
        'pending_this_month': pending_this_month,
        'overdue_count': overdue_count,
        'overdue_amount': overdue_amount,
        'active_loans_count': active_loans_count,
        'total_borrowers': total_borrowers,
    }


def get_upcoming_dues(days=7):
    """Get installments due in the next specified days"""
    today = timezone.now().date()
    future_date = today + timedelta(days=days)
    
    return Installment.objects.filter(
        due_date__gte=today,
        due_date__lte=future_date,
        status='PENDING',
        loan__status='ACTIVE'
    ).select_related('loan', 'loan__borrower').order_by('due_date')


def get_recent_payments(limit=10):
    """Get recent payments"""
    return Payment.objects.select_related(
        'installment', 'installment__loan', 'installment__loan__borrower'
    ).order_by('-created_at')[:limit]


def calculate_loan_details(principal, interest_rate, tenure_months):
    """Calculate loan details for given parameters"""
    principal = Decimal(str(principal))
    rate = Decimal(str(interest_rate)) / 100  # Convert percentage to decimal
    time_years = Decimal(str(tenure_months)) / 12
    
    # Simple interest calculation
    interest = principal * rate * time_years
    total_amount = (principal + interest).quantize(Decimal('1'))  # Round to whole number
    monthly_installment = (total_amount / tenure_months).quantize(Decimal('1'))  # Round to whole number
    
    return {
        'principal': principal.quantize(Decimal('1')),
        'interest': interest.quantize(Decimal('1')),
        'total_amount': total_amount,
        'monthly_installment': monthly_installment
    }


def get_loan_performance_data():
    """Get data for loan performance charts"""
    # Monthly disbursement data for the last 12 months
    today = timezone.now().date()
    twelve_months_ago = today - timedelta(days=365)
    
    monthly_data = []
    for i in range(12):
        month_start = twelve_months_ago + timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        disbursed = Loan.objects.filter(
            start_date__gte=month_start,
            start_date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        collected = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'disbursed': float(disbursed),
            'collected': float(collected)
        })
    
    return monthly_data


def get_borrower_loan_summary(borrower):
    """Get loan summary for a specific borrower"""
    loans = borrower.loans.all()
    
    total_borrowed = loans.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_paid = Decimal('0')
    total_outstanding = Decimal('0')
    
    for loan in loans:
        total_paid += loan.get_paid_amount()
        if loan.status == 'ACTIVE':
            total_outstanding += loan.get_outstanding_amount()
    
    overdue_installments = Installment.objects.filter(
        loan__borrower=borrower,
        due_date__lt=timezone.now().date(),
        status__in=['PENDING', 'PARTIAL']
    ).count()
    
    return {
        'total_borrowed': total_borrowed,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'overdue_count': overdue_installments,
        'active_loans': loans.filter(status='ACTIVE').count(),
        'closed_loans': loans.filter(status='CLOSED').count(),
    }


def update_overdue_statuses():
    """Update installment statuses for overdue items"""
    today = timezone.now().date()
    
    # Update overdue installments
    overdue_installments = Installment.objects.filter(
        due_date__lt=today,
        status='PENDING'
    )
    
    updated_count = overdue_installments.update(status='OVERDUE')
    return updated_count


def get_monthly_collection_report(year, month):
    """Get collection report for a specific month"""
    installments = Installment.objects.filter(
        due_date__year=year,
        due_date__month=month,
        loan__status='ACTIVE'
    ).select_related('loan', 'loan__borrower')
    
    total_due = installments.aggregate(total=Sum('amount_due'))['total'] or Decimal('0')
    total_collected = installments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    collection_rate = (total_collected / total_due * 100) if total_due > 0 else 0
    
    return {
        'total_due': total_due,
        'total_collected': total_collected,
        'collection_rate': collection_rate,
        'installments': installments
    }


def validate_file_upload(file):
    """Validate uploaded files"""
    if not file:
        return True, None
    
    # Check file size (5MB limit)
    if file.size > 5 * 1024 * 1024:
        return False, "File size cannot exceed 5MB"
    
    # Check file extension
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    file_ext = file.name.lower().split('.')[-1]
    if f'.{file_ext}' not in allowed_extensions:
        return False, "Only PDF, JPG, JPEG, and PNG files are allowed"
    
    return True, None


def format_currency(amount):
    """Format amount as Indian currency"""
    if amount is None:
        return "₹0"
    return f"₹{amount:,.2f}"


def get_loan_status_distribution():
    """Get distribution of loans by status"""
    return Loan.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('status')
