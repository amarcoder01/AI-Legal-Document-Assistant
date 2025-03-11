import smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io
import logging
from fpdf import FPDF  # Add this import for PDF generation
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add a local PDF generation function to avoid importing from app.py
def generate_email_pdf(content):
    """Generate a professionally formatted PDF for email attachment"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Add a header with logo placeholder
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "Legal Document Analysis", 0, 1, "C")
        pdf.set_font("Arial", "I", 10)
        pdf.cell(190, 5, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, "C")
        pdf.line(10, 25, 200, 25)
        pdf.ln(5)
        
        # Process the content by sections
        content_parts = content.split("\n\n")
        
        for part in content_parts:
            if "DOCUMENT SUMMARY" in part:
                # Summary section
                pdf.set_font("Arial", "B", 14)
                pdf.cell(190, 10, "Document Summary", 0, 1, "L")
                pdf.set_font("Arial", "", 11)
                
                # Get the content after the header
                summary_content = part.split("-" * 30)[1].strip() if "-" * 30 in part else part
                
                # Format the content with proper line breaks
                pdf.multi_cell(190, 7, summary_content)
                pdf.ln(5)
                
            elif "RISK SCORE" in part:
                # Risk score section
                pdf.set_font("Arial", "B", 14)
                pdf.cell(190, 10, "Risk Assessment Score", 0, 1, "L")
                pdf.set_font("Arial", "", 11)
                
                # Get the content after the header
                score_content = part.split("-" * 30)[1].strip() if "-" * 30 in part else part
                
                # Format the content with proper line breaks
                pdf.multi_cell(190, 7, score_content)
                pdf.ln(5)
                
            elif "RISK ANALYSIS" in part:
                # Risk analysis section
                pdf.set_font("Arial", "B", 14)
                pdf.cell(190, 10, "Detailed Risk Analysis", 0, 1, "L")
                pdf.set_font("Arial", "", 11)
                
                # Get the content after the header
                analysis_content = part.split("-" * 30)[1].strip() if "-" * 30 in part else part
                
                # Format the content with proper line breaks
                pdf.multi_cell(190, 7, analysis_content)
                pdf.ln(5)
            
            else:
                # Other content
                pdf.set_font("Arial", "", 11)
                pdf.multi_cell(190, 7, part)
                pdf.ln(3)
        
        # Add footer
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}}", 0, 0, "C")
        
        pdf_bytes = pdf.output(dest="S").encode("latin1")
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        return buf
        
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        # Return None on error, will be handled in email_ui_section
        return None

def send_email(recipient_email, subject, body, attachment=None, attachment_name=None, attachment_type=None):
    """
    Send an email with optional attachment
    
    Parameters:
    - recipient_email: Email address of the recipient
    - subject: Email subject
    - body: Email body content
    - attachment: Binary data for attachment (optional)
    - attachment_name: Name of the attachment file (optional)
    - attachment_type: Type of attachment (pdf, docx, txt) (optional)
    
    Returns:
    - (success, message): Tuple with success status and message
    """
    try:
        # Get email credentials from Streamlit secrets
        # These should be set in your .streamlit/secrets.toml file
        smtp_server = st.secrets["email"]["SMTP_SERVER"]
        smtp_port = int(st.secrets["email"]["SMTP_PORT"])
        sender_email = st.secrets["email"]["SENDER_EMAIL"]
        sender_password = st.secrets["email"]["SENDER_PASSWORD"]
        
        # Log the configuration (omitting password)
        logging.info(f"Email configuration: Server={smtp_server}, Port={smtp_port}, Email={sender_email}")
        
        # Validate email configuration
        if not all([smtp_server, smtp_port, sender_email, sender_password]):
            return False, "Email configuration is incomplete. Please check your Streamlit secrets."
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment and attachment_name and attachment_type:
            attachment_data = attachment
            
            # Create attachment
            if attachment_type == "pdf":
                part = MIMEApplication(attachment_data.read() if hasattr(attachment_data, 'read') else attachment_data, Name=attachment_name)
                part['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
                msg.attach(part)
            elif attachment_type == "docx":
                part = MIMEApplication(attachment_data.getvalue(), Name=attachment_name)
                part['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
                msg.attach(part)
            elif attachment_type == "txt":
                part = MIMEText(attachment_data)
                part['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
                msg.attach(part)
                
        # Connect to server and send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        return True, "Email sent successfully!"
        
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return False, f"Error sending email: {str(e)}"

def validate_email(email):
    """Simple email validation"""
    if not email:
        return False
        
    # Basic validation
    if "@" not in email or "." not in email:
        return False
        
    # Check for common domains (very basic validation)
    return True

def prepare_email_content(include_summary, include_risk_score, include_risks, include_visuals):
    """Prepare well-formatted content for email"""
    email_content = []
    
    # Add document summary if selected
    if include_summary and st.session_state.get("summary"):
        email_content.append("DOCUMENT SUMMARY")
        email_content.append("-" * 30)
        
        summary = st.session_state.summary
        # Format summary if needed (e.g., bullet points)
        if not summary.startswith("•") and not summary.startswith("-"):
            # Try to add some basic formatting if not already formatted
            paragraphs = [p.strip() for p in summary.split("\n") if p.strip()]
            formatted_summary = "\n\n".join(paragraphs)
            email_content.append(formatted_summary)
        else:
            email_content.append(summary)
    
    # Add risk score if selected
    if include_risk_score and st.session_state.get("risks"):
        email_content.append("\nRISK SCORE")
        email_content.append("-" * 30)
        
        # Calculate the actual risk score
        if isinstance(st.session_state.risks, str):
            # Try to calculate a score from the text
            score, high, medium, low = calculate_risk_counts(st.session_state.risks)
            
            email_content.append(f"Overall Risk Score: {score}/100")
            email_content.append(f"Risk Level: {'High' if score >= 70 else 'Medium' if score >= 40 else 'Low'}")
            email_content.append(f"High Priority Issues: {high}")
            email_content.append(f"Medium Priority Issues: {medium}")
            email_content.append(f"Low Priority Issues: {low}")
        else:
            email_content.append("Risk score analysis is included in the detailed risk section.")
    
    # Add risk analysis if selected
    if include_risks and st.session_state.get("risks"):
        email_content.append("\nRISK ANALYSIS")
        email_content.append("-" * 30)
        
        if isinstance(st.session_state.risks, str):
            # Format the risks text
            risks_text = st.session_state.risks
            
            # Try to categorize the risks by severity
            high_risks, medium_risks, low_risks = categorize_risks(risks_text)
            
            if high_risks:
                email_content.append("\nHIGH PRIORITY RISKS:")
                for i, risk in enumerate(high_risks, 1):
                    email_content.append(f"{i}. {risk}")
            
            if medium_risks:
                email_content.append("\nMEDIUM PRIORITY RISKS:")
                for i, risk in enumerate(medium_risks, 1):
                    email_content.append(f"{i}. {risk}")
            
            if low_risks:
                email_content.append("\nLOW PRIORITY RISKS:")
                for i, risk in enumerate(low_risks, 1):
                    email_content.append(f"{i}. {risk}")
                
            if not (high_risks or medium_risks or low_risks):
                # If categorization failed, just include the text
                email_content.append(risks_text)
        else:
            email_content.append("Detailed risk analysis is not available in text format.")
    
    return "\n\n".join(email_content)

def calculate_risk_counts(risks_text):
    """Calculate risk counts and score from text for better formatting"""
    # Count occurrences of risk-related keywords
    text_lower = risks_text.lower()
    
    # Count sentences containing risk keywords
    sentences = [s.strip() for s in text_lower.split('.') if s.strip()]
    
    high_count = sum(1 for s in sentences if any(word in s for word in 
                     ['critical', 'severe', 'high risk', 'significant', 'major']))
    
    medium_count = sum(1 for s in sentences if any(word in s for word in 
                       ['moderate', 'medium', 'potential', 'concerning']))
    
    # Count remaining sentences as low risks if they're substantial
    low_count = sum(1 for s in sentences if len(s.split()) > 5 and not 
                   any(word in s for word in ['critical', 'severe', 'high risk', 
                                             'moderate', 'medium', 'potential']))
    
    total = high_count + medium_count + low_count
    if total == 0:
        return 0, 0, 0, 0
    
    # Calculate weighted score
    score = min(100, round((high_count * 3 + medium_count * 2 + low_count) / (total * 3) * 100))
    
    return score, high_count, medium_count, low_count

def categorize_risks(risks_text):
    """Categorize risks into high, medium, and low for better formatting"""
    high_risks = []
    medium_risks = []
    low_risks = []
    
    # Split into sentences
    sentences = [s.strip() for s in risks_text.split('.') if s.strip()]
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(word in sentence_lower for word in ['critical', 'severe', 'high']):
            high_risks.append(sentence)
        elif any(word in sentence_lower for word in ['moderate', 'medium']):
            medium_risks.append(sentence)
        elif len(sentence.split()) > 5:  # Only include as low risk if it's a substantial sentence
            low_risks.append(sentence)
    
    return high_risks, medium_risks, low_risks

def email_ui_section():
    """Display the email UI in the sidebar"""
    st.subheader("📧 Send Email")
    # Check if we have content to email
    has_summary = st.session_state.get("summary") is not None
    has_risks = st.session_state.get("risks") is not None
    
    if not has_summary and not has_risks:
        st.info("No content available to email. Generate a summary or risk analysis first.")
        return
        
    # Email form
    recipient = st.text_input("Recipient Email Address")
    subject = st.text_input("Email Subject", "Legal Document Analysis Results")
    
    # Content selection
    st.write("**Content to Include:**")
    
    col1, col2 = st.columns(2)
    with col1:
        include_summary = st.checkbox("Document Summary", value=has_summary, disabled=not has_summary)
        include_risk_score = st.checkbox("Risk Score", value=has_risks, disabled=not has_risks)
    with col2:
        include_risks = st.checkbox("Risk Analysis", value=has_risks, disabled=not has_risks)
        include_visuals = st.checkbox("Visualizations", value=False, disabled=not has_risks)
    
    # Format selection
    format_option = st.radio("Select Format:", ["PDF (.pdf)", "Text (.txt)"], horizontal=True)
    
    # Send button
    send_button = st.button("📤 Send Email", use_container_width=True, type="primary")
    
    if send_button:
        if not validate_email(recipient):
            st.error("⚠️ Please enter a valid email address")
        elif not any([include_summary, include_risk_score, include_risks]):
            st.warning("⚠️ Please select at least one content type to include")
        else:
            # Use the enhanced content preparation function
            combined_content = prepare_email_content(
                include_summary, include_risk_score, include_risks, include_visuals)
            
            # Generate attachment based on format
            try:
                if format_option == "Text (.txt)":
                    attachment = combined_content
                    attachment_name = "document_analysis.txt"
                    attachment_type = "txt"
                else:  # PDF
                    # Use our enhanced PDF generator
                    attachment = generate_email_pdf(combined_content)
                    if attachment is None:
                        st.error("❌ Failed to generate PDF. Sending as text instead.")
                        attachment = combined_content
                        attachment_name = "document_analysis.txt"
                        attachment_type = "txt"
                    else:
                        attachment_name = "document_analysis.pdf"
                        attachment_type = "pdf"
                
                with st.spinner("📧 Sending email..."):
                    success, message = send_email(
                        recipient, 
                        subject, 
                        "Please find attached your document analysis from the Legal Document Assistant.",
                        attachment,
                        attachment_name,
                        attachment_type
                    )
                    
                    if success:
                        st.success("✅ " + message)
                    else:
                        st.error("❌ " + message)
            except Exception as e:
                st.error(f"❌ Error preparing email: {str(e)}")
                # Try to send as plain text if PDF fails
                try:
                    st.info("Attempting to send as plain text instead...")
                    success, message = send_email(
                        recipient,
                        subject,
                        "Please find attached your document analysis from the Legal Document Assistant.",
                        combined_content,
                        "document_analysis.txt",
                        "txt"
                    )
                    if success:
                        st.success("✅ " + message)
                    else:
                        st.error("❌ " + message)
                except Exception as e2:
                    st.error(f"❌ Email sending failed completely: {str(e2)}") 