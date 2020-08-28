# Overview of KSD Example Command

This is a trivial example project demonstrating how to use Koji Smoky
Dingo to add a few new commands to the Koji CLI.


## Commands

The example provides the following example command implementations

| Command | Description |
|---------|-------------|
|`beep` |Prints "beep boop" |
|`boop` |Prints "boop beep" |
|`whoami` |Prints information about the currently logged-in user |


## Install

```bash
# for Python 2.6
python2 setup.py clean build install --user

# for Python 2.7
python2 setup.py clean bdist_wheel
pip2 install --user dist/ksd_command-1.0.0-py2-none-any.whl

# for Python 3
python3 setup.py clean bdist_wheel
pip3 install --user dist/ksd_command-1.0.0-py3-none-any.whl
```


## Contact

Author: Christopher O'Brien  <obriencj@gmail.com>

Original Git Repository: <https://github.com/obriencj/koji-smoky-dingo>

Documentation: <https://obriencj.github.io/koji-smoky-dingo>


## License

This library is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.

This library is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this library; if not, see <http://www.gnu.org/licenses/>.
