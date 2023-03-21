# TEST MONGO PAGINATION

## DESCRIPTION

This is a test project to test the pagination of a mongo database.

## HOW TO TEST

`docker-compose run --build app`

## EXPECTED RESULT

All tests should pass

## ACTUAL RESULT

Tests are failing randomly with the following error:

`FAILED app/test.py::test_get_items_async_unwind_pagination_sorted - AssertionError`

## ADDITIONAL INFO

The test is failing because the `unwind` is not working as expected. The `unwind` is not returning the expected results sorted. 

It fails only if the items are inserted concurrently.

## ENVIRONMENT

Every MongoDB version is affected.