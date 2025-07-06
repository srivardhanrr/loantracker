from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from ..models import Installment, Payment
from ..forms import PaymentForm


def installment_pay_view(request, installment_id):
    """Record payment for an installment"""
    installment = get_object_or_404(
        Installment.objects.select_related('loan', 'loan__borrower'), 
        id=installment_id
    )
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, installment=installment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.installment = installment
            payment.save()
            
            # Check if loan is fully paid and close it
            if installment.loan.is_fully_paid():
                installment.loan.close_loan()
                messages.success(
                    request, 
                    f'Payment recorded! Loan for "{installment.loan.borrower.name}" is now fully paid and closed.'
                )
            else:
                messages.success(request, 'Payment recorded successfully!')
            
            return redirect('loan_detail', loan_id=installment.loan.id)
    else:
        form = PaymentForm(installment=installment)
    
    context = {
        'form': form,
        'installment': installment,
        'remaining_amount': installment.get_remaining_amount(),
        'title': f'Record Payment: {installment.loan.borrower.name}'
    }
    
    return render(request, 'loans/payment_form.html', context)


def payment_history_view(request, installment_id):
    """View payment history for an installment"""
    installment = get_object_or_404(
        Installment.objects.select_related('loan', 'loan__borrower'), 
        id=installment_id
    )
    payments = installment.payments.all().order_by('-payment_date')
    
    context = {
        'installment': installment,
        'payments': payments,
        'title': f'Payment History: {installment.loan.borrower.name}'
    }
    
    return render(request, 'loans/payment_history.html', context)


@require_http_methods(["POST"])
def mark_installment_paid_ajax(request, installment_id):
    """AJAX endpoint to mark installment as fully paid"""
    try:
        installment = get_object_or_404(Installment, id=installment_id)
        remaining = installment.get_remaining_amount()
        
        if remaining <= 0:
            return JsonResponse({'error': 'Installment is already paid'})
        
        # Create payment record
        payment = Payment.objects.create(
            installment=installment,
            amount=remaining,
            payment_date=timezone.now().date(),
            payment_method='CASH',
            notes='Quick payment via dashboard'
        )
        
        # Check if loan is fully paid
        loan_closed = False
        if installment.loan.is_fully_paid():
            installment.loan.close_loan()
            loan_closed = True
        
        return JsonResponse({
            'success': True,
            'message': 'Payment recorded successfully!',
            'loan_closed': loan_closed,
            'remaining_amount': str(installment.get_remaining_amount())
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)})


def overdue_installments_view(request):
    """View all overdue installments"""
    overdue_installments = Installment.objects.filter(
        due_date__lt=timezone.now().date(),
        status__in=['PENDING', 'PARTIAL'],
        loan__status='ACTIVE'
    ).select_related('loan', 'loan__borrower').order_by('due_date')
    
    total_overdue_amount = sum(
        installment.get_remaining_amount() for installment in overdue_installments
    )
    
    context = {
        'overdue_installments': overdue_installments,
        'total_overdue_amount': total_overdue_amount,
        'title': 'Overdue Installments'
    }
    
    return render(request, 'loans/overdue_installments.html', context)


def upcoming_dues_view(request):
    """View upcoming dues for the next 30 days"""
    today = timezone.now().date()
    future_date = today + timezone.timedelta(days=30)
    
    upcoming_installments = Installment.objects.filter(
        due_date__gte=today,
        due_date__lte=future_date,
        status='PENDING',
        loan__status='ACTIVE'
    ).select_related('loan', 'loan__borrower').order_by('due_date')
    
    total_upcoming_amount = sum(
        installment.amount_due for installment in upcoming_installments
    )
    
    context = {
        'upcoming_installments': upcoming_installments,
        'total_upcoming_amount': total_upcoming_amount,
        'title': 'Upcoming Dues (Next 30 Days)'
    }
    
    return render(request, 'loans/upcoming_dues.html', context)


def all_payments_view(request):
    """View all payments with filters"""
    payments = Payment.objects.select_related(
        'installment', 'installment__loan', 'installment__loan__borrower'
    ).order_by('-payment_date')
    
    # Add filtering logic here if needed
    borrower_filter = request.GET.get('borrower')
    if borrower_filter:
        payments = payments.filter(
            installment__loan__borrower__name__icontains=borrower_filter
        )
    
    date_from = request.GET.get('date_from')
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(payments, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'borrower_filter': borrower_filter,
        'date_from': date_from,
        'date_to': date_to,
        'title': 'All Payments'
    }
    
    return render(request, 'loans/all_payments.html', context)
