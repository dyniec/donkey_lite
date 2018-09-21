#!/usr/bin/env python

from distutils.core import setup, Extension

setup(name             = "donkey_lite_scaffolding",
      version          = "0.1",
      description      = "Lightweight donkey-car.",
      author           = "",
      author_email     = "",
      maintainer       = "",
      url              = "",
      ext_modules      = [
          Extension(
              'lib.cext', ['src/cext.cpp'],
              extra_compile_args=["-Ofast", "-march=native", "-fopenmp"],
              libraries=["gomp"]),
      ], 
      
)
