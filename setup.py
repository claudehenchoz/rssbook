"""Setup configuration for rssbook package."""

from setuptools import setup, find_packages

setup(
    name="rssbook",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "feedparser",
        "trafilatura",
        "lxml",
        "ebooklib",
        "python-slugify",
        "requests",
        "favicon"
    ],
    entry_points={
        'console_scripts': [
            'rssbook=rssbook.cli:main',
        ],
    },
    author="Claude Henchoz",
    author_email="claude.henchoz@gmail.com",
    description="Convert RSS feeds to EPUB books",
    long_description=open("README.md").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    keywords="rss epub ebook converter",
    url="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
)
