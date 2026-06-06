from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser account using phone number and password."

    def add_arguments(self, parser):
        parser.add_argument("--phone", required=True, help="Phone number: +998XXXXXXXXX")
        parser.add_argument("--password", required=True, help="Account password")
        parser.add_argument("--full-name", default="Admin", help="Full name (optional)")

    def handle(self, *args, **options):
        phone = options["phone"]
        password = options["password"]
        full_name = options["full_name"]

        if User.objects.filter(phone=phone).exists():
            raise CommandError(f"A user with phone '{phone}' already exists.")

        User.objects.create_superuser(
            phone=phone,
            password=password,
            full_name=full_name,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Superuser '{phone}' created successfully.")
        )
