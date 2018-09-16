import os
import re

from django.views import View
from django.http import HttpResponse as HR, JsonResponse as JR

from ..executors import AccountExecutor, set_message

# Use cases
actions = [
    ("create_account", "^criar$"),
    ("cancel_account", "^cancelar$"),
    ("transfer_money", "^transferir 8[2-7][0-9]{7} [0-9]+$"),
    ("check_balance" , "^saldo$"),
]

EMPTY_MSG = INVALID_FORMAT = """Formato de mensagem inválido. 
Opções disponíveis: 
- Criar (Para criar conta) 
- Saldo (Para consultar o saldo corrente) 
- Cancelar (Para cancelar a sua conta) 
- Tranferir <Número> <Valor> (Para transferir 
dinheiro para o número de destino)"""

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
                return JR(set_message(EMPTY_MSG))

            for action, regex in actions:
                if re.match(regex, content.lower()):
                    executor = AccountExecutor(from_number, content)
                    return getattr(executor, action)()

            return JR(set_message(INVALID_FORMAT))
        else:
            return HR("Event not implemented", 'text/plain', 403)