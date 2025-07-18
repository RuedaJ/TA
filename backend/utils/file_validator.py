
import pandas as pd

REQUIRED_COLUMNS = {
    "assets": ["Asset Name", "Location", "Floor Area (m²)", "Carbon Intensity (kgCO2e/m²)", "EPC Rating"],
    "utilities": ["Asset Name", "Month", "Energy Consumption (kWh)", "Water Consumption (m³)", "Waste (kg)"],
}

def validate_csv(file_path: str, file_type: str) -> dict:
    """
    Validates a CSV file against required schema.

    Args:
        file_path (str): Path to the CSV file.
        file_type (str): One of ['assets', 'utilities']

    Returns:
        dict: {'status': 'success' or 'error', 'message': str, 'data': DataFrame or None}
    """
    try:
        df = pd.read_csv(file_path)

        missing_cols = [col for col in REQUIRED_COLUMNS[file_type] if col not in df.columns]
        if missing_cols:
            return {"status": "error", "message": f"Missing columns: {', '.join(missing_cols)}", "data": None}

        return {"status": "success", "message": "File validated successfully.", "data": df}

    except Exception as e:
        return {"status": "error", "message": str(e), "data": None}
