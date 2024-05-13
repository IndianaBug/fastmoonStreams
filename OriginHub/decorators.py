import backoff
from websockets.exceptions import WebSocketException
from .errors import websockets_heartbeats_errors, kafka_recoverable_errors, kafka_restart_errors, kafka_giveup_errors, aiohttp_recoverable_errors, kafka_send_errors

def keepalive_decorator(max_reconnect_retries):
    """ Pattern of keep alive for every exchange"""
    def decorator(func):
        @backoff.on_exception(backoff.expo,
                                WebSocketException,
                                max_tries=max_reconnect_retries)
        async def wrapper(*args, **kwargs):
            connection_data = kwargs.get('connection_data')
            websocket = kwargs.get('websocket')
            logger = kwargs.get('logger')
            id_ws = connection_data.get("id_ws", "unknown")
            exchange = connection_data.get("exchange")  
            
            if exchange == "kucoin":
                pingInterval, pingTimeout = args[0].get_kucoin_pingInterval(connection_data)
                args[0].kucoin_pp_intervals[id_ws] = {
                    "pingInterval": pingInterval,
                    "pingTimeout": pingTimeout
                }
            
            args[0].keep_alives_running[id_ws] = True
            
            while args[0].keep_alives_running.get(id_ws, False):
                try:
                    await func(websocket, connection_data, logger, *args, **kwargs)
                except aiohttp_recoverable_errors as e:
                    logger.exception("Keep-Alive error, connection closed: %s, ID_WS: %s", e, id_ws, exc_info=True)
                    args[0].KEEP_ALIVE_ERRORS.labels(error_type='recoverable_error', exchange=exchange, websocket_id=id_ws).inc()
                    raise
                except Exception as e:
                    logger.exception("Keep-Alive error, connection closed: %s, ID_WS: %s", e, id_ws, exc_info=True)
                    args[0].KEEP_ALIVE_DISCONNECTS.labels(websocket_id=id_ws, exchange=exchange).inc()
                    break
        return wrapper
    return decorator