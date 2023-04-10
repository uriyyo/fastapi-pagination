Let's create a custom pagination class that will allow us to paginate `sqlalchemy` queries.

```py
{! ../docs_src/tutorials_advanced/custom_paginate.py !}
```


## Step 1: create `paginate` function

First, we need to create a function that will paginate `sqlalchemy` queries.
`paginete` is a common name for this function, but you can use any name you want.

```py hl_lines="13"
{! ../docs_src/tutorials_advanced/custom_paginate.py !}
```

## Step 2: define required function parameters

```py hl_lines="16-19"
{! ../docs_src/tutorials_advanced/custom_paginate.py !}
```

Parameters:

* `params` - `AbstractParams` instance that contains pagination parameters.
* `tranformer` - function that will be used to transform items.
* `additional_data` - additional data that will be added to created page.

## Step 3: verify that `params`

```py hl_lines="21"
{! ../docs_src/tutorials_advanced/custom_paginate.py !}
``` 

Verify that `params` is a instance of `limit-offset` pagination params type.

## Step 4: fetch total number of items

```py hl_lines="23"
{! ../docs_src/tutorials_advanced/custom_paginate.py !}
```

## Step 5: fetch items

```py hl_lines="24-25"
{! ../docs_src/tutorials_advanced/custom_paginate.py !}
```

## Step 6: transform items

```py hl_lines="27"
{! ../docs_src/tutorials_advanced/custom_paginate.py !}
```


## Step 7: create page and return it

```py hl_lines="29-34"
{! ../docs_src/tutorials_advanced/custom_paginate.py !}
```