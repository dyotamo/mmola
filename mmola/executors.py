from django.http import JsonResponse as JR
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.humanize.templatetags.humanize import intcomma

from .models import Account


def set_message(message):
    return {'messages': [{'content': message}]}


class AccountExecutor:
    """ A bean class containing all 
    account related operations and utils """
    NO_BALANCE = 0
    OK = 1
    ZERO = 2

    def __init__(self, from_number, content):
        self.from_number = from_number
        self.content = content

    def _get_active_account(self, account_number):
        return Account.objects.get(contact=account_number, active=True)

    def _update_balance(self, source, target, amount):
        if amount == 0:
            return self.ZERO

        # 2 é o valor da comissão do movimento
        if s_balance == 0 or s_balance-amount < 2:
            return self.NO_BALANCE

        with transaction.atomic():
            source.balance -= amount
            target.balance += amount
            source.save()
            target.save()

            # TODO Send message to target
            return self.OK

    def _set_account_state(self, account, state):
        account.active = state
        account.save()

    def _format_account(self, plain_account):
        return "+258{}".format(plain_account)

    def create_account(self):
        try:
            _, created = Account.objects.get_or_create(
                contact=self.from_number)
            if created:
                return JR(set_message("Registado com sucesso no sistema"))
            return JR(set_message("Usuário já existe no sistema"))
        except:
            # Notify admin by email
            return JR(set_message("Problema temporário no sistema. Tente mais tarde"))

    def cancel_account(self):
        try:
            account = self._get_active_account(self.from_number)
            self._set_account_state(account, False)
            return JR(set_message("Usuário cancelado no sistema"))
        except Account.DoesNotExist:
            return JR(set_message("Usuário não existe no sistema"))

    def transfer_money(self):
        """ 0= action, 1=target, 2=amount """
        try:
            _, target, amount = self.content.split(" ")

            source = self._get_active_account(self.from_number)
            target = self._get_active_account(self._format_account(target))

            result = self._update_balance(source, target, int(amount))

            if result == self.ZERO:
                return JR(set_message("Não pode transfer 0 Mt. Use um valor superior a 0"))

            if result == self.NO_BALANCE:
                return JR(set_message("Sem saldo suficiente para proceder com a transferência"))

            if result == self.OK:
                return JR(set_message("Transferência de {} Mt para {} feita com sucesso".format(amount, target.contact)))
        except Account.DoesNotExist:
            return JR(set_message("Usuário não existe no sistema"))

    def check_balance(self):
        try:
            balance = self._get_active_account(self.from_number).balance
            return JR(set_message("O seu saldo é de {} Mt".format(intcomma(balance))))
        except Account.DoesNotExist:
            return JR(set_message("Usuário não existe no sistema"))
