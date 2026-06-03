"""
admin_api/warehouse_views.py  —  v2
-------------------------------------
1. Dollar kursi — WarehouseSettings.dollar_rate (DB)
2. Guruh yaratish — Punktga qabul
3. To'lov tekshiruvlari
4. Topshirish navbati:
   A) To'lov tasdiqlangan → faqat "Topshirildi" tugmasi
   B) To'lovsiz topshirish → naqd+karta dialog
"""
import json
from django.utils import timezone
from django.db.models import Q, Sum, Count
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from cargo.models import Cargo
from warehouse.models import ArrivedGroup
from accounts.models import User
from services.models import WarehouseSettings


# ─── YORDAMCHI ───────────────────────────────────────────────

def get_rate():
    obj, _ = WarehouseSettings.objects.get_or_create(pk=1, defaults={
        "china_avia_phone": "", "china_avia_address": "",
        "china_avia_price": 0, "china_avia_term": "",
        "china_auto_phone": "", "china_auto_address": "",
        "china_auto_price": 0, "china_auto_term": "",
        "contact_telegram": "", "contact_instagram": "",
        "contact_phone": "", "dollar_rate": 12700,
    })
    return float(obj.dollar_rate or 12700)


def group_dict(g, request=None):
    rate = get_rate()
    usd = float(g.total_price)
    summa = round(usd * rate)
    return {
        "id": g.id,
        "receipt_code": g.receipt_code,
        "user_id": g.user.user_id or "-",
        "user_name": f"{g.user.first_name} {g.user.last_name}".strip() or g.user.phone,
        "user_phone": g.user.phone,
        "total_weight": float(g.total_weight),
        "total_price_usd": usd,
        "total_price_sum": summa,
        "dollar_rate": rate,
        "payment_status": g.payment_status,
        "delivery_method": g.delivery_method or "-",
        "delivery_address": g.delivery_address or "-",
        "cargo_count": g.selected_cargos.count(),
        "admin_note": g.admin_note or "",
        "cash_amount": float(g.cash_amount) if g.cash_amount else None,
        "card_amount": float(g.card_amount) if g.card_amount else None,
        "delivered_at": g.delivered_at.strftime("%d.%m.%Y %H:%M") if g.delivered_at else None,
        "image": request.build_absolute_uri(g.image.url) if request and g.image else None,
        "payment_check": request.build_absolute_uri(g.payment_check.url) if request and g.payment_check else None,
        "created_at": g.created_at.strftime("%d.%m.%Y %H:%M"),
        "created_by": str(g.created_by) if g.created_by else "-",
    }


def _paginate(qs, request, size=30):
    page = int(request.GET.get("page", 1))
    total = qs.count()
    items = qs[(page - 1) * size: page * size]
    return items, total, page, (total + size - 1) // size


# ─── DOLLAR KURSI ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_dollar_rate(request):
    """GET /api/admin/warehouse/dollar-rate/"""
    obj, _ = WarehouseSettings.objects.get_or_create(pk=1, defaults={
        "china_avia_phone": "", "china_avia_address": "",
        "china_avia_price": 0, "china_avia_term": "",
        "china_auto_phone": "", "china_auto_address": "",
        "china_auto_price": 0, "china_auto_term": "",
        "contact_telegram": "", "contact_instagram": "",
        "contact_phone": "", "dollar_rate": 12700,
    })
    return Response({
        "rate": float(obj.dollar_rate or 12700),
        "updated": obj.dollar_rate_updated_at.strftime("%d.%m.%Y %H:%M") if obj.dollar_rate_updated_at else None,
    })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def set_dollar_rate(request):
    """POST /api/admin/warehouse/dollar-rate/set/  { rate: 12750 }"""
    try:
        rate = float(request.data.get("rate", 0))
        if rate <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return Response({"error": "Noto'g'ri kurs kiritildi"}, status=400)

    obj, _ = WarehouseSettings.objects.get_or_create(pk=1, defaults={
        "china_avia_phone": "", "china_avia_address": "",
        "china_avia_price": 0, "china_avia_term": "",
        "china_auto_phone": "", "china_auto_address": "",
        "china_auto_price": 0, "china_auto_term": "",
        "contact_telegram": "", "contact_instagram": "",
        "contact_phone": "",
    })
    obj.dollar_rate = rate
    obj.dollar_rate_updated_at = timezone.now()
    obj.save()
    return Response({
        "ok": True,
        "rate": rate,
        "updated": obj.dollar_rate_updated_at.strftime("%d.%m.%Y %H:%M"),
    })


# ─── FOYDALANUVCHI QIDIRISH ───────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def warehouse_user_search(request):
    """GET /api/admin/warehouse/users/?q=alisher"""
    q = request.GET.get("q", "").strip()
    qs = User.objects.filter(is_staff=False, status="approved")
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(phone__icontains=q) | Q(user_id__icontains=q)
        )
    return Response([{
        "id": u.id, "user_id": u.user_id or "-",
        "name": f"{u.first_name} {u.last_name}".strip() or u.phone,
        "phone": u.phone,
    } for u in qs.order_by("-date_joined")[:20]])


@api_view(["GET"])
@permission_classes([IsAdminUser])
def warehouse_user_flights(request, user_id):
    """GET /api/admin/warehouse/users/<id>/flights/"""
    flights = (
        Cargo.objects.filter(user_id=user_id, status="Yo'lda")
        .exclude(flight_name__isnull=True).exclude(flight_name="")
        .values_list("flight_name", flat=True).distinct()
    )
    return Response(list(flights))


@api_view(["GET"])
@permission_classes([IsAdminUser])
def warehouse_user_cargos(request, user_id):
    """GET /api/admin/warehouse/users/<id>/cargos/?flight=R-125"""
    flight = request.GET.get("flight", "")
    qs = Cargo.objects.filter(user_id=user_id, status="Yo'lda")
    if flight:
        qs = qs.filter(flight_name=flight)
    return Response([{
        "id": c.id, "track_code": c.track_code,
        "flight_name": c.flight_name or "-",
        "transport_type": c.transport_type or "-",
        "created_at": c.created_at.strftime("%d.%m.%Y"),
    } for c in qs.order_by("track_code")])


# ─── GURUH YARATISH ───────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def group_create(request):
    """POST /api/admin/warehouse/groups/create/"""
    user_id = request.data.get("user_id")
    flight_name = request.data.get("flight_name", "").strip()
    total_weight = float(request.data.get("total_weight", 0) or 0)
    total_price = float(request.data.get("total_price", 0) or 0)

    if not user_id:
        return Response({"error": "Foydalanuvchi tanlanmagan"}, status=400)
    if not flight_name:
        return Response({"error": "Reys nomi kiritilmagan"}, status=400)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "Foydalanuvchi topilmadi"}, status=404)

    cargo_ids = []
    try:
        raw = request.data.get("cargo_ids", "[]")
        cargo_ids = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        pass

    new_track_codes = []
    raw_codes = request.data.get("new_track_codes", "").strip()
    if raw_codes:
        new_track_codes = [c.strip() for c in raw_codes.replace(",", "\n").split("\n") if c.strip()]

    if not cargo_ids and not new_track_codes:
        return Response({"error": "Kamida bitta yuk tanlang yoki trek kodi kiriting"}, status=400)

    receipt_code = f"{flight_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"

    group = ArrivedGroup(
        user=user, receipt_code=receipt_code,
        total_weight=total_weight, total_price=total_price,
        payment_status="To'lov kutilmoqda", created_by=request.user,
    )
    if "image" in request.FILES:
        group.image = request.FILES["image"]
    group.save()

    push_ids = []
    if cargo_ids:
        cargos = Cargo.objects.filter(pk__in=cargo_ids, status="Yo'lda")
        group.selected_cargos.set(cargos)
        cargos.update(status="Punktda", arrived_group=group, arrived_admin=request.user)
        push_ids.extend(list(cargos.values_list("pk", flat=True)))

    new_count = 0
    for code in new_track_codes:
        cargo, created = Cargo.objects.get_or_create(
            track_code=code,
            defaults={"user": user, "flight_name": flight_name, "status": "Punktda",
                      "arrived_group": group, "arrived_admin": request.user}
        )
        if not created:
            cargo.status = "Punktda"
            cargo.arrived_group = group
            cargo.arrived_admin = request.user
            cargo._skip_push_signal = True
            cargo.save()
        group.selected_cargos.add(cargo)
        push_ids.append(cargo.pk)
        new_count += 1

    if push_ids:
        try:
            from utils.push_service import send_flight_status_push
            push_cargos = list(Cargo.objects.filter(pk__in=push_ids).select_related("user"))
            send_flight_status_push(push_cargos, "Punktda")
        except Exception as e:
            print(f"Push xatosi: {e}")

    rate = get_rate()
    return Response({
        "ok": True, "group_id": group.id,
        "receipt_code": receipt_code,
        "total_cargos": len(cargo_ids) + new_count,
        "total_price_usd": total_price,
        "total_price_sum": round(total_price * rate),
        "dollar_rate": rate,
    })


# ─── GURUHLAR RO'YXATI ────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def group_list(request):
    """GET /api/admin/warehouse/groups/"""
    qs = ArrivedGroup.objects.select_related("user").order_by("-created_at")
    if s := request.GET.get("status"):
        qs = qs.filter(payment_status=s)
    if q := request.GET.get("search", "").strip():
        qs = qs.filter(
            Q(receipt_code__icontains=q) | Q(user__user_id__icontains=q) |
            Q(user__phone__icontains=q) | Q(user__first_name__icontains=q)
        )
    items, total, page, pages = _paginate(qs, request)
    return Response({
        "results": [group_dict(g, request) for g in items],
        "total": total, "page": page, "pages": pages,
        "dollar_rate": get_rate(),
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def group_detail(request, pk):
    """GET /api/admin/warehouse/groups/<pk>/"""
    try:
        g = ArrivedGroup.objects.select_related("user").get(pk=pk)
    except ArrivedGroup.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)
    data = group_dict(g, request)
    data["cargos"] = [{
        "id": c.id, "track_code": c.track_code,
        "flight_name": c.flight_name or "-",
        "transport_type": c.transport_type or "-",
        "status": c.status,
    } for c in g.selected_cargos.all()]
    return Response(data)


# ─── TO'LOV TEKSHIRUVLARI ─────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def payment_list(request):
    """GET /api/admin/warehouse/payments/"""
    qs = ArrivedGroup.objects.select_related("user").order_by("-created_at")
    if s := request.GET.get("status"):
        qs = qs.filter(payment_status=s)
    if q := request.GET.get("search", "").strip():
        qs = qs.filter(
            Q(receipt_code__icontains=q) | Q(user__user_id__icontains=q) | Q(user__phone__icontains=q)
        )
    items, total, page, pages = _paginate(qs, request)
    return Response({
        "results": [group_dict(g, request) for g in items],
        "total": total, "page": page, "pages": pages,
    })


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def payment_approve(request, pk):
    try:
        g = ArrivedGroup.objects.get(pk=pk)
    except ArrivedGroup.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)
    g.payment_status = "To'lov tasdiqlandi"
    g.admin_note = f"Tasdiqlandi ✅ — {request.user} — {timezone.now().strftime('%d.%m.%Y %H:%M')}"
    g.save()
    return Response({"ok": True})


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def payment_reject(request, pk):
    try:
        g = ArrivedGroup.objects.get(pk=pk)
    except ArrivedGroup.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)
    g.payment_status = "To'lov rad etildi"
    g.admin_note = request.data.get("note", "Rad etildi ❌")
    g.save()
    return Response({"ok": True})


# ─── TOPSHIRISH NAVBATI ───────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def delivery_queue(request):
    """GET /api/admin/warehouse/delivery/
    To'lov tasdiqlangan guruhlar (topshirish kutilmoqda)
    """
    qs = ArrivedGroup.objects.select_related("user").filter(
        payment_status="To'lov tasdiqlandi"
    ).order_by("-created_at")
    if q := request.GET.get("search", "").strip():
        qs = qs.filter(
            Q(receipt_code__icontains=q) | Q(user__user_id__icontains=q) | Q(user__phone__icontains=q)
        )
    items, total, page, pages = _paginate(qs, request)
    return Response({
        "results": [group_dict(g, request) for g in items],
        "total": total, "page": page, "pages": pages,
    })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def deliver_group(request, pk):
    """
    POST /api/admin/warehouse/delivery/<pk>/deliver/
    Body: { cash_amount, card_amount, note }

    Ikki holatda ishlaydi:
    A) To'lov tasdiqlangan — cash/card shart emas
    B) To'lovsiz topshirish — cash + card kiritiladi
    """
    try:
        g = ArrivedGroup.objects.get(pk=pk)
    except ArrivedGroup.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)

    cash = request.data.get("cash_amount")
    card = request.data.get("card_amount")
    note = request.data.get("note", "").strip()

    cash_val = float(cash) if cash is not None else None
    card_val = float(card) if card is not None else None

    rate = get_rate()
    total_sum = round(float(g.total_price) * rate)

    g.payment_status = "Topshirildi"
    g.delivered_admin = request.user
    g.delivered_at = timezone.now()
    # Har doim cash/card saqlaymiz — dashboard statistikasi uchun
    if cash_val is not None:
        try: g.cash_amount = cash_val
        except Exception: pass
    if card_val is not None:
        try: g.card_amount = card_val
        except Exception: pass

    note_parts = [f"Topshirildi ✅ — {request.user} — {g.delivered_at.strftime('%d.%m.%Y %H:%M')}"]
    if cash_val is not None or card_val is not None:
        note_parts.append(f"Naqd: {(cash_val or 0):,.0f} so'm | Karta: {(card_val or 0):,.0f} so'm")
    if note:
        note_parts.append(f"Izoh: {note}")
    g.admin_note = "\n".join(note_parts)
    g.save()

    cargos = g.selected_cargos.all()
    cargo_ids = list(cargos.values_list("pk", flat=True))
    cargos.update(
        status="Topshirildi",
        delivered_at=g.delivered_at,
        delivered_admin=request.user,
        updated_by=request.user,
    )

    try:
        import threading
        from utils.push_service import send_flight_status_push
        push_cargos = list(Cargo.objects.filter(pk__in=cargo_ids).select_related("user"))
        t = threading.Thread(target=send_flight_status_push, args=(push_cargos, "Topshirildi"), daemon=True)
        t.start()
    except Exception as e:
        print(f"Push xatosi: {e}")

    return Response({
        "ok": True,
        "delivered_cargos": len(cargo_ids),
        "cash_amount": cash_val,
        "card_amount": card_val,
        "total_sum": total_sum,
    })


# ─── TO'LOVSIZ TOPSHIRISH (Ombordan to'lab ketish) ───────────

@api_view(["POST"])
@permission_classes([IsAdminUser])
def deliver_without_payment(request, pk):
    """
    POST /api/admin/warehouse/delivery/<pk>/pay-and-deliver/
    Foydalanuvchi omborga kelib to'laydi, keyin yukni oladi.
    Body: { cash_amount, card_amount, note }
    """
    try:
        g = ArrivedGroup.objects.get(pk=pk)
    except ArrivedGroup.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)

    cash_val = float(request.data.get("cash_amount", 0) or 0)
    card_val = float(request.data.get("card_amount", 0) or 0)
    note = request.data.get("note", "").strip()

    if cash_val == 0 and card_val == 0:
        return Response({"error": "To'lov miqdori kiritilmagan"}, status=400)

    rate = get_rate()
    total_sum = round(float(g.total_price) * rate)

    g.payment_status = "Topshirildi"
    g.delivered_admin = request.user
    g.delivered_at = timezone.now()
    try:
        g.cash_amount = cash_val
        g.card_amount = card_val
    except Exception:
        pass
    g.admin_note = (
        f"Ombordan to'lab topshirildi ✅ — {request.user}\n"
        f"Naqd: {cash_val:,.0f} so'm | Karta: {card_val:,.0f} so'm\n"
        f"Jami: {total_sum:,.0f} so'm"
        + (f"\nIzoh: {note}" if note else "")
    )
    g.save()

    cargos = g.selected_cargos.all()
    cargo_ids = list(cargos.values_list("pk", flat=True))
    cargos.update(
        status="Topshirildi",
        delivered_at=g.delivered_at,
        delivered_admin=request.user,
        updated_by=request.user,
    )

    try:
        import threading
        from utils.push_service import send_flight_status_push
        push_cargos = list(Cargo.objects.filter(pk__in=cargo_ids).select_related("user"))
        t = threading.Thread(target=send_flight_status_push, args=(push_cargos, "Topshirildi"), daemon=True)
        t.start()
    except Exception as e:
        print(f"Push xatosi: {e}")

    return Response({
        "ok": True, "delivered_cargos": len(cargo_ids),
        "cash_amount": cash_val, "card_amount": card_val, "total_sum": total_sum,
    })


# ─── DASHBOARD STATISTIKASI ───────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def payment_stats(request):
    """
    GET /api/admin/warehouse/stats/
    Dashboard uchun to'lov statistikasi:
    - confirmed: ilovadan to'langan (payment_check bor, admin tasdiqlagan)
    - kassa: punktda to'lab ketgan (cash_amount/card_amount bor)
    - jami: ikkalasi birgalikda
    """
    import datetime
    now = timezone.now()
    rate = get_rate()

    def calc_period(qs):
        """
        Bir period uchun statistika.
        confirmed = ilovadan to'langan (payment_check bor)
        kassa = punktdan to'lagan (cash_amount yoki card_amount bor)
        """
        all_groups = list(qs.values("total_price", "cash_amount", "card_amount", "payment_check"))

        confirmed_usd = 0.0
        kassa_cash = 0.0
        kassa_card = 0.0
        count = len(all_groups)

        for g in all_groups:
            usd = float(g["total_price"] or 0)
            cash = float(g["cash_amount"] or 0)
            card = float(g["card_amount"] or 0)

            if cash > 0 or card > 0:
                # Punktdan to'lagan — kassa
                kassa_cash += cash
                kassa_card += card
            else:
                # Ilovadan to'lagan — tasdiqlangan
                confirmed_usd += usd

        confirmed_sum = round(confirmed_usd * rate)
        kassa_total = round(kassa_cash + kassa_card)
        total_sum = confirmed_sum + kassa_total

        return {
            "total_usd": confirmed_usd,
            "total_sum": total_sum,
            "confirmed_usd": confirmed_usd,
            "confirmed_sum": confirmed_sum,
            "kassa_cash": kassa_cash,
            "kassa_card": kassa_card,
            "kassa_total": kassa_total,
            "count": count,
        }

    delivered = ArrivedGroup.objects.filter(payment_status="Topshirildi")

    # Bugun
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today = calc_period(delivered.filter(
        Q(delivered_at__gte=today_start) |
        Q(delivered_at__isnull=True, created_at__gte=today_start)
    ))

    # Bu hafta
    week_start = now - datetime.timedelta(days=7)
    week = calc_period(delivered.filter(
        Q(delivered_at__gte=week_start) |
        Q(delivered_at__isnull=True, created_at__gte=week_start)
    ))

    # Bu oy
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month = calc_period(delivered.filter(
        Q(delivered_at__gte=month_start) |
        Q(delivered_at__isnull=True, created_at__gte=month_start)
    ))

    # Jami
    total = calc_period(delivered)

    # Kutilayotganlar
    pending_sum = ArrivedGroup.objects.exclude(
        payment_status="Topshirildi"
    ).aggregate(t=Sum("total_price"))["t"] or 0

    return Response({
        "today": today,
        "week": week,
        "month": month,
        "total": total,
        "pending_usd": float(pending_sum),
        "pending_sum": round(float(pending_sum) * rate),
        "dollar_rate": rate,
    })
