import copy, random, math
import pandas as pd
from tqdm import tqdm
from utils import print_masters_table, createMasterDict, createProductBlocks, process_selected_pos, filter_inventory

########################################
# Helper: Check Validity of a Solution
########################################
def is_valid_solution(masters, num_products):
    assigned = sum(len(block) for m in masters for block in m['Products'])
    return assigned == num_products

########################################
# Waste Calculation (as Percentage)
########################################
def calculateWaste(masters):
    total_msi = 0
    total_prod = 0

    for m in masters:
        block_wastes = []
        
        for block in m['Products']:
            if not block:  # Skip empty blocks
                block_wastes.append(0)
                continue

            # Theoretical MSI for this block based on its assigned width
            total_master = (m['Length'] * m['Width'] * 12) / 1000
            total_block = sum((p[0] * m['Length'] * 12) / 1000 for p in block)

            # Calculate waste only for blocks that contain products
            if total_block > 0:
                waste = (abs(total_master - total_block) / total_block) * 100
            else:
                waste = 0  # No assigned products → no waste to calculate
            
            block_wastes.append(waste)
            total_msi += total_master
            total_prod += total_block

        m['Waste'] = block_wastes
    
    # Ensure we don't divide by zero
    if total_prod == 0:
        return float('inf')

    overall_waste = (abs(total_msi - total_prod) / total_prod) * 100
    return overall_waste


########################################
# Normal Best-Fit Initial Assignment
########################################
def initialSolHeuristic(masters, products):
    products_sorted = sorted(products, key=lambda p: p[0], reverse=True)
    for p in products_sorted:
        prodWidth, prodLength, _ = p
        best_fit = None
        best_slack = float('inf')
        for m in masters:
            for block in m['Products']:
                used_width = sum(prod[0] for prod in block)
                slack = m['Width'] - used_width - prodWidth
                if slack >= 0 and slack < best_slack:
                    best_slack = slack
                    best_fit = block
        if best_fit is not None:
            best_fit.append(p)
        else:
            print("Unable to assign product:", p)
    return masters

########################################
# Single-Product Master Heuristic
########################################
def initialSolHeuristic_single(masters, products):
    """
    Try to assign each product to a master that currently has no products assigned.
    If no such master is available, fall back to the normal best-fit assignment.
    """
    products_sorted = sorted(products, key=lambda p: p[0], reverse=True)
    for p in products_sorted:
        prodWidth, prodLength, _ = p
        assigned = False
        # First, try to assign to an empty master.
        for m in masters:
            if all(len(block) == 0 for block in m['Products']):
                if m['Width'] >= prodWidth:
                    m['Products'][0].append(p)
                    assigned = True
                    break
        # If not assigned, fall back to best-fit.
        if not assigned:
            for m in masters:
                for block in m['Products']:
                    used_width = sum(prod[0] for prod in block)
                    if (m['Width'] - used_width) >= prodWidth:
                        block.append(p)
                        assigned = True
                        break
                if assigned:
                    break
        if not assigned:
            print("Unable to assign product in single mode:", p)
    return masters

########################################
# Compute Initial Solution
########################################
def compute_initial_solution(inv_df, products, len_tol, useSingle=False):
    unit_length = products[0][1]
    masters = createMasterDict(inv_df=inv_df, prod_list_length=unit_length, len_tol=0.5)
    
    if useSingle:
        masters = initialSolHeuristic_single(masters, products)
    else:
        masters = initialSolHeuristic(masters, products)
    
    #print_masters_table(masters)
    waste = calculateWaste(masters)
    return masters

########################################
# Improved Perturbation with Simulated Annealing Options
########################################
def perturb_solution(masters, lengthTol=0.1, waste_threshold=5, greedy_prob=0.1):
    new_masters = copy.deepcopy(masters)
    
    # Build candidate list: each candidate is (master, block, block_waste)
    candidate_list = []
    for m in new_masters:
        for block, block_waste in zip(m['Products'], m['Waste']):
            if block and block_waste >= waste_threshold:
                candidate_list.append((m, block, block_waste))
    
    # Fallback: if no candidate meets threshold, use all non-empty blocks.
    if not candidate_list:
        for m in new_masters:
            for block, block_waste in zip(m['Products'], m['Waste']):
                if block:
                    candidate_list.append((m, block, block_waste))
    if not candidate_list:
        return new_masters

    # With probability greedy_prob, choose from blocks that have more than one product;
    # otherwise, choose randomly among candidates.
    if random.random() < greedy_prob:
        filtered = [cand for cand in candidate_list if len(cand[1]) > 1]
        if filtered:
            donor_master, donor_block, donor_block_waste = max(filtered, key=lambda x: x[2])
        else:
            donor_master, donor_block, donor_block_waste = random.choice(candidate_list)
    else:
        donor_master, donor_block, donor_block_waste = random.choice(candidate_list)

    candidate_product = random.choice(donor_block)
    donor_block.remove(candidate_product)
    prodWidth, prodLength, _ = candidate_product

    # Build target candidate list by treating each product block independently.
    target_candidates = []
    for m in new_masters:
        for block, block_waste in zip(m['Products'], m['Waste']):
            if m is donor_master and block is donor_block:
                continue
            used_width = sum(p[0] for p in block)
            available = m['Width'] - used_width
            if available >= prodWidth and block_waste >= waste_threshold:
                if abs(m['Length'] - prodLength) / m['Length'] <= lengthTol:
                    target_candidates.append((m, block, block_waste))
                    
    if target_candidates:
        target_master, target_block, _ = random.choice(target_candidates)
        target_block.append(candidate_product)
    else:
        # Fallback: try any block where the product fits.
        fallback_candidates = []
        for m in new_masters:
            for block in m['Products']:
                if m is donor_master and block is donor_block:
                    continue
                used_width = sum(p[0] for p in block)
                available = m['Width'] - used_width
                if available >= prodWidth and abs(m['Length'] - prodLength) / m['Length'] <= lengthTol:
                    fallback_candidates.append((m, block))
        if fallback_candidates:
            target_master, target_block = random.choice(fallback_candidates)
            target_block.append(candidate_product)
        else:
            donor_block.append(candidate_product)
            
    #print(calculateWaste(masters))
    #print_masters_table(masters)
    return new_masters





########################################
# Simulated Annealing-Based Local Search
########################################
def localSearch(masters, total_prod, iterations=1000, lengthTol=0.1,
                initial_temp=1.2, cooling_rate=0.99):
    current_solution = copy.deepcopy(masters)
    current_waste = calculateWaste(current_solution)
    best_solution = copy.deepcopy(current_solution)
    best_waste = current_waste
    temperature = initial_temp

    for i in range(iterations):
        candidate = perturb_solution(current_solution, lengthTol)
        candidate_waste = calculateWaste(candidate)
        delta = candidate_waste - current_waste
        if candidate_waste < best_waste:
                best_solution = candidate
                best_waste = candidate_waste
        if delta < 0 or random.random() < math.exp(-delta / temperature):
            current_solution = candidate
            current_waste = candidate_waste
        temperature *= cooling_rate
    return best_solution, best_waste

########################################
# Local Search Wrapper
########################################
def local_search_solution(masters, total_msi, iterations=10000, lengthTol=0.1,
                          initial_temp=1.0, cooling_rate=0.99):
    best_masters, best_waste = localSearch(masters, total_msi, iterations=iterations, 
                                           lengthTol=lengthTol, initial_temp=initial_temp,
                                           cooling_rate=cooling_rate)
    return best_masters, best_waste

########################################
# Main Solve Function (SA-based)
########################################
def solve(inv_df, po_df, selected_pos, label_code, 
          util_tol=0.8,
          rem_tol=0.15,
          len_tol=0.1,
          num_restarts=100,
          iterations=1000):
    products, total_msi = process_selected_pos(selected_pos)
    original_product_count = len(products)
    filtered_inv = filter_inventory(inv_df, label_code)
    
    best_overall_waste = float('inf')
    best_overall_masters = None

    progress_bar = tqdm(range(num_restarts), 
                        desc=f"Restart iterations | Best Waste: {best_overall_waste:.2f}%")
    
    for restart in progress_bar:
        products_copy = products[:]  # Copy product list for this restart.
        masters = compute_initial_solution(filtered_inv, products_copy, len_tol, useSingle=useSingle)
        candidate_masters, candidate_waste = local_search_solution(masters, total_msi, 
                                                                   iterations=iterations, lengthTol=len_tol,
                                                                   initial_temp=1.0, cooling_rate=0.99)
        if candidate_waste < best_overall_waste:
            best_overall_waste = candidate_waste
            best_overall_masters = candidate_masters
        progress_bar.set_description(f"Restart {restart+1}/{num_restarts} | Best Waste: {best_overall_waste:.2f}%")
    
    if best_overall_masters is None or not is_valid_solution(best_overall_masters, original_product_count):
        print("No solution found using current number of Products")
        return None

    calculateWaste(best_overall_masters)
    print(f"\nBest waste: {best_overall_waste:.4f}%")
    print_masters_table(best_overall_masters)
    return best_overall_masters
