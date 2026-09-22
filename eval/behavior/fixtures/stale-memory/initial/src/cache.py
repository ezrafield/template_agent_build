def expired(created, now, ttl):
    return now - created > ttl
