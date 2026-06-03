"""
admin_api/admin_management_views.py
-------------------------------------
Admin qo'shish, tahrirlash, ruxsatlar boshqaruvi.
Faqat superuser yoki can_add_admin=True bo'lgan adminlar kirishi mumkin.
"""
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import User, AdminPermission


# ── Ruxsat tekshirish decorator ────────────────────────────

def require_permission(perm):
    """
    Decorator: superuser yoki berilgan ruxsati bor adminlar o'ta oladi.
    Foydalanish:
        @require_permission("can_add_admin")
        def my_view(request): ...
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return func(request, *args, **kwargs)
            try:
                p = request.user.admin_permission
                if getattr(p, perm, False):
                    return func(request, *args, **kwargs)
            except AdminPermission.DoesNotExist:
                pass
            return Response({"error": "Bu amalni bajarishga ruxsat yo'q"}, status=403)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


# ── Yordamchi ──────────────────────────────────────────────

def perm_dict(perm):
    """AdminPermission ob'ektini dict ga aylantirish"""
    if not perm:
        return None
    return {
        "can_dashboard":     perm.can_dashboard,
        "can_accounts":      perm.can_accounts,
        "can_warehouse":     perm.can_warehouse,
        "can_cargo":         perm.can_cargo,
        "can_flights":       perm.can_flights,
        "can_chat":          perm.can_chat,
        "can_calc":          perm.can_calc,
        "can_notifications": perm.can_notifications,
        "can_unassigned":    perm.can_unassigned,
        "can_videos":        perm.can_videos,
        "can_settings":      perm.can_settings,
        "can_add_admin":     perm.can_add_admin,
        "can_export":        perm.can_export,
        "can_bulk_actions":  perm.can_bulk_actions,
        "can_delete":        perm.can_delete,
        "note":              perm.note or "",
    }


def admin_dict(u):
    """Admin user ob'ektini dict ga aylantirish"""
    try:
        perm = u.admin_permission
    except AdminPermission.DoesNotExist:
        perm = None

    return {
        "id":            u.id,
        "phone":         u.phone,
        "name":          f"{u.first_name} {u.last_name}".strip() or u.phone,
        "first_name":    u.first_name,
        "last_name":     u.last_name,
        "is_superuser":  u.is_superuser,
        "is_active":     u.is_active,
        "date_joined":   u.date_joined.strftime("%d.%m.%Y %H:%M"),
        "last_active":   u.last_active.strftime("%d.%m.%Y %H:%M") if u.last_active else None,
        "permissions":   perm_dict(perm),
        "created_by":    str(perm.created_by) if perm and perm.created_by else "-",
    }


# ── ADMINLAR RO'YXATI ───────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
@require_permission("can_add_admin")
def admin_list(request):
    """GET /api/admin/admins/ — Barcha adminlar ro'yxati"""
    admins = User.objects.filter(is_staff=True).order_by("-date_joined")
    return Response([admin_dict(u) for u in admins])


# ── YANGI ADMIN QO'SHISH ────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAdminUser])
@require_permission("can_add_admin")
def admin_create(request):
    """
    POST /api/admin/admins/create/
    Body: {
        phone, password, first_name, last_name,
        permissions: { can_warehouse: true, ... },
        note: "..."
    }
    """
    phone      = request.data.get("phone", "").strip()
    password   = request.data.get("password", "").strip()
    first_name = request.data.get("first_name", "").strip()
    last_name  = request.data.get("last_name", "").strip()
    note       = request.data.get("note", "").strip()
    perms_data = request.data.get("permissions", {})

    if not phone:
        return Response({"error": "Telefon raqam kiritilmagan"}, status=400)
    if not password or len(password) < 6:
        return Response({"error": "Parol kamida 6 ta belgi bo'lishi kerak"}, status=400)
    if User.objects.filter(phone=phone).exists():
        return Response({"error": f"Bu telefon raqam allaqachon ro'yxatdan o'tgan: {phone}"}, status=400)

    # Admin user yaratish
    admin = User(
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        is_staff=True,
        is_active=True,
        status="approved",
    )
    admin.set_password(password)
    admin.save()

    # Ruxsatlar yaratish
    PERM_FIELDS = [
        "can_dashboard", "can_accounts", "can_warehouse", "can_cargo",
        "can_flights", "can_chat", "can_calc", "can_notifications",
        "can_unassigned", "can_videos", "can_settings",
        "can_add_admin", "can_export", "can_bulk_actions", "can_delete",
    ]
    perm_kwargs = {
        field: bool(perms_data.get(field, field == "can_dashboard"))
        for field in PERM_FIELDS
    }
    perm = AdminPermission.objects.create(
        admin=admin,
        note=note,
        created_by=request.user,
        **perm_kwargs,
    )

    return Response({
        "ok": True,
        "admin": admin_dict(admin),
        "message": f"✅ {phone} uchun admin yaratildi",
    })


# ── ADMIN TAHRIRLASH ────────────────────────────────────────

@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdminUser])
@require_permission("can_add_admin")
def admin_detail(request, pk):
    """GET/PATCH/DELETE /api/admin/admins/<pk>/"""
    try:
        admin = User.objects.get(pk=pk, is_staff=True)
    except User.DoesNotExist:
        return Response({"error": "Admin topilmadi"}, status=404)

    # Superuserga tegib bo'lmaydi (o'zidan boshqa)
    if admin.is_superuser and admin.pk != request.user.pk:
        return Response({"error": "Superuserga o'zgartirish kirita olmaysiz"}, status=403)

    if request.method == "GET":
        return Response(admin_dict(admin))

    if request.method == "DELETE":
        if admin.pk == request.user.pk:
            return Response({"error": "O'zingizni o'chirib bo'lmaydi"}, status=400)
        admin.delete()
        return Response({"ok": True})

    # PATCH
    if "first_name" in request.data:
        admin.first_name = request.data["first_name"]
    if "last_name" in request.data:
        admin.last_name = request.data["last_name"]
    if "is_active" in request.data:
        admin.is_active = bool(request.data["is_active"])
    if "password" in request.data:
        pwd = request.data["password"].strip()
        if len(pwd) < 6:
            return Response({"error": "Parol kamida 6 ta belgi"}, status=400)
        admin.set_password(pwd)
    admin.save()

    # Ruxsatlarni yangilash
    perms_data = request.data.get("permissions")
    if perms_data is not None:
        perm, _ = AdminPermission.objects.get_or_create(
            admin=admin,
            defaults={"created_by": request.user},
        )
        PERM_FIELDS = [
            "can_dashboard", "can_accounts", "can_warehouse", "can_cargo",
            "can_flights", "can_chat", "can_calc", "can_notifications",
            "can_unassigned", "can_videos", "can_settings",
            "can_add_admin", "can_export", "can_bulk_actions", "can_delete",
        ]
        for field in PERM_FIELDS:
            if field in perms_data:
                setattr(perm, field, bool(perms_data[field]))
        if "note" in request.data:
            perm.note = request.data["note"]
        perm.save()

    return Response({"ok": True, "admin": admin_dict(admin)})


# ── JORIY ADMIN RUXSATLARI ─────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def my_permissions(request):
    """
    GET /api/admin/my-permissions/
    Joriy login qilgan admin ruxsatlarini qaytaradi.
    Frontend bu ma'lumot asosida menu va tugmalarni ko'rsatadi.
    """
    if request.user.is_superuser:
        # Superuserna hamma narsa ruxsat
        return Response({
            "is_superuser": True,
            "permissions": {
                "can_dashboard":     True,
                "can_accounts":      True,
                "can_warehouse":     True,
                "can_cargo":         True,
                "can_flights":       True,
                "can_chat":          True,
                "can_calc":          True,
                "can_notifications": True,
                "can_unassigned":    True,
                "can_videos":        True,
                "can_settings":      True,
                "can_add_admin":     True,
                "can_export":        True,
                "can_bulk_actions":  True,
                "can_delete":        True,
            }
        })

    try:
        perm = request.user.admin_permission
        return Response({
            "is_superuser": False,
            "permissions": perm_dict(perm),
        })
    except AdminPermission.DoesNotExist:
        # Ruxsat yo'q — faqat dashboard
        return Response({
            "is_superuser": False,
            "permissions": {
                "can_dashboard": True,
                "can_accounts": False, "can_warehouse": False,
                "can_cargo": False, "can_flights": False,
                "can_chat": False, "can_calc": False,
                "can_notifications": False, "can_unassigned": False,
                "can_videos": False, "can_settings": False,
                "can_add_admin": False, "can_export": False,
                "can_bulk_actions": False, "can_delete": False,
            }
        })
