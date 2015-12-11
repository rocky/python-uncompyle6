#! python

"""Setup script for the 'uncompyle' distribution."""

from distutils.core import setup, Extension

setup (name = "uncompyle6",
       version = "2.0",
       description = "Python byte-code to source-code converter",
       author = "Mysterie",
       author_email = "kajusska@gmail.com",
       url = "http://github.com/Mysterie/uncompyle2",
       packages=['uncompyle6', 'uncompyle6.opcode'],
       scripts=['scripts/uncompyle6']
      )
