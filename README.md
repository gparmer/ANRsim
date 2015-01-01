ANRsim
======

A discrete event simulator for Android: Netrunner, a collectable card game made by Fantasy Flight Games.

FAQ
===

Why a simulator, rather than a statistical analysis?
----------------------------------------------------

A statistical analysis of many of the phenomenon within a typical economy, let alone the interactions between runners and coporations is intractable.  The first program I wrote to get information about simple runner economies did not answer a number of key questions:  What is the variablility within an economy, often referred to as its "consistency".  What is the interaction between many cards with dependencies (e.g. Prepaid Voice Pad with events)?  How does one account for changes in use of a card over time that are required in specific circumstances (Test Running out a Magnum Opus)?  The easiest way to answer these questions is with a simulation that has since turned into a full-blown discrete event simulation.

Why is it useful?
-----------------

The ANR community has many honed intuitions about what economies work under which circumstances.  This project is meant to investigate massive numbers of somewhat idealized games (i.e. a model of real games), to determine scientifically why some economties are better than others, under which circumstances, and provide guidance for deckbuilding.

What assumptions is the simulator making?
-----------------------------------------

A number of assumptions are made that simply the game into a state that can be reasonably and usefully simulated:

- Hand size is infinite.
- We consider only clicks used for "macro".  That is, only clicks that you would normally use to gain credits, or cards.  If you run once per turn, and install a program at about the same rate, then the other two clicks per turn will likely be used for macro (econ and card management).  Thus, there is not a direct correspondance between the click number in the simulation, to the click number in the real game.
- There is currently *no interaction* between runner and corp.  The results of this simulation are meant to provide information to a runner regarding how efficient each click spent on econ/draw is.  This is the largest assumption, but is necessary to simply the game to the level where a simulation provides useful information.
- An ordering, or priority, is assigned to different cards that is used to determine which action to take with any given click.  This ordering is derived from my own experience with playing ANR, and watching others play.

Non-trivial aspects of the game we do consider:

- Mulligan.
- Starting hard size.
- Deck size.
- Many different cards, with their specific rules (e.g. Earthrise Hotel, Test Run, SMC, Lucky Find).

Those are bad assumptions!  They don't represent a real game.
-------------------------------------------------------------

That's not a question, but we'll answer anyway ;-).

Every simulation operates on a *model* of the real phenomenon.  Models are simplified systems that attempt to 1) be tractable to simulate, and 2) in doing so, still provide useful information about the actual phenomenon.  The question is if the model is simplified to the point of being useless?

I believe the results from this simulation provide useful information for deckbuilding that is somewhat tangential to the other information sources we have.  Other sources include:

- *Personal experience.*  As we play, we glean an intuition about if a given set of cards (e.g. an economic package) work in a given deck.  What works, and what doesn't work are fit into the feedback loop of deck building.

- *Crowdsourced experience.* We talk to our friends, and read online sources (bgg, stimhack, netrunner.reddit.com) thus crowd sourcing some of this knowledge.  NetrunnerDB is perhaps one of the best sources for this, if you already have significant personal experience.

- *Statistical Analysis.*  It is not difficult to compute the percent chance that you can get one of a set of cards in your starting hand with mulligan.  I know, for instance, that my Kit decks have ~90% chance of finding my econ engine reliably.  However, how does it impact my economy if I don't find it immediately?  With multiple ways of finding my econ, how do each of them impact the "credit curve"?  These are answers that a simple statistical analysis won't reliably provide.

The **ANRsim** provides statistical measures, and a foundation for analysis of specific economic packages.  Econ is, of course, only one side of the equation, and cannot be considered in a vacuum.  Different decks require different econs (burst vs. consistent, early-game vs. late, etc...), but once the required econ is identified, this simulation should provide a useful source of information for which economic engines will satisfy your requirements.

A hidden benefit is that we can investigate changes in the meta by instantly (well, nearly instantly) playing thousands of games, and determining the impact of a card, or set of cards in a given meta.

When will the code be released?
-------------------------------

It needs to be fleshed out in a few areas.  Once they are done, I'll release it.  These areas include, but aren't limited to:

- Adding logic to investigate consistency in getting breakers out.  This will require adding a dependency engine into the simulator that understands MU, credits (already done), and program/hardware dependencies.

- Adding Corporation logic.  This is tricky as the corp econ is much more dependent on the runner's actions, thus the difficulty here is finding an appropriate model, and co-simulating the runner with the corp.

Who am I?
=========

I'm a [professor](http://www.seas.gwu.edu/~gparmer) of CS at GWU.  I write systems, and  mainly hack on operating systems.  Our [*Composite*](http://composite.seas.gwu.edu) component-based operating system is my main passion.  However, when I need to de-stress, I play ANR.  The Capital Area Netrunner group is awesome for this.
