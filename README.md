# Loan Tracker - Personal Loan Management System

A comprehensive Django-based web application for managing personal loans in your local community. Track borrowers, loans, installments, and payments with ease.

## Features

### 🏦 **Core Functionality**
- **Borrower Management**: Add, edit, and manage borrower profiles with ID proof uploads
- **Loan Creation**: Create loans with automatic calculation of interest and installments
- **Installment Tracking**: Auto-generated monthly installment schedules
- **Payment Recording**: Track payments with support for partial payments
- **Dashboard**: Comprehensive overview of all loan activities

### 📊 **Dashboard Features**
- Total amount disbursed across all loans
- Total receivable amount
- Expected income for current month
- Overdue installments tracking
- Recent payment activities

### 💰 **Loan Calculations**
- Simple interest calculation (Principal + Interest)
- Automatic total amount calculation
- Monthly installment computation
- Outstanding amount tracking

### 🔍 **Advanced Features**
- Search and filter functionality
- Overdue payment alerts
- Loan status management (Active/Closed/Defaulted)
- Payment history tracking
- Responsive design for mobile devices

## Technology Stack

- **Backend**: Django 5.2.4
- **Database**: SQLite (default, easily changeable)
- **Frontend**: Bootstrap 5.3, HTML5, CSS3, JavaScript
- **File Handling**: Django's FileField for document uploads
- **Date Management**: python-dateutil for advanced date calculations

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone or Setup Project
```bash
# Navigate to your project directory
cd C:\Users\Sriva\PycharmProjects\loantracker
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Database Setup
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser
```

### Step 5: Create Sample Data (Optional)
```bash
# Generate sample borrowers and loans for testing
python manage.py create_sample_data --borrowers 10 --loans 15
```

### Step 6: Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## Usage Guide

### 📝 **Getting Started**

1. **Access the Application**: Navigate to `http://localhost:8000`
2. **Add Your First Borrower**: Click "Add New Borrower" and fill in the details
3. **Create a Loan**: Select the borrower and create a loan with your terms
4. **Track Payments**: Use the dashboard to see upcoming dues and record payments

### 🏠 **Dashboard Overview**

The dashboard provides:
- **Key Metrics**: Total disbursed, receivable, monthly expected income
- **Quick Actions**: Add borrower, create loan, view overdue payments
- **Recent Activities**: Latest payments and upcoming installments

### 👤 **Borrower Management**

- **Add Borrower**: Name, phone, email, address, and ID proof upload
- **View Profile**: Complete borrower information with loan history
- **Edit Details**: Update borrower information as needed

### 💸 **Loan Management**

- **Create Loan**: 
  - Select borrower
  - Enter loan amount (minimum ₹1,000)
  - Set interest rate (annual percentage)
  - Choose tenure (1-60 months)
  - Set installment day (1-31 of each month)
  - System auto-calculates total amount and monthly EMI

- **Track Progress**: 
  - View installment schedule
  - Monitor payment status
  - Check outstanding amounts

### 💳 **Payment Processing**

- **Record Payments**: Full or partial payment support
- **Payment Methods**: Cash, Bank Transfer, Online, Check
- **Payment History**: Complete audit trail for each installment

## Example Loan Calculation

**Loan Parameters:**
- Principal Amount: ₹1,00,000
- Interest Rate: 24% annually
- Tenure: 12 months
- Loan Start Date: January 15, 2024
- Installment Day: 5th of each month

**Calculations:**
- Interest Amount: ₹24,000 (Simple Interest)
- Total Amount: ₹1,24,000
- Monthly EMI: ₹10,333 (rounded to whole number)

**Installment Schedule:**
- Loan Disbursement: January 15, 2024
- First EMI Due: February 5, 2024
- Second EMI Due: March 5, 2024
- Last EMI Due: January 5, 2025

*Note: Installments start from the month following loan disbursement.*

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` with your superuser credentials for advanced management:

- Advanced filtering and search
- Bulk operations
- Detailed loan analytics
- Data export capabilities

## File Structure

```
loantracker/
├── loans/                          # Main application
│   ├── models.py                   # Database models
│   ├── views/                      # View controllers
│   ├── forms.py                    # Form definitions
│   ├── utils.py                    # Utility functions
│   ├── admin.py                    # Admin interface
│   └── management/commands/        # Custom management commands
├── templates/loans/                # HTML templates
├── static/                         # CSS, JavaScript, images
├── media/                          # Uploaded files
├── manage.py                       # Django management script
└── requirements.txt                # Python dependencies
```

## Customization

### Interest Calculation
The system uses simple interest calculation. To modify:
1. Edit the `calculate_totals()` method in `loans/models.py`
2. Update the JavaScript calculator in `loan_form.html`

### Default Settings
Modify default values in `loans/forms.py`:
- Default interest rate
- Default tenure
- Default installment day

### UI Customization
- Edit `static/css/custom.css` for styling changes
- Modify templates in `templates/loans/` for layout changes

## Security Features

- CSRF protection on all forms
- File upload validation (size and type)
- SQL injection protection (Django ORM)
- XSS protection (Django templating)

## Backup & Data Management

### Regular Backups
```bash
# Backup database
python manage.py dumpdata > backup.json

# Restore database
python manage.py loaddata backup.json
```

### Data Export
- Use Django admin interface for CSV exports
- Create custom management commands for specific reports

## Troubleshooting

### Common Issues

1. **Migration Errors**: Delete `db.sqlite3` and re-run migrations
2. **Static Files Not Loading**: Run `python manage.py collectstatic`
3. **File Upload Issues**: Check `MEDIA_ROOT` settings
4. **Date Calculation Errors**: Ensure `python-dateutil` is installed

### Performance Tips

- Regular database maintenance
- Archive old closed loans
- Optimize media file storage
- Use database indexing for large datasets

## License

This project is created for personal use. Feel free to modify and adapt according to your needs.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django documentation
3. Examine the code comments for implementation details

## Future Enhancements

Potential improvements:
- SMS/Email notifications for due payments
- Advanced reporting and analytics
- Mobile app integration
- Multi-currency support
- Compound interest calculations
- Automated backup scheduling

---

**Note**: This application is designed for personal loan management in small communities. For larger scale operations, consider additional security measures and database optimization.
