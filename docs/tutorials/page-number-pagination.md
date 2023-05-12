You can use `page-number` pagination type to paginate data by page number. It is the most common pagination type.
In this tutorial, you will learn how to use `page-number` pagination type.

## General information

`page` parameter is used to specify the page number, and `size` parameter is used to specify the number of items per page.
For instance if you have 100 items and you want to get 10 items per page, you will have 10 pages.

By default, `page` is `1` and `size` is `50`, but you can change them.

Response schema will contain:

* `items` - list of items paginated items.
* `page` - current page number.
* `size` - number of items per page.
* `pages` - total number of pages.
* `total` - total number of items.

## Example

To use `page-number` you need to import `Page` from `fastapi_pagination` and use it as a response model.

```py hl_lines="6"
{! ../docs_src/tutorial/page_number_pagination.py !}
```

Now when we will call `/users` endpoint we will get paginated data like this:

```py
GET /users?page=2&size=3
```

```json
{
  "items": [
    {
      "name": "John",
      "email": "john@example.com"
    },
    {
      "name": "Jane",
      "email": "jane@example.com"
    },
    {
      "name": "Bob",
      "email": "bob@example.com"
    }
  ],
  "page": 2,
  "size": 3,
  "pages": 34,
  "total": 100
}
```

## OpenAPI

Code above will add pagination parameters to the endpoint and you will see them in the OpenAPI docs.

![OpenAPI Result](../img/tutorials/page-number-pagination.png)
