import pandas as pd


def print_masters_table(masters):
    """
    Prints a formatted table where each row represents a master
    and the columns represent the widths of the products in that master.
    
    - Masters are sorted in decreasing order based on their width.
    - Product widths in each row are sorted in increasing order.
    """
    # Prepare data for DataFrame
    table_data = []
    max_products = 0  # Track the max number of products in any master
    
    for i, master in enumerate(masters):
        if master['Products']:  # Only include masters with products
            product_widths = sorted([p[0] for p in master['Products']], reverse=True)  # Sort widths in increasing order
            max_products = max(max_products, len(product_widths))  # Update max products
            table_data.append([int(master['Width'])] + product_widths)  # Store row data
    
    # Create column headers dynamically based on the max number of products
    column_headers = ["Master"] + [f"Product {i+1}" for i in range(max_products)]
    
    # Convert to DataFrame and sort Masters in decreasing order
    df = pd.DataFrame(table_data, columns=column_headers).fillna("-")
    df = df.sort_values(by="Master", ascending=False)  # Sort by master width in decreasing order
    
    # Print formatted table
    print(df.to_string(index=False))

def createProductBlocks(po_df, selected_pos):
    
    numbers = []
    for p in selected_pos:
        p = p.split(' ')[0]
        numbers.append(p)
    
    df = po_df.loc[po_df['No'].astype(str).isin(numbers)]
    
    valid_products_per_row = []

    # Loop through each row
    for index, row in df.iterrows():
        # Get the number of valid products
        num_products = int(row['num_products'])
        
        # Collect valid products
        valid_products = []
        for i in range(1, num_products + 1):
            product = row[f'Product#{i}']
            if product != 'nan/nan/nan':  # Ensure the product is valid
                valid_products_per_row.append(product)
    
    return valid_products_per_row

def createMasterDict(inv_df):
    
    masterDict = []
    
    for index, row in inv_df.iterrows():
        code = float(row['Code achat'])
        width = float(row['Larg.'])
        length = float(row['Longueur'])
        tempDict = {'Code': code, 'Width': width, 'Length': length, 'Products': []}
        masterDict.append(tempDict)
    
    
    return masterDict

def process_selected_pos(selected_pos):
    """
    Convert selected PO strings into a list of product tuples and compute the total MSI.
    Each product tuple is: (width, length_in_mm, product_msi)
    """
    keys = ['Paper', 'Width', 'Length', 'Nb', 'msi']
    products_dict = [dict(zip(keys, item.split('/'))) for item in selected_pos]
    
    for p in products_dict:
        print(f"  Product (Width={p['Width']}, Length={p['Length']}, MSI per product={p['msi']}): {p['Nb']}")
    
    products = []
    for d in products_dict:
        num = int(float(d['Nb']))
        # Distribute the total MSI equally among the individual products
        prod_msi = float(d['msi']) / num
        for _ in range(num):
            products.append((float(d['Width']), float(d['Length']) * 1000, prod_msi))
    
    total_msi = sum(float(d['msi']) for d in products_dict)
    print("Total MSI:", total_msi)
    return products, total_msi

def filter_inventory(inv_df, label_code):
    """
    Filter the inventory DataFrame to only include rows matching the label code,
    and drop the 'Code LabelEdge' column.
    """
    filtered_df = inv_df.loc[inv_df['Code LabelEdge'] == label_code].copy()
    filtered_df = filtered_df.drop(columns=['Code LabelEdge'])
    return filtered_df

