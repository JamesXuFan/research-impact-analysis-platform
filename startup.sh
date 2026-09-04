#!/bin/bash
# Azure App Service (Linux, Python) startup command for this Streamlit app.
# Set as the App Service "Startup Command" — see docs/deployment-azure.md.
#
# --server.address 0.0.0.0 : listen on all interfaces, required behind
#   App Service's reverse proxy (default is localhost-only, unreachable).
# --server.port 8000        : matches App Service's default expected port
#   (WEBSITES_PORT) for the Python Linux runtime; change both together if
#   you set WEBSITES_PORT to something else.
# --server.headless true    : do not try to open a local browser tab.
python -m streamlit run app/Home.py \
    --server.address 0.0.0.0 \
    --server.port 8000 \
    --server.headless true
