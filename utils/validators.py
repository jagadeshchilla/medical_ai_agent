"""Validation utilities for medical office data."""

import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    
    if email.count('.com') > 1:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def clean_email(email: str) -> Optional[str]:
    """Clean and normalize email address.
    
    Args:
        email: Email address to clean
        
    Returns:
        Cleaned email address or None if invalid
    """
    if not email or not isinstance(email, str):
        return None
    
    email = email.strip()
    
    if email.endswith('.com.com'):
        email = email[:-4]
    
    if validate_email(email):
        return email
    
    return None

def validate_phone(phone: str) -> bool:
    """Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone is valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    digits_only = re.sub(r'\D', '', phone)
    return len(digits_only) == 10

def clean_phone(phone: str) -> Optional[str]:
    """Clean and normalize phone number.
    
    Args:
        phone: Phone number to clean
        
    Returns:
        Cleaned phone number or None if invalid
    """
    if not phone or not isinstance(phone, str):
        return None
    
    digits_only = re.sub(r'\D', '', phone)
    
    if len(digits_only) == 10:
        return f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
    
    return None