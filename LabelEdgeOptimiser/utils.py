import pandas as pd

def print_masters_table(masters):
    table_data = []
    max_products = 0  # Maximum number of products in any block

    for master in masters:
        master_msi = (master['Width'] * master['Length'] * 12) / 1000  # Calculate Master MSI

        # Assume master['Waste'] is a list corresponding to each block in master['Products']
        for block, waste in zip(master['Products'], master['Waste']):
            product_widths = sorted([p[0] for p in block], reverse=True)
            max_products = max(max_products, len(product_widths))

            # Compute Block MSI based on assigned product widths
            block_msi = (sum(p[0] for p in block) * master['Length'] * 12) / 1000 if block else 0
            
            # Append data to the table
            table_data.append([master['Code'], master['Width'], master['Length'], waste] + product_widths)

    # Adjust column headers to include Master MSI & Block MSI
    column_headers = ["Master ID", "Width", "Length", "Waste"] + [f"Product {i+1}" for i in range(max_products)]
    
    # Create DataFrame and format output
    df = pd.DataFrame(table_data, columns=column_headers).fillna("-")
    df = df.sort_values(by="Master ID", ascending=False)
    print(df.to_string(index=False))


def createProductBlocks(po_df, selected_pos):
    
    numbers = [p.split(' ')[0] for p in selected_pos]
    
    # Create a lookup dictionary for quick mapping from PO_Number to Products string.
    lookup = {str(row['PO_Number']): row['Products'] for _, row in po_df.iterrows()}
    
    product_blocks = []
    for num in numbers:
        product_str = lookup.get(num, '')
        if product_str:
            # Split product_str by comma, trim whitespace, and filter out empty strings.
            products = [p.strip() for p in product_str.split(',') if p.strip()]
            product_blocks.extend(products)
    
    return product_blocks

def createMasterDict(inv_df, prod_list_length, len_tol=0.1):
    masterDict = []
    
    for index, row in inv_df.iterrows():
        code = row['Roll ID']
        width = float(row['Larg.'])
        master_length = float(row['Longueur'])
        
        # Calculate how many full product lists fit into the master length.
        base_count = int(master_length // prod_list_length)
        remainder = master_length - (base_count * prod_list_length)
        
        # If the remainder is within tolerance of a full unit, add an extra list.
        if (remainder / prod_list_length) >= (1 - len_tol):
            num_lists = base_count + 1
        else:
            num_lists = base_count
        
        # Ensure at least one product list is created.
        if num_lists < 1:
            num_lists = 1
        
        # Calculate allocated length per product list.
        allocated_length = master_length / num_lists
        
        tempDict = {
            'Code': code,
            'Width': width,
            'Length': allocated_length,
            'Products': [[] for _ in range(num_lists)],  # Create a list of empty product lists.
            'Waste': []
        }
        masterDict.append(tempDict)
        
    #print(masterDict)
    
    return masterDict

def process_selected_pos(selected_pos):
    """
    Convert selected PO strings into a list of product tuples and compute the total MSI.
    Each product tuple is: (width, length_in_mm, product_msi)
    """
    keys = ['Paper', 'Width', 'Length', 'Nb', 'msi']
    products_dict = [dict(zip(keys, item.split('/'))) for item in selected_pos]
    print(products_dict)
    
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
    filtered_df = inv_df.loc[inv_df['Code LabelEdge'].isin(label_code)].copy()
    filtered_df = filtered_df.drop(columns=['Code LabelEdge'])
    return filtered_df

