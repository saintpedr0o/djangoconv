import secrets
import string


def generate_api_key():
    chars = string.ascii_letters + string.digits
    part_lengths = [12, 10, 24]
    parts = ["".join(secrets.choice(chars) for _ in range(l)) for l in part_lengths]
    return "-".join(parts)
