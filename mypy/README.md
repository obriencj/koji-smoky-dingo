# MyPy Type Checking

Static type analysis can be pretty helpful, so we do that here. This
directory holds supporting content towards that end.

Note that none of the code in this directory is utilized at runtime
from within KSD. It only exists to provide comparisons for [MyPy]'s
analysis.

[MyPy]: https://mypy-lang.org/


## koji typing stub

The koji project does not provide typing information for its python
API. Moreover, the `ClientSession` class which we use to communicate
to a koji instance is primarily dynamic, producing members to act as a
virtual XMLRPC interface on-demand. This makes it really hard to
identify whether we're using the client API correctly during static
analysis. Thus I created a typing stub for use when checking against
koji. In addition, I added signatures for the hub-side calls that a
`ClientSession` would correctly respond to. This [stub] needs to be
kept up-to-date against the upstream koji project regularly (or at
least whenever we start using a newly added API call).

[stub]: ./koji/__init__.pyi


## proxytype plugin

`koji.ClientSession` and its dynamic methods are one thing to
workaround, but the `koji.MultiCallSession` is an entirely different
beast. This class has all the same methods as the `ClientSession` but
they're wrapped so that they return a `koji.VirtualCall` wrapper
around their result.

To save my sanity, I wrote a mypy [plugin] that will allow me to munge
an empty class definition with all the methods stolen from my work on
documenting `ClientSession` API, modified with that `VirtualCall`
return type.

[plugin]: ./proxytype.py
