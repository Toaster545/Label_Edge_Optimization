import pulp

def optimize_assignment(masters, product_list):
    
    aggregated = {}
    for prod in product_list:
        width = float(prod["Width"])
        length = float(prod["Length"])
        nb = float(prod["Nb"])
        key = (width, length)
        if key not in aggregated:
            aggregated[key] = {"width": width, "length": length, "msi": float(prod["msi"]), "demand": 0}
        aggregated[key]["demand"] += nb
    
    aggregated_products = list(aggregated.values())
    types = list(range(len(aggregated_products)))  # product types as 0,1,2,...
    
    demand = {t: aggregated_products[t]["demand"] for t in types}
    product_types = {t: aggregated_products[t] for t in types}
    
    # Step 2: Build a list of blocks.
    # For each master, record its width (W) and its allocated length (L)
    # (from createMasterDict, each block gets the same L as the master).
    blocks = []
    for m_idx, master in enumerate(masters):
        W = float(master['Width'])
        L = float(master['Length'])
        for b_idx in range(len(master['Products'])):
            blocks.append((m_idx, b_idx, W, L))
    
    B = len(blocks)
    
    # Step 3: Build the MILP model.
    prob = pulp.LpProblem("Aggregated_RollAssignment", pulp.LpMinimize)
    
    # Decision variables: x[(i, t)] = number of products of type t assigned to block i.
    x = pulp.LpVariable.dicts("x", ((i, t) for i in range(B) for t in types), lowBound=0, cat="Integer")
    
    # Binary variables: y[i] indicates whether block i is used.
    y = pulp.LpVariable.dicts("y", (i for i in range(B)), cat="Binary")
    
    # Constraint 1: For each product type, total assigned equals its aggregated demand.
    for t in types:
        prob += pulp.lpSum(x[(i, t)] for i in range(B)) == demand[t], f"Demand_{t}"
    
    # Constraint 2: For each block, total product width (in raw units) does not exceed master width.
    # (Because if we multiply by (L*12/1000), the capacity in MSI is (L*W*12)/1000 and consumption is (L*width*12)/1000.)
    for i in range(B):
        W = blocks[i][2]
        prob += pulp.lpSum(product_types[t]["width"] * x[(i, t)] for t in types) <= W * y[i], f"Capacity_{i}"
    
    # Objective: Minimize total unused MSI across all blocks.
    # For block i (with master parameters W and L), available MSI = (L*W*12)/1000 and used MSI =
    # (L*12)/1000 * sum_{t}(product_types[t]["width"] * x[(i,t)]). Thus, unused MSI =
    # (L*12)/1000 * (W*y[i] - sum_{t}(product_types[t]["width"] * x[(i,t)])).
    obj = pulp.lpSum(((blocks[i][3] * 12)/1000) * (blocks[i][2] * y[i] - 
             pulp.lpSum(product_types[t]["width"] * x[(i, t)] for t in types)) for i in range(B))
    prob += obj, "Total_Unused_MSI"
    
    # Solve the MILP.
    prob.solve()
    print("Solver Status:", pulp.LpStatus[prob.status])
    
    # Step 4: Map the solution back into the masters structure.
    # Clear any existing product assignments.
    for master in masters:
        for b in range(len(master['Products'])):
            master['Products'][b] = []
    
    # For each block, assign products according to the solved decision variables.
    for i in range(B):
        m_idx, b_idx, W, L = blocks[i]
        for t in types:
            count = int(pulp.value(x[(i, t)]))
            product_tuple = (float(product_types[t]["width"]),
                             float(product_types[t]["length"]),
                             float(product_types[t]["msi"]))
            masters[m_idx]['Products'][b_idx].extend([product_tuple] * count)
    
    return masters
