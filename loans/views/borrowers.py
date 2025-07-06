from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import Borrower
from ..forms import BorrowerForm, BorrowerSearchForm
from ..utils import get_borrower_loan_summary


def borrower_list_view(request):
    """List all borrowers with search functionality"""
    search_form = BorrowerSearchForm(request.GET)
    borrowers = Borrower.objects.all()
    
    # Apply search filter
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        if search_query:
            borrowers = borrowers.filter(
                Q(name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query)
            )
    
    # Pagination
    paginator = Paginator(borrowers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'title': 'Borrowers'
    }
    
    return render(request, 'loans/borrower_list.html', context)


def borrower_detail_view(request, borrower_id):
    """View borrower details with loan history"""
    borrower = get_object_or_404(Borrower, id=borrower_id)
    loans = borrower.loans.all().order_by('-start_date')
    
    # Get borrower summary
    summary = get_borrower_loan_summary(borrower)
    
    context = {
        'borrower': borrower,
        'loans': loans,
        'summary': summary,
        'title': f'Borrower: {borrower.name}'
    }
    
    return render(request, 'loans/borrower_detail.html', context)


def borrower_add_view(request):
    """Add new borrower"""
    if request.method == 'POST':
        form = BorrowerForm(request.POST, request.FILES)
        if form.is_valid():
            borrower = form.save()
            messages.success(request, f'Borrower "{borrower.name}" added successfully!')
            return redirect('borrower_detail', borrower_id=borrower.id)
    else:
        form = BorrowerForm()
    
    context = {
        'form': form,
        'title': 'Add New Borrower'
    }
    
    return render(request, 'loans/borrower_form.html', context)


def borrower_edit_view(request, borrower_id):
    """Edit existing borrower"""
    borrower = get_object_or_404(Borrower, id=borrower_id)
    
    if request.method == 'POST':
        form = BorrowerForm(request.POST, request.FILES, instance=borrower)
        if form.is_valid():
            borrower = form.save()
            messages.success(request, f'Borrower "{borrower.name}" updated successfully!')
            return redirect('borrower_detail', borrower_id=borrower.id)
    else:
        form = BorrowerForm(instance=borrower)
    
    context = {
        'form': form,
        'borrower': borrower,
        'title': f'Edit Borrower: {borrower.name}'
    }
    
    return render(request, 'loans/borrower_form.html', context)


def borrower_delete_view(request, borrower_id):
    """Delete borrower (only if no active loans)"""
    borrower = get_object_or_404(Borrower, id=borrower_id)
    
    # Check if borrower has active loans
    active_loans = borrower.loans.filter(status='ACTIVE')
    if active_loans.exists():
        messages.error(request, 'Cannot delete borrower with active loans!')
        return redirect('borrower_detail', borrower_id=borrower.id)
    
    if request.method == 'POST':
        borrower_name = borrower.name
        borrower.delete()
        messages.success(request, f'Borrower "{borrower_name}" deleted successfully!')
        return redirect('borrower_list')
    
    context = {
        'borrower': borrower,
        'title': f'Delete Borrower: {borrower.name}'
    }
    
    return render(request, 'loans/borrower_confirm_delete.html', context)
