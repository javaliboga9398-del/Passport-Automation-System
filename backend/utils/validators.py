import re
from datetime import datetime, date

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
MOBILE_REGEX = r'^[6-9]\d{9}$'  # Standard 10-digit Indian mobile format
PINCODE_REGEX = r'^\d{6}$'

def validate_email(email):
    if not email:
        return False, "Email is required."
    if not re.match(EMAIL_REGEX, email.strip()):
        return False, "Please enter a valid email address."
    return True, ""

def validate_mobile(mobile):
    if not mobile:
        return False, "Mobile number is required."
    clean_mobile = re.sub(r'[\s\-+]', '', mobile.strip())
    if clean_mobile.startswith('91') and len(clean_mobile) == 12:
        clean_mobile = clean_mobile[2:]
    if not re.match(MOBILE_REGEX, clean_mobile):
        return False, "Please enter a valid 10-digit mobile number."
    return True, clean_mobile

def validate_password(password):
    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""

def validate_pincode(pincode):
    if not pincode:
        return False, "PIN code is required."
    if not re.match(PINCODE_REGEX, pincode.strip()):
        return False, "PIN code must be exactly 6 digits."
    return True, ""

def validate_dob(dob_str):
    if not dob_str:
        return False, "Date of birth is required.", None
    try:
        parsed_date = datetime.strptime(dob_str, '%Y-%m-%d').date()
        if parsed_date >= date.today():
            return False, "Date of birth cannot be today or in the future.", None
        return True, "", parsed_date
    except ValueError:
        return False, "Invalid date format. Expected YYYY-MM-DD.", None

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
