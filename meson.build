project('edipy2', 'fortran')

dependencies = [
  'numpy > 2.0.0',
]

python = import('python').find_installation(pure: false)


python_src  = ['src/sphinxfortran_ng/crackfortran_for_sphinx.py',
               'src/sphinxfortran_ng/fortran_autodoc.py',
               'src/sphinxfortran_ng/fortran_domain.py',
               'src/sphinxfortran_ng/__init__.py']


python.install_sources(
    python_src,
    subdir: 'sphinxfortran_ng'
)
