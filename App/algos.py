import copy, random
import pandas as pd
from tqdm import tqdm
from utils import print_masters_table, createMasterDict, createProductBlocks, process_selected_pos, filter_inventory


########################################
# Helper: Check if a solution is valid
########################################
def is_valid_solution(masters, num_products):
    """
    Check if the solution is valid, meaning all products are assigned.
    Each master has 'Products' as a list of blocks (lists). This function 
    counts the total assigned products and returns True if it matches num_products.
    """
    assigned = sum(len(block) for m in masters for block in m['Products'])
    return assigned == num_products

########################################
# Main Solve Function
########################################
def solve(inv_df, po_df, selected_pos, label_code, 
          util_tol=0.8,         # Minimum utilization threshold
          rem_tol=0.15,         # Maximum removal fraction per product type
          len_tol=0.1,
          num_restarts=100,     # Number of restarts for the local search
          iterations=1000):     # Local search iterations per restart
    """
    Main function to compute a solution using an initial solution, local search, and restarts.
    It also removes underutilized product assignments and re-optimizes.
    If the final solution is not valid (i.e. not all products are used), it prints an error message.
    """
    # Process the selected purchase orders into products and a total MSI target.
    products, total_msi = process_selected_pos(selected_pos)
    original_product_count = len(products)  # Keep track of how many products we must assign.
    
    # Filter the inventory DataFrame for the specific label code.
    filtered_inv = filter_inventory(inv_df, label_code)
    
    best_overall_waste = float('inf')
    best_overall_masters = None
    
    # Create a progress bar to track restarts (display best overall waste in percentage, two decimals)
    progress_bar = tqdm(range(num_restarts), desc=f"Restart iterations | Best Waste: {best_overall_waste*100:.2f}%")
    
    prod_len = products[0][1]
    print("Max Length:", ((len_tol * prod_len) + prod_len), "Min length",(prod_len-(len_tol * prod_len)))
    # Restart loop: compute initial solution, run local search, and update best solution if improved.
    for restart in progress_bar:
        products_copy = products[:]  # Make a shallow copy of the products list
        
        # Compute an initial solution (randomizes masters and products order internally)
        masters = compute_initial_solution(filtered_inv, products_copy, len_tol)
        
        # Run local search starting from this initial solution.
        current_masters, current_waste = local_search_solution(masters, total_msi, iterations=iterations, lengthTol=len_tol)
        
        # If the current solution is better, update the best overall solution.
        if current_waste < best_overall_waste:
            best_overall_waste = current_waste
            best_overall_masters = current_masters
        
        # Update progress bar description with current best overall waste (in percent)
        progress_bar.set_description(f"Restart {restart+1}/{num_restarts} | Best Waste: {best_overall_waste*100:.2f}%")
    
    # Check if the best solution is valid (all products assigned)
    if best_overall_masters is None or not is_valid_solution(best_overall_masters, original_product_count):
        print("No solution found using current number of Products")
        #return None
    
    print(f"\nBest waste: {best_overall_waste*100:.4f}%")
    print_masters_table(best_overall_masters)
    
    # Optionally, further processing (like removal of underutilized products) can be done here.
    
    return best_overall_masters

########################################
# INITIAL SOLUTION COMPUTING
########################################
def compute_initial_solution(inv_df, products, len_tol):
    """
    Create the master dictionary from inventory and assign products initially.
    The number of product lists per master is determined by comparing the master length
    to the product length (using createMasterDict).
    """
    # Use the product length (assumed to be the second element of the product tuple) as the unit.
    length = products[0][1]
    masters = createMasterDict(inv_df=inv_df, prod_list_length=length, len_tol=len_tol)
    masters = initialSol(masters, products, lengthTol=len_tol)
    waste = calculateWaste(masters)
    # print("Initial waste:", waste)
    return masters

########################################
# Initial Product Assignment
########################################
def initialSol(masters, products, lengthTol=0.1):
    random.shuffle(masters)
    random.shuffle(products)
    
    # Iterate over a copy of the products list so we can modify the original.
    for p in products[:]:
        prodWidth, prodLength, _ = p
        assigned = False
        for m in masters:
            # m['Products'] is assumed to be a list of blocks (lists)
            num_blocks = len(m['Products'])
            if num_blocks == 0:
                continue
            for block in m['Products']:
                used_width = sum(product[0] for product in block)
                if (m['Width'] - used_width) >= prodWidth:
                    # Compute relative difference using the allocated block length (m['Length'])
                    lengthDiff = abs(m['Length'] - prodLength) / m['Length']
                    if lengthDiff <= lengthTol:
                        block.append(p)
                        products.remove(p)
                        assigned = True
                        break  # Assigned to a block; stop iterating blocks.
            if assigned:
                break  # Assigned to a master; stop iterating masters.
        if not assigned:
            #print(p)
            pass
    #print_masters_table(masters)
    return masters


########################################
# Removing Underutilized Masters
########################################
def remove_underutilized_masters(masters, total_msi, min_utilization=0.8, max_removal_fraction=0.5):
    """
    For each master that has products but whose width utilization is below min_utilization,
    remove products from that master—but for each product type (tuple: (width, length, product_msi))
    do not remove more than max_removal_fraction of its original count.
    
    This removal is only accepted if the resulting waste (calculated by calculateWaste)
    is lower than the original waste.
    """
    orig_waste = calculateWaste(masters)
    new_masters = copy.deepcopy(masters)
    new_total_msi = total_msi
    
    orig_counts = {}
    for m in new_masters:
        for p in m['Products']:
            key = (p[0], p[1], p[2])
            orig_counts[key] = orig_counts.get(key, 0) + 1

    removal_counts = {key: 0 for key in orig_counts}
    removed_products = []

    for m in new_masters:
        if m['Products']:
            utilization = sum(p[0] for p in m['Products']) / m['Width']
            if utilization < min_utilization:
                new_products = []
                for p in m['Products']:
                    key = (p[0], p[1], p[2])
                    if removal_counts[key] < max_removal_fraction * orig_counts[key]:
                        removed_products.append(p)
                        removal_counts[key] += 1
                    else:
                        new_products.append(p)
                m['Products'] = new_products
                print("Underutilized master (utilization={:.2f}) processed.".format(utilization))
    
    if removed_products:
        total_removed_msi = sum(p[2] for p in removed_products)
        new_total_msi -= total_removed_msi
        print("New total MSI after removal:", new_total_msi)
        product_counts_removed = {}
        for p in removed_products:
            key = (p[0], p[1], p[2])
            product_counts_removed[key] = product_counts_removed.get(key, 0) + 1
        for key, count in product_counts_removed.items():
            print(f"Removed {count} of product (Width={key[0]}, Length={key[1]}, MSI per product={key[2]})")
    
    new_waste = calculateWaste(new_masters)
    print("Original waste:", orig_waste, "New waste:", new_waste)
    
    if new_waste < orig_waste:
        print("Accepting removal solution as it improves waste.")
        return new_masters, new_total_msi
    else:
        print("Discarding removal solution as it does not improve waste.")
        return masters, total_msi

########################################
# Waste Calculation
########################################
def calculateWaste(masters):
    total_msi = 0
    total_prod = 0

    for m in masters:
        num_blocks = sum(1 for block in m['Products'] if block)
        master_msi = (m['Length'] * m['Width'] * 12 * num_blocks) / 1000
        assigned_msi = sum((p[0] * m['Length'] * 12) / 1000 for block in m['Products'] for p in block)
        
        if assigned_msi > 0:
            m['Waste'] = abs(master_msi - assigned_msi) / assigned_msi
        else:
            m['Waste'] = float('inf')

        total_msi += master_msi
        total_prod += assigned_msi

    if total_prod == 0:
        return float('inf')

    return abs(total_msi - total_prod) / total_prod


########################################
# Perturbation: Modify the Current Solution
########################################
import random
import copy

def perturb_solution(masters, lengthTol=0.1, top_waste_fraction=0.3, allow_swaps=True):
    """
    Perturb the current assignment by:
    1. Moving a product from a high-waste master to a lower-waste master (if space allows).
    2. Swapping products between two masters (if beneficial and swapping is enabled).

    - Prioritizes high-waste masters (top `top_waste_fraction` percentage).
    - Ensures that the new master has enough space for at least one more product.
    - If `allow_swaps` is True, attempts to swap two products instead of just moving.
    - Only makes a move if it reduces overall waste.
    """
    new_masters = copy.deepcopy(masters)

    # Sort masters by waste (descending order)
    sorted_masters = sorted(new_masters, key=lambda m: m['Waste'], reverse=True)

    # Select only the top X% highest waste masters
    num_top_waste = max(1, int(len(sorted_masters) * top_waste_fraction))
    high_waste_masters = sorted_masters[:num_top_waste]

    # Identify candidate masters that have space available
    candidate_masters = [m for m in sorted_masters if any(len(block) > 0 for block in m['Products'])]

    if not high_waste_masters or not candidate_masters:
        return new_masters  # No viable candidates

    # Pick a high-waste master at random
    master_from = random.choice(high_waste_masters)

    # Select a product from the most overfilled block in that master
    non_empty_blocks = [block for block in master_from['Products'] if block]
    if not non_empty_blocks:
        return new_masters

    block_from = max(non_empty_blocks, key=lambda b: sum(p[0] for p in b))  # Pick the most filled block
    product = random.choice(block_from)
    block_from.remove(product)

    # Try to move it to a lower-waste master
    random.shuffle(candidate_masters)
    assigned = False
    prodWidth, prodLength, _ = product

    for m in candidate_masters:
        if m == master_from:
            continue  # Skip the same master
        
        # Check all blocks within the candidate master
        for block in m['Products']:
            used_width = sum(p[0] for p in block)
            widthLeft = m['Width'] - used_width
            lengthDiff = abs(m['Length'] - prodLength) / prodLength

            # Option 1: Directly add the product
            if widthLeft >= prodWidth and lengthDiff <= lengthTol:
                block.append(product)
                assigned = True
                break

        if assigned:
            break

    # If no valid move, try swapping instead (only if swapping is enabled)
    if not assigned and allow_swaps:
        for m in candidate_masters:
            if m == master_from:
                continue
            
            # Find a product to swap with
            for block in m['Products']:
                for other_product in block:
                    otherWidth, otherLength, _ = other_product
                    widthLeft_in_master_from = master_from['Width'] - sum(p[0] for p in block_from) + prodWidth
                    widthLeft_in_master_to = m['Width'] - sum(p[0] for p in block) + otherWidth
                    
                    lengthDiff_from = abs(master_from['Length'] - otherLength) / master_from['Length']
                    lengthDiff_to = abs(m['Length'] - prodLength) / m['Length']

                    if (
                        widthLeft_in_master_from >= otherWidth and
                        widthLeft_in_master_to >= prodWidth and
                        lengthDiff_from <= lengthTol and
                        lengthDiff_to <= lengthTol
                    ):
                        # Perform swap
                        block.remove(other_product)
                        block.append(product)
                        block_from.append(other_product)
                        assigned = True
                        break
                if assigned:
                    break
            if assigned:
                break

    # If no move or swap was found, return product to the original master
    if not assigned:
        block_from.append(product)

    return new_masters


########################################
# Local Search Wrapper
########################################
def local_search_solution(masters, total_msi, iterations=10000, lengthTol=0.1):
    """
    Run the local search to improve the solution.
    """
    best_masters, best_waste = localSearch(masters, total_msi, iterations=iterations, lengthTol=lengthTol)
    return best_masters, best_waste

def localSearch(masters, total_prod, iterations=1000, lengthTol=0.1):
    """
    Iteratively perturb the solution and accept changes that lower the waste.
    """
    best_masters = copy.deepcopy(masters)
    best_waste = calculateWaste(best_masters)
    
    for i in range(iterations):
        candidate = perturb_solution(best_masters, lengthTol)
        candidate_waste = calculateWaste(candidate)
        if candidate_waste < best_waste:
            best_masters, best_waste = candidate, candidate_waste
            # Optionally, log progress: print(f"Iteration {i}: Improved waste = {best_waste}")
    
    return best_masters, best_waste
