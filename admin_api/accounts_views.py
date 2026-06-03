"""
Accounts bo'limi uchun to'liq API views.
admin_api/views.py ga qo'shing yoki alohida accounts_views.py sifatida saqlang.
"""
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from accounts.models import User, OTPCode, UserRelative


# ─── YORDAMCHI ───────────────────────────────────────────────

def _paginate(qs, request, size=30):
    page = int(request.GET.get("page", 1))
    total = qs.count()
    items = qs[(page - 1) * size: page * size]
    return items, total, page, (total + size - 1) // size


def _user_dict(u, request=None):
    d = {
        "id": u.id,
        "user_id": u.user_id or "",
        "phone": u.phone,
        "first_name": u.first_name or "",
        "last_name": u.last_name or "",
        "full_name": f"{u.first_name} {u.last_name}".strip() or u.phone,
        "jshshir": u.jshshir or "",
        "passport_series": u.passport_series or "",
        "birth_date": str(u.birth_date) if u.birth_date else "",
        "address": u.address or "",
        "status": u.status,
        "is_active": u.is_active,
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
        "rejection_reason": u.rejection_reason or "",
        "rejection_note": u.rejection_note or "",
        "date_joined": u.date_joined.strftime("%d.%m.%Y %H:%M"),
        "last_active": u.last_active.strftime("%d.%m.%Y %H:%M") if u.last_active else "",
        "cargo_count": u.cargos.count(),
    }
    if request:
        d["passport_front"] = request.build_absolute_uri(u.passport_front.url) if u.passport_front else None
        d["passport_back"] = request.build_absolute_uri(u.passport_back.url) if u.passport_back else None
    return d


def _next_user_id():
    max_num = 100
    for u in User.objects.filter(user_id__startswith="UTS-"):
        try:
            n = int(u.user_id.split("-")[1])
            if n > max_num:
                max_num = n
        except (IndexError, ValueError):
            pass
    return f"UTS-{max_num + 1:04d}"


# ─── OTP KODLAR ──────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def otp_list(request):
    """GET /api/admin/otp/"""
    qs = OTPCode.objects.select_related("user").order_by("-created_at")
    if q := request.GET.get("search", "").strip():
        qs = qs.filter(Q(user__phone__icontains=q) | Q(user__first_name__icontains=q) | Q(code__icontains=q))
    items, total, page, pages = _paginate(qs, request)
    results = [{
        "id": o.id,
        "code": o.code,
        "phone": o.user.phone,
        "user_name": f"{o.user.first_name} {o.user.last_name}".strip() or o.user.phone,
        "user_id": o.user.user_id or "-",
        "created_at": o.created_at.strftime("%d.%m.%Y %H:%M:%S"),
    } for o in items]
    return Response({"results": results, "total": total, "page": page, "pages": pages})


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def otp_delete(request, pk):
    """DELETE /api/admin/otp/<pk>/"""
    try:
        OTPCode.objects.get(pk=pk).delete()
        return Response({"ok": True})
    except OTPCode.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)


# ─── RO'YXATDAN O'TISH SO'ROVLARI ────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def application_list(request):
    """GET /api/admin/applications/  — pending + rejected"""
    qs = User.objects.filter(is_staff=False).exclude(status="approved").order_by("-date_joined")
    if s := request.GET.get("status"):
        qs = qs.filter(status=s)
    if q := request.GET.get("search", "").strip():
        qs = qs.filter(Q(phone__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(jshshir__icontains=q))
    items, total, page, pages = _paginate(qs, request)
    return Response({"results": [_user_dict(u, request) for u in items], "total": total, "page": page, "pages": pages})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def application_detail(request, pk):
    """GET /api/admin/applications/<pk>/"""
    try:
        u = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)
    return Response(_user_dict(u, request))


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def application_update(request, pk):
    """PATCH /api/admin/applications/<pk>/  — barcha maydonlarni tahrirlash"""
    try:
        u = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)

    fields = ["first_name", "last_name", "phone", "jshshir", "passport_series",
              "birth_date", "address", "status", "rejection_reason", "rejection_note", "user_id"]
    for f in fields:
        if f in request.data and request.data[f] != "":
            setattr(u, f, request.data[f])

    # Rasmlar
    if "passport_front" in request.FILES:
        u.passport_front = request.FILES["passport_front"]
    if "passport_back" in request.FILES:
        u.passport_back = request.FILES["passport_back"]

    u.save()
    return Response({"ok": True, "user": _user_dict(u, request)})


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def application_approve(request, pk):
    """PATCH /api/admin/applications/<pk>/approve/"""
    try:
        u = User.objects.get(pk=pk, is_staff=False)
    except User.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)

    if not u.user_id:
        u.user_id = _next_user_id()

    u.status = "approved"
    u.is_active = True
    u.rejection_reason = None
    u.rejection_note = None
    u.save()
    return Response({"ok": True, "user_id": u.user_id})


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def application_reject(request, pk):
    """PATCH /api/admin/applications/<pk>/reject/"""
    try:
        u = User.objects.get(pk=pk, is_staff=False)
    except User.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)

    u.status = "rejected"
    u.rejection_reason = request.data.get("reason", "other")
    u.rejection_note = request.data.get("note", "")
    u.save()
    return Response({"ok": True})


# ─── FOYDALANUVCHILAR ────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAdminUser])
def user_list(request):
    """GET /api/admin/users/"""
    qs = User.objects.filter(is_staff=False, status="approved").order_by("-date_joined")
    if q := request.GET.get("search", "").strip():
        qs = qs.filter(Q(phone__icontains=q) | Q(user_id__icontains=q) |
                       Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(jshshir__icontains=q))
    if active := request.GET.get("is_active"):
        qs = qs.filter(is_active=(active == "true"))
    items, total, page, pages = _paginate(qs, request)
    return Response({"results": [_user_dict(u) for u in items], "total": total, "page": page, "pages": pages})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def user_detail(request, pk):
    """GET /api/admin/users/<pk>/"""
    try:
        u = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)

    data = _user_dict(u, request)

    # Qarindoshlar
    relatives = []
    for r in u.relatives.all():
        relatives.append({
            "id": r.id,
            "full_name": r.full_name,
            "jshshir": r.jshshir,
            "passport_series": r.passport_series,
            "birth_date": str(r.birth_date) if r.birth_date else "",
            "phone": r.phone or "",
            "created_at": r.created_at.strftime("%d.%m.%Y"),
        })
    data["relatives"] = relatives

    # So'nggi yuklar
    from cargo.models import Cargo
    cargos = Cargo.objects.filter(user=u).order_by("-created_at")[:10]
    data["recent_cargos"] = [{
        "track_code": c.track_code,
        "status": c.status,
        "flight_name": c.flight_name or "-",
        "created_at": c.created_at.strftime("%d.%m.%Y"),
    } for c in cargos]

    return Response(data)


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def user_update(request, pk):
    """PATCH /api/admin/users/<pk>/  — barcha maydonlarni tahrirlash"""
    try:
        u = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)

    text_fields = ["first_name", "last_name", "phone", "jshshir",
                   "passport_series", "birth_date", "address", "user_id"]
    for f in text_fields:
        if f in request.data:
            setattr(u, f, request.data[f])

    # Boolean maydonlar
    if "is_active" in request.data:
        u.is_active = request.data["is_active"] in [True, "true", "True", "1"]
    if "is_staff" in request.data:
        u.is_staff = request.data["is_staff"] in [True, "true", "True", "1"]

    # Rasmlar
    if "passport_front" in request.FILES:
        u.passport_front = request.FILES["passport_front"]
    if "passport_back" in request.FILES:
        u.passport_back = request.FILES["passport_back"]

    # Parol
    if password := request.data.get("password", "").strip():
        if len(password) >= 6:
            u.set_password(password)
        else:
            return Response({"error": "Parol kamida 6 ta belgidan iborat bo'lishi kerak"}, status=400)

    u.save()
    return Response({"ok": True, "user": _user_dict(u, request)})


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def user_delete(request, pk):
    """DELETE /api/admin/users/<pk>/"""
    try:
        u = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)
    if u.is_superuser:
        return Response({"error": "Superuserni o'chirib bo'lmaydi"}, status=403)
    u.delete()
    return Response({"ok": True})


# ─── QARINDOSHLAR ────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAdminUser])
def relative_create(request, user_pk):
    """POST /api/admin/users/<user_pk>/relatives/"""
    try:
        u = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)

    r = UserRelative.objects.create(
        user=u,
        full_name=request.data.get("full_name", ""),
        jshshir=request.data.get("jshshir", ""),
        passport_series=request.data.get("passport_series", ""),
        birth_date=request.data.get("birth_date") or None,
        phone=request.data.get("phone", ""),
    )
    return Response({"ok": True, "id": r.id})


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def relative_delete(request, pk):
    """DELETE /api/admin/relatives/<pk>/"""
    try:
        UserRelative.objects.get(pk=pk).delete()
        return Response({"ok": True})
    except UserRelative.DoesNotExist:
        return Response({"error": "Topilmadi"}, status=404)
