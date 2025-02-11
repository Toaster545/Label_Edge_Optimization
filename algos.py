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
        width = float(row['Larg.'])
        length = float(row['Longueur'])
        tempDict = {'Width': width, 'Length': length, 'Cur Total': 0, }
        masterDict.append(tempDict)
    
    
    return masterDict

def initialSol():
    return

def solve(inv_df, po_df, selected_pos, label_code):
    keys = ['Paper', 'Width', 'Length', 'Nb', 'msi']
    products_dict = [dict(zip(keys, item.split('/'))) for item in selected_pos]
    products = [(float(d['Width']), float(d['Length'])) for d in products_dict for _ in range(int(float(d['Nb'])))]
    total_msi_pos = sum(float(d['msi']) for d in products_dict)
    print("Total MSI: ", total_msi_pos , "Products: ", products)
    
    inv_df = inv_df.loc[inv_df['Code LabelEdge'] == label_code]
    inv_df = inv_df.drop(columns=['Code LabelEdge'])
    masters = createMasterDict(inv_df=inv_df)
    print("Masters", masters)
    
    
    
    return