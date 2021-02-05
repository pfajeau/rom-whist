from tests import test_belote_ai
from tests import test_ohell_ai
from tests import test_belote
from tests import test_ohell

def main():
    test_ohell.main()
    test_ohell_ai.main()
    test_belote.main()
    test_belote_ai.main()

if __name__ == '__main__':
    main()
