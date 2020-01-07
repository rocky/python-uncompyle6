Making a release is a somewhat tedious process so I've automated it a little


Here are tools that I, rocky, use to check and build a distribution.

They are customized to my environment:
- I use pyenv to various Python versions installed
- I have git repos for xdis, and spark parser at the same level as uncompyle6

There may be other rocky-specific things that need customization.
how-to-make-a-release.md has overall how I make a release

Since this project uses python over a wide variety of release, some versions
of projects that should be used for specific Python versions

for 3.2.6:
   pytest==2.9.2

for 3.1.5
   pytset==2.1.0
   py=1.8.0 and comment out line 10 of _builtin.py # callable = callable
   six==1.10.0
