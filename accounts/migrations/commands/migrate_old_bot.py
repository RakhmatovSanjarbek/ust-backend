import os
from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
from accounts.models import User
from warehouse.models import Cargo  # Cargo qaysi appdaligiga qarab importni tekshiring


class Command(BaseCommand):
    help = "Eski Telegram bot bazasidan ma'lumotlarni UTS bazasiga ko'chirish"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Migratsiya boshlanmoqda..."))

        # 1. Eski bazaga ulanish (Buning uchun settings.py da 'old_bot' degan havola bo'lishi kerak)
        # Yoki eski jadvallarni vaqtincha hozirgi PostgreSQL bazangizga import qilgan bo'lsangiz 'default' deb qoldiring
        db_conn = connections['default']

        with db_conn.cursor() as cursor:
            # 2. Eski Customers va TelegramUsers jadvallarini birlashtirib o'qiymiz
            self.stdout.write("Foydalanuvchilarni o'qish...")
            cursor.execute("""
                SELECT 
                    c."Id", c."FirstName", c."LastName", c."PhoneNumber", t."TelegramId"
                FROM public."Customers" c
                LEFT JOIN public."TelegramUsers" t ON c."Id" = t."CustomerId"
            """)
            old_customers = cursor.fetchall()

            customer_mapping = {}  # Eski Customer ID -> UTS User obyekti

            for row in old_customers:
                old_id, first_name, last_name, phone, telegram_id = row

                # Telefon raqam formatini to'g'rilash (+ belgisini olib tashlash yoki qo'shish)
                clean_phone = phone.strip().replace(" ", "")
                if not clean_phone.startswith('+') and clean_phone.isdigit():
                    clean_phone = f"+{clean_phone}"

                # UTS bazasida bunday telefonli user bormi?
                user = User.objects.filter(phone=clean_phone).first()

                if not user:
                    # Agar foydalanuvchi yangi ilovada hali yo'q bo'lsa, uni yaratamiz
                    # user_id sifatida telegram_id yoki tasodifiy raqam beramiz
                    u_id = f"TG{telegram_id}" if telegram_id else f"OLD{old_id}"

                    user = User.objects.create_user(
                        phone=clean_phone,
                        password=None,  # Parolsiz, ilovaga kirganda OTP bilan kiradi
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

            # 3. Eski yuklarni (Goods) o'qiymiz va Cargo modeliga o'tkazamiz
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

                # Bu yuk qaysi userga tegishli ekanligini topamiz
                target_user = customer_mapping.get(cust_id)

                # Eski statelarni UTS statuslariga o'giramiz (Masalan: Active bo'lsa Topshirildi yoki Ombor)
                # Eski bazada "State" ustuni bor ekan, shunga qarab status beramiz
                final_status = 'Topshirildi' if state == 'Active' else 'Omborda'

                # Yuk UTS bazasida allaqachon bormi tekshiramiz (dublikat bo'lmasligi uchun)
                if not Cargo.objects.filter(track_code=tracking_number).exists():
                    cargo = Cargo(
                        user=target_user,
                        track_code=tracking_number,
                        flight_name=flight_number or "ESKI-REYS",
                        status=final_status,
                        weight=weight or 0.0,
                        created_at=arrived_date or timezone.now()
                    )
                    # SIZNING MODELDAGI SIGNALNI O'CHIRISH BAYROG'I (Push ketmaydi)
                    cargo._skip_push_signal = True
                    cargo.save()
                    cargo_count += 1

            self.stdout.write(self.style.SUCCESS(f"Muvaffaqiyatli yakunlandi! {cargo_count} ta yuk ko'chirildi."))