from datetime import datetime, timezone

from fastapi.templating import Jinja2Templates

from .config import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def timeago(value):
    if value is None:
        return ""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if value.tzinfo is not None:
        value = value.replace(tzinfo=None)
    seconds = (now - value).total_seconds()
    if seconds < 60:
        return "刚刚"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} 分钟前"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} 小时前"
    days = hours / 24
    if days < 30:
        return f"{int(days)} 天前"
    months = days / 30
    if months < 12:
        return f"{int(months)} 个月前"
    years = months / 12
    return f"{int(years)} 年前"


templates.env.filters["timeago"] = timeago


def render(request, name, current_user=None, status_code=200, **context):
    user = current_user if current_user is not None else getattr(request.state, "current_user", None)
    return templates.TemplateResponse(
        request,
        name,
        {"current_user": user, **context},
        status_code=status_code,
    )
