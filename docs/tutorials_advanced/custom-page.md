Let's create custom page parameter that is compatible with JSON API 1.0 specification.

```py
{! ../docs_src/tutorials_advanced/custom_page.py !}
```

## Step 1: Create pagination params


```py hl_lines="10-15"
{! ../docs_src/tutorials_advanced/custom_page.py !}
```

## Step 2: override `to_raw_params` method 

```py hl_lines="14-15"
{! ../docs_src/tutorials_advanced/custom_page.py !}
```

## Step 3: Create custom page

```py hl_lines="18-51"
{! ../docs_src/tutorials_advanced/custom_page.py !}
```

## Step 4: override `create` page method

```py hl_lines="35-51"
{! ../docs_src/tutorials_advanced/custom_page.py !}
```

## Example

Now we can use `JSONAPIPage` in our API.

```py
@app.get("/users")
def get_users() -> JSONAPIPage[UserOut]:
    return paginate(...)
```
