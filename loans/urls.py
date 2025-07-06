from django.urls import path, include
from .views.dashboard import dashboard_view, home_view
from .views.borrowers import (
    borrower_list_view, borrower_detail_view, borrower_add_view, 
    borrower_edit_view, borrower_delete_view
)
from .views.loans import (
    loan_list_view, loan_detail_view, loan_add_view, loan_edit_view,
    loan_close_view, calculate_loan_ajax, installment_schedule_view
)
from .views.installments import (
    installment_pay_view, payment_history_view, mark_installment_paid_ajax,
    overdue_installments_view, upcoming_dues_view, all_payments_view
)
from .views.auth import CustomLoginView, logout_view

urlpatterns = [
    # Authentication
    path('auth/login/', CustomLoginView.as_view(), name='login'),
    path('auth/logout/', logout_view, name='logout'),
    
    # Dashboard
    path('', home_view, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Borrowers
    path('borrowers/', borrower_list_view, name='borrower_list'),
    path('borrowers/add/', borrower_add_view, name='borrower_add'),
    path('borrowers/<int:borrower_id>/', borrower_detail_view, name='borrower_detail'),
    path('borrowers/<int:borrower_id>/edit/', borrower_edit_view, name='borrower_edit'),
    path('borrowers/<int:borrower_id>/delete/', borrower_delete_view, name='borrower_delete'),
    
    # Loans
    path('loans/', loan_list_view, name='loan_list'),
    path('loans/add/', loan_add_view, name='loan_add'),
    path('loans/<int:loan_id>/', loan_detail_view, name='loan_detail'),
    path('loans/<int:loan_id>/edit/', loan_edit_view, name='loan_edit'),
    path('loans/<int:loan_id>/close/', loan_close_view, name='loan_close'),
    path('loans/<int:loan_id>/schedule/', installment_schedule_view, name='installment_schedule'),
    
    # Installments and Payments
    path('installments/<int:installment_id>/pay/', installment_pay_view, name='installment_pay'),
    path('installments/<int:installment_id>/history/', payment_history_view, name='payment_history'),
    path('installments/overdue/', overdue_installments_view, name='overdue_installments'),
    path('installments/upcoming/', upcoming_dues_view, name='upcoming_dues'),
    path('payments/', all_payments_view, name='all_payments'),
    
    # AJAX endpoints
    path('ajax/calculate-loan/', calculate_loan_ajax, name='calculate_loan_ajax'),
    path('ajax/mark-paid/<int:installment_id>/', mark_installment_paid_ajax, name='mark_installment_paid_ajax'),
]
