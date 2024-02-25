# Old way of customization

!!! warning "Old way of customizing pagination"

    `Page.with_custom_options` and `Page.with_params` methods are now deprecated.
    They will be removed in the next major release.

    Please use `CustomizedPage` instead.

To customize pagination, you should use new `CustomizedPage` annotated-like class.
It allows you to change default pagination in `mypy` compatible way.

The main issue with old `Page.with_custom_options` and `Page.with_params` methods 
was that they were not `mypy` compatible.
It means that you could not use them with `mypy` type checking, because they return 
new class objects and `mypy` does not support such ways.

# Customization

First, let's import all necessary components:

```py
{!../docs_src/tutorials_advanced/customization.py [ln:1-9]!}
```

Now we can customize our page.

### Change name

If you want to change default name of page class, you should use `UseName` customizer:

```py
{!../docs_src/tutorials_advanced/customization.py [ln:11-14]!}
```

1. Now your class will be names 'IntPage' instead of 'CustomizedPage'.

!!! note
    
    Everytime you customize page, name of the class will be changed to `your-class-name` + "Customized".
    In order to change it, you should use `UseName` customizer.


### Change total behavior

By default, cursor-based page don't include total count of items, and offset-based page include it.
If you want to change this behavior, you should use `UseIncludeTotal` customizer:

```py
{!../docs_src/tutorials_advanced/customization.py [ln:16-19]!}
```

1. Now when you will paginate using `PageNoToal` class, it will not include total count of items.

### Change params default values

If you want to change default values of pagination parameters, you should use `UseParamsFields` customizer:

```py
{!../docs_src/tutorials_advanced/customization.py [ln:21-24]!}
```

1. Now when `size` parameter is not provided, it will be equal to 500.


### Make params fields optional

If you want to change type of pagination parameters, you should use `UseParams` customizer:

```py
{!../docs_src/tutorials_advanced/customization.py [ln:26-29]!}
```

1. Now all pagination parameters will be optional.


### Change page params type

If you want to change type of page parameters, you should use `UseParams` customizer:

```py
{!../docs_src/tutorials_advanced/customization.py [ln:31-39]!}
```

1. Now `Page.__params_type__` attribute will be point to `MyParams` class.


### Combine multiple customizers

You can use multiple customizers at once, just pass them as to regular `Annotated`:

```py
{!../docs_src/tutorials_advanced/customization.py [ln:41-47]!}
```

1. Now `CustomPage` will have `CustomPage` name, no total count of items, all params optional.