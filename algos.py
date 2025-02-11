import copy, random
import pandas as pd

def solve(inv_df, po_df, selected_pos, label_code, util_tol = 0.8, rem_tol = 0.15):
    # Process the selected purchase orders into products and a total MSI target.
    products, total_msi = process_selected_pos(selected_pos)
    
    # Filter the inventory DataFrame for the specific label code.
    filtered_inv = filter_inventory(inv_df, label_code)
    
    # Compute an initial solution.
    masters = compute_initial_solution(filtered_inv, products, total_msi)
    
    # Run local search to improve the solution.
    best_masters, best_waste = local_search_solution(masters, total_msi, iterations=10000, lengthTol=0.1)
    print_masters_table(best_masters)
    
    # Remove products from masters that are underutilized.
    best_masters, total_msi = remove_underutilized_masters(best_masters, total_msi, min_utilization=util_tol, max_removal_fraction=rem_tol)
    
    # Optionally, re-run local search with the updated solution.
    best_masters, best_waste = local_search_solution(best_masters, total_msi, iterations=10000, lengthTol=0.1)
    print_masters_table(best_masters)
    
    
    return best_masters


def print_masters_table(masters):
    """
    Prints a formatted table where each row represents a master
    and the columns represent the widths of the products in that master.
    """
    # Prepare data for DataFrame
    table_data = []
    max_products = 0  # Track the max number of products in any master
    
    for i, master in enumerate(masters):
        if master['Products']:  # Only include masters with products
            product_widths = [p[0] for p in master['Products']]  # Extract widths
            max_products = max(max_products, len(product_widths))  # Update max products
            table_data.append([int(master['Width'])] + product_widths)
    
    # Create column headers dynamically based on the max number of products
    column_headers = ["Master"] + [f"Product {i+1}" for i in range(max_products)]
    
    # Convert to DataFrame and fill empty cells with "-"
    df = pd.DataFrame(table_data, columns=column_headers).fillna("-")
    
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

def compute_initial_solution(inv_df, products, total_msi):
    """
    Create the master dictionary from inventory and assign products initially.
    Also print the waste of the initial solution.
    """
    masters = createMasterDict(inv_df=inv_df)
    masters = initialSol(masters, products)
    waste = calculateWaste(masters, total_msi)
    print("Initial waste:", waste)
    return masters

def local_search_solution(masters, total_msi, iterations=10000, lengthTol=0.1):
    """
    Improve the solution using local search.
    """
    best_masters, best_waste = localSearch(masters, total_msi, iterations=iterations, lengthTol=lengthTol)
    print("Best waste found:", best_waste)
    return best_masters, best_waste

def remove_underutilized_masters(masters, total_msi, min_utilization=0.8, max_removal_fraction=0.5):
    """
    For each master that has products but whose width utilization is below min_utilization,
    remove products from that master—but for each product type (defined as (width, length, product_msi))
    do not remove more than max_removal_fraction of its original count.
    
    This removal is only kept if the resulting waste (calculated by calculateWaste) is lower
    than the original waste.
    
    Returns:
      (masters, total_msi) based on whether the removal improved the waste.
    """
    import copy
    # Compute the original waste value.
    orig_waste = calculateWaste(masters, total_msi)
    
    # Create a deep copy of the masters and total_msi to test removals.
    new_masters = copy.deepcopy(masters)
    new_total_msi = total_msi
    
    # Compute the original global counts for each product type.
    orig_counts = {}
    for m in new_masters:
        for p in m['Products']:
            key = (p[0], p[1], p[2])
            orig_counts[key] = orig_counts.get(key, 0) + 1

    # Initialize removal counts for each product type.
    removal_counts = {key: 0 for key in orig_counts}
    removed_products = []  # To track all removed products

    # Process each master.
    for m in new_masters:
        if m['Products']:
            # Calculate utilization as the sum of product widths divided by master width.
            utilization = sum(p[0] for p in m['Products']) / m['Width']
            if utilization < min_utilization:
                new_products = []
                for p in m['Products']:
                    key = (p[0], p[1], p[2])
                    # Only remove this product if the number removed so far is less than the allowed fraction.
                    if removal_counts[key] < max_removal_fraction * orig_counts[key]:
                        removed_products.append(p)
                        removal_counts[key] += 1
                    else:
                        new_products.append(p)
                m['Products'] = new_products
                print("Underutilized master (utilization={:.2f}) processed.".format(utilization))
    
    if removed_products:
        # Subtract the MSI of removed products from new_total_msi.
        total_removed_msi = sum(p[2] for p in removed_products)
        new_total_msi -= total_removed_msi
        print("New total MSI after removal:", new_total_msi)
        # Print the number of removed products per type.
        product_counts_removed = {}
        for p in removed_products:
            key = (p[0], p[1], p[2])
            product_counts_removed[key] = product_counts_removed.get(key, 0) + 1
        for key, count in product_counts_removed.items():
            print(f"Removed {count} of product (Width={key[0]}, Length={key[1]}, MSI per product={key[2]})")
    
    # Compute the new waste value after removals.
    new_waste = calculateWaste(new_masters, new_total_msi)
    print("Original waste:", orig_waste, "New waste:", new_waste)
    
    # Accept the new solution only if the waste is improved.
    if new_waste < orig_waste:
        print("Accepting removal solution as it improves waste.")
        return new_masters, new_total_msi
    else:
        print("Discarding removal solution as it does not improve waste.")
        return masters, total_msi

def initialSol(masters, products, lengthTol = 0.1):
    
    # Iterate over a copy of the list so we can modify the original safely
    for p in products[:]:  # Using products[:] creates a shallow copy
        prodWidth, prodLength, _ = p
        for m in masters:
            widthLeft = m['Width'] - sum(p[0] for p in m["Products"])
            lengthDiff = abs(m['Length'] - prodLength) / prodLength
            if widthLeft > prodWidth and lengthDiff <= lengthTol:
                m['Products'].append(p)
                products.remove(p)  # Remove the product from the original list
                break  # Stop checking other masters once assigned
    
    
    return masters

def calculateWaste(masters, total_prod):
    # Compute total MSI for all masters that have at least one product
    total_msi = sum((m['Length'] * m['Width'] * 12) / 1000 for m in masters if m['Products'])

    # Output the result
    waste = abs(total_msi - total_prod)/total_prod
    return waste

def perturb_solution(masters, lengthTol=0.1):
    """
    Perturb the current assignment by removing one product from a random master 
    and trying to reassign it to a different master.
    """
    new_masters = copy.deepcopy(masters)
    # Select a random master that has at least one product
    masters_with_products = [m for m in new_masters if m['Products']]
    if not masters_with_products:
        return new_masters  # No change if none have products
    master_from = random.choice(masters_with_products)
    # Randomly remove a product from this master
    product = random.choice(master_from['Products'])
    master_from['Products'].remove(product)
    
    # Attempt to assign the product to a different master
    other_masters = [m for m in new_masters if m is not master_from]
    random.shuffle(other_masters)
    assigned = False
    prodWidth, prodLength, _ = product
    for m in other_masters:
        widthLeft = m['Width'] - sum(p[0] for p in m["Products"])
        lengthDiff = abs(m['Length'] - prodLength) / prodLength
        if widthLeft > prodWidth and lengthDiff <= lengthTol:
            m['Products'].append(product)
            assigned = True
            break
    if not assigned:
        # If no suitable master is found, reassign to original master
        master_from['Products'].append(product)
    return new_masters

def localSearch(masters, total_prod, iterations=1000, lengthTol=0.1):
    """
    Iteratively perturb the solution and accept changes that reduce waste.
    """
    best_masters = copy.deepcopy(masters)
    best_waste = calculateWaste(best_masters, total_prod)
    
    for i in range(iterations):
        candidate = perturb_solution(best_masters, lengthTol)
        candidate_waste = calculateWaste(candidate, total_prod)
        if candidate_waste < best_waste:
            best_masters, best_waste = candidate, candidate_waste
            # Optionally, print or log progress:
            # print(f"Iteration {i}: Improved waste = {best_waste}")
    
    return best_masters, best_waste
