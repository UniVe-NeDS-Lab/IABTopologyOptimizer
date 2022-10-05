decr = 1
diam = 4
deg = 4
for j in range(2, deg+1):
    for i in range(1, diam+1):
        print(f'=== deg {j}  === diam {i}')
        nodes = 1
        level_nodes = 1
        degree = j
        for r in range(1, i+1):
            if not degree:
                break
            level_nodes = level_nodes*degree
            degree -= decr
            nodes += level_nodes
            print(f'deg={degree}, diam={i}, range={r}, nodes={nodes}, level_nodes={level_nodes}')

