import os
import random
from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
from accounts.models import User
from cargo.models import Cargo


class Command(BaseCommand):
    help = "Eski Telegram bot bazasidan ma'lumotlarni UTS bazasiga ko'chirish"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Migratsiya boshlanmoqda..."))

        db_conn = connections['default']

        with db_conn.cursor() as cursor:
            # 1. Foydalanuvchilar va ularning pasport ma'lumotlarini bog'lab o'qiymiz
            self.stdout.write("Foydalanuvchilar va Pasportlarni o'qish...")
            cursor.execute("""
                SELECT 
                    c."Id", c."FirstName", c."LastName", c."PhoneNumber",
                    p."SerialNumber", p."Pinfl"
                FROM public."Customers" c
                LEFT JOIN public."Passports" p ON c."Id" = p."CustomerId"
            """)
            old_customers = cursor.fetchall()

            customer_mapping = {}

            for row in old_customers:
                old_id, first_name, last_name, phone, passport_serial, pinfl = row

                if not phone or not str(phone).strip():
                    continue

                clean_phone = str(phone).strip().replace(" ", "")
                clean_phone = "".join([c for c in clean_phone if c.isdigit() or c == '+'])

                if len(clean_phone) < 9:
                    continue

                if not clean_phone.startswith('+') and clean_phone.isdigit():
                    clean_phone = f"+{clean_phone}"

                user = User.objects.filter(phone=clean_phone).first()

                if not user:
                    # UTS-XXXXX formatida takrorlanmas ID generatsiya qilish
                    attempts = 0
                    while attempts < 10:
                        random_id = f"UTS-{random.randint(10000, 99999)}"
                        if not User.objects.filter(user_id=random_id).exists():
                            generated_user_id = random_id
                            break
                        attempts += 1
                    else:
                        generated_user_id = f"UTS-{old_id}{random.randint(10, 99)}"

                    # Ism oxiriga "tg bot" qo'shish, familiyani to'g'rilash
                    f_name = first_name.strip() if first_name else "Klient"
                    if "Eski" in f_name:
                        f_name = f_name.replace("Eski", "").strip()

                    # Oxiriga "tg bot" qo'shimchasi
                    if not f_name.endswith("tg bot"):
                        f_name = f"{f_name} tg bot"

                    l_name = last_name.strip() if last_name else ""
                    if "Eski" in l_name:
                        l_name = l_name.replace("Eski", "").strip()

                    try:
                        user = User.objects.create_user(
                            phone=clean_phone,
                            password=None,
                            first_name=f_name,
                            last_name=l_name or "Mijoz",
                            user_id=generated_user_id,
                            passport_series=passport_serial,  # Django model field nomi bilan bir xilligini tekshiring
                            jshshir=pinfl,
                            status='approved',
                            is_verified=True
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f"Yangi foydalanuvchi yaratildi: {clean_phone} | ID: {generated_user_id}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Xatolik foydalanuvchida ({clean_phone}): {e}"))
                        continue
                else:
                    self.stdout.write(f"Mavjud foydalanuvchi topildi: {clean_phone}")
                    # Mavjud foydalanuvchining ma'lumotlarini yangilash
                    if "tg bot" not in user.first_name:
                        user.first_name = f"{user.first_name} tg bot"
                    if passport_serial and not user.passport_series:
                        user.passport_series = passport_serial
                    if pinfl and not user.jshshir:
                        user.jshshir = pinfl
                    user.save()

                customer_mapping[old_id] = user

            # 2. Eski yuklarni (Goods) o'qiymiz
            self.stdout.write("Yuklarni (Goods) ko'chirish boshlanmoqda...")
            cursor.execute("""
                SELECT 
                    "CustomerId", "TrackingNumber", "FlightNumber", "Arrived", "State"
                FROM public."Goods"
            """)
            old_goods = cursor.fetchall()

            cargo_count = 0
            for good in old_goods:
                cust_id, tracking_number, flight_number, arrived_date, state = good

                if not tracking_number:
                    continue

                target_user = customer_mapping.get(cust_id)
                final_status = 'Topshirildi' if state == 'Active' else 'Omborda'

                if not Cargo.objects.filter(track_code=tracking_number).exists():
                    # Modelda 'weight' yo'qligi uchun argumentlardan olib tashlandi
                    cargo = Cargo(
                        user=target_user,
                        track_code=tracking_number,
                        flight_name=flight_number or "ESKI-REYS",
                        status=final_status,
                        created_at=arrived_date or timezone.now()
                    )
                    cargo._skip_push_signal = True
                    cargo.save()
                    cargo_count += 1

            self.stdout.write(self.style.SUCCESS(f"Muvaffaqiyatli yakunlandi! {cargo_count} ta yuk ko'chirildi."))