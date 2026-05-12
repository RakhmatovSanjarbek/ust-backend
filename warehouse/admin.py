# admin.py (to'liq o'zgartirilgan)

import json
from django.contrib import admin
from django.urls import path
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import models
from cargo.models import Cargo
from warehouse.models import ArrivedGroup, PaymentRequest, DeliveryQueue
from accounts.models import User


@admin.register(ArrivedGroup)
class ArrivedGroupAdmin(admin.ModelAdmin):
    change_list_template = 'admin/warehouse/arrived_group_chat.html'

    list_display = ('receipt_code', 'user', 'payment_status', 'total_weight', 'total_price', 'created_at')
    list_filter = ('payment_status', 'user')
    search_fields = ('receipt_code', 'user__phone', 'user__first_name', 'user__last_name', 'user__user_id')
    readonly_fields = ('display_group_image', 'display_payment_check', 'total_weight', 'total_price')
    list_per_page = 50

    fieldsets = (
        ('Asosiy ma\'lumotlar', {'fields': ('user', 'receipt_code', 'payment_status')}),
        ('Yuklar', {'fields': ('selected_cargos',)}),
        ('To\'lov va Yetkazish',
         {'fields': ('total_weight', 'total_price', 'image', 'payment_check', 'delivery_method', 'delivery_address')}),
        ('Admin ma\'lumotlari', {'fields': ('admin_note', 'created_by', 'delivered_admin'), 'classes': ('collapse',)}),
    )

    filter_horizontal = ('selected_cargos',)

    def display_group_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" style="border-radius:8px; object-fit:cover;"/>',
                               obj.image.url)
        return "Rasm yuklanmagan"

    display_group_image.short_description = "Guruh rasmi"

    def display_payment_check(self, obj):
        if obj.payment_check:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" width="300" style="border-radius:8px;"/></a>',
                obj.payment_check.url)
        return "Chek yo'q"

    display_payment_check.short_description = "To'lov cheki rasmi"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('selected_cargos')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('api/users/', self.admin_site.admin_view(self.api_users), name='warehouse_api_users'),
            path('api/users/search/', self.admin_site.admin_view(self.api_users_search),
                 name='warehouse_api_users_search'),
            path('api/flights/<int:user_id>/', self.admin_site.admin_view(self.api_flights),
                 name='warehouse_api_flights'),
            path('api/flights/search/<int:user_id>/', self.admin_site.admin_view(self.api_flights_search),
                 name='warehouse_api_flights_search'),
            path('api/cargos/<int:user_id>/<str:flight_name>/', self.admin_site.admin_view(self.api_cargos),
                 name='warehouse_api_cargos'),
            path('api/create-group/', self.admin_site.admin_view(self.api_create_group),
                 name='warehouse_api_create_group'),
            path('api/groups/', self.admin_site.admin_view(self.api_groups), name='warehouse_api_groups'),
            path('api/group/<int:group_id>/', self.admin_site.admin_view(self.api_group_detail),
                 name='warehouse_api_group_detail'),
        ]
        return custom_urls + urls

    def api_users(self, request):
        """Barcha foydalanuvchilarni olish (Select2 uchun)"""
        users = User.objects.filter(is_staff=False).order_by('-date_joined')
        data = [{
            'id': u.id,
            'name': f"{u.first_name} {u.last_name}".strip() or u.phone,
            'text': f"{u.first_name} {u.last_name}".strip() or u.phone,
            'user_id': u.user_id,
            'phone': u.phone
        } for u in users]
        return JsonResponse(data, safe=False)

    def api_users_search(self, request):
        """Foydalanuvchilarni qidirish (Select2 AJAX uchun)"""
        search_term = request.GET.get('q', '').strip()
        page = int(request.GET.get('page', 1))
        per_page = 20

        if search_term:
            users = User.objects.filter(is_staff=False).filter(
                models.Q(first_name__icontains=search_term) |
                models.Q(last_name__icontains=search_term) |
                models.Q(phone__icontains=search_term) |
                models.Q(user_id__icontains=search_term)
            ).order_by('-date_joined')
        else:
            users = User.objects.filter(is_staff=False).order_by('-date_joined')

        # Pagination
        total = users.count()
        start = (page - 1) * per_page
        end = start + per_page
        users = users[start:end]

        data = [{
            'id': u.id,
            'text': f"{u.first_name} {u.last_name}".strip() or u.phone,
            'user_id': u.user_id,
            'phone': u.phone,
            'name': f"{u.first_name} {u.last_name}".strip() or u.phone
        } for u in users]

        return JsonResponse({
            'results': data,
            'pagination': {'more': end < total}
        })

    def api_flights(self, request, user_id):
        """Foydalanuvchining barcha reyslarini olish"""
        cargos = Cargo.objects.filter(
            user_id=user_id,
            status="Yo'lda"
        ).exclude(flight_name__isnull=True).exclude(
            flight_name=''
        ).values('flight_name').distinct()

        flights = [{'id': c['flight_name'], 'text': f"✈️ {c['flight_name']}"} for c in cargos if c['flight_name']]
        return JsonResponse({'results': flights}, safe=False)

    def api_flights_search(self, request, user_id):
        """Reyslarni qidirish (Select2 AJAX uchun)"""
        search_term = request.GET.get('q', '').strip()

        queryset = Cargo.objects.filter(
            user_id=user_id,
            status="Yo'lda"
        ).exclude(flight_name__isnull=True).exclude(flight_name='')

        if search_term:
            queryset = queryset.filter(flight_name__icontains=search_term)

        flights = queryset.values('flight_name').distinct()

        data = [{'id': c['flight_name'], 'text': f"✈️ {c['flight_name']}"} for c in flights if c['flight_name']]
        return JsonResponse({'results': data}, safe=False)

    def api_cargos(self, request, user_id, flight_name):
        """Reysdagi barcha yuklarni olish"""
        cargos = Cargo.objects.filter(
            user_id=user_id,
            flight_name=flight_name,
            status="Yo'lda"
        ).values('id', 'track_code', 'flight_name')

        data = [{
            'id': c['id'],
            'track_code': c['track_code'],
            'flight_name': c['flight_name']
        } for c in cargos]
        return JsonResponse(data, safe=False)

    def api_groups(self, request):
        """Barcha guruhlarni olish"""
        groups = ArrivedGroup.objects.all().select_related('user').order_by('-created_at')
        data = []
        for g in groups:
            # To'lov holati uchun badge class
            status_class_map = {
                'To\'lov kutilmoqda': 'badge-warning',
                'Tasdiqlash jarayonida': 'badge-info',
                'To\'lov tasdiqlandi': 'badge-success',
                'To\'lov rad etildi': 'badge-danger',
                'Topshirildi': 'badge-secondary'
            }

            data.append({
                'id': g.id,
                'receipt_code': g.receipt_code,
                'user_name': str(g.user),
                'user_id': g.user.user_id,
                'user_phone': g.user.phone,
                'image': g.image.url if g.image else None,
                'total_weight': float(g.total_weight),
                'total_price': float(g.total_price),
                'payment_status': g.payment_status,
                'payment_status_class': status_class_map.get(g.payment_status, 'badge-secondary'),
                'delivery_method': g.delivery_method or '—',
                'delivery_address': g.delivery_address or '—',
                'cargos_count': g.selected_cargos.count(),
                'created_at': g.created_at.isoformat(),
                'created_at_display': g.created_at.strftime('%d.%m.%Y %H:%M'),
            })
        return JsonResponse(data, safe=False)

    def api_group_detail(self, request, group_id):
        """Bitta guruh detallarini olish"""
        try:
            group = ArrivedGroup.objects.get(id=group_id)
            cargos = group.selected_cargos.all().values('id', 'track_code', 'flight_name', 'status')

            return JsonResponse({
                'id': group.id,
                'receipt_code': group.receipt_code,
                'user_name': str(group.user),
                'total_weight': float(group.total_weight),
                'total_price': float(group.total_price),
                'payment_status': group.payment_status,
                'delivery_method': group.delivery_method,
                'delivery_address': group.delivery_address,
                'cargos': list(cargos),
                'image': group.image.url if group.image else None,
            })
        except ArrivedGroup.DoesNotExist:
            return JsonResponse({'error': 'Guruh topilmadi'}, status=404)

    @method_decorator(csrf_exempt)
    def api_create_group(self, request):
        """Yangi guruh yaratish"""
        if request.method == 'POST':
            try:
                # Rasmni olish (fayl yoki base64)
                image = request.FILES.get('image')

                # Agar base64 da kelgan bo'lsa
                if not image and request.POST.get('image_base64'):
                    import base64
                    from django.core.files.base import ContentFile
                    import uuid

                    image_base64 = request.POST.get('image_base64')
                    format, imgstr = image_base64.split(';base64,')
                    ext = format.split('/')[-1]
                    image = ContentFile(
                        base64.b64decode(imgstr),
                        name=f'group_{uuid.uuid4().hex}.{ext}'
                    )

                cargo_ids = json.loads(request.POST.get('cargo_ids', '[]'))
                user_id = request.POST.get('user_id')
                flight_name = request.POST.get('flight_name')

                # Umumiy og'irlik va narx (bitta qiymat)
                total_weight = float(request.POST.get('total_weight', 0))
                total_price = float(request.POST.get('total_price', 0))

                if not user_id:
                    return JsonResponse({'error': 'Foydalanuvchi tanlanmagan'}, status=400)
                if not flight_name:
                    return JsonResponse({'error': 'Reys tanlanmagan'}, status=400)
                if not cargo_ids:
                    return JsonResponse({'error': 'Hech qanday yuk tanlanmagan'}, status=400)

                user = get_object_or_404(User, id=user_id)
                cargos = Cargo.objects.filter(id__in=cargo_ids, status="Yo'lda")

                if not cargos.exists():
                    return JsonResponse({'error': 'Tanlangan yuklar topilmadi yoki ular allaqachon punktda'},
                                        status=400)

                # Receipt code sifatida reys nomi + vaqt
                receipt_code = f"{flight_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"

                group = ArrivedGroup.objects.create(
                    user=user,
                    receipt_code=receipt_code,
                    total_weight=total_weight,
                    total_price=total_price,
                    image=image,
                    created_by=request.user if request.user.is_authenticated else None,
                    payment_status='To\'lov kutilmoqda'
                )

                group.selected_cargos.set(cargos)

                # Yuklarning statusini yangilash - arrived_at maydonini olib tashladim
                cargos.update(
                    status='Punktda',
                    arrived_group=group,
                    arrived_admin=request.user if request.user.is_authenticated else None
                    # arrived_at maydoni yo'q, shuning uchun olib tashlandi
                )

                return JsonResponse({
                    'status': 'success',
                    'group_id': group.id,
                    'receipt_code': receipt_code,
                    'message': f'✅ {len(cargo_ids)} ta yuk guruhga qo\'shildi | ⚖ {total_weight} kg | 💰 {total_price:,.0f} so\'m',
                    'group': {
                        'id': group.id,
                        'receipt_code': receipt_code,
                        'total_weight': total_weight,
                        'total_price': total_price,
                        'payment_status': group.payment_status
                    }
                })
            except json.JSONDecodeError as e:
                return JsonResponse({'error': f'JSON xatosi: {str(e)}'}, status=400)
            except ValueError as e:
                return JsonResponse({'error': f'Qiymat xatosi: {str(e)}'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Xatolik yuz berdi: {str(e)}'}, status=500)

        return JsonResponse({'error': 'Method not allowed'}, status=405)


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('receipt_code', 'display_user', 'total_price', 'payment_status', 'created_at')
    list_filter = ('payment_status',)
    search_fields = ('receipt_code', 'user__phone', 'user__first_name', 'user__user_id')
    readonly_fields = ('payment_check_image',)
    list_per_page = 30

    def get_queryset(self, request):
        return super().get_queryset(request).filter(payment_status='Tasdiqlash jarayonida')

    def display_user(self, obj):
        return format_html("<b>{}</b><br/><small>{}</small>", obj.user.get_full_name() or obj.user.phone,
                           obj.user.user_id)

    display_user.short_description = "Foydalanuvchi"

    def payment_check_image(self, obj):
        if obj.payment_check:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" width="300" style="border-radius:8px;"/></a>',
                obj.payment_check.url)
        return "Chek yuklanmagan"

    payment_check_image.short_description = "Chek rasmi"

    actions = ['approve_payments', 'reject_payments']

    @admin.action(description="✅ To'lovni tasdiqlash")
    def approve_payments(self, request, queryset):
        count = 0
        for group in queryset:
            group.payment_status = 'To\'lov tasdiqlandi'
            group.admin_note = f"To'lov qabul qilindi ✅ - {request.user}"
            group.save()
            count += 1
        self.message_user(request, f"{count} ta to'lov muvaffaqiyatli tasdiqlandi.")

    @admin.action(description="❌ To'lovni rad etish")
    def reject_payments(self, request, queryset):
        count = 0
        for group in queryset:
            group.payment_status = 'To\'lov rad etildi'
            group.admin_note = f"To'lov topilmadi yoki chek xato ❌ - {request.user}"
            group.save()
            count += 1
        self.message_user(request, f"{count} ta to'lov rad etildi.")


@admin.register(DeliveryQueue)
class DeliveryQueueAdmin(admin.ModelAdmin):
    list_display = ('receipt_code', 'get_customer', 'total_weight', 'total_price', 'delivery_method',
                    'delivery_address', 'payment_status')
    list_filter = ('delivery_method', 'payment_status')
    search_fields = ('receipt_code', 'user__phone', 'user__first_name', 'user__user_id')
    list_per_page = 30

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            payment_status='To\'lov tasdiqlandi'
        ).exclude(delivery_method__isnull=True).exclude(
            delivery_method=''
        ).exclude(
            selected_cargos__status='Topshirildi'
        ).distinct()

    def get_customer(self, obj):
        return format_html(
            "<b>{}</b><br/>📞 {}<br/>🆔 {}",
            obj.user.get_full_name() or obj.user.phone,
            obj.user.phone,
            obj.user.user_id
        )

    get_customer.short_description = "Mijoz"

    def total_weight(self, obj):
        return f"{obj.total_weight} kg"

    total_weight.short_description = "Umumiy og'irlik"

    def total_price(self, obj):
        return f"{obj.total_price:,.0f} so'm"

    total_price.short_description = "Umumiy summa"

    actions = ['ship_out_cargos']

    @admin.action(description="🚚 Tanlangan yuklarni topshirish")
    def ship_out_cargos(self, request, queryset):
        now = timezone.now()
        count = 0
        cargos_count = 0

        for group in queryset:
            group.payment_status = 'Topshirildi'
            group.delivered_admin = request.user
            group.admin_note = f"Yuk topshirildi ✅ - {request.user}"
            group.save()

            cargos = group.selected_cargos.all()
            cargos_count += cargos.count()
            cargos.update(
                status='Topshirildi',
                delivered_at=now,
                delivered_admin=request.user,
                updated_by=request.user
            )
            count += 1

        self.message_user(
            request,
            f"✅ {count} ta guruh va {cargos_count} ta yuk muvaffaqiyatli topshirildi."
        )