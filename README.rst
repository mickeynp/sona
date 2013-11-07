============
 PySemantic
============

Introduction
============

PySemantic is a language-aware search tool for Python. Instead of searching for strings you search for semantic or syntactic constructs using a query language where you make assertions about what you want PySemantic to return.

PySemantic uses a concept called Assertion-Based Search. By mixing assertions with conditions you can tell PySemantic not only *what* you want (be it functions, classes, variable assignments, and so on) but *which* ones you want. A naïve boolean query language is not sufficient to capture both dimensions.

Simple Assertion Examples
-------------------------
Let's say you want a complete list of all functions found by PySemantic. The assertion for that would simply be

::

   fn:name

and that's it. If you want to filter by functions named "hello", the assertion would instead be

::

   fn:name == "hello"

Let's say you want a list of all function names *and* class names you would make the following assertions

::

   fn:name; cls:name

As you can see, the syntax is similar to the first example, but in order to express more than one assertion at a time, you must delimit each assertion with a semicolon `;`. Each assertion makes one claim -- to either return a list of everything that has a field, such as `fn:name`, or a subset of that very list, such as `fn:name == "hello"`.

