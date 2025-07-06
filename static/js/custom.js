// Custom JavaScript for Loan Tracker

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide messages after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.classList.contains('show')) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) closeBtn.click();
            }
        }, 5000);
    });
    
    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
    
    // Confirm delete actions
    const deleteLinks = document.querySelectorAll('a[href*="delete"]');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
    
    // Auto-calculate loan totals (for loan form)
    if (document.getElementById('id_amount')) {
        setupLoanCalculator();
    }
    
    // Setup tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Setup popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Loan Calculator Functions
function setupLoanCalculator() {
    const amountInput = document.getElementById('id_amount');
    const rateInput = document.getElementById('id_interest_rate');
    const tenureInput = document.getElementById('id_tenure_months');
    
    if (amountInput && rateInput && tenureInput) {
        [amountInput, rateInput, tenureInput].forEach(input => {
            input.addEventListener('input', calculateLoanTotals);
            input.addEventListener('change', calculateLoanTotals);
        });
        
        // Initial calculation
        calculateLoanTotals();
    }
}

function calculateLoanTotals() {
    const amount = parseFloat(document.getElementById('id_amount').value) || 0;
    const interestRate = parseFloat(document.getElementById('id_interest_rate').value) || 0;
    const tenureMonths = parseInt(document.getElementById('id_tenure_months').value) || 1;
    
    if (amount > 0 && tenureMonths > 0) {
        // Simple interest calculation
        const principal = amount;
        const rate = interestRate / 100;
        const timeYears = tenureMonths / 12;
        
        const interest = principal * rate * timeYears;
        const totalAmount = principal + interest;
        const monthlyInstallment = totalAmount / tenureMonths;
        
        // Update display elements
        updateCalculationDisplay('calculated-interest', interest);
        updateCalculationDisplay('calculated-total', totalAmount);
        updateCalculationDisplay('calculated-monthly', monthlyInstallment);
        
        // Show calculations
        const calculationsDiv = document.getElementById('loan-calculations');
        if (calculationsDiv) {
            calculationsDiv.style.display = 'block';
        }
    } else {
        // Hide calculations
        const calculationsDiv = document.getElementById('loan-calculations');
        if (calculationsDiv) {
            calculationsDiv.style.display = 'none';
        }
    }
}

function updateCalculationDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = '₹' + value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
}

// Utility Functions
function formatCurrency(amount) {
    return '₹' + amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}

// AJAX Functions
function markInstallmentPaid(installmentId) {
    if (!confirmAction('Mark this installment as paid?')) {
        return;
    }
    
    fetch(`/ajax/mark-paid/${installmentId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            location.reload(); // Refresh page to show updated data
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('An error occurred. Please try again.', 'error');
    });
}

// Cookie helper function for CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show message function
function showMessage(message, type) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="bi bi-${icon}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insert at the top of the main content
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) closeBtn.click();
            }
        }, 5000);
    }
}

// Search functionality
function setupSearch() {
    const searchInputs = document.querySelectorAll('input[type="search"], .search-input');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                const form = this.closest('form');
                if (form) form.submit();
            }
        });
    });
}

// Table sorting (basic)
function sortTable(tableId, columnIndex, dataType = 'string') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        if (dataType === 'number') {
            return parseFloat(aValue.replace(/[^\d.-]/g, '')) - parseFloat(bValue.replace(/[^\d.-]/g, ''));
        } else if (dataType === 'date') {
            return new Date(aValue) - new Date(bValue);
        } else {
            return aValue.localeCompare(bValue);
        }
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

// Print functionality
function printPage() {
    window.print();
}

// Export functionality (basic CSV export)
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csvContent = Array.from(rows).map(row => {
        const cells = row.querySelectorAll('th, td');
        return Array.from(cells).map(cell => 
            '"' + cell.textContent.trim().replace(/"/g, '""') + '"'
        ).join(',');
    }).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename || 'export.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Initialize search on page load
document.addEventListener('DOMContentLoaded', setupSearch);
