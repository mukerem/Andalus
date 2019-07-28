from django.core.exceptions  import ValidationError
import os
from django.core.validators import validate_email
from phonenumber_field.validators import validate_international_phonenumber

def validate_problem_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')
    
def validate_testcase_in_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.in']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')

def validate_testcase_out_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.out']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')


def phone_validate(phone):
    try :
        validate_international_phonenumber(phone)
    except ValidationError as e:
        return 0
    else:
        return 1

def email_validate(email_address):
    try:
        validate_email(email_address)
    except ValidationError as e:
        return 0
    else:
        return 1