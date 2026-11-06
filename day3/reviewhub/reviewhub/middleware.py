import logging

# LOGGING у settings не налаштовано, тому цей логер не має handler-ів. WARNING і вище
# все одно потрапляє в stderr через logging.lastResort, а INFO вже ні.
logger = logging.getLogger(__name__)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # request.user з'являється лише після AuthenticationMiddleware, тому в MIDDLEWARE
        # цей клас стоїть нижче за неї.
        logger.warning("-> %s %s user=%s", request.method, request.path, request.user)
        response = self.get_response(request)
        logger.warning("<- %s %s", request.path, response.status_code)
        return response
