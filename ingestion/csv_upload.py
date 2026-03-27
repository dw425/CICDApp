"""CSV Upload - Parse and validate uploaded CSV/Excel files.
Implementation: Phase 5
"""
import pandas as pd
from io import BytesIO
import base64


def parse_upload(contents, filename):
    """Parse an uploaded file (from dcc.Upload component).

    Args:
        contents: base64-encoded file contents from dcc.Upload
        filename: original filename

    Returns:
        tuple: (DataFrame, error_message) - error_message is None on success
    """
    if contents is None:
        return None, "No file uploaded"

    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(BytesIO(decoded))
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(BytesIO(decoded))
        else:
            return None, f"Unsupported file type: {filename}"

        return df, None
    except Exception as e:
        return None, f"Error parsing {filename}: {str(e)}"
