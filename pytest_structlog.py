import pytest
import structlog


class EventList(list):
    """A list subclass that overrides ordering operations.
    Instead of A <= B being a lexicographical comparison,
    now it means every element of A is contained within B,
    in the same order, although there may be other items
    interspersed throughout (i.e. A is a subsequence of B)
    """

    def __ge__(self, other):
        return is_subseq(other, self)

    def __gt__(self, other):
        return len(self) > len(other) and is_subseq(other, self)

    def __le__(self, other):
        return is_subseq(self, other)

    def __lt__(self, other):
        return len(self) < len(other) and is_subseq(self, other)


absent = object()


def is_submap(d1, d2):
    """is every pair from d1 also in d2? (unique and order insensitive)"""
    return all(d2.get(k, absent) == v for k, v in d1.items())


def is_subseq(l1, l2):
    """is every element of l1 also in l2? (non-unique and order sensitive)"""
    it = iter(l2)
    return all(d in it for d in l1)


class StructuredLogCapture(object):
    def __init__(self):
        self.events = EventList()

    def process(self, logger, method_name, event_dict):
        event_dict["level"] = method_name
        self.events.append(event_dict)
        raise structlog.DropEvent

    def has(self, message, **context):
        context["event"] = message
        return any(is_submap(context, e) for e in self.events)


def no_op(*args, **kwargs):
    pass


@pytest.fixture
def log(monkeypatch):
    cap = StructuredLogCapture()
    structlog.configure(processors=[cap.process])
    monkeypatch.setattr("structlog.configure", no_op)
    monkeypatch.setattr("structlog.configure_once", no_op)
    return cap
