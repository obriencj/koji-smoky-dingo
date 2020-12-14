# Overview of KSD Standalone using LonelyDingo

This is a trivial example script demonstrating how to use Koji Smoky
Dingo to write a script that works with a Koji instance.

The standalone case is a middle ground between the command and script
examples. It runs outside of the koji command line as its own command,
but it follows the structure of writing it as a plugin command. This
is thanks to the `kojismokyding.standalone.LonelyDingo` class, which
acts as an adaptive layer between the two styles.


## Use

The example whoami.py script can be executed directly

```
[cobrien@crayon standalone]$ ./whoami.py --help
usage: whoami.py [-h] --profile PROFILE [--json]

Print identity and information about the currently logged-in user

optional arguments:
  -h, --help            show this help message and exit
  --json                Output as JSON

Koji Profile options:
  --profile PROFILE, -p PROFILE
                        specify a configuration profile
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
