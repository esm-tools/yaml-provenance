.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
======================

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/esm-tools/yaml-provenance/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Your Python version and ``yaml-provenance`` version.
* A minimal reproducible example that demonstrates the bug.
* Any details about your local setup that might be helpful in troubleshooting.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

yaml-provenance could always use more documentation, whether as part of the
official docs, in docstrings, or even on the web in blog posts, articles,
and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at
https://github.com/esm-tools/yaml-provenance/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
============

Ready to contribute? Here's how to set up ``yaml-provenance`` for local
development.

1. Fork the ``yaml-provenance`` repo on GitHub.

2. Clone your fork locally::

    $ git clone https://github.com/your-username/yaml-provenance.git

3. Create a virtual environment and install the package in development mode
   with test dependencies::

    $ cd yaml-provenance
    $ python -m venv venv
    $ source venv/bin/activate
    $ pip install -e ".[test,docs]"

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, run the test suite::

    $ pytest

   You can also run tests with coverage::

    $ pytest --cov=yaml_provenance

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
=======================

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests for any new functionality or bug fixes.

2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring.

3. The pull request should work for Python 3.8, 3.9, 3.10, 3.11, and 3.12.

Code Style
==========

* Follow `PEP 8 <https://peps.python.org/pep-0008/>`_ conventions.
* Use type hints where they improve clarity, but they are not required
  everywhere.
* Write docstrings in `NumPy style
  <https://numpydoc.readthedocs.io/en/latest/format.html>`_.

Deploying
=========

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in CHANGELOG).
Then run::

    $ bumpversion patch  # possible: major / minor / patch
    $ git push
    $ git push --tags
