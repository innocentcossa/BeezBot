from django.db import models

class lbt_customer(models.Model):
    col_cust_no = models.CharField(max_length=30, primary_key=True)
    col_firstname = models.CharField(max_length=30)
    col_lastname = models.CharField(max_length=30)
    col_mobi_num = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.col_firstname} {self.col_lastname} ({self.col_cust_no})"


class account_balances(models.Model):
    col_mobi_num = models.CharField(max_length=50, null=True, blank=True)
    col_cust_no = models.CharField(max_length=30)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Balance for {self.col_cust_no}: {self.balance}"


class lbt_stuff(models.Model):
    col_stuf_no = models.CharField(max_length=30, primary_key=True)
    col_stuff_firstname = models.CharField(max_length=30)
    col_stuff_lastname = models.CharField(max_length=30)
    col_stuff_mobi_num = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.col_stuff_firstname} {self.col_stuff_lastname} ({self.col_stuf_no})"


class BankDetail(models.Model):
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    branch = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"
