# iTunes Scripts
Just a collection of scripts around iTunes library management.

__itunes-playlist-export.pl__

_Create M3U files for every playlist in your iTunes library_

How to use this script:
* Requires Mac::iTunes::Library and URI::Encode. On a mac, open terminal and execute:
```
  cpan
  # answer questions if this is the first time using CPAN #
  cpan> install Mac::iTunes::Library
  cpan> install URI::Encode
  cpan> exit
```
  
* Reload your shell (close and reopen terminal)

* Create a directory where you want to store the M3U files, such as:

`mkdir ~/Music/Export`

* Run the script, specifying the output directory:

`./itunes-playlist-export --export=~/Music/Export`
