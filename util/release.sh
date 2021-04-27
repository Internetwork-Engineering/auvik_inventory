#!/bin/sh

VERSION=`python setup.py --version`

echo "Doing git..."
git tag -a v$VERSION -m v$VERSION
git push --tags

echo "Building packages..."
rm -f dist/*
python setup.py sdist bdist_wheel

echo "Done!"
