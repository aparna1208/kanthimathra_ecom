from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def send_invoice_email(order):
    subject = "Your Order Invoice - Kanthi Mantra"
    message = render_to_string("web/invoice_email.html", {
        "order": order
    })

    email = EmailMessage(
        subject,
        message,
        to=[order.user.email]
    )
    email.content_subtype = "html"
    email.send()
