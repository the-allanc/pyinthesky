import setuptools

setup_params = dict(
    name='pyinthesky',
    packages=setuptools.find_packages(),
    install_requires=[
        'requests',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
