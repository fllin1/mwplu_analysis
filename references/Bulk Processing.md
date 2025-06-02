# PLU Bulk Processing System

A comprehensive, modular system for processing PLU (Plan Local d'Urbanisme) documents in bulk using YAML configuration files and a clean CLI interface.

## Overview

The bulk processing system orchestrates the entire PLU pipeline, from initial OCR processing to final Supabase upload, using your YAML configuration files to automatically discover and process documents across different cities and stages.

## Architecture

### Core Components

1. **BulkProcessor** - Main orchestrator class
2. **MainPipelineProcessor** - Handles main.py pipeline commands
3. **SupabaseProcessor** - Manages Supabase uploads
4. **bulk_runner.py** - User-friendly CLI interface

### Pipeline Stages

| Stage | Description | Input | Output |
|-------|-------------|-------|--------|
| `ocr` | Extract text from PDFs using Mistral | PDF files in `data/external/` | JSON files in `data/raw/` |
| `extract_pages` | Extract and categorize pages using Gemini | JSON files in `data/raw/` | JSON files in `data/interim/` |
| `synthesis` | Generate structured analysis using Gemini | JSON files in `data/interim/` | JSON files in `data/processed/` |
| `reports` | Create PDF reports from processed data | JSON files in `data/processed/` | PDF files in `data/pdf/` |
| `upload_supabase` | Upload to Supabase database | JSON files in `data/processed/` | Database records + HTML files |

## Quick Start

### 1. Check Current Status

```bash
python bulk_runner.py status
```

This shows file counts across all pipeline stages for each city.

### 2. Upload Existing Processed Data

```bash
python bulk_runner.py upload_all
```

Quickly upload all your processed JSON files to Supabase.

### 3. Process Specific Cities

```bash
# Run synthesis and generate reports for specific cities
python bulk_runner.py run --stages synthesis reports --cities grenoble nantes

# Process all stages for a single city
python bulk_runner.py run --all-stages --cities grenoble
```

### 4. Dry Run (Preview)

```bash
python bulk_runner.py run --stages synthesis reports --cities all --dry-run
```

See what would be executed without actually running it.

## Usage Examples

### Basic Commands

```bash
# Show help
python bulk_runner.py --help

# List available cities
python bulk_runner.py list-cities

# List available pipeline stages  
python bulk_runner.py list-stages

# Check pipeline status
python bulk_runner.py status
```

### Processing Commands

```bash
# Run OCR for specific cities
python bulk_runner.py run --stages ocr --cities bordeaux nantes

# Generate reports for all cities
python bulk_runner.py run --stages reports --cities all

# Run multiple stages for specific cities
python bulk_runner.py run --stages synthesis reports upload_supabase --cities grenoble

# Run all stages (full pipeline)
python bulk_runner.py run --all-stages --cities all

# Force execution without confirmation
python bulk_runner.py run --stages synthesis --cities grenoble --force
```

### Supabase Operations

```bash
# Upload all processed data (interactive)
python bulk_runner.py upload_all

# Upload specific cities
python bulk_runner.py run --stages upload_supabase --cities grenoble nantes
```

## Workflow Patterns

### New City Processing

When you add a new city with PDF documents:

```bash
# 1. Run OCR
python bulk_runner.py run --stages ocr --cities NEW_CITY

# 2. Extract pages
python bulk_runner.py run --stages extract_pages --cities NEW_CITY  

# 3. Generate synthesis
python bulk_runner.py run --stages synthesis --cities NEW_CITY

# 4. Create reports
python bulk_runner.py run --stages reports --cities NEW_CITY

# 5. Upload to Supabase
python bulk_runner.py run --stages upload_supabase --cities NEW_CITY
```

### Batch Processing

For processing multiple cities efficiently:

```bash
# Process all OCR and page extraction
python bulk_runner.py run --stages ocr extract_pages --cities all

# Then synthesis for all
python bulk_runner.py run --stages synthesis --cities all

# Finally reports and upload
python bulk_runner.py run --stages reports upload_supabase --cities all
```

### Update Existing Data

To re-process and update existing city data:

```bash
# Re-run synthesis and reports
python bulk_runner.py run --stages synthesis reports --cities CITY_NAME

# Update Supabase
python bulk_runner.py run --stages upload_supabase --cities CITY_NAME
```

## Configuration

The system automatically reads from your YAML configuration files:

- `config/plu/plu_external.yaml` - External PDF sources
- `config/plu/plu_raw.yaml` - OCR outputs  
- `config/plu/plu_interim.yaml` - Extracted pages
- `config/plu/plu_processed.yaml` - Final processed data

### Updating Configurations

Regenerate YAML configs after adding new files:

```bash
python config/generate_plu_configs.py
```

## Environment Variables

For Supabase operations, ensure these are set:

```bash
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
```

## Advanced Features

### Task Generation

The system intelligently generates tasks based on:

- **File structure detection** - Handles different directory layouts (date-based vs direct)
- **Stage dependencies** - Ensures proper processing order
- **City filtering** - Process specific cities or all cities
- **Dry run capability** - Preview tasks before execution

### Error Handling

- **Robust execution** - Continues processing other tasks if one fails
- **Detailed logging** - All operations are logged with appropriate levels
- **Progress tracking** - Shows completion status and success/failure counts
- **Graceful degradation** - Handles missing files and invalid configurations

### Integration with Existing Workflow

The bulk processor:

- ✅ Uses your existing `main.py` commands
- ✅ Preserves your current file structure  
- ✅ Integrates with your Supabase setup
- ✅ Leverages your YAML configurations
- ✅ Maintains compatibility with manual processing

## File Structure Integration

The system works with your existing directory structure:

```text
data/
├── external/          # Source PDFs
│   ├── bordeaux/
│   │   └── 2024-02-02/      # Date-based structure
│   │       └── zones_A/
│   ├── grenoble/            # Direct structure
│   └── nantes/
├── raw/               # OCR outputs
├── interim/           # Extracted pages  
├── processed/         # Final JSON + metadata
└── pdf/              # Generated reports
```

## Troubleshooting

### Common Issues

1. **"No tasks generated"** - Check if YAML configs are up to date
2. **"Invalid city"** - Run `list-cities` to see available cities
3. **"Supabase connection failed"** - Verify environment variables
4. **"Task failed"** - Check logs for specific error details

### Debugging

```bash
# Use dry run to debug task generation
python bulk_runner.py run --stages STAGE --cities CITY --dry-run

# Check status to see data availability
python bulk_runner.py status

# Regenerate configs if files were added manually
python config/generate_plu_configs.py
```

## Migration from Manual Processing

If you're currently using `python.sh` and manual commands:

1. **Keep existing workflow** - The bulk processor is additive
2. **Start with dry runs** - Test with `--dry-run` first
3. **Process incrementally** - Start with single stages/cities
4. **Verify results** - Compare with manual processing outputs

The bulk processor executes the same `main.py` commands you're already using, just automatically and in bulk.

## Performance Considerations

- **Parallel processing** - Each task runs independently
- **Memory efficient** - Processes one task at a time
- **Resumable** - Failed tasks can be re-run individually
- **Scalable** - Handles any number of cities/documents

## Examples Reference

See `config/bulk_processing_examples.yaml` for complete examples and workflow patterns.

---

This bulk processing system transforms your manual PLU processing workflow into a scalable, automated pipeline while preserving all your existing tools and data structures.
