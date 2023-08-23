# Items Transformer

If you want to transform items before passing it to schema validation stage,
you can use `transformer` argument of `paginate` function.

```py hl_lines="13"
{! ../docs_src/tutorial/items_transformer.py !}
```

`transformer` argument is a function that accepts a list of items and returns a list of items that will be passed to
page schema validation stage.