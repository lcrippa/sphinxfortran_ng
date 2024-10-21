project('edipy2', 'fortran')

dependencies = [
  'numpy > 2.0.0',
]

python = import('python').find_installation(pure: false)


python_src  = ['pyfiles/crackfortran_for_sphinx.py',
               'pyfiles/fortran_autodoc.py',
               'pyfiles/fortran_domain.py',
               'pyfiles/__init__.py']


python.install_sources(
    python_src,
    subdir: 'sphinxfortran_ng'
)
