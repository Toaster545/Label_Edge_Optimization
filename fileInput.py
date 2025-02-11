import pandas as pd


def xlsm_to_dataframe(xlsm_file, sheet_name, start_row=3):
    """
    Reads a specific sheet from an .xlsm file, starting from a specified row, and converts it to a Pandas DataFrame.
    
    Args:
        xlsm_file (str): Path to the .xlsm file.
        sheet_name (str): Name of the sheet to read.
        start_row (int): Row number to start reading from (1-based index).
    
    Returns:
        pd.DataFrame: DataFrame containing the sheet's data starting from the specified row.
    """
    print(f"Reading File: {xlsm_file}")
    try:
        # Load the sheet into a Pandas DataFrame, skipping rows before `start_row`
        df = pd.read_excel(
            xlsm_file, 
            sheet_name=sheet_name, 
            engine="openpyxl", 
            skiprows=start_row - 1
        )
        return df
    except ValueError as e:
        print(f"Error: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: The file '{xlsm_file}' was not found.")
        return None
    
def filter_inv_df(df, label_code, actIna="A", orderBy = "Larg."):
    df = df.loc[df['Actif / Inactif'] == actIna]
    df = df.sort_values(by=orderBy, ascending=True)
    df = df.reset_index(drop=True)
    df = convert_units(df)
    
    code_values = df["Code LabelEdge"].unique()

    # Print the unique values
    #print("Unique code values in 'Code LabelEdge':")
    #print(code_values)
    
    # Filtering 
    #df = df.loc[df["Code LabelEdge"] == label_code]
    df = df[["Code achat", "Code LabelEdge", "Larg.", "Longueur"]]
    
    df = df.reset_index(drop=True)
    return df

def filter_po_df(df, start_row):
    df = df.loc[df['Active/Inactive'] == 'A']
    po_df = df.loc[df['No'] >=start_row]
    po_df = po_df[po_df["Vendu à"].notna()]
    
    start_column = "Code Prix 1"
    named_columns = ["No", "Vendu à", "No Commande"]
    start_index = po_df.columns.get_loc(start_column)
    columns_to_keep = named_columns + list(po_df.columns[start_index:])
    po_df = po_df[columns_to_keep]
    
    po_df = process_groups(po_df, start_column)
    po_df = po_df.reset_index(drop=True)
    
    return po_df
    

def convert_units(df):
    """
    Converts 'mm' to 'po' (inches) and 'm' to 'pi' (feet) in the specified DataFrame columns.
    
    Args:
        df (pd.DataFrame): Input DataFrame with "Larg.", "Unit", "Longueur", and "Unit2" columns.

    Returns:
        pd.DataFrame: Updated DataFrame with converted values.
    """
    # Conversion factors
    mm_to_inch = 0.0393701
    m_to_feet = 3.28084
    
    df["Larg."] = df["Larg."].astype(float)
    df["Longueur"] = df["Longueur"].astype(float)

    # Convert "Larg." from mm to inches if the Unit is "mm"
    mask_larg_mm = df["Unit"] == "mm"
    df.loc[mask_larg_mm, "Larg."] = df.loc[mask_larg_mm, "Larg."] * mm_to_inch
    df.loc[mask_larg_mm, "Unit"] = "po"

    # Convert "Longueur" from meters to feet if the Unit2 is "m"
    mask_long_m = df["Unit2"] == "m"
    df.loc[mask_long_m, "Longueur"] = df.loc[mask_long_m, "Longueur"] * m_to_feet
    df.loc[mask_long_m, "Unit2"] = "pi"

    return df

def process_groups(df, start_column):
    """
    Processes a DataFrame by grouping columns into subsets of 4 starting from a specific column.
    Combines columns 2, 3, and 4 of each group into a single column named 'Product#'.
    Updates 'num_products' to exclude invalid products (e.g., 'nan/nan/nan').

    Args:
        df (pd.DataFrame): Input DataFrame.
        start_column (str): Column name from which to start processing.

    Returns:
        pd.DataFrame: Processed DataFrame with the grouped 'Product#' columns and 'num_products' column.
    """
    # Find the start index for processing
    start_index = df.columns.get_loc(start_column)
    
    # Columns before the start index remain untouched
    processed_df = df.iloc[:, :start_index].copy()
    
    # Group columns starting from the start index
    remaining_columns = df.iloc[:, start_index:]
    num_groups = len(remaining_columns.columns) // 4  # Number of groups of 4
    product_columns = []

    # Process each group
    for group_idx in range(num_groups):
        group_start = group_idx * 4
        group_columns = remaining_columns.iloc[:, group_start:group_start + 4]
        
        # Combine columns 2, 3, and 4 of the group into a single column
        product_column = (
            group_columns.iloc[:, 1].astype(str) + '/' +
            group_columns.iloc[:, 2].astype(str) + '/' +
            group_columns.iloc[:, 3].astype(str)
        )
        
        # Name the new column as 'Product#X', where X is the group number
        product_column_name = f"Product#{group_idx + 1}"
        processed_df[product_column_name] = product_column
        product_columns.append(product_column_name)

    # Add the 'num_products' column by counting valid 'Product#' entries (excluding 'nan/nan/nan')
    processed_df["num_products"] = processed_df[product_columns].apply(
        lambda row: sum((value != "nan/nan/nan" 
                         and value != '//0/nan/nan' 
                         and value != '//0/nan/0.0'
                         and value != '//nan/nan') for value in row), axis=1
    )

    return processed_df
