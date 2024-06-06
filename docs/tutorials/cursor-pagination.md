Another popular pagination type is `cursor`.

It is similar to `limit-offset` pagination type, but instead 
of using `offset` parameter, it uses `cursor` parameter.

Cursor is a value that is used to identify the position of the last item in the previous page.
It is usually a primary key of the last item in the previous page.

In this tutorial, you will learn how to use `cursor` pagination type.

!!! note 

    `cursor` pagination is only available for `sqlalchemy` and `casandra` backends.


## Example

To use `cursor` you need to import `CursorPage` from `fastapi_pagination.cursor` and use it as a response model.

```py hl_lines="7"
{! ../docs_src/tutorial/cursor_pagination.py !}
```


## Total items behavior 

By default `CursorPage` doesn't include total count of items. If you want to include it, you should customize page
using `UseIncludeTotal` customizer.

```py hl_lines="58-63"
{! ../docs_src/tutorial/cursor_pagination_with_total.py !}
```