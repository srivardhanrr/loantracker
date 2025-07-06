from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Loan, Installment, Borrower, Payment
from ..utils import get_dashboard_stats, get_upcoming_dues, get_recent_payments


@login_required
def dashboard_view(request):
    """Dashboard view with key statistics and recent activities"""
    
    # Get dashboard statistics
    stats = get_dashboard_stats()
    
    # Get upcoming dues (next 7 days)
    upcoming_dues = get_upcoming_dues(days=7)
    
    # Get recent payments
    recent_payments = get_recent_payments(limit=5)
    
    # Get overdue installments
    overdue_installments = Installment.objects.filter(
        due_date__lt=timezone.now().date(),
        status__in=['PENDING', 'PARTIAL'],
        loan__status='ACTIVE'
    ).select_related('loan', 'loan__borrower').order_by('due_date')[:10]
    
    context = {
        'stats': stats,
        'upcoming_dues': upcoming_dues,
        'recent_payments': recent_payments,
        'overdue_installments': overdue_installments,
        'title': 'Dashboard'
    }
    
    return render(request, 'loans/dashboard.html', context)


def home_view(request):
    """Redirect to dashboard"""
    return redirect('dashboard')
