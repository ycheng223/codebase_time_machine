#!/usr/bin/env python3
"""
Minimal Web UI for Codebase_Time_Machine
Exposes a tiny form and health endpoint for local testing.
"""
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

DATA_STORE = {}

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/save', methods=['POST'])
def save_item():
    payload = request.get_json() or {}
    item_id = payload.get('id')
    if not item_id:
        return jsonify({"error": "id required"}), 400
    DATA_STORE[item_id] = payload
    return jsonify({"status": "saved", "id": item_id}), 200

@app.route('/api/items', methods=['GET'])
def list_items():
    return jsonify(list(DATA_STORE.values()))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    print(f"Starting Codebase_Time_Machine web UI on port {port}")
    app.run(host='127.0.0.1', port=port, debug=True)
