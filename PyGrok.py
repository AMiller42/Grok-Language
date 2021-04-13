#!/usr/bin/python

"""
Modified from official ><> interpereter found at https://gist.github.com/anonymous/6392418
Python interpreter for the esoteric language Grok.
Usage: ./Grok.py --help
More information: http://esolangs.org/wiki/Grok
Requires python 3 or higher.
"""

import sys
import time
import random
from collections import defaultdict

# constants
NCHARS = "0123456789"
ARITHMETIC = "+-*%" # not division, as it requires special handling
COMPARISON = { "=": "==", ">": ">" }
DIRECTIONS = { "l": (1,0), "h": (-1,0), "j": (0,1), "k": (0,-1) }


class _Getch:
    """
    Provide cross-platform getch functionality. Shamelessly stolen from 
    http://code.activestate.com/recipes/134892/
    """
    def __init__(self):
        try:
            self._impl = _GetchWindows()
        except ImportError:
            self._impl = _GetchUnix()

    def __call__(self): return self._impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()
getch = _Getch()


def read_string():
    #Read one character from stdin. Returns -1 when no input is available.
    if sys.stdin.isatty():
        # we're in console, read a character from the user
        char = " " 
        string = ""
        sys.stdout.write("> ")
        sys.stdout.flush()
        while (True): # while character isn't carriage return or line feed
            char = getch()
            if ord(char) == 3:  #check for ctrl-c (break)
                sys.stdout.write("^C")
                sys.stdout.flush()
                raise KeyboardInterrupt
            if ord(char) in {10, 13}:
                break
            string += str(char)
            sys.stdout.write(char)
            sys.stdout.flush()
        sys.stdout.write("\n")
        return string
    else:
        # input is redirected using pipes
        string = input()
        # return -1 if there is no more input available
        return string if string != "" else -1


class Interpreter:
    """
    Grok interpreter.
    """
    def __init__(self, code):
        """
        Initialize a new interpreter.
        Arguments:
            code -- the code to execute as a string
        """
        # check for hashbang in first line
        lines = code.split("\n")
        if lines[0][:2] == "#!":
            code = "\n".join(lines[1:])
        
        # construct a 2D defaultdict to contain the code
        self._wordbox = defaultdict(lambda: defaultdict(int))
        line_n = char_n = 0
        for char in code:
            if char != "\n":
                self._wordbox[line_n][char_n] = 0 if char == " " else ord(char)
                char_n += 1
            else:
                char_n = 0
                line_n += 1
        

        self._position = [-1,0]
        self._direction = DIRECTIONS["l"]
        
        # are we in debug mode? (real error messages displayed)
        self._debug = False

        # the register is initially empty
        self._register = 0
        # string mode is initially disabled
        self._string_mode = None
        self._num_entered = False
        # have we encountered a skip instruction?
        self._skip = False
        
        self._insert_string = ""

        self._stack = []

        # is the last outputted character a newline?
        self._newline = None
    
    def move(self):
        """
        Move one step in the execution process, and handle the instruction (if
        any) at the new position.
        """
        # move one step in the current direction
        self._position[0] += self._direction[0]
        self._position[1] += self._direction[1]

        # wrap around if we reach the borders of the wordbox
        if self._position[1] > max(self._wordbox.keys()):
            # if the current position is beyond the number of lines, wrap to the top
            self._position[1] = 0
        elif self._position[1] < 0:
            # if we're above the top, move to the bottom
            self._position[1] = max(self._wordbox.keys())
        
        if self._direction[0] == 1 and self._position[0] > max(self._wordbox[self._position[1]].keys()):
            # wrap to the beginning if we are beyond the last character on a line and moving rightwards
            self._position[0] = 0;
        elif self._position[0] < 0:
            # also wrap if we reach the left hand side
            self._position[0] = max(self._wordbox[self._position[1]].keys())
        
        # execute the instruction found
        if not self._skip:
            instruction = int(self._wordbox[self._position[1]][self._position[0]])
            # the current position might not be a valid character
            try:
                # use space if current cell is 0
                instruction = chr(instruction) if instruction > 0 else " "
            except:
                instruction = None
            if self._debug:
                try:
                    self._handle_instruction(instruction)
                except StopExecution:
                    raise
                except KeyboardInterrupt:
                    # avoid catching as error
                    raise KeyboardInterrupt
            else:
                try:
                    self._handle_instruction(instruction)
                except StopExecution:
                    raise
                except KeyboardInterrupt:
                    # avoid catching as error
                    raise KeyboardInterrupt
                except Exception as e:
                    raise StopExecution("You don't grok Grok.")
            return instruction
        
        self._skip = False
    
    def _handle_instruction(self, instruction):
        """
        Execute an instruction.
        """
        if instruction == None:
            # error on invalid characters
            raise Exception
        

        # handle insert mode
        if self._string_mode == "insert" and instruction != "`":
            self._insert_string += str(instruction)
            return

        # handle insert escape
        elif self._string_mode == "insert" and instruction == "`":
            is_num = True
            string = self._insert_string
            for char in string:
                if char not in NCHARS:
                    is_num = False
                    break
            if is_num:
                self._push(int(string))
            else:
                string = string[::-1]
                for char in string:
                    self._push(ord(char))
            self._insert_string = ""
            self._string_mode = None

        
        # handle regin mode
        elif self._string_mode == "regin" and instruction != "`":
            if instruction in NCHARS:        # if the instruction is a number, push it and continue in regin
                self._register = ( str(instruction) if not self._num_entered else self._register + str(instruction) )
                self._num_entered = True
                return
            elif instruction not in NCHARS:
                self._string_mode = None        # if the instruction is not a number, end regin mode and execute it
                if self._num_entered:
                    self._register = int(self._register)
                    self._num_entered = False
                else:
                    self._register = ord(instruction)  # if not a number and is first instruction in regin,
                    return                             # push it and end regin mode

        # handle regin escape
        elif self._string_mode == "regin" and instruction == "`":
            if self._num_entered:
                self._register = int(self._register)
                self._num_entered = False
            self._skip = True
            self._string_mode = None


        # handle escape
        elif self._string_mode == None and instruction == "`":
            self._skip = True


        # instruction is one of kjlh, change direction
        elif instruction in DIRECTIONS:
            self._direction = DIRECTIONS[instruction]

        # instruction is 0-9, push corresponding int value
        elif instruction in NCHARS:
            self._push(int(instruction))
        
        # instruction is an arithmetic operator
        elif instruction in ARITHMETIC:
            a, b = self._pop(), self._pop()
            exec("self._push(b{}a)".format(instruction))
        
        # division
        elif instruction == "/":
            a, b = self._pop(), self._pop()
            # try converting them to floats for python 2 compability
            try:
                a, b = float(a), float(b)
            except OverflowError:
                pass
            self._push(b/a)
        
        # comparison operators
        elif instruction in COMPARISON:
            a, b = self._pop(), self._pop()
            exec("self._push(1 if b{}a else 0)".format(COMPARISON[instruction]))

        # logical NOT
        elif instruction == "!":
            a = self._pop()
            self._push(0) if a else self._push(1)

        # turn on string mode
        elif instruction == "i": # turn on string parsing
            self._string_mode = "insert"

        elif instruction == "I": # turn on "regin" string parsing
            self._string_mode = "regin"

        # duplicate ath value on stack to the register
        elif instruction == "y":
            a = self._pop()
            self._register = self._copy(len(self._stack)-(1+a))

        # duplicate top of stack to the register
        elif instruction == "Y":
            self._register = self._copy()

        # pop register value and push it to the stack
        elif instruction == "p":
            self._push(self._register)
            self._register = 0

        # duplicate register value to the stack
        elif instruction == "P":
            self._push(self._register)
         
        # remove top of stack
        elif instruction == "x":
            self._pop()

        # remove register value
        elif instruction == "X":
            self._register = 0
         
        # remove a values from stack, or push to register if a == 0
        elif instruction == "d":
            a = self._pop()
            if a:
                for x in range(a): self._pop()
            else: self._register = self._pop()

        # rotate pointer right
        elif instruction == "}":
            d = self._direction
            a = self._pop()
            if not a:
                if d == DIRECTIONS["l"]:
                    self._direction = DIRECTIONS["j"]
                elif d == DIRECTIONS["j"]:
                    self._direction = DIRECTIONS["h"]
                elif d == DIRECTIONS["h"]:
                    self._direction = DIRECTIONS["k"]
                elif d == DIRECTIONS["k"]:
                    self._direction = DIRECTIONS["l"]
        
        # rotate pointer left
        elif instruction == "{":
            d = self._direction
            a = self._pop()
            if not a:
                if d == DIRECTIONS["l"]:
                    self._direction = DIRECTIONS["k"]
                elif d == DIRECTIONS["k"]:
                    self._direction = DIRECTIONS["h"]
                elif d == DIRECTIONS["h"]:
                    self._direction = DIRECTIONS["j"]
                elif d == DIRECTIONS["j"]:
                    self._direction = DIRECTIONS["l"]

        # pop and output as character
        elif instruction == "w":
            self._output(chr(int(self._pop())))
        
        # pop from register and output as character
        elif instruction == "W":
            self._output(chr(int(self._register)))
            self._register = 0

        # pop and output as number
        elif instruction == "z":
            n = self._pop()
            # try outputting without the decimal point if possible
            self._output(int(n) if int(n) == n else n)

        # pop from register and output as number
        elif instruction == "Z":
            n = self._register
            self._output(int(n) if int(n) == n else n)
            self._register = 0

        # handle input
        elif instruction == ":":
            i = self._input()
            is_num = True
            for char in i:
                if char not in NCHARS:
                    is_num = False
                    break
            if is_num:
                self._push(int(i))
            else:
                i = i[::-1]
                for char in i:
                    self._push(ord(char))
        
        # the end
        elif instruction == "q":
            raise StopExecution()
        
        # space is NOP
        elif instruction == " ":
            pass

        # invalid instruction
        else:
            raise Exception("Invalid instruction", instruction)
    
    def _push(self, value, index=None):
        """
        Push a value to the stack.
        Keyword arguments:
            index -- the index to push/insert to. (default: end of stack)
        """
        self._stack.insert(len(self._stack) if index == None else index, value)
        
    def _pop(self, index=None):
        """
        Pop and return a value from the current stack.
        Keyword arguments:
            index -- the index to pop from (default: end of stack)
        """
        # if there are no values to pop, return 0
        try:
            value = self._stack.pop(len(self._stack)-1 if index == None else index)
        except IndexError:
            value = 0
        # convert to int where possible to avoid float overflow
        if value == int(value):
            value = int(value)
        return value

    def _copy(self, index=None):
        """
        Copy and return a value from the stack.
        Keyword arguments:
            index -- the index to copy from (default: end of stack)
        """
        # if there are no values to copy, return 0
        try:
            value = self._stack[(len(self._stack)-1 if index == None else index)]
        except IndexError:
            value = 0
        # convert to int where possible to avoid float overflow
        if value == int(value):
            value = int(value)
        return value

    def _input(self):
        """
        Return an inputted character.
        """
        return read_string()

    
    def _output(self, output):
        """
        Output a string without a newline appended.
        """
        output = str(output)
        self._newline = output.endswith("\n")
        sys.stdout.write(output)
        sys.stdout.flush()


class StopExecution(Exception):
    """
    Exception raised when a script has finished execution.
    """
    def __init__(self, message = None):
        self.message = message

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="""
    Execute a Grok script.
    Executing a script is as easy as:
        %(prog)s <script file>
    You can also execute code directly using the -c/--code flag:
        %(prog)s -c '1z23zzq'
        > 132
    The -v and -s flags can be used to prepopulate the stack:
        %(prog)s echo.grk -s "hello, world" -v 32 49 50 51 -s "456"
        > hello, world 123456""", usage="""%(prog)s [-h] (<script file> | -c <code>) [<options>]""", 
    formatter_class=argparse.RawDescriptionHelpFormatter)
    
    group = parser.add_argument_group("code")
    # group script file and --code together to only allow one
    code_group = group.add_mutually_exclusive_group(required=True)
    code_group.add_argument("script", 
                            type=argparse.FileType("r"), 
                            nargs="?", 
                            help=".grk file to execute")
    code_group.add_argument("-c", "--code", 
                            metavar="<code>", 
                            help="string of instructions to execute")
    
    options = parser.add_argument_group("options")
    options.add_argument("-s", "--string", 
                         action="append", 
                         metavar="<string>", 
                         dest="stack")
    options.add_argument("-v", "--value", 
                         type=float, 
                         nargs="+", 
                         action="append",
                         metavar="<number>",  
                         dest="stack", 
                         help="push numbers or strings onto the stack before execution starts")
    options.add_argument("-t", "--tick", 
                         type=float,
                         default=0.0,
                         metavar="<seconds>",
                         help="define a tick time, or a delay between the execution of each instruction")
    options.add_argument("-a", "--always-tick",
                         action="store_true", 
                         default=False,
                         dest="always_tick", 
                         help="make every instruction cause a tick (delay), even whitespace and skipped instructions")
    options.add_argument("-e", "--show-errors",
                         action="store_true",
                         default=False,
                         dest="show_errors",
                         help="disable \"You don't grok Grok.\" error message and show true error message")
    
    # parse arguments from sys.argv
    arguments = parser.parse_args()
    
    # initialize an interpreter
    if arguments.script:
        code = arguments.script.read()
        arguments.script.close()
    else:
        code = arguments.code
    
    interpreter = Interpreter(code)

    if arguments.show_errors:
        interpreter._debug = True

    # add supplied values to the interpreters stack
    if arguments.stack:
        for x in arguments.stack:
            if isinstance(x, str):
                interpreter._stack += [float(ord(c)) for c in x]
            else:
                interpreter._stack += x

    # run the script
    try:
        while True:
            try:
                instr = interpreter.move()
            except StopExecution as stop:
                # only print a newline if the script didn't
                newline = ("\n" if (not interpreter._newline) and interpreter._newline != None else "")
                parser.exit(message=(newline+stop.message+"\n") if stop.message else newline)
            
            if instr and not instr == " " or arguments.always_tick:
                time.sleep(arguments.tick)
    except KeyboardInterrupt:
        # exit cleanly
        parser.exit(message="\n")
