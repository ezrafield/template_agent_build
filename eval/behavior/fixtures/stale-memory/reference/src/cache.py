def expired(created, now, ttl):
    return ttl < 0 or now - created >= ttl
