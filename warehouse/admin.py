from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from cargo.models import Cargo
from warehouse.models import ArrivedGroup, PaymentRequest, DeliveryQueue
from accounts.models import User


@admin.register(ArrivedGroup)
class ArrivedGroupAdmin(admin.ModelAdmin):
    list_display = ('receipt_code', 'user', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'user')
    search_fields = ('receipt_code', 'user__phone', 'user__first_name')
    readonly_fields = ('display_group_image', 'display_payment_check', 'total_weight', 'total_price')

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('user', 'receipt_code', 'payment_status')
        }),
        ('Yuklar', {
            'fields': ('selected_cargos',)
        }),
        ('To\'lov va Yetkazish', {
            'fields': ('total_weight', 'total_price', 'image', 'payment_check', 'delivery_method', 'delivery_address')
        }),
        ('Admin ma\'lumotlari', {
            'fields': ('admin_note', 'created_by', 'delivered_admin'),
            'classes': ('collapse',)
        }),
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
            path('create-group/', self.admin_site.admin_view(self.create_group_view), name='arrived_group_create'),
            path('api/users/', self.admin_site.admin_view(self.api_users), name='warehouse_api_users'),
            path('api/flights/<int:user_id>/', self.admin_site.admin_view(self.api_flights),
                 name='warehouse_api_flights'),
            path('api/cargos/<int:user_id>/<str:flight_name>/', self.admin_site.admin_view(self.api_cargos),
                 name='warehouse_api_cargos'),
            path('api/create-group/', self.admin_site.admin_view(self.api_create_group),
                 name='warehouse_api_create_group'),
        ]
        return custom_urls + urls

    def create_group_view(self, request):
        context = {
            'title': 'Yangi guruh yaratish',
            'opts': self.model._meta,
            'has_view_permission': True,
            'has_add_permission': True,
        }
        return TemplateResponse(request, 'admin/warehouse/create_group.html', context)

    def api_users(self, request):
        users = User.objects.filter(is_staff=False).order_by('-date_joined')
        data = []
        for user in users:
            data.append({
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}".strip() or user.phone,
                'phone': user.phone,
                'user_id': user.user_id or 'ID yo\'q',
            })
        return JsonResponse(data, safe=False)

    def api_flights(self, request, user_id):
        cargos = Cargo.objects.filter(user_id=user_id, status="Yo'lda").exclude(flight_name__isnull=True).exclude(
            flight_name='').values('flight_name').distinct()
        flights = [c['flight_name'] for c in cargos if c['flight_name']]
        return JsonResponse(flights, safe=False)

    def api_cargos(self, request, user_id, flight_name):
        cargos = Cargo.objects.filter(
            user_id=user_id,
            flight_name=flight_name,
            status="Yo'lda"
        ).values('id', 'track_code', 'flight_name', 'status')
        return JsonResponse(list(cargos), safe=False)

    @method_decorator(csrf_exempt)
    def api_create_group(self, request):
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            user_id = data.get('user_id')
            receipt_code = data.get('receipt_code')
            cargo_ids = data.get('cargo_ids', [])

            if not user_id or not receipt_code:
                return JsonResponse({'error': 'Foydalanuvchi va Res kod kiritilishi shart'}, status=400)

            if not cargo_ids:
                return JsonResponse({'error': 'Hech qanday yuk tanlanmagan'}, status=400)

            try:
                with transaction.atomic():
                    user = get_object_or_404(User, id=user_id)

                    # Tanlangan yuklarni olish
                    cargos = Cargo.objects.filter(id__in=cargo_ids, status="Yo'lda")

                    if not cargos.exists():
                        return JsonResponse({'error': 'Tanlangan yuklar topilmadi yoki ular Yo\'lda emas'}, status=400)

                    # Jami og'irlik va summani hisoblash (agar mavjud bo'lsa)
                    total_weight = sum(float(c.weight or 0) for c in cargos)
                    total_price = sum(float(c.price or 0) for c in cargos)

                    # Guruh yaratish
                    group = ArrivedGroup.objects.create(
                        user=user,
                        receipt_code=receipt_code,
                        total_weight=total_weight,
                        total_price=total_price,
                        created_by=request.user,
                        payment_status='To\'lov kutilmoqda'
                    )

                    # Yuklarni qo'shish
                    group.selected_cargos.set(cargos)

                    # Statusni 'Punktda' ga o'zgartirish
                    cargos.update(status='Punktda', arrived_group=group, arrived_admin=request.user)

                    return JsonResponse({
                        'status': 'success',
                        'group_id': group.id,
                        'message': f'Guruh muvaffaqiyatli yaratildi! {len(cargo_ids)} ta yuk qo\'shildi.'
                    })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'error': 'Method not allowed'}, status=405)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        if not change:
            obj.selected_cargos.all().update(
                status='Punktda',
                arrived_group=obj,
                arrived_admin=request.user
            )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


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