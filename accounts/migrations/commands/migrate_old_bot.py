import os
from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
from accounts.models import User
from cargo.models import Cargo  # To'g'rilangan import


class Command(BaseCommand):
    help = "Eski Telegram bot bazasidan ma'lumotlarni UTS bazasiga ko'chirish"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Migratsiya boshlanmoqda..."))

        db_conn = connections['default']

        with db_conn.cursor() as cursor:
            self.stdout.write("Foydalanuvchilarni o'qish...")
            cursor.execute("""
                SELECT 
                    c."Id", c."FirstName", c."LastName", c."PhoneNumber", t."TelegramId"
                FROM public."Customers" c
                LEFT JOIN public."TelegramUsers" t ON c."Id" = t."CustomerId"
            """)
            old_customers = cursor.fetchall()

            customer_mapping = {}

            for row in old_customers:
                old_id, first_name, last_name, phone, telegram_id = row

                # QO'SHILDI: Agar telefon raqam bo'sh bo'lsa, uni tashlab ketamiz (Skip)
                if not phone or not phone.strip():
                    continue

                # Telefon raqam formatini to'g'rilash
                clean_phone = phone.strip().replace(" ", "")
                if not clean_phone.startswith('+') and clean_phone.isdigit():
                    clean_phone = f"+{clean_phone}"

                # UTS bazasida bunday telefonli user bormi?
                user = User.objects.filter(phone=clean_phone).first()

                if not user:
                    u_id = f"TG{telegram_id}" if telegram_id else f"OLD{old_id}"

                    user = User.objects.create_user(
                        phone=clean_phone,
                        password=None,
                        first_name=first_name or "Klient",
                        last_name=last_name or "Eski",
                        user_id=u_id,
                        status='approved',
                        is_verified=True
                    )
                    self.stdout.write(self.style.SUCCESS(f"Yangi foydalanuvchi yaratildi: {clean_phone}"))
                else:
                    self.stdout.write(f"Mavjud foydalanuvchi topildi: {clean_phone}")

                customer_mapping[old_id] = user

            # 3. Eski yuklarni (Goods) o'qiymiz
            self.stdout.write("Yuklarni (Goods) ko'chirish boshlanmoqda...")
            cursor.execute("""
                SELECT 
                    "CustomerId", "TrackingNumber", "FlightNumber", "Weight", "Arrived", "State"
                FROM public."Goods"
            """)
            old_goods = cursor.fetchall()

            cargo_count = 0
            for good in old_goods:
                cust_id, tracking_number, flight_number, weight, arrived_date, state = good

                if not tracking_number:
                    continue

                target_user = customer_mapping.get(cust_id)

                final_status = 'Topshirildi' if state == 'Active' else 'Omborda'

                if not Cargo.objects.filter(track_code=tracking_number).exists():
                    cargo = Cargo(
                        user=target_user,
                        track_code=tracking_number,
                        flight_name=flight_number or "ESKI-REYS",
                        status=final_status,
                        weight=weight or 0.0,
                        created_at=arrived_date or timezone.now()
                    )
                    cargo._skip_push_signal = True
                    cargo.save()
                    cargo_count += 1

            self.stdout.write(self.style.SUCCESS(f"Muvaffaqiyatli yakunlandi! {cargo_count} ta yuk ko'chirildi."))