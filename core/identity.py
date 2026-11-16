"""
Synthetic Identity Generator Pro.
Generates multi-locale realistic personas, compliant passwords, and addresses.
"""
import random
import string
from typing import Dict, Any, Tuple, Optional


LOCALES = {
    "US": {
        "first_names": ["James", "Alexander", "Emily", "Sophia", "Oliver", "Lucas", "Liam", "Emma", "Daniel", "Chloe"],
        "last_names": ["Walker", "Harris", "Miller", "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White"],
        "cities": [("New York", "NY", "10001"), ("San Francisco", "CA", "94105"), ("Austin", "TX", "78701"), ("Seattle", "WA", "98101")],
        "phone_prefix": "+1"
    },
    "UK": {
        "first_names": ["George", "Arthur", "Harry", "Jack", "Noah", "Leo", "Olivia", "Amelia", "Isla", "Ava"],
        "last_names": ["Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Robinson", "Wright"],
        "cities": [("London", "GL", "EC1A 1BB"), ("Manchester", "GM", "M1 1AE"), ("Edinburgh", "ED", "EH1 1YZ")],
        "phone_prefix": "+44"
    },
    "DE": {
        "first_names": ["Maximilian", "Paul", "Alexander", "Elias", "Leon", "Marie", "Sophie", "Maria", "Mia", "Emma"],
        "last_names": ["Mueller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann"],
        "cities": [("Berlin", "BE", "10115"), ("Munich", "BY", "80331"), ("Hamburg", "HH", "20095")],
        "phone_prefix": "+49"
    }
}

_ADJECTIVES = ["cool", "swift", "hyper", "cyber", "nova", "prime", "alpha", "zen", "cloud", "stellar", "vivid"]
_NOUNS = ["dev", "coder", "lab", "hub", "tech", "wave", "pilot", "spark", "flow", "forge", "byte"]


def generate_synthetic_name(locale: str = "US") -> Tuple[str, str]:
    """Return realistic first and last names matching target locale."""
    data = LOCALES.get(locale.upper(), LOCALES["US"])
    first = random.choice(data["first_names"])
    last = random.choice(data["last_names"])
    return first, last


def generate_compliant_password(length: int = 14) -> str:
    """
    Generate an enterprise-compliant password satisfying all modern password complexity rules:
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 2 special symbols
    - High entropy distribution
    """
    if length < 10:
        length = 14
    lower = random.choice(string.ascii_lowercase)
    upper = random.choice(string.ascii_uppercase)
    digit1 = random.choice(string.digits)
    digit2 = random.choice(string.digits)
    sym1 = random.choice("!@#$%&*")
    sym2 = random.choice("_-=+")
    
    pool = string.ascii_letters + string.digits + "!@#$%&*_-=+"
    remaining = [random.choice(pool) for _ in range(length - 6)]
    
    chars = [lower, upper, digit1, digit2, sym1, sym2] + remaining
    random.shuffle(chars)
    return "".join(chars)


def generate_username(first: str, last: str) -> str:
    """Generate a coherent, believable username derived from name and tech terms."""
    adj = random.choice(_ADJECTIVES)
    num = random.randint(10, 999)
    patterns = [
        f"{first.lower()}_{last.lower()}{num}",
        f"{first.lower()}.{adj}{num}",
        f"{last.lower()}_{random.choice(_NOUNS)}{num}",
        f"{adj}_{first.lower()}{num}",
        f"{first.lower()}{last.lower()[:3]}{num}"
    ]
    return random.choice(patterns)


def generate_identity(
    email_domain: Optional[str] = None,
    locale: str = "US",
    use_disposable: bool = False,
    mail_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generate a cohesive, multi-field identity profile.

    If mail_client is provided, delegates mailbox creation to it.
    Else if use_disposable is True, dynamically allocates a real mailbox via DisposableMailClient.
    If email_domain is given, constructs an address on that domain.
    Otherwise uses an explicit mock domain (@local.dev) to avoid fabricating unowned mail domains.
    """
    loc_data = LOCALES.get(locale.upper(), LOCALES["US"])
    first, last = generate_synthetic_name(locale)
    username = generate_username(first, last)
    password = generate_compliant_password()

    if mail_client is not None:
        try:
            email = mail_client.create_mailbox()
        except Exception:
            domain = email_domain or "local.dev"
            email = f"{username}@{domain}"
    elif use_disposable:
        try:
            from core.mail_client import DisposableMailClient
            client = DisposableMailClient()
            email = client.create_mailbox()
        except Exception:
            domain = email_domain or "local.dev"
            email = f"{username}@{domain}"
    elif email_domain:
        email = f"{username}@{email_domain}"
    else:
        email = f"{username}@local.dev"

    city, state, postal = random.choice(loc_data["cities"])
    phone_suffix = "".join(random.choices(string.digits, k=10))
    phone = f"{loc_data['phone_prefix']}{phone_suffix}"

    birth_year = random.randint(1988, 2004)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)

    return {
        "locale": locale.upper(),
        "first_name": first,
        "last_name": last,
        "full_name": f"{first} {last}",
        "username": username,
        "email": email,
        "password": password,
        "phone": phone,
        "city": city,
        "state": state,
        "postal_code": postal,
        "birth_date": f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
    }
