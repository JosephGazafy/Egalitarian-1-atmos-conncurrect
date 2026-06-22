#!/usr/bin/env bash

REPO="Egalitarian-1-atmos-conncurrect"

gh auth login

gh repo create "$REPO" \
  --public \
  --description "Combined Atmos Omega concurrent framework" \
  --clone=false

git init
git branch -M main
git add .
git commit -m "Initial commit"

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/JosephGazafy/$REPO.git"

git push -u origin main
