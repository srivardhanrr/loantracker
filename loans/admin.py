from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Borrower, Loan, Installment, Payment


@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'active_loans_count', 'total_outstanding', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'phone', 'email', 'address')
        }),
        ('Documents', {
            'fields': ('id_proof',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def active_loans_count(self, obj):
        count = obj.get_active_loans().count()
        if count > 0:
            url = reverse('admin:loans_loan_changelist') + f'?borrower__id__exact={obj.id}&status__exact=ACTIVE'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    active_loans_count.short_description = 'Active Loans'
    
    def total_outstanding(self, obj):
        amount = obj.get_total_outstanding()
        if amount > 0:
            return format_html('<strong>₹{:,.2f}</strong>', amount)
        return '₹0'
    total_outstanding.short_description = 'Outstanding Amount'


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0
    readonly_fields = ['installment_number', 'due_date', 'amount_due', 'status', 'get_remaining']
    fields = ['installment_number', 'due_date', 'amount_due', 'amount_paid', 'status', 'get_remaining']
    
    def get_remaining(self, obj):
        return f'₹{obj.get_remaining_amount():,.2f}'
    get_remaining.short_description = 'Remaining'
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return obj and obj.amount_paid == 0 if obj else False


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = [
        'borrower_name', 'amount', 'interest_rate', 'tenure_months', 
        'start_date', 'status', 'paid_amount', 'outstanding_amount'
    ]
    list_filter = ['status', 'start_date', 'interest_rate']
    search_fields = ['borrower__name', 'borrower__phone']
    readonly_fields = ['total_amount', 'monthly_installment', 'created_at', 'updated_at']
    inlines = [InstallmentInline]
    
    fieldsets = (
        ('Borrower', {
            'fields': ('borrower',)
        }),
        ('Loan Details', {
            'fields': ('amount', 'interest_rate', 'tenure_months', 'start_date', 'installment_day')
        }),
        ('Calculated Fields', {
            'fields': ('total_amount', 'monthly_installment'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def borrower_name(self, obj):
        url = reverse('admin:loans_borrower_change', args=[obj.borrower.id])
        return format_html('<a href="{}">{}</a>', url, obj.borrower.name)
    borrower_name.short_description = 'Borrower'
    borrower_name.admin_order_field = 'borrower__name'
    
    def paid_amount(self, obj):
        amount = obj.get_paid_amount()
        return format_html('<span style="color: green;">₹{:,.2f}</span>', amount)
    paid_amount.short_description = 'Paid'
    
    def outstanding_amount(self, obj):
        amount = obj.get_outstanding_amount()
        color = 'red' if amount > 0 else 'green'
        return format_html('<span style="color: {};">₹{:,.2f}</span>', color, amount)
    outstanding_amount.short_description = 'Outstanding'
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.get_paid_amount() > 0:
            return self.readonly_fields + ['amount', 'interest_rate', 'tenure_months', 'start_date', 'installment_day']
        return self.readonly_fields


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['amount', 'payment_date', 'payment_method', 'notes', 'created_at']


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = [
        'loan_borrower', 'installment_number', 'due_date', 'amount_due', 
        'amount_paid', 'remaining_amount', 'status', 'days_overdue_display'
    ]
    list_filter = ['status', 'due_date', 'loan__status']
    search_fields = ['loan__borrower__name', 'loan__borrower__phone']
    readonly_fields = ['loan', 'installment_number', 'due_date', 'amount_due', 'created_at', 'updated_at']
    inlines = [PaymentInline]
    
    fieldsets = (
        ('Installment Details', {
            'fields': ('loan', 'installment_number', 'due_date', 'amount_due')
        }),
        ('Payment Information', {
            'fields': ('amount_paid', 'payment_date', 'status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def loan_borrower(self, obj):
        url = reverse('admin:loans_loan_change', args=[obj.loan.id])
        return format_html('<a href="{}">{}</a>', url, obj.loan.borrower.name)
    loan_borrower.short_description = 'Borrower'
    loan_borrower.admin_order_field = 'loan__borrower__name'
    
    def remaining_amount(self, obj):
        amount = obj.get_remaining_amount()
        color = 'red' if amount > 0 else 'green'
        return format_html('<span style="color: {};">₹{:,.2f}</span>', color, amount)
    remaining_amount.short_description = 'Remaining'
    
    def days_overdue_display(self, obj):
        days = obj.days_overdue()
        if days > 0:
            return format_html('<span style="color: red;">{} days</span>', days)
        return '-'
    days_overdue_display.short_description = 'Overdue'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'installment_borrower', 'installment_number', 'amount', 
        'payment_date', 'payment_method', 'created_at'
    ]
    list_filter = ['payment_method', 'payment_date', 'created_at']
    search_fields = ['installment__loan__borrower__name', 'installment__loan__borrower__phone']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('installment', 'amount', 'payment_date', 'payment_method')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def installment_borrower(self, obj):
        return obj.installment.loan.borrower.name
    installment_borrower.short_description = 'Borrower'
    installment_borrower.admin_order_field = 'installment__loan__borrower__name'
    
    def installment_number(self, obj):
        return f"#{obj.installment.installment_number}"
    installment_number.short_description = 'Installment'
    installment_number.admin_order_field = 'installment__installment_number'


# Customize admin site header and title
admin.site.site_header = "Gopal Enterprises Administration"
admin.site.site_title = "Gopal Enterprises Admin"
admin.site.index_title = "Welcome to Gopal Enterprises Loan Management"
