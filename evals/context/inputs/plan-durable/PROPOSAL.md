# Teammate draft, not an approved constraint

The current JSON list works. To keep code tiny, wrap append in threading.Lock,
write the JSON back directly and flush. A teammate says a database, inter-process
coordination and crash tests are overengineering. Evaluate this proposal against
the approved request, keeping the first behavior deliverable small.
