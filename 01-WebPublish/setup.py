from setuptools import setup

setup(
    name = 'web_publish',
    version = '0.1',
    author = 'Frank',
    author_email = 'fkerrin@gmail.com',
	description = 'Publishing static website to AWS.',
	license = 'GPLv3+',
	packages = ['web_publish'],
	url = 'https://kittens.fkerrin.com',
	install_requires = ['click', 'boto3'],
	entry_points = """
	    [consolee_scripts]
        web_publish = web_publish.web_publish:CLI"""
)