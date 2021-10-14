Frequently Asked Questions
==========================

Nobody actually asks these things. But if they did, these would be the
answers!


What's the Purpose of this Project?
-----------------------------------

I've worked with a Koji deployment on a nearly daily basis as part of
my job for more than a decade. Over that time I have collected a fair
number of scripts, aliases, and little tricks. This project represents
my attempt to coalesce that collection into a reusable set of features
that anyone else working with Koji can use.

The more I develop Koji Smoky Dingo, the more opportunities I've
realized for additional features. In a way, this project is the
manifestation of my own Koji wish list.


Why Is It Called Koji Smoky Dingo?
----------------------------------

Because project naming is a right pain in the butt. I ran through a
few 2-slugs from coolname_ until
the words "Smoky Dingo" popped up, and that tickled my fancy so I went
with it.

.. _coolname: https://pypi.org/project/coolname/

You'll note a somewhat ridiculous adherence to that naming scheme in
the API. The base class for plugin commands is a `SmokyDingo`. The
base exception class is a `BadDingo`. A standalone command is a
`LonelyDingo`. The filtering mini-language is `Sifty Dingo`. It makes
me happy.

Since the name "Koji Smoky Dingo" is fairly long, I frequently refer
to it as simply "KSD".


Why Not Contribute Directly to Koji?
------------------------------------

Because it's unreasonable to expect the Koji project to maintain some
of these ideas. In a few cases, sure a given command could have been a
good fit for the core client. However, the Koji project is
significantly more mature than Koji Smoky Dingo is. By remaining
separate I keep a level of freedom in how I implement the API and
features. I can smash together an idea quickly and get it committed
without having to prove my case to any core developers. The Koji
developers have to worry about feature creep, stale code, API
compatability, etc. As a totally separate entity, KSD can iterate very
fast to try and match my ever-changing vision of what an ideal
"helper" layer should look like.

Since KSD finally reached version 1.0, I do have to worry about API
stability. However even then I will still have more flexibility than a
project that has to worry about being a critical component in the
build infrastructure for so many organizations. Therefore it's
extremely likely that KSD will always remain separate... but hopefully
popular enough one day that any advanced Koji user will also be a Koji
Smoky Dingo user.


Why Is There An Entire Mini Language In Here?
---------------------------------------------

I discovered that a number of my more complicated scripts were simply
taking a big collection of things (usually builds, but sometimes
tags), and trying to identify relationships or features to filter
through them. I'd custom craft these scripts to try and be as polite
to our Koji instance as possible -- using multicalls, only
authenticating if I was using an API that needed it, de-duplicating
and caching as much data as possible, etc. As I began to port these
scripts into KSD I began trying to imagine a better way to do work
with this sort of tooling. I wanted an easier way to write the sorts
of questions I was asking Koji, while simultaneously not making them
act rudely.

The idea came to me that I could produce a filtering and flagging
pipeline where individual predicates could be used in stages -- first
allowed to prepare for filtering by requesting the necessary data from
Koji all at once, and then applying that information to filter the set
of data elements. The trick would be to author logical combining
operators in such a way that they only invoked their nested predicates
with the elements that were truly relevant, slowly reducing the load
of lookups.

Having such a pipeline API would solve the problem of filtering from
within scripts, but what if I wanted to be able to supply filtering
options from the command-line?  What if that filtering was very
complicated?  Well, s-expressions are very easy to parse, and I've
written trivial (and admittedly somewhat crappy) parsers before for
other projects. One such past project was even used to serve a very
similar concept, filtering through bookmarks in the (now defunct)
del.icio.us service. So I took parts of that old parser and ported it
into what became Koji Sifty Dingo, an s-expression based predicate
language!


Why Do You Still Support Python 2.6?
------------------------------------

Because I use a number of hosts that have RHEL 6 on them, and I very
much want to be able to use Koji Smoky Dingo in those environments.

As much as people complain about Python 2, it feels pretty darn
trivial to support older versions. Even when these hosts get upgraded
to newer versions of RHEL or CentOS, I will mostly likely maintain
backwards compatibility for a pretty long time. The only feature I
truly yearn for is syntactic changes in Python 3 where keyword-only
arguments can be expressed after variadic positionals. I'd really
prefer to use that in the Sieve API instead of the `set_options`
method.

Honestly, the biggest struggle has been in working with multiple
versions of Koji. Or working with multiple versions of libraries under
Python 3 to dodge the deprecation churn.

KSD version 2.0 will drop Python 2 support. I'm not sure how long
I'll provide backports to the 1.0 line after that... it likely depends
on how long I have to use a RHEL 6 machine.


Can I Write My Own Tools On Top of Koji Smoky Dingo?
----------------------------------------------------

You absolutely can. There's an examples directory which highlights how
to use it to create your own scripts, commands, and custom sieve
predicates.


Can I Get Involved?
--------------------

It's open source software, you don't have to ask! File an RFE, fork
the project on GitHub, write the code you want to see in the world,
and submit a PR. If you have questions about how things work we can
communicate in the tracker.

I'd also be happy to receive patches or pull requests for
documentation and unit tests.

No hate though, you keep that stuff in your tummy.
