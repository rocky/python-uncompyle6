#! python

"""Setup script for the 'uncompyle' distribution."""

from distutils.core import setup, Extension

setup (name = "uncompyle2",
       version = "1.1",
       description = "Python byte-code to source-code converter",
       author = "Mysterie",
       author_email = "kajusska@gmail.com",
       url = "http://github.com/Mysterie/uncompyle2",
       packages=['uncompyle2', 'uncompyle2.opcode'],
       scripts=['scripts/uncompyle2']
      )
