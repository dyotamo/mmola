from django.db import models
from django.core.validators import RegexValidator

from auditlog.registry import auditlog


class Account(models.Model):
    """ Represents a user or agent account """
    contact = models.CharField(max_length=13, unique=True, validators=[
                               RegexValidator("^\+2588[2-7][0-9]{7}$")])
    active = models.BooleanField(default=True)
    balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.contact

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Conta"
        verbose_name_plural = "Contas"


auditlog.register(Account)
