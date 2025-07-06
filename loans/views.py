from .dashboard import dashboard_view, home_view
from .borrowers import (
    borrower_list_view, borrower_detail_view, borrower_add_view, 
    borrower_edit_view, borrower_delete_view
)
from .loans import (
    loan_list_view, loan_detail_view, loan_add_view, loan_edit_view,
    loan_close_view, calculate_loan_ajax, installment_schedule_view
)
from .installments import (
    installment_pay_view, payment_history_view, mark_installment_paid_ajax,
    overdue_installments_view, upcoming_dues_view, all_payments_view
)
