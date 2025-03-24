import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_sheets():
    """
    Connect to Google Sheets using service account or public access
    """
    try:
        # Untuk spreadsheet publik bisa diakses langsung dengan URL
        sheet_id = "1OrofvXQ5a-H27SR5YtrTkv4szzRRDQ6KUELGAVMWbVg"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="
        return sheet_id, url
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None, None

def load_dataset(sheet_name):
    """
    Load dataset from specific sheet
    """
    sheet_id, url = connect_to_sheets()
    if not sheet_id:
        return pd.DataFrame()
    
    try:
        # Load data directly using pandas
        df = pd.read_csv(f"{url}{sheet_name}")
        return df
    except Exception as e:
        print(f"Error loading data from sheet {sheet_name}: {e}")
        return pd.DataFrame()

def process_entities(cell_value):
    """
    Process cell values by:
    1. Splitting entities by comma
    2. Removing entities containing '##'
    """
    if pd.isna(cell_value):
        return []
    
    entities = [entity.strip() for entity in str(cell_value).split(',')]
    filtered_entities = [entity for entity in entities if '##' not in entity]
    return filtered_entities

def process_dataset(df, column_name):
    """
    Process specific column in dataset to extract entities
    """
    if column_name not in df.columns:
        return df, pd.Series()
    
    # Apply processing to the column
    entities_series = df[column_name].apply(process_entities)
    
    # Create a flattened list of all entities
    all_entities = []
    for entity_list in entities_series:
        all_entities.extend(entity_list)
    
    entity_counts = pd.Series(all_entities).value_counts()
    
    return df, entity_counts

def get_unique_locations(df, location_column):
    """
    Extract unique locations from dataset
    """
    if location_column not in df.columns:
        return []
    
    # Process locations column to get unique values
    locations = []
    for loc in df[location_column]:
        if pd.isna(loc):
            continue
        entities = process_entities(loc)
        locations.extend(entities)
    
    return list(set(locations))
