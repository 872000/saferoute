"""SOS alert simulation: a contact cascade with acknowledgements.

Triggering SOS:
  1. shares the current location with the emergency network,
  2. alerts emergency contacts one at a time in priority order,
  3. waits for a simulated acknowledgement from each before moving on,
  4. escalates to 911 if nobody acknowledges.

Fully offline — contacts, delays, and ack probabilities are simulated.
"""

from __future__ import annotations

import random
import time

from .city import GridCity

# Demo emergency contacts in priority order.
DEFAULT_CONTACTS = [
    {"name": "Priya Sharma", "relation": "Sister", "phone": "+1-416-555-0142"},
    {"name": "Raj Mehta", "relation": "Partner", "phone": "+1-905-555-0187"},
    {"name": "Campus Security", "relation": "Security desk", "phone": "+1-905-555-0911"},
]


def trigger_sos(city: GridCity, location, contacts=None, seed: int = 7,
                wait_seconds: float = 0.4, ack_chance: float = 0.7):
    """Run the SOS cascade. Returns a list of (contact_name, acked) results.

    Prints each alert/ack to the console as it happens.
    """
    contacts = list(contacts) if contacts is not None else list(DEFAULT_CONTACTS)
    if not contacts:
        raise ValueError("need at least one emergency contact")
    rng = random.Random(seed)

    label = city.label(location)
    print("🚨  SOS ALERT TRIGGERED")
    print(f"📍  Sharing current location with emergency network: block {label} "
          f"(row {location[0]}, col {location[1]})")
    print(f"👥  Contact cascade starting — {len(contacts)} contacts in priority order")
    print("-" * 52)

    results = []
    for i, c in enumerate(contacts, start=1):
        print(f"[{i}/{len(contacts)}] Alerting {c['name']} ({c['relation']}) "
              f"at {c['phone']} …")
        time.sleep(wait_seconds)
        acked = rng.random() < ack_chance
        if acked:
            print(f"        ✅ Acknowledged by {c['name']} — help is on the way.")
            results.append((c["name"], True))
            break
        print(f"        … no response from {c['name']}, escalating to next contact.")
        results.append((c["name"], False))
    else:
        # Nobody acknowledged: escalate to emergency services.
        print("-" * 52)
        print("⚠️  No contact acknowledged — escalating to 911 emergency services.")
        print("📞  911 dispatched to block "
              f"{label} with your live location share.")
        return results

    print("-" * 52)
    print(f"🟢  SOS resolved: {results[-1][0]} is responding. Stay visible, stay lit.")
    return results
