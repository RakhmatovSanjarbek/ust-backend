import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def send_cargo_status_push(cargo):
    """Bitta yuk uchun push yuboradi va bazaga saqlaydi."""
    if not cargo.user:
        return

    token = getattr(cargo.user, 'fcm_token', None)
    title = _get_status_title(cargo.status)
    body = f"Trek: {cargo.track_code} | Reys: {cargo.flight_name or '-'}"

    # Bazaga saqlash
    _save_notification(
        user=cargo.user,
        title=title,
        body=body,
        notification_type=cargo.status,
        cargo_id=cargo.pk,
        track_code=cargo.track_code,
    )

    if not token:
        logger.warning(f"FCM token topilmadi: user={cargo.user.pk}")
        return

    _send_push(
        token=token,
        title=title,
        body=body,
        data={"cargo_id": str(cargo.pk), "track_code": cargo.track_code, "status": cargo.status}
    )


def send_flight_status_push(cargos, new_status):
    """
    Bir reys bo'yicha GURUHLANGAN push yuborish.
    Har bir foydalanuvchiga bitta xabar.
    """
    user_cargos = defaultdict(list)
    for cargo in cargos:
        if cargo.user:
            user_cargos[cargo.user].append(cargo)

    success_count = 0
    error_count = 0

    for user, user_cargo_list in user_cargos.items():
        if len(user_cargo_list) == 1:
            cargo = user_cargo_list[0]
            body = f"Trek: {cargo.track_code}"
            if cargo.flight_name:
                body += f" | Reys: {cargo.flight_name}"
            cargo_id = cargo.pk
            track_code = cargo.track_code
        else:
            flight_names = list({c.flight_name for c in user_cargo_list if c.flight_name})
            flight_str = ", ".join(flight_names) if flight_names else "-"
            body = f"{len(user_cargo_list)} ta yukingiz | Reys: {flight_str}"
            cargo_id = None
            track_code = None

        title = _get_status_title(new_status)

        # ✅ Har bir foydalanuvchi uchun bazaga saqlash
        _save_notification(
            user=user,
            title=title,
            body=body,
            notification_type=new_status,
            cargo_id=cargo_id,
            track_code=track_code,
        )

        token = getattr(user, 'fcm_token', None)
        if not token:
            logger.warning(f"FCM token topilmadi: user={user.pk}")
            error_count += 1
            continue

        result = _send_push(
            token=token,
            title=title,
            body=body,
            data={
                "status": new_status,
                "cargo_count": str(len(user_cargo_list)),
                "cargo_ids": ",".join(str(c.pk) for c in user_cargo_list),
            }
        )
        if result:
            success_count += 1
        else:
            error_count += 1

    logger.info(f"[PUSH] Status: {new_status} | ✅ {success_count} | ❌ {error_count}")
    return success_count, error_count


def _save_notification(user, title, body, notification_type, cargo_id=None, track_code=None):
    """Bildirishnomani bazaga saqlaydi."""
    try:
        from notifications.models import Notification
        Notification.objects.create(
            user=user,
            title=title,
            body=body,
            notification_type=notification_type,
            cargo_id=cargo_id,
            track_code=track_code,
        )
    except Exception as e:
        logger.error(f"Notification saqlashda xato: {e}")


def _get_status_title(status):
    titles = {
        'Omborda':     "📦 Yukingiz omborda",
        "Yo'lda":      "🚚 Yukingiz yo'lda",
        'Punktda':     "📍 Yukingiz punktda",
        'Topshirildi': "✅ Yukingiz topshirildi",
        'Kutilmoqda':  "⏳ Yukingiz kutilmoqda",
    }
    return titles.get(status, "📦 Yuk holati o'zgardi")


def _send_push(token, title, body, data=None):
    try:
        import firebase_admin
        from firebase_admin import messaging

        try:
            firebase_admin.get_app()
        except ValueError:
            logger.error("Firebase Admin SDK ishga tushurilmagan!")
            return False

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default", badge=1, content_available=True)
                )
            ),
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(sound="default", priority="high"),
            ),
        )

        messaging.send(message)
        logger.info(f"[PUSH ✅] token=...{token[-10:]} | {title}")
        return True

    except Exception as e:
        logger.error(f"[PUSH ❌] token=...{token[-10:]} | Xato: {e}")
        return False