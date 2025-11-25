import os
import time
from google import genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib
import random
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

def generate_feedback(client):
    feedback_types = [
        'very_satisfied',
        'satisfied',
        'neutral',
        'dissatisfied',
        'product_issue',
        'delivery_issue',
        'service_issue',
        'payment_issue',
        'return_issue',
        'website_issue',
        'app_issue',
        'other_issue'
    ]
    
    selected_type = random.choice(feedback_types)

    prompts = {
        'very_satisfied': """Generate an enthusiastic customer feedback email about a recent purchase. 
            Mention specific product features you loved, excellent delivery time, and outstanding customer service experience.
            Include details about product quality and why you would recommend it. Fill in fake details. 
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",
        
        'satisfied': """Generate a positive customer feedback email that highlights good product experience.
            Mention what met your expectations about the product, delivery, and overall service.
            Include one minor suggestion for improvement. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",
        
        'neutral': """Generate a balanced customer feedback email about your purchase.
            Discuss both positive aspects (like product features or delivery) and areas needing improvement.
            Be specific about what worked and what didn't. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",
        
        'dissatisfied': """Generate a professional but critical customer feedback email.
            Address specific issues with the product, delivery delays, or service problems.
            Clearly state what went wrong and what resolution you expect. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",
        
        'product_issue': """Generate a detailed customer complaint email about product quality issues.
            Describe specific problems encountered, when they started, and their impact.
            Request specific resolution (replacement, refund, or repair) and timeline expectations. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",

        'delivery_issue': """Generate a customer complaint email about delivery problems.
            Describe the delivery delay, missing items, or damaged package.
            Request specific resolution (replacement, refund, or compensation) and timeline expectations. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",

        'service_issue': """Generate a customer complaint email about poor service experience.
            Describe the issue with customer service representative, response time, or lack of resolution.
            Request specific resolution (apology, compensation, or escalation) and timeline expectations. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",

        'payment_issue': """Generate a customer complaint email about payment problems.
            Describe the payment error, double charge, or refund delay.
            Request specific resolution (refund, confirmation, or investigation) and timeline expectations. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",

        'return_issue': """Generate a customer complaint email about return process issues.
            Describe the return rejection, refund delay, or return shipping problem.
            Request specific resolution (refund, replacement, or return label) and timeline expectations. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",

        'website_issue': """Generate a customer complaint email about website usability issues.
            Describe the problem with navigation, search, or checkout process.
            Request specific resolution (fix, refund, or discount) and timeline expectations. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",

        'app_issue': """Generate a customer complaint email about mobile app functionality issues.
            Describe the app crash, login error, or payment failure.
            Request specific resolution (update, refund, or support) and timeline expectations. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line.""",

        'other_issue': """Generate a customer complaint email about other issues not listed.
            Describe the problem encountered, its impact, and your expectations.
            Request specific resolution (refund, replacement, or compensation) and timeline expectations. Fill in fake details.
            Don't use placeholders. Write in plain text, don't use formating, **only use newline characters (\n) to beautify the email**. Don't wrirte the subject line."""
    }
    
    # UPDATED: New generate_content syntax
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompts[selected_type]
    )
    return response.text

def extract_details_with_gemini(client, text):
    prompt = f"""
    Extract these details from the email text and return as JSON object:
    - customer_name
    - order_id (if available) else return "N/A"
    - order_item (if available) else return "N/A"
    - order_date (if available) else return "N/A"
    - amount (if available) else return "N/A"

    Email: {text}

    Don't use ```json``` or ```return``` in your response. Just write the JSON object as plain text.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "customer_name": None,
            "order_id": "N/A", 
            "order_item": "N/A",
            "order_date": "N/A",
            "amount": "N/A"
        }
    
def generate_fake_invoice(invoice_data):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    heading_style = styles['Heading2']
    
    # Add invoice header
    header = Paragraph("<b>INVOICE</b>", title_style)
    elements.append(header)
    elements.append(Spacer(1, 12))
    
    # Add company information
    company_info = Paragraph("Company Name<br/>123 Business Road<br/>City, State, ZIP<br/>Email: info@company.com", normal_style)
    elements.append(company_info)
    elements.append(Spacer(1, 24))
    
    # Customer and Invoice details section
    customer_info = Paragraph(f"<b>Customer:</b> {invoice_data['customer_name']}<br/>"
                               f"<b>Invoice Number:</b> {invoice_data['order_id']}<br/>"
                               f"<b>Date:</b> {invoice_data['order_date']}", normal_style)
    elements.append(customer_info)
    elements.append(Spacer(1, 12))
    
    # Create table with product and pricing details
    table_data = [
        ["Product", "Quantity", "Price", "Total"],
        [invoice_data['order_item'], "1", f"${invoice_data['amount']}", f"${invoice_data['amount']}"]
    ]
    
    table = Table(table_data, colWidths=[200, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 24))
    
    # Add footer
    footer = Paragraph("Thank you for your business!<br/>For questions, contact us at info@company.com.", normal_style)
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

def send_bulk_feedback_emails(sender_email, app_password, recipient_email, num_emails, api_key):
    # List of fake sender emails for testing
    fake_senders = [
        'customer1@example.com',
        'happy.buyer@example.com',
        'regular.client@example.com',
        'new.customer@example.com',
        'loyal.shopper@example.com',
        'first.time@example.com',
        'return.buyer@example.com',
        'verified.purchase@example.com',
        'old.customer@example.com',
        'big.buyer@example.com'
    ]
    
    # Configure Gemini with provided API key
    client = genai.Client(api_key=api_key)

    # Email setup
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, app_password)
            
            for i in range(num_emails):
                try:
                    current_sender = fake_senders[i % len(fake_senders)]
                    # Generate feedback using Gemini
                    feedback_message = generate_feedback(client)                
                    time.sleep(1)
                    # Extract invoice data from feedback message
                    invoice_data = extract_details_with_gemini(client, feedback_message)
                    time.sleep(1)
                    # Create email message
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = f"Customer Feedback #{i+1}"
                    msg['From'] = current_sender
                    msg['To'] = recipient_email

                    text_part = MIMEText(feedback_message, 'plain')
                    html_feedback_message = feedback_message.replace("\n", "<br>")
                    html_part = MIMEText(f'<html><body><p>{html_feedback_message}</p></body></html>', 'html')                
                    msg.attach(text_part)
                    msg.attach(html_part)

                    # Attach PDF invoice if order_id is valid
                    if invoice_data['order_id'] != "N/A":
                        invoice_buffer = generate_fake_invoice(invoice_data)
                        pdf_part = MIMEApplication(invoice_buffer.read(), _subtype='pdf')
                        pdf_part.add_header('Content-Disposition', 'attachment', filename=f"invoice_{invoice_data['order_id']}.pdf")
                        msg.attach(pdf_part)

                    server.send_message(msg)
                    print(f"Email {i+1} sent successfully")
                    time.sleep(1)
                except Exception as e:
                    print(f"Error sending email {i+1}: {e}")
                    continue

    except Exception as e:
        print(f"Error: {e}")

GEMINI_API_KEY = ''  # Replace with actual API key

SENDER_EMAIL = '' # customer email
APP_PASSWORD = ''
RECIPIENT_EMAIL = '' # company email

send_bulk_feedback_emails(
    sender_email="ashishchauhan123ch@gmail.com",
    app_password="geauzcxwbcoiobms",
    recipient_email="company.c2601144@gmail.com",
    num_emails=10,
    api_key="AIzaSyBql5VoPuW1lJp5ZZNiAinWsRuX0lW32IA"
)