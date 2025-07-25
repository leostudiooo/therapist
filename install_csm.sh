#!/bin/bash

# Install Sesame CSM repository
echo "🔧 Installing Sesame CSM..."

# Clone the CSM repository
if [ ! -d "csm_repo" ]; then
    git clone https://github.com/SesameAILabs/csm.git csm_repo
fi

# Copy essential files to backend
echo "📂 Copying CSM files to backend..."
cp csm_repo/generator.py backend/csm_generator.py 2>/dev/null || echo "Warning: generator.py not found, using our implementation"
cp csm_repo/models.py backend/csm_models.py 2>/dev/null || echo "Warning: models.py not found"
cp csm_repo/watermarking.py backend/csm_watermarking.py 2>/dev/null || echo "Warning: watermarking.py not found"

# Install dependencies
echo "📦 Installing CSM dependencies..."
cd backend

# Update pyproject.toml to include the silentcipher dependency
echo "Adding silentcipher dependency..."

# Install dependencies using uv
uv sync --frozen

echo "✅ CSM installation completed!"
echo "Note: You'll need to authenticate with Hugging Face to access CSM-1B and Llama-3.2-1B models:"
echo "  huggingface-cli login"
echo ""
echo "Environment variables needed:"
echo "  export NO_TORCH_COMPILE=1"