from django.core.management.base import BaseCommand
from django.db import transaction
from loans.models import Loan, Installment
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Update existing loans to start installments from next month'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually apply the changes (default is dry-run)',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        
        if not apply_changes:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
            self.stdout.write('Add --apply flag to actually update the loans')
        
        # Find loans that have installments starting in the same month as loan start date
        loans_to_update = []
        
        for loan in Loan.objects.filter(status='ACTIVE'):
            first_installment = loan.installments.order_by('installment_number').first()
            if first_installment:
                # Check if first installment is in the same month as loan start
                if (first_installment.due_date.year == loan.start_date.year and 
                    first_installment.due_date.month == loan.start_date.month):
                    loans_to_update.append(loan)
        
        if not loans_to_update:
            self.stdout.write(
                self.style.SUCCESS('No loans need updating - all are already correct!')
            )
            return
        
        self.stdout.write(f'Found {len(loans_to_update)} loans that need updating:')
        
        for loan in loans_to_update:
            first_installment = loan.installments.order_by('installment_number').first()
            self.stdout.write(
                f'- Loan {loan.id}: {loan.borrower.name} '
                f'(Start: {loan.start_date}, First EMI: {first_installment.due_date})'
            )
        
        if not apply_changes:
            self.stdout.write(
                self.style.WARNING('\nTo apply these changes, run: python manage.py fix_installment_dates --apply')
            )
            return
        
        # Apply changes
        updated_count = 0
        
        with transaction.atomic():
            for loan in loans_to_update:
                # Check if any payments have been made
                if loan.get_paid_amount() > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping loan {loan.id} - payments already made'
                        )
                    )
                    continue
                
                # Delete existing installments
                loan.installments.all().delete()
                
                # Regenerate installments (will use new logic)
                loan.generate_installments()
                
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated loan {loan.id} for {loan.borrower.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully updated {updated_count} loans! '
                f'Installments now start from next month.'
            )
        )
