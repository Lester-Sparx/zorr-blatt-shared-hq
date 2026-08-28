from __future__ import annotations
from .router import route_message

def handle_webhook(envelope, github, executor, config):
    return route_message(envelope, github, executor, config)
