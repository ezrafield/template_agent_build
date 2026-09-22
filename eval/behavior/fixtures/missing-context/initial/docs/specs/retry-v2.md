# Retry v2

For attempts 0, 1, and 2 the delays are 0, 250, and 1000 milliseconds.
For attempts 3 and above the delay is capped at 4000 milliseconds.
An attempt is ready at or after the delay boundary.
Negative attempt values must raise ValueError.
