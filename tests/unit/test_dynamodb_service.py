import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from backend.services.dynamodb_service import DynamoDBService


@pytest.fixture
def mock_table():
    """Mock DynamoDB table for testing."""
    return MagicMock()


@pytest.fixture
def dynamodb_service(mock_table):
    """Create DynamoDBService with mocked table."""
    return DynamoDBService(table=mock_table)


def test_create_item_success(dynamodb_service, mock_table):
    item = {"artifact_id": "123", "name": "Test Artifact"}
    mock_table.put_item.return_value = {}
    result = dynamodb_service.create_item(item)
    mock_table.put_item.assert_called_once_with(Item=item)
    assert result is True


def test_create_item_failure(dynamodb_service, mock_table):
    mock_table.put_item.side_effect = ClientError(
        error_response={"Error": {"Message": "Failed"}},
        operation_name="PutItem"
    )
    result = dynamodb_service.create_item({"artifact_id": "123"})
    assert result is False


def test_get_item_found(dynamodb_service, mock_table):
    mock_table.get_item.return_value = {"Item": {"artifact_id": "123", "name": "Test"}}
    item = dynamodb_service.get_item("123")
    mock_table.get_item.assert_called_once_with(Key={"artifact_id": "123"})
    assert item["name"] == "Test"


def test_get_item_not_found(dynamodb_service, mock_table):
    mock_table.get_item.return_value = {}
    item = dynamodb_service.get_item("999")
    assert item is None


def test_get_item_client_error(dynamodb_service, mock_table):
    mock_table.get_item.side_effect = ClientError(
        error_response={"Error": {"Message": "Bad"}},
        operation_name="GetItem"
    )
    item = dynamodb_service.get_item("999")
    assert item is None


def test_update_item_success(dynamodb_service, mock_table):
    update_data = {"license": "MIT", "updated_at": "2025-11-11"}
    result = dynamodb_service.update_item("123", update_data)
    mock_table.update_item.assert_called_once()
    assert result is True


def test_update_item_failure(dynamodb_service, mock_table):
    mock_table.update_item.side_effect = ClientError(
        error_response={"Error": {"Message": "Fail"}},
        operation_name="UpdateItem"
    )
    result = dynamodb_service.update_item("123", {"license": "MIT"})
    assert result is False


def test_delete_item_success(dynamodb_service, mock_table):
    result = dynamodb_service.delete_item("123")
    mock_table.delete_item.assert_called_once_with(Key={"artifact_id": "123"})
    assert result is True


def test_delete_item_failure(dynamodb_service, mock_table):
    mock_table.delete_item.side_effect = ClientError(
        error_response={"Error": {"Message": "Delete failed"}},
        operation_name="DeleteItem"
    )
    result = dynamodb_service.delete_item("123")
    assert result is False


def test_scan_all_success(dynamodb_service, mock_table):
    mock_table.scan.return_value = {"Items": [{"artifact_id": "1"}, {"artifact_id": "2"}]}
    items = dynamodb_service.scan_all()
    mock_table.scan.assert_called_once()
    assert len(items) == 2


def test_scan_all_failure(dynamodb_service, mock_table):
    mock_table.scan.side_effect = ClientError(
        error_response={"Error": {"Message": "Scan failed"}},
        operation_name="Scan"
    )
    items = dynamodb_service.scan_all()
    assert items == []


def test_reset_table(dynamodb_service, mock_table):
    mock_table.scan.return_value = {"Items": [{"artifact_id": "1"}, {"artifact_id": "2"}]}
    dynamodb_service.reset_table()
    # It should call delete_item twice (once per artifact)
    assert mock_table.delete_item.call_count == 2
