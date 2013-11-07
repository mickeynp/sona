============
 PySemantic
============

Introduction
============

PySemantic is a language-aware search tool for Python. Instead of searching for string patterns you search for semantic or syntactic constructs using series of assertions about what you want your results to be.

PySemantic uses a concept called Assertion-Based Search. By mixing assertions with conditions you can tell PySemantic not only *what* you want (be it functions, classes, variable assignments, and so on) but *which* ones you want. A naïve boolean query language is not sufficient to capture both dimensions.

As great as ``grep`` is, it's a line-based pattern tool; it knows nothing about Python and does little to help you find the things you really care about - like functions named a certain way or with a certain number of arguments. PySemantic uses static analysis to parse your source code -- no actual code is ever executed. As such -- and this is particularly true where there is heavy use of Python's dynamic nature -- PySemantic may not uncover things it cannot compute by simpy analyzing the code statically.

Why You Should Use PySemantic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Python-aware search. Search by function/class name definitions; imports in a module; function calls and more!
* PySemantic understands git and will search for files that exist only in git;
* Simple, expressive and powerful assertion-based language with Python regular expression support;
* Comes with built-in support for Emacs;
* PySemantic uses multiprocessing to speed up parsing.

Simple Assertion Examples
-------------------------
Let's say you want a complete list of all ``function definitions`` found by PySemantic. The assertion for that would simply be

::

   fn:name

and that's it. If you want to filter by ``function definitions`` named "hello", the assertion would instead be

::

   fn:name == "hello"

Let's say you want a list of all ``function name definitions`` ``and`` ``class name definitions`` you would make the following assertions

::

   fn:name; cls:name

As you can see, the syntax is similar to the first example, but in order to express more than one assertion at a time, you must delimit each assertion with a semicolon ``;``. Each assertion makes one claim -- to either return a list of everything that has a field, such as ``fn:name``, or a subset of that very list, such as ``fn:name == "hello"``.

But what if you want a list of all ``class name definitions`` but only a subset of all ``function name definitions`` that are named ``upload_file`` and ``download_file`` -- well, it's easy:

::

   cls:name; fn:name == "upload_file", fn:name == "download_file"

or just,

::

   cls:name; fn:name == r"(upload|download)_file"

using a regular expression.
