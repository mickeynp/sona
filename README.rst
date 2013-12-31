====
Sona
====

Sona is a language-aware command line search tool for Python. Sona understands Python code and can pick out, filter, and display the important bits of the code -- like function and class names, including their arguments; variable names and variable assignments; function calls and object creation; class inheritance hierarchy; and so much more!

Sona is a truly versatile tool for any Python developer. It all but eliminates the need for grepping, whether you're hunting for a function definition you know exist *somewhere* -- or if you're looking for something more complex, like a method belonging to a particular class with a precise number of arguments.

Sona uses a concept called Assertion-Based Search. By mixing assertions with simple, familiar, conditionals (like ``==``, ``!=``, ``in`` and ``not in``) you can tell Sona not only *what* you want (be it functions, classes, variable assignments, and so on) but *which* ones you want. A naive Boolean query language is not sufficient to capture both dimensions easily.

As great as ``grep`` is, it's a line-based pattern tool; it knows nothing about what it searches and makes no effort to distinguish between comments, strings and code. Sona uses static analysis to parse your source code -- no actual code is ever executed -- and can therefore uncover things based on the *structure* of your code: want a list of all functions declared in your source files? No problem.

Why You Should Use Sona
~~~~~~~~~~~~~~~~~~~~~~~

* Sona does Python-aware search. Search by function/class name definitions, function calls, classes and their methods, and more;
* Sona will by default search your git repository (using your current HEAD and branch) for Python files;
* Simple, expressive and powerful assertion-based language with Python regular expression support;
* Comes with built-in output for Emacs, JSON and Grep;
* Sona understands code with syntax errors in it, and will try to parse it anyway;
* User-friendly command line interface aimed at developers;

Simple Assertion Examples
-------------------------
Here's a few sample queries to whet your appetite. Let's start with one of the most fundamental *assertions* you can declare.

::

   fn:name

This simply tells Sona you want all function *declarations* from all the files you tell it to search.

If you want to narrow down the scope of function declarations to just the ones matching a certain string, you could make the following assertion

::

   fn:name == "download_file"

If you want more than just one set of function declarations returned, you must add a new *expression* -- this is trivially done by separating your assertion with ``;``, like so:

::

   fn:name == "download_file"; fn:name == "upload_file"

You could also use the ``in`` operator

::

   fn:name in {"download_file", "upload_file"}

Of course, there's nothing stopping you from gathering a list of function *and* class definitions in the same result set:

::

   fn:name; cls:name

What if you're looking for all ``__init__`` constructors, but only want ones that have 2 or 3 arguments?

::

   fn:name == "__init__", fn:argcount in {2, 3}

Observe that instead of splitting our two assertions into two expressions, delimited by ``;``, we used a ``,`` instead -- and the reason for that is simple: commas filter on the existing result set, and semicolons retrieve a new one. So the following query

::

   fn:name == "__init__"; fn:argcount in {2, 3}

would give you all function definitions with ``name`` equal to ``__init__`` **and** the set of functions with an ``argcount`` of ``2`` or ``3``.

===========================
Sona Query System Reference
===========================
This is the reference for the Sona Query System, and it will cover the syntax of the query language; the operational features and constraints; and a complete list of all locators.

Sona Query System is loosely inspired by Python's syntax, yet not so closely that you are likely to apply Python language constructs -- which is obviously a considerably more expressive language -- to Sona.

Queries
~~~~~~~

The two most important concepts about Sona's Assertion system are **Assertions** and **Expressions**. A string of assertions and expressions are referred to as a **query**.

More formally, a query looks like this:

::

   <assertion 1_1>, ...., <assertion N_1>; <assertion 2_1>, ...
   \------------------------------------/
                 Expression 1
   \-----------------------------------------------------------/
                               Query

Expressions
~~~~~~~~~~~

An expression is made up one-to-many assertions. Each expression, delimited by a ``;``, consitutes a new result set. That is, it is possible to request several sets of results by using many expressions and apply different assertions to each one. The combined results of all expressions in a query will be then displayed.


Assertions
~~~~~~~~~~

Each assertion can express exactly one fact about what you are looking for. Subsequent assertions **in the same expression** further filter the previous assertion's result set, starting from the left and moving to the right. There are no precedence semantics.

:NOTE: As each assertion passes the result set forward, left-to-right, an assertion that returns no matches **will terminate with an empty result set**. Run sona with ``--log-level=debug`` to see how Sona applied your assertions if you expected matches but didn't get any.

Assertions are always associative; the order in which you write them does not matter. ``fn:argcount == 2, fn:name == 'Hello'`` will yield the same result as ``fn:name == 'Hello', fn:argcount == 2``.

Fields and Field Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each assertion will require one field followed by one field attribute, separated with a ``:``, like so:

::

   field:attribute

The field is the category of node (syntactic construct) you want to act on. Some nodes will map directly to a known concept (such as ``fn`` to ``def``) -- others are more abstract or generic and may not have a direct correspondence to any one language construct in Python.

Filtering a field is optional. If you do not specify a condition, then everything that matches the assertion will be shown.

:NOTE: Unconditional assertions are *no-op* unless they are the first assertion in an expression.

A field attribute is, like the field itself, an idealized name for the sort of field you want to filter by. For instance ``name`` refers to the name of a function definition in the field ``fn``, and to a class definition in the field ``cls``. Some field attributes do not have a direct equivalent in Python, and like the field, they are named for convenience and clarity, not accuracy.

When an operator is used in an assertion it will narrow the result set of the previous assertion **only**.

Field Operators
---------------

+------------+----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
| Operator   | Description                      | Example                                                                                                                           |
+============+==================================+===================================================================================================================================+
| ``==``     | Case-sensitive equality check.   | ``fn:name == 'Hello'`` will return all function definitions named ``Hello``                                                       |
+------------+----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
| ``!=``     | Case-sensitive inequality check. | ``fn:name != 'Hello'`` will return all function definitions **not** named ``Hello``                                               |
+------------+----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
| ``in``     | Case-sensitive membership test.  | ``fn:name in {'Hello', 'Goodbye'}`` will return all function definitions found in the set of ``Hello`` or ``Goodbye``             |
+------------+----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------+
| ``not in`` | Case-sensitive membership test.  | ``fn:name not in {'Hello', 'Goodbye'}`` will return all function definitions **not** found in the set of ``Hello`` or ``Goodbye`` |
+------------+----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------+

Data types
----------

Sona will recognise three data types:

+--------------------+-----------------------------------------------------------------------+
| Data Type          | Description                                                           |
+====================+=======================================================================+
| Strings            | As in Python, use either ``'`` or ``"`` quote symbols.                |
|                    |                                                                       |
+--------------------+-----------------------------------------------------------------------+
| Integers           | As in Python                                                          |
+--------------------+-----------------------------------------------------------------------+
| Sets               | Unordered, like in Python. The syntax is ``{elem1, ..., elemN}``      |
|                    |                                                                       |
|                    |                                                                       |
|                    |                                                                       |
+--------------------+-----------------------------------------------------------------------+

List of Locators
~~~~~~~~~~~~~~~~
This is a complete list of locators known to Sona.

+-----------------------------------------------------------------+
|          ``FN``: Fields involving Functions.                    |
+========================+========================================+
|``name``                |Matches the name of a function          |
|                        |definition.                             |
|                        |                                        |
|                        |Example: ``fn:name == 'Hello'`` matches |
|                        |all function definitions named          |
|                        |``Hello``.                              |
+------------------------+----------------------------------------+
|``argcount``            |Matches the count of a function         |
|                        |definition's arguments.                 |
|                        |                                        |
|                        |Example: ``fn:argcount in {2, 3}``      |
|                        |matches all function definitions with 2 |
|                        |or 3 arguments.                         |
+------------------------+----------------------------------------+
|``parent``              |Matches a parent of a                   |
|                        |function definition.                    |
|                        |                                        |
|                        |Example: ``fn:parent == "MyClass"``     |
|                        |matches all functions that have a       |
|                        |parent called ``MyClass``.              |
+------------------------+----------------------------------------+
|``call``                |Matches all function and method calls   |
|                        |that Sona can resolve with static       |
|                        |analysis.                               |
|                        |                                        |
|                        |Example: ``fn:call == "download_file"`` |
|                        |finds all calls to ``download_file``.   |
+------------------------+----------------------------------------+


+-----------------------------------------------------------------+
|          ``cls``: Fields involving Classes.                     |
+========================+========================================+
|``name``                |Matches the name of a class definition. |
|                        |                                        |
|                        | Example: ``cls:name == 'MyClass'``.    |
|                        |                                        |
+------------------------+----------------------------------------+
|``parent``              |Matches the bases (parents) of a class  |
|                        |                                        |
|                        |Example: ``cls:parent == 'object'``.    |
+------------------------+----------------------------------------+
