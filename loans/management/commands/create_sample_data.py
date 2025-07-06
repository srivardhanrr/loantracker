from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from loans.models import Borrower, Loan, Payment


class Command(BaseCommand):
    help = 'Generate sample data for testing the loan tracker application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--borrowers',
            type=int,
            default=10,
            help='Number of borrowers to create'
        )
        parser.add_argument(
            '--loans',
            type=int,
            default=15,
            help='Number of loans to create'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create borrowers
        borrowers_created = self.create_borrowers(options['borrowers'])
        self.stdout.write(f'Created {borrowers_created} borrowers')
        
        # Create loans
        loans_created = self.create_loans(options['loans'])
        self.stdout.write(f'Created {loans_created} loans')
        
        # Create some payments
        payments_created = self.create_payments()
        self.stdout.write(f'Created {payments_created} payments')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def create_borrowers(self, count):
        first_names = [
            'Rajesh', 'Priya', 'Amit', 'Sunita', 'Vikram', 'Anjali', 'Suresh', 'Kavita',
            'Ravi', 'Meera', 'Arun', 'Deepa', 'Sanjay', 'Rekha', 'Vinod', 'Pooja'
        ]
        last_names = [
            'Sharma', 'Patel', 'Singh', 'Kumar', 'Gupta', 'Yadav', 'Joshi', 'Verma',
            'Agarwal', 'Mishra', 'Tiwari', 'Pandey', 'Rana', 'Chauhan', 'Jain', 'Shah'
        ]
        
        created = 0
        for i in range(count):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = f"9{random.randint(100000000, 999999999)}"
            
            # Check if borrower already exists
            if not Borrower.objects.filter(phone=phone).exists():
                Borrower.objects.create(
                    name=name,
                    phone=phone,
                    email=f"{name.lower().replace(' ', '.')}@example.com",
                    address=f"House No. {random.randint(1, 999)}, {random.choice(['MG Road', 'Gandhi Nagar', 'Station Road', 'Market Street'])}, Jaipur"
                )
                created += 1
        
        return created

    def create_loans(self, count):
        borrowers = list(Borrower.objects.all())
        if not borrowers:
            self.stdout.write(self.style.ERROR('No borrowers found. Create borrowers first.'))
            return 0
        
        loan_amounts = [50000, 75000, 100000, 125000, 150000, 200000, 250000, 300000]
        interest_rates = [18, 20, 22, 24, 26, 28, 30]
        tenures = [6, 9, 12, 15, 18, 24]
        
        created = 0
        for i in range(count):
            borrower = random.choice(borrowers)
            
            # Don't create more than 3 loans per borrower
            if borrower.loans.count() >= 3:
                continue
            
            start_date = timezone.now().date() - timedelta(days=random.randint(30, 365))
            
            loan = Loan.objects.create(
                borrower=borrower,
                amount=Decimal(str(random.choice(loan_amounts))),
                interest_rate=Decimal(str(random.choice(interest_rates))),
                tenure_months=random.choice(tenures),
                start_date=start_date,
                installment_day=random.randint(1, 28),
                status=random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'CLOSED'])  # 75% active
            )
            created += 1
        
        return created

    def create_payments(self):
        # Create payments for some installments
        from loans.models import Installment
        
        installments = Installment.objects.filter(
            loan__status='ACTIVE',
            due_date__lte=timezone.now().date()
        ).order_by('due_date')
        
        created = 0
        for installment in installments[:50]:  # Process first 50 overdue installments
            # 70% chance of payment
            if random.random() < 0.7:
                payment_amount = installment.amount_due
                
                # 20% chance of partial payment
                if random.random() < 0.2:
                    payment_amount = installment.amount_due * Decimal(str(random.uniform(0.3, 0.9)))
                
                Payment.objects.create(
                    installment=installment,
                    amount=payment_amount,
                    payment_date=installment.due_date + timedelta(days=random.randint(0, 15)),
                    payment_method=random.choice(['CASH', 'BANK', 'ONLINE']),
                    notes='Sample payment'
                )
                created += 1
        
        return created
