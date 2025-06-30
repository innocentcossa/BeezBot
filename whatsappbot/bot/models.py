from django.db import models

class lbt_customer(models.Model):
    col_cust_no = models.CharField(max_length=30, primary_key=True)
    col_firstname = models.CharField(max_length=30)
    col_lastname = models.CharField(max_length=30)
    col_mobi_num = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'Beezfees_lbt_customer'
        managed = False

    def __str__(self):
        return f"{self.col_firstname} {self.col_lastname} ({self.col_cust_no})"


class account_balances(models.Model):
    customer_number= models.CharField(max_length=30)
    account_number = models.CharField(max_length=30)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    full_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'Account_balances'
        managed = False

    def __str__(self):
        return f"{self.full_name} - {self.balance}"


class lbt_stuff(models.Model):
    col_stuf_no = models.CharField(max_length=30, primary_key=True)
    col_stuff_firstname = models.CharField(max_length=30)
    col_stuff_lastname = models.CharField(max_length=30)
    col_stuff_mobi_num = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'Beezfees_lbt_stuff'
        managed = False

    def __str__(self):
        return f"{self.col_stuff_firstname} {self.col_stuff_lastname} ({self.col_stuf_no})"


class BankDetail(models.Model):
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    branch = models.CharField(max_length=100)

    class Meta:
        db_table = 'Beezfees_bankdetail'  # Use your actual table name
        managed = True  # Or False if it's a manual table

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class lbt_company(models.Model):
    col_co_code = models.CharField(max_length=10, primary_key=True)
    col_co_name = models.CharField(max_length=255)
    col_co_phy_address = models.CharField(max_length=255, blank=True, null=True)
    col_co_email_add = models.EmailField(blank=True, null=True)
    col_co_mobile_no = models.CharField(max_length=30, blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    class Meta:
        db_table = 'Beezfees_lbt_company'
        managed = False

    def __str__(self):
        return self.col_co_name



