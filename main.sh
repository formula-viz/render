#!/bin/bash

create_tmux_window() {
    local window_name=$1
    local command=$2
    tmux new-window -n "$window_name"
    tmux send-keys "$command" C-m
}

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$PROJECT_ROOT"

FLASK_CMD="chmod +x scripts/start_flask.sh && ./scripts/start_flask.sh"
REDIS_CMD="chmod +x scripts/start_rq.sh && ./scripts/start_rq.sh"

if [ -n "$TMUX" ]; then
    # We're inside tmux, create new windows based on current count
    window_count=$(tmux list-windows | wc -l)

    create_tmux_window "Flask Server" "$FLASK_CMD"
    create_tmux_window "Redis Worker" "$REDIS_CMD"
else
    SESSION_NAME="formula-viz/render"
    tmux new-session -d -s $SESSION_NAME

    tmux rename-window -t $SESSION_NAME:0 'Flask Server'
    tmux send-keys -t $SESSION_NAME:0 "$FLASK_CMD" C-m

    create_tmux_window "Redis Worker" "$REDIS_CMD"

    tmux attach-session -t $SESSION_NAME
fi
