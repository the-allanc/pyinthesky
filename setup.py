import setuptools

setup_params = dict(
    name='pyinthesky',
    packages=setuptools.find_packages(),
    install_requires=[
        'requests',
        'iso8601',
        'formencode',
        'six',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
