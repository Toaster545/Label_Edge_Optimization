import pulp
from collections import defaultdict

def optimize_assignment_column_generation(masters, products):
    """
    Assign product orders to master roll blocks using a column generation (knapsack) approach
    with an iterative improvement phase and a fallback mechanism.
    
    Parameters:
      masters: a list of master roll dictionaries (e.g. created via createMasterDict)
      products: a list of product tuples (width, length_in_mm, product_msi) from process_selected_pos.
      
    Returns:
      masters: The master roll structure updated with product assignments in each block and waste calculated.
      
    Approach:
      - Group the products by their width (i.e., count demand for each width).
      - For each block in each master roll, solve a bounded knapsack problem:
            maximize total width used subject to the block's capacity (with a slight tolerance)
            and not exceeding the remaining demand.
      - If the knapsack returns zero even though demand remains, force a fallback assignment.
      - Update global demand and compute waste.
    """
    EPS = 1e-2  # Small tolerance for capacity constraint

    # Group products by width and store a representative product tuple for each width.
    demand = defaultdict(int)
    rep = {}
    for p in products:
        w = p[0]
        demand[w] += 1
        if w not in rep:
            rep[w] = p

    # Create a sorted list of unique product widths (largest first)
    product_widths = sorted(demand.keys(), reverse=True)

    # === Initial Assignment Phase ===
    for master in masters:
        master['Waste'] = []
        num_blocks = len(master['Products'])
        for b in range(num_blocks):
            capacity = master['Width']  # The available width for this block.
            # If no remaining demand, assign an empty block (full waste)
            if all(demand[w] <= 0 for w in product_widths):
                master['Products'][b] = []
                master['Waste'].append(capacity)
                continue

            # Set up the knapsack problem for this block.
            knap = pulp.LpProblem("Knapsack_Block", pulp.LpMaximize)
            x = {}
            for i, w in enumerate(product_widths):
                x[i] = pulp.LpVariable(f"x_{i}", lowBound=0, cat="Integer")
            # Objective: maximize total width used.
            knap += pulp.lpSum(product_widths[i] * x[i] for i in range(len(product_widths)))
            # Constraint: do not exceed the block capacity (with a tiny tolerance).
            knap += pulp.lpSum(product_widths[i] * x[i] for i in range(len(product_widths))) <= capacity + EPS
            # Constraint: do not exceed the remaining demand.
            for i, w in enumerate(product_widths):
                knap += x[i] <= demand[w]
            
            knap.solve(pulp.PULP_CBC_CMD(msg=0))
            pattern = [int(pulp.value(x[i]) or 0) for i in range(len(product_widths))]
            
            # Fallback: if no products can be cut from this block even though there is demand,
            # force at least one piece of the smallest product that fits.
            if sum(pattern) == 0:
                # Find the smallest product that fits into the block and that has demand.
                forced_assigned = False
                for w in sorted(product_widths):
                    if demand[w] > 0 and w <= capacity:
                        pattern[product_widths.index(w)] = 1
                        forced_assigned = True
                        break
                if not forced_assigned:
                    master['Products'][b] = []
                    master['Waste'].append(capacity)
                    continue
            
            # Build the block assignment and update global demand.
            block_assignment = []
            for i, count in enumerate(pattern):
                for _ in range(count):
                    block_assignment.append(rep[product_widths[i]])
                    demand[product_widths[i]] -= 1
            master['Products'][b] = block_assignment
            used = sum(product_widths[i] * pattern[i] for i in range(len(product_widths)))
            waste = capacity - used
            master['Waste'].append(waste)

    # === Optional: Iterative Improvement Phase ===
    # (This part remains similar to the previous version; you can adjust iterations if desired.)
    max_iter = 5  # Adjust as needed.
    iteration = 0
    improved = True
    while improved and iteration < max_iter:
        improved = False
        # For each master roll and block, try to improve the assignment.
        for master in masters:
            capacity = master['Width']
            num_blocks = len(master['Products'])
            for b in range(num_blocks):
                current_assignment = master['Products'][b]
                current_used = sum(item[0] for item in current_assignment)
                
                # Restore current assignment back into demand.
                temp_counts = defaultdict(int)
                for item in current_assignment:
                    temp_counts[item[0]] += 1
                    demand[item[0]] += 1

                # Re-solve the knapsack for this block.
                knap = pulp.LpProblem("Knapsack_Block_Improve", pulp.LpMaximize)
                x = {}
                for i, w in enumerate(product_widths):
                    x[i] = pulp.LpVariable(f"x_imp_{i}", lowBound=0, cat="Integer")
                knap += pulp.lpSum(product_widths[i] * x[i] for i in range(len(product_widths)))
                knap += pulp.lpSum(product_widths[i] * x[i] for i in range(len(product_widths))) <= capacity + EPS
                for i, w in enumerate(product_widths):
                    knap += x[i] <= demand[w]
                knap.solve(pulp.PULP_CBC_CMD(msg=0))
                new_pattern = [int(pulp.value(x[i]) or 0) for i in range(len(product_widths))]
                new_used = sum(product_widths[i] * new_pattern[i] for i in range(len(product_widths)))
                
                # If improvement, update assignment.
                if new_used > current_used:
                    new_assignment = []
                    for i, count in enumerate(new_pattern):
                        for _ in range(count):
                            new_assignment.append(rep[product_widths[i]])
                            demand[product_widths[i]] -= 1
                    master['Products'][b] = new_assignment
                    master['Waste'][b] = capacity - new_used
                    improved = True
                else:
                    # Otherwise, revert: remove the temporary counts.
                    for w, count in temp_counts.items():
                        demand[w] -= count
                    master['Products'][b] = current_assignment
        iteration += 1

    return masters
