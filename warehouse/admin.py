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
from cargo.models import Cargo
from warehouse.models import ArrivedGroup, PaymentRequest, DeliveryQueue
from accounts.models import User


@admin.register(ArrivedGroup)
class ArrivedGroupAdmin(admin.ModelAdmin):
    change_list_template = 'admin/warehouse/arrived_group_chat.html'

    list_display = ('receipt_code', 'user', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'user')
    search_fields = ('receipt_code', 'user__phone', 'user__first_name')
    readonly_fields = ('display_group_image', 'display_payment_check', 'total_weight', 'total_price')

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
            return format_html('<img src="{}" width="150" style="border-radius:8px;"/>', obj.image.url)
        return "Rasm yuklanmagan"

    display_group_image.short_description = "Guruh rasmi"

    def display_payment_check(self, obj):
        if obj.payment_check:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="300" /></a>', obj.payment_check.url)
        return "Chek yo'q"

    display_payment_check.short_description = "To'lov cheki rasmi"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('api/users/', self.admin_site.admin_view(self.api_users), name='warehouse_api_users'),
            path('api/flights/<int:user_id>/', self.admin_site.admin_view(self.api_flights),
                 name='warehouse_api_flights'),
            path('api/cargos/<int:user_id>/<str:flight_name>/', self.admin_site.admin_view(self.api_cargos),
                 name='warehouse_api_cargos'),
            path('api/create-group/', self.admin_site.admin_view(self.api_create_group),
                 name='warehouse_api_create_group'),
            path('api/groups/', self.admin_site.admin_view(self.api_groups), name='warehouse_api_groups'),
        ]
        return custom_urls + urls

    def api_users(self, request):
        users = User.objects.filter(is_staff=False).order_by('-date_joined')
        data = [{'id': u.id, 'name': f"{u.first_name} {u.last_name}".strip() or u.phone, 'user_id': u.user_id,
                 'phone': u.phone} for u in users]
        return JsonResponse(data, safe=False)

    def api_flights(self, request, user_id):
        cargos = Cargo.objects.filter(user_id=user_id, status="Yo'lda").exclude(flight_name__isnull=True).exclude(
            flight_name='').values('flight_name').distinct()
        flights = [c['flight_name'] for c in cargos if c['flight_name']]
        return JsonResponse(flights, safe=False)

    def api_cargos(self, request, user_id, flight_name):
        cargos = Cargo.objects.filter(user_id=user_id, flight_name=flight_name, status="Yo'lda").values('id',
                                                                                                        'track_code',
                                                                                                        'flight_name')
        data = [{'id': c['id'], 'track_code': c['track_code'], 'flight_name': c['flight_name']} for c in cargos]
        return JsonResponse(data, safe=False)

    def api_groups(self, request):
        groups = ArrivedGroup.objects.all().order_by('-created_at')
        data = []
        for g in groups:
            data.append({
                'id': g.id,
                'receipt_code': g.receipt_code,
                'user_name': str(g.user),
                'user_id': g.user.user_id,
                'image': g.image.url if g.image else None,
                'total_weight': float(g.total_weight),
                'total_price': float(g.total_price),
                'payment_status': g.payment_status,
                'delivery_method': g.delivery_method or '—',
                'delivery_address': g.delivery_address or '—',
                'created_at': g.created_at.isoformat(),
            })
        return JsonResponse(data, safe=False)

    @method_decorator(csrf_exempt)
    def api_create_group(self, request):
        if request.method == 'POST':
            try:
                image = request.FILES.get('image')
                cargo_ids = json.loads(request.POST.get('cargo_ids', '[]'))
                user_id = request.POST.get('user_id')
                flight_name = request.POST.get('flight_name')  # Reys nomi

                # Og'irlik va narxlarni olish
                cargo_weights = json.loads(request.POST.get('cargo_weights', '[]'))
                cargo_prices = json.loads(request.POST.get('cargo_prices', '[]'))

                user = get_object_or_404(User, id=user_id)
                cargos = Cargo.objects.filter(id__in=cargo_ids, status="Yo'lda")

                if not cargos.exists():
                    return JsonResponse({'error': 'Tanlangan yuklar topilmadi'}, status=400)

                # Yuklarni og'irlik va narxlarini yangilash (agar modelda weight/price bo'lsa)
                total_weight = 0
                total_price = 0
                for i, cargo in enumerate(cargos):
                    w = float(cargo_weights[i]) if i < len(cargo_weights) else 0
                    p = float(cargo_prices[i]) if i < len(cargo_prices) else 0
                    total_weight += w
                    total_price += p

                    # Agar Cargo modelida weight va price maydonlari bo'lsa
                    # cargo.weight = w
                    # cargo.price = p
                    # cargo.save()

                # Receipt code sifatida reys nomini ishlatamiz
                receipt_code = flight_name

                group = ArrivedGroup.objects.create(
                    user=user,
                    receipt_code=receipt_code,
                    total_weight=total_weight,
                    total_price=total_price,
                    image=image,
                    created_by=request.user,
                    payment_status='To\'lov kutilmoqda'
                )

                group.selected_cargos.set(cargos)
                cargos.update(status='Punktda', arrived_group=group, arrived_admin=request.user)

                return JsonResponse({
                    'status': 'success',
                    'group_id': group.id,
                    'message': f'{len(cargo_ids)} ta yuk guruhga qo\'shildi | ⚖ {total_weight} kg | 💰 {total_price:,.0f} so\'m'
                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'error': 'Method not allowed'}, status=405)


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('receipt_code', 'display_user', 'total_price', 'payment_status', 'created_at')
    list_filter = ('payment_status',)
    readonly_fields = ('payment_check_image',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(payment_status='Tasdiqlash jarayonida')

    def display_user(self, obj):
        return f"{obj.user.first_name} ({obj.user.user_id})"

    display_user.short_description = "Foydalanuvchi"

    def payment_check_image(self, obj):
        if obj.payment_check:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="300" /></a>', obj.payment_check.url)
        return "Chek yuklanmagan"

    payment_check_image.short_description = "Chek rasmi"

    actions = ['approve_payments', 'reject_payments']

    @admin.action(description="To'lovni tasdiqlash (✅)")
    def approve_payments(self, request, queryset):
        for group in queryset:
            group.payment_status = 'To\'lov tasdiqlandi'
            group.admin_note = "To'lov qabul qilindi ✅"
            group.save()
        self.message_user(request, f"{queryset.count()} ta to'lov tasdiqlandi.")

    @admin.action(description="To'lovni rad etish (❌)")
    def reject_payments(self, request, queryset):
        queryset.update(payment_status='To\'lov rad etildi', admin_note="To'lov topilmadi yoki chek xato ❌")
        self.message_user(request, f"{queryset.count()} ta to'lov rad etildi.")


@admin.register(DeliveryQueue)
class DeliveryQueueAdmin(admin.ModelAdmin):
    list_display = ('receipt_code', 'get_customer', 'delivery_method', 'delivery_address', 'payment_status')
    list_filter = ('delivery_method', 'payment_status')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            payment_status='To\'lov tasdiqlandi'
        ).exclude(delivery_method__isnull=True).exclude(delivery_method='').exclude(
            selected_cargos__status='Topshirildi').distinct()

    def get_customer(self, obj):
        return format_html("<b>{}</b><br/>{}", obj.user.first_name, obj.user.phone)

    get_customer.short_description = "Mijoz"

    actions = ['ship_out_cargos']

    @admin.action(description="Tanlangan yuklarni topshirish (🚚)")
    def ship_out_cargos(self, request, queryset):
        now = timezone.now()
        for group in queryset:
            group.payment_status = 'Topshirildi'
            group.delivered_admin = request.user
            group.save()
            cargos = group.selected_cargos.all()
            cargos.update(
                status='Topshirildi',
                delivered_at=now,
                delivered_admin=request.user,
                updated_by=request.user
            )
        self.message_user(request, f"{queryset.count()} ta guruh va ulardagi yuklar muvaffaqiyatli topshirildi.")