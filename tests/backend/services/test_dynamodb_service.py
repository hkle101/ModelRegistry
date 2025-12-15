from __future__ import annotations

from backend.services.dynamodb_service import DynamoDBService


class _FakeTable:
    """Minimal DynamoDB table stub compatible with `DynamoDBService` methods."""

    def __init__(self):
        self.items = {}
        self.update_calls = []
        self.deleted = []

    def put_item(self, Item):
        self.items[Item["artifact_id"]] = dict(Item)

    def get_item(self, Key):
        it = self.items.get(Key["artifact_id"])
        return {"Item": dict(it)} if it else {}

    def update_item(self, **kwargs):
        self.update_calls.append(kwargs)

    def delete_item(self, Key):
        self.deleted.append(Key["artifact_id"])
        self.items.pop(Key["artifact_id"], None)

    def scan(self):
        return {"Items": list(self.items.values())}


def test_dynamodb_service_create_and_get_item():
    t = _FakeTable()
    svc = DynamoDBService(table=t)

    assert svc.create_item({"artifact_id": "a1", "name": "n"}) is True
    assert svc.get_item("a1")["name"] == "n"


def test_dynamodb_service_update_item_builds_expression():
    t = _FakeTable()
    svc = DynamoDBService(table=t)

    ok = svc.update_item("a1", {"name": "new", "size": 1})
    assert ok is True

    call = t.update_calls[-1]
    assert call["Key"] == {"artifact_id": "a1"}
    assert call["UpdateExpression"].startswith("SET ")
    assert call["ExpressionAttributeNames"]["#name"] == "name"
    assert call["ExpressionAttributeValues"][":name"] == "new"


def test_dynamodb_service_delete_and_scan_and_reset():
    t = _FakeTable()
    t.put_item(Item={"artifact_id": "a1"})
    t.put_item(Item={"artifact_id": "a2"})
    svc = DynamoDBService(table=t)

    assert len(svc.scan_all()) == 2
    assert svc.delete_item("a1") is True
    assert svc.get_item("a1") is None

    # reset should delete remaining items
    svc.reset_table()
    assert svc.scan_all() == []
