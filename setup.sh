#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hook for Black
if [ -d .git ]; then
  echo "Installing pre-commit hook for Black..."
  echo '#!/bin/bash
black --check .' > .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
fi

echo "Setup complete."