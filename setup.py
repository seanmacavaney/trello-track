import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="trello-track", # Replace with your own username
    version="0.0.1",
    author="Sean MacAvaney",
    author_email="dev.sean.macavaney@gmail.com",
    description="Tracks running processes via Trello",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seanmacavaney/trello-track",
    packages=setuptools.find_packages(),
    classifiers=[],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['trello-track=trello_track:main_cli'],
    }
)
