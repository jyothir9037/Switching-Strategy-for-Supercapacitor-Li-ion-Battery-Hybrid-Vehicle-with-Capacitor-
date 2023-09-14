def startCharge():
    pass

def capCharge(current_distance, charge_matrix):
    for i in range(0, len(charge_matrix)):
        if( ((current_distance - charge_matrix[i]) < 2) and ((current_distance - charge_matrix[i]) > 0) ):
            startCharge()