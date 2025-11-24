#!/usr/bin/env python
"""
Remote Whisper Transcription Server

This server runs Whisper on a GPU-enabled machine and provides transcription
services over HTTP. It's designed to be run on a remote machine on your LAN
to offload transcription processing from the Raspberry Pi.

Usage:
    python -m will_byers.whisper_server --host 0.0.0.0 --port 5000 --model base

Requirements:
    - CUDA-capable GPU (recommended)
    - whisper (openai-whisper)
    - flask
"""

import argparse
import io
import os
import tempfile
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wavfile
import whisper
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global model variable
model = None
model_name = None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'model': model_name,
        'device': str(model.device) if model else 'not loaded'
    })


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe audio from uploaded WAV file.
    
    Expects:
        - File upload with key 'audio' containing WAV data
        - Optional 'language' parameter (default: 'en')
    
    Returns:
        JSON with 'text' field containing transcription
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    language = request.form.get('language', 'en')
    
    try:
        # Read the uploaded WAV file
        audio_bytes = audio_file.read()
        
        # Save to temporary file (Whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
            f.write(audio_bytes)
        
        try:
            # Transcribe using Whisper
            print(f"Transcribing audio (language: {language})...")
            result = model.transcribe(temp_path, language=language)
            transcription = result['text'].strip()
            
            print(f"Transcription: {transcription}")
            
            return jsonify({
                'text': transcription,
                'language': result.get('language', language)
            })
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        print(f"Error during transcription: {e}")
        return jsonify({'error': str(e)}), 500


def main():
    """Main entry point for the Whisper server."""
    parser = argparse.ArgumentParser(
        description='Remote Whisper Transcription Server'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0 for all interfaces)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to listen on (default: 5000)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='base',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Whisper model to use (default: base)'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Device to use (cuda/cpu, default: auto-detect)'
    )
    
    args = parser.parse_args()
    
    # Load Whisper model
    global model, model_name
    model_name = args.model
    
    print(f"Loading Whisper model '{model_name}'...")
    print("This may take a moment on first run...")
    
    # Load model with specified device
    if args.device:
        model = whisper.load_model(model_name, device=args.device)
    else:
        model = whisper.load_model(model_name)
    
    print(f"✓ Model loaded on device: {model.device}")
    print(f"\nStarting server on {args.host}:{args.port}")
    print(f"Transcription endpoint: http://{args.host}:{args.port}/transcribe")
    print(f"Health check endpoint: http://{args.host}:{args.port}/health")
    print("\nPress Ctrl+C to stop the server.\n")
    
    # Run Flask server
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == '__main__':
    main()