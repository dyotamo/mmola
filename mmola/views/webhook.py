import os
import re

from django.views import View
from django.http import HttpResponse as HR

from ..executors import AccountExecutor

# Use cases
actions = [
    ("create_account", "^criar$"),
    ("cancel_account", "^cancelar$"),
    ("transfer_money", "^transferir 8[2-7][0-9]{7} [0-9]+$"),
    ("check_balance" , "^saldo$"),
    ("deposit_money" , "^depositar 8[2-7][0-9]{7} [0-9]+$"),
    ("withdraw_money", "^levantar 8[2-7][0-9]{7} [0-9]+$")
]

class Listener(View):
    """ Telerivet listener for incomming messages """
    def post(self, request):
        webhook_secret = os.environ["WEBHOOK_SECRET"]
        
        if request.POST.get('secret') != webhook_secret:
            return HR("Invalid webhook secret", 'text/plain', 403)

        if request.POST.get('event') == 'incoming_message':
            from_number = request.POST.get('from_number')
            content = request.POST.get('content')

            if not content:
                return HR("Empty content", 'text/plain', 403)

            for action, regex in actions:
                if re.match(regex, content):
                    executor = AccountExecutor(from_number, content)
                    method   = getattr(executor, action)
                    
                    # Invoke method by reflection
                    return method()

            return HR("Invalid action (show actions list)", 'text/plain', 404)
        else:
            return HR("Event not implemented", 'text/plain', 403)