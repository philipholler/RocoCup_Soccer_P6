from pathlib import Path

VERIFYTA_PATH = Path(__file__).parent / 'bin' / 'verifyta'
VERIFYTA_QUERIES_PATH = Path(__file__).parent.parent / 'uppaal' / 'queries'
VERIFYTA_MODELS_PATH = Path(__file__).parent.parent / 'uppaal' / 'models'
VERIFYTA_OUTPUT_DIR_PATH = Path(__file__).parent.parent / 'uppaal' / 'outputdir'