#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# vim: noai:et:tw=80:ts=2:ss=2:sts=2:sw=2:ft=bash

# Title:            init_repo.sh
# ==============================================================================

_pwd=$(basename $PWD)
if [[ ${_pwd} =~ util ]]
then
  # Ran from util folder backup one
  cd ../
  REPO=$(basename $PWD)
else
  REPO=$_pwd
fi

if [[ ! -f 'README.md' ]]
then
  echo "Creating README.md"
  echo "# ${REPO}" >> README.md
fi

if [[ ! -d '.git' ]]
then
  echo "Initializing ${REPO}"
  git init .
fi

git branch -M main
git remote add origin "git@github.com:IE-OnDemand/${REPO}"
git add README.md
git commit -m "Python project creation script"
git push -u origin main

