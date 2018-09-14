import re

from django.views import View
from django.http import HttpResponse as HR, JsonResponse as JR
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.humanize.templatetags.humanize import intcomma

from ..models import Account

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
        webhook_secret = 'xyz'
        
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

class AccountExecutor:
    
    NO_BALANCE = 0
    OK         = 1
    ZERO       = 2
    
    def __init__(self, from_number, content):
        self.from_number = from_number
        self.content     = content

    def _get_active_account(self, account_number):
        return Account.objects.get(contact=account_number, active=True)

    def _update_balance(self, source, target, amount):
        if amount == 0:
            return self.ZERO

        # 2 é o valor da comissão do movimento
        if s_balance == 0 or s_balance-amount < 2:
            return self.NO_BALANCE

        with transaction.atomic():
            source.balance -= amount; target.balance += amount
            source.save(); target.save()

            # TODO Send message to target
            return self.OK

    def _activate_account(self, account, state):
        account.active = state
        account.save()

    def _set_message(self, message):
        return {'messages': [{'content': message}]}

    def _format_account(self, plain_account):
        return "+258{}".format(plain_account)

    def create_account(self):
        try:
            _, created = Account.objects.get_or_create(contact=self.from_number)
            if created:
                return JR(self._set_message("Registado com sucesso no sistema"))
            return JR(self._set_message("Usuário já existe no sistema"))
        except ValidationError as e:
            return JR(self._set_message(str(e)))

    def cancel_account(self):
        try:
            account = self._get_active_account(self.from_number)
            self._activate_account(account, False)
            return JR(self._set_message("Usuário cancelado no sistema"))
        except Account.DoesNotExist:
            return JR(self._set_message("Usuário não existe no sistema"))

    def transfer_money(self):
        """ 0= action, 1=target, 2=amount """
        try:
            _, target, amount = self.content.split(" ")

            source = self._get_active_account(self.from_number)
            target = self._get_active_account(self._format_account(target))

            result = self._update_balance(source, target, int(amount))

            if result == self.ZERO:
                return JR(self._set_message(
                    "Não pode transfer 0 Mt. Use um valor superior a 0"
                ))

            if result == self.NO_BALANCE:
                return JR(self._set_message(
                    "Sem saldo suficiente para proceder com a transferência"
                ))

            if result == self.OK:
                return JR(self._set_message(
                    "Transferência de {} Mt para {} feita "\
                    "com sucesso".format(amount, target.contact)
                ))
        except Account.DoesNotExist:
            return JR(self._set_message("Usuário não existe no sistema"))

    def check_balance(self):
        try:
            balance = self._get_active_account(self.from_number).balance
            return JR(self._set_message("O seu saldo é de {} Mt".format(intcomma(balance))))
        except Account.DoesNotExist:
            return JR(self._set_message("Usuário não existe no sistema"))

    def withdraw_money(self):
        """ Withdraw money into 
        a client (only agents)"""
        
        try:
            account = self._get_active_account(self.from_number)
        except Account.DoesNotExist:
            return JR(self._set_message("Usuário não existe no sistema"))

        if not account.agent:
            return JR(self._set_message("A sua conta não é de agente. Dirija-se a "\
            "uma loja para activar a opção de agente"))
        
        return self.transfer_money()

