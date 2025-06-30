from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML
from django.db import connection
from datetime import date
from django.conf import settings
import base64
import os

from bot.models import lbt_customer, lbt_company, account_balances


def get_logo_base64(company):
    if company and getattr(company, 'logo', None):
        logo_path = os.path.join(settings.MEDIA_ROOT, str(company.logo))
        if os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode("utf-8")
            except Exception as e:
                print("Error reading logo:", e)
    return ""


def generate_fee_statement_pdf_html(phone):
    students = lbt_customer.objects.filter(col_mobi_num=phone)
    company = lbt_company.objects.first()
    logo_base64 = get_logo_base64(company)

    if not students.exists():
        html_string = "<h1>No student data found.</h1>"
    else:
        student = students.first()
        balance_record = account_balances.objects.filter(customer_number=student.col_cust_no).first()
        balance = balance_record.balance if balance_record else "Not Available"

        context = {
            "student_name": f"{student.col_firstname} {student.col_lastname}",
            "reg_no": student.col_cust_no,
            "balance": balance,
            "multiple": students.count() > 1,
            "all_students": [
                {
                    "name": f"{s.col_firstname} {s.col_lastname}",
                    "reg_no": s.col_cust_no,
                    "balance": account_balances.objects.filter(customer_number=s.col_cust_no).first().balance
                    if account_balances.objects.filter(customer_number=s.col_cust_no).exists()
                    else "Not Available"
                }
                for s in students
            ],
            "company": company,
            "logo_base64": logo_base64,
            "dat": date.today(),
        }
        html_string = render_to_string("fee_statement.html", context)

    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file


def generate_student_fee_statement_pdf_html(reg_no):
    try:
        student = lbt_customer.objects.get(col_cust_no=reg_no)
        balance_record = account_balances.objects.filter(customer_number=reg_no).first()
        balance = balance_record.balance if balance_record else "Not Available"

        company = lbt_company.objects.first()
        logo_base64 = get_logo_base64(company)

        context = {
            "student_name": f"{student.col_firstname} {student.col_lastname}",
            "reg_no": student.col_cust_no,
            "balance": balance,
            "company": company,
            "logo_base64": logo_base64,
            "dat": date.today(),
        }
        html_string = render_to_string("student_fee_statement.html", context)
    except lbt_customer.DoesNotExist:
        html_string = "<h1>❌ Student not found.</h1>"

    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file


def generate_debtors_report_pdf_html():
    students_with_balance = account_balances.objects.filter(balance__gt=0)
    debtors = []
    for record in students_with_balance:
        try:
            student = lbt_customer.objects.get(col_cust_no=record.customer_number)
            debtors.append({
                "name": f"{student.col_firstname} {student.col_lastname}",
                "reg_no": student.col_cust_no,
                "balance": float(record.balance),
            })
        except lbt_customer.DoesNotExist:
            continue

    company = lbt_company.objects.first()
    logo_base64 = get_logo_base64(company)

    context = {
        "debtors": debtors,
        "company": company,
        "logo_base64": logo_base64,
        "dat": date.today(),
    }
    html_string = render_to_string("debtors_report.html", context)

    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file


def generate_fees_statement_whatsapp_pdf(account_number):
    try:
        dat = date.today()
        company = lbt_company.objects.first()
        logo_base64 = get_logo_base64(company)

        with connection.cursor() as cursor:
            cursor.execute("SELECT col_cust_no FROM CRDR_AMOUNTS WHERE col_acc_no = %s LIMIT 1", [account_number])
            result = cursor.fetchone()
            if not result:
                raise ValueError("Account not found.")
            col_cust_no = result[0]

        try:
            customer = lbt_customer.objects.get(col_cust_no=col_cust_no)
            customer_first_name = customer.col_firstname
            customer_last_name = customer.col_lastname
        except lbt_customer.DoesNotExist:
            customer_first_name = ''
            customer_last_name = ''

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM CRDR_AMOUNTS WHERE col_acc_no = %s", [account_number])
            fees_statements = cursor.fetchall()

        running_balance = 0
        processed_statements = []

        for statement in fees_statements:
            transaction_date = statement[4]
            description = statement[1]
            dr_amount = float(statement[11]) if statement[11] else 0
            cr_amount = float(statement[12]) if statement[12] else 0
            running_balance += dr_amount - cr_amount

            processed_statements.append({
                'transaction_date': transaction_date,
                'description': description,
                'dr_amount': dr_amount,
                'cr_amount': cr_amount,
                'running_balance': running_balance
            })

        context = {
            'fees_statements': processed_statements,
            'dat': dat,
            'company': company,
            'col_cust_no': col_cust_no,
            'customer_first_name': customer_first_name,
            'customer_last_name': customer_last_name,
            'logo_base64': logo_base64
        }

        html_string = render_to_string("fees_statements.html", context)
        pdf_file = BytesIO()
        HTML(string=html_string).write_pdf(pdf_file)
        pdf_file.seek(0)
        return pdf_file

    except Exception as e:
        print(f"❌ Error generating fee statement PDF: {e}")
        return None
