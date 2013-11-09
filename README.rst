====
Sona
====

Sona is a language-aware search tool for Python. Instead of searching for string patterns you tell Sona you want a all function definitions with a name ``name``. In other words, Sona uses the syntactic and semantic constructs of your source code to find matches.

Sona uses a concept called Assertion-Based Search. By mixing assertions with simple conditions (like ``==`` and ``!=``) you can tell Sona not only *what* you want (be it functions, classes, variable assignments, and so on) but *which* ones you want. A naive Boolean query language is not sufficient to capture both dimensions easily.

As great as ``grep`` is, it's a line-based pattern tool; it knows nothing about what it searches and makes no effort to distinguish between comments, strings and code. Sona uses static analysis to parse your source code -- no actual code is ever executed -- and can therefore uncover things based on the *structure* of your code: want a list of all functions declared in your source files? No problem.

Why You Should Use Sona
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Python-aware search. Search by function/class name definitions, imports in a module, function calls, and more;
* Sona understands git and will search all your python source code stored in your current HEAD;
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

Of course, there's nothing stopping you from gathering a list of function *and* class definitions in the same result set:

::

   fn:name; cls:name

What if you're looking for all ``__init__`` constructors, but only want ones that have 3 arguments?

::

   fn:name == "__init__", cls:argcount == 3

Observe that instead of splitting our two assertions into two expressions, delimited by ``;``, we used a ``,`` instead -- and the reason for that is simple: commas filter on the existing result set, and semicolons retrieve a new one. So the following query

::

   fn:name == "__init__"; fn:argcount == 3

would give you all function definitions with ``name`` equal to ``__init__`` **and** the set of functions with an ``argcount`` of ``3``.
