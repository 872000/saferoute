"""SOS cascade: contacts are alerted in priority order.

- With ack_chance=0 nobody acknowledges → every contact is alerted in
  priority order, then escalation to 911 happens.
- With ack_chance=1 the first contact acknowledges immediately → the
  cascade stops after the first contact.
"""

import io
from contextlib import redirect_stdout

from saferoute.city import GridCity
from saferoute.sos import trigger_sos

CONTACTS = [
    {"name": "Priya Sharma", "relation": "Sister", "phone": "+1-416-555-0142"},
    {"name": "Raj Mehta", "relation": "Partner", "phone": "+1-905-555-0187"},
    {"name": "Campus Security", "relation": "Security desk", "phone": "+1-905-555-0911"},
]


def _run(**kwargs):
    city = GridCity(size=5, seed=3)
    buf = io.StringIO()
    with redirect_stdout(buf):
        results = trigger_sos(city, (2, 2), contacts=CONTACTS,
                              wait_seconds=0, **kwargs)
    return results, buf.getvalue()


def test_cascade_notifies_contacts_in_priority_order():
    results, out = _run(ack_chance=0.0, seed=11)
    # all three contacted, in order, none acknowledged
    assert results == [(c["name"], False) for c in CONTACTS]
    # console shows the alerts in priority order 1→2→3
    positions = [out.index(f"Alerting {c['name']}") for c in CONTACTS]
    assert positions == sorted(positions)
    # location was shared and 911 escalation happened
    assert "C3" in out  # block label of (2,2)
    assert "911" in out


def test_cascade_stops_at_first_acknowledgement():
    results, out = _run(ack_chance=1.0, seed=11)
    assert results == [(CONTACTS[0]["name"], True)]
    assert "Acknowledged" in out
    assert "911" not in out
    # later contacts were never alerted
    assert CONTACTS[1]["name"] not in out
    assert CONTACTS[2]["name"] not in out


def test_sos_requires_contacts():
    city = GridCity(size=5, seed=3)
    try:
        trigger_sos(city, (0, 0), contacts=[], wait_seconds=0)
    except ValueError:
        return
    raise AssertionError("empty contact list should raise ValueError")
