def invoice_total(cents, percent):
    return cents - cents * percent // 100


def subscription_total(cents, percent, months):
    return (cents - cents * percent // 100) * months
