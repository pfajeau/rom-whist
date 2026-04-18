"""
This module implements test all functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from tests import test_belote_ai
from tests import test_ohell_ai
from tests import test_belote
from tests import test_ohell
from tests import test_contree
from tests import test_contree_ai

def main():
    test_ohell.main()
    test_ohell_ai.main()
    test_belote.main()
    test_belote_ai.main()
    test_contree.main()
    test_contree_ai.main()

if __name__ == '__main__':
    main()
