from django.core.management.base import BaseCommand
from django.db import transaction
from loans.models import Loan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Round off all existing loan amounts to whole numbers'

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
        
        # Find loans with decimal values
        loans_to_update = []
        
        for loan in Loan.objects.all():
            # Check if any amounts have decimal places
            if (loan.total_amount % 1 != 0 or 
                loan.monthly_installment % 1 != 0):
                loans_to_update.append(loan)
        
        if not loans_to_update:
            self.stdout.write(
                self.style.SUCCESS('No loans need updating - all amounts are already whole numbers!')
            )
            return
        
        self.stdout.write(f'Found {len(loans_to_update)} loans with decimal amounts:')
        
        for loan in loans_to_update:
            self.stdout.write(
                f'- Loan {loan.id}: {loan.borrower.name} '
                f'(Total: ₹{loan.total_amount}, EMI: ₹{loan.monthly_installment})'
            )\n        \n        if not apply_changes:\n            self.stdout.write(\n                self.style.WARNING('\\nTo apply these changes, run: python manage.py round_loan_amounts --apply')\n            )\n            return\n        \n        # Apply changes\n        updated_count = 0\n        \n        with transaction.atomic():\n            for loan in loans_to_update:\n                # Round the amounts\n                loan.total_amount = loan.total_amount.quantize(Decimal('1'))\n                loan.monthly_installment = loan.monthly_installment.quantize(Decimal('1'))\n                \n                # Update all installments to rounded amount\n                for installment in loan.installments.all():\n                    installment.amount_due = loan.monthly_installment\n                    installment.save()\n                \n                loan.save()\n                updated_count += 1\n                \n                self.stdout.write(\n                    self.style.SUCCESS(\n                        f'Updated loan {loan.id} - Total: ₹{loan.total_amount}, EMI: ₹{loan.monthly_installment}'\n                    )\n                )\n        \n        self.stdout.write(\n            self.style.SUCCESS(\n                f'\\nSuccessfully updated {updated_count} loans! All amounts are now whole numbers.'\n            )\n        )"
            )
            return
        
        # Apply changes
        updated_count = 0
        
        with transaction.atomic():
            for loan in loans_to_update:
                # Round the amounts
                loan.total_amount = loan.total_amount.quantize(Decimal('1'))
                loan.monthly_installment = loan.monthly_installment.quantize(Decimal('1'))
                
                # Update all installments to rounded amount
                for installment in loan.installments.all():
                    installment.amount_due = loan.monthly_installment
                    installment.save()
                
                loan.save()
                updated_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated loan {loan.id} - Total: ₹{loan.total_amount}, EMI: ₹{loan.monthly_installment}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully updated {updated_count} loans! All amounts are now whole numbers.'
            )
        )
