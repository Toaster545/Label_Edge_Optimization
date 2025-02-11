def createProductBlocks(po_df, selected_pos):
    
    print(selected_pos)
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

def initialSol():
    return

def solve(inv_df, po_df, selected_pos):
    products = createProductBlocks(po_df, selected_pos)
    
    
    
    return