import asyncio

import pytest

from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture(scope="session")
def db():
    db = AsyncIOMotorClient("mongodb://mongo:27017/").get_database("test")
    yield db
    db.drop_collection("items")
    db.drop_collection("feeds")


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


async def add_feed(db, feed):
    return await db["feeds"].insert_one(feed)


async def add_item(db, item):
    return await db["items"].insert_one(item)


async def get_items(db, feed_id, offset, limit):
    return await db["items"].aggregate(
        [
            {"$match": {"feed_id": feed_id}},
            {
                "$sort": {
                    "_id": 1,
                },
            },
            {
                "$facet": {
                    "result": [
                        {"$skip": offset},
                        {"$limit": limit},
                    ],
                    "total": [
                        {"$count": "count"},
                    ],
                },
            },
        ],
    ).next()


async def get_items_unwind(db, feed_id, offset, limit):
    return await db["feeds"].aggregate(
        [
            {"$match": {"_id": feed_id}},
            {
                "$lookup": {
                    "from": "items",
                    "localField": "_id",
                    "foreignField": "feed_id",
                    "as": "items",
                }
            },
            {"$unwind": "$items"},
            {
                "$sort": {
                    "_id": 1,
                },
            },
            {
                "$facet": {
                    "result": [
                        {"$replaceRoot": {"newRoot": "$items"}},
                        {"$skip": offset},
                        {"$limit": limit},
                    ],
                    "total": [
                        {"$count": "count"},
                    ],
                },
            },
        ],
    ).next()


@pytest.mark.asyncio
async def test_get_items_pagination_sorted(db):
    feed = await add_feed(db, feed={"test": 1})
    feed_id = feed.inserted_id

    tasks = []
    for i in range(1000):
        tasks.append(
            add_item(db, item={"test": i, "feed_id": feed_id})
        )

    await asyncio.gather(*tasks)

    # when I try to fetch the items from the feed id with a limit of 1000
    items = await get_items(db, feed_id, limit=1000, offset=0)
    items_sorted = list(sorted(items["result"], key=lambda x: x["_id"]))

    # then Items should be sorted by item_id
    assert items_sorted == items["result"]

    assert len(items["result"]) == 1000


@pytest.mark.asyncio
async def test_get_items_sequenced_unwind_pagination_sorted(db):
    feed = await add_feed(db, feed={"test": 1})
    feed_id = feed.inserted_id

    for i in range(1000):
        await add_item(db, item={"test": i, "feed_id": feed_id})


    # when I try to fetch the items from the feed id with a limit of 1000
    items = await get_items_unwind(db, feed_id, limit=1000, offset=0)
    items_sorted = list(sorted(items["result"], key=lambda x: x["_id"]))

    # then Items should be sorted by item_id
    assert items_sorted == items["result"]

    assert len(items["result"]) == 1000


@pytest.mark.asyncio
async def test_get_items_async_unwind_pagination_sorted(db):
    feed = await add_feed(db, feed={"test": 1})
    feed_id = feed.inserted_id

    tasks = []
    for i in range(1000):
        tasks.append(
            add_item(db, item={"test": i, "feed_id": feed_id})
        )

    await asyncio.gather(*tasks)

    # when I try to fetch the items from the feed id with a limit of 1000
    items = await get_items_unwind(db, feed_id, limit=1000, offset=0)
    items_sorted = list(sorted(items["result"], key=lambda x: x["_id"]))

    # then Items should be sorted by item_id
    assert items_sorted == items["result"]

    assert len(items["result"]) == 1000
