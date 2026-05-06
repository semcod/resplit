#!/usr/bin/env bash
set -e
clear

VENV=".venv"
PIP="$VENV/bin/pip"

if [ ! -f "$PIP" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

$PIP install psutil --upgrade --quiet
$PIP install code2llm --upgrade --quiet
$VENV/bin/code2llm ./ -f all -o ./project --no-chunk --no-png
find ./project -maxdepth 1 -type f \( -name "*.mmd" -o -name "mermaid.export" \) \
    -exec sed -i 's/^# generated/%% generated/' {} \;

$PIP install code2docs --upgrade --quiet
$VENV/bin/code2docs ./ --readme-only

#$PIP install redup --upgrade --quiet
$PIP install redup -e .
$VENV/bin/redup scan . --format toon --output ./project

$PIP install doql --upgrade --quiet
$VENV/bin/doql adopt . --format less --output app.doql.less --force

$PIP install sumd --upgrade --quiet
$VENV/bin/sumd .
$VENV/bin/sumr .
