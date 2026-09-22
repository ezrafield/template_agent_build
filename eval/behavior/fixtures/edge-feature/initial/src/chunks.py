def chunks(values):
    values = list(values)
    for index in range(0, len(values), 2):
        yield values[index:index + 2]
