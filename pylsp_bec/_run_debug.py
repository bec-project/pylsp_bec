import sys

from pylsp.__main__ import main

if __name__ == "__main__":
    sys.argv = ["pylsp", "--ws", "-v", "--port", "5678"]
    main()
