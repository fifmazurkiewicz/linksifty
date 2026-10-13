from linksifty.infrastructure.memory_repository import MemoryRepository


def test_repository_never_returns_another_users_item() -> None:
    repository = MemoryRepository()
    item = repository.create_item("user-a", "https://example.com")

    assert repository.get_item("user-b", item.id) is None
    assert repository.get_item("user-a", item.id) == item


def test_repository_orders_unread_before_read() -> None:
    repository = MemoryRepository()
    read = repository.create_item("user-a", "https://read.example", unread=False)
    unread = repository.create_item("user-a", "https://unread.example", unread=True)

    assert repository.list_items("user-a") == [unread, read]
