# Mistral Models Support in Morphik

This document describes the Mistral AI model support that has been added to the Morphik RAG system.

## Overview

Mistral AI models have been integrated into Morphik using LiteLLM, providing access to both completion and embedding models from Mistral AI.

## Configuration

### Environment Variable

Add your Mistral API key to your environment variables:

```bash
export MISTRAL_API_KEY="your-mistral-api-key-here"
```

### Available Models

The following Mistral models have been added to the `morphik.toml` configuration:

#### Completion Models
- **`mistral_small`** - `mistral/mistral-small-latest` - Fast, cost-effective model for simple tasks
- **`mistral_medium`** - `mistral/mistral-medium-latest` - Balanced performance and cost for most tasks  
- **`mistral_large`** - `mistral/mistral-large-latest` - Most capable model for complex tasks

#### Embedding Model
- **`mistral_embed`** - `mistral/mistral-embed` - High-quality text embeddings

## Usage

### Using Mistral Models in Configuration

To use Mistral models in your Morphik configuration, update the relevant sections in `morphik.toml`:

#### For Completion Tasks
```toml
[completion]
model = "mistral_large"  # or mistral_small, mistral_medium

[agent]
model = "mistral_medium"

[document_analysis]
model = "mistral_large"

[workflows]
model = "mistral_medium"
```

#### For Embeddings
```toml
[embedding]
model = "mistral_embed"
```

### Model Selection Guidelines

- **mistral_small**: Use for simple tasks, content summarization, basic Q&A
- **mistral_medium**: Recommended for most RAG applications, document analysis, complex reasoning
- **mistral_large**: Use for the most demanding tasks requiring highest accuracy
- **mistral_embed**: Use for generating high-quality embeddings for your documents

## API Key Setup

1. Get your API key from [Mistral AI Platform](https://console.mistral.ai/)
2. Set the environment variable:
   ```bash
   # Linux/Mac
   export MISTRAL_API_KEY="your-api-key"
   
   # Windows
   set MISTRAL_API_KEY=your-api-key
   ```
3. Or add it to your `.env` file:
   ```
   MISTRAL_API_KEY=your-api-key
   ```

## Example Configuration

Here's an example configuration using Mistral models:

```toml
[agent]
model = "mistral_medium"

[completion]
model = "mistral_medium"
default_max_tokens = "1000"
default_temperature = 0.3

[embedding]
model = "mistral_embed"
dimensions = 1024
similarity_metric = "cosine"

[document_analysis]
model = "mistral_large"

[workflows]
model = "mistral_medium"
```

## Benefits

- **Cost-effective**: Mistral models offer competitive pricing
- **High Performance**: Strong performance across various NLP tasks
- **Multilingual**: Excellent support for multiple languages
- **Fast Inference**: Low latency for real-time applications
- **Seamless Integration**: Works through the existing LiteLLM infrastructure

## Notes

- All Mistral models use the `-latest` suffix to automatically get the newest version
- The embedding model `mistral-embed` produces 1024-dimensional vectors
- Mistral models support function calling and structured output where applicable
- Ensure your `MISTRAL_API_KEY` is properly set before using any Mistral models

## Troubleshooting

1. **Authentication Error**: Verify your `MISTRAL_API_KEY` is correctly set
2. **Model Not Found**: Ensure you're using the exact model names as specified in the configuration
3. **Rate Limiting**: Mistral API has rate limits; consider implementing exponential backoff for high-volume usage

For more information about Mistral AI models and their capabilities, visit the [Mistral AI documentation](https://docs.mistral.ai/).