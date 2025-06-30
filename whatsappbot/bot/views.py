from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .send_api import (
    send_text_message,
    send_document_message,
    upload_pdf_to_whatsapp
)

from .pdf_generator import (
    generate_fee_statement_pdf_html,
    generate_student_fee_statement_pdf_html,
    generate_debtors_report_pdf_html,
    generate_fees_statement_whatsapp_pdf  
)

from bot.models import lbt_customer, account_balances, lbt_stuff, BankDetail

VERIFY_TOKEN = "my_secure_verify_token_123"
USER_STATES = {}


def get_bank_details():
    bank = BankDetail.objects.first()
    if not bank:
        return "⚠️ Bank details not available at the moment. Please contact the office."
    return (
        "🏦 *Bank Payment Details:*\n\n"
        f"🏛 Bank: {bank.bank_name}\n"
        f"💳 Account: {bank.account_number}\n"
        f"🏢 Branch: {bank.branch}\n\n"
        "📌 Please use the student's name and reg number as reference."
    )


@csrf_exempt
def webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponseForbidden("Verification token mismatch")

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            message_obj = data['entry'][0]['changes'][0]['value']['messages'][0]
            phone = message_obj['from']
            message_type = message_obj.get('type')
            text = message_obj['text']['body'].strip().lower() if message_type == 'text' else ''
            state = USER_STATES.get(phone)

            staff = lbt_stuff.objects.filter(col_stuff_mobi_num=phone).first()
            parent = lbt_customer.objects.filter(col_mobi_num=phone).first()

            if staff:
                role = "staff"
                name = staff.col_stuff_firstname
            elif parent:
                role = "parent"
                name = parent.col_firstname
            else:
                send_text_message(phone, "❌ Your number is not recognized. Please contact the school office.")
                return JsonResponse({"status": "not recognized"}, status=200)

            if text in {"hi", "hello", "menu", "start"}:
                USER_STATES[phone] = "waiting_confirmation"
                send_text_message(phone, f"👋 Hello {name}, welcome to BeezBot!\n👉 Reply with *1* to proceed to the menu.")
                return JsonResponse({"status": "greeted"}, status=200)

            if text in {"exit", "cancel", "quit"}:
                USER_STATES.pop(phone, None)
                send_text_message(phone, "🛑 Session ended. Type *hi* to start again.")
                return JsonResponse({"status": "exited"}, status=200)

            if not state:
                USER_STATES[phone] = "waiting_confirmation"
                send_text_message(phone, "👋 Welcome to BeezBot!\n👉 Reply with *1* to proceed to the main menu.")
                return JsonResponse({"status": "waiting confirmation"}, status=200)

            if state == "waiting_confirmation":
                if text == "1":
                    USER_STATES[phone] = "main_menu"
                    send_text_message(phone, get_main_menu(role))
                else:
                    send_text_message(phone, "❓ Please reply with *1* to continue to the menu.")
                return JsonResponse({"status": "waiting confirmation response"}, status=200)

            if state == "main_menu":
                if text == "1" and role == "staff":
                    USER_STATES[phone] = "awaiting_student_reg"
                    send_text_message(phone, "📝 Please enter the Student's REGISTRATION NUMBER")
                elif text == "1" and role == "parent":
                    response = handle_menu_selection(role, "1", phone)
                    send_text_message(phone, response)
                elif text == "2":
                    send_text_message(phone, get_bank_details())
                elif text == "3":
                    if role == "parent":
                        pdf_buffer = generate_fee_statement_pdf_html(phone)
                        media_id = upload_pdf_to_whatsapp(pdf_buffer, filename="FeeStatement.pdf")
                        if media_id:
                            send_document_message(phone, media_id, caption="📄 Your Fee Statement")
                        else:
                            send_text_message(phone, "❌ Failed to upload statement.")
                    else:
                        USER_STATES[phone] = "awaiting_statement_reg"
                        send_text_message(phone, "📥 Please enter the student's REGISTRATION NUMBER for the PDF")
                elif text == "4" and role == "staff":
                    pdf_buffer = generate_debtors_report_pdf_html()
                    media_id = upload_pdf_to_whatsapp(pdf_buffer, filename="DebtorsReport.pdf")
                    if media_id:
                        send_document_message(phone, media_id, caption="📄 Debtors Report (Balances > $0)")
                    else:
                        send_text_message(phone, "❌ Could not generate debtors report.")
                else:
                    send_text_message(phone, "❌ Invalid selection. Type *menu* to return to the main menu.")
                return JsonResponse({"status": "main menu handled"}, status=200)

            if state == "awaiting_student_reg":
                reg_no = text.upper()
                balance_msg = get_student_balance_by_reg(reg_no)
                send_text_message(phone, balance_msg)
                USER_STATES[phone] = "main_menu"
                return JsonResponse({"status": "student reg processed"}, status=200)

            if state == "awaiting_statement_reg":
                reg_no = text.upper()
                pdf_buffer = generate_fees_statement_whatsapp_pdf(reg_no)  # Updated to use new function with logo
                if pdf_buffer:
                    media_id = upload_pdf_to_whatsapp(pdf_buffer, filename=f"{reg_no}_Statement.pdf")
                    if media_id:
                        send_document_message(phone, media_id, caption=f"📄 Fee Statement for {reg_no}")
                    else:
                        send_text_message(phone, "❌ Could not upload statement.")
                else:
                    send_text_message(phone, "❌ Could not generate statement PDF.")
                USER_STATES[phone] = "main_menu"
                return JsonResponse({"status": "statement sent"}, status=200)

            USER_STATES.pop(phone, None)
            send_text_message(phone, "⚠️ Session reset. Please send *hi* to start again.")

        except Exception as e:
            print("Webhook error:", e)

        return JsonResponse({"status": "received"}, status=200)


def get_main_menu(role):
    if role == "staff":
        return (
            "👨‍🏫 *Staff Menu:*\n"
            "1. View Student Balance\n"
            "2. Bank Account Details\n"
            "3. Student Fees Statement PDF\n"
            "4. Debtors Report PDF\n"
            "🔁 Type 'menu' to return\n❌ Type 'exit' to cancel"
        )
    return (
        "👨‍👩‍👧 *BeezParent Menu:*\n"
        "1. Fees Balance\n"
        "2. Bank Account Details\n"
        "3. Fees Statement PDF\n"
        "🔁 Type 'menu' to return\n❌ Type 'exit' to cancel"
    )


def handle_menu_selection(role, message, phone):
    if message == "1" and role == "parent":
        try:
            children = lbt_customer.objects.filter(col_mobi_num=phone)
            if not children.exists():
                return "⚠️ No students found associated with your number. Please contact the office."

            response = "💰 *Fees Balances Report*\n\n"
            for child in children:
                balance_record = account_balances.objects.filter(col_cust_no=child.col_cust_no).first()
                if balance_record:
                    balance = float(balance_record.balance)
                    formatted = f"{balance:.2f}"
                    status = (
                        f"🔴 Outstanding balance of ${formatted}" if balance > 0 else
                        f"🟢 Credit of (${abs(balance):.2f})" if balance < 0 else
                        "🟢 Account fully paid"
                    )
                    response += (
                        f"*Learner:* {child.col_firstname} {child.col_lastname}\n"
                        f"*Reg No:* {child.col_cust_no}\n"
                        f"*Balance:* ${formatted}\n"
                        f"*Status:* {status}\n\n"
                    )
                else:
                    response += (
                        f"*Learner:* {child.col_firstname} {child.col_lastname}\n"
                        f"*Reg No:* {child.col_cust_no}\n"
                        "⚠️ Balance information not available\n\n"
                    )
            return response + "📌 For statements, select option 3"
        except Exception as e:
            print("Parent balance error:", e)
            return "⚠️ Could not retrieve balances. Please contact the office."

    return "❌ Invalid selection. Type *menu* to return to the main menu."


def get_student_balance_by_reg(reg_no):
    try:
        customer = lbt_customer.objects.get(col_cust_no=reg_no)
        balance_record = account_balances.objects.filter(col_cust_no=reg_no).first()

        if not balance_record:
            return f"⚠️ No balance record found for student {reg_no}."

        balance = float(balance_record.balance)
        formatted = f"{balance:.2f}"

        status = (
            f"🔴 Outstanding: ${formatted}" if balance > 0 else
            f"🟢 Credit: ${abs(balance):.2f}" if balance < 0 else
            "🟢 Account settled"
        )

        return (
            f"*Student Balance Details*\n\n"
            f"*Name:* {customer.col_firstname} {customer.col_lastname}\n"
            f"*Reg No:* {reg_no}\n"
            f"*Amount:* ${formatted}\n"
            f"*Status:* {status}"
        )

    except lbt_customer.DoesNotExist:
        return "❌ Student registration number not found. Please check and try again."
    except Exception as e:
        print("Staff balance lookup error:", e)
        return "⚠️ Error retrieving balance. Please try again later."

