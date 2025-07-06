from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Create a new user for the loan tracker system'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the new user')
        parser.add_argument('email', type=str, help='Email for the new user')
        parser.add_argument('--password', type=str, help='Password for the new user')
        parser.add_argument('--first-name', type=str, help='First name of the user')
        parser.add_argument('--last-name', type=str, help='Last name of the user')
        parser.add_argument('--superuser', action='store_true', help='Create as superuser')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options.get('password')
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        is_superuser = options.get('superuser', False)

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'User "{username}" already exists!')
            )
            return

        # Check if email already exists
        if email and User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'User with email "{email}" already exists!')
            )
            return

        # Get password if not provided
        if not password:
            password = input('Enter password: ')
            confirm_password = input('Confirm password: ')
            if password != confirm_password:
                self.stdout.write(
                    self.style.ERROR('Passwords do not match!')
                )
                return

        try:
            # Create the user
            if is_superuser:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                user_type = "superuser"
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                user_type = "user"

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {user_type} "{username}" ({email})'
                )
            )

            # Display login instructions
            self.stdout.write(
                self.style.WARNING(
                    f'\nYou can now login at http://localhost:8000/auth/login/'
                    f'\nUsername: {username}'
                    f'\nPassword: [your password]'
                )
            )

        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
