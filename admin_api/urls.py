from django.urls import path
from . import views
from .admin_management_views import my_permissions, admin_list, admin_create, admin_detail

from .warehouse_views import (
    get_dollar_rate, set_dollar_rate,
    warehouse_user_search, warehouse_user_flights, warehouse_user_cargos,
    group_create, group_list, group_detail,
    payment_list as wh_payment_list,
    payment_approve as wh_payment_approve,
    payment_reject as wh_payment_reject,
    delivery_queue, deliver_group,
    deliver_without_payment,
    payment_stats,
)
from .accounts_views import (
    otp_list, otp_delete,
    application_list, application_detail, application_update,
    application_approve, application_reject,
    user_list, user_detail, user_update, user_delete,
    relative_create, relative_delete,
)
from .cargo_views import (
    cargo_list, cargo_create, cargo_import_excel,
    cargo_detail, cargo_update_status, cargo_bulk_status,
    cargo_all_ids, cargo_export_excel,
)

urlpatterns = [
    path("login/", views.admin_login),
    path("my-permissions/", my_permissions),

    # ── Admin boshqaruvi (faqat superuser / can_add_admin) ──
    path("admins/", admin_list),
    path("admins/create/", admin_create),
    path("admins/<int:pk>/", admin_detail),
    path("dashboard/", views.dashboard_stats),

    # OTP
    path("otp/", otp_list),
    path("otp/<int:pk>/", otp_delete),

    # Arizalar
    path("applications/", application_list),
    path("applications/<int:pk>/", application_detail),
    path("applications/<int:pk>/update/", application_update),
    path("applications/<int:pk>/approve/", application_approve),
    path("applications/<int:pk>/reject/", application_reject),

    # Foydalanuvchilar
    path("users/", user_list),
    path("users/<int:pk>/", user_detail),
    path("users/<int:pk>/update/", user_update),
    path("users/<int:pk>/delete/", user_delete),
    path("users/<int:user_pk>/relatives/", relative_create),
    path("relatives/<int:pk>/", relative_delete),

    # Yuklar
    path("cargos/", cargo_list),
    path("cargos/create/", cargo_create),
    path("cargos/import/", cargo_import_excel),
    path("cargos/bulk-status/", cargo_bulk_status),
    path("cargos/all-ids/", cargo_all_ids),
    path("cargos/export/", cargo_export_excel),
    path("cargos/<int:pk>/", cargo_detail),
    path("cargos/<int:pk>/status/", cargo_update_status),

    # Warehouse — Dollar kursi
    path("warehouse/dollar-rate/", get_dollar_rate),
    path("warehouse/dollar-rate/set/", set_dollar_rate),

    # Warehouse — Statistika (dashboard uchun)
    path("warehouse/stats/", payment_stats),

    # Warehouse — Foydalanuvchi qidirish
    path("warehouse/users/", warehouse_user_search),
    path("warehouse/users/<int:user_id>/flights/", warehouse_user_flights),
    path("warehouse/users/<int:user_id>/cargos/", warehouse_user_cargos),

    # Warehouse — Guruhlar
    path("warehouse/groups/", group_list),
    path("warehouse/groups/create/", group_create),
    path("warehouse/groups/<int:pk>/", group_detail),

    # Warehouse — To'lov tekshiruvlari
    path("warehouse/payments/", wh_payment_list),
    path("warehouse/payments/<int:pk>/approve/", wh_payment_approve),
    path("warehouse/payments/<int:pk>/reject/", wh_payment_reject),

    # Warehouse — Topshirish navbati (to'lov tasdiqlangan)
    path("warehouse/delivery/", delivery_queue),
    path("warehouse/delivery/<int:pk>/deliver/", deliver_group),

    # Warehouse — Ombordan to'lab topshirish (to'lovsiz)
    path("warehouse/delivery/<int:pk>/pay-and-deliver/", deliver_without_payment),

    # Dashboard uchun eski to'lovlar
    path("payments/", views.payment_list),
    path("payments/<int:pk>/approve/", views.payment_approve),
    path("payments/<int:pk>/reject/", views.payment_reject),
    path("payments/<int:pk>/deliver/", views.payment_deliver),

    # Reyslar
    path("flights/", views.flight_list),
    path("flights/create/", views.flight_create),
    path("flights/<int:pk>/", views.flight_detail),

    # Chat
    path("chat/users/", views.chat_users),
    path("chat/messages/<int:user_id>/", views.chat_messages),
    path("chat/reply/<int:user_id>/", views.chat_reply),

    # Kalkulator
    path("calc/", views.calc_list),
    path("calc/<int:pk>/reply/", views.calc_reply),

    # Kodsiz tovarlar
    path("unassigned/", views.unassigned_list),
    path("unassigned/import/", views.unassigned_import_excel),
    path("unassigned/create/", views.unassigned_create),
    path("unassigned/<int:pk>/", views.unassigned_delete),

    # Bildirishnomalar
    path("notifications/", views.notification_list),
    path("notifications/send/", views.notification_send),

    # Video
    path("videos/", views.video_list),
    path("videos/create/", views.video_create),
    path("videos/<int:pk>/", views.video_delete),

    # Sozlamalar
    path("settings/", views.settings_view),
    path("app-version/", views.app_version_view),
]
