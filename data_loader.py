import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def connect_to_sheets():
    """
    Connect to Google Sheets using service account from Streamlit Secrets
    """
    # Spreadsheet ID
    sheet_id = "1OrofvXQ5a-H27SR5YtrTkv4szzRRDQ6KUELGAVMWbVg"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="
    
    try:
        # Get credentials from Streamlit Secrets
        if 'gcp_service_account' in st.secrets:
            # Convert the Streamlit secrets dict to a service account info dict
            credentials_dict = st.secrets["gcp_service_account"]
            
            # Create credentials
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_dict, scope)
            
            # Authorize and get the Google Sheets client
            client = gspread.authorize(credentials)
            
            return client, sheet_id, url
        else:
            # Fallback to public access if no credentials
            return None, sheet_id, url
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None, sheet_id, url

def load_dataset(sheet_name):
    """
    Load dataset from specific sheet
    """
    try:
        client, sheet_id, url = connect_to_sheets()
        
        if client:
            # Use gspread client to open the sheet
            try:
                spreadsheet = client.open_by_key(sheet_id)
                worksheet = spreadsheet.worksheet(sheet_name)
                data = worksheet.get_all_values()
                
                # Convert to pandas DataFrame
                if data:
                    headers = data[0]
                    values = data[1:]
                    df = pd.DataFrame(values, columns=headers)
                    return df
                else:
                    st.warning(f"Tidak ada data di sheet {sheet_name}")
                    return pd.DataFrame()
            except Exception as e:
                st.warning(f"Gagal mengakses sheet dengan gspread: {e}. Mencoba metode alternatif...")
                # Fallback to direct CSV access if gspread fails
                df = pd.read_csv(f"{url}{sheet_name}")
                return df
        else:
            # Fallback to direct CSV access
            df = pd.read_csv(f"{url}{sheet_name}")
            return df
    except Exception as e:
        st.error(f"Error loading data from sheet {sheet_name}: {e}")
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
