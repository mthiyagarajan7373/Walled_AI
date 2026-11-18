# MCP Communication Monitoring and User Authorization System

## Overview

This Python-based application monitors Model Context Protocol (MCP) communications initiated by Claude Desktop and Claude Web, and gives users control over whether each individual MCP request is allowed to proceed or is blocked.

The system intercepts MCP requests in real-time, displays a web-based confirmation modal, and allows users to make informed decisions about each request.

## Features

- MCP Communication Monitoring
- User Confirmation Mechanism via Web Modal
- Request Handling (Allow/Block)
- Concurrent Request Support
- Web Interface for Management

## Installation

1. Install Python 3.8+
2. Install Flask: `pip install flask`
3. Run: `python run.py`

## Usage

- Start the application
- Open browser to `http://127.0.0.1:5000`
- Use the interface to allow or block MCP requests

## Architecture

The system uses Flask for the web interface and threading for monitoring MCP requests.