# Grok-Language
Grok is a two-dimensional, stack-based language inspired by [Befunge], [`><>`][Fish], and the [Vim editor][Vim].

---

## Documentation
+ [Tutorial]
+ [Instruction List]
+ [Examples]
+ [Online Interpreter]
+ [Esolangs.org Wiki Page][Wiki]

---

## Getting Started
The PyGrok interpreter requires Python 3 or higher.

```
$ PyGrok.py --help
usage: PyGrok.py [-h] (<script file> | -c <code>) [<options>]

    Execute a Grok script.
    Executing a script is as easy as:
        PyGrok.py <script file>
    You can also execute code directly using the -c/--code flag:
        PyGrok.py -c '1z23zzq'
        > 132
    The -v and -s flags can be used to prepopulate the stack:
        PyGrok.py echo.grk -s "hello, world" -v 32 49 50 51 -s "456"
        > hello, world 123456

optional arguments:
  -h, --help            show this help message and exit

code:
  script                .grk file to execute
  -c <code>, --code <code>
                        string of instructions to execute

options:
  -s <string>, --string <string>
  -v <number> [<number> ...], --value <number> [<number> ...]
                        push numbers or strings onto the stack before execution starts
  -t <seconds>, --tick <seconds>
                        define a tick time, or a delay between the execution of each instruction
  -a, --always-tick     make every instruction cause a tick (delay), even whitespace and skipped instructions
  -e, --show-errors     disable "You don't grok Grok." error message and show true error message
```
---

The official specification can be found at [Esolangs.org][Wiki]

[Tutorial]: https://github.com/AMiller42/Grok-Language/wiki/Tutorial
[Instruction List]: https://github.com/AMiller42/Grok-Language/wiki/Instruction-List
[Examples]: https://github.com/AMiller42/Grok-language/wiki/Examples
[Online Interpreter]: http://grok.pythonanywhere.com
[Wiki]: https://esolangs.org/wiki/Grok

[Befunge]: https://esolangs.org/wiki/Befunge
[Fish]: https://esolangs.org/wiki/Fish
[Vim]: https://en.wikipedia.org/wiki/Vim_(text_editor)
