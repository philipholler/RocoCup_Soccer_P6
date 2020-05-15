from pathlib import Path

VERIFYTA_PATH = Path(__file__).parent / 'bin' / 'verifyta'
QUERIES_PATH = Path(__file__).parent.parent / 'uppaal' / 'queries'
MODELS_PATH = Path(__file__).parent.parent / 'uppaal' / 'models'
OUTPUT_DIR_PATH = Path(__file__).parent.parent / 'uppaal' / 'outputdir'
STATIC_MODEL_RESULTS = Path(__file__).parent.parent / 'uppaal' / 'staticmodels_results'