class PlanValidator:
    """
    Validates Wayang plans
    """

    def validate_plan(self, plan):
        """
        Validates a JSON Wayang Plan to verify it is executable in Wayang server

        """
        
        # List for errors found
        errors = []
        
        # Go over each operation
        for i, operation in enumerate(plan.get("operators", [])):
            try:
                # Get parameters
                op_id = int(operation.get("id", -1))
                op_input = operation.get("input", [])
                op_output = operation.get("output", [])
                op_cat = operation.get("cat", None)

                # Check that op_id is larger than zero
                if op_id > 0:
                    dummy = None
                else:
                    errors.append(f"Operation id {op_id}: ID must be larger than zero and a number")

                # Check input ids are lower than id
                for input_id in op_input:
                    if input_id >= op_id:
                        errors.append(f"Operation id {op_id}: Input id {input_id} ≥ operation id. Input ids must be smaller than operation id")

                # Check output ids are higher than id
                for output_id in op_output:
                    if output_id <= op_id:
                        errors.append(f"Operation id {op_id}: Output id {output_id} ≤ operation id. Output ids must be larger than operation id")
                
                if op_cat == "unary":

                    # Check that operator have a single input
                    if len(op_output) < 1 and i != len(plan["operators"]) - 1:
                        if i != len(plan["operators"]) - 2:
                            errors.append(f"Operation id {op_id}: Missing output operator")

                    # Check if input operator is longer than one
                    if len(op_input) != 1:
                        errors.append(f"Operation id {op_id}: Unary operators can only have one input id")

                    # Check if there is more than one output operator
                    if len(op_output) > 1:
                        errors.append(f"Operation id {op_id}: Unary operators can only have up to one output id")
                                  
                if op_cat == "binary":

                    # Must have an output id if it is not the last operation
                    if len(op_output) < 1 and i != len(plan["operators"]) - 1:
                        if i != len(plan["operators"]) - 2:
                            errors.append(f"Operation id {op_id}: Missing output operator") 
                    
                    # Check that operators have two inputs
                    if len(op_input) != 2:
                        errors.append(f"Operation id {op_id}: Binary operators must have two input ids")

            except Exception as e:
                errors.append(f"Operation id {op_id}: Unexpected error - {e}")

        # If any errors, return false and the erros
        if errors:
            return False, errors
        # Else return true and an empty error list
        else:
            return True, []