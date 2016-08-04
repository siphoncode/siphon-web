
import string
import random
import uuid

def generate_slug(length=10):
    """
    Returns a YouTube-style random string containing only alphabet letters.
    """
    chars = string.ascii_lowercase + string.ascii_uppercase
    return ''.join(random.choice(chars) for i in range(length))

def generate_id():
    """
    Returns a long id.
    """
    return str(uuid.uuid4())