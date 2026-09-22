def discount_cents(cents, percent):
    return cents - cents * percent // 100


def invoice_total(cents, percent):
    return discount_cents(cents, percent)


def subscription_total(cents, percent, months):
    return discount_cents(cents, percent) * months
