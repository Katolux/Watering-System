from flask import Blueprint, render_template

from gardenhub.services.notifications import (
    get_notification_feed,
    unavailable_notification_feed,
)


notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications")
def notifications():
    try:
        feed = get_notification_feed()
    except Exception:
        feed = unavailable_notification_feed()
    return render_template("notifications.html", notification_feed=feed)
