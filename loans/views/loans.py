from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..models import Loan, Borrower, Installment
from ..forms import LoanForm, LoanSearchForm
from ..utils import calculate_loan_details


@login_required
def loan_list_view(request):
    """List all loans with search and filter functionality"""
    search_form = LoanSearchForm(request.GET)
    loans = Loan.objects.select_related('borrower').all()
    
    # Apply filters
    if search_form.is_valid():
        borrower_name = search_form.cleaned_data.get('borrower_name')
        status = search_form.cleaned_data.get('status')
        start_date_from = search_form.cleaned_data.get('start_date_from')
        start_date_to = search_form.cleaned_data.get('start_date_to')
        
        if borrower_name:
            loans = loans.filter(borrower__name__icontains=borrower_name)
        
        if status:
            loans = loans.filter(status=status)
        
        if start_date_from:
            loans = loans.filter(start_date__gte=start_date_from)
        
        if start_date_to:
            loans = loans.filter(start_date__lte=start_date_to)
    
    # Pagination
    paginator = Paginator(loans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'title': 'Loans'
    }
    
    return render(request, 'loans/loan_list.html', context)


@login_required
def loan_detail_view(request, loan_id):
    """View loan details with installment schedule"""
    loan = get_object_or_404(Loan.objects.select_related('borrower'), id=loan_id)
    installments = loan.installments.all().order_by('due_date')
    
    # Calculate loan statistics
    total_paid = loan.get_paid_amount()
    outstanding = loan.get_outstanding_amount()
    overdue_installments = loan.get_overdue_installments()
    next_installment = loan.get_next_installment()
    
    context = {
        'loan': loan,
        'installments': installments,
        'total_paid': total_paid,
        'outstanding': outstanding,
        'overdue_installments': overdue_installments,
        'next_installment': next_installment,
        'title': f'Loan: {loan.borrower.name}'
    }
    
    return render(request, 'loans/loan_detail.html', context)


@login_required
def loan_add_view(request):
    """Add new loan"""
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            loan = form.save()
            messages.success(request, f'Loan for "{loan.borrower.name}" created successfully!')
            return redirect('loan_detail', loan_id=loan.id)
    else:
        form = LoanForm()
    
    context = {
        'form': form,
        'title': 'Create New Loan'
    }
    
    return render(request, 'loans/loan_form.html', context)


@login_required
def loan_edit_view(request, loan_id):
    """Edit existing loan (only if no payments made)"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    # Check if any payments have been made
    if loan.get_paid_amount() > 0:
        messages.error(request, 'Cannot edit loan after payments have been made!')
        return redirect('loan_detail', loan_id=loan.id)
    
    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loan)
        if form.is_valid():
            # Delete existing installments and recreate them
            loan.installments.all().delete()
            loan = form.save()
            messages.success(request, f'Loan for "{loan.borrower.name}" updated successfully!')
            return redirect('loan_detail', loan_id=loan.id)
    else:
        form = LoanForm(instance=loan)
    
    context = {
        'form': form,
        'loan': loan,
        'title': f'Edit Loan: {loan.borrower.name}'
    }
    
    return render(request, 'loans/loan_form.html', context)


@login_required
def loan_close_view(request, loan_id):
    """Close a loan"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    if request.method == 'POST':
        if loan.close_loan():
            messages.success(request, f'Loan for "{loan.borrower.name}" closed successfully!')
        else:
            messages.error(request, 'Cannot close loan. Outstanding amount remains.')
        return redirect('loan_detail', loan_id=loan.id)
    
    context = {
        'loan': loan,
        'outstanding': loan.get_outstanding_amount(),
        'title': f'Close Loan: {loan.borrower.name}'
    }
    
    return render(request, 'loans/loan_confirm_close.html', context)


@login_required
def loan_delete_view(request, loan_id):
    """Delete a loan (only if no payments made)"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    # Check if any payments have been made
    if loan.get_paid_amount() > 0:
        messages.error(request, 'Cannot delete loan after payments have been made!')
        return redirect('loan_detail', loan_id=loan.id)
    
    if request.method == 'POST':
        borrower_name = loan.borrower.name
        loan_amount = loan.amount
        
        # Delete the loan (this will also delete related installments due to CASCADE)
        loan.delete()
        
        messages.success(request, f'Loan of ₹{loan_amount} for "{borrower_name}" deleted successfully!')
        return redirect('loan_list')
    
    context = {
        'loan': loan,
        'title': f'Delete Loan: {loan.borrower.name}'
    }
    
    return render(request, 'loans/loan_confirm_delete.html', context)


@login_required
@require_http_methods(["GET"])
def calculate_loan_ajax(request):
    """AJAX endpoint to calculate loan details"""
    try:
        amount = float(request.GET.get('amount', 0))
        interest_rate = float(request.GET.get('interest_rate', 0))
        tenure_months = int(request.GET.get('tenure_months', 1))
        
        if amount <= 0 or tenure_months <= 0:
            return JsonResponse({'error': 'Invalid input values'})
        
        details = calculate_loan_details(amount, interest_rate, tenure_months)
        
        return JsonResponse({
            'success': True,
            'principal': str(details['principal']),
            'interest': str(details['interest']),
            'total_amount': str(details['total_amount']),
            'monthly_installment': str(details['monthly_installment'])
        })
    
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid input parameters'})


@login_required
def installment_schedule_view(request, loan_id):
    """View detailed installment schedule for a loan"""
    loan = get_object_or_404(Loan.objects.select_related('borrower'), id=loan_id)
    installments = loan.installments.all().order_by('installment_number')
    
    context = {
        'loan': loan,
        'installments': installments,
        'title': f'Installment Schedule: {loan.borrower.name}'
    }
    
    return render(request, 'loans/installment_schedule.html', context)
