import google.generativeai as genai
import logging
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)

# Fetch API key securely from Streamlit secrets
try:
    api_key = st.secrets["api"]["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    logging.error("Gemini API key is missing or incorrect. Please check your secrets file.")

def summarize_document(text):
    """Generate a comprehensive summary of the document, with document description first followed by a structured summary."""
    if not text:
        return "No text provided for summarization."
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        
        # Limit text length to avoid token limit issues
        max_text_length = 10000
        text_to_analyze = text[:max_text_length]
        
        prompt = (
            "You are a legal document specialist. Analyze the following legal document text and provide an informative summary. "
            "Format your response in two clearly separated sections:\n\n"
            "1. DOCUMENT DESCRIPTION (first): A concise 2-3 sentence description of what this document is - identify the document type, "
            "its apparent purpose, and general subject matter.\n\n"
            "2. DOCUMENT SUMMARY (second): A well-organized summary of the key points using bullet points and subsections. "
            "Include the main clauses, provisions, rights, obligations, and any notable terms. Maintain a formal, factual tone. "
            "Use clear headings for different sections of the summary.\n\n"
            "Document text (first portion):\n"
            f"{text_to_analyze}\n\n"
            "Remember to first provide the DOCUMENT DESCRIPTION as a short paragraph, followed by the DOCUMENT SUMMARY with clear structure."
        )
        
        response = model.generate_content(prompt)
        
        if response and hasattr(response, "text"):
            return response.text.strip()
        else:
            return "Unable to generate a summary. The document may be too complex or in an unsupported format."
    
    except Exception as e:
        logging.error(f"Summarization error: {str(e)}")
        return f"Error occurred during summarization: {str(e)}"

def identify_risks(text):
    """Identifies risks in the document using Google Gemini API."""
    if not text:
        return "No text provided."

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        prompt = f"Analyze the following legal document and identify potential risks in a clear and organized manner:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, "text") else "No risks identified."
    except Exception as e:
        logging.error(f"Risk analysis error: {str(e)}")
        return f"Error occurred during risk analysis: {str(e)}"

def chat_with_document(text, query):
    """Allows users to chat with the document using Google Gemini API with a natural, conversational style."""
    if not text or not query:
        return "No text or query provided."

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        
        # Check if the query is a general greeting or small talk
        greeting_phrases = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 
                           'good evening', 'how are you', 'nice to meet you']
        
        is_greeting = any(query.lower().strip() == phrase or query.lower().strip().startswith(phrase + ' ') 
                         for phrase in greeting_phrases)
        
        if is_greeting:
            # Handle greetings with a more concise, natural response
            greeting_prompt = (
                "You are a helpful AI legal assistant. The user has greeted you. Respond with a SHORT, FRIENDLY greeting "
                "that's no more than 2-3 sentences. Briefly mention you can help analyze their legal document. "
                "DO NOT include a long list of suggestions - keep it brief and natural, like a human assistant would respond."
                f"User greeting: {query}"
            )
            response = model.generate_content(greeting_prompt)
            if response and hasattr(response, "text"):
                return response.text.strip()
            else:
                return "Hello! I'm here to help analyze your legal document. What would you like to know about it?"
        
        # Determine if the query is about the document or a general question
        document_related_keywords = ['document', 'contract', 'agreement', 'clause', 'section', 'paragraph', 'legal',
                                    'provision', 'term', 'condition', 'article', 'law', 'regulation', 'compliance',
                                    'risk', 'liability', 'obligation', 'right', 'breach', 'terminate', 'renewal',
                                    'this document', 'the document', 'in the text', 'what does it say']
        
        is_document_question = any(keyword in query.lower() for keyword in document_related_keywords)
        
        if is_document_question:
            # Use a comprehensive document analysis prompt with improved formatting
            document_prompt = (
                "You are an expert legal assistant. The user has a specific question about their legal document. "
                "Respond in a clear, direct style focusing ONLY on their question. Organize your response with "
                "short paragraphs or bullet points when appropriate. BE CONCISE.\n\n"
                "Document text (excerpt):\n"
                f"{text[:3500]}...\n\n"
                "User question about the document:\n"
                f"{query}\n\n"
                "Begin your response by directly answering their question. If possible, include ONE short relevant quote "
                "from the document (if applicable). Keep your overall response under 150 words unless complexity absolutely requires more."
            )
            response = model.generate_content(document_prompt)
        else:
            # Handle general legal or information questions with better formatting
            general_prompt = (
                "You are a helpful AI legal assistant. The user has asked a general question not specifically about "
                "their document. Respond in a conversational, helpful way like ChatGPT would - direct, informative, and concise. "
                "DO NOT unnecessarily reference their document.\n\n"
                "Remember to structure your response with short paragraphs or bullet points when appropriate. "
                f"User query: {query}\n\n"
                "Keep your response under 150 words unless absolutely necessary for a complete answer. "
                "Focus on being helpful rather than demonstrating exhaustive knowledge."
            )
            response = model.generate_content(general_prompt)
        
        if response and hasattr(response, "text"):
            return response.text.strip()
        else:
            return "I'm sorry, I couldn't generate a proper response. Please try asking in a different way."
    
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return f"I encountered an error processing your question. Please try again with a different question."
