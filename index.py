#! python3

from interface import tui
import curses


def main():
    curses.wrapper(tui.TerminalInterface)


if __name__ == "__main__":
    main()
