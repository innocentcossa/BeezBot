# bot/admin.py

from django.contrib import admin
from .models import BankDetail, lbt_customer, account_balances, lbt_stuff

admin.site.register(BankDetail)
admin.site.register(lbt_customer)
admin.site.register(account_balances)
admin.site.register(lbt_stuff)
