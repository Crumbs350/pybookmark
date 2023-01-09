from setuptools import setup, find_packages
import os
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

# read README using pypandoc
try:
    import pypandoc
    readme = pypandoc.convert_file(PROJECT_PATH + '/README.md', 'rst')
except(IOError, ImportError):
    readme = open(PROJECT_PATH + '/README.md').read()

# read VERSION
with open(PROJECT_PATH + "/pybookmark/VERSION", 'r') as fd:
    VERSION = fd.readline().rstrip('\n')

setup(
    name="PyBookmark",
    version=VERSION,
    url="https://github.com/Crumbs350/pybookmark",
    author="Crumbs",
    author_email="22521102+Crumbs350@users.noreply.github.com",
    maintainer='Crumbs',
    maintainer_email='22521102+Crumbs350@users.noreply.github.com',
    description="A Bookmark.html file parser, merger and data viewer using pure python",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    # python_requires='>3.6.0',
    license='LICENSE',
    keywords="python bookmark json tkinter privacy",
    packages=find_packages(exclude=['tests']),   # find all the sub-packages
    # packages=find_packages('pybookmark/', exclude=['tests']),  this version fails because the installed module can never be found
    include_package_data=True,
    py_modules=["scripts/PyBookmark_viewer", "scripts/bookmarks_merge"],
    entry_points={
        'console_scripts': ['PyBookmark=PyBookmark.PyBookmark:PyBookmarkJSONViewer',
                            'bookmarks_parse=PyBookmark.PyBookmark:bookmarks_parse',
                            'bookmarks_merge=PyBookmark.scripts:bookmarks_merge',
                            'viewer=PyBookmark.scripts:PyBookmark_viewer',
                           ]},
    data_files=[('data', ['data/addr.json', 'data/bookmarks_test.html', 'data/bookmarks.html'])],
    # https://pypi.org/classifiers/
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    install_requires=[
        # "argparse",
        # "bs4",    # beautiful soup 4
        # "datetime",
        # "glob",
        # "json",
        # "os",
        # "re",
        # "sys",
        # "time",
        # "tkinter",
        # "urllib",
        # "webbrowser",
        "pyyaml",
    ],
)
