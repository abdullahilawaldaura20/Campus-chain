from extensions import db
from models import Notification


def notify(user_id, type_, content, link_id=None):
    """
    Create an in-app notification. Called from other routes whenever
    something notification-worthy happens (new message, buy request,
    sale completed, etc.) — see routes/messages.py, routes/products.py.
    """
    note = Notification(user_id=user_id, type=type_, content=content, link_id=link_id)
    db.session.add(note)
    db.session.commit()
    return note
