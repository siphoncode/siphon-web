
import json
import os
import pika

APP_NOTIFICATIONS_EXCHANGE = 'siphon.apps.notifications'


def _connect():
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=os.environ.get('RABBITMQ_PORT_5672_TCP_ADDR', 'localhost'),
        port=int(os.environ.get('RABBITMQ_PORT_5672_TCP_PORT', 5672)),
        ssl=False
    ))

def post_notification(obj):
    payload = json.dumps(obj)

    # Don't bother conencting in dev/testing mode.
    if os.environ.get('SIPHON_ENV') == 'dev':
        return

    conn = _connect()
    channel = conn.channel()
    channel.exchange_declare(
        exchange=APP_NOTIFICATIONS_EXCHANGE,
        exchange_type='fanout',
        durable=True,
        auto_delete=False,
        internal=False
    )
    channel.basic_publish(
        exchange=APP_NOTIFICATIONS_EXCHANGE,
        routing_key='',
        body=payload
    )
    conn.close()
