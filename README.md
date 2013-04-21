```
                                        _
                                       ( )
      ___    _     ___ ___   _ _      _| |
    /'___) /'_`\ /' _ ` _ `\( '_`\  /'_` |
   ( (___ ( (_) )| ( ) ( ) || (_) )( (_| |
   `\____)`\___/'(_) (_) (_)| ,__/'`\__,_)
                            | |
                            (_)
```

A competition daemon for Student Robotics.

Many Scarzies died to bring us this implementation.

History
=======

This will be the fourth implementation of compd in as many years. Hopefully this one, being simpler than the others, will actually stick.

Getting Started
===============

To install:

1. Install redis, version 2.6 or later
2. Install python development tooling (via, eg, *sudo apt-get install python-dev*)
3. Install virtualenv (via, eg, *sudo easy_install virtualenv*)
4. Run *./install*

All other dependencies, through the magic of virtualenv, are installed locally - in the *dep* directory as a matter of fact.

To run, use *./run*.

To develop, enter the virtualenv using *./shell*.

Interfaces
==========
There is one main interface to compd, which is just a direct socket connection.

The socket connection is available on port 18333 (by default, set by `control_port` in `config.yaml`)
on the host machine. Into this connection, commands can be pumped with a newline as the terminating character.
For instance:
~~~~
echo list-teams | nc localhost 18333
~~~~
Because it sucks to have to pipe things through netcat, there's a wrapper cli
that can be used instead:
~~~~
./command list-teams
~~~~

Credit
======

This implementation done through effective slave labour by Alistair Lynn.

With thanks to Rob Spanton, Scarzy, Sam Phippen, Edd Seabrook and Ben Clive for ideas and work on the previous iterations.
