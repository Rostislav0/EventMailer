from validate_email import validate_email
#is_valid = validate_email('example@example.com', check_mx=True)

emails = ["email@example.com", "email@bad_domain", "email2@example.com"]
verified_domains = set()
for email in emails:
    domain = email.split("@")[-1]
    domain_verified = domain in verified_domains
    is_valid = validate_email(email, check_mx=not domain_verified)
    if is_valid:
        verified_domains.add(domain)