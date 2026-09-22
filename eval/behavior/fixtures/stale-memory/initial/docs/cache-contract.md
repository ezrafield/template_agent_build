# Cache contract

A cache entry expires when elapsed seconds are greater than or equal to TTL.
The clock uses seconds; do not convert to milliseconds.
Negative TTL expires immediately.
