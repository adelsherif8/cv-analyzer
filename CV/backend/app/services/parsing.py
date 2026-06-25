import fitz  # PyMuPDF
from docx import Document
import os
import re
from typing import Optional

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return clean_text(text)
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return clean_text(text)
    except Exception as e:
        raise Exception(f"Failed to extract text from DOCX: {str(e)}")

def extract_text_from_rtf(file_path: str) -> str:
    """Extract text from RTF file"""
    try:
        # RTF files can often be read as plain text with some formatting
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Simple RTF text extraction - remove RTF control codes
        import re
        # Remove RTF control words and formatting
        text = re.sub(r'\\[a-z]+\d*', '', content)
        text = re.sub(r'[{}]', '', text)
        text = re.sub(r'\\', '', text)
        
        return clean_text(text)
    except Exception as e:
        raise Exception(f"Failed to extract text from RTF: {str(e)}")

def extract_text_from_odt(file_path: str) -> str:
    """Extract text from ODT file"""
    try:
        # Try to extract as plain text first
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return clean_text(text)
    except Exception as e:
        raise Exception(f"Failed to extract text from ODT: {str(e)}")

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return clean_text(text)
    except Exception as e:
        raise Exception(f"Failed to extract text from TXT: {str(e)}")

def extract_text_generic(file_path: str) -> str:
    """Fallback text extraction using pdfminer for PDFs"""
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(file_path)
        return clean_text(text)
    except Exception as e:
        raise Exception(f"Generic text extraction failed: {str(e)}")

def extract_text_from_file(file_path: str) -> str:
    """Main function to extract text from various file types"""
    if not os.path.exists(file_path):
        raise Exception(f"File not found: {file_path}")
    
    file_extension = file_path.lower().split('.')[-1]
    
    try:
        if file_extension == 'pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension in ['doc', 'docx']:
            return extract_text_from_docx(file_path)
        elif file_extension == 'txt':
            return extract_text_from_txt(file_path)
        elif file_extension == 'rtf':
            return extract_text_from_rtf(file_path)
        elif file_extension == 'odt':
            return extract_text_from_odt(file_path)
        else:
            # Try generic extraction as fallback
            if file_extension == 'pdf':
                return extract_text_generic(file_path)
            else:
                raise Exception(f"Unsupported file type: {file_extension}")
    
    except Exception as e:
        # Final fallback for PDFs
        if file_extension == 'pdf':
            try:
                return extract_text_generic(file_path)
            except:
                pass
        raise e

def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\-\(\)\@\:\;\/\%\$\+\=]', ' ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_years_from_text(text: str) -> Optional[float]:
    """Extract years of experience from text using regex"""
    patterns = [
        r'(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
        r'(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)',
        r'experience.*?(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                continue
    
    return None

def extract_contact_info(text: str) -> dict:
    """Extract basic contact information from CV text"""
    contact_info = {
        "emails": [],
        "phones": [],
        "links": []
    }
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    contact_info["emails"] = re.findall(email_pattern, text)
    
    # Phone pattern (simple)
    phone_pattern = r'[\+]?[\d\s\-\(\)]{10,}'
    contact_info["phones"] = re.findall(phone_pattern, text)
    
    # URL pattern
    url_pattern = r'https?://[^\s]+'
    contact_info["links"] = re.findall(url_pattern, text)
    
    return contact_info
