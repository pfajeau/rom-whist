#!/bin/bash

declare -A descriptions
descriptions["romwhist.py"]="Main application entry point that sets up Flask app with internationalization (Babel) and initializes SocketIO for real-time communication."
descriptions["wsgi.py"]="WSGI application wrapper for deployment behind Apache/Gunicorn/Nginx."
descriptions["config.py"]="Configuration module for environment-agnostic settings like tuning parameters and extension-specific settings."
descriptions["romwhist/__init__.py"]="App initialization module that creates Flask app instance with proxy middleware, SocketIO support, and internationalization."
descriptions["romwhist/card.py"]="Card class representing individual cards with suit and rank properties."
descriptions["romwhist/deck.py"]="Deck class managing a collection of cards with deal operations."
descriptions["romwhist/player.py"]="Player class with status and type enums (Active/Inactive, Human/AI/Shadowed)."
descriptions["romwhist/hand.py"]="Hand class managing a player's cards with sorting and manipulation operations."
descriptions["romwhist/round.py"]="Round class tracking cards played by each player during a round and determining winners."
descriptions["romwhist/game.py"]="CardGame base class with core game logic including phases (Deal, Bet, Play, Over) and player/score management."
descriptions["romwhist/game_state.py"]="GameState class providing a serializable structure of game state for inter-process communication as JSON."
descriptions["romwhist/models.py"]="Database models including BaseModel and User models using SQLAlchemy ORM."
descriptions["romwhist/extensions.py"]="Flask extensions instantiation (SQLAlchemy and CSRF protection) to avoid circular imports."
descriptions["romwhist/commands.py"]="Flask CLI commands module with example command structure."
descriptions["romwhist/controllers.py"]="Controllers module with utility functions like form error flashing."
descriptions["romwhist/forms.py"]="WTForms including LoginForm, GameForm, and StartForm with validation."
descriptions["romwhist/utils.py"]="Utility functions for copying dictionaries."
descriptions["romwhist/common_routes.py"]="Shared route logic and WebSocket handling for all game types with user authentication."
descriptions["romwhist/i18n_strings.py"]="Internationalization strings dictionary for template translation."
descriptions["romwhist/ai/ai.py"]="Main AI module connecting to game servers via SocketIO, manages AI players for different game types (Ohell, Belote, Contree)."
descriptions["romwhist/ai/ai_agents.py"]="Abstract AI agent class with game simulation lookup utilities and Monte Carlo Tree Search agent implementation."
descriptions["romwhist/ai/ai_player.py"]="Base AiPlayer class managing AI player state and game lifecycle."
descriptions["romwhist/ai/sim_game.py"]="SimGame base class for simulating game scenarios in AI agents."
descriptions["romwhist/belote/belote.py"]="BeloteGame class implementing Belote game rules with deal phases, betting, and special belote/rebelote announcements."
descriptions["romwhist/belote/belote_ai.py"]="BeloteAiPlayer class using Monte Carlo Tree Search for AI decision-making in Belote."
descriptions["romwhist/belote/belote_state.py"]="BeloteState extending GameState with Belote-specific state including phase and belote status."
descriptions["romwhist/belote/belote_status.py"]="BeloteStatus enum tracking announcement states (Not Allowed, Allowed, Belote Announced, etc.)."
descriptions["romwhist/belote/belote_routes.py"]="Flask routes and WebSocket handlers for Belote game endpoints and real-time updates."
descriptions["romwhist/belote/belote_form.py"]="BeloteStartForm extending StartForm with points-to-reach configuration validation."
descriptions["romwhist/belote/belote_sim.py"]="BeloteSim simulation class for Monte Carlo simulations of Belote game scenarios."
descriptions["romwhist/contree/contree.py"]="ContreeGame extending BeloteGame with Contree-specific rules and counting methods (Points Bid, Points Achieved, etc.)."
descriptions["romwhist/contree/contree_ai.py"]="ContreeAiPlayer extending BeloteAiPlayer with Contree-specific MCTS agents and correction factors."
descriptions["romwhist/contree/contree_state.py"]="ContreeState extending BeloteState with Contree-specific state like contree status and current bet."
descriptions["romwhist/contree/contree_routes.py"]="Flask routes and WebSocket handlers for Contree game."
descriptions["romwhist/contree/contree_form.py"]="ContreeStartForm with counting method selection and validation."
descriptions["romwhist/contree/contree_sim.py"]="ContreeSim simulation class for Monte Carlo simulations in Contree with game-specific logic."
descriptions["romwhist/contree/announce.py"]="Announce class representing contract bids with comparison operators and string parsing."
descriptions["romwhist/ohell/ohell.py"]="OhellGame class implementing Oh Hell (Ombre) game rules with trick-taking and hand progression."
descriptions["romwhist/ohell/ohell_ai.py"]="OhellAiPlayer class using MCTS agents for AI decision-making in Oh Hell."
descriptions["romwhist/ohell/ohell_state.py"]="OhellState extending GameState with Oh Hell-specific state like rounds won."
descriptions["romwhist/ohell/ohell_routes.py"]="Flask routes and WebSocket handlers for Oh Hell game."
descriptions["romwhist/ohell/ohell_form.py"]="OhellStartForm with options for one-card deals, no-trump deals, and increment configuration."
descriptions["romwhist/ohell/ohell_sim.py"]="OhellSim simulation class for Monte Carlo simulations in Oh Hell game scenarios."
descriptions["tests/conftest.py"]="Pytest configuration file with app fixture and incremental test setup/teardown hooks."
descriptions["tests/test_all.py"]="Master test runner that executes all individual test modules sequentially."
descriptions["tests/test_common.py"]="Common test utilities including hand creation and round play simulation helpers."
descriptions["tests/test_belote.py"]="Unit tests for Belote game mechanics and game flow."
descriptions["tests/test_belote_ai.py"]="Unit tests for Belote AI players and MCTS agents."
descriptions["tests/test_ohell.py"]="Unit tests for Oh Hell game mechanics and game initialization."
descriptions["tests/test_ohell_ai.py"]="Unit tests for Oh Hell AI players with game state simulation."
descriptions["tests/test_contree.py"]="Unit tests for Contree game rules and announcements."
descriptions["tests/test_contree_ai.py"]="Unit tests for Contree AI players with AI creation and decision-making."
descriptions["tests/test_controllers.py"]="Unit test templates for controller endpoints (mostly empty with example structure)."
descriptions["instance/config.py"]="Configuration module for environment-agnostic settings like tuning parameters and extension-specific settings."  # duplicate, but instance has its own

for file in $(find . -name "*.py" -type f); do
  rel_file=${file#./}
  desc=${descriptions["$rel_file"]}
  if [ -z "$desc" ]; then
    desc="Python module for the Rom-Whist project."
  fi
  HEADER="# -*- coding: utf-8 -*-
#
# Description: $desc
#
# Copyright (C) 2026 Philippe Fajeau
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"
  if grep -q "Description:" "$file"; then
    echo "Skipping $file, already has description"
  else
    # Remove old partial copyright if present
    if grep -q "Copyright" "$file"; then
      sed -i '/^# Copyright/d' "$file"
    fi
    if head -1 "$file" | grep -q "#!"; then
      # insert after first line
      { head -1 "$file"; echo "$HEADER"; tail -n +2 "$file"; } > temp && mv temp "$file"
    else
      # insert at top
      { echo "$HEADER"; cat "$file"; } > temp && mv temp "$file"
    fi
  fi
done